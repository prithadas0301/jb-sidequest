# 📉 Use Case 2 — Churn Prediction: Imbalance + a Leakage Trap

**Track**: Traditional ML / Python
**Estimated time**: ~1 hour (this is the more demanding of the two use cases — two graded deliverables)
**No banking/domain knowledge needed.** No GPU, no deep learning — plain scikit-learn is enough. No API keys required.

---

## 📋 The brief

A subscription service wants to predict which customers will churn next
month, so the retention team can reach out first. You get a labeled
training set and an unlabeled held-out set with the same columns.

### Generate the data (first step)

```bash
cd usecase-2-churn-leakage-imbalance
python data/generate_data.py
```

Writes `data/train.csv` (3000 labeled rows) and `data/test_features.csv`
(800 unlabeled rows) — deterministic, safe to re-run.

**Columns**: `customer_id`, `tenure_months`, `monthly_spend`,
`num_support_tickets`, `plan_type`, `payment_failed_count`,
`days_since_last_login`, `satisfaction_score`, `auto_renew`,
`cancellation_request_flag`, and (train only) `label` (0 = stayed, 1 = churned).

Churn is the **minority class** — expect roughly 1 in 10 rows to be
positive. Look at the actual distribution yourself before you start modeling.

### How the held-out set works

Same design as the rest of this repo: `test_features.csv`'s rows are
real and fixed; `test_labels.csv` doesn't exist anywhere you can read it.
CI regenerates it from a **secret** seed (`ML_HOLDOUT_SEED`, a repo
secret — see [`docs/HIRING_GUIDE.md`](../docs/HIRING_GUIDE.md)) and
discards it after scoring. Locally, the trusted tests fall back to a
**public** seed (`4242`) so you can see a real score while iterating —
just know CI's actual labels differ, so there's no benefit to
overfitting the public split.

---

## 🧠 Why this is harder than it looks

Two traps, both realistic, both things a model (or an AI assistant asked
to "build a classifier") will walk straight into if you let it:

1. **`cancellation_request_flag` looks like a gift.** On the training
   data, it's extremely well correlated with `label` — a model that
   leans on it will look almost suspiciously good on a train/validation
   split. That's the tell. In this dataset, that field behaves
   differently on the held-out set than it does on train (details are
   deliberately not spelled out further here — the README that matters
   is `data/generate_data.py`'s docstring, and yes, you're meant to go
   read it). A model that over-relies on it will do noticeably worse on
   the held-out set than its own training performance suggested. Real
   production systems have this exact failure mode: a feature that's a
   near-perfect proxy for the label in historical data because of *how*
   it was collected, not because it's causally predictive going forward.
2. **Imbalanced classes.** With ~10% positive rate, a model that just
   optimizes accuracy can get a deceptively decent-looking number by
   essentially never predicting churn. That's why this is graded on
   **average precision** (area under the precision-recall curve), not
   accuracy — a metric that a "predict the majority class" model scores
   badly on.

Neither trap is hidden — both are visible if you actually look at the
data and think about where each column plausibly comes from, instead of
one-shotting `RandomForestClassifier().fit(everything)`.

---

## 🎯 What you're building

Two functions, in your `submissions/<your-name>/usecase-2-churn-leakage-imbalance/solution.py`:

### `train_and_predict`
```python
def train_and_predict(train_csv_path: str, test_csv_path: str) -> list[float]:
    """Train on train_csv_path, return a churn PROBABILITY (0.0-1.0) for
    every row in test_csv_path, in the same row order."""
```

### `top_risk_customers`
```python
def top_risk_customers(customer_ids: list[str], probabilities: list[float], n: int) -> list[str]:
    """Return the n customer_ids with the highest probability, sorted
    descending by probability, ties broken by customer_id ascending.
    Must stay efficient when len(customer_ids) is much larger than n -
    see the Performance row below."""
```

This second one is a plain data-structures question hiding in an ML use
case: the retention team doesn't want a ranked list of 800 customers,
they want the top 20. Sorting everything just to throw away all but the
top few is the wrong complexity class — see `starter/solution.py`'s hint.

Copy `starter/solution.py` into your submission folder to start. Also
include the root README's required `README.md` (design, your
understanding of the problem, why you took the approach you did, name +
contact details).

---

## ✅ How this is graded

`tests/test_solution.py` (trusted, don't edit) checks predictions shape
and range, average precision against the held-out set (two tiers — floor
for partial credit, target for full credit), and `top_risk_customers`
correctness including the tie-break rule. `benchmark/perf_bench.py`
separately times `top_risk_customers` on 3,000,000 rows.

| Component | Weight | What it measures |
|---|---|---|
| Correctness | 30% | Prediction shape/range, average precision floor+target, `top_risk_customers` correctness + tie-breaking |
| Performance | 20% | `top_risk_customers` on 3M rows — a full sort loses points a correctness test can't catch |
| Reusability | 15% | Function/method complexity, length, docstrings + type hints (see root README) |
| Code quality | 15% | `ruff` findings per line |
| Maintainability | 10% | `radon` maintainability index |
| Completion | 10% | `solution.py` and a real `README.md` present |

Run it yourself before pushing:
```bash
# from the repo root
python -m scoring.cli --usecase usecase-2-churn-leakage-imbalance \
  --submission submissions/<your-name>/usecase-2-churn-leakage-imbalance
```

## 💡 Using Claude (or any AI assistant) here

Good uses: asking it to explain why average precision is a better metric
than accuracy for imbalanced classification; reviewing your feature
choices for anything that looks "too good to be true"; explaining
`heapq.nlargest`'s complexity versus a full sort.

What it won't do reliably on its own: notice that
`cancellation_request_flag` is suspicious. Ask an assistant to "build the
best classifier you can" over this dataset with no further guidance, and
there's a good chance it hands you exactly the trap — because from a
pure "which features correlate with the label" view, that column looks
like the best one you have. Recognizing *why* that's a warning sign
rather than a gift is the part that's on you.
