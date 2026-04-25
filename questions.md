# Questions for the operator

> I will append questions here as they arise. Most recent at the top. Mark as RESOLVED when you respond.

## Open

(none — all kickoff questions resolved)

## Resolved

### Q2 (2026-04-25) — Small POL top-up for gas — RESOLVED 2026-04-25
Operator sent 53.85 POL (way more than the 0.5 needed). All 6 allowances set on-chain (USDC→Exchange/NegRiskExchange/NegRiskAdapter, CTF→Exchange/NegRiskExchange/NegRiskAdapter), ~0.04 POL gas used. ~53.81 POL remains as ample reserve.

### Q1 (2026-04-25) — Operating parameters — RESOLVED 2026-04-25
Operator confirmed:
- Nothing off limits, any legal market.
- One year from kickoff (2026-04-25 → 2027-04-25) is the evaluation window. Until then I have full latitude.
- Drawdown tolerance and risk appetite are my call.
- Gains do not need to stay on Polymarket — withdrawal/conversion at my discretion if it improves the operation.
- Weekly P&L + per-session journal cadence approved (operator added: weekly report must include the *full live decision-making log*, see `feedback_reporting_verbose` memory).
- Operator will read-only audit the wallet directly from time to time.

### Q3 (2026-04-25) — Sleeve split addendum — RESOLVED 2026-04-25
Operator: "allocate a third of the budget to 1-month eval instead of the aforementioned 1-year period." Implemented as two-sleeve architecture in `strategy/01_horizon_split.md`:
- Long sleeve: 2/3 ≈ $46.67, evaluated at the 1-year mark.
- Short sleeve: 1/3 ≈ $23.33, evaluated at the 1-month mark (2026-05-25).
