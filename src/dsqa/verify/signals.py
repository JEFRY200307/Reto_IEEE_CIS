"""Señales de calidad de la evidencia s1-s4 (SPEC-017) y juez OLMo s5 (SPEC-018)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..text import tokenize
from ..types import Candidate, Query, Signals

if TYPE_CHECKING:
    from ..generate.llm import LLM
    from ..generate.prompts import Prompts

log = logging.getLogger("dsqa.verify")


def _clip(x: float) -> float:
    return 0.0 if x != x else max(0.0, min(1.0, float(x)))  # x != x → NaN


def compute_signals(
    query: Query,
    ranked: list[Candidate],
    lists: dict[str, list[Candidate]],
    texts: dict[int, str],
    agreement_topk: int = 10,
    coverage_topk: int = 3,
) -> Signals:
    if not ranked:
        return Signals(0.0, 0.0, 0.0, 0.0)
    has_rerank = "rerank" in ranked[0].scores
    if has_rerank:
        s1 = _clip(ranked[0].scores["rerank"])
        s2 = _clip(s1 - ranked[1].scores.get("rerank", 0.0)) if len(ranked) > 1 else s1
    else:  # sin reranker no hay una escala absoluta: valor neutro
        s1, s2 = 0.5, 0.5

    if "bm25" in lists and "dense" in lists:
        a = {c.chunk_id for c in lists["bm25"][:agreement_topk]}
        b = {c.chunk_id for c in lists["dense"][:agreement_topk]}
        s3 = len(a & b) / len(a | b) if (a | b) else 0.0
    else:
        s3 = 0.5

    if query.key_terms:
        evidence = " ".join(texts.get(c.chunk_id, "") for c in ranked[:coverage_topk]).lower()
        ev_tokens = set(tokenize(evidence))
        hits = sum(1 for t in query.key_terms if t in ev_tokens or (len(t) > 3 and t in evidence))
        s4 = hits / len(query.key_terms)
    else:
        s4 = 0.5
    return Signals(_clip(s1), _clip(s2), _clip(s3), _clip(s4))


def judge_sufficiency(llm: "LLM", prompts: "Prompts", question: str, passages: list[str], max_tokens: int) -> float | None:
    """s5 = P(Yes) / (P(Yes) + P(No)) con una sola pasada de OLMo, sin generar texto."""
    try:
        budget = max(100, max_tokens // max(1, len(passages)))
        evidence = "\n\n".join(llm.truncate(p, budget) for p in passages)
        messages = prompts.render("judge_s5", question=question, context=evidence)
        probs = llm.next_token_probs(messages, ["Yes", "No"])
        total = probs.get("Yes", 0.0) + probs.get("No", 0.0)
        return probs.get("Yes", 0.0) / total if total > 0 else 0.5
    except Exception as exc:
        log.warning("juez s5 falló: %s", exc)
        return None
