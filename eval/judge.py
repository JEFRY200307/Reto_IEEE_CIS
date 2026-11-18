"""Juez local binario (correcto / incorrecto) frente a la respuesta de referencia (SPEC-030).

Sirve para COMPARAR configuraciones entre sí, no para predecir el puesto: el juez oficial es otro.
run_local.py --judge olmo lo llama directamente reutilizando el OLMo ya cargado.

Backends:
  olmo    OLMo con el prompt judge_local (en AWS, con GPU)
  manual  escribe verdicts_manual.csv para completar a mano (columna verdict: 1 o 0)
  file    lee ese CSV ya completado

Uso:
    python eval/judge.py --run experiments/runs/s04/e3 experiments/runs/s04/e4 --backend olmo
    python eval/judge.py --run experiments/runs/s04/e3 --backend manual
    python eval/judge.py --run experiments/runs/s04/e3 --backend file
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from common import DEFAULT_BENCH, REPO, balanced_accuracy, bootstrap_ci, load_bench, read_jsonl


def build_items(run: Path, bench: dict[str, dict]) -> list[dict]:
    answers = {r["id"]: r["answer"] for r in read_jsonl(run / "answers.jsonl")}
    return [{"id": i, "domain": bench[i].get("domain", ""), "question_type": bench[i].get("question_type", ""),
             "question": bench[i]["question"], "reference": bench[i]["answer"], "answer": ans}
            for i, ans in answers.items() if i in bench and ans]


def judge_with_llm(items: list[dict], llm, prompts) -> dict[str, int]:
    out = {}
    for it in items:
        msgs = prompts.render("judge_local", question=it["question"], reference=it["reference"], answer=it["answer"])
        text = llm.generate(msgs, 5).upper()
        out[it["id"]] = int("INCORRECT" not in text and "CORRECT" in text)
    return out


def write_results(run: Path, items: list[dict], verdicts: dict[str, int], backend: str) -> dict:
    with (run / "verdicts.jsonl").open("w", encoding="utf-8") as f:
        for it in items:
            if it["id"] in verdicts:
                f.write(json.dumps({"id": it["id"], "verdict": verdicts[it["id"]], "backend": backend}) + "\n")
    domains = {it["id"]: it["domain"] for it in items}
    m = balanced_accuracy(verdicts, domains)
    lo, hi = bootstrap_ci(verdicts, domains, 2000) if verdicts else (0.0, 0.0)
    m["ci95"] = [round(lo, 4), round(hi, 4)]
    by_type: dict[str, list[int]] = {}
    for it in items:
        if it["id"] in verdicts:
            by_type.setdefault(it["question_type"], []).append(verdicts[it["id"]])
    m["by_type"] = {k: round(sum(v) / len(v), 3) for k, v in by_type.items()}
    m["backend"] = backend
    (run / "metrics.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
    return m


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, nargs="+", required=True)
    ap.add_argument("--bench", nargs="+", type=Path, default=[DEFAULT_BENCH])
    ap.add_argument("--backend", choices=["olmo", "manual", "file"], default="olmo")
    ap.add_argument("--model-id", default="allenai/Olmo-3.1-32B-Instruct")
    a = ap.parse_args()
    bench = {q["id"]: q for q in load_bench(a.bench)}

    llm = prompts = None
    if a.backend == "olmo":
        from dsqa.generate.llm import load_llm
        from dsqa.generate.prompts import Prompts
        from dsqa.runtime.config import Config

        llm = load_llm(a.model_id, Config().generate)  # una sola carga para todas las ejecuciones
        prompts = Prompts(REPO / "resources" / "prompts")

    for run in a.run:
        items = build_items(run, bench)
        csv_path = run / "verdicts_manual.csv"
        if a.backend == "manual":
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["id", "domain", "question_type", "question", "reference", "answer", "verdict"])
                w.writeheader()
                for it in items:
                    w.writerow({**it, "verdict": ""})
            print(f"completa la columna verdict (1/0) en {csv_path} y ejecuta --backend file")
            continue
        if a.backend == "file":
            with csv_path.open(encoding="utf-8") as f:
                verdicts = {r["id"]: int(str(r["verdict"]).strip().upper() in ("1", "CORRECT", "TRUE", "SI", "SÍ"))
                            for r in csv.DictReader(f) if str(r.get("verdict", "")).strip()}
        else:
            verdicts = judge_with_llm(items, llm, prompts)
        m = write_results(run, items, verdicts, a.backend)
        print(f"{run}: {json.dumps(m, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
