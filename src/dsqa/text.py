"""Utilidades de texto compartidas: tokenización técnica, stopwords y similitud difusa.

rapidfuzz y ftfy están en el entorno de Codabench; si faltan (p. ej. en la laptop) se usan
alternativas de la librería estándar con el mismo comportamiento aproximado.
"""

from __future__ import annotations

import difflib
import re
from typing import Iterable

try:  # pragma: no cover - depende del entorno
    from rapidfuzz import fuzz as _rf_fuzz
    from rapidfuzz import process as _rf_process

    HAVE_RAPIDFUZZ = True
except Exception:  # pragma: no cover
    HAVE_RAPIDFUZZ = False

STOPWORDS = frozenset(
    """a about above after again against all am an and any are as at be because been before being below
    between both but by can could did do does doing down during each few for from further had has have
    having he her here hers herself him himself his how i if in into is it its itself just me more most my
    myself no nor not now of off on once only or other our ours ourselves out over own same she should so
    some such than that the their theirs them themselves then there these they this those through to too
    under until up very was we were what when where which while who whom why will with would you your
    yours yourself yourselves also may might must shall within without upon via per vs etc""".split()
)

QUESTION_WORDS = frozenset(
    """what which who whom whose when where why how would could should does do did is are was were will
    can explain describe give provide name list approximately approximate main point time""".split()
)

# Tokens técnicos: palabras con guiones o dígitos (Be-7, RQ-Kmeans, 40MeV, L=512) y palabras normales.
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*")


def tokenize(text: str, keep_stopwords: bool = False) -> list[str]:
    """Minúsculas; conserva tokens con guion/dígitos y emite además su forma sin separadores."""
    out: list[str] = []
    for m in _TOKEN_RE.finditer(text):
        tok = m.group(0).lower().strip(".")
        if not tok:
            continue
        if not keep_stopwords and tok in STOPWORDS:
            continue
        out.append(tok)
        if any(c in tok for c in "-_."):
            joined = re.sub(r"[-_.]", "", tok)
            if joined and joined != tok:
                out.append(joined)
            out.extend(p for p in re.split(r"[-_.]", tok) if len(p) > 1 and p not in STOPWORDS)
    return out


def ratio(a: str, b: str) -> float:
    """Similitud 0-100."""
    if HAVE_RAPIDFUZZ:
        return float(_rf_fuzz.ratio(a, b))
    return 100.0 * difflib.SequenceMatcher(None, a, b).ratio()


def partial_ratio(a: str, b: str) -> float:
    """Similitud 0-100 del mejor fragmento de la cadena larga con la corta."""
    if HAVE_RAPIDFUZZ:
        return float(_rf_fuzz.partial_ratio(a, b))
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    if not short:
        return 0.0
    if short in long_:
        return 100.0
    n = len(short)
    best = 0.0
    step = max(1, n // 4)
    for i in range(0, max(1, len(long_) - n + 1), step):
        best = max(best, difflib.SequenceMatcher(None, short, long_[i : i + n]).ratio())
    return 100.0 * best


def best_match(word: str, choices: Iterable[str], threshold: float) -> str | None:
    """Mejor coincidencia de `word` en `choices` con similitud >= threshold."""
    choices = list(choices)
    if not choices:
        return None
    if HAVE_RAPIDFUZZ:
        hit = _rf_process.extractOne(word, choices, scorer=_rf_fuzz.ratio, score_cutoff=threshold)
        return hit[0] if hit else None
    hits = difflib.get_close_matches(word, choices, n=1, cutoff=threshold / 100.0)
    return hits[0] if hits else None


def fix_text(text: str) -> str:
    try:
        import ftfy  # type: ignore

        return ftfy.fix_text(text)
    except Exception:
        # Ligaduras y espacios raros más comunes.
        for bad, good in (("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"), ("ﬃ", "ffi"), (" ", " ")):
            text = text.replace(bad, good)
        return text


_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_RE.split(text) if s.strip()]
