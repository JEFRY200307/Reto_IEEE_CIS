"""Ejecuta una o varias configs sobre el banco local, igual que Codabench (SPEC-030).

- Reutiliza OLMo entre configs (se carga una vez por proceso).
- Escribe cada pregunta en cuanto termina: answers.jsonl y traces.jsonl (permite --resume tras un corte spot).
- --retrieval-only: sin LLM, solo recuperación y señales (sirve en la laptop para recall@k).

Uso (en AWS, todas las estrategias con juez local):
    python eval/run_local.py --configs configs/e*.yaml --corpus data/public_pdfs \
        --model-id allenai/Olmo-3.1-32B-Instruct --out experiments/runs/$DSQA_SESSION --resume --judge olmo
Uso (laptop, solo recuperación):
    python eval/run_local.py --configs configs/e2.yaml --corpus data/public_pdfs --retrieval-only --out experiments/runs/local
"""

from __future__ import annotations

import argparse
import gc
import json
import subprocess
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from common import DEFAULT_BENCH, DEFAULT_GOLD, REPO, append_jsonl, load_bench, read_jsonl

from dsqa.pipeline import retrieve
from dsqa.retrieval.query import analyze
from dsqa.runtime import state
from dsqa.runtime.clock import CLOCK
from dsqa.runtime.config import load_config, resolve_to_file
from dsqa.runtime.safety import answer_with_config, setup_logging
from dsqa.text import partial_ratio
from dsqa.verify.actions import run_verification
from dsqa.verify.threshold import NoVerify


def gold_ids(res, gold_texts: list[str], threshold: float = 85.0) -> list[int]:
    """Chunks que contienen alguno de los textos correctos marcados a mano."""
    out = []
    for g in gold_texts:
        g = g.strip().lower()
        if not g:
            continue
        for c in res.chunks:
            if partial_ratio(g, c.raw.lower()) >= threshold:
                out.append(c.chunk_id)
    return sorted(set(out))


def start_sync(out: Path, uri: str | None, every: int) -> threading.Event:
    stop = threading.Event()
    if not uri:
        return stop

    def loop() -> None:
        while not stop.wait(every):
            subprocess.run(["aws", "s3", "sync", str(out), uri, "--only-show-errors"], check=False)

    threading.Thread(target=loop, daemon=True).start()
    return stop


def run_config(cfg_path: Path, args, questions: list[dict], gold: dict[str, list[str]]) -> None:
    cfg = load_config(cfg_path)
    name = cfg_path.stem
    out = args.out / name
    out.mkdir(parents=True, exist_ok=True)
    resolve_to_file(cfg, out / "config_resolved.yaml")
    answers_path, traces_path = out / "answers.jsonl", out / "traces.jsonl"
    done = {a["id"] for a in read_jsonl(answers_path)} if args.resume else set()
    if not args.resume:
        answers_path.unlink(missing_ok=True)
        traces_path.unlink(missing_ok=True)
    pending = [q for q in questions if q["id"] not in done]
    print(f"[{name}] {len(pending)} preguntas pendientes ({len(done)} ya hechas)")

    model_id = None if args.retrieval_only else args.model_id
    CLOCK.reset()
    t0 = time.monotonic()
    res = state.get_or_init(str(args.corpus), model_id, cfg, REPO)
    init_s = time.monotonic() - t0
    print(f"[{name}] inicialización {init_s:.1f} s: {len(res.documents)} docs, {len(res.chunks)} chunks, "
          f"errores={res.init_errors}")

    meta = {"config": cfg_path.as_posix(), "strategy": cfg.strategy, "model_id": model_id, "corpus": str(args.corpus),
            "started": datetime.now(timezone.utc).isoformat(timespec="seconds"), "init_seconds": round(init_s, 1),
            "documents": len(res.documents), "chunks": len(res.chunks), "init_errors": res.init_errors,
            "skipped_docs": res.skipped_docs, "timings": dict(CLOCK.timings)}
    (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    for i, q in enumerate(pending, 1):
        trace: dict = {"id": q["id"], "domain": q.get("domain"), "question_type": q.get("question_type"),
                       "question": q["question"], "gold_chunk_ids": gold_ids(res, gold.get(q["id"], []))}
        t = time.monotonic()
        if args.retrieval_only:
            query = analyze(q["question"], res, cfg)
            ev = run_verification(query, res, cfg, res.decider or NoVerify(),
                                  lambda qq, f, txt: retrieve(qq, res, cfg, f, txt), CLOCK.mode(), None)
            from dsqa.pipeline import _trace_candidates

            trace.update({"ranked": _trace_candidates(ev.candidates, res, 50, True),
                          "lists": {k: _trace_candidates(v, res, cfg.retrieval.top_k, False) for k, v in ev.lists.items()},
                          "verification": ev.history, "named_doc": query.named_doc, "expansions": query.expansions,
                          "normalized": query.normalized})
            answer = ""
        else:
            answer = answer_with_config(q["question"], str(args.corpus), model_id, cfg, REPO, trace)
        secs = round(time.monotonic() - t, 2)
        append_jsonl(answers_path, {"id": q["id"], "answer": answer, "seconds": secs, "level": trace.get("level")})
        append_jsonl(traces_path, trace)
        print(f"[{name}] {i}/{len(pending)} id={q['id']} {secs}s nivel={trace.get('level')}")

    answers = read_jsonl(answers_path)
    summary = {"n": len(answers), "init_seconds": round(init_s, 1),
               "answer_seconds_total": round(sum(a["seconds"] for a in answers), 1),
               "answer_seconds_mean": round(sum(a["seconds"] for a in answers) / max(1, len(answers)), 2),
               "levels": Counter(a.get("level") for a in answers),
               "estimated_minutes_50q": round((init_s + 50 * sum(a["seconds"] for a in answers) / max(1, len(answers))) / 60, 1)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[{name}] resumen: {summary}")

    # Métricas de recuperación (si hay gold) y juez local reutilizando el OLMo ya cargado.
    traces = read_jsonl(traces_path)
    if any(t.get("gold_chunk_ids") for t in traces):
        from retrieval_metrics import metrics

        rm = {"final": metrics(traces, [1, 5, 20, 50])}
        for key in ("bm25", "dense"):
            if any(key in t.get("lists", {}) for t in traces):
                rm[key] = metrics(traces, [1, 5, 20, 50], key)
        (out / "retrieval_metrics.json").write_text(json.dumps(rm, indent=2), encoding="utf-8")
        print(f"[{name}] recall: {rm['final'].get('ALL')}")
    if args.judge == "olmo" and not args.retrieval_only and res.llm is not None and res.prompts is not None:
        from judge import build_items, judge_with_llm, write_results

        items = build_items(out, {q["id"]: q for q in questions})
        m = write_results(out, items, judge_with_llm(items, res.llm, res.prompts), "olmo")
        print(f"[{name}] juez local: precisión balanceada {m['balanced_accuracy']:.3f} "
              f"(DONES {m['acc_DONES']}, AI {m['acc_AI']})")

    state.clear_caches(keep_llm=True)
    gc.collect()
    try:
        import torch

        torch.cuda.empty_cache()
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--configs", nargs="+", type=Path, required=True)
    ap.add_argument("--bench", nargs="+", type=Path, default=[DEFAULT_BENCH])
    ap.add_argument("--gold", nargs="+", type=Path, default=[DEFAULT_GOLD])
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--model-id", default="allenai/Olmo-3.1-32B-Instruct")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ids", nargs="*", default=None)
    ap.add_argument("--retrieval-only", action="store_true")
    ap.add_argument("--judge", choices=["none", "olmo"], default="none",
                    help="olmo: juzga las respuestas al terminar cada config con el mismo OLMo cargado")
    ap.add_argument("--sync-s3", default=None, help="URI s3:// donde copiar --out cada --sync-every segundos")
    ap.add_argument("--sync-every", type=int, default=300)
    args = ap.parse_args()
    setup_logging()

    questions = load_bench(args.bench)
    if args.ids:
        questions = [q for q in questions if q["id"] in set(args.ids)]
    if args.limit:
        questions = questions[: args.limit]
    gold: dict[str, list[str]] = {}
    for gpath in [*args.gold, DEFAULT_GOLD]:
        if gpath.exists():
            for g in json.loads(gpath.read_text(encoding="utf-8")):
                gold.setdefault(str(g["id"]), g.get("gold_texts", []))
    args.out.mkdir(parents=True, exist_ok=True)
    stop = start_sync(args.out, args.sync_s3, args.sync_every)
    try:
        for cfg_path in args.configs:
            run_config(cfg_path, args, questions, gold)
    finally:
        stop.set()
        if args.sync_s3:
            subprocess.run(["aws", "s3", "sync", str(args.out), args.sync_s3, "--only-show-errors"], check=False)


if __name__ == "__main__":
    main()
