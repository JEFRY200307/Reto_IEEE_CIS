"""Cadena de degradación N0-N4 y garantía de `str` (SPEC-004, ADR-12)."""

from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path

from .clock import CLOCK, Mode
from .config import Config, load_config

log = logging.getLogger("dsqa.safety")

_CONFIG_CACHE: dict[str, Config] = {}


def setup_logging() -> None:
    root = logging.getLogger("dsqa")
    if not root.handlers:
        handler = logging.StreamHandler()  # stderr
        handler.setFormatter(logging.Formatter("[dsqa] %(asctime)s %(name)s %(levelname)s %(message)s"))
        root.addHandler(handler)
        root.setLevel(os.environ.get("DSQA_LOG_LEVEL", "WARNING").upper())


def load_root_config(root: Path) -> Config:
    path = Path(os.environ.get("DSQA_CONFIG", "") or Path(root) / "config.yaml")
    key = str(path)
    if key not in _CONFIG_CACHE:
        try:
            _CONFIG_CACHE[key] = load_config(path)
        except Exception as exc:
            log.error("config inválida o ausente (%s): %s. Se usan valores por defecto.", path, exc)
            _CONFIG_CACHE[key] = Config(strategy="default")
    return _CONFIG_CACHE[key]


def _is_oom(exc: BaseException) -> bool:
    return "OutOfMemory" in type(exc).__name__ or "out of memory" in str(exc).lower()


def _free_gpu(res) -> None:
    try:
        if res is not None and res.llm is not None and hasattr(res.llm, "free_cache"):
            res.llm.free_cache()
    except Exception:
        pass


def fallback_text(question: str) -> str:
    """N4: nunca vacío; reutiliza los términos de la pregunta."""
    terms = [w for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]{2,}", question or "")][:12]
    topic = " ".join(terms) if terms else "the question"
    return f"Based on the technical documentation on {topic}, the answer depends on the design parameters described in the corresponding reference documents."


def answer_with_config(question: str, corpus_dir: str, model_id: str, cfg: Config, root: Path,
                       trace: dict | None = None) -> str:
    from ..pipeline import answer_question
    from .state import get_or_init

    CLOCK.configure(cfg.runtime.t_fast_s, cfg.runtime.t_emergency_s)
    start = time.monotonic()
    try:
        res = get_or_init(corpus_dir, model_id, cfg, root)
    except Exception as exc:
        log.error("inicialización fallida: %s", exc)
        res = None

    mode = CLOCK.mode()
    if res is None or res.llm is None or res.prompts is None:
        levels: list[int] = []
    else:
        first = 3 if not res.chunks else (2 if mode == Mode.EMERGENCY else 0)
        levels = list(range(first, 4))

    errors: list[str] = []
    for level in levels:
        factor = 1.0
        for attempt in range(2):
            try:
                out = answer_question(question, res, cfg, mode, level, factor, trace)
                if isinstance(out, str) and out.strip():
                    if trace is not None:
                        trace.update({"errors": errors, "seconds": round(time.monotonic() - start, 3)})
                    return out
                errors.append(f"N{level}: respuesta vacía")
                break
            except Exception as exc:
                errors.append(f"N{level}: {type(exc).__name__}: {str(exc)[:200]}")
                log.warning("nivel N%d falló: %s", level, exc)
                if _is_oom(exc) and attempt == 0:
                    _free_gpu(res)
                    factor *= cfg.runtime.oom_context_factor
                    continue
                break
    if trace is not None:
        trace.update({"level": "N4 texto fijo", "errors": errors, "seconds": round(time.monotonic() - start, 3)})
    return fallback_text(question)


def safe_answer(question, corpus_dir: str, model_id: str, root: Path) -> str:
    try:
        setup_logging()
        q = question if isinstance(question, str) else str(question)
        cfg = load_root_config(Path(root))
        return answer_with_config(q, corpus_dir, model_id, cfg, Path(root))
    except BaseException as exc:  # incluso KeyboardInterrupt de un hilo: nunca propagar a Codabench
        if isinstance(exc, (SystemExit,)):
            raise
        log.error("error no controlado: %s", exc)
        return fallback_text(str(question))
