"""Extracción de PDF → páginas con metadatos (SPEC-005, ADR-05).

La extracción corre en un pool de procesos. En Linux se usa `fork` y el pool se crea ANTES de
lanzar el hilo que carga OLMo (ADR-04), para no copiar hilos ni tensores a los hijos.
"""

from __future__ import annotations

import hashlib
import logging
import multiprocessing as mp
import os
import re
import sys
import time
from concurrent.futures import Future, ProcessPoolExecutor
from pathlib import Path

from ..types import ExtractedDoc, Page

log = logging.getLogger("dsqa.ingest")

_CAPTION_RE = re.compile(r"^\s*(fig\.?|figure|table|tab\.)\s*\d+[.:]?\s+\S", re.IGNORECASE)
_ABSTRACT_RE = re.compile(r"^\s*abstract\s*[:.\-—]?\s*", re.IGNORECASE | re.MULTILINE)
_INTRO_RE = re.compile(r"^\s*(?:1\.?|I\.)?\s*introduction\b", re.IGNORECASE | re.MULTILINE)
_BAD_TITLE_RE = re.compile(r"(microsoft word|untitled|\.docx?|\.pdf|^[\d\W]+$)", re.IGNORECASE)
MIN_DOC_CHARS = 200


def list_pdfs(corpus_dir: str | Path) -> list[Path]:
    root = Path(corpus_dir)
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf")


def doc_id_for(path: Path, corpus_dir: str | Path) -> str:
    try:
        rel = path.resolve().relative_to(Path(corpus_dir).resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()
    return hashlib.sha1(rel.encode("utf-8")).hexdigest()[:12]


# --------------------------------------------------------------------------------------------
# PyMuPDF
# --------------------------------------------------------------------------------------------


def _import_pymupdf():
    try:
        import pymupdf  # type: ignore
    except ImportError:  # versiones antiguas
        import fitz as pymupdf  # type: ignore
    return pymupdf


def _title_from_fonts(page) -> str:
    """Línea con la fuente más grande de la primera página."""
    best_size, best_text = 0.0, ""
    try:
        data = page.get_text("dict")
    except Exception:
        return ""
    for block in data.get("blocks", []):
        for line in block.get("lines", []):
            spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
            if not spans:
                continue
            size = max(s.get("size", 0) for s in spans)
            text = " ".join(s["text"].strip() for s in spans).strip()
            if size > best_size + 0.5 and 8 <= len(text) <= 250:
                best_size, best_text = size, text
            elif abs(size - best_size) <= 0.5 and best_text and len(best_text) + len(text) < 250:
                best_text = f"{best_text} {text}"
    return best_text.strip()


def _abstract(text: str) -> str:
    m = _ABSTRACT_RE.search(text)
    if not m:
        return ""
    rest = text[m.end() :]
    end = _INTRO_RE.search(rest)
    return rest[: end.start() if end else 2000].strip()[:2000]


def _table_text(rows: list[list]) -> str:
    lines = []
    for row in rows:
        cells = [re.sub(r"\s+", " ", str(c)).strip() if c is not None else "" for c in row]
        if any(cells):
            lines.append(" | ".join(cells))
    return "\n".join(lines)


def _tables_pdfplumber(path: str, page_no: int) -> list[str]:
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(path) as pdf:
            return [_table_text(t) for t in pdf.pages[page_no].extract_tables() if t]
    except Exception:
        return []


def extract_pymupdf(path: str, doc_id: str, tables: bool = True, captions: bool = True, max_pages: int = 400) -> ExtractedDoc:
    pymupdf = _import_pymupdf()
    doc = pymupdf.open(path)
    try:
        if getattr(doc, "needs_pass", False) or getattr(doc, "is_encrypted", False):
            raise ValueError("PDF cifrado")
        pages: list[Page] = []
        table_pages: list[Page] = []
        caption_pages: list[Page] = []
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            text = page.get_text("text", sort=True) or ""
            pages.append(Page(doc_id, i, text))
            if captions:
                lines = text.splitlines()
                for j, line in enumerate(lines):
                    if _CAPTION_RE.match(line):
                        cap = line.strip()
                        if j + 1 < len(lines) and len(cap) < 120 and lines[j + 1].strip():
                            cap = f"{cap} {lines[j + 1].strip()}"
                        caption_pages.append(Page(doc_id, i, cap))
            if tables:
                found: list[str] = []
                try:
                    finder = page.find_tables()
                    for tab in finder.tables:
                        found.append(_table_text(tab.extract()))
                except Exception:
                    found = _tables_pdfplumber(path, i)
                for t in found:
                    if t.count("|") >= 2 and len(t) >= 20:
                        table_pages.append(Page(doc_id, i, t, is_table=True))

        meta_title = (doc.metadata or {}).get("title", "") or ""
        title = meta_title.strip()
        if len(title) < 10 or _BAD_TITLE_RE.search(title):
            title = _title_from_fonts(doc[0]) if len(doc) else ""
        if not title:
            title = Path(path).stem.replace("_", " ")
        head = "\n".join(p.text for p in pages[:2])
        return ExtractedDoc(doc_id, path, title, _abstract(head), pages, table_pages, caption_pages)
    finally:
        doc.close()


# --------------------------------------------------------------------------------------------
# Docling (solo E0, igual que el kit)
# --------------------------------------------------------------------------------------------

_DOCLING = None


def extract_docling(path: str, doc_id: str, artifacts_path: str | None = None) -> ExtractedDoc:
    global _DOCLING
    if _DOCLING is None:
        from docling.datamodel.base_models import InputFormat  # type: ignore
        from docling.datamodel.pipeline_options import PdfPipelineOptions  # type: ignore
        from docling.document_converter import DocumentConverter, PdfFormatOption  # type: ignore

        opts = PdfPipelineOptions(do_ocr=False, do_table_structure=False)
        if artifacts_path and Path(artifacts_path).exists():
            opts.artifacts_path = artifacts_path
        _DOCLING = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    md = _DOCLING.convert(path).document.export_to_markdown()
    title = next((ln.lstrip("# ").strip() for ln in md.splitlines() if ln.startswith("#")), Path(path).stem)
    return ExtractedDoc(doc_id, path, title, _abstract(md), [Page(doc_id, 0, md)])


# --------------------------------------------------------------------------------------------
# Pool de procesos
# --------------------------------------------------------------------------------------------


def _extract_one(args: tuple) -> ExtractedDoc | tuple[str, str]:
    path, doc_id, extractor, tables, captions, max_pages, artifacts = args
    try:
        if extractor == "docling":
            doc = extract_docling(path, doc_id, artifacts)
        else:
            doc = extract_pymupdf(path, doc_id, tables, captions, max_pages)
        if sum(len(p.text) for p in doc.pages) < MIN_DOC_CHARS:
            return (path, "sin texto")
        return doc
    except Exception as exc:  # cualquier PDF dañado se omite
        return (path, f"{type(exc).__name__}: {exc}")


class ExtractionJob:
    """Extracción en curso. Se crea antes de cargar OLMo y se recoge después."""

    def __init__(self, corpus_dir: str, cfg, root: Path) -> None:
        self.paths = list_pdfs(corpus_dir)
        self.cfg = cfg
        self.skipped: list[tuple[str, str]] = []
        self._executor: ProcessPoolExecutor | None = None
        self._futures: list[tuple[str, Future]] = []
        artifacts = str(Path(root) / "models" / "docling")
        args = [
            (str(p), doc_id_for(p, corpus_dir), cfg.extractor, cfg.tables, cfg.captions, cfg.max_pages, artifacts)
            for p in self.paths
        ]
        self._args = args
        workers = max(1, min(cfg.workers, os.cpu_count() or 1, len(args) or 1))
        self._inline = workers == 1 or len(args) <= 2
        if args and not self._inline:
            ctx = mp.get_context("fork" if sys.platform.startswith("linux") else "spawn")
            self._executor = ProcessPoolExecutor(max_workers=workers, mp_context=ctx)
            self._futures = [(a[0], self._executor.submit(_extract_one, a)) for a in args]

    def collect(self) -> list[ExtractedDoc]:
        docs: list[ExtractedDoc] = []
        if self._inline:
            results = [(a[0], _extract_one(a)) for a in self._args]
        else:
            results = []
            for path, fut in self._futures:
                start = time.monotonic()
                try:
                    results.append((path, fut.result(timeout=self.cfg.doc_timeout_s)))
                except Exception as exc:
                    results.append((path, (path, f"tiempo agotado o error: {type(exc).__name__}")))
                    if time.monotonic() - start >= self.cfg.doc_timeout_s:
                        fut.cancel()
            assert self._executor is not None
            self._executor.shutdown(wait=False, cancel_futures=True)
        for path, res in results:
            if isinstance(res, ExtractedDoc):
                docs.append(res)
            else:
                self.skipped.append(res)
                log.warning("PDF omitido %s: %s", path, res[1])
        return docs
