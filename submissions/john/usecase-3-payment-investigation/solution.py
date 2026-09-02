"""Payment ledger investigation - duplicates, orphaned refunds, and
over-refunds, computed in a single pass with exact integer-cent math.
See README.md for design rationale.
"""
from __future__ import annotations


def _parse_cents(amount: str) -> int:
    """Parse a decimal-string amount ("19.99") into integer cents without
    ever going through float - split on the decimal point instead.
    """
    sign = -1 if amount.startswith("-") else 1
    unsigned = amount.lstrip("-")
    dollars, _, cents = unsigned.partition(".")
    cents = (cents + "00")[:2]
    return sign * (int(dollars) * 100 + int(cents))


def investigate_ledger(events) -> dict:
    """Investigate a batch of charge/refund webhook events. See
    ../README.md for the exact output contract.
    """
    seen_event_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    dedup_events = []
    for event in events:
        if event.event_id in seen_event_ids:
            duplicate_ids.add(event.event_id)
            continue
        seen_event_ids.add(event.event_id)
        dedup_events.append(event)

    charge_cents: dict[str, int] = {}
    refunds_by_charge: dict[str, int] = {}
    for event in dedup_events:
        cents = _parse_cents(event.amount)
        if event.event_type == "charge":
            charge_cents[event.charge_id] = cents
        else:
            refunds_by_charge[event.charge_id] = refunds_by_charge.get(event.charge_id, 0) + cents

    orphan_ids = sorted(
        charge_id for charge_id in refunds_by_charge if charge_id not in charge_cents
    )
    over_refunded_ids = sorted(
        charge_id
        for charge_id, refunded in refunds_by_charge.items()
        if charge_id in charge_cents and refunded > charge_cents[charge_id]
    )
    net_cents = {
        charge_id: charge_cents[charge_id] - refunds_by_charge.get(charge_id, 0)
        for charge_id in charge_cents
    }

    return {
        "duplicate_event_ids": sorted(duplicate_ids),
        "orphan_refund_charge_ids": orphan_ids,
        "over_refunded_charge_ids": over_refunded_ids,
        "net_cents": net_cents,
    }
