from pathlib import Path

import pytest
from pydantic import ValidationError

from dsqa.runtime.clock import Clock, Mode
from dsqa.runtime.config import Config, diff_blocks, load_config

REPO = Path(__file__).resolve().parents[2]
CONFIGS = REPO / "configs"


def test_all_configs_load():
    for p in CONFIGS.rglob("*.yaml"):
        assert load_config(p).strategy


@pytest.mark.parametrize("a,b,expected", [
    ("e0", "e1", {"ingest", "index", "context", "generate"}),
    ("e1", "e2", {"retrieval", "fusion"}),
    ("e2", "e3", {"index", "retrieval", "rerank", "context"}),
    ("e3", "e4", {"verify", "generate"}),
    ("e4", "e5", {"fusion"}),
    ("e5", "e6", {"verify"}),
])
def test_each_step_changes_only_its_blocks(a, b, expected):
    assert diff_blocks(load_config(CONFIGS / f"{a}.yaml"), load_config(CONFIGS / f"{b}.yaml")) == expected


def test_unknown_key_is_rejected():
    with pytest.raises(ValidationError) as err:
        Config.model_validate({"retrieval": {"top_kk": 5}})
    assert "top_kk" in str(err.value)


def test_cross_validation():
    with pytest.raises(ValidationError):
        Config.model_validate({"retrieval": {"retrievers": ["bm25", "dense"]}, "fusion": {"method": "none"}})
    with pytest.raises(ValidationError):
        Config.model_validate({"runtime": {"t_fast_s": 3000, "t_emergency_s": 2000}})


def test_circular_extends(tmp_path):
    (tmp_path / "a.yaml").write_text("extends: b.yaml\n")
    (tmp_path / "b.yaml").write_text("extends: a.yaml\n")
    with pytest.raises(ValueError, match="circular"):
        load_config(tmp_path / "a.yaml")


def test_clock_modes_never_go_back():
    now = [0.0]
    clock = Clock(lambda: now[0])
    clock.configure(3000, 3360)
    for t, expected in [(2999, Mode.NORMAL), (3001, Mode.FAST), (3361, Mode.EMERGENCY)]:
        now[0] = t
        assert clock.mode() == expected
    now[0] = 10
    assert clock.mode() == Mode.EMERGENCY


def test_clock_stage_accumulates():
    now = [0.0]
    clock = Clock(lambda: now[0])
    with clock.stage("x"):
        now[0] += 2
    with clock.stage("x"):
        now[0] += 3
    assert clock.timings["x"] == 5
