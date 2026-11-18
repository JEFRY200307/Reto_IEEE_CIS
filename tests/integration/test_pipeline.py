"""Pipeline completo E0-E6 con modelos simulados (EchoLLM, HashEncoder, OverlapScorer)."""

import importlib.util
import inspect
import json
from pathlib import Path

import pytest

from dsqa.runtime import state
from dsqa.runtime.config import load_config
from dsqa.runtime.safety import answer_with_config

REPO = Path(__file__).resolve().parents[2]
QUESTIONS = [
    "What is the bypass ratio of the ICS Branch of the DONES Li loop?",
    "What would be the radioactive decay constant of Be7 if we round its half life in days to the nearest integer?",
    "In WinStat, what window size is recommended for L = 512?",
]


def _cfg(name: str):
    cfg = load_config(REPO / "configs" / f"{name}.yaml")
    if cfg.ingest.extractor == "docling":  # Docling no está en la laptop: misma E0 con PyMuPDF
        cfg = cfg.model_copy(update={"ingest": cfg.ingest.model_copy(update={"extractor": "pymupdf", "workers": 1})})
    return cfg.model_copy(update={"ingest": cfg.ingest.model_copy(update={"workers": 1})})


@pytest.mark.parametrize("name", ["e0", "e1", "e2", "e3", "e4", "e5", "e6"])
def test_strategy_answers_every_question(name, corpus_dir, fake_models):
    cfg = _cfg(name)
    for q in QUESTIONS:
        trace: dict = {}
        out = answer_with_config(q, str(corpus_dir), "fake/model", cfg, REPO, trace)
        assert isinstance(out, str) and out.strip()
        assert trace["level"].startswith("N0"), trace.get("errors")
        assert trace.get("ranked"), "debería haber evidencia recuperada"
        if cfg.verify.enabled:
            assert trace["verification"], "E4+ registra la verificación"


def test_initialization_happens_once(corpus_dir, fake_models, monkeypatch):
    calls = []
    original = state.build_resources
    monkeypatch.setattr(state, "build_resources", lambda *a, **k: calls.append(1) or original(*a, **k))
    cfg = _cfg("e2")
    for q in QUESTIONS:
        answer_with_config(q, str(corpus_dir), "fake/model", cfg, REPO)
    assert len(calls) == 1


def test_e3_detects_named_paper_and_glossary(corpus_dir, fake_models):
    trace: dict = {}
    answer_with_config(QUESTIONS[2], str(corpus_dir), "fake/model", _cfg("e3"), REPO, trace)
    assert trace["named_doc"] is not None
    assert all("WinStat" in r["text"] or r["doc_id"] for r in trace["ranked"][:3])
    trace2: dict = {}
    answer_with_config(QUESTIONS[0], str(corpus_dir), "fake/model", _cfg("e3"), REPO, trace2)
    assert "Impurity Control System" in trace2["expansions"]
    assert "5 %" in json.dumps(trace2["ranked"][:3])


def test_failure_in_dense_index_degrades_but_answers(corpus_dir, fake_models, monkeypatch):
    def broken(cfg, root):
        raise RuntimeError("embedder roto")

    monkeypatch.setitem(state.FACTORIES, "encoder", broken)
    trace: dict = {}
    out = answer_with_config(QUESTIONS[0], str(corpus_dir), "fake/model", _cfg("e2"), REPO, trace)
    assert out.strip()
    res = next(iter(state._RES_CACHE.values()))
    assert res.dense is None and any("denso" in e for e in res.init_errors)


def test_missing_corpus_uses_zero_shot(tmp_path, fake_models):
    trace: dict = {}
    out = answer_with_config(QUESTIONS[0], str(tmp_path / "no-existe"), "fake/model", _cfg("e4"), REPO, trace)
    assert out.strip() and trace["level"].startswith("N3")


def test_no_llm_returns_fixed_text(corpus_dir, fake_models, monkeypatch):
    def broken(model_id, gcfg):
        raise RuntimeError("sin GPU")

    monkeypatch.setitem(state.FACTORIES, "llm", broken)
    trace: dict = {}
    out = answer_with_config(QUESTIONS[0], str(corpus_dir), "fake/model", _cfg("e1"), REPO, trace)
    assert out.strip() and trace["level"].startswith("N4")


def test_oom_retries_with_smaller_context(corpus_dir, fake_models, monkeypatch):
    from dsqa.generate.llm import EchoLLM

    class OutOfMemoryError(RuntimeError):
        pass

    class OOMOnce(EchoLLM):
        calls = 0

        def generate(self, messages, max_new_tokens):
            OOMOnce.calls += 1
            if OOMOnce.calls == 1:
                raise OutOfMemoryError("CUDA out of memory")
            return super().generate(messages, max_new_tokens)

    monkeypatch.setitem(state.FACTORIES, "llm", lambda m, g: OOMOnce())
    trace: dict = {}
    out = answer_with_config(QUESTIONS[0], str(corpus_dir), "fake/model", _cfg("e1"), REPO, trace)
    assert out.strip() and trace["level"].startswith("N0") and any("OutOfMemory" in e for e in trace["errors"])


def test_main_contract(corpus_dir, fake_models, monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("submission_main", REPO / "submission" / "main.py")
    main = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main)
    sig = inspect.signature(main.answer)
    assert list(sig.parameters) == ["question", "corpus_dir", "model_id"]
    monkeypatch.setenv("DSQA_CONFIG", str(tmp_path / "missing.yaml"))  # config ausente: valores por defecto
    for q in ["", "x" * 10000, "$\\lambda = \\ln 2 / T_{1/2}$", None, "¿Qué es ñ? ∑∫"]:
        out = main.answer(q, str(corpus_dir), "fake/model")
        assert isinstance(out, str) and out.strip()
