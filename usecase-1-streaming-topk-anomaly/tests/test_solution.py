"""Trusted test suite for use case 1. This IS the spec - do not edit (see
'Protecting the autoscoring engine' in the root README).

Spec being tested (see ../README.md for the candidate-facing version):

  observe(event) is called once per event, in arrival order. On each call:
    1. Compute this event's z-score against the CURRENT window's mean/pstdev
       (the window as it stands BEFORE this event is added - i.e. against
       recent history, not including itself). If the window has fewer than
       2 prior points, or its stdev is exactly 0, z = 0.0.
    2. This z-score is frozen permanently for this event.
    3. Add this event to the window (evicting the oldest if the window is
       now over window_size).
    4. Return up to `k` event_ids, restricted to events STILL IN THE WINDOW
       whose |z| >= z_threshold, sorted by |z| descending, ties broken by
       event_id descending (most recent first).

The oracle below is a deliberately simple, brute-force (O(n * window))
implementation of exactly this spec, using stdlib `statistics` (numerically
stable) - used only to compute expected outputs for small test inputs, never
for grading performance. Comparing a submission's output against it,
event-by-event, is what actually verifies correctness; nothing here is a
hand-computed expected value that could hide an arithmetic mistake.
"""
from __future__ import annotations

import statistics
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # this usecase dir

from data.generate_data import Event, generate_stream  # noqa: E402
from scoring.submission_loader import load_module  # noqa: E402


def oracle_run(events: list[Event], window_size: int, k: int, z_threshold: float) -> list[list[int]]:
    outputs: list[list[int]] = []
    window_values: deque[float] = deque()
    window_entries: deque[tuple[int, float]] = deque()  # (event_id, frozen z), arrival order

    for event in events:
        if len(window_values) >= 2:
            mean = statistics.mean(window_values)
            std = statistics.pstdev(window_values)
            z = 0.0 if std == 0 else (event.value - mean) / std
        else:
            z = 0.0

        window_values.append(event.value)
        window_entries.append((event.event_id, z))
        if len(window_values) > window_size:
            window_values.popleft()
            window_entries.popleft()

        candidates = [(eid, zz) for eid, zz in window_entries if abs(zz) >= z_threshold]
        candidates.sort(key=lambda pair: (-abs(pair[1]), -pair[0]))
        outputs.append([eid for eid, _ in candidates[:k]])

    return outputs


def _run_submission(events: list[Event], window_size: int, k: int, z_threshold: float) -> list[list[int]]:
    solution = load_module("solution.py")
    tracker = solution.AnomalyTracker(window_size=window_size, k=k, z_threshold=z_threshold)
    return [list(tracker.observe(event)) for event in events]


def test_matches_oracle_on_a_moderate_random_stream():
    events = generate_stream(n=400, seed=42, anomaly_rate=0.03, anomaly_magnitude=6.0)
    window_size, k, z_threshold = 25, 3, 2.5

    expected = oracle_run(events, window_size, k, z_threshold)
    actual = _run_submission(events, window_size, k, z_threshold)

    assert len(actual) == len(events), "observe() must be called and return once per event"
    mismatches = [i for i, (e, a) in enumerate(zip(expected, actual)) if e != a]
    assert not mismatches, (
        f"{len(mismatches)}/{len(events)} steps disagree with the reference implementation. "
        f"First mismatch at step {mismatches[0]}: expected {expected[mismatches[0]]}, "
        f"got {actual[mismatches[0]]}"
    )


def test_return_type_and_length_bounds():
    events = generate_stream(n=100, seed=7, anomaly_rate=0.05)
    k = 4
    outputs = _run_submission(events, window_size=15, k=k, z_threshold=2.0)
    for i, out in enumerate(outputs):
        assert isinstance(out, list), f"step {i}: observe() must return a list, got {type(out)}"
        assert len(out) <= k, f"step {i}: returned {len(out)} ids, more than k={k}"
        assert len(set(out)) == len(out), f"step {i}: returned duplicate event_ids: {out}"


def test_eviction_removes_stale_anomalies_from_topk():
    """A large spike near the start must stop appearing in the topk output
    once enough events have passed for it to have left the window - this
    is the part a heap-without-lazy-deletion (or "just keep growing a
    max-heap forever") implementation gets wrong.
    """
    window_size, k, z_threshold = 20, 3, 2.5
    baseline = generate_stream(n=5, seed=1, anomaly_rate=0.0)
    spike = [Event(event_id=1000, timestamp=5.0, value=1000.0)]  # unmistakably anomalous
    filler_raw = generate_stream(n=window_size + 10, seed=2, anomaly_rate=0.0)
    filler = [Event(event_id=2000 + i, timestamp=10.0 + i, value=e.value) for i, e in enumerate(filler_raw)]
    events = baseline + spike + filler

    outputs = _run_submission(events, window_size, k, z_threshold)

    spike_index = len(baseline)  # index of the spike event in `events`/`outputs`
    assert 1000 in outputs[spike_index], "the spike should be flagged the moment it arrives"

    later_index = len(events) - 1  # well past window_size events after the spike
    assert 1000 not in outputs[later_index], (
        "the spike is still being returned long after it must have left the window - "
        "topk state isn't being evicted alongside the baseline window"
    )


def test_numerical_stability_under_large_offset():
    """base=1e9 with tiny noise: sum(x^2)/n - mean^2 (the naive shortcut
    variance formula) suffers catastrophic cancellation here and produces
    garbage; a numerically stable computation (Welford's, or two-pass
    mean-then-deviations like the oracle) does not. Compares which events
    get flagged, not raw z-scores - not a floating-point-tolerance test.
    """
    events = generate_stream(
        n=2000, seed=99, base=1_000_000_000.0, noise_std=0.001,
        anomaly_rate=0.02, anomaly_magnitude=50.0,
    )
    window_size, k, z_threshold = 100, 5, 3.0

    expected = oracle_run(events, window_size, k, z_threshold)
    actual = _run_submission(events, window_size, k, z_threshold)

    expected_flagged = {eid for step in expected for eid in step}
    actual_flagged = {eid for step in actual for eid in step}

    jaccard_overlap = (
        len(expected_flagged & actual_flagged) / len(expected_flagged | actual_flagged)
        if (expected_flagged or actual_flagged) else 1.0
    )
    assert jaccard_overlap >= 0.9, (
        f"only {jaccard_overlap:.0%} overlap between your flagged anomalies and the reference "
        f"on a large-offset/tiny-variance stream - this usually means the variance computation "
        f"isn't numerically stable (avoid the sum(x^2)/n - mean^2 shortcut)"
    )


def test_zero_variance_window_does_not_crash():
    constant_events = [Event(event_id=i, timestamp=float(i), value=5.0) for i in range(50)]
    outputs = _run_submission(constant_events, window_size=10, k=3, z_threshold=1.0)
    assert all(out == [] for out in outputs), (
        "a perfectly constant window has zero variance - nothing should ever be flagged, and "
        "this must not raise a ZeroDivisionError"
    )
