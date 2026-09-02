# Known issues

## KI-101: ConnectionPoolTimeoutException in payment-gateway-adapter

A `ConnectionPoolTimeoutException` in `payment-gateway-adapter` logs is a
known signature of an undersized connection pool relative to current
traffic. Cross-reference against the deployment history for any recent
change to the pool size configuration on `payment-gateway-adapter` — this
signature has recurred more than once (see previous incidents) and both
prior occurrences traced back to a pool size reduction.

## KI-088: Duplicate order creation on network retry

`order-service` can create duplicate orders if a client retries a
`POST /api/orders` call after a network timeout without an idempotency
key. Fixed in v2.3.8. Not relevant to payment gateway timeouts.
