"""Descarga los modelos auxiliares y los guarda en fp16 dentro de models/ (RF-OF-01, ADR-13).

Se ejecuta con internet (laptop, o la instancia de preparación). Los pesos NO van a git: van en el zip.

    models/embedder          BAAI/bge-base-en-v1.5          (E1+)   ~220 MB en fp16
    models/reranker          BAAI/bge-reranker-base         (E3+)   ~560 MB en fp16
    models/embedder-minilm   sentence-transformers/all-MiniLM-L6-v2 (E0) ~90 MB
    models/docling           modelo de layout de Docling    (E0)

Uso:
    python offline/download_models.py                         # embedder + reranker
    python offline/download_models.py --what minilm docling   # lo que necesita E0
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODELS = REPO / "models"
SPECS = {
    "embedder": ("BAAI/bge-base-en-v1.5", MODELS / "embedder"),
    "reranker": ("BAAI/bge-reranker-base", MODELS / "reranker"),
    "minilm": ("sentence-transformers/all-MiniLM-L6-v2", MODELS / "embedder-minilm"),
}


def size_mb(path: Path) -> float:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) / 2**20


def save_sentence_transformer(repo_id: str, out: Path, fp16: bool) -> None:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(repo_id, device="cpu")
    if fp16:
        model.half()
    model.save(str(out), safe_serialization=True)


def save_reranker(repo_id: str, out: Path) -> None:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(repo_id)
    try:
        model = AutoModelForSequenceClassification.from_pretrained(repo_id, dtype=torch.float16)
    except TypeError:
        model = AutoModelForSequenceClassification.from_pretrained(repo_id, torch_dtype=torch.float16)
    tok.save_pretrained(out)
    model.save_pretrained(out, safe_serialization=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--what", nargs="+", default=["embedder", "reranker"],
                    choices=["embedder", "reranker", "minilm", "docling"])
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    MODELS.mkdir(exist_ok=True)
    for what in a.what:
        if what == "docling":
            out = MODELS / "docling"
            if out.exists() and not a.force:
                print(f"ya existe {out}")
                continue
            subprocess.run(["docling-tools", "models", "download", "layout", "-o", str(out)], check=True)
        else:
            repo_id, out = SPECS[what]
            if out.exists() and not a.force:
                print(f"ya existe {out} ({size_mb(out):.0f} MB); usa --force para rehacerlo")
                continue
            print(f"descargando {repo_id} → {out}")
            if what == "reranker":
                save_reranker(repo_id, out)
            else:
                save_sentence_transformer(repo_id, out, fp16=(what == "embedder"))
        print(f"listo: {out} ({size_mb(out):.0f} MB)")
    total = sum(size_mb(p) for p in MODELS.iterdir() if p.is_dir())
    print(f"total en models/: {total:.0f} MB (límite del envío: 950 MB con todo lo demás)")


if __name__ == "__main__":
    main()
