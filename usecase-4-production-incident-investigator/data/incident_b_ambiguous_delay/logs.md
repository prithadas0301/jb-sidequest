# Application logs — 2026-08-15

```
2026-08-15 08:55:02 INFO  order-service            Order created order_id=ORD-55021
2026-08-15 08:55:03 INFO  payment-gateway-adapter  Charge succeeded order_id=ORD-55021
2026-08-15 08:55:03 INFO  notification-service     Email queued order_id=ORD-55021
2026-08-15 09:41:38 INFO  notification-service     Email sent order_id=ORD-55021
2026-08-15 10:02:11 INFO  order-service            Order created order_id=ORD-55040
2026-08-15 10:02:12 INFO  payment-gateway-adapter  Charge succeeded order_id=ORD-55040
2026-08-15 10:02:12 INFO  notification-service     Email queued order_id=ORD-55040
2026-08-15 10:44:38 INFO  notification-service     Email sent order_id=ORD-55040
2026-08-15 11:10:02 WARN  notification-service     Queue depth elevated: 340 messages
2026-08-15 11:15:19 INFO  order-service            Order created order_id=ORD-55071
2026-08-15 11:15:20 INFO  payment-gateway-adapter  Charge succeeded order_id=ORD-55071
2026-08-15 11:15:20 INFO  notification-service     Email queued order_id=ORD-55071
2026-08-15 12:30:44 INFO  notification-service     Email sent order_id=ORD-55071
2026-08-15 13:02:07 INFO  order-service            Order created order_id=ORD-55090
2026-08-15 13:02:08 INFO  payment-gateway-adapter  Charge succeeded order_id=ORD-55090
2026-08-15 13:02:08 INFO  notification-service     Email queued order_id=ORD-55090
2026-08-15 13:58:51 INFO  notification-service     Email sent order_id=ORD-55090
```

Delays are consistently 40–75 minutes between "Email queued" and
"Email sent". No `ERROR`-level entries anywhere in this window, no
exceptions, no failed sends — every email does eventually go out. Payment
and order creation both complete normally and quickly.
