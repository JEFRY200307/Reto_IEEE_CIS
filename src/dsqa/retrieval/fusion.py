"""Fusión de listas de buscadores: ninguna, RRF (E2-E4) y OWA difusa (E5+) (SPEC-014, SPEC-015)."""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np

from ..types import Candidate

log = logging.getLogger("dsqa.fusion")


def _merge(lists: dict[str, list[Candidate]]) -> dict[int, Candidate]:
    merged: dict[int, Candidate] = {}
    for name, cands in lists.items():
        for c in cands:
            m = merged.setdefault(c.chunk_id, Candidate(c.chunk_id))
            m.scores[name] = c.scores.get(name, 0.0)
            m.ranks[name] = c.ranks.get(name, 0)
    return merged


def _ranked(merged: dict[int, Candidate], top_n: int) -> list[Candidate]:
    out = sorted(merged.values(), key=lambda c: (-c.scores["fused"], c.chunk_id))[:top_n]
    for r, c in enumerate(out, 1):
        c.ranks["fused"] = r
    return out


class Fusion(Protocol):
    def fuse(self, lists: dict[str, list[Candidate]], top_n: int) -> list[Candidate]: ...


class NoFusion:
    """E0-E1: una sola lista (si hay varias, la densa)."""

    def fuse(self, lists: dict[str, list[Candidate]], top_n: int) -> list[Candidate]:
        if not lists:
            return []
        name = "dense" if "dense" in lists else next(iter(lists))
        merged = _merge({name: lists[name]})
        for c in merged.values():
            c.scores["fused"] = c.scores[name]
        return _ranked(merged, top_n)


class RRF:
    def __init__(self, k: int = 60) -> None:
        self.k = k

    def fuse(self, lists: dict[str, list[Candidate]], top_n: int) -> list[Candidate]:
        merged = _merge(lists)
        for c in merged.values():
            c.scores["fused"] = sum(1.0 / (self.k + r) for r in c.ranks.values() if r > 0)
        return _ranked(merged, top_n)


@dataclass
class OWAParams:
    norm: str = "minmax"
    a: dict[str, float] = field(default_factory=lambda: {"bm25": 8.0, "dense": 8.0})
    c: dict[str, float] = field(default_factory=lambda: {"bm25": 0.5, "dense": 0.5})
    w: list[float] = field(default_factory=lambda: [0.4, 0.6])

    def validate(self) -> "OWAParams":
        if abs(sum(self.w) - 1.0) > 1e-6 or any(x < 0 for x in self.w):
            raise ValueError(f"los pesos OWA deben ser >= 0 y sumar 1 (recibido {self.w})")
        if self.norm not in ("minmax", "zscore"):
            raise ValueError("owa.norm debe ser minmax o zscore")
        return self

    @classmethod
    def load(cls, path: Path | None) -> "OWAParams":
        if not path or not path.exists():
            log.warning("sin parámetros OWA (%s): se usan los iniciales", path)
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data.get("norm", "minmax"), data["a"], data["c"], data["w"]).validate()

    def to_json(self) -> dict:
        return {"norm": self.norm, "a": self.a, "c": self.c, "w": self.w}


def _normalize(values: np.ndarray, method: str) -> np.ndarray:
    if values.size == 0:
        return values
    if method == "zscore":
        std = values.std()
        z = (values - values.mean()) / std if std > 1e-9 else np.zeros_like(values)
        return 1.0 / (1.0 + np.exp(-z))  # a [0,1] para usar el mismo centro c
    lo, hi = values.min(), values.max()
    if hi - lo < 1e-9:
        return np.full_like(values, 0.5)
    return (values - lo) / (hi - lo)


class OWA:
    """Puntajes → pertenencias μ_r = sigmoide(a_r(ŝ_r − c_r)); OWA(d) = Σ_j w_j b_j con b ordenadas."""

    def __init__(self, params: OWAParams) -> None:
        self.p = params.validate()

    def memberships(self, lists: dict[str, list[Candidate]]) -> dict[int, dict[str, float]]:
        mu: dict[int, dict[str, float]] = {}
        for name, cands in lists.items():
            if not cands:
                continue
            raw = np.asarray([c.scores.get(name, 0.0) for c in cands], dtype=np.float64)
            norm = _normalize(raw, self.p.norm)
            a, c0 = self.p.a.get(name, 8.0), self.p.c.get(name, 0.5)
            for cand, s in zip(cands, norm):
                mu.setdefault(cand.chunk_id, {})[name] = 1.0 / (1.0 + math.exp(-a * (s - c0)))
        return mu

    def fuse(self, lists: dict[str, list[Candidate]], top_n: int) -> list[Candidate]:
        merged = _merge(lists)
        mu = self.memberships(lists)
        names = list(lists)
        w = self.p.w
        if len(w) != len(names):  # un solo buscador disponible: OWA = su pertenencia
            w = [1.0] + [0.0] * (len(names) - 1)
        for cid, c in merged.items():
            b = sorted((mu.get(cid, {}).get(n, 0.0) for n in names), reverse=True)
            c.scores["fused"] = float(sum(wj * bj for wj, bj in zip(w, b)))
            for n in names:
                c.scores[f"mu_{n}"] = mu.get(cid, {}).get(n, 0.0)
        return _ranked(merged, top_n)


def make_fusion(cfg, root: Path) -> Fusion:
    from ..runtime.config import resolve_path

    f = cfg.fusion
    if f.method == "rrf":
        return RRF(f.rrf_k)
    if f.method == "owa":
        return OWA(OWAParams.load(resolve_path(root, f.owa_params)))
    return NoFusion()
