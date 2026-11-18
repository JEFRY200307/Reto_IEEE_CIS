import pytest

from dsqa.index.dense import DenseIndex, HashEncoder
from dsqa.index.lexical import LexicalIndex
from dsqa.retrieval.fusion import OWA, RRF, OWAParams
from dsqa.retrieval.query import fix_typos, is_numeric
from dsqa.retrieval.rerank import OverlapScorer, Reranker
from dsqa.text import tokenize
from dsqa.types import Candidate


def test_tokenize_technical_terms():
    toks = tokenize("Be-7 inventory in the ICS")
    assert {"be-7", "be7", "inventory", "ics"} <= set(toks)
    assert "the" not in toks


def test_bm25_ranks_exact_terms_first():
    idx = LexicalIndex(["the cold trap removes tritium", "ICS bypass ratio is 5 percent", "beam diagnostics"])
    hits = idx.search("ICS bypass", 3)
    assert hits[0].chunk_id == 1 and hits[0].ranks["bm25"] == 1


def test_dense_self_retrieval_and_subset():
    texts = ["lithium loop heat exchanger", "window size for forecasting", "statin therapy outcomes"]
    idx = DenseIndex(HashEncoder(), texts)
    assert idx.search(texts[1], 1)[0].chunk_id == 1
    import numpy as np

    assert all(c.chunk_id == 2 for c in idx.search("forecasting", 3, np.array([2])))


def _lists():
    a = [Candidate(1, {"bm25": 9.0}, {"bm25": 1}), Candidate(2, {"bm25": 5.0}, {"bm25": 2}), Candidate(3, {"bm25": 1.0}, {"bm25": 3})]
    b = [Candidate(2, {"dense": 0.9}, {"dense": 1}), Candidate(3, {"dense": 0.5}, {"dense": 2}), Candidate(4, {"dense": 0.1}, {"dense": 3})]
    return {"bm25": a, "dense": b}


def test_rrf_matches_manual_formula():
    fused = {c.chunk_id: c.scores["fused"] for c in RRF(60).fuse(_lists(), 10)}
    assert fused[2] == pytest.approx(1 / 62 + 1 / 61)
    assert fused[1] == pytest.approx(1 / 61)
    assert max(fused, key=fused.get) == 2


@pytest.mark.parametrize("w,agg", [([1.0, 0.0], max), ([0.0, 1.0], min), ([0.5, 0.5], lambda x: sum(x) / 2)])
def test_owa_extremes(w, agg):
    owa = OWA(OWAParams(w=w))
    lists = _lists()
    mu = owa.memberships(lists)
    for c in owa.fuse(lists, 10):
        values = [mu.get(c.chunk_id, {}).get(n, 0.0) for n in lists]
        assert c.scores["fused"] == pytest.approx(agg(values))


def test_owa_rejects_bad_weights():
    with pytest.raises(ValueError):
        OWA(OWAParams(w=[0.7, 0.7]))


def test_mmr_removes_near_duplicates():
    texts = ["lithium loop bypass ratio ICS", "lithium loop bypass ratio ICS", "nitrogen trap temperature", "heat exchanger flow"]
    cands = [Candidate(i, {"fused": 1.0}) for i in range(4)]
    out = Reranker(OverlapScorer()).rerank("lithium loop ICS bypass", cands, texts, top_n=2, lam=0.5)
    assert {c.chunk_id for c in out} != {0, 1}


def test_typo_fix_and_numeric_detection():
    vocab = {"volume", "main", "building", "ics"}
    assert "volume" in fix_typos("What will be volumen of the main building", vocab, 80)
    assert "ICS" in fix_typos("the ICS branch", vocab, 90)
    assert is_numeric("What would be the radioactive decay constant of Be7 if we round its half life in days?")
    assert not is_numeric('What does a "destructive" beam diagnostic do to the beam it measures?')
