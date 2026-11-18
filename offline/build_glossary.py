"""Amplía el glosario de siglas de DONES a partir de PDFs públicos (SPEC-027).

Detecta "Nombre Largo (SIGLA)" y "SIGLA (Nombre Largo)". Las entradas existentes (semilla) tienen
prioridad; las nuevas solo se añaden si aparecen en >= --min-docs documentos.

Uso:
    python offline/build_glossary.py --pdfs data/public_pdfs/DONES --out resources/glossary_dones.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dsqa.ingest.extract import extract_pymupdf, list_pdfs  # noqa: E402

LONG_SHORT = re.compile(r"\b((?:[A-Z][a-z]+[\s-]){1,6}[A-Z][a-z]+)\s*\(([A-Z][A-Za-z0-9-]{1,9})\)")
SHORT_LONG = re.compile(r"\b([A-Z][A-Z0-9-]{1,9})\s*\(((?:[A-Z][a-z]+[\s-]){1,6}[A-Z][a-z]+)\)")
STOP = {"THE", "AND", "FOR", "WITH", "FIG", "TABLE", "NOTE", "ALL", "NOT"}


def initials_match(acr: str, long: str) -> bool:
    words = [w for w in re.split(r"[\s-]+", long) if w and w[0].isupper()]
    letters = "".join(w[0] for w in words).upper()
    core = re.sub(r"[^A-Z]", "", acr.upper())
    return len(core) >= 2 and (letters.startswith(core) or core in letters)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pdfs", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=REPO / "resources" / "glossary_dones.json")
    ap.add_argument("--min-docs", type=int, default=2)
    a = ap.parse_args()

    glossary = json.loads(a.out.read_text(encoding="utf-8")) if a.out.exists() else {}
    seen: dict[tuple[str, str], set[str]] = defaultdict(set)
    manifest_path = a.pdfs / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for pdf in list_pdfs(a.pdfs):
        try:
            text = "\n".join(p.text for p in extract_pymupdf(str(pdf), pdf.stem, tables=False, captions=False).pages)
        except Exception as exc:
            print(f"omitido {pdf.name}: {exc}")
            continue
        text = re.sub(r"\s+", " ", text)
        for long, acr in LONG_SHORT.findall(text):
            if acr.upper() not in STOP and initials_match(acr, long):
                seen[(acr, long.strip())].add(pdf.name)
        for acr, long in SHORT_LONG.findall(text):
            if acr.upper() not in STOP and initials_match(acr, long):
                seen[(acr, long.strip())].add(pdf.name)

    added = 0
    for (acr, long), docs in sorted(seen.items()):
        if len(docs) < a.min_docs or acr.startswith("_"):
            continue
        entry = glossary.setdefault(acr, {"expansions": [], "source": ""})
        if isinstance(entry, dict) and long not in entry["expansions"]:
            if entry.get("source") == "semilla" and entry["expansions"]:
                continue  # la semilla manda
            entry["expansions"].append(long)
            src = next(iter(sorted(docs)))
            entry["source"] = manifest.get(src, {}).get("url", src)
            added += 1
    a.out.write_text(json.dumps(glossary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{added} expansiones nuevas; {sum(1 for k in glossary if not k.startswith('_'))} siglas en {a.out}")


if __name__ == "__main__":
    main()
