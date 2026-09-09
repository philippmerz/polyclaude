# Emergency assessment and drills

Status: CURRENT safety reference; consolidated 2026-09-09 from the [historical operations runbook](../archive/operations-2026-09-09.md). Open only for a real incident or the monthly drill.

## Before an exit decision

Identify the exact exposed wallet, asset, chain and protocol. A news keyword is not evidence of exposure. Preserve grouped-position topology and verify live orders/claims; an unavailable API does not mean an empty wallet.

Three assessment layers:

1. **Independent corroboration:** inspect ≥3 independent sources; require ≥2 confirming the same event, preferring official incident reports. Repeated copies of one report are not independent.
2. **Market/protocol reaction:** inspect current quotes, withdrawals, TVL or contract balances and chain progress relevant to the failure. Historical alert thresholds were stablecoin price <$0.98 or >10% one-hour TVL drawdown; these are signals, not proof.
3. **On-chain verification:** read relevant balances, transactions, recent block progression and the affected contract/protocol state. A balance read alone cannot prove absence of exploit or solvency.

**Unknown stays unknown.** Gamma responding does not prove trading/withdrawals work; `eth_chainId` responding does not prove a sequencer is advancing. Do not convert timeout or silence into confirmation or permission. On disagreement, report the discrepancy immediately with timestamps and preserve the evidence.

Keep the response scoped to the verified affected assets and retain the existing three-layer sanity check. Record the evidence, decision and actual result; report failed gates and discrepancies. The original incident procedure is preserved in the [operations archive](../archive/operations-2026-09-09.md#emergency-exit-protocol); documentation consolidation does not create a different operator mandate.

## Existing financial write tools

| Script | Scope / principal hazard |
|---|---|
| `scripts/emergency_exit_polymarket.py` | Cancels orders and sells positions; confirm locked shares, full depth, fees, slippage and protected groups |
| `scripts/emergency_exit_ostium.py` | Closes Ostium positions; verify exact inventory and venue health |
| `scripts/emergency_bridge_to_safety.py` | Bridges USDC via Across; never route through the compromised bridge |
| `scripts/emergency_swap_usdc_to_eth.py` | USDC→WETH swap; preserve min-output, price and liquidity checks |

Do not write new emergency execution code under panic or broaden an exit to unaffected assets.

## Monthly checks

The next due date lives in [backlog](../../notes/backlog.md), not this reference. Inspect CLI/source before using dry-run: it must suppress approval, wrap, order, cancel and transaction side effects, not merely the final submission. Verify live inventory is nonempty when a test requires it; an empty loop is not a passed execution-path test.

Bounded verification includes offline tests, current public/read-only state, fee-distribution check via `pm_fees.py`, and inspected side-effect-free simulations. Confirm exact expected semantic results, plus unchanged order inventory and gas where relevant. The existing monthly procedure is preserved in the [dated backlog archive](../archive/backlog-2026-09-09.md).

Unfillable FOK submissions and deliberately invalid cancels are financial write requests, not read-only tests; record them as such and inspect their actual side effects. Dry-run success cannot establish the untested authenticated submission path; record that coverage limitation explicitly.
