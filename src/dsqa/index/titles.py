"""Índice de títulos: ¿qué documento nombra la pregunta? (SPEC-011)."""

from __future__ import annotations

import re
from collections import Counter

import numpy as np

from ..text import ratio, tokenize
from ..types import Document
from .lexical import BM25

# Nombres propios: mayúsculas internas (WinStat, ZeroDiff), siglas (REVEL, FCM) o letras+dígitos (ONB-MACF, GPT4).
_NAME_RE = re.compile(r"\b(?:[A-Z][a-z]+[A-Z][A-Za-z0-9]*|[A-Z]{2,}[A-Za-z0-9]*(?:-[A-Za-z0-9]+)*|[A-Za-z]+-?\d+[A-Za-z0-9-]*)\b")
_COMMON = {"AI", "LLM", "LLMS", "ML", "DNN", "CNN", "RNN", "GPU", "CPU", "PDF", "USA", "EU", "IEEE", "II", "III", "IV"}


def proper_names(text: str) -> set[str]:
    return {m.group(0) for m in _NAME_RE.finditer(text) if m.group(0).upper() not in _COMMON}


class TitleIndex:
    def __init__(self, docs: list[Document], fuzzy_threshold: float = 90.0, ambiguity_gap: float = 0.1) -> None:
        self.docs = docs
        self.fuzzy_threshold = fuzzy_threshold
        self.ambiguity_gap = ambiguity_gap
        self.bm25 = BM25([f"{d.title}\n{d.abstract}" for d in docs])
        names = [proper_names(d.title) for d in docs]
        df = Counter(n.lower() for ns in names for n in ns)
        # Un nombre que aparece en muchos títulos (p. ej. IFMIF-DONES) no identifica un documento.
        self.names = [{n for n in ns if df[n.lower()] <= 2} for ns in names]

    def match(self, question: str, top: int = 3) -> list[tuple[str, float]]:
        if not self.docs:
            return []
        q_names = [n.lower() for n in proper_names(question)]
        bm = self.bm25.scores(tokenize(question))
        bm_norm = bm / bm.max() if bm.max() > 0 else bm
        conf = np.zeros(len(self.docs), dtype=np.float32)
        for i, names in enumerate(self.names):
            hit = 0.0
            for qn in q_names:
                for tn in names:
                    if ratio(qn, tn.lower()) >= self.fuzzy_threshold:
                        hit = 1.0
                        break
                if hit:
                    break
            conf[i] = 0.7 * hit + 0.3 * float(bm_norm[i])
        order = np.argsort(-conf, kind="stable")[:top]
        result = [(self.docs[i].doc_id, float(conf[i])) for i in order]
        if len(result) >= 2 and result[0][1] - result[1][1] < self.ambiguity_gap:
            result[0] = (result[0][0], result[0][1] * 0.5)  # homónimos: menos confianza
        return result
