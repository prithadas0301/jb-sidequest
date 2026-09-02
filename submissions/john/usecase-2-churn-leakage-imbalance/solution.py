"""Churn prediction (train_and_predict) + efficient top-n selection
(top_risk_customers). See README.md for design rationale.
"""
from __future__ import annotations

import heapq

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder

# Deliberately excluded - see README.md "Why I took this approach". On the
# training data this is suspiciously well correlated with churn; that's a
# reason to distrust it, not a reason to use it.
_LEAKY_COLUMN = "cancellation_request_flag"

_CATEGORICAL_COLS = ["plan_type"]
_NUMERIC_COLS = [
    "tenure_months", "monthly_spend", "num_support_tickets",
    "payment_failed_count", "days_since_last_login", "satisfaction_score",
    "auto_renew",
]


def _build_features(df: pd.DataFrame, encoder: OneHotEncoder, fit: bool) -> pd.DataFrame:
    cat = encoder.fit_transform(df[_CATEGORICAL_COLS]) if fit else encoder.transform(df[_CATEGORICAL_COLS])
    features = pd.concat([df[_NUMERIC_COLS].reset_index(drop=True), pd.DataFrame(cat)], axis=1)
    features.columns = features.columns.astype(str)
    return features


def train_and_predict(train_csv_path: str, test_csv_path: str) -> list[float]:
    """Train on train_csv_path, return a churn probability per row of
    test_csv_path, in order.
    """
    train_df = pd.read_csv(train_csv_path)
    test_df = pd.read_csv(test_csv_path)

    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    x_train = _build_features(train_df, encoder, fit=True)
    x_test = _build_features(test_df, encoder, fit=False)
    y_train = train_df["label"]

    clf = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
    )
    clf.fit(x_train, y_train)

    return clf.predict_proba(x_test)[:, 1].tolist()


def top_risk_customers(customer_ids: list[str], probabilities: list[float], n: int) -> list[str]:
    """Return the n customer_ids with the highest probability, descending,
    ties broken by customer_id ascending. O(m log n) via a bounded heap
    rather than sorting all m rows just to keep the top n.
    """
    selected = heapq.nsmallest(
        n,
        zip(probabilities, customer_ids),
        key=lambda pair: (-pair[0], pair[1]),
    )
    return [customer_id for _probability, customer_id in selected]
