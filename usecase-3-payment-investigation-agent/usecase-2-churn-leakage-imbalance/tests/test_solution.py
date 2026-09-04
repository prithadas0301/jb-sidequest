"""Trusted test suite for use case 2. This IS the spec - do not edit (see
'Protecting the autoscoring engine' in the root README). Loads the
candidate's solution.py from SUBMISSION_DIR.
"""
from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # this usecase dir

from scoring.submission_loader import load_module  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
AP_FLOOR = 0.20
AP_TARGET = 0.45

# Scrubbed from os.environ before the candidate's module is ever imported -
# see usecase-5 in the hackit sibling project's docs for why this matters:
# a submission executes in this same process, so the secret must be gone
# from os.environ before that happens, not just "not used" by our own code.
_HOLDOUT_SEED = os.environ.pop("ML_HOLDOUT_SEED", None)


def _ensure_data():
    if not (DATA_DIR / "train.csv").exists() or not (DATA_DIR / "test_features.csv").exists():
        subprocess.run([sys.executable, str(DATA_DIR / "generate_data.py")], check=True)


def _true_labels() -> dict:
    sys.path.insert(0, str(DATA_DIR.parent))
    from data.generate_data import PUBLIC_FALLBACK_HOLDOUT_SEED, generate_test_labels

    if _HOLDOUT_SEED:
        return generate_test_labels(int(_HOLDOUT_SEED))
    print(
        "\nML_HOLDOUT_SEED not set - grading against the PUBLIC fallback seed "
        f"({PUBLIC_FALLBACK_HOLDOUT_SEED}) for local iteration. CI uses a "
        "different, secret seed - see the use case README."
    )
    return generate_test_labels(PUBLIC_FALLBACK_HOLDOUT_SEED)


def _test_customer_ids() -> list[str]:
    with (DATA_DIR / "test_features.csv").open() as f:
        return [row["customer_id"] for row in csv.DictReader(f)]


@pytest.fixture(scope="module")
def predictions():
    _ensure_data()
    solution = load_module("solution.py")
    preds = solution.train_and_predict(str(DATA_DIR / "train.csv"), str(DATA_DIR / "test_features.csv"))
    return list(preds)


@pytest.fixture(scope="module")
def average_precision(predictions):
    from sklearn.metrics import average_precision_score

    ids = _test_customer_ids()
    labels_by_id = _true_labels()
    y_true = [labels_by_id[cid] for cid in ids]
    return average_precision_score(y_true, predictions)


def test_predictions_shape_and_range(predictions):
    ids = _test_customer_ids()
    assert len(predictions) == len(ids), (
        f"train_and_predict returned {len(predictions)} predictions, expected {len(ids)} "
        "(one per row in test_features.csv, in order)"
    )
    assert all(isinstance(p, (int, float)) for p in predictions), "every prediction must be a number"
    assert all(0.0 <= p <= 1.0 for p in predictions), (
        "predictions must be probabilities in [0, 1] - return probability estimates, not hard labels"
    )


def test_average_precision_floor(average_precision):
    print(f"\nAverage precision on held-out set: {average_precision:.4f}")
    assert average_precision >= AP_FLOOR, (
        f"average precision {average_precision:.4f} is below the floor of {AP_FLOOR}. If this "
        f"scored much higher on your own train/validation split, look at "
        f"`cancellation_request_flag` - it behaves differently on the held-out set (see the README)."
    )


def test_average_precision_target(average_precision):
    assert average_precision >= AP_TARGET, (
        f"average precision {average_precision:.4f} is below the target of {AP_TARGET} "
        f"(floor {AP_FLOOR} still counts for partial credit)"
    )


# --- top_risk_customers -----------------------------------------------

def test_top_risk_customers_matches_reference():
    solution = load_module("solution.py")
    ids = [f"C{i}" for i in range(20)]
    probs = [round((i * 37 % 20) / 20, 3) for i in range(20)]  # deterministic pseudo-random-looking spread

    expected = [cid for cid, _ in sorted(zip(ids, probs), key=lambda pair: (-pair[1], pair[0]))[:5]]
    actual = solution.top_risk_customers(ids, probs, 5)

    assert actual == expected, f"expected top-5 {expected}, got {actual}"


def test_top_risk_customers_tie_break_is_customer_id_ascending():
    solution = load_module("solution.py")
    ids = ["C3", "C1", "C2"]
    probs = [0.5, 0.5, 0.5]  # all tied

    actual = solution.top_risk_customers(ids, probs, 2)
    assert actual == ["C1", "C2"], f"ties must break by customer_id ascending, got {actual}"


def test_top_risk_customers_n_larger_than_input():
    solution = load_module("solution.py")
    ids = ["C1", "C2"]
    probs = [0.9, 0.1]
    actual = solution.top_risk_customers(ids, probs, 10)
    assert actual == ["C1", "C2"], f"n larger than input should just return everything, sorted; got {actual}"
