"""Reloj global y modos de operación (SPEC-002, ADR-07)."""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from enum import Enum
from typing import Callable, Iterator


class Mode(str, Enum):
    NORMAL = "normal"
    FAST = "fast"
    EMERGENCY = "emergency"


_ORDER = {Mode.NORMAL: 0, Mode.FAST: 1, Mode.EMERGENCY: 2}


class Clock:
    def __init__(self, now: Callable[[], float] = time.monotonic) -> None:
        self._now = now
        self._start = now()
        self._mode = Mode.NORMAL
        self.t_fast_s = 3000.0
        self.t_emergency_s = 3360.0
        self.timings: dict[str, float] = defaultdict(float)

    def configure(self, t_fast_s: float, t_emergency_s: float) -> None:
        self.t_fast_s = float(t_fast_s)
        self.t_emergency_s = float(t_emergency_s)

    def elapsed(self) -> float:
        return self._now() - self._start

    def remaining(self, limit_s: float) -> float:
        return limit_s - self.elapsed()

    def mode(self) -> Mode:
        e = self.elapsed()
        if e >= self.t_emergency_s:
            current = Mode.EMERGENCY
        elif e >= self.t_fast_s:
            current = Mode.FAST
        else:
            current = Mode.NORMAL
        # Los modos nunca retroceden.
        if _ORDER[current] > _ORDER[self._mode]:
            self._mode = current
        return self._mode

    def reset(self) -> None:
        """Solo para la evaluación local: reinicia el reloj entre configuraciones."""
        self._start = self._now()
        self._mode = Mode.NORMAL
        self.timings.clear()

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        t0 = self._now()
        try:
            yield
        finally:
            self.timings[name] += self._now() - t0


CLOCK = Clock()
