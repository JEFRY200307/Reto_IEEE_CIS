"""Análisis de la consulta (SPEC-012): normalización, erratas, glosario, dominio, paper nombrado,
detección de preguntas numéricas, términos clave y reformulaciones para el reintento."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from ..text import QUESTION_WORDS, STOPWORDS, best_match, fix_text, tokenize
from ..types import Query

if TYPE_CHECKING:
    from ..runtime.config import Config
    from ..runtime.state import Resources

_LATEX_CMD_RE = re.compile(r"\\(?:text|mathrm|mathbf|mathit|operatorname)\{([^}]*)\}")
_NUMERIC_RE = re.compile(
    r"\b(how (?:many|much|long|large|big|high|fast)|what (?:is|would be|will be) the (?:value|number|rate|"
    r"constant|volume|temperature|pressure|flow|ratio|energy|current|power|mass|size|length|half[- ]life|dose|"
    r"activity)|volum(?:e|en)|temperature|flow rate|decay constant|half[- ]life|ratio|percentage|percent|"
    r"calculate|compute|estimate|approximate|in (?:days|hours|seconds|years|kelvin|celsius|mev|kev|ma|kw|mw|m3|m\^3))\b",
    re.IGNORECASE,
)
_NUM_UNIT_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|k?m|mm|cm|m3|l|s|ms|h|days?|years?|k|°c|mev|kev|gev|ma|kw|mw|bar|pa|t|kg|g)\b", re.IGNORECASE)
_ACRONYM_RE = re.compile(r"\b[A-Z][A-Za-z0-9]*[A-Z0-9][A-Za-z0-9-]*\b")


def load_glossary(path: Path | None) -> dict[str, list[str]]:
    if not path or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for key, value in data.items():
        if key.startswith("_"):
            continue
        exps = value.get("expansions", []) if isinstance(value, dict) else list(value)
        if exps:
            out[key] = exps
    return out


def normalize(question: str) -> str:
    q = fix_text(question)
    q = _LATEX_CMD_RE.sub(r"\1", q)
    q = q.replace("$", " ").replace("\\", " ")
    return re.sub(r"\s+", " ", q).strip()


def fix_typos(text: str, vocabulary: set[str], threshold: float) -> str:
    if not vocabulary:
        return text
    words = re.findall(r"[A-Za-z]{4,}", text)
    for w in set(words):
        lw = w.lower()
        if lw in vocabulary or lw in STOPWORDS or w.isupper():
            continue
        candidates = [v for v in vocabulary if abs(len(v) - len(lw)) <= 2 and v[:1] == lw[:1] and v.isalpha()]
        hit = best_match(lw, candidates, threshold)
        if hit and hit != lw:
            text = re.sub(rf"\b{re.escape(w)}\b", hit, text)
    return text


def is_numeric(question: str) -> bool:
    return bool(_NUMERIC_RE.search(question) or _NUM_UNIT_RE.search(question))


def key_terms(text: str) -> list[str]:
    seen: list[str] = []
    for tok in tokenize(text):
        if tok in QUESTION_WORDS or len(tok) < 2 or tok in seen:
            continue
        seen.append(tok)
    return seen[:20]


def analyze(question: str, res: "Resources", cfg: "Config") -> Query:
    rc = cfg.retrieval
    norm = normalize(question)
    if rc.typo_fix and res.lexical is not None:
        norm = fix_typos(norm, res.vocabulary, rc.typo_threshold)

    expansions: list[str] = []
    if res.glossary:
        for acr in dict.fromkeys(_ACRONYM_RE.findall(norm)):
            for exp in res.glossary.get(acr, []):
                if exp.lower() not in norm.lower() and exp not in expansions:
                    expansions.append(exp)

    domain = res.lexicon.memberships(f"{norm} {' '.join(expansions)}")
    if expansions:  # el glosario es de DONES
        domain["DONES"] = max(domain.get("DONES", 0.0), 0.6)

    named = None
    if rc.detect_paper and res.titles is not None:
        hits = res.titles.match(norm)
        if hits:
            named = hits[0]

    return Query(
        original=question,
        normalized=norm,
        expansions=expansions,
        named_doc=named,
        domain=domain,
        is_numeric=is_numeric(norm),
        key_terms=key_terms(norm),
    )


def reformulate(query: Query, res: "Resources") -> list[str]:
    """Consultas alternativas para el reintento (E4+)."""
    variants = [" ".join([*query.key_terms, *query.expansions])]
    if query.named_doc:
        title = res.documents.get(query.named_doc[0])
        if title:
            stripped = re.sub(re.escape(title.title), "", query.normalized, flags=re.IGNORECASE)
            variants.append(stripped)
    out: list[str] = []
    for v in variants:
        v = v.strip()
        if v and v not in out:
            out.append(v)
    return out
