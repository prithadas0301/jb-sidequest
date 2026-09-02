"""Performance benchmark for use case 4, invoked by scoring_hooks.run_benchmark.
Builds a much larger synthetic corpus (many more log lines, padded
documents) than either graded incident, to catch an approach that
rescans/re-embeds the whole corpus in a way that doesn't scale - e.g.
recomputing a global TF-IDF fit per document comparison instead of once.
"""
from __future__ import annotations

import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # this usecase dir

from data.loader import load_incident  # noqa: E402
from scoring.submission_loader import load_module  # noqa: E402

_LOG_LINE_TEMPLATE = (
    "2026-09-02 {h:02d}:{m:02d}:{s:02d} INFO  payment-service  "
    "Charge request received order_id=ORD-{n:06d}\n"
)


def _build_large_corpus(base_corpus: dict[str, str], n_extra_log_lines: int) -> dict[str, str]:
    corpus = dict(base_corpus)
    extra_lines = []
    for i in range(n_extra_log_lines):
        extra_lines.append(_LOG_LINE_TEMPLATE.format(h=(i // 3600) % 24, m=(i // 60) % 60, s=i % 60, n=i))
    corpus["logs.md"] = corpus.get("logs.md", "") + "\n" + "".join(extra_lines)
    # pad every other document too, so retrieval genuinely has more text to rank
    for name in list(corpus):
        if name != "logs.md":
            corpus[name] = corpus[name] * 5
    return corpus


def run(n_extra_log_lines: int = 5000) -> dict:
    solution = load_module("solution.py")
    query, base_corpus = load_incident("incident_a_pool_exhaustion")
    corpus = _build_large_corpus(base_corpus, n_extra_log_lines)

    tracemalloc.start()
    start = time.perf_counter()
    solution.investigate(query, corpus)
    elapsed = time.perf_counter() - start
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "wall_clock_seconds": elapsed,
        "peak_memory_kb": peak / 1024,
    }


if __name__ == "__main__":
    print(run())
