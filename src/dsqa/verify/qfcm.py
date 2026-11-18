"""Decisor con mapa cognitivo difuso cuasi-no lineal (q-FCM) — contribución CI 2 (SPEC-020).

Conceptos: C1 relevancia (s1), C2 claridad (s2), C3 acuerdo (s3), C4 cobertura (s4),
C5 suficiencia semántica (s5, juez OLMo) y C6 confianza en la evidencia (salida).

Regla:  A(t+1)_j = φ · f(Σ_i A(t)_i w_ij − h_j) + (1 − φ) · A(0)_j,   f(x) = 1 / (1 + e^(−λx))

Los conceptos de entrada sin aristas entrantes quedan fijos en su evidencia (no se "olvida" la
entrada). Como A(0) de C6 es 0, su activación máxima es φ; la confianza es A6 / φ ∈ [0, 1].
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..types import Signals, Verdict

log = logging.getLogger("dsqa.qfcm")

CONCEPTS = ["C1", "C2", "C3", "C4", "C5", "C6"]
LABELS = ("incorrect", "ambiguous", "correct")

EXPERT_EDGES = {"C1->C6": 0.65, "C2->C6": 0.30, "C3->C6": 0.30, "C4->C6": 0.45, "C5->C6": 0.55, "C1->C5": 0.0}
EXPERT_BOUNDS = {
    "C1->C6": [0.4, 0.9], "C2->C6": [0.1, 0.5], "C3->C6": [0.1, 0.5],
    "C4->C6": [0.2, 0.7], "C5->C6": [0.3, 0.8], "C1->C5": [0.0, 0.3],
}
EXPERT_MF = {"incorrect": [0.0, 0.0, 0.30, 0.45], "ambiguous": [0.30, 0.45, 0.60, 0.75], "correct": [0.60, 0.75, 1.0, 1.0]}


def trapezoid(x: float, a: float, b: float, c: float, d: float) -> float:
    if x < a or x > d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a) if b > a else 1.0
    return (d - x) / (d - c) if d > c else 1.0


@dataclass
class QFCMParams:
    phi: float = 0.7
    lam: float = 3.0
    bias: float = 1.1
    iterations: int = 10
    edges: dict[str, float] = field(default_factory=lambda: dict(EXPERT_EDGES))
    bounds: dict[str, list[float]] = field(default_factory=lambda: {k: list(v) for k, v in EXPERT_BOUNDS.items()})
    out_mf: dict[str, list[float]] = field(default_factory=lambda: {k: list(v) for k, v in EXPERT_MF.items()})

    def validate(self) -> "QFCMParams":
        if not 0.0 <= self.phi <= 1.0:
            raise ValueError("phi debe estar en [0, 1]")
        for key, w in self.edges.items():
            src, _, dst = key.partition("->")
            if src not in CONCEPTS or dst not in CONCEPTS:
                raise ValueError(f"arista inválida {key}")
            if not -1.0 <= w <= 1.0:
                raise ValueError(f"peso {key}={w} fuera de [-1, 1]")
            lo, hi = self.bounds.get(key, [-1.0, 1.0])
            if not lo - 1e-9 <= w <= hi + 1e-9:
                raise ValueError(f"peso {key}={w} fuera del rango de experto [{lo}, {hi}]")
        if set(self.out_mf) != set(LABELS):
            raise ValueError(f"out_mf debe definir {LABELS}")
        return self

    @classmethod
    def load(cls, path: Path | None) -> "QFCMParams":
        if not path or not path.exists():
            log.warning("sin parámetros q-FCM (%s): se usan los de experto", path)
            return cls()
        d = json.loads(path.read_text(encoding="utf-8"))
        return cls(d.get("phi", 0.7), d.get("lam", 3.0), d.get("bias", 1.1), d.get("iterations", 10),
                   d.get("edges", dict(EXPERT_EDGES)), d.get("bounds", dict(EXPERT_BOUNDS)),
                   d.get("out_mf", dict(EXPERT_MF))).validate()

    def to_json(self) -> dict:
        return {"phi": self.phi, "lam": self.lam, "bias": self.bias, "iterations": self.iterations,
                "edges": self.edges, "bounds": self.bounds, "out_mf": self.out_mf}

    def matrix(self) -> np.ndarray:
        W = np.zeros((6, 6))
        for key, w in self.edges.items():
            src, _, dst = key.partition("->")
            W[CONCEPTS.index(src), CONCEPTS.index(dst)] = w
        return W


class QFCMDecider:
    def __init__(self, params: QFCMParams, iterations: int | None = None) -> None:
        self.p = params.validate()
        if iterations:
            self.p.iterations = iterations
        self.W = self.p.matrix()
        incoming = np.abs(self.W).sum(axis=0)
        self.updated = [j for j in range(6) if incoming[j] > 0]
        # Sesgo: el de la config para C6; para otros conceptos, la mitad de su entrada positiva máxima.
        self.h = np.array([0.5 * self.W[:, j].clip(min=0).sum() for j in range(6)])
        self.h[5] = self.p.bias

    def activations(self, s: Signals) -> np.ndarray:
        a0 = np.array([*s.as_list(), 0.0])
        a = a0.copy()
        phi, lam = self.p.phi, self.p.lam
        for _ in range(self.p.iterations):
            x = a @ self.W
            new = a.copy()
            for j in self.updated:
                new[j] = phi / (1.0 + math.exp(-lam * (x[j] - self.h[j]))) + (1 - phi) * a0[j]
            if np.max(np.abs(new - a)) < 1e-4:
                a = new
                break
            a = new
        return a

    def confidence(self, s: Signals) -> float:
        a = self.activations(s)
        return float(a[5] / self.p.phi) if self.p.phi > 0 else 0.0

    def decide(self, s: Signals) -> Verdict:
        a = self.activations(s)
        conf = float(a[5] / self.p.phi) if self.p.phi > 0 else 0.0
        mem = {k: trapezoid(conf, *self.p.out_mf[k]) for k in LABELS}
        label = max(LABELS, key=lambda k: (mem[k], LABELS.index(k)))
        return Verdict(label, mem, conf, {"activations": [round(float(x), 4) for x in a]})
