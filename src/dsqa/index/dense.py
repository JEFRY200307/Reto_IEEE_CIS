"""Índice denso: embedder + búsqueda por producto interno (SPEC-009, ADR-13).

El codificador es intercambiable:
- `SentenceTransformerEncoder`: el real (MiniLM en E0, bge-base desde E1), cargado desde `models/embedder`.
- `HashEncoder`: determinista y sin modelos, para pruebas y para la prueba de humo local.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol

import numpy as np

from ..text import tokenize
from ..types import Candidate
from .lexical import top_candidates


class Encoder(Protocol):
    def encode(self, texts: list[str], is_query: bool = False) -> np.ndarray: ...


class SentenceTransformerEncoder:
    def __init__(self, model_dir: Path, device: str = "auto", batch_size: int = 256, fp16: bool = True,
                 query_instruction: str = "", max_seq_length: int = 512) -> None:
        import torch
        from sentence_transformers import SentenceTransformer

        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(str(model_dir), device=device)
        self.model.max_seq_length = max_seq_length
        if fp16 and device.startswith("cuda"):
            self.model.half()
        elif not device.startswith("cuda"):
            # Los pesos vienen en fp16; en CPU fp16 es emulado y muy lento: se pasa a fp32.
            self.model.float()
        self.batch_size = batch_size
        # Instrucción de consulta de BGE (vacía para MiniLM en E0); viene de la config.
        self.query_instruction = query_instruction

    def encode(self, texts: list[str], is_query: bool = False) -> np.ndarray:
        if is_query and self.query_instruction:
            texts = [self.query_instruction + t for t in texts]
        emb = self.model.encode(texts, batch_size=self.batch_size, normalize_embeddings=True,
                                convert_to_numpy=True, show_progress_bar=False)
        return np.asarray(emb, dtype=np.float32)


class HashEncoder:
    """Bolsa de tokens con hashing (dim 512), normalizada. Sin red ni modelos."""

    def __init__(self, dim: int = 512) -> None:
        self.dim = dim

    def encode(self, texts: list[str], is_query: bool = False) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for tok in tokenize(t):
                h = int.from_bytes(hashlib.md5(tok.encode()).digest()[:4], "little")
                out[i, h % self.dim] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.maximum(norms, 1e-9)


class DenseIndex:
    def __init__(self, encoder: Encoder, texts: list[str]) -> None:
        self.encoder = encoder
        self.embeddings = encoder.encode(texts) if texts else np.zeros((0, 1), dtype=np.float32)
        self._faiss = None
        try:
            import faiss  # type: ignore

            if len(texts):
                self._faiss = faiss.IndexFlatIP(self.embeddings.shape[1])
                self._faiss.add(self.embeddings)
        except Exception:
            self._faiss = None

    def search(self, query: str, k: int, subset: np.ndarray | None = None) -> list[Candidate]:
        if self.embeddings.shape[0] == 0:
            return []
        q = self.encoder.encode([query], is_query=True)[0]
        if subset is None and self._faiss is not None:
            scores, idx = self._faiss.search(q[None, :], min(k, self.embeddings.shape[0]))
            return [Candidate(int(i), {"dense": float(s)}, {"dense": r + 1})
                    for r, (s, i) in enumerate(zip(scores[0], idx[0])) if i >= 0]
        scores = self.embeddings @ q
        return top_candidates(scores, k, "dense", subset)
