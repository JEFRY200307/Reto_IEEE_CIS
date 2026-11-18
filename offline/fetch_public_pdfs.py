"""Descarga PDFs públicos de los sitios fuente para el banco local (RF-OF-03, RNF-CU-02).

Lee una lista CSV con columnas: url,filename,domain,license,note
(ejemplo en eval/bench/pdf_list.csv). Guarda en data/public_pdfs/<domain>/<filename> y un
manifest.json con URL, licencia y fecha, para citar las fuentes en la metodología.

Uso:
    python offline/fetch_public_pdfs.py --list eval/bench/pdf_list.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (research; IEEE CIS DSQA challenge local benchmark)"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", type=Path, default=REPO / "eval" / "bench" / "pdf_list.csv")
    ap.add_argument("--out", type=Path, default=REPO / "data" / "public_pdfs")
    ap.add_argument("--delay", type=float, default=1.0, help="segundos entre descargas (cortesía con los sitios)")
    a = ap.parse_args()

    manifest_path = a.out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    with a.list.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("url", "").strip() and not r["url"].startswith("#")]
    for r in rows:
        dest = a.out / (r.get("domain") or "otros") / r["filename"]
        if dest.exists():
            print(f"ya existe: {dest.name}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            req = urllib.request.Request(r["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if not data.startswith(b"%PDF"):
                print(f"NO es un PDF (¿página de acceso?): {r['url']}")
                continue
            dest.write_bytes(data)
            manifest[dest.relative_to(a.out).as_posix()] = {
                "url": r["url"], "license": r.get("license", ""), "note": r.get("note", ""),
                "downloaded": datetime.now(timezone.utc).isoformat(timespec="seconds"), "bytes": len(data)}
            print(f"ok: {dest.name} ({len(data) / 2**20:.1f} MB)")
        except Exception as exc:
            print(f"error en {r['url']}: {exc}")
        time.sleep(a.delay)
    a.out.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(manifest)} PDFs en el manifest: {manifest_path}")


if __name__ == "__main__":
    main()
