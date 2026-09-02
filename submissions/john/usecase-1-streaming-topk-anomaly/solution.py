"""AnomalyTracker - sliding-window top-k anomaly detector.

Design: two pieces of state, both O(window_size) in size, both updated in
O(log window_size) or better per event:

  - self.window: a deque of (event_id, value, frozen_z) for events
    currently in the baseline window, plus a Welford-style running
    (n, mean, M2) that supports both adding a point AND removing one
    (the standard Welford recurrences run in reverse) - this avoids ever
    recomputing mean/variance from scratch, which is what makes this
    O(1) amortized per event instead of O(window).
  - self.anomalies: a SortedList of (event_id, z) for window members
    whose |z| cleared the threshold, keyed so iteration order is exactly
    "most anomalous first, ties broken by most recent first". Sorted
    containers support O(log window_size) insert/remove, which is what
    makes evicting a stale anomaly cheap instead of requiring a full
    rescan of a max-heap (heaps don't support efficient arbitrary removal).
"""
from __future__ import annotations

from collections import deque

from sortedcontainers import SortedList


class AnomalyTracker:
    def __init__(self, window_size: int, k: int, z_threshold: float) -> None:
        self.window_size = window_size
        self.k = k
        self.z_threshold = z_threshold

        self.window: deque[tuple[int, float, float]] = deque()
        self.n = 0
        self.mean = 0.0
        self.m2 = 0.0
        self.anomalies = SortedList(key=lambda pair: (-abs(pair[1]), -pair[0]))

    def _current_std(self) -> float:
        if self.n < 2:
            return 0.0
        return (self.m2 / self.n) ** 0.5

    def _add_to_baseline(self, value: float) -> None:
        self.n += 1
        delta = value - self.mean
        self.mean += delta / self.n
        delta2 = value - self.mean
        self.m2 += delta * delta2

    def _remove_from_baseline(self, value: float) -> None:
        if self.n <= 1:
            self.n, self.mean, self.m2 = 0, 0.0, 0.0
            return
        delta = value - self.mean
        self.mean -= delta / (self.n - 1)
        delta2 = value - self.mean
        self.m2 -= delta * delta2
        self.n -= 1

    def observe(self, event) -> list[int]:
        if self.n >= 2:
            std = self._current_std()
            z = 0.0 if std == 0 else (event.value - self.mean) / std
        else:
            z = 0.0

        self._add_to_baseline(event.value)
        self.window.append((event.event_id, event.value, z))
        if abs(z) >= self.z_threshold:
            self.anomalies.add((event.event_id, z))

        if len(self.window) > self.window_size:
            old_id, old_value, old_z = self.window.popleft()
            self._remove_from_baseline(old_value)
            if abs(old_z) >= self.z_threshold:
                self.anomalies.remove((old_id, old_z))

        return [event_id for event_id, _ in self.anomalies[: self.k]]
