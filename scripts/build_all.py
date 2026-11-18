"""Construye y comprueba de una vez los zips de todas las estrategias (E0-E6 y, si existen, las calibradas).

Uso:
    python scripts/build_all.py                       # dist/dsqa_e0_….zip … dsqa_e6_….zip
    python scripts/build_all.py --configs configs/e1.yaml configs/e3.yaml
    python scripts/build_all.py --allow-dirty --allow-missing-models   # solo pruebas locales
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from build_submission import build  # noqa: E402
from check_submission import static_checks  # noqa: E402


def default_configs() -> list[Path]:
    configs = sorted((REPO / "configs").glob("e[0-9].yaml"))
    if (REPO / "resources" / "calibrated").exists():
        configs += sorted((REPO / "configs" / "variants").glob("*-calibrado.yaml"))
    return configs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--configs", nargs="+", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=REPO / "dist")
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--allow-missing-models", action="store_true")
    a = ap.parse_args()

    rows = []
    for cfg in a.configs or default_configs():
        try:
            z = build(cfg, a.out, a.allow_dirty, a.allow_missing_models, None)
            errors = static_checks(z)
            rows.append((cfg.stem, z.name, f"{z.stat().st_size / 2**20:.0f} MB", "OK" if not errors else "; ".join(errors)))
        except SystemExit as exc:
            rows.append((cfg.stem, "—", "—", f"NO construido: {exc}"))
    print("\n| Config | Zip | Tamaño comprimido | Chequeo |\n|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(r) + " |")
    if any(r[3] != "OK" for r in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
