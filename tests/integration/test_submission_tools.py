"""Chequeo del zip y métricas de evaluación."""

import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "eval"))

from check_submission import static_checks  # noqa: E402
from common import balanced_accuracy  # noqa: E402

GOOD_MAIN = "def answer(question, corpus_dir, model_id):\n    return 'x'\n"


def _zip(tmp_path: Path, files: dict[str, str]) -> Path:
    path = tmp_path / "s.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return path


def test_check_accepts_valid_zip(tmp_path):
    z = _zip(tmp_path, {"main.py": GOOD_MAIN + "import numpy, yaml, fitz, json\n", "config.yaml": "strategy: t\n"})
    assert static_checks(z) == []


def test_check_rejects_main_in_subfolder(tmp_path):
    z = _zip(tmp_path, {"sub/main.py": GOOD_MAIN, "config.yaml": "strategy: t\n"})
    assert any("raíz" in e for e in static_checks(z))


def test_check_rejects_unavailable_import(tmp_path):
    z = _zip(tmp_path, {"main.py": GOOD_MAIN + "import vllm\n", "config.yaml": "strategy: t\n"})
    assert any("vllm" in e for e in static_checks(z))


def test_check_rejects_bad_signature_and_config(tmp_path):
    z = _zip(tmp_path, {"main.py": "def answer(q):\n    return 'x'\n", "config.yaml": "retrieval:\n  top_kk: 1\n"})
    errors = static_checks(z)
    assert any("firma" in e for e in errors) and any("config.yaml" in e for e in errors)


def test_balanced_accuracy_official_formula():
    verdicts = {f"d{i}": int(i < 3) for i in range(10)} | {f"p{i}": int(i < 9) for i in range(15)}
    domains = {k: ("DONES" if k.startswith("d") else "AI Papers") for k in verdicts}
    assert balanced_accuracy(verdicts, domains)["balanced_accuracy"] == pytest.approx(0.5 * (0.3 + 0.6))
