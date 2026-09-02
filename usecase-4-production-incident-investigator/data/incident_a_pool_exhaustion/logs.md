# Application logs — 2026-09-02

```
2026-09-02 09:14:03 INFO  payment-service          Charge request received order_id=ORD-88213
2026-09-02 09:14:03 INFO  payment-gateway-adapter  Acquiring connection from pool
2026-09-02 09:14:03 INFO  payment-gateway-adapter  Charge succeeded order_id=ORD-88213
2026-09-02 11:02:47 INFO  payment-service          Charge request received order_id=ORD-88301
2026-09-02 11:02:47 INFO  payment-gateway-adapter  Acquiring connection from pool
2026-09-02 11:02:48 INFO  payment-gateway-adapter  Charge succeeded order_id=ORD-88301
2026-09-02 14:30:00 INFO  deploy-agent             Deployment v2.4.1 completed on payment-gateway-adapter
2026-09-02 14:47:12 ERROR payment-gateway-adapter  ConnectionPoolTimeoutException: no available connection after 5000ms
2026-09-02 14:47:12 ERROR payment-service          Charge failed order_id=ORD-88350 reason=GATEWAY_TIMEOUT
2026-09-02 14:52:01 ERROR payment-gateway-adapter  ConnectionPoolTimeoutException: no available connection after 5000ms
2026-09-02 14:52:01 ERROR payment-service          Charge failed order_id=ORD-88351 reason=GATEWAY_TIMEOUT
2026-09-02 15:03:45 INFO  payment-gateway-adapter  Acquiring connection from pool
2026-09-02 15:03:46 INFO  payment-gateway-adapter  Charge succeeded order_id=ORD-88355
2026-09-02 15:11:09 ERROR payment-gateway-adapter  ConnectionPoolTimeoutException: no available connection after 5000ms
2026-09-02 15:11:09 ERROR payment-service          Charge failed order_id=ORD-88362 reason=GATEWAY_TIMEOUT
2026-09-02 15:22:30 ERROR payment-gateway-adapter  ConnectionPoolTimeoutException: no available connection after 5000ms
2026-09-02 15:22:30 ERROR payment-service          Charge failed order_id=ORD-88370 reason=GATEWAY_TIMEOUT
2026-09-02 15:40:02 INFO  order-service            Order created order_id=ORD-88375
2026-09-02 15:41:18 ERROR payment-gateway-adapter  ConnectionPoolTimeoutException: no available connection after 5000ms
2026-09-02 15:41:18 ERROR payment-service          Charge failed order_id=ORD-88375 reason=GATEWAY_TIMEOUT
```

Note the pattern: charges succeed normally all morning, then intermittent
`ConnectionPoolTimeoutException` failures begin appearing in
`payment-gateway-adapter`, starting shortly after the 14:30 deployment —
interleaved with occasional successes, not a hard outage.
