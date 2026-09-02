# 💳 Use Case 3 — Payment Investigation: Duplicates, Orphans & Over-Refunds

**Track**: Python / Data Structures
**Estimated time**: ~1 hour
**No banking/domain knowledge needed** beyond "a charge can be refunded" — no API keys, no GPU, no ML libraries.

---

## 📋 The brief

You're given a batch of payment webhook events — charges and refunds —
from a payment gateway that, like every real one, occasionally redelivers
the same event, delivers events out of order, and sometimes lets a
merchant refund more than they charged. Your job is to investigate the
batch and report what's actually wrong with it.

### Exact spec

Implement:

```python
def investigate_ledger(events) -> dict:
    """Each event has .event_id, .event_type ("charge"|"refund"),
    .charge_id, .amount (a string with exactly 2 decimal places, e.g.
    "19.99"), .timestamp."""
```

Return a dict with exactly these keys:

- **`duplicate_event_ids`** — `event_id`s that appear more than once in
  the input (a redelivered webhook). List each such id once, however many
  times it actually appeared.
- **`orphan_refund_charge_ids`** — `charge_id`s that have at least one
  refund event but **no charge event anywhere in the batch**. Events are
  not guaranteed to arrive charge-first — decide this from the whole
  batch, not as you process events one at a time.
- **`over_refunded_charge_ids`** — `charge_id`s (that do have a charge)
  where the total refunded amount **exceeds** the charge amount.
- **`net_cents`** — `dict[charge_id, int]`: charge amount minus total
  refunded, in integer cents, for every `charge_id` that has a charge event.

**Deduplicate first.** A redelivered event (same `event_id` twice) must
be counted once — not once per delivery — when you compute sums.

That's the whole spec — the trusted tests check exactly this, nothing more.

---

## 🧠 Why this is harder than it looks

- **Order independence.** "Orphaned" has to mean "no charge anywhere in
  this batch," not "no charge seen yet." A single left-to-right pass that
  flags a refund as orphaned the moment it's seen, before its charge
  arrives later in the same list, gets this wrong — and webhook delivery
  order is never guaranteed in practice.
- **Money is not a float.** Amount strings always have exactly 2 decimal
  places — parse them into integer cents by splitting the string, and do
  every calculation in integer cents. Route currency through `float` at
  any point and you will eventually hit a case where several amounts that
  should sum to exactly the charge don't — `0.1 + 0.2 != 0.3` in IEEE 754,
  and summing more values makes it worse, not better. One of the trusted
  tests constructs exactly this case.
- **The naive solution *works*.** "For each refund, scan every charge to
  find a match" gets the right answer on any small input. It's O(n²), and
  it will fail the performance benchmark on a larger batch where an
  indexed (`charge_id -> amount` dict) approach stays fast.

---

## 🎯 What you're building

In your `submissions/<your-name>/usecase-3-payment-investigation/` folder:

- **`solution.py`** — your `investigate_ledger`. Copy `starter/solution.py`
  in as your starting point.
- **`README.md`** — see the root [README.md](../README.md)'s "Submission
  requirements" for what this needs to contain.

---

## ✅ How this is graded

`tests/test_solution.py` (trusted, don't edit) compares your output
against a reference implementation on a generated ledger, plus three
targeted tests: out-of-order orphan detection, duplicate deduplication,
and the float-money trap (with a check that a genuine over-refund is
still caught after you fix it — the test isn't satisfied by just never
flagging anything). `benchmark/perf_bench.py` separately times a
20,000-charge ledger.

| Component | Weight | What it measures |
|---|---|---|
| Correctness | 30% | Matches the reference implementation; order-independence, deduplication, and exact money math specifically |
| Performance | 20% | Wall-clock time and peak memory on a 20k-charge ledger — where an O(n²) scan-per-refund solution loses points a correctness test can't catch |
| Reusability | 15% | Function/method complexity, length, docstrings + type hints (see root README) |
| Code quality | 15% | `ruff` findings per line |
| Maintainability | 10% | `radon` maintainability index |
| Completion | 10% | `solution.py` and a real `README.md` present |

Run it yourself before pushing:
```bash
# from the repo root
python -m scoring.cli --usecase usecase-3-payment-investigation \
  --submission submissions/<your-name>/usecase-3-payment-investigation
```

## 💡 Using Claude (or any AI assistant) here

Useful for: explaining exactly why `0.1 + 0.2 != 0.3` and what the fix
actually is; reviewing whether your orphan-detection logic really is
order-independent or just happens to pass the one test case you tried;
walking through why an index beats a nested scan. Less useful for:
noticing on its own that amounts need to stay as strings-turned-integers
rather than floats — ask an assistant to "parse the amount" with no
further steering and there's a real chance you get `float(amount)`.
