# Submission — usecase-2-churn-leakage-imbalance

**Name**: John Smith
**Email**: john.smith@example.com
**Phone**: +65 8123 4567

## Design

Two independent pieces: `train_and_predict` (a RandomForest over
one-hot-encoded plan type plus the numeric behavioral features) and
`top_risk_customers` (a bounded-heap top-n selection, unrelated to the
model itself). I kept them fully separate — nothing in the second
function depends on how the first one works — since the brief frames them
as two different graded concerns (a modeling problem and a data-structures
problem) rather than one pipeline.

## My understanding of the problem

The headline difficulty isn't the modeling — RandomForest on this feature
set is a completely standard choice. It's `cancellation_request_flag`:
on the training data it's an unusually strong predictor of `label`, which
in a real system is exactly the kind of signal that's too good to be
trusted without asking *why* it's that good. A field that's essentially
"the customer already told us they're leaving" isn't predicting future
behavior, it's restating the outcome — and there's no guarantee (and no
way to check from the training data alone) that it's populated the same
way, or as reliably, at the point you'd actually want to make this
prediction in production. Separately, churn is a small minority of rows,
so anything that just chases accuracy will collapse to "predict no one
churns" and still look fine on the wrong metric.

## Why I took this approach

I dropped `cancellation_request_flag` entirely rather than trying to
downweight or partially trust it — I didn't have a principled way to
decide *how much* to trust a feature I already suspected of leaking the
label, and keeping it in "just a little" felt like it would still let the
model lean on it during training in a way I couldn't easily audit.
I used `class_weight="balanced"` rather than manual resampling
(oversampling/undersampling) because it's simpler to reason about and
doesn't risk duplicating or discarding real rows. I'm scored on average
precision rather than accuracy, so I didn't tune a decision threshold at
all — `predict_proba` is what's actually asked for.

For `top_risk_customers`, I used `heapq.nsmallest` with a
`(-probability, customer_id)` key rather than `heapq.nlargest` with a
custom reverse-string comparator — negating the probability and letting
`customer_id` sort ascending naturally gets the tie-break rule for free
without needing a wrapper class.

## What I'd try next with more time

Cross-validated hyperparameter search rather than fixed
`n_estimators`/`min_samples_leaf`, and a closer look at whether
`monthly_spend` needs to be bucketed by plan type rather than used raw,
since its range differs a lot between plans.
