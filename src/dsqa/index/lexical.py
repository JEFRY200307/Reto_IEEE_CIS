"""Índice BM25 (SPEC-010).

Implementación propia con matrices dispersas (scipy): los pesos BM25 se precalculan una vez y
cada consulta es una suma de columnas, mucho más rápido que recorrer documentos en Python.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from scipy import sparse

from ..text import tokenize
from ..types import Candidate


class BM25:
    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.vocab: dict[str, int] = {}
        rows, cols, tfs = [], [], []
        lengths = np.zeros(len(texts), dtype=np.float32)
        for i, text in enumerate(texts):
            counts = Counter(tokenize(text))
            lengths[i] = sum(counts.values())
            for term, tf in counts.items():
                j = self.vocab.setdefault(term, len(self.vocab))
                rows.append(i)
                cols.append(j)
                tfs.append(tf)
        n_docs, n_terms = len(texts), len(self.vocab)
        self.n_docs = n_docs
        if n_docs == 0 or n_terms == 0:
            self.matrix = sparse.csc_matrix((n_docs, max(n_terms, 1)), dtype=np.float32)
            return
        tf = np.asarray(tfs, dtype=np.float32)
        df = np.bincount(np.asarray(cols), minlength=n_terms).astype(np.float32)
        idf = np.log1p((n_docs - df + 0.5) / (df + 0.5))
        avgdl = float(lengths.mean()) or 1.0
        norm = k1 * (1 - b + b * lengths[np.asarray(rows)] / avgdl)
        weights = idf[np.asarray(cols)] * tf * (k1 + 1) / (tf + norm)
        self.matrix = sparse.csc_matrix((weights, (rows, cols)), shape=(n_docs, n_terms), dtype=np.float32)

    def scores(self, query_tokens: list[str]) -> np.ndarray:
        idx = [self.vocab[t] for t in query_tokens if t in self.vocab]
        if not idx or self.n_docs == 0:
            return np.zeros(self.n_docs, dtype=np.float32)
        counts = Counter(idx)
        cols = list(counts)
        sub = self.matrix[:, cols]
        return np.asarray(sub @ np.asarray([counts[c] for c in cols], dtype=np.float32)).ravel()


def top_candidates(scores: np.ndarray, k: int, key: str, subset: np.ndarray | None = None) -> list[Candidate]:
    """Los k mejores (con puntaje > 0 para BM25) como Candidate, con rango 1-based."""
    if subset is not None:
        if subset.size == 0:
            return []
        local = scores[subset]
        order = subset[np.argsort(-local, kind="stable")]
    else:
        order = np.argsort(-scores, kind="stable")
    out: list[Candidate] = []
    for i in order[:k]:
        s = float(scores[i])
        if key == "bm25" and s <= 0:
            break
        out.append(Candidate(int(i), {key: s}, {key: len(out) + 1}))
    return out


class LexicalIndex:
    def __init__(self, texts: list[str], k1: float = 1.5, b: float = 0.75) -> None:
        self.bm25 = BM25(texts, k1, b)

    @property
    def vocabulary(self) -> set[str]:
        return set(self.bm25.vocab)

    def search(self, query: str, k: int, subset: np.ndarray | None = None) -> list[Candidate]:
        return top_candidates(self.bm25.scores(tokenize(query)), k, "bm25", subset)
