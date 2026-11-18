"""Chunking fijo (E0) y por sección con estructura padre-hijo (E1+) (SPEC-007)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..text import split_sentences
from ..types import Chunk, ExtractedDoc

_HEADING_RE = re.compile(
    r"^(?:(?:\d+(?:\.\d+){0,3}\.?)|(?:[IVX]{1,5}\.)|(?:[A-H]\.))\s+[A-Z][^\n]{2,90}$"
)
MIN_CHILD_CHARS = 50


@dataclass
class ChunkSet:
    children: list[Chunk] = field(default_factory=list)  # lo que se indexa
    parents: list[Chunk] = field(default_factory=list)  # lo que lee el LLM


class IdGen:
    def __init__(self) -> None:
        self.child = 0
        self.parent = 0

    def next_child(self) -> int:
        self.child += 1
        return self.child - 1

    def next_parent(self) -> int:
        self.parent += 1
        return self.parent - 1


def _is_heading(line: str) -> bool:
    s = line.strip()
    if len(s) < 4 or len(s) > 90:
        return False
    if _HEADING_RE.match(s):
        return True
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 4 and all(c.isupper() for c in letters) and len(s.split()) <= 8


def _paragraphs(doc: ExtractedDoc) -> list[tuple[int, str, bool]]:
    """(página, párrafo, es_encabezado) en orden de lectura."""
    out: list[tuple[int, str, bool]] = []
    for p in doc.pages:
        buf: list[str] = []
        for line in p.text.split("\n"):
            if not line.strip():
                if buf:
                    out.append((p.page, " ".join(buf).strip(), False))
                    buf = []
            elif _is_heading(line):
                if buf:
                    out.append((p.page, " ".join(buf).strip(), False))
                    buf = []
                out.append((p.page, line.strip(), True))
            else:
                buf.append(line.strip())
                # Párrafos sin línea en blanco: cortar cuando una línea termina en punto y es corta.
                if line.rstrip().endswith((".", ":")) and len(line.strip()) < 60:
                    out.append((p.page, " ".join(buf).strip(), False))
                    buf = []
        if buf:
            out.append((p.page, " ".join(buf).strip(), False))
    return [x for x in out if x[1]]


def _windows(text: str, size: int, overlap: int) -> list[str]:
    """Ventanas de ~size caracteres cortando en oraciones; una oración larga se corta en palabras."""
    if len(text) <= size:
        return [text]
    units: list[str] = []
    for sent in split_sentences(text):
        if len(sent) <= size:
            units.append(sent)
        else:
            words, cur = sent.split(), ""
            for w in words:
                if len(cur) + len(w) + 1 > size and cur:
                    units.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            if cur:
                units.append(cur)
    out, cur = [], ""
    for u in units:
        if len(cur) + len(u) + 1 > size and cur:
            out.append(cur)
            tail = cur[-overlap:] if overlap else ""
            tail = tail[tail.find(" ") + 1 :] if " " in tail else tail
            cur = f"{tail} {u}".strip()
        else:
            cur = f"{cur} {u}".strip()
    if cur:
        out.append(cur)
    return out


def _side_chunks(doc: ExtractedDoc, ids: IdGen, out: ChunkSet) -> None:
    for t in doc.tables:
        out.children.append(Chunk(ids.next_child(), doc.doc_id, t.page, "Table", t.text[:4000], t.text[:4000], None, "table"))
    for c in doc.captions:
        out.children.append(Chunk(ids.next_child(), doc.doc_id, c.page, "Caption", c.text, c.text, None, "caption"))


def chunk_fixed(doc: ExtractedDoc, ids: IdGen, size: int = 800, overlap: int = 150, side: bool = False) -> ChunkSet:
    """Baseline del kit: párrafos agrupados en ~size caracteres con solape."""
    out = ChunkSet()
    paras = _paragraphs(doc)
    cur, cur_page = "", 0
    for page, para, _ in paras:
        for piece in _windows(para, size, overlap) if len(para) > size else [para]:
            if cur and len(cur) + len(piece) + 1 > size:
                out.children.append(Chunk(ids.next_child(), doc.doc_id, cur_page, "", cur, cur))
                cur = cur[-overlap:] if overlap else ""
                cur_page = page
            if not cur.strip():
                cur_page = page
            cur = f"{cur}\n{piece}".strip() if cur else piece
    if cur.strip():
        out.children.append(Chunk(ids.next_child(), doc.doc_id, cur_page or 0, "", cur, cur))
    out.children = [c for c in out.children if len(c.raw) >= MIN_CHILD_CHARS]
    if side:
        _side_chunks(doc, ids, out)
    return out


def chunk_section(
    doc: ExtractedDoc, ids: IdGen, child_chars: int = 600, parent_chars: int = 2000, overlap: int = 100
) -> ChunkSet:
    out = ChunkSet()
    paras = _paragraphs(doc)
    n_headings = sum(1 for *_, h in paras if h)

    sections: list[tuple[str, list[tuple[int, str]]]] = []
    current: tuple[str, list[tuple[int, str]]] = ("", [])
    for page, text, is_head in paras:
        if is_head and n_headings >= 2:
            if current[1]:
                sections.append(current)
            current = (text, [])
        else:
            current[1].append((page, text))
    if current[1]:
        sections.append(current)

    for title, items in sections:
        # Padres: párrafos acumulados hasta parent_chars.
        buf, buf_page = "", None
        groups: list[tuple[int, str]] = []
        for page, text in items:
            if buf and len(buf) + len(text) + 1 > parent_chars:
                groups.append((buf_page or 0, buf))
                buf, buf_page = "", None
            if buf_page is None:
                buf_page = page
            buf = f"{buf}\n{text}".strip() if buf else text
        if buf:
            groups.append((buf_page or 0, buf))
        for page, ptext in groups:
            if len(ptext) > parent_chars * 1.5:  # párrafo gigante: se parte también el padre
                ptexts = _windows(ptext, parent_chars, overlap)
            else:
                ptexts = [ptext]
            for pt in ptexts:
                pid = ids.next_parent()
                out.parents.append(Chunk(pid, doc.doc_id, page, title, pt, pt, None, "parent"))
                for ct in _windows(pt.replace("\n", " "), child_chars, overlap):
                    if len(ct) >= MIN_CHILD_CHARS:
                        out.children.append(Chunk(ids.next_child(), doc.doc_id, page, title, ct, ct, pid, "text"))
    _side_chunks(doc, ids, out)
    return out
