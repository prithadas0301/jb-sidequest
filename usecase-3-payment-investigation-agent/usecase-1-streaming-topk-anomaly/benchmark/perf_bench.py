"""Performance benchmark for use case 1, invoked by scoring_hooks.run_benchmark
(itself called from scoring/performance.py). Measures wall-clock time and
peak memory for processing a large stream - see ../README.md's Performance
row for what these numbers are meant to separate.
"""
from __future__ import annotations

import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # this usecase dir

from data.generate_data import generate_stream  # noqa: E402
from scoring.submission_loader import load_module  # noqa: E402


def run(num_events: int = 200_000, window_size: int = 1000, k: int = 10, z_threshold: float = 3.0) -> dict:
    solution = load_module("solution.py")
    events = generate_stream(n=num_events, seed=2024, anomaly_rate=0.005, anomaly_magnitude=6.0)

    tracker = solution.AnomalyTracker(window_size=window_size, k=k, z_threshold=z_threshold)

    tracemalloc.start()
    start = time.perf_counter()
    for event in events:
        tracker.observe(event)
    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "wall_clock_seconds": elapsed,
        "peak_memory_kb": peak / 1024,
    }


if __name__ == "__main__":
    print(run())
