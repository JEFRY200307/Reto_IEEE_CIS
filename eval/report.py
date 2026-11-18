"""Tabla de ablación E0-E6 y grafo del q-FCM para el paper (SPEC-030, RF-EV-06).

Recorre experiments/runs/**/ buscando metrics.json, summary.json y retrieval_metrics.json.

Uso:
    python eval/report.py --runs experiments/runs --out experiments/report
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import REPO


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def fmt(x, pct: bool = True) -> str:
    if x is None or x == "":
        return "—"
    return f"{100 * x:.1f}" if pct else f"{x}"


def ablation_table(runs: Path) -> str:
    rows = []
    for summary_path in sorted(runs.rglob("summary.json")):
        run = summary_path.parent
        m, s, r = load(run / "metrics.json"), load(summary_path), load(run / "retrieval_metrics.json")
        meta = load(run / "meta.json")
        final = r.get("final", {}).get("ALL", {})
        rows.append([
            run.relative_to(runs).as_posix(), meta.get("strategy", run.name),
            fmt(m.get("balanced_accuracy")), fmt(m.get("acc_DONES")), fmt(m.get("acc_AI")),
            fmt(final.get("recall@5")), fmt(s.get("answer_seconds_mean"), False), fmt(s.get("estimated_minutes_50q"), False),
        ])
    head = ["Ejecución", "Estrategia", "Prec. bal. %", "DONES %", "AI %", "Recall@5 %", "s/pregunta", "Min. est. (50 q)"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    lines += ["| " + " | ".join(map(str, r)) + " |" for r in rows]
    return "\n".join(lines)


JUMPS = [("e0", "e1"), ("e1", "e2"), ("e2", "e3"), ("e3", "e4"), ("e4", "e5"), ("e5", "e6")]


def jumps_table(runs: Path) -> str:
    """Salto por salto (y E0 → E6): precisión, Δ y McNemar, dentro de cada carpeta de sesión."""
    from common import read_jsonl
    from stats import mcnemar_exact

    head = ["Sesión", "Salto", "Prec. A %", "Prec. B %", "Δ pts", "Solo A", "Solo B", "p (McNemar)"]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    sessions = sorted({p.parent.parent for p in runs.rglob("verdicts.jsonl")})
    for sess in sessions:
        for a, b in [*JUMPS, ("e0", "e6")]:
            ra, rb = sess / a, sess / b
            if not ((ra / "verdicts.jsonl").exists() and (rb / "verdicts.jsonl").exists()):
                continue
            va = {r["id"]: r["verdict"] for r in read_jsonl(ra / "verdicts.jsonl")}
            vb = {r["id"]: r["verdict"] for r in read_jsonl(rb / "verdicts.jsonl")}
            ma, mb = load(ra / "metrics.json"), load(rb / "metrics.json")
            mc = mcnemar_exact(va, vb)
            pa, pb = ma.get("balanced_accuracy", 0.0), mb.get("balanced_accuracy", 0.0)
            lines.append("| " + " | ".join([
                sess.relative_to(runs).as_posix() or ".", f"{a.upper()} → {b.upper()}", fmt(pa), fmt(pb),
                f"{100 * (pb - pa):+.1f}", str(mc["only_a_correct"]), str(mc["only_b_correct"]), f"{mc['p_value']:.3f}",
            ]) + " |")
    return "\n".join(lines)


def qfcm_dot(params_path: Path) -> str:
    p = load(params_path)
    names = {"C1": "Relevancia (s1)", "C2": "Claridad (s2)", "C3": "Acuerdo (s3)", "C4": "Cobertura (s4)",
             "C5": "Juez OLMo (s5)", "C6": "Confianza"}
    lines = ["digraph qfcm {", "  rankdir=LR; node [shape=ellipse, fontname=Helvetica];"]
    for k, v in names.items():
        lines.append(f'  {k} [label="{v}"{", shape=doublecircle" if k == "C6" else ""}];')
    for edge, w in p.get("edges", {}).items():
        if abs(w) > 1e-9:
            a, _, b = edge.partition("->")
            lines.append(f'  {a} -> {b} [label="{w:+.2f}", penwidth={1 + 3 * abs(w):.1f}];')
    lines.append(f'  label="q-FCM  φ={p.get("phi")}  λ={p.get("lam")}  h={p.get("bias")}";')
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=Path, default=REPO / "experiments" / "runs")
    ap.add_argument("--out", type=Path, default=REPO / "experiments" / "report")
    ap.add_argument("--qfcm", type=Path, default=REPO / "resources" / "qfcm_params.json")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    table = ablation_table(a.runs)
    jumps = jumps_table(a.runs)
    (a.out / "ablation.md").write_text(f"## Resultados por ejecución\n\n{table}\n\n## Saltos (McNemar)\n\n{jumps}\n",
                                       encoding="utf-8")
    (a.out / "qfcm.dot").write_text(qfcm_dot(a.qfcm) + "\n", encoding="utf-8")
    print(table)
    print()
    print(jumps)
    print(f"\nGrafo del q-FCM: {a.out / 'qfcm.dot'} (renderizar con: dot -Tpdf qfcm.dot -o qfcm.pdf)")


if __name__ == "__main__":
    main()
