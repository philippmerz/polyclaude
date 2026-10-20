# October20 06:22 financial observation

**Canonical bankroll195.90 including5.81 separately funded gas; trading190.09mid/185.89indicative fee-netdepth versus170 contributed (+11.82%/+9.35%).** These are sequential rounded estimates, not synchronized NAV or guaranteed proceeds. The19.72 accounting residual is not independently audited cash profit; VM/API costs remain excluded.

- Producer: `scripts/bankroll.py`, actual call window2026-10-20T06:22:11.687442Z–06:22:29.705743Z. Same producer: PM36.14mid/31.94indicative fee-netdepth, marked unrealized+.37/depth−3.83. The4.20mid/depth gap is preserved.
- Derived trading values use only that producer:195.90−5.81=190.09;190.09−36.14+31.94=185.89. No balances or gas prices from another observation enter the aggregate.
- Same-producer displayed components: PM36.14; PM Polygon POL4.40, USDC.11, pUSD19.25, aUSDC.e3.50, aUSDC122.14; crypto Polygon POL.18, Arbitrum ETH1.00/aUSDC7.90, Base ETH.22/USDC1.05. Individually rounded cells need not sum exactly to the producer's total.
- Separate `positions.py` call06:22:29–34: PM36.14mid/31.82depth, open cost35.77, seven open rows; two resolved rows excluded. Its31.82 is a later estimate and is **not** substituted into the canonical aggregate. The over58 Clarity leg shows9pp average exit slippage; manage the equal pair as a whole.
- Wallet call06:22:34–38: pUSD19.251290 minus6.50 outstanding BUY commitments gives12.751290 arithmetic. This is not a venue collateral/allowance or execution certificate. Aave and both wallet balances were read; no transfer occurred.
- Authenticated06:22:49–50: three original LIVE0matched BUYs/6.50; separate order details match inventory/06UTC terms. All127 exhausted trade rows match earlier captures; nine public indexed condition/asset/outcome and quantity records are unchanged. No new fill. Fresh CTF proof is not claimed.
- Ostium:0 open trades/0 active limits/0 allowance. Redemption dry-run found0 winning claims; Whale0-payout and separate uncertain legacyGemini claims remain unburned.

[Account facts](../data/deep_review_20261017/work/tick060240_account_facts.json) · [Root verification](../data/deep_review_20261017/work/tick060240_verification.json) · [Hold/exit judgment](../data/deep_review_20261017/work/tick060240_primary_review.json).

Private receipt/body pairs preserve full command outputs and authenticated responses. CLI envelopes use the existing `sdk_result_serialization` enum but contain serialized stdout/stderr/returncode; they are not raw HTTP. Public source responses are separately labeled HTTP bodies. All timestamps are call-window bounds.

Performance CSV now has232 observations: one new check-window row from this producer preserves all231 previous observations and external contributions. No additional price request or financial action for the chart.
