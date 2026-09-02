"""Copy this file into your submissions/<your-name>/usecase-1-streaming-topk-anomaly/
folder and implement AnomalyTracker. See ../README.md for the full spec.

Required interface - do not change the signature:

    class AnomalyTracker:
        def __init__(self, window_size: int, k: int, z_threshold: float): ...
        def observe(self, event) -> list[int]:
            # event has .event_id (int), .timestamp (float), .value (float)
            # return up to k event_ids, per the spec in the README/tests
            ...

Two things the tests specifically check that are easy to get wrong:

1. Numerical stability. Don't compute variance as
   `sum(x*x for x in window)/n - mean**2` - for a window with a large
   common offset and small real variance, that shortcut suffers
   catastrophic cancellation and gives you garbage. Use an incremental,
   numerically-stable approach (Welford's algorithm, generalized to
   support *removing* a point when it leaves the window - not just adding
   one, which is the textbook version most references show).

2. Eviction. A max-heap makes "give me the top-k by z-score" easy, but
   heaps don't support efficient arbitrary removal - and you need to
   remove an anomaly from consideration the moment it ages out of the
   window, not just stop adding new ones. Common approaches: lazy
   deletion (keep a "still valid" check and skip/pop stale entries when
   they reach the top) or a structure that supports both operations
   directly (e.g. `sortedcontainers.SortedList`, already in requirements.txt).

A solution that recomputes mean/variance and re-sorts the whole window on
every single event will pass the correctness tests but fail the
performance benchmark - that's deliberate, see the Performance row in the
scoring table.
"""
from __future__ import annotations


class AnomalyTracker:
    def __init__(self, window_size: int, k: int, z_threshold: float) -> None:
        self.window_size = window_size
        self.k = k
        self.z_threshold = z_threshold
        # TODO: your state here

    def observe(self, event) -> list[int]:
        # TODO: implement per the spec in ../README.md
        raise NotImplementedError
