"""Búsqueda con los buscadores activos y filtro blando documento → pasaje (SPEC-013)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..types import Candidate, Query

if TYPE_CHECKING:
    from ..runtime.config import Config
    from ..runtime.state import Resources

log = logging.getLogger("dsqa.retrieval")


def search(
    query: Query, res: "Resources", cfg: "Config", use_doc_filter: bool = True, text: str | None = None
) -> dict[str, list[Candidate]]:
    rc = cfg.retrieval
    text = text or query.search_text
    subset = None
    if use_doc_filter and rc.detect_paper and query.named_doc and query.named_doc[1] >= rc.doc_filter_threshold:
        subset = res.doc_chunks.get(query.named_doc[0])

    out: dict[str, list[Candidate]] = {}
    for name in rc.retrievers:
        index = res.lexical if name == "bm25" else res.dense
        if index is None:
            continue
        try:
            hits = index.search(text, rc.top_k, subset)
            if subset is not None and len(hits) < rc.min_hits:
                # Filtro blando: se completa con búsqueda global.
                seen = {c.chunk_id for c in hits}
                extra = [c for c in index.search(text, rc.top_k) if c.chunk_id not in seen]
                hits = hits + extra[: rc.top_k - len(hits)]
                for r, c in enumerate(hits, 1):
                    c.ranks[name] = r
            out[name] = hits
        except Exception as exc:
            log.warning("buscador %s falló: %s", name, exc)
    return out
