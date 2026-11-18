"""Calibración offline con CMA-ES de OWA (E5) y del q-FCM (E6) — contribución CI 3 (SPEC-029, ADR-10).

Corre en la laptop (sin GPU) a partir de una ejecución ya hecha en AWS:
- OWA: maximiza recall@N de la lista fusionada, recalculando la fusión con los puntajes por
  buscador guardados en traces.jsonl (necesita gold_chunk_ids).
- q-FCM: maximiza la precisión balanceada con la que la confianza del intento 0 predice si la
  respuesta final fue correcta (necesita verdicts.jsonl del juez local y señales con s5, es decir,
  una ejecución E6 con los pesos de experto).

Control del sobreajuste: validación cruzada de k particiones y variables limitadas a rangos de experto.
Si la brecha calibración − validación supera 10 puntos, se conservan los valores de experto.

Uso:
    python offline/calibrate_cmaes.py --run experiments/runs/s05/e6 --target both
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "eval"))

from common import domain_code, read_jsonl  # noqa: E402

from dsqa.retrieval.fusion import OWA, OWAParams  # noqa: E402
from dsqa.types import Candidate, Signals  # noqa: E402
from dsqa.verify.qfcm import QFCMDecider, QFCMParams  # noqa: E402


# ------------------------------------------------------------------------------------------
# Optimizador: CMA-ES si está instalado; si no, búsqueda aleatoria con perturbaciones.
# ------------------------------------------------------------------------------------------

def optimize(objective, dim: int, budget: int, seed: int) -> tuple[np.ndarray, float]:
    try:
        import cma  # type: ignore

        es = cma.CMAEvolutionStrategy(dim * [0.5], 0.25, {"bounds": [0, 1], "seed": seed, "maxfevals": budget,
                                                          "verbose": -9})
        while not es.stop():
            xs = es.ask()
            es.tell(xs, [-objective(np.asarray(x)) for x in xs])
        return np.asarray(es.result.xbest), -float(es.result.fbest)
    except ImportError:
        print("AVISO: 'cma' no instalado (pip install cma); uso búsqueda aleatoria")
        rng = np.random.default_rng(seed)
        best_x, best_f = np.full(dim, 0.5), objective(np.full(dim, 0.5))
        for i in range(budget):
            x = np.clip(best_x + rng.normal(0, 0.15 if i % 3 else 0.4, dim), 0, 1)
            f = objective(x)
            if f > best_f:
                best_x, best_f = x, f
        return best_x, best_f


def folds(ids: list[str], domains: dict[str, str], k: int, seed: int) -> list[list[str]]:
    rng = random.Random(seed)
    by = {"D": [i for i in ids if domains[i] == "D"], "P": [i for i in ids if domains[i] == "P"]}
    out: list[list[str]] = [[] for _ in range(k)]
    for group in by.values():
        rng.shuffle(group)
        for j, i in enumerate(group):
            out[j % k].append(i)
    return [f for f in out if f]


def balanced(pairs: list[tuple[str, int]]) -> float:
    per = {"D": [], "P": []}
    for dom, ok in pairs:
        per[dom].append(ok)
    vals = [sum(v) / len(v) for v in per.values() if v]
    return sum(vals) / len(vals) if vals else 0.0


# ------------------------------------------------------------------------------------------
# OWA
# ------------------------------------------------------------------------------------------

OWA_BOUNDS = {"a_bm25": (2.0, 20.0), "a_dense": (2.0, 20.0), "c_bm25": (0.2, 0.8), "c_dense": (0.2, 0.8), "w1": (0.2, 0.8)}


def owa_from_x(x: np.ndarray) -> OWAParams:
    v = {k: lo + float(xi) * (hi - lo) for (k, (lo, hi)), xi in zip(OWA_BOUNDS.items(), x)}
    return OWAParams("minmax", {"bm25": v["a_bm25"], "dense": v["a_dense"]},
                     {"bm25": v["c_bm25"], "dense": v["c_dense"]}, [round(v["w1"], 4), round(1 - v["w1"], 4)])


def owa_recall(traces: list[dict], params: OWAParams, top_n: int) -> list[tuple[str, int]]:
    fusion = OWA(params)
    out = []
    for t in traces:
        lists = {name: [Candidate(c["chunk_id"], {name: c["scores"].get(name, 0.0)}, {name: r + 1})
                        for r, c in enumerate(items)] for name, items in t.get("lists", {}).items()}
        fused = fusion.fuse(lists, top_n)
        gold = set(t["gold_chunk_ids"])
        out.append((domain_code(t.get("domain", "")), int(any(c.chunk_id in gold for c in fused[:top_n]))))
    return out


def calibrate_owa(traces: list[dict], k: int, budget: int, seed: int, top_n: int) -> dict:
    traces = [t for t in traces if t.get("gold_chunk_ids") and {"bm25", "dense"} <= set(t.get("lists", {}))]
    if len(traces) < 6:
        raise SystemExit("OWA: hacen falta >= 6 preguntas con gold_chunk_ids y listas bm25+dense en las trazas")
    ids = [t["id"] for t in traces]
    doms = {t["id"]: domain_code(t.get("domain", "")) for t in traces}
    by_id = {t["id"]: t for t in traces}
    expert = OWAParams.load(REPO / "resources" / "owa_params.json")
    train_scores, val_scores, val_expert = [], [], []
    for fold in folds(ids, doms, k, seed):
        train = [by_id[i] for i in ids if i not in fold]
        x, f = optimize(lambda x: balanced(owa_recall(train, owa_from_x(x), top_n)), len(OWA_BOUNDS), budget, seed)
        train_scores.append(f)
        val_scores.append(balanced(owa_recall([by_id[i] for i in fold], owa_from_x(x), top_n)))
        val_expert.append(balanced(owa_recall([by_id[i] for i in fold], expert, top_n)))
    x, f = optimize(lambda x: balanced(owa_recall(traces, owa_from_x(x), top_n)), len(OWA_BOUNDS), budget, seed)
    return {"params": owa_from_x(x), "train": float(np.mean(train_scores)), "val": float(np.mean(val_scores)),
            "val_expert": float(np.mean(val_expert)), "full": f, "metric": f"recall@{top_n} balanceado", "n": len(traces)}


# ------------------------------------------------------------------------------------------
# q-FCM
# ------------------------------------------------------------------------------------------

EDGE_KEYS = ["C1->C6", "C2->C6", "C3->C6", "C4->C6", "C5->C6", "C1->C5"]


def qfcm_from_x(x: np.ndarray, base: QFCMParams) -> QFCMParams:
    edges = {}
    for key, xi in zip(EDGE_KEYS, x[: len(EDGE_KEYS)]):
        lo, hi = base.bounds[key]
        edges[key] = round(lo + float(xi) * (hi - lo), 4)
    phi = round(0.3 + float(x[6]) * 0.7, 4)  # [0.3, 1.0]
    bias = round(0.5 + float(x[7]) * 1.5, 4)  # [0.5, 2.0]
    return QFCMParams(phi, base.lam, bias, base.iterations, edges, base.bounds, base.out_mf)


def qfcm_score(items: list[tuple[str, Signals, int]], params: QFCMParams) -> float:
    dec = QFCMDecider(params)
    # Acierto del decisor: confianza >= 0,5 ↔ la respuesta fue correcta.
    return balanced([(dom, int((dec.confidence(s) >= 0.5) == bool(ok))) for dom, s, ok in items])


def calibrate_qfcm(traces: list[dict], verdicts: dict[str, int], k: int, budget: int, seed: int) -> dict:
    items, ids, doms = [], [], {}
    for t in traces:
        hist = t.get("verification") or []
        if not hist or t["id"] not in verdicts:
            continue
        s = hist[0]["signals"]
        items.append((domain_code(t.get("domain", "")),
                      Signals(s["s1_top1"], s["s2_gap"], s["s3_agreement"], s["s4_coverage"], s.get("s5_judge")),
                      verdicts[t["id"]]))
        ids.append(t["id"])
        doms[t["id"]] = domain_code(t.get("domain", ""))
    if len(items) < 6:
        raise SystemExit("q-FCM: hacen falta >= 6 preguntas con señales (ejecución E4-E6) y verdicts.jsonl")
    if all(it[1].s5_judge is None for it in items):
        print("AVISO: ninguna traza tiene s5 (usa una ejecución E6); se calibra con s5 = 0,5")
    base = QFCMParams.load(REPO / "resources" / "qfcm_params.json")
    by_id = dict(zip(ids, items))
    dim = len(EDGE_KEYS) + 2
    train_scores, val_scores, val_expert = [], [], []
    for fold in folds(ids, doms, k, seed):
        train = [by_id[i] for i in ids if i not in fold]
        x, f = optimize(lambda x: qfcm_score(train, qfcm_from_x(x, base)), dim, budget, seed)
        train_scores.append(f)
        val = [by_id[i] for i in fold]
        val_scores.append(qfcm_score(val, qfcm_from_x(x, base)))
        val_expert.append(qfcm_score(val, base))
    x, f = optimize(lambda x: qfcm_score(items, qfcm_from_x(x, base)), dim, budget, seed)
    return {"params": qfcm_from_x(x, base), "train": float(np.mean(train_scores)), "val": float(np.mean(val_scores)),
            "val_expert": float(np.mean(val_expert)), "full": f, "metric": "precisión balanceada del decisor", "n": len(items)}


def report_and_save(name: str, result: dict, path: Path, max_gap: float, dry_run: bool) -> dict:
    gap = result["train"] - result["val"]
    keep = gap <= max_gap and result["val"] >= result["val_expert"]
    summary = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in result.items() if k != "params"}
    summary.update({"gap": round(gap, 4), "accepted": keep, "params": result["params"].to_json()})
    print(f"\n{name}: {json.dumps(summary, indent=2, ensure_ascii=False)}")
    if not keep:
        print(f"{name}: NO se guardan los calibrados (brecha {gap:.3f} > {max_gap} o peor que experto en validación)")
    elif not dry_run:
        data = result["params"].to_json()
        data["_calibracion"] = {k: v for k, v in summary.items() if k != "params"}
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{name}: guardado en {path}")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, nargs="+", required=True, help="carpeta(s) con traces.jsonl (+ verdicts.jsonl)")
    ap.add_argument("--target", choices=["owa", "qfcm", "both"], default="both")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--budget", type=int, default=600)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--top-n", type=int, default=20, help="recall@N de la fusión (entrada al reranker)")
    ap.add_argument("--max-gap", type=float, default=0.10)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--save-to", type=Path, default=REPO / "resources",
                    help="carpeta donde escribir owa_params.json y qfcm_params.json (en AWS: dentro de la sesión)")
    a = ap.parse_args()
    a.save_to.mkdir(parents=True, exist_ok=True)

    traces, verdicts = [], {}
    for run in a.run:
        traces += read_jsonl(run / "traces.jsonl")
        verdicts.update({r["id"]: int(r["verdict"]) for r in read_jsonl(run / "verdicts.jsonl")})
    report: dict = {}
    targets = {
        "owa": lambda: report_and_save("OWA", calibrate_owa(traces, a.folds, a.budget, a.seed, a.top_n),
                                       a.save_to / "owa_params.json", a.max_gap, a.dry_run),
        "qfcm": lambda: report_and_save("q-FCM", calibrate_qfcm(traces, verdicts, a.folds, a.budget, a.seed),
                                        a.save_to / "qfcm_params.json", a.max_gap, a.dry_run),
    }
    for name, fn in targets.items():
        if a.target not in (name, "both"):
            continue
        try:
            report[name] = fn()
        except SystemExit as exc:  # datos insuficientes para este objetivo: se sigue con el otro
            print(f"{name}: omitido ({exc})")
            report[name] = {"skipped": str(exc)}
    out = a.run[0] / "cmaes_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\ninforme: {out}")


if __name__ == "__main__":
    main()
