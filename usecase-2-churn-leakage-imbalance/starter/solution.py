"""Copy this file into your submissions/<your-name>/usecase-2-churn-leakage-imbalance/
folder and implement both functions. See ../README.md for the full brief.
"""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder


def train_and_predict(train_csv_path: str, test_csv_path: str) -> list:
    """Train on train_csv_path, return a churn PROBABILITY (0.0-1.0, not a
    hard 0/1 label) for every row in test_csv_path, in the same row order.
    """
    train_df = pd.read_csv(train_csv_path)
    test_df = pd.read_csv(test_csv_path)

    # TODO: look at what's in train_df before you pick features. Not every
    # column that looks predictive on train actually generalizes - see the
    # README's "Why this is harder than it looks" before you decide what
    # to include.
    feature_cols = [
        "tenure_months", "monthly_spend", "num_support_tickets", "plan_type",
        "payment_failed_count", "days_since_last_login", "satisfaction_score",
        "auto_renew", "cancellation_request_flag",
    ]

    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    train_cat = encoder.fit_transform(train_df[["plan_type"]])
    test_cat = encoder.transform(test_df[["plan_type"]])

    num_cols = [c for c in feature_cols if c != "plan_type"]
    X_train = pd.concat([train_df[num_cols].reset_index(drop=True), pd.DataFrame(train_cat)], axis=1)
    X_test = pd.concat([test_df[num_cols].reset_index(drop=True), pd.DataFrame(test_cat)], axis=1)
    X_train.columns = X_train.columns.astype(str)
    X_test.columns = X_test.columns.astype(str)

    y_train = train_df["label"]

    # TODO: this dataset is imbalanced (churners are the minority class).
    # A model optimizing plain accuracy will happily predict "no churn"
    # for everyone and still look decent on accuracy alone - that's not
    # what's graded here (see the README's scoring table). Consider
    # class_weight, and don't assume the default threshold/behavior is
    # what you want.
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)

    probabilities = clf.predict_proba(X_test)[:, 1]
    return probabilities.tolist()


def top_risk_customers(customer_ids: list, probabilities: list, n: int) -> list:
    """Return the n customer_ids with the highest probability, sorted
    descending by probability, ties broken by customer_id ascending. Must
    stay efficient for `n` much smaller than `len(customer_ids)` - see the
    Performance row in the README.
    """
    # TODO: a full sort of everything just to keep the top n is exactly
    # the O(m log m) approach the performance benchmark is calibrated
    # against. Look at heapq.nlargest / heapq.nsmallest.
    raise NotImplementedError


if __name__ == "__main__":
    # Handy for manual iteration:
    #   python starter/solution.py
    from pathlib import Path

    data_dir = Path(__file__).resolve().parents[1] / "data"
    preds = train_and_predict(str(data_dir / "train.csv"), str(data_dir / "test_features.csv"))
    print(f"{len(preds)} predictions, first 5: {preds[:5]}")
