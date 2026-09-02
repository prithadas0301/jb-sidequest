# Submission — usecase-3-payment-investigation

**Name**: John Smith
**Email**: john.smith@example.com
**Phone**: +65 8123 4567

## Design

Three passes, each O(n): first deduplicate by `event_id` into a clean
event list, then build two dicts (`charge_cents`, `refunds_by_charge`)
from that clean list, then derive orphans/over-refunds/net from those two
dicts. Building the index up front instead of searching the event list
per refund is what keeps this O(n) instead of O(n²).

## My understanding of the problem

Three separate failure modes hiding in what looks like a straightforward
aggregation: (1) a charge and its refund aren't guaranteed to arrive in
order, so "orphaned" can't be decided as you go — it can only be decided
after you've seen everything; (2) the same webhook can be redelivered, so
counting by event occurrence instead of by unique event_id silently
double-counts money; (3) amounts are decimal strings, and routing them
through `float` for summation or comparison is the single most common way
this kind of code is subtly wrong in production — it doesn't fail loudly,
it just occasionally reports the wrong number.

## Why I took this approach

I parse amounts by splitting on `"."` rather than `int(round(float(amount) * 100))`.
The float route usually works, but "usually" isn't good enough for money —
`float(amount) * 100` isn't guaranteed to land exactly on the integer
cent value for every possible input, and I'd rather not depend on
rounding behavior bailing me out. Splitting the string is exact by
construction and doesn't need a rounding step at all.

I dedupe by `event_id` before building any aggregates, not while building
them, so the aggregation logic never has to think about duplicates at
all — it's just working over a clean list. That felt easier to get right
than trying to make the aggregation itself duplicate-aware.

I kept `orphan_refund_charge_ids` and `over_refunded_charge_ids` as two
separate checks with no interaction — an orphaned charge_id never appears
in `over_refunded_charge_ids`, since there's no charge amount to compare
against. I considered treating "any refund with no charge" as trivially
over-refunded too, but decided that conflates two different problems a
reviewer would want to see called out separately.

## What I'd try next with more time

Right now a charge_id with two independent charge events (not a
redelivery — two different event_ids both claiming to charge the same
charge_id) isn't handled specially; the second just overwrites the first
in `charge_cents`. The brief doesn't generate that case, but a real
gateway integration would need an explicit decision about what that means.
