"""Construye el zip de envío para Codabench a partir de una config (SPEC-026).

Uso:
    python scripts/build_submission.py --config configs/e3.yaml
    python scripts/build_submission.py --config configs/e1.yaml --out dist --allow-dirty
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dsqa.runtime.config import Config, load_config, resolve_to_file  # noqa: E402

LIMIT_BYTES = 950 * 1024 * 1024
WARN_BYTES = 900 * 1024 * 1024
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")


def git_info() -> dict:
    def run(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
        except Exception:
            return ""

    return {"commit": run("rev-parse", "HEAD"), "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(run("status", "--porcelain", "--untracked-files=no"))}


def required_files(cfg: Config) -> tuple[list[str], list[str]]:
    """(recursos, modelos) que la config necesita, como rutas relativas al repo."""
    resources = [cfg.generate.prompts_dir, cfg.ingest.domain_lexicon]
    if cfg.retrieval.glossary:
        resources.append(cfg.retrieval.glossary)
    if cfg.fusion.method == "owa":
        resources.append(cfg.fusion.owa_params)
    if cfg.verify.enabled and cfg.verify.decider == "qfcm":
        resources.append(cfg.verify.qfcm.params_file)
    models = []
    if "dense" in cfg.retrieval.retrievers:
        models.append(cfg.index.embedder)
    if cfg.rerank.enabled:
        models.append(cfg.rerank.model)
    if cfg.ingest.extractor == "docling":
        models.append("models/docling")
    return resources, models


def dir_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def build(config: Path, out: Path, allow_dirty: bool, allow_missing_models: bool, name: str | None) -> Path:
    cfg = load_config(config)
    info = git_info()
    if info["dirty"] and not allow_dirty:
        raise SystemExit("hay cambios sin commit: haz commit (y etiqueta) o usa --allow-dirty")

    resources, models = required_files(cfg)
    missing = [p for p in resources if not (REPO / p).exists()]
    if missing:
        raise SystemExit(f"faltan recursos: {missing}")
    missing_models = [m for m in models if not (REPO / m).exists()]
    if missing_models and not allow_missing_models:
        raise SystemExit(f"faltan modelos: {missing_models}. Ejecuta offline/download_models.py "
                         "(o --allow-missing-models solo para pruebas locales).")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    name = name or f"dsqa_{cfg.strategy.lower()}_{stamp}"
    stage = out / "build" / name
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    shutil.copy2(REPO / "submission" / "main.py", stage / "main.py")
    shutil.copytree(REPO / "src" / "dsqa", stage / "dsqa", ignore=IGNORE)
    resolve_to_file(cfg, stage / "config.yaml")
    for rel in resources:
        src, dst = REPO / rel, stage / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=IGNORE)
        else:
            shutil.copy2(src, dst)
    for rel in models:
        if (REPO / rel).exists():
            shutil.copytree(REPO / rel, stage / rel, ignore=IGNORE)

    sizes = {p.name: dir_size(p) if p.is_dir() else p.stat().st_size for p in stage.iterdir()}
    total = sum(sizes.values())
    build_info = {
        **info, "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config": config.as_posix(), "strategy": cfg.strategy, "description": cfg.description,
        "sizes_bytes": sizes, "total_bytes": total, "missing_models": missing_models,
    }
    (stage / "BUILD_INFO.json").write_text(json.dumps(build_info, indent=2, ensure_ascii=False), encoding="utf-8")

    if total > LIMIT_BYTES:
        raise SystemExit(f"el envío ocupa {total / 2**20:.0f} MB > 950 MB (límite interno)")
    if total > WARN_BYTES:
        print(f"AVISO: el envío ocupa {total / 2**20:.0f} MB (cerca del límite)")

    out.mkdir(parents=True, exist_ok=True)
    zip_path = out / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(stage).as_posix())
    print(f"zip: {zip_path}  ({total / 2**20:.1f} MB sin comprimir, {zip_path.stat().st_size / 2**20:.1f} MB comprimido)")
    if missing_models:
        print(f"AVISO: zip SIN los modelos {missing_models}: no subir a Codabench")
    return zip_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--out", default=REPO / "dist", type=Path)
    ap.add_argument("--name", default=None)
    ap.add_argument("--allow-dirty", action="store_true")
    ap.add_argument("--allow-missing-models", action="store_true", help="solo para pruebas locales")
    a = ap.parse_args()
    build(a.config, a.out, a.allow_dirty, a.allow_missing_models, a.name)


if __name__ == "__main__":
    main()
