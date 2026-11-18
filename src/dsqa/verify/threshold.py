"""Decisores simples: sin verificación (E0-E3) y umbrales fijos estilo CRAG (E4-E5) (SPEC-019)."""

from __future__ import annotations

from typing import Protocol

from ..types import Signals, Verdict


class Decider(Protocol):
    def decide(self, s: Signals) -> Verdict: ...


class NoVerify:
    def decide(self, s: Signals) -> Verdict:
        return Verdict("correct", {"correct": 1.0, "ambiguous": 0.0, "incorrect": 0.0}, 1.0)


class ThresholdDecider:
    def __init__(self, tau_high: float = 0.7, tau_low: float = 0.3, kappa: float = 0.5) -> None:
        if tau_low >= tau_high:
            raise ValueError("tau_low debe ser menor que tau_high")
        self.tau_high, self.tau_low, self.kappa = tau_high, tau_low, kappa

    def decide(self, s: Signals) -> Verdict:
        if s.s1_top1 >= self.tau_high and s.s4_coverage >= self.kappa:
            label = "correct"
        elif s.s1_top1 < self.tau_low:
            label = "incorrect"
        else:
            label = "ambiguous"
        mem = {k: 1.0 if k == label else 0.0 for k in ("correct", "ambiguous", "incorrect")}
        return Verdict(label, mem, s.s1_top1)
