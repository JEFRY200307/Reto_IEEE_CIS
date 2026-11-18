"""Reordenamiento con cross-encoder y diversidad con MMR (SPEC-016)."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Protocol

import numpy as np

from ..text import tokenize
from ..types import Candidate

log = logging.getLogger("dsqa.rerank")


class Scorer(Protocol):
    def score(self, query: str, passages: list[str]) -> list[float]: ...


class CrossEncoderScorer:
    """bge-reranker-base (FlagEmbedding); respaldo con CrossEncoder de sentence-transformers."""

    def __init__(self, model_dir: Path, batch_size: int = 32, max_length: int = 512) -> None:
        self.batch_size, self.max_length = batch_size, max_length
        try:
            import torch
            from FlagEmbedding import FlagReranker  # type: ignore

            self._flag = FlagReranker(str(model_dir), use_fp16=torch.cuda.is_available())
            self._ce = None
            if not torch.cuda.is_available() and getattr(self._flag, "model", None) is not None:
                # Pesos guardados en fp16: en CPU fp16 es emulado (~9× más lento); solo pruebas locales.
                self._flag.model.float()
        except Exception as exc:
            log.warning("FlagReranker no disponible (%s); uso CrossEncoder", exc)
            from sentence_transformers import CrossEncoder

            self._flag = None
            self._ce = CrossEncoder(str(model_dir), max_length=max_length)

    def score(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []
        pairs = [[query, p] for p in passages]
        if self._flag is not None:
            s = self._flag.compute_score(pairs, batch_size=self.batch_size, max_length=self.max_length, normalize=True)
            return [float(x) for x in (s if isinstance(s, list) else [s])]
        raw = self._ce.predict(pairs, batch_size=self.batch_size)
        return [1.0 / (1.0 + math.exp(-float(x))) for x in raw]


class OverlapScorer:
    """Respaldo sin modelos: cobertura de términos de la consulta (para pruebas)."""

    def score(self, query: str, passages: list[str]) -> list[float]:
        q = set(tokenize(query))
        if not q:
            return [0.0] * len(passages)
        return [len(q & set(tokenize(p))) / len(q) for p in passages]


DUPLICATE_SIM = 0.95


def mmr(cands: list[Candidate], vectors: np.ndarray | None, texts: list[str], lam: float, k: int) -> list[Candidate]:
    """Elige iterativamente el candidato con mayor λ·relevancia − (1−λ)·máx. similitud con los elegidos.

    Además descarta casi-duplicados (similitud >= 0,95 con uno ya elegido) mientras queden alternativas.
    """
    if len(cands) < 2:
        return cands[:k]
    if vectors is None:
        sets = [set(tokenize(t)) for t in texts]

        def sim(i: int, j: int) -> float:
            u = sets[i] | sets[j]
            return len(sets[i] & sets[j]) / len(u) if u else 0.0
    else:
        def sim(i: int, j: int) -> float:
            return float(vectors[i] @ vectors[j])

    rel = [c.scores.get("rerank", 0.0) for c in cands]
    chosen: list[int] = []
    remaining = list(range(len(cands)))
    while remaining and len(chosen) < k:
        best, best_val = None, -1e9
        dups = []
        for i in remaining:
            div = max((sim(i, j) for j in chosen), default=0.0)
            if div >= DUPLICATE_SIM:
                dups.append(i)
                continue
            val = lam * rel[i] - (1 - lam) * div
            if val > best_val:
                best, best_val = i, val
        if best is None:  # solo quedan duplicados
            best = dups[0]
        chosen.append(best)
        remaining.remove(best)
    return [cands[i] for i in chosen]


class Reranker:
    def __init__(self, scorer: Scorer) -> None:
        self.scorer = scorer

    def rerank(self, query: str, cands: list[Candidate], texts: list[str], top_n: int,
               lam: float, vectors: np.ndarray | None = None) -> list[Candidate]:
        scores = self.scorer.score(query, texts)  # todos los fusionados (fusion.top_n, 50 por defecto)
        for c, s in zip(cands, scores):
            c.scores["rerank"] = float(s)
        order = sorted(range(len(cands)), key=lambda i: (-cands[i].scores["rerank"], cands[i].chunk_id))
        cands = [cands[i] for i in order]
        texts = [texts[i] for i in order]
        vecs = vectors[order] if vectors is not None else None
        out = mmr(cands, vecs, texts, lam, top_n)
        for r, c in enumerate(out, 1):
            c.ranks["rerank"] = r
        return out
