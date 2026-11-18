"""Tipos de datos compartidos por todas las etapas (documentación técnica §2.6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Kind = Literal["text", "table", "caption", "parent"]
VerdictLabel = Literal["correct", "ambiguous", "incorrect"]


@dataclass
class Page:
    doc_id: str
    page: int  # 0-based
    text: str
    is_table: bool = False


@dataclass
class ExtractedDoc:
    doc_id: str
    path: str
    title: str
    abstract: str
    pages: list[Page]
    tables: list[Page] = field(default_factory=list)
    captions: list[Page] = field(default_factory=list)


@dataclass
class Document:
    doc_id: str
    path: str
    title: str
    abstract: str
    domain: dict[str, float]  # pertenencias {"DONES": μ, "AI": μ}


@dataclass
class Chunk:
    chunk_id: int
    doc_id: str
    page: int
    section: str
    text: str  # texto que se indexa (con prefijo de título y sección si hay enriquecimiento)
    raw: str  # texto original, sin prefijo
    parent_id: int | None = None
    kind: Kind = "text"


@dataclass
class Query:
    original: str
    normalized: str
    expansions: list[str] = field(default_factory=list)
    named_doc: tuple[str, float] | None = None
    domain: dict[str, float] = field(default_factory=dict)
    is_numeric: bool = False
    key_terms: list[str] = field(default_factory=list)

    @property
    def search_text(self) -> str:
        return " ".join([self.normalized, *self.expansions]).strip()

    @property
    def main_domain(self) -> str:
        if not self.domain:
            return "UNKNOWN"
        name, value = max(self.domain.items(), key=lambda kv: kv[1])
        return name if value > 0 else "UNKNOWN"


@dataclass
class Candidate:
    chunk_id: int
    scores: dict[str, float] = field(default_factory=dict)
    ranks: dict[str, int] = field(default_factory=dict)

    def score(self, key: str = "rerank") -> float:
        for k in (key, "fused", "dense", "bm25"):
            if k in self.scores:
                return self.scores[k]
        return 0.0


@dataclass
class Signals:
    s1_top1: float = 0.0
    s2_gap: float = 0.0
    s3_agreement: float = 0.5
    s4_coverage: float = 0.5
    s5_judge: float | None = None

    def as_list(self) -> list[float]:
        s5 = 0.5 if self.s5_judge is None else self.s5_judge
        return [self.s1_top1, self.s2_gap, self.s3_agreement, self.s4_coverage, s5]


@dataclass
class Verdict:
    label: VerdictLabel
    memberships: dict[str, float]
    confidence: float
    detail: dict = field(default_factory=dict)


@dataclass
class Evidence:
    candidates: list[Candidate]
    verdict: Verdict
    attempt: int = 0
    refined: bool = False
    lists: dict[str, list[Candidate]] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
