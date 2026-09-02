"""Scoring configuration consumed by scoring/cli.py. Candidates should not
need to read or modify this file - and per scoring/PROTECTED_MANIFEST.json,
doing so fails CI's integrity check before scoring even runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

USECASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(USECASE_DIR.parent))  # repo root
sys.path.insert(0, str(USECASE_DIR))

WEIGHTS = {
    "correctness": 0.30,
    "performance": 0.20,
    "reusability": 0.15,
    "code_quality": 0.15,
    "maintainability": 0.10,
    "completion": 0.10,
}

REQUIRED_FILES = ["solution.py"]

# First-pass estimates, not independently benchmarked on a real CI runner -
# sanity-check with a known-good reference solution before running this for
# real (see docs/HIRING_GUIDE.md). A TF-IDF (or similar) approach fit once
# over the corpus should clear `target` easily; an approach that re-scores
# the whole corpus per candidate document pair, or re-fits per query term,
# should not clear even `floor` at this corpus size.
PERFORMANCE_THRESHOLDS = {
    "wall_clock_seconds": {"floor": 15.0, "target": 3.0, "higher_is_better": False},
    "peak_memory_kb": {"floor": 300_000.0, "target": 50_000.0, "higher_is_better": False},
}


def run_benchmark() -> dict:
    from benchmark.perf_bench import run
    return run(n_extra_log_lines=5000)
