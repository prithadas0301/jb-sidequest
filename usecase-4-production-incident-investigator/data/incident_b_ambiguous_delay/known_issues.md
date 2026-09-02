# Known issues

No known-issue entry matches "elevated queue depth with no error-level
logs and no correlated deployment." The single `WARN` entry in this
incident's logs (queue depth 340) is the only anomalous signal, and it
appears only once in the log window — not established as a known
recurring signature.

## KI-101: ConnectionPoolTimeoutException in payment-gateway-adapter

Unrelated: this incident's logs contain no `ConnectionPoolTimeoutException`
entries and no payment failures at all.
