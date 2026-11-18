"""Compara dos ejecuciones pregunta por pregunta: McNemar exacto y bootstrap (SPEC-030, §7.3).

Uso:
    python eval/stats.py --a experiments/runs/s04/e3 --b experiments/runs/s04/e4
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import DEFAULT_BENCH, balanced_accuracy, bootstrap_ci, load_bench, read_jsonl


def mcnemar_exact(a: dict[str, int], b: dict[str, int]) -> dict:
    from scipy.stats import binomtest

    common = sorted(set(a) & set(b))
    only_a = sum(1 for i in common if a[i] == 1 and b[i] == 0)
    only_b = sum(1 for i in common if a[i] == 0 and b[i] == 1)
    n = only_a + only_b
    p = binomtest(min(only_a, only_b), n, 0.5).pvalue if n else 1.0
    return {"n_common": len(common), "only_a_correct": only_a, "only_b_correct": only_b, "p_value": round(float(p), 4)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", type=Path, required=True)
    ap.add_argument("--b", type=Path, required=True)
    ap.add_argument("--bench", nargs="+", type=Path, default=[DEFAULT_BENCH])
    args = ap.parse_args()
    domains = {q["id"]: q.get("domain", "") for q in load_bench(args.bench)}
    va = {r["id"]: r["verdict"] for r in read_jsonl(args.a / "verdicts.jsonl")}
    vb = {r["id"]: r["verdict"] for r in read_jsonl(args.b / "verdicts.jsonl")}
    if not va or not vb:
        raise SystemExit("faltan verdicts.jsonl: ejecuta antes eval/judge.py en ambas ejecuciones")
    result = {
        "a": {"run": str(args.a), **balanced_accuracy(va, domains), "ci95": bootstrap_ci(va, domains, 2000)},
        "b": {"run": str(args.b), **balanced_accuracy(vb, domains), "ci95": bootstrap_ci(vb, domains, 2000)},
        "mcnemar": mcnemar_exact(va, vb),
    }
    p = result["mcnemar"]["p_value"]
    result["conclusion"] = ("diferencia significativa (p < 0,05)" if p < 0.05
                            else "sin diferencia significativa: no decidir por esta comparación")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
