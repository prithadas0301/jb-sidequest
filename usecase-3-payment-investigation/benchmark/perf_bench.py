"""Performance benchmark for use case 3, invoked by scoring_hooks.run_benchmark.
A per-refund linear scan over all charges (instead of an index) is the
natural trap this is calibrated against.
"""
from __future__ import annotations

import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # this usecase dir

from data.generate_data import generate_ledger  # noqa: E402
from scoring.submission_loader import load_module  # noqa: E402


def run(n_charges: int = 20_000) -> dict:
    solution = load_module("solution.py")
    events = generate_ledger(n_charges=n_charges, seed=777)

    tracemalloc.start()
    start = time.perf_counter()
    solution.investigate_ledger(events)
    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "wall_clock_seconds": elapsed,
        "peak_memory_kb": peak / 1024,
    }


if __name__ == "__main__":
    print(run())
