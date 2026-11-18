"""Utilidades compartidas por los scripts de evaluación local."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

# La consola de Windows usa cp1252 y no puede imprimir Δ, →, φ, λ: forzar UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

DEFAULT_BENCH = REPO / "eval" / "bench" / "sample_qa.json"
DEFAULT_GOLD = REPO / "eval" / "bench" / "gold_chunks.json"


def domain_code(domain: str) -> str:
    """'DONES' → D; cualquier otro ('AI Papers', 'AI') → P."""
    return "D" if str(domain).upper().startswith("DONES") else "P"


def load_bench(paths: Iterable[Path]) -> list[dict]:
    out: list[dict] = []
    for p in paths:
        for q in json.loads(Path(p).read_text(encoding="utf-8")):
            q = dict(q)
            q["id"] = str(q["id"])
            out.append(q)
    return out


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, item: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def balanced_accuracy(verdicts: dict[str, int], domains: dict[str, str]) -> dict:
    """Fórmula oficial: A = ½ (acc_D + acc_P). Un dominio sin preguntas no cuenta."""
    per: dict[str, list[int]] = {"D": [], "P": []}
    for qid, v in verdicts.items():
        per[domain_code(domains.get(qid, ""))].append(int(v))
    accs = {k: (sum(v) / len(v) if v else None) for k, v in per.items()}
    present = [a for a in accs.values() if a is not None]
    return {"balanced_accuracy": sum(present) / len(present) if present else 0.0,
            "acc_DONES": accs["D"], "acc_AI": accs["P"], "n_DONES": len(per["D"]), "n_AI": len(per["P"]),
            "n": sum(len(v) for v in per.values())}


def bootstrap_ci(verdicts: dict[str, int], domains: dict[str, str], n_boot: int = 10000, seed: int = 0) -> tuple[float, float]:
    """IC 95 % de la precisión balanceada remuestreando preguntas con reemplazo."""
    rng = random.Random(seed)
    ids = list(verdicts)
    if not ids:
        return 0.0, 0.0
    vals = []
    for _ in range(n_boot):
        per: dict[str, list[int]] = {"D": [], "P": []}
        for _ in ids:
            q = rng.choice(ids)
            per[domain_code(domains.get(q, ""))].append(int(verdicts[q]))
        present = [sum(v) / len(v) for v in per.values() if v]
        vals.append(sum(present) / len(present))
    vals.sort()
    return vals[int(0.025 * n_boot)], vals[min(n_boot - 1, int(0.975 * n_boot))]
