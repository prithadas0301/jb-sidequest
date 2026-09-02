#!/usr/bin/env python3
"""Deterministic synthetic-data generator for use case 2.

Same held-out design as used elsewhere in this repo: test *features* are
public (fixed seed), test *labels* are not committed and are regenerated
on demand from a seed (secret in CI, a known public fallback for local
iteration) - see generate_test_labels() and ../README.md "How the
held-out set works".

The interesting part: `cancellation_request_flag` is generated
differently for train vs test. In train, it's strongly correlated with
the true label (as if pulled from a real "customer already opened a
cancellation ticket" field) - a model that leans on it will look great on
train. In test, it's generated independently of the label - simulating
that this signal isn't reliably available/meaningful at real prediction
time. A model that actually relies on it will underperform on the held-out
set relative to train; that gap is the point.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path

DATA_DIR = Path(__file__).parent

TRAIN_N = 3000
TEST_N = 800

TRAIN_FEATURE_SEED = 30260101
TRAIN_LABEL_SEED = 30260102
TRAIN_FLAG_SEED = 30260103
TEST_FEATURE_SEED = 30260201
TEST_FLAG_SEED = 30260202
PUBLIC_FALLBACK_HOLDOUT_SEED = 4242  # local-iteration only, see module docstring

PLAN_TYPES = ["basic", "standard", "premium"]
PLAN_SPEND_RANGES = {"basic": (9.0, 19.0), "standard": (20.0, 39.0), "premium": (40.0, 89.0)}

FEATURE_COLUMNS = [
    "customer_id", "tenure_months", "monthly_spend", "num_support_tickets",
    "plan_type", "payment_failed_count", "days_since_last_login",
    "satisfaction_score", "auto_renew", "cancellation_request_flag",
]


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _risk_score(row: dict) -> float:
    score = -1.2  # base log-odds, calibrated for ~9-10% average churn rate
    score += -0.04 * row["tenure_months"]
    score += 0.25 * row["num_support_tickets"]
    score += 0.5 * row["payment_failed_count"]
    score += 0.02 * row["days_since_last_login"]
    score += -0.35 * row["satisfaction_score"]
    score += -0.6 if row["auto_renew"] else 0.6
    return score


def _generate_features(n: int, feature_seed: int, id_prefix: str) -> list[dict]:
    rng = random.Random(feature_seed)
    rows = []
    for i in range(n):
        plan = rng.choice(PLAN_TYPES)
        low, high = PLAN_SPEND_RANGES[plan]
        rows.append({
            "customer_id": f"{id_prefix}{i:05d}",
            "tenure_months": rng.randint(0, 60),
            "monthly_spend": round(rng.uniform(low, high), 2),
            "num_support_tickets": rng.choices(range(8), weights=[30, 25, 15, 10, 8, 5, 4, 3])[0],
            "plan_type": plan,
            "payment_failed_count": rng.choices(range(5), weights=[70, 15, 8, 4, 3])[0],
            "days_since_last_login": rng.randint(0, 90),
            "satisfaction_score": round(rng.uniform(1.0, 5.0), 1),
            "auto_renew": 1 if rng.random() < 0.7 else 0,
        })
    return rows


def _generate_labels(rows: list[dict], label_seed: int) -> list[int]:
    rng = random.Random(label_seed)
    return [1 if rng.random() < _sigmoid(_risk_score(row)) else 0 for row in rows]


def _apply_correlated_flag(rows: list[dict], labels: list[int], flag_seed: int) -> None:
    rng = random.Random(flag_seed)
    for row, label in zip(rows, labels):
        p = 0.90 if label == 1 else 0.03
        row["cancellation_request_flag"] = 1 if rng.random() < p else 0


def _apply_decorrelated_flag(rows: list[dict], flag_seed: int) -> None:
    rng = random.Random(flag_seed)
    for row in rows:
        row["cancellation_request_flag"] = 1 if rng.random() < 0.10 else 0


def _write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def ensure_public_data() -> None:
    """Regenerate data/train.csv and data/test_features.csv if either is
    missing. Called by the trusted test suite, so grading never depends on
    a committed-but-possibly-stale CSV. Candidates can also just run this
    file directly.
    """
    if (DATA_DIR / "train.csv").exists() and (DATA_DIR / "test_features.csv").exists():
        return
    _write_all()


def _write_all() -> None:
    train_rows = _generate_features(TRAIN_N, TRAIN_FEATURE_SEED, id_prefix="TRAIN")
    train_labels = _generate_labels(train_rows, TRAIN_LABEL_SEED)
    _apply_correlated_flag(train_rows, train_labels, TRAIN_FLAG_SEED)
    for row, label in zip(train_rows, train_labels):
        row["label"] = label
    _write_csv(DATA_DIR / "train.csv", train_rows, FEATURE_COLUMNS + ["label"])

    test_rows = _generate_features(TEST_N, TEST_FEATURE_SEED, id_prefix="TEST")
    _apply_decorrelated_flag(test_rows, TEST_FLAG_SEED)
    _write_csv(DATA_DIR / "test_features.csv", test_rows, FEATURE_COLUMNS)


def generate_test_labels(holdout_seed: int) -> dict[str, int]:
    """customer_id -> true label for every row in test_features.csv, using
    the given seed. Used by the trusted test suite - never write this to a
    file a submission could read.
    """
    test_rows = _generate_features(TEST_N, TEST_FEATURE_SEED, id_prefix="TEST")
    labels = _generate_labels(test_rows, holdout_seed)
    return {row["customer_id"]: label for row, label in zip(test_rows, labels)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--holdout-seed", type=int, default=None,
                         help="Regenerate only test_labels.csv (for the existing test_features.csv)")
    parser.add_argument("--labels-out", default=None)
    args = parser.parse_args()

    if args.holdout_seed is not None:
        labels_by_id = generate_test_labels(args.holdout_seed)
        out_path = Path(args.labels_out) if args.labels_out else DATA_DIR / "test_labels.csv"
        rows = [{"customer_id": cid, "label": lbl} for cid, lbl in labels_by_id.items()]
        _write_csv(out_path, rows, ["customer_id", "label"])
        print(f"Wrote {len(rows)} held-out labels to {out_path} (seed={args.holdout_seed})")
        return 0

    _write_all()
    print(f"Wrote {TRAIN_N} labeled training rows to {DATA_DIR / 'train.csv'}")
    print(f"Wrote {TEST_N} unlabeled test rows to {DATA_DIR / 'test_features.csv'}")
    print(f"(Public fallback holdout seed for local iteration: {PUBLIC_FALLBACK_HOLDOUT_SEED} - "
          f"CI grades with a different, secret seed. See the use case README.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
