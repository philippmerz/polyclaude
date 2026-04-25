# Questions for the operator

> I will append questions here as they arise. Most recent at the top. Mark as RESOLVED when you respond.

## Open

### Q2 (2026-04-25) — Need a small MATIC top-up for gas (BLOCKING for first trade)
The wallet has **70.00 USDC.e** ✅ but **0 MATIC**. Polymarket trading is gasless (orders are EIP-712 signed and relayed), but the *initial* on-chain approvals (USDC.e to the Exchange contract; CTF to the NegRiskAdapter) are real transactions that need MATIC for gas.

Please send **~0.5 MATIC** (≈ a few cents) to:

`0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B`

Any amount ≥ 0.2 MATIC works; 0.5 gives buffer for occasional withdrawals. After that, all trading is gasless.

Alternative paths I considered and rejected:
- Swap a tiny USDC.e → MATIC on a Polygon DEX: still requires MATIC to sign the swap → chicken/egg.
- EIP-2612 permit on USDC.e: the bridged USDC.e (0x2791…) on Polygon doesn't support permit. Native USDC (0x3c49…) does, but Polymarket settles in USDC.e.
- Public Polygon faucets: mostly dried up / require captcha + social account.

Sending MATIC is the cleanest one-time setup cost.

### Q1 (2026-04-25) — Confirmation of operating parameters
Just to make sure my mental model matches yours:
- Bankroll target: ~$60 USDC funded on Polygon. I'll verify the on-chain balance before trading.
- Horizon: 1 year from today (2026-04-25 → 2027-04-25). I will treat this as the *evaluation* window, but can hold positions that resolve at any time inside it.
- Drawdown tolerance: not specified. I will default to "Kelly/4" sizing and a soft rule that I never risk more than ~15% of remaining bankroll on a single uncorrelated thesis. **If you have a different risk appetite, tell me.**
- Withdrawal: I assume gains stay on Polymarket and compound. Confirm or override.
- Reporting cadence: I'll write a short journal entry into `polyclaude/journal/` after every trading session and a weekly P&L summary. Tell me if you want a different cadence.
- Restrictions: anything off-limits? (e.g. politicized US election markets, sports, specific people). I assume no restrictions unless you say so.

No need to answer right away — I'll proceed with the defaults above and adjust when you reply.

## Resolved

### Q1 (2026-04-25) — Operating parameters — RESOLVED 2026-04-25
Operator confirmed:
- Nothing off limits, any legal market.
- One year from kickoff (2026-04-25 → 2027-04-25) is the evaluation window. Until then I have full latitude.
- Drawdown tolerance and risk appetite are my call.
- Gains do not need to stay on Polymarket — withdrawal/conversion at my discretion if it improves the operation.
- Weekly P&L + per-session journal cadence approved.
- Operator will read-only audit the wallet directly from time to time.
