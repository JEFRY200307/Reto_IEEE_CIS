import random

import pytest

from dsqa.generate.llm import EchoLLM, postprocess
from dsqa.generate.pot import run_sandboxed, solve, validate
from dsqa.generate.prompts import Prompts
from dsqa.types import Candidate, Query, Signals
from dsqa.verify.qfcm import QFCMDecider, QFCMParams
from dsqa.verify.signals import compute_signals, judge_sufficiency
from dsqa.verify.threshold import ThresholdDecider

from pathlib import Path

PROMPTS = Path(__file__).resolve().parents[2] / "resources" / "prompts"


def test_signals_in_range_and_single_candidate():
    q = Query("q", "q", key_terms=["lithium", "loop"])
    rng = random.Random(0)
    for _ in range(50):
        ranked = [Candidate(i, {"rerank": rng.random()}) for i in range(rng.randint(1, 5))]
        lists = {"bm25": ranked[:3], "dense": ranked[1:]}
        s = compute_signals(q, ranked, lists, {c.chunk_id: "lithium text" for c in ranked})
        for v in (s.s1_top1, s.s2_gap, s.s3_agreement, s.s4_coverage):
            assert 0.0 <= v <= 1.0
    one = compute_signals(q, [Candidate(0, {"rerank": 0.8})], {}, {0: "x"})
    assert one.s2_gap == pytest.approx(0.8)


def test_threshold_decider_table():
    d = ThresholdDecider(0.7, 0.3, 0.5)
    assert d.decide(Signals(0.8, 0, 0, 0.6)).label == "correct"
    assert d.decide(Signals(0.2, 0, 0, 0.9)).label == "incorrect"
    assert d.decide(Signals(0.8, 0, 0, 0.2)).label == "ambiguous"
    assert d.decide(Signals(0.7, 0, 0, 0.5)).label == "correct"  # bordes inclusivos


def test_qfcm_limits_and_extremes():
    dec = QFCMDecider(QFCMParams())
    assert dec.decide(Signals(1, 1, 1, 1, 1)).label == "correct"
    assert dec.decide(Signals(0, 0, 0, 0, 0)).label == "incorrect"
    p0 = QFCMParams(phi=0.0)
    a = QFCMDecider(p0).activations(Signals(0.3, 0.2, 0.1, 0.4, 0.5))
    assert list(a[:5]) == pytest.approx([0.3, 0.2, 0.1, 0.4, 0.5]) and a[5] == pytest.approx(0.0)


def test_qfcm_rejects_out_of_bounds():
    p = QFCMParams()
    p.edges["C1->C6"] = 0.99
    with pytest.raises(ValueError):
        p.validate()


def test_judge_s5_uses_probabilities():
    assert judge_sufficiency(EchoLLM(), Prompts(PROMPTS), "q", ["evidence"], 500) == pytest.approx(0.7)


def test_pot_blocks_dangerous_code():
    for code in ["import os\nanswer = 1", "answer = open('x').read()", "while True:\n    pass",
                 "answer = ().__class__.__bases__"]:
        with pytest.raises(ValueError):
            validate(code)


def test_pot_computes_decay_constant():
    code = validate("import math\nT = 53\nlam = math.log(2) / T\nanswer = f'{lam:.5f} day^-1'")
    assert run_sandboxed(code, 10) == "0.01308 day^-1"


def test_pot_timeout_and_error_return_none():
    assert run_sandboxed("x = 1 / 0", 10) is None
    assert run_sandboxed("answer = sum(range(10**12))", 1) is None


def test_pot_solve_with_echo_llm():
    r = solve(EchoLLM(), Prompts(PROMPTS), "How many?", "[Doc: t, p. 1]\nvalue 42", 10, 64)
    assert r is not None and r.value == "42"


def test_postprocess_cleans_template_tokens():
    assert postprocess("<|assistant|>  Answer: **5 %**  of the flow\n\n\n\nok") == "**5 %** of the flow\n\nok"
    assert postprocess("<think>hidden</think>The value is 3.") == "The value is 3."


def test_prompts_do_not_target_the_judge():
    for path in PROMPTS.glob("*.txt"):
        if path.stem in ("judge_local", "judge_s5"):
            continue
        text = path.read_text(encoding="utf-8").lower()
        assert "judge" not in text and "grader" not in text and "mark this" not in text
