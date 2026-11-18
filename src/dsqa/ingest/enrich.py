"""Enriquecimiento de chunks y pertenencia difusa de dominio (SPEC-008)."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

from ..types import Chunk, Document, ExtractedDoc

DOMAINS = ("DONES", "AI")


class DomainLexicon:
    """Términos característicos de cada dominio. Pertenencia μ = 1 - exp(-coincidencias / k)."""

    def __init__(self, terms: dict[str, list[str]], k: float = 4.0) -> None:
        self.k = k
        self.patterns = {
            d: re.compile(r"\b(?:" + "|".join(re.escape(t) for t in sorted(ts, key=len, reverse=True)) + r")\b", re.IGNORECASE)
            for d, ts in terms.items()
            if ts
        }

    @classmethod
    def load(cls, path: Path | None) -> "DomainLexicon":
        if path and path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls({d: data.get(d, []) for d in DOMAINS}, float(data.get("k", 4.0)))
        return cls(DEFAULT_TERMS)

    def memberships(self, text: str) -> dict[str, float]:
        return {d: 1.0 - math.exp(-len(p.findall(text)) / self.k) for d, p in self.patterns.items()}


DEFAULT_TERMS = {
    "DONES": ["IFMIF", "DONES", "lithium loop", "deuteron", "accelerator", "neutron", "irradiation", "beam",
              "target", "test cell", "fusion", "tritium", "activation", "HEBT", "RFQ", "linac", "dpa"],
    "AI": ["neural", "learning", "dataset", "model", "training", "transformer", "benchmark", "classification",
           "algorithm", "fuzzy", "optimization", "embedding", "language model", "reinforcement", "accuracy"],
}


def document_domain(doc: ExtractedDoc, lexicon: DomainLexicon) -> dict[str, float]:
    sample = " ".join([doc.title, doc.abstract, *(p.text for p in doc.pages[:2])])[:12000]
    return lexicon.memberships(sample)


def to_document(doc: ExtractedDoc, lexicon: DomainLexicon) -> Document:
    return Document(doc.doc_id, doc.path, doc.title, doc.abstract, document_domain(doc, lexicon))


def enrich(chunks: list[Chunk], doc: Document, enabled: bool) -> list[Chunk]:
    if not enabled:
        return chunks
    for c in chunks:
        prefix = doc.title if not c.section else f"{doc.title} | {c.section}"
        c.text = f"{prefix}\n{c.raw}"
    return chunks
