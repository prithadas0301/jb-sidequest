"""Performance benchmark for use case 2 - specifically top_risk_customers(),
invoked by scoring_hooks.run_benchmark. Training-time for the model itself
isn't measured (a few thousand rows trains in a blink regardless of
approach); the data-structures angle in this use case is selecting the
top n out of a much larger m without a full sort.
"""
from __future__ import annotations

import random
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root

from scoring.submission_loader import load_module  # noqa: E402


def run(m: int = 3_000_000, n: int = 20) -> dict:
    solution = load_module("solution.py")

    rng = random.Random(2024)
    ids = [f"C{i:08d}" for i in range(m)]
    probs = [rng.random() for _ in range(m)]

    tracemalloc.start()
    start = time.perf_counter()
    solution.top_risk_customers(ids, probs, n)
    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "wall_clock_seconds": elapsed,
        "peak_memory_kb": peak / 1024,
    }


if __name__ == "__main__":
    print(run())
