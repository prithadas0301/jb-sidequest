"""Copy this file into your submissions/<your-name>/usecase-3-payment-investigation/
folder and implement investigate_ledger. See ../README.md for the full spec.

Required interface - do not change the signature:

    def investigate_ledger(events) -> dict:
        # each event has .event_id, .event_type ("charge"|"refund"),
        # .charge_id, .amount (string, e.g. "19.99"), .timestamp
        ...

Return a dict with exactly these keys:
    "duplicate_event_ids"        list[str] - event_ids seen more than once
    "orphan_refund_charge_ids"   list[str] - refunded charge_ids with no
                                  charge event anywhere in the batch
    "over_refunded_charge_ids"   list[str] - charge_ids refunded for more
                                  than the charge amount
    "net_cents"                  dict[str, int] - charge minus refunds, in
                                  integer cents, for every charge_id that
                                  has a charge event

Three things the tests specifically check that are easy to get wrong:

1. Order independence. Events are not guaranteed to arrive charge-first -
   a refund can appear before its charge in the input list. Whether a
   charge_id is "orphaned" has to be decided from the whole batch, not
   as you go.
2. Deduplication. The same event_id can appear more than once (a
   redelivered webhook) - it must be counted once, not once per
   appearance, when computing sums.
3. Money math. Amount strings always have exactly 2 decimal places.
   Parse them into integer cents directly (split on "." - don't go
   through float) and do ALL arithmetic in integer cents. Summing
   several float dollar amounts and comparing with `>` or `==` is the
   classic way this goes wrong - 0.1 + 0.2 != 0.3 in IEEE 754, and it
   gets worse the more values you sum.

A solution that scans the full event list once per refund to find its
matching charge will pass the correctness tests but fail the performance
benchmark on a large ledger - build a charge_id -> amount index first.
"""
from __future__ import annotations


def investigate_ledger(events) -> dict:
    # TODO: implement per the spec in ../README.md
    raise NotImplementedError
