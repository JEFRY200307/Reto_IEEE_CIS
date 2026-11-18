"""Fixtures: mini-corpus de PDFs generado al vuelo y modelos simulados (sin GPU ni red)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dsqa.generate.llm import EchoLLM  # noqa: E402
from dsqa.index.dense import HashEncoder  # noqa: E402
from dsqa.retrieval.rerank import OverlapScorer  # noqa: E402
from dsqa.runtime import state  # noqa: E402

HEADER = "IFMIF-DONES Technical Report - Internal"

DONES_PAGES = [
    ("IFMIF-DONES Lithium Loop and Impurity Control Design", [
        "Abstract",
        "This report describes the lithium loop of the IFMIF-DONES facility, the Impurity Control System and "
        "the main heat exchanger of the primary loop.",
        "1. Introduction",
        "The DEMO Oriented Neutron Source produces neutrons by deuteron irradiation of a liquid lithium target. "
        "The lithium flows at 15 m/s in front of the beam.",
    ]),
    (None, [
        "2. Impurity Control System",
        "The Impurity Control System (ICS) branch of the DONES Li loop takes a small fraction of the main flow. "
        "The bypass ratio of the ICS branch is 5 % of the main lithium flow. The on-line nitrogen trap operates "
        "at a temperature of 600 C. The hot traps remove nitrogen and the cold trap removes tritium and Be7.",
        "Table 5. Radionuclide data used in the inventory calculation.",
        "The half-life of Be7 is 53.22 days. Beryllium-7 is the main source of activity in the heat exchanger "
        "during the first months after shutdown.",
    ]),
    (None, [
        "3. Heat Exchanger",
        "The primary heat exchanger transfers 9 MW from the lithium loop to the oil loop. The approximate "
        "volumetric flow rate in the primary heat exchanger is 0.1 m3/s.",
        "References",
        "[1] A. Author, Lithium loop design, Fusion Eng. Des. 2020.",
    ]),
]

WINSTAT_PAGES = [
    ("WinStat: Window Statistics for Long Sequence Time Series Forecasting", [
        "Abstract",
        "We propose WinStat, a window-based statistical normalization for long-horizon forecasting with "
        "transformer models. WinStatFlex adds a normalized weighting mechanism across windows.",
        "1. Introduction",
        "Time series forecasting with input length L requires choosing a window size. For L = 512 the "
        "recommended window size is 16, which balances local statistics and stability.",
        "2. Method",
        "WinStatFlex computes a weighted average of window statistics where the weights are normalized with a "
        "softmax over learnable scores.",
    ]),
]

MEDICAL_PAGES = [
    ("Clinical outcomes of statin therapy in elderly patients", [
        "Abstract",
        "We analyse cardiovascular outcomes in a cohort of 4000 elderly patients treated with statins. "
        "Mortality and hospital admissions were recorded for five years.",
    ]),
]


def _make_pdf(path: Path, pages: list[tuple[str | None, list[str]]]) -> None:
    import pymupdf

    doc = pymupdf.open()
    for title, paragraphs in pages:
        page = doc.new_page()
        page.insert_text((50, 30), HEADER if "DONES" in path.stem else "", fontsize=8)
        y = 60
        if title:
            page.insert_textbox(pymupdf.Rect(50, y, 550, y + 60), title, fontsize=18)
            y += 70
        for para in paragraphs:
            rect = pymupdf.Rect(50, y, 550, y + 200)
            page.insert_textbox(rect, para, fontsize=10)
            lines = max(1, len(para) // 90 + 1)
            y += 14 * lines + 18
    doc.set_metadata({"title": pages[0][0] or ""})
    doc.save(path)
    doc.close()


@pytest.fixture(scope="session")
def corpus_dir(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("corpus")
    _make_pdf(root / "dones_li_loop.pdf", DONES_PAGES)
    _make_pdf(root / "winstat.pdf", WINSTAT_PAGES)
    _make_pdf(root / "medical.pdf", MEDICAL_PAGES)
    (root / "broken.pdf").write_bytes(b"%PDF-1.4 esto no es un pdf valido")
    (root / "notes.txt").write_text("no es un pdf")
    return root


@pytest.fixture()
def fake_models(monkeypatch):
    """OLMo, embedder y reranker simulados; cachés limpias en cada prueba."""
    monkeypatch.setitem(state.FACTORIES, "llm", lambda model_id, gcfg: EchoLLM())
    monkeypatch.setitem(state.FACTORIES, "encoder", lambda cfg, root: HashEncoder())
    monkeypatch.setitem(state.FACTORIES, "scorer", lambda cfg, root: OverlapScorer())
    state.clear_caches(keep_llm=False)
    yield
    state.clear_caches(keep_llm=False)
