"""Limpieza del texto extraído (SPEC-006)."""

from __future__ import annotations

import logging
import re
from collections import Counter

from ..text import fix_text
from ..types import ExtractedDoc, Page

log = logging.getLogger("dsqa.ingest")

_HYPHEN_RE = re.compile(r"([A-Za-z]+)-\n\s*([A-Za-z0-9]+)")
_REFS_RE = re.compile(r"^\s*(?:\d+\.?\s*)?(references|bibliography|literature cited)\s*$", re.IGNORECASE | re.MULTILINE)


def _dehyphen(text: str) -> str:
    def repl(m: re.Match) -> str:
        a, b = m.group(1), m.group(2)
        if b[0].islower() and a.isalpha():
            return a + b  # tempera-\nture → temperature
        return f"{a}-{b}"  # Be-\n7 → Be-7

    return _HYPHEN_RE.sub(repl, text)


def _normalize_line(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip().lower())


EDGE_LINES = 3  # encabezados y pies solo se buscan en las primeras/últimas líneas de cada página


def _edge_indices(lines: list[str]) -> set[int]:
    idx = [i for i, ln in enumerate(lines) if ln.strip()]
    return set(idx[:EDGE_LINES] + idx[-EDGE_LINES:])


def _remove_headers(pages: list[Page]) -> list[Page]:
    if len(pages) < 3:
        return pages
    counts: Counter[str] = Counter()
    for p in pages:
        lines = p.text.splitlines()
        counts.update({_normalize_line(lines[i]) for i in _edge_indices(lines) if len(lines[i].strip()) < 100})
    repeated = {ln for ln, c in counts.items() if c >= max(2, 0.5 * len(pages))}
    if not repeated:
        return pages
    out = []
    for p in pages:
        lines = p.text.splitlines()
        edges = _edge_indices(lines)
        kept = [ln for i, ln in enumerate(lines) if not (i in edges and _normalize_line(ln) in repeated)]
        out.append(Page(p.doc_id, p.page, "\n".join(kept), p.is_table))
    return out


def _cut_references(pages: list[Page]) -> list[Page]:
    full = "\n".join(p.text for p in pages)
    matches = list(_REFS_RE.finditer(full))
    if not matches:
        return pages
    cut = matches[-1].start()
    if cut < 0.5 * len(full) or (len(full) - cut) > 0.5 * len(full):
        return pages  # no recortar más de la mitad del documento
    out, pos = [], 0
    for p in pages:
        start, end = pos, pos + len(p.text)
        if start >= cut:
            break
        text = p.text if end <= cut else p.text[: cut - start]
        out.append(Page(p.doc_id, p.page, text, p.is_table))
        pos = end + 1
    return out


def _whitespace(text: str) -> str:
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_doc(doc: ExtractedDoc, steps: list[str]) -> ExtractedDoc:
    pages = doc.pages
    for step in steps:
        try:
            if step == "ftfy":
                pages = [Page(p.doc_id, p.page, fix_text(p.text), p.is_table) for p in pages]
            elif step == "dehyphen":
                pages = [Page(p.doc_id, p.page, _dehyphen(p.text), p.is_table) for p in pages]
            elif step == "headers":
                pages = _remove_headers(pages)
            elif step == "references":
                pages = _cut_references(pages)
            elif step == "whitespace":
                pages = [Page(p.doc_id, p.page, _whitespace(p.text), p.is_table) for p in pages]
        except Exception as exc:
            log.warning("limpieza '%s' falló en %s: %s", step, doc.path, exc)
    title = fix_text(doc.title) if "ftfy" in steps else doc.title
    abstract = _whitespace(fix_text(doc.abstract)) if steps else doc.abstract
    return ExtractedDoc(doc.doc_id, doc.path, title, abstract, pages, doc.tables, doc.captions)
