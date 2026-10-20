# October20 01:40 UTC financial snapshot

**Authoritative bankroll $195.95 includes $5.80 separately funded gas; trading value $190.15 at midpoint / $187.95 at indicative fee-net depth.** Depth versus $170 trading contributions is +10.56%. Canonical `bankroll.py` producer:01:40:14.155441–01:40:29.969247UTC. Root verified its complete stdout and raw/gzip receipt. Quotes are sequential, rounded estimates, not synchronized NAV or guaranteed proceeds. VM/API costs are excluded.

- PM holdings:35.00 midpoint /32.80 indicative fee-net depth. Producer warning2.21 differs from separately rounded component subtraction2.20; preserve both and use explicit32.80. Calculation:195.95−5.80−35.00+32.80=187.95.
- Reported19.72 settled residual is accounting arithmetic, not independently audited cash profit. No financial mutation occurred during this producer.
- As01:40:30–31, four LIVE zero-matched BUYs commit7.70. Exact inventory/detail, exhausted126 authenticated trades, indexed positions and four reservations agree. This predates the subsequently detected Kimi fill; do not use it as current order state.
- Observation227 appends once, preserving226 existing CSV rows. The01:40:14Z plotting anchor is the producer window's start, not an exact source quote time. Later fill verification and a separate post-fill producer retain their own times.

[Producer/account evidence](../data/deep_review_20261017/work/tick012937_state_0140.json).
