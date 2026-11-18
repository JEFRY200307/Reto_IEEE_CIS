"""Construcción del contexto que lee OLMo (SPEC-022)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ..runtime.clock import Mode
from ..types import Evidence

if TYPE_CHECKING:
    from ..runtime.config import Config
    from ..runtime.state import Resources


def _approx_tokens(text: str) -> int:
    return int(len(text) / 4 * 1.1) + 1


def select(evidence: Evidence, cfg: "Config", mode: Mode, limit_override: int | None = None) -> list[int]:
    """Chunk IDs elegidos, en orden de relevancia."""
    c = cfg.context
    cands = evidence.candidates
    if limit_override is not None:
        return [x.chunk_id for x in cands[:limit_override]]
    if c.mode == "budget":
        chosen = [x.chunk_id for x in cands]
    elif c.mode == "topk":
        chosen = [x.chunk_id for x in cands[: c.top_k]]
    else:
        good = [x.chunk_id for x in cands if x.score("rerank") >= c.min_score]
        n = max(c.min_chunks, min(len(good), c.max_chunks))
        chosen = [x.chunk_id for x in cands[:n]]
    if evidence.refined:
        extra = cfg.verify.ambiguous_extra_chunks
        chosen = [x.chunk_id for x in cands[: len(chosen) + extra]]
    if mode != Mode.NORMAL:
        chosen = chosen[:3]
    return chosen


def build_context(
    evidence: Evidence,
    res: "Resources",
    cfg: "Config",
    mode: Mode = Mode.NORMAL,
    count_tokens: Callable[[str], int] | None = None,
    max_tokens: int | None = None,
    limit_override: int | None = None,
) -> tuple[str, int, list[str]]:
    """Devuelve (texto del contexto, tokens, claves de los pasajes usados)."""
    c = cfg.context
    count = count_tokens or _approx_tokens
    budget = max_tokens or c.max_tokens
    neighbors = c.neighbors + (1 if evidence.refined and c.neighbors == 0 else 0)
    if mode != Mode.NORMAL:
        neighbors = 0

    keys: list[tuple[str, int]] = []
    for cid in select(evidence, cfg, mode, limit_override):
        ch = res.chunks[cid]
        if c.use_parent and ch.parent_id is not None:
            base = ("p", ch.parent_id)
            pool, idx = res.parents, ch.parent_id
        else:
            base = ("c", cid)
            pool, idx = res.chunks, cid
        group = [base]
        for d in range(1, neighbors + 1):
            for j in (idx - d, idx + d):
                if 0 <= j < len(pool) and pool[j].doc_id == ch.doc_id and pool[j].kind == pool[idx].kind:
                    group.append((base[0], j))
        for k in group:
            if k not in keys:
                keys.append(k)

    parts: list[str] = []
    used: list[str] = []
    total = 0
    for kind, idx in keys:
        ch = res.parents[idx] if kind == "p" else res.chunks[idx]
        doc = res.documents.get(ch.doc_id)
        title = doc.title if doc else ch.doc_id
        block = f"[Doc: {title}, p. {ch.page + 1}]\n{ch.raw.strip()}"
        n = count(block)
        if total + n > budget:
            if not parts and n > budget:  # un único pasaje demasiado largo: se recorta
                ratio = budget / n
                block = block[: max(200, int(len(block) * ratio * 0.95))]
                parts.append(block)
                used.append(f"{kind}{idx}")
                total += count(block)
            break
        parts.append(block)
        used.append(f"{kind}{idx}")
        total += n
    return "\n\n".join(parts), total, used
