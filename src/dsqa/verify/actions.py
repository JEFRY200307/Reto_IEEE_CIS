"""Acciones según el veredicto: aceptar, refinar o reintentar (SPEC-021, ADR-08, ADR-12)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from ..runtime.clock import Mode
from ..types import Candidate, Evidence, Query
from .qfcm import QFCMDecider, QFCMParams
from .signals import compute_signals, judge_sufficiency
from .threshold import Decider, NoVerify, ThresholdDecider

if TYPE_CHECKING:
    from ..generate.prompts import Prompts
    from ..runtime.config import Config
    from ..runtime.state import Resources

log = logging.getLogger("dsqa.verify")

RetrieveFn = Callable[[Query, bool, "str | None"], "tuple[list[Candidate], dict[str, list[Candidate]]]"]


def make_decider(cfg: "Config", root: Path) -> Decider:
    from ..runtime.config import resolve_path

    v = cfg.verify
    if not v.enabled or v.decider == "none":
        return NoVerify()
    if v.decider == "threshold":
        t = v.threshold
        return ThresholdDecider(t.tau_high, t.tau_low, t.kappa)
    return QFCMDecider(QFCMParams.load(resolve_path(root, v.qfcm.params_file)), v.qfcm.iterations)


def run_verification(
    query: Query,
    res: "Resources",
    cfg: "Config",
    decider: Decider,
    retrieve: RetrieveFn,
    mode: Mode,
    prompts: "Prompts | None" = None,
) -> Evidence:
    v = cfg.verify
    ranked, lists = retrieve(query, True, None)
    if not v.enabled:
        return Evidence(ranked, NoVerify().decide(None), 0, False, lists)  # type: ignore[arg-type]

    texts = {c.chunk_id: res.chunks[c.chunk_id].raw for c in ranked}
    use_s5 = "s5" in v.signals and mode == Mode.NORMAL and res.llm is not None and prompts is not None
    history: list[dict] = []
    best: Evidence | None = None
    variants = [None]  # intento 0 con la consulta normal
    attempt = 0
    while True:
        signals = compute_signals(query, ranked, lists, texts, v.agreement_topk, v.coverage_topk)
        if use_s5 and ranked:
            passages = [res.chunks[c.chunk_id].raw for c in ranked[: v.judge_topk]]
            signals.s5_judge = judge_sufficiency(res.llm, prompts, query.original, passages, v.judge_max_tokens)
        verdict = decider.decide(signals)
        history.append({"attempt": attempt, "signals": vars(signals), "verdict": verdict.label,
                        "confidence": round(verdict.confidence, 4), "memberships": verdict.memberships})
        ev = Evidence(ranked, verdict, attempt, False, lists, history)
        if best is None or verdict.confidence > best.verdict.confidence:
            best = ev

        if verdict.label == "correct":
            return _with_history(ev, history)
        if verdict.label == "ambiguous":
            ev.refined = True
            return _with_history(ev, history)
        # incorrecta
        if attempt >= v.max_retries or mode != Mode.NORMAL:
            return _with_history(best, history)
        attempt += 1
        if len(variants) == 1:
            from ..retrieval.query import reformulate

            variants = [None, *reformulate(query, res)]
        text = variants[min(attempt, len(variants) - 1)]
        try:
            ranked, lists = retrieve(query, False, text)  # sin filtro por documento
            texts.update({c.chunk_id: res.chunks[c.chunk_id].raw for c in ranked})
        except Exception as exc:
            log.warning("reintento falló: %s", exc)
            return _with_history(best, history)


def _with_history(ev: Evidence, history: list[dict]) -> Evidence:
    ev.history = history
    return ev
