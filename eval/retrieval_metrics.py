"""Recall@k y MRR por dominio a partir de las trazas (sin LLM) (SPEC-030).

Usa `gold_chunk_ids` de cada traza (los resuelve run_local.py a partir de eval/bench/gold_chunks.json).

Uso:
    python eval/retrieval_metrics.py --run experiments/runs/s03/e2 --k 1 5 20 50
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import domain_code, read_jsonl


def metrics(traces: list[dict], ks: list[int], key: str = "ranked") -> dict:
    per = {"D": [], "P": [], "ALL": []}
    for t in traces:
        gold = set(t.get("gold_chunk_ids") or [])
        if not gold:
            continue
        ids = [c["chunk_id"] for c in t.get(key, [])] if key == "ranked" else [c["chunk_id"] for c in t.get("lists", {}).get(key, [])]
        rank = next((i + 1 for i, cid in enumerate(ids) if cid in gold), None)
        row = {f"recall@{k}": int(rank is not None and rank <= k) for k in ks}
        row["mrr"] = 1.0 / rank if rank else 0.0
        per[domain_code(t.get("domain", ""))].append(row)
        per["ALL"].append(row)
    out = {}
    for dom, rows in per.items():
        if rows:
            out[dom] = {m: round(sum(r[m] for r in rows) / len(rows), 4) for m in rows[0]} | {"n": len(rows)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--k", nargs="+", type=int, default=[1, 5, 20, 50])
    a = ap.parse_args()
    traces = read_jsonl(a.run / "traces.jsonl")
    result = {"final": metrics(traces, a.k)}
    for name in ("bm25", "dense"):
        if any(name in t.get("lists", {}) for t in traces):
            result[name] = metrics(traces, a.k, name)
    with_gold = sum(1 for t in traces if t.get("gold_chunk_ids"))
    result["questions_with_gold"] = with_gold
    (a.run / "retrieval_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not with_gold:
        print("AVISO: ninguna pregunta tiene gold_chunk_ids. Completa eval/bench/gold_chunks.json y vuelve a ejecutar run_local.")


if __name__ == "__main__":
    main()
