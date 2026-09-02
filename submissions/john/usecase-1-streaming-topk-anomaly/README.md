# Submission — usecase-1-streaming-topk-anomaly

**Name**: John Smith
**Email**: john.smith@example.com
**Phone**: +65 8123 4567

## Design

`AnomalyTracker` keeps two pieces of state, both bounded to `window_size`
and both updated in O(log window_size) or better per event, never O(window):

1. A `deque` of `(event_id, value, frozen_z)` for the current window, plus
   a Welford-style running `(n, mean, M2)`. Welford's is normally taught
   as an add-only algorithm; I implemented the reverse recurrence too so
   a point leaving the window updates the running mean/variance in O(1)
   instead of forcing a full recompute over what's left.
2. A `sortedcontainers.SortedList` of `(event_id, z)` for whichever window
   members currently clear `z_threshold`, keyed so iteration order is
   "most anomalous first, ties by most recent". Sorted containers support
   O(log n) insert *and* remove-by-value, which is the part a plain
   `heapq` max-heap can't do - you can push onto a heap cheaply, but you
   can't cheaply pull an arbitrary element back out of the middle of it
   when it ages out of the window.

## My understanding of the problem

The spec looks like "keep a window, compute z-scores" - trivial with a
list and `statistics.pstdev`. The actual problem is that the naive version
of that is O(window) per event (recompute stats from scratch, rescan for
top-k), which is fine for a demo and falls over at real volume. The two
things that actually matter are (a) doing the variance update
incrementally without ever revisiting the whole window, and (b) making
sure something that stops being anomalous - because it aged out of the
window - actually disappears from the output, which a max-heap alone
doesn't give you for free.

## Why I took this approach

I considered just recomputing `statistics.pstdev(window)` fresh every
call - it's simpler and matches the reference test's oracle almost
exactly, which felt lower-risk for correctness. I went with the
incremental Welford approach anyway because the brief's performance
section makes it clear that's the actual point of the exercise, and a
solution that's "correct but O(window)" is explicitly called out as the
thing this use case is designed to catch. The tradeoff is a slightly
higher chance of a floating-point rounding difference against the
reference oracle (incremental vs. two-pass batch computation can differ
in the last couple of bits) - I judged that risk as much smaller than
the certainty of failing the performance benchmark outright.

One thing I did not handle specially: ties in z-score are broken by
`event_id` descending per the spec, which `SortedList`'s key function
gives me directly since `event_id` is unique per event - no separate
tie-break logic needed.
