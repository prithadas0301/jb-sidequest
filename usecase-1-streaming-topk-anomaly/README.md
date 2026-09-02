# 📈 Use Case 1 — Sliding-Window Top-K Anomaly Tracker

**Track**: Python / Data Structures & Algorithms
**Estimated time**: ~1 hour
**No banking/domain knowledge needed.** No API keys, no GPU, no ML libraries required for this one.

---

## 📋 The brief

You're processing a live event stream — one `(event_id, timestamp, value)`
triple at a time. You never get to see the whole stream at once, and you
can't buffer it: only the most recent `window_size` events matter at any
moment ("recent history"), and only `k` results are ever asked for.

For every event, as it arrives, you need to:

1. Score how anomalous it is relative to **recent history** — a z-score
   against the mean/stdev of the current window (**before** this event is
   added to it, not including itself).
2. Report the **top-k currently-anomalous events still within the
   window** — sorted by how anomalous they are, most extreme first.

That's the whole problem. It sounds like five lines of pandas. It isn't —
see "Why this is harder than it looks" below before you start.

### Exact spec

Implement a class with this interface:

```python
class AnomalyTracker:
    def __init__(self, window_size: int, k: int, z_threshold: float): ...
    def observe(self, event) -> list[int]:
        """event has .event_id (int), .timestamp (float), .value (float).
        Called once per event, in arrival order."""
```

On each call to `observe(event)`:

1. Compute `event`'s z-score against the **current window's** mean and
   population stdev — the window as it stands **before** this event is
   added (i.e. against recent history, not itself). If the window has
   fewer than 2 prior points, or its stdev is exactly `0`, the z-score is
   `0.0`.
2. This z-score is **frozen** for this event — it never gets recomputed
   later, even as the window's stats drift.
3. Add this event to the window, evicting the oldest event if the window
   is now over `window_size`.
4. Return up to `k` event_ids — restricted to events **still in the
   window** whose `|z| >= z_threshold` — sorted by `|z|` descending, ties
   broken by `event_id` descending (most recent first).

That's it. No hidden requirements beyond this — the trusted test suite
checks exactly this spec, nothing more.

## 🧠 Why this is harder than it looks

- **Numerical stability.** The obvious "fast" variance formula —
  `sum(x*x)/n - mean**2` — catastrophically cancels when your data has a
  large common offset and small real variance (which one of the trusted
  tests deliberately constructs). You need an incrementally-maintained,
  numerically stable computation — and the textbook version of Welford's
  algorithm only covers *adding* a point, not *removing* one when it
  leaves the window.
- **Eviction from a priority structure.** A max-heap makes "top-k by
  z-score" trivial for a growing stream — but heaps don't support
  efficient arbitrary removal, and an anomaly has to *disappear* from
  your results the moment it ages out of the window, not just stop
  accumulating new ones. This is the actual data-structures problem here.
- **The naive solution *works*.** "Keep a list of the window, recompute
  mean/stdev and re-sort every time" will pass every small correctness
  test. It'll fail the performance benchmark, and it may fail the
  numerical-stability test depending on how you compute variance. An AI
  assistant asked to "track anomalies in a sliding window" will very
  often hand you exactly this — plausible, wrong under load.

---

## 🎯 What you're building

In your `submissions/<your-name>/usecase-1-streaming-topk-anomaly/` folder:

- **`solution.py`** — your `AnomalyTracker`. Copy `starter/solution.py` in
  as your starting point; it has the interface stubbed and hints on both
  hard parts.
- **`README.md`** — see the root [README.md](../README.md)'s "Submission
  requirements" for what this needs to contain (design, your understanding
  of the problem, why you took the approach you did, your name and contact
  details).

---

## ✅ How this is graded

`tests/test_solution.py` (trusted, don't edit) compares your output
event-by-event against a brute-force reference implementation on random
streams, plus two targeted tests: one that specifically checks eviction
(a spike must disappear from results once it's aged out of the window),
and one that specifically stresses numerical stability (large-offset,
tiny-variance data). `benchmark/perf_bench.py` separately times a 200,000-event
run under `scoring/performance.py`'s thresholds.

| Component | Weight | What it measures |
|---|---|---|
| Correctness | 30% | Matches the reference implementation, handles eviction and the zero-variance edge case |
| Performance | 20% | Wall-clock time and peak memory on a 200k-event stream — this is where an O(window)-per-event solution loses points a correctness test can't catch |
| Reusability | 15% | Function/method complexity, length, docstrings + type hints (see root README) |
| Code quality | 15% | `ruff` findings per line |
| Maintainability | 10% | `radon` maintainability index |
| Completion | 10% | `solution.py` and a real `README.md` present |

Run it yourself before pushing:
```bash
# from the repo root
python -m scoring.cli --usecase usecase-1-streaming-topk-anomaly \
  --submission submissions/<your-name>/usecase-1-streaming-topk-anomaly
```

## 💡 Using Claude (or any AI assistant) here

It's genuinely useful for explaining Welford's algorithm, walking through
why heaps don't support efficient removal, or reviewing whether your
specific implementation actually achieves the complexity you think it
does. It is not a substitute for understanding *why* the naive version is
wrong — ask it to generate a first pass and you'll very likely get
something that passes small tests and fails the benchmark. Recognizing
that gap, and knowing what to fix, is the actual skill this use case checks.
