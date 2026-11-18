"""Configuración de estrategias E0-E6 (SPEC-025, ADR-02).

Cada estrategia es un YAML que puede heredar de otro con `extends`. La config se valida con
pydantic: claves desconocidas o valores fuera de rango son error.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Block(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RuntimeCfg(_Block):
    t_fast_s: float = Field(3000, ge=60, le=7000)
    t_emergency_s: float = Field(3360, ge=60, le=7200)
    seed: int = 42
    parallel_init: bool = True
    oom_context_factor: float = Field(0.5, gt=0, lt=1)

    @model_validator(mode="after")
    def _order(self) -> "RuntimeCfg":
        if self.t_emergency_s <= self.t_fast_s:
            raise ValueError("runtime.t_emergency_s debe ser mayor que runtime.t_fast_s")
        return self


class IngestCfg(_Block):
    extractor: Literal["pymupdf", "docling"] = "pymupdf"
    tables: bool = True
    captions: bool = True
    clean_steps: list[Literal["ftfy", "dehyphen", "headers", "references", "whitespace"]] = Field(
        default_factory=lambda: ["ftfy", "dehyphen", "headers", "references", "whitespace"]
    )
    chunker: Literal["fixed", "section"] = "section"
    fixed_chars: int = Field(800, ge=100, le=5000)
    fixed_overlap: int = Field(150, ge=0, le=1000)
    child_chars: int = Field(600, ge=150, le=3000)
    parent_chars: int = Field(2000, ge=200, le=8000)
    overlap: int = Field(100, ge=0, le=1000)
    enrich: bool = True
    domain_lexicon: str = "resources/domain_lexicon.json"
    workers: int = Field(30, ge=1, le=64)
    doc_timeout_s: float = Field(60, ge=5, le=900)
    max_pages: int = Field(400, ge=1)

    @model_validator(mode="after")
    def _sizes(self) -> "IngestCfg":
        if self.parent_chars < self.child_chars:
            raise ValueError("ingest.parent_chars debe ser >= ingest.child_chars")
        return self


class IndexCfg(_Block):
    embedder: str = "models/embedder"
    device: Literal["cuda", "cpu", "auto"] = "auto"
    batch_size: int = Field(256, ge=1, le=4096)
    fp16: bool = True
    query_instruction: str = "Represent this sentence for searching relevant passages: "
    max_seq_length: int = Field(512, ge=32, le=8192)
    bm25_k1: float = Field(1.5, ge=0.1, le=3.0)
    bm25_b: float = Field(0.75, ge=0.0, le=1.0)
    titles: bool = False


class RetrievalCfg(_Block):
    retrievers: list[Literal["bm25", "dense"]] = Field(default_factory=lambda: ["dense"])
    top_k: int = Field(50, ge=1, le=500)
    glossary: str | None = None
    typo_fix: bool = False
    typo_threshold: float = Field(90, ge=50, le=100)
    detect_paper: bool = False
    doc_filter_threshold: float = Field(0.7, ge=0, le=1)
    min_hits: int = Field(5, ge=1, le=100)

    @model_validator(mode="after")
    def _nonempty(self) -> "RetrievalCfg":
        if not self.retrievers:
            raise ValueError("retrieval.retrievers no puede estar vacío")
        return self


class FusionCfg(_Block):
    method: Literal["none", "rrf", "owa"] = "none"
    rrf_k: int = Field(60, ge=1, le=1000)
    top_n: int = Field(50, ge=1, le=500)
    owa_params: str = "resources/owa_params.json"


class RerankCfg(_Block):
    enabled: bool = False
    model: str = "models/reranker"
    top_n: int = Field(20, ge=1, le=200)
    mmr_lambda: float = Field(0.7, ge=0, le=1)
    batch_size: int = Field(32, ge=1, le=512)
    max_length: int = Field(512, ge=64, le=2048)


class ThresholdCfg(_Block):
    tau_high: float = Field(0.7, ge=0, le=1)
    tau_low: float = Field(0.3, ge=0, le=1)
    kappa: float = Field(0.5, ge=0, le=1)

    @model_validator(mode="after")
    def _order(self) -> "ThresholdCfg":
        if self.tau_low >= self.tau_high:
            raise ValueError("verify.threshold.tau_low debe ser menor que tau_high")
        return self


class QFCMCfg(_Block):
    params_file: str = "resources/qfcm_params.json"
    iterations: int = Field(10, ge=1, le=100)


class VerifyCfg(_Block):
    enabled: bool = False
    decider: Literal["none", "threshold", "qfcm"] = "none"
    signals: list[Literal["s1", "s2", "s3", "s4", "s5"]] = Field(default_factory=lambda: ["s1", "s2", "s3", "s4"])
    judge_topk: int = Field(3, ge=1, le=10)
    judge_max_tokens: int = Field(2000, ge=200, le=8000)
    max_retries: int = Field(1, ge=0, le=2)
    ambiguous_extra_chunks: int = Field(2, ge=0, le=10)
    agreement_topk: int = Field(10, ge=1, le=100)
    coverage_topk: int = Field(3, ge=1, le=20)
    threshold: ThresholdCfg = Field(default_factory=ThresholdCfg)
    qfcm: QFCMCfg = Field(default_factory=QFCMCfg)


class ContextCfg(_Block):
    mode: Literal["budget", "topk", "threshold"] = "topk"
    max_tokens: int = Field(4000, ge=200, le=60000)
    top_k: int = Field(5, ge=1, le=50)
    min_chunks: int = Field(3, ge=1, le=50)
    max_chunks: int = Field(8, ge=1, le=50)
    min_score: float = Field(0.3, ge=0, le=1)
    neighbors: int = Field(0, ge=0, le=3)
    use_parent: bool = True


class PoTCfg(_Block):
    enabled: bool = False
    timeout_s: float = Field(5, ge=0.5, le=60)
    max_new_tokens: int = Field(256, ge=32, le=2048)


class GenerateCfg(_Block):
    prompts_dir: str = "resources/prompts"
    style: Literal["generic", "domain"] = "domain"
    max_new_tokens: int = Field(300, ge=16, le=4096)
    max_new_tokens_fast: int = Field(200, ge=16, le=4096)
    max_new_tokens_emergency: int = Field(120, ge=16, le=4096)
    attn_implementation: Literal["sdpa", "eager"] = "sdpa"
    quantization: Literal["none", "8bit", "4bit"] = "none"
    pot: PoTCfg = Field(default_factory=PoTCfg)


class Config(_Block):
    strategy: str = "custom"
    description: str = ""
    runtime: RuntimeCfg = Field(default_factory=RuntimeCfg)
    ingest: IngestCfg = Field(default_factory=IngestCfg)
    index: IndexCfg = Field(default_factory=IndexCfg)
    retrieval: RetrievalCfg = Field(default_factory=RetrievalCfg)
    fusion: FusionCfg = Field(default_factory=FusionCfg)
    rerank: RerankCfg = Field(default_factory=RerankCfg)
    verify: VerifyCfg = Field(default_factory=VerifyCfg)
    context: ContextCfg = Field(default_factory=ContextCfg)
    generate: GenerateCfg = Field(default_factory=GenerateCfg)

    @model_validator(mode="after")
    def _cross(self) -> "Config":
        if len(self.retrieval.retrievers) > 1 and self.fusion.method == "none":
            raise ValueError("con más de un buscador, fusion.method debe ser rrf u owa")
        if self.verify.enabled and self.verify.decider == "none":
            raise ValueError("verify.enabled requiere verify.decider threshold o qfcm")
        if "s5" in self.verify.signals and self.verify.decider != "qfcm":
            raise ValueError("la señal s5 (juez OLMo) solo se usa con el decisor qfcm")
        return self


BLOCKS = ("runtime", "ingest", "index", "retrieval", "fusion", "rerank", "verify", "context", "generate")


def _deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_raw(path: str | Path, _seen: tuple[Path, ...] = ()) -> dict[str, Any]:
    """Lee un YAML resolviendo `extends` de forma recursiva (relativo al archivo)."""
    path = Path(path).resolve()
    if path in _seen:
        raise ValueError(f"herencia circular en configs: {' -> '.join(p.name for p in (*_seen, path))}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} no contiene un mapa YAML")
    parent = data.pop("extends", None)
    if parent:
        base = load_raw(path.parent / parent, (*_seen, path))
        data = _deep_merge(base, data)
    return data


def load_config(path: str | Path) -> Config:
    return Config.model_validate(load_raw(path))


def resolve_to_file(cfg: Config, out: str | Path) -> None:
    """Escribe la config ya resuelta, sin herencia (para el zip)."""
    Path(out).write_text(
        yaml.safe_dump(cfg.model_dump(mode="json"), sort_keys=False, allow_unicode=True), encoding="utf-8"
    )


def diff_blocks(a: Config, b: Config) -> set[str]:
    da, db = a.model_dump(), b.model_dump()
    return {k for k in BLOCKS if da[k] != db[k]}


def resolve_path(root: str | Path, value: str | None) -> Path | None:
    if not value:
        return None
    p = Path(value)
    return p if p.is_absolute() else Path(root) / p
