"""Orquestador de las 5 etapas: consulta → recuperación → verificación → contexto → generación."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from .context.builder import build_context
from .generate.llm import postprocess
from .generate.pot import solve
from .retrieval.query import analyze
from .retrieval.search import search
from .runtime.clock import Mode
from .types import Candidate, Evidence, Query, Verdict
from .verify.actions import run_verification
from .verify.threshold import NoVerify

if TYPE_CHECKING:
    from .runtime.config import Config
    from .runtime.state import Resources

LEVELS = ("N0 completo", "N1 sin verificación ni PoT", "N2 solo BM25", "N3 zero-shot", "N4 texto fijo")


def retrieve(query: Query, res: "Resources", cfg: "Config", use_doc_filter: bool = True,
             text: str | None = None) -> tuple[list[Candidate], dict[str, list[Candidate]]]:
    """Búsqueda → fusión → reranking."""
    lists = search(query, res, cfg, use_doc_filter, text)
    if not lists:
        return [], {}
    fused = res.fusion.fuse(lists, cfg.fusion.top_n) if res.fusion else next(iter(lists.values()))
    if res.reranker is not None and cfg.rerank.enabled and fused:
        texts = [res.chunks[c.chunk_id].text for c in fused]
        vectors = res.dense.embeddings[[c.chunk_id for c in fused]] if res.dense is not None else None
        fused = res.reranker.rerank(query.original, fused, texts, cfg.rerank.top_n, cfg.rerank.mmr_lambda, vectors)
    return fused, lists


def _answer_kind(query: Query, cfg: "Config", has_context: bool) -> str:
    if not has_context:
        return "zero_shot"
    if cfg.generate.style == "generic":
        return "answer_generic"
    dones, ai = query.domain.get("DONES", 0.0), query.domain.get("AI", 0.0)
    if dones == 0 and ai == 0:
        return "answer_generic"
    return "answer_dones" if dones >= ai else "answer_ai"


def _max_new_tokens(cfg: "Config", mode: Mode) -> int:
    g = cfg.generate
    return {Mode.NORMAL: g.max_new_tokens, Mode.FAST: min(g.max_new_tokens, g.max_new_tokens_fast),
            Mode.EMERGENCY: min(g.max_new_tokens, g.max_new_tokens_emergency)}[mode]


def _trace_candidates(cands: list[Candidate], res: "Resources", n: int, with_text: bool) -> list[dict]:
    out = []
    for c in cands[:n]:
        ch = res.chunks[c.chunk_id]
        item: dict[str, Any] = {"chunk_id": c.chunk_id, "doc_id": ch.doc_id, "page": ch.page + 1,
                                "scores": {k: round(v, 5) for k, v in c.scores.items()}}
        if with_text:
            item["text"] = ch.raw[:1200]
        out.append(item)
    return out


def answer_question(question: str, res: "Resources", cfg: "Config", mode: Mode, level: int,
                    ctx_factor: float = 1.0, trace: dict | None = None) -> str:
    llm, prompts = res.llm, res.prompts
    if llm is None or prompts is None:
        raise RuntimeError("sin LLM o sin prompts")
    t0 = time.monotonic()
    timings: dict[str, float] = {}
    query = analyze(question, res, cfg)
    timings["query"] = time.monotonic() - t0
    max_new = _max_new_tokens(cfg, mode)
    budget = int(cfg.context.max_tokens * ctx_factor)

    evidence: Evidence | None = None
    if level <= 2 and res.chunks:
        t = time.monotonic()
        if level == 2:
            hits = res.lexical.search(query.search_text, 3) if res.lexical else []
            evidence = Evidence(hits, NoVerify().decide(None))  # type: ignore[arg-type]
            max_new = min(max_new, cfg.generate.max_new_tokens_emergency)
        elif level == 1:
            ranked, lists = retrieve(query, res, cfg)
            evidence = Evidence(ranked, NoVerify().decide(None), lists=lists)  # type: ignore[arg-type]
        else:
            evidence = run_verification(
                query, res, cfg, res.decider or NoVerify(),
                lambda q, use_filter, text: retrieve(q, res, cfg, use_filter, text), mode, prompts,
            )
        timings["retrieval_verify"] = time.monotonic() - t

    context, ctx_tokens, used = "", 0, []
    if evidence is not None and evidence.candidates:
        context, ctx_tokens, used = build_context(
            evidence, res, cfg, mode, llm.count_tokens, budget, limit_override=3 if level >= 1 else None
        )

    t = time.monotonic()
    answer = None
    pot_info = None
    g = cfg.generate
    if level == 0 and g.pot.enabled and mode == Mode.NORMAL and query.is_numeric and context:
        result = solve(llm, prompts, question, context, g.pot.timeout_s, g.pot.max_new_tokens)
        if result is not None:
            pot_info = {"code": result.code, "value": result.value}
            msgs = prompts.render("pot_answer", question=question, context=context, result=result.value)
            answer = postprocess(llm.generate(msgs, max_new))
    if answer is None:
        kind = _answer_kind(query, cfg, bool(context))
        answer = postprocess(llm.generate(prompts.render(kind, question=question, context=context), max_new))
    timings["generate"] = time.monotonic() - t

    if trace is not None:
        trace.update({
            "level": LEVELS[level], "mode": mode.value,
            "domain_membership": {k: round(v, 3) for k, v in query.domain.items()},
            "normalized": query.normalized, "expansions": query.expansions, "named_doc": query.named_doc,
            "is_numeric": query.is_numeric, "key_terms": query.key_terms, "context_tokens": ctx_tokens,
            "context_keys": used, "pot": pot_info, "timings": {k: round(v, 3) for k, v in timings.items()},
        })
        if evidence is not None:
            trace["ranked"] = _trace_candidates(evidence.candidates, res, 50, True)
            trace["lists"] = {k: _trace_candidates(v, res, cfg.retrieval.top_k, False) for k, v in evidence.lists.items()}
            trace["verification"] = evidence.history
            trace["verdict"] = evidence.verdict.label if isinstance(evidence.verdict, Verdict) else None
    return answer
