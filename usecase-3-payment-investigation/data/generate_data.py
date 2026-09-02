"""Deterministic synthetic payment-ledger generator shared by the trusted
tests and the benchmark. Not something candidates need to run themselves.
"""
from __future__ import annotations

import random
from typing import NamedTuple


class PaymentEvent(NamedTuple):
    event_id: str
    event_type: str   # "charge" or "refund"
    charge_id: str     # the charge this event is about
    amount: str          # decimal string with exactly 2 places, e.g. "19.99"
    timestamp: float


def _fmt_amount(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def generate_ledger(
    n_charges: int,
    seed: int,
    duplicate_rate: float = 0.03,
    orphan_refund_rate: float = 0.02,
    over_refund_rate: float = 0.05,
    shuffle: bool = True,
) -> list[PaymentEvent]:
    """A mostly-clean ledger with three deliberately injected anomaly
    types: redelivered (duplicate) events, orphaned refunds (no matching
    charge anywhere in the batch), and genuine over-refunds. Deterministic
    for a given seed.
    """
    rng = random.Random(seed)
    events: list[PaymentEvent] = []
    ts = 0.0

    for idx in range(n_charges):
        charge_id = f"CHG{idx:06d}"
        amount_cents = rng.randint(50, 20000)  # $0.50 - $200.00
        ts += 1.0
        events.append(PaymentEvent(f"evt-charge-{idx}", "charge", charge_id, _fmt_amount(amount_cents), ts))

        if rng.random() < 0.5:
            if rng.random() < over_refund_rate:
                refund_cents = amount_cents + rng.randint(1, 500)
            else:
                refund_cents = rng.randint(1, amount_cents)
            ts += 1.0
            events.append(PaymentEvent(f"evt-refund-{idx}", "refund", charge_id, _fmt_amount(refund_cents), ts))

    n_orphans = max(1, int(n_charges * orphan_refund_rate))
    for i in range(n_orphans):
        ts += 1.0
        events.append(PaymentEvent(
            f"evt-orphan-{i}", "refund", f"CHGXX{i:06d}", _fmt_amount(rng.randint(50, 5000)), ts,
        ))

    originals = list(events)  # snapshot before adding redeliveries
    n_duplicates = max(1, int(len(originals) * duplicate_rate))
    for _ in range(n_duplicates):
        original = rng.choice(originals)
        ts += 1.0
        events.append(original._replace(timestamp=ts))  # same event_id, redelivered later

    if shuffle:
        rng.shuffle(events)

    return events
