"""Deterministic synthetic event-stream generator shared by the trusted
tests and the benchmark. Not something candidates need to run themselves -
this is imported directly by tests/test_solution.py and benchmark/perf_bench.py.
"""
from __future__ import annotations

import random
from typing import NamedTuple


class Event(NamedTuple):
    event_id: int
    timestamp: float
    value: float


def generate_stream(
    n: int,
    seed: int,
    base: float = 0.0,
    noise_std: float = 1.0,
    anomaly_rate: float = 0.01,
    anomaly_magnitude: float = 8.0,
) -> list[Event]:
    """A mostly-Gaussian stream around `base` with occasional large spikes.
    Deterministic for a given seed - same seed always produces the same
    stream, so this is safe to call fresh in every grading run rather than
    needing pre-generated fixture files.
    """
    rng = random.Random(seed)
    events = []
    for i in range(n):
        if rng.random() < anomaly_rate:
            sign = rng.choice([-1, 1])
            value = base + sign * anomaly_magnitude * noise_std + rng.gauss(0, noise_std)
        else:
            value = base + rng.gauss(0, noise_std)
        events.append(Event(event_id=i, timestamp=float(i), value=value))
    return events
