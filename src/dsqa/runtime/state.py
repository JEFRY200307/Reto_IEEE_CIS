"""Inicialización perezosa, paralela y cacheada de todo lo costoso (SPEC-003, ADR-03, ADR-04)."""

from __future__ import annotations

import hashlib
import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np

from ..generate.prompts import Prompts
from ..index.dense import DenseIndex, HashEncoder, SentenceTransformerEncoder
from ..index.lexical import LexicalIndex
from ..index.titles import TitleIndex
from ..ingest.chunk import IdGen, chunk_fixed, chunk_section
from ..ingest.clean import clean_doc
from ..ingest.enrich import DomainLexicon, enrich, to_document
from ..ingest.extract import ExtractionJob
from ..retrieval.fusion import Fusion, make_fusion
from ..retrieval.query import load_glossary
from ..retrieval.rerank import CrossEncoderScorer, OverlapScorer, Reranker
from ..types import Chunk, Document
from ..verify.actions import make_decider
from ..verify.threshold import Decider
from .clock import CLOCK
from .config import Config, resolve_path

log = logging.getLogger("dsqa.state")

# Sustituciones para pruebas: {"llm": f(model_id, gcfg), "encoder": f(cfg, root), "scorer": f(cfg, root)}
FACTORIES: dict[str, Callable[..., Any]] = {}

_LLM_CACHE: dict[tuple, Any] = {}
_RES_CACHE: dict[tuple, "Resources"] = {}
_LOCK = threading.Lock()


@dataclass
class Resources:
    root: Path
    corpus_dir: str
    documents: dict[str, Document] = field(default_factory=dict)
    chunks: list[Chunk] = field(default_factory=list)
    parents: list[Chunk] = field(default_factory=list)
    doc_chunks: dict[str, np.ndarray] = field(default_factory=dict)
    lexical: LexicalIndex | None = None
    dense: DenseIndex | None = None
    titles: TitleIndex | None = None
    reranker: Reranker | None = None
    llm: Any = None
    glossary: dict[str, list[str]] = field(default_factory=dict)
    lexicon: DomainLexicon = field(default_factory=lambda: DomainLexicon.load(None))
    prompts: Prompts | None = None
    fusion: Fusion | None = None
    decider: Decider | None = None
    init_errors: list[str] = field(default_factory=list)
    skipped_docs: list[tuple[str, str]] = field(default_factory=list)
    _vocab: set[str] | None = None

    @property
    def vocabulary(self) -> set[str]:
        if self._vocab is None:
            self._vocab = self.lexical.vocabulary if self.lexical else set()
        return self._vocab


# ------------------------------------------------------------------------------------------
# Fábricas
# ------------------------------------------------------------------------------------------


def get_llm(model_id: str, cfg: Config) -> Any:
    key = (model_id, cfg.generate.quantization, cfg.generate.attn_implementation, os.environ.get("DSQA_LLM_BACKEND", "hf"))
    with _LOCK:
        if key in _LLM_CACHE:
            return _LLM_CACHE[key]
    if "llm" in FACTORIES:
        llm = FACTORIES["llm"](model_id, cfg.generate)
    else:
        from ..generate.llm import load_llm

        llm = load_llm(model_id, cfg.generate)
    with _LOCK:
        _LLM_CACHE[key] = llm
    return llm


def make_encoder(cfg: Config, root: Path):
    if "encoder" in FACTORIES:
        return FACTORIES["encoder"](cfg, root)
    if os.environ.get("DSQA_ENCODER_BACKEND", "").lower() == "hash":
        return HashEncoder()
    path = resolve_path(root, cfg.index.embedder)
    if path is None or not path.exists():
        raise FileNotFoundError(f"no existe el embedder en {path} (offline/download_models.py)")
    ic = cfg.index
    return SentenceTransformerEncoder(path, ic.device, ic.batch_size, ic.fp16, ic.query_instruction, ic.max_seq_length)


def make_reranker(cfg: Config, root: Path) -> Reranker:
    if "scorer" in FACTORIES:
        return Reranker(FACTORIES["scorer"](cfg, root))
    if os.environ.get("DSQA_RERANKER_BACKEND", "").lower() == "overlap":
        return Reranker(OverlapScorer())
    path = resolve_path(root, cfg.rerank.model)
    if path is None or not path.exists():
        raise FileNotFoundError(f"no existe el reranker en {path} (offline/download_models.py)")
    return Reranker(CrossEncoderScorer(path, cfg.rerank.batch_size, cfg.rerank.max_length))


# ------------------------------------------------------------------------------------------
# Construcción
# ------------------------------------------------------------------------------------------


def _cfg_key(cfg: Config) -> str:
    return hashlib.sha1(cfg.model_dump_json().encode()).hexdigest()[:16]


def _safe(errors: list[str], name: str, fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except Exception as exc:
        msg = f"{name}: {type(exc).__name__}: {exc}"
        log.error("inicialización: %s", msg)
        errors.append(msg)
        return None


def build_chunks(raw_docs, cfg: Config, lexicon: DomainLexicon) -> tuple[dict[str, Document], list[Chunk], list[Chunk]]:
    ic = cfg.ingest
    ids = IdGen()
    documents: dict[str, Document] = {}
    children: list[Chunk] = []
    parents: list[Chunk] = []
    for raw in raw_docs:
        doc = clean_doc(raw, ic.clean_steps)
        meta = to_document(doc, lexicon)
        documents[meta.doc_id] = meta
        try:
            if ic.chunker == "fixed":
                cs = chunk_fixed(doc, ids, ic.fixed_chars, ic.fixed_overlap, side=ic.tables or ic.captions)
            else:
                cs = chunk_section(doc, ids, ic.child_chars, ic.parent_chars, ic.overlap)
        except Exception as exc:
            log.warning("chunking por sección falló en %s (%s): uso fijo", raw.path, exc)
            cs = chunk_fixed(doc, ids, ic.fixed_chars, ic.fixed_overlap)
        children.extend(enrich(cs.children, meta, ic.enrich))
        parents.extend(cs.parents)
    for i, c in enumerate(children):  # chunk_id == posición
        c.chunk_id = i
    return documents, children, parents


def build_resources(corpus_dir: str, model_id: str | None, cfg: Config, root: Path) -> Resources:
    root = Path(root)
    res = Resources(root=root, corpus_dir=corpus_dir)
    errors = res.init_errors

    # 1. La extracción arranca primero: en Linux hace fork antes de que exista cualquier hilo.
    job = _safe(errors, "extracción", lambda: ExtractionJob(corpus_dir, cfg.ingest, root))

    # 2. OLMo en paralelo con la ingesta (ADR-04).
    llm_box: dict[str, Any] = {}

    def _load() -> None:
        with CLOCK.stage("init_llm"):
            llm_box["llm"] = _safe(errors, "llm", lambda: get_llm(model_id, cfg))

    thread = None
    if model_id:
        if cfg.runtime.parallel_init:
            thread = threading.Thread(target=_load, name="dsqa-llm-loader", daemon=True)
            thread.start()
        else:
            _load()

    # 3. Ingesta → chunks.
    res.lexicon = DomainLexicon.load(resolve_path(root, cfg.ingest.domain_lexicon))
    with CLOCK.stage("init_ingest"):
        raw_docs = job.collect() if job else []
        res.skipped_docs = job.skipped if job else []
        chunked = _safe(errors, "chunking", lambda: build_chunks(raw_docs, cfg, res.lexicon))
    if chunked:
        res.documents, res.chunks, res.parents = chunked
    by_doc: dict[str, list[int]] = {}
    for c in res.chunks:
        by_doc.setdefault(c.doc_id, []).append(c.chunk_id)
    res.doc_chunks = {d: np.asarray(v, dtype=np.int64) for d, v in by_doc.items()}
    texts = [c.text for c in res.chunks]

    # 4. Índices. BM25 siempre (es barato y es el respaldo N2).
    with CLOCK.stage("init_index"):
        res.lexical = _safe(errors, "bm25", lambda: LexicalIndex(texts, cfg.index.bm25_k1, cfg.index.bm25_b))
        if cfg.index.titles or cfg.retrieval.detect_paper:
            res.titles = _safe(errors, "títulos", lambda: TitleIndex(list(res.documents.values())))
        if "dense" in cfg.retrieval.retrievers and texts:
            res.dense = _safe(errors, "denso", lambda: DenseIndex(make_encoder(cfg, root), texts))

    # 5. Resto.
    if thread is not None:
        thread.join()
    res.llm = llm_box.get("llm")
    if cfg.rerank.enabled:
        res.reranker = _safe(errors, "reranker", lambda: make_reranker(cfg, root))
    res.glossary = _safe(errors, "glosario", lambda: load_glossary(resolve_path(root, cfg.retrieval.glossary))) or {}
    res.prompts = _safe(errors, "prompts", lambda: Prompts(resolve_path(root, cfg.generate.prompts_dir)))
    res.fusion = _safe(errors, "fusión", lambda: make_fusion(cfg, root))
    res.decider = _safe(errors, "decisor", lambda: make_decider(cfg, root))
    log.info("listo: %d documentos, %d chunks, %d padres, %d omitidos, errores=%s",
             len(res.documents), len(res.chunks), len(res.parents), len(res.skipped_docs), errors)
    return res


def get_or_init(corpus_dir: str, model_id: str | None, cfg: Config, root: Path) -> Resources:
    key = (str(Path(corpus_dir).resolve()) if corpus_dir else "", model_id, _cfg_key(cfg), str(root))
    if key not in _RES_CACHE:
        _RES_CACHE[key] = build_resources(corpus_dir, model_id, cfg, root)
    return _RES_CACHE[key]


def clear_caches(keep_llm: bool = True) -> None:
    _RES_CACHE.clear()
    if not keep_llm:
        _LLM_CACHE.clear()
