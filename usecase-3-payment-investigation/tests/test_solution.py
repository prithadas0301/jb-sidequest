"""Trusted test suite for use case 3. This IS the spec - do not edit (see
'Protecting the autoscoring engine' in the root README).

Spec being tested (see ../README.md for the candidate-facing version):

  investigate_ledger(events) -> dict with:
    "duplicate_event_ids"        sorted list, one entry per event_id that
                                  appears more than once in `events`
    "orphan_refund_charge_ids"   sorted list of charge_ids with a refund
                                  but no charge ANYWHERE in the batch
                                  (order in the input list doesn't matter)
    "over_refunded_charge_ids"   sorted list of charge_ids (that DO have a
                                  charge) whose total refunded amount
                                  exceeds the charge amount
    "net_cents"                  dict charge_id -> int cents remaining
                                  (charge - refunds), for every charge_id
                                  that has a charge event

  Duplicates (repeated event_id) must be deduplicated - counted once -
  before computing sums. All money math must be exact integer cents;
  amount strings always have exactly 2 decimal places.

The oracle below parses amounts via string splitting (never float) and is
used only to compute expected outputs for test inputs - not for grading
performance.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # this usecase dir

from data.generate_data import PaymentEvent, generate_ledger  # noqa: E402
from scoring.submission_loader import load_module  # noqa: E402


def _parse_cents_exact(amount: str) -> int:
    sign = -1 if amount.startswith("-") else 1
    s = amount.lstrip("-")
    dollars, _, cents = s.partition(".")
    cents = (cents + "00")[:2]
    return sign * (int(dollars) * 100 + int(cents))


def oracle_investigate(events: list[PaymentEvent]) -> dict:
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    dedup_events = []
    for e in events:
        if e.event_id in seen_ids:
            duplicate_ids.add(e.event_id)
            continue
        seen_ids.add(e.event_id)
        dedup_events.append(e)

    charge_cents: dict[str, int] = {}
    refunds_by_charge: dict[str, int] = {}
    for e in dedup_events:
        cents = _parse_cents_exact(e.amount)
        if e.event_type == "charge":
            charge_cents[e.charge_id] = cents
        else:
            refunds_by_charge[e.charge_id] = refunds_by_charge.get(e.charge_id, 0) + cents

    orphan_ids = sorted(cid for cid in refunds_by_charge if cid not in charge_cents)
    over_refunded = sorted(
        cid for cid, refunded in refunds_by_charge.items()
        if cid in charge_cents and refunded > charge_cents[cid]
    )
    net_cents = {cid: charge_cents[cid] - refunds_by_charge.get(cid, 0) for cid in charge_cents}

    return {
        "duplicate_event_ids": sorted(duplicate_ids),
        "orphan_refund_charge_ids": orphan_ids,
        "over_refunded_charge_ids": over_refunded,
        "net_cents": net_cents,
    }


def _run_submission(events: list[PaymentEvent]) -> dict:
    solution = load_module("solution.py")
    return solution.investigate_ledger(events)


def test_matches_oracle_on_a_generated_ledger():
    events = generate_ledger(n_charges=300, seed=11)
    expected = oracle_investigate(events)
    actual = _run_submission(events)

    for key in ("duplicate_event_ids", "orphan_refund_charge_ids", "over_refunded_charge_ids"):
        assert sorted(actual.get(key, [])) == expected[key], (
            f"'{key}' mismatch.\nExpected: {expected[key]}\nGot: {sorted(actual.get(key, []))}"
        )
    assert actual.get("net_cents") == expected["net_cents"], (
        "'net_cents' mismatch against the reference implementation"
    )


def test_out_of_order_refund_is_not_orphaned():
    """Webhook delivery order isn't guaranteed - a refund can arrive
    before its charge in the batch. Orphan status must be decided from
    the whole batch, not a single left-to-right pass.
    """
    events = [
        PaymentEvent("evt-refund-1", "refund", "CHG000001", "5.00", 1.0),
        PaymentEvent("evt-charge-1", "charge", "CHG000001", "20.00", 2.0),
    ]
    actual = _run_submission(events)
    assert "CHG000001" not in actual["orphan_refund_charge_ids"], (
        "a refund that arrived before its charge in the input was wrongly treated as orphaned - "
        "orphan status must be evaluated over the whole batch, not greedily as events are seen"
    )
    assert actual["net_cents"]["CHG000001"] == 1500


def test_duplicate_event_is_not_double_counted():
    events = [
        PaymentEvent("evt-charge-1", "charge", "CHG000002", "50.00", 1.0),
        PaymentEvent("evt-refund-1", "refund", "CHG000002", "10.00", 2.0),
        PaymentEvent("evt-refund-1", "refund", "CHG000002", "10.00", 3.0),  # redelivery, same event_id
    ]
    actual = _run_submission(events)
    assert "evt-refund-1" in actual["duplicate_event_ids"]
    assert actual["net_cents"]["CHG000002"] == 4000, (
        "the redelivered refund must be counted once, not twice - net should be "
        "5000 - 1000 = 4000 cents, not 3000"
    )
    assert "CHG000002" not in actual["over_refunded_charge_ids"]


def test_money_math_is_exact_not_float():
    """Ten refunds of 0.10 against a 1.00 charge sum to EXACTLY 1.00 in
    cents (100). Summed as float, 0.10 * 10 (or repeated += 0.10) does not
    reliably equal 1.0 in IEEE 754 - a naive float-based implementation is
    at real risk of flagging this as an over-refund (or under) that isn't
    real.
    """
    events = [PaymentEvent("evt-charge-1", "charge", "CHG000003", "1.00", 0.0)]
    for i in range(10):
        events.append(PaymentEvent(f"evt-refund-{i}", "refund", "CHG000003", "0.10", float(i + 1)))

    actual = _run_submission(events)
    assert actual["net_cents"]["CHG000003"] == 0, (
        f"expected exactly 0 net cents (1.00 charged, 10x 0.10 refunded), got "
        f"{actual['net_cents'].get('CHG000003')} - this is the classic float-money rounding trap, "
        f"use integer cents throughout, never float arithmetic on amounts"
    )
    assert "CHG000003" not in actual["over_refunded_charge_ids"], (
        "flagged as over-refunded when the refunds sum to exactly the charge amount - "
        "almost certainly a float precision artifact"
    )


def test_genuine_over_refund_is_still_caught():
    events = [
        PaymentEvent("evt-charge-1", "charge", "CHG000004", "10.00", 0.0),
        PaymentEvent("evt-refund-1", "refund", "CHG000004", "7.00", 1.0),
        PaymentEvent("evt-refund-2", "refund", "CHG000004", "7.00", 2.0),
    ]
    actual = _run_submission(events)
    assert "CHG000004" in actual["over_refunded_charge_ids"], (
        "a charge refunded for more than it was worth (14.00 refunded on a 10.00 charge) "
        "must still be flagged - fixing the float trap shouldn't make you stop catching real cases"
    )
