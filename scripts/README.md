# Tool map

Open the relevant category, then the script's `--help`/source. Commands use repo `.venv/bin/python` unless noted. “Read” below means no financial transaction; some tools update caches, snapshots or analytical logs. Do not run the full aggregator for documentation-only work.

## Knowledge retrieval (local, read-only)

`python3 scripts/kb.py search "term"` finds bounded current-doc matches; `--history` includes research/audit history. `toc PATH` lists headings; `recent PATH --entries 2` reads recent dated entries; `read PATH --start N --lines 60` opens a slice. Every result has line numbers; truncation is explicit. [Knowledge map](../docs/INDEX.md).

## Portfolio and risk

| Tool | Use / caveat |
|---|---|
| `bankroll.py` | Only authoritative total: both wallets, PM, Aave, pUSD, stables and natives; disclose warnings |
| `positions.py`, `wallet_status.py`, `crypto_status.py` | Quantities/PM marks and depth estimates, sleeve balances |
| `polyclaude_status.py` | Convenience aggregator; not the full checklist or an aggregate-bankroll replacement; `--telegram` sends |
| `clob_v2.py orders`, `orderbook` | Authenticated current order inventory / public book, not historical fills |
| `uma_status_check.py` | Resolution-state and price alerts; failed/capped inventory = unknown |
| `ostium_client.py status`, `ostium_state_diff.py` | Perp inventory and changes |
| `check_marginal_apy.py`, `exit_analysis.py` | Prior-based expected carry and hold-vs-full-exit comparison, not automatic orders |
| `portfolio_kelly.py --constrained` | Joint-group reservations, budget/correlation-aware diagnostic sizing |
| `position_state_audit.py` | Live book vs priors, claims, triggers and holds; `--fix` changes local snapshots/expired acknowledgments only |
| `crux_coverage_check.py --quiet` | Finds unmatched news keywords; cannot prove coverage of the resolution crux |
| `source_freeze_check.py` | Validated source comparison; default HLE mode checks all result rows and both scores; other modes may be token-only |
| `brownian_bridge_fv.py` | Hazard-model diagnostic; “TRIM/SCALE_UP” depends on model assumptions, not transaction authority |

[Reporting definitions](../docs/reference/reporting.md) · [group/entry policy](../strategy/00_philosophy.md) · [orders policy](../notes/resting_orders.md).

## Discovery and research

| Tool | Scope / failure mode |
|---|---|
| `discover_markets.py` | Default plus thin-tail discovery; gross APY is win-assumed, not expected edge |
| `sports_pm_scan.py` | Mid-market/sports screen; supplied odds/URL dates do not prove fresh comparable consensus. Opt-in `--with-kalshi` is public evidence only |
| `macro_pm_scan.py --no-consensus` | Fed/CPI visibility; automated CME consensus is unreliable |
| `event_monotonicity_scan.py` | Exact-proposition/criteria/deadline-compatible ladders only; same event is not proof of a hedge |
| `polymarket_consistency_scan.py` | Bounded neg-risk keyset slice; report coverage, failures and unquoted legs. Sequential positives are provisional leads |
| `favorite_fade_scan.py` | Candidate surfacer only; population edge failed replication, printed edge is not a sizing prior |
| `limitless_arb_scan.py` | Bounded matched-leaf scan; identity/schema failure aborts publication; textual similarity is not equivalence |
| `limitless_arb_executor.py` | **Execution-disabled public quote inspector**, not a trader. Unknown fees, minima, freshness and criteria remain gates |
| `catalyst_check.py` | Targeted exact-Gamma-criteria underwriting; ambiguous/incomplete identity aborts before analysis |
| `world_state_digest.py` | Curated primary-source domains → themes; writes world-state log |
| `longterm_check.py` | Cyclical/secular/catalyst/margin framework; equities/multi-year research is operator IBKR-side |
| `watchlist_monitor.py` | Price triggers; `--auto-revet` launches bounded fresh fundamental checks, not buys |

Historical studies and rejected hypotheses: [research index](../research/INDEX.md). Weekly procedure: [check-in](../docs/checkin.md#weekly-long-term-review). Do not expand scans indefinitely after a clean bounded pass.

## Money-math / execution implementation

These descriptions map the implementation; preserve the existing strategy, execution and risk gates.

- `pm_fees.py`: canonical structured `feeSchedule`, per-fill `rate × [p × (1−p)]^exponent`; legacy rate caps do not override structured schedules.
- `book_walk.py`: pure per-level quantity/fee math; malformed/nonfinite inputs rejected. Numerical validity does not prove identity, freshness or synchronized execution.
- `position_groups.py`: fail-closed exact topology, equal-share/payoff checks and complete-group valuations; malformed members remain protected.
- `polyclaude_enter.py`: mandatory BUY proposal/reservation pipeline, robust edge, UMA gates, Kelly+ρ, 15% ticket /30% event/configured-cluster entry caps. Every authenticated resting BUY requires one matching atomic reservation; fills/cancels need affirmative reconciliation.
- `clob_v2.py`: v2 REST/EIP-712 signer. No raw BUY bypass; shared lock, one-time reservation claim and reconciliation tombstones. SELL/cancel/redeem modes are financial writes; `redeem-all --dry-run` is the inspection mode. Legacy `polyclaude_client.py` is not the v2 write path.
- Bundle mode reserves all component FOKs under lock before order one; validates one negRisk event, equal integer quantity, joint robust EV, full pending exposure, fees/minima/collateral/allowances and bounded rollback depth. No independent-leg action on protected groups.
- `spot_swap.py`: compares fee tiers, independently specified min-output, fresh post-approval quote without weakening the floor.
- `aave_deposit.py rate` reads yield; `supply/withdraw`, `across_bridge.py`, spot swaps and Ostium `open/close` are financial writes.
- [Emergency tools and assessment](../docs/reference/emergency.md); distinguish read-only simulation from actual write-path testing and document its side effects.

## Decision records

`decisions.py pending/list/summary` reads `notes/decisions.json`; add/update modes write it. `ledger_calibration.py` grades exact identities and final outcomes; original forecasts/quotes remain immutable. Own forecasts and matched-baseline rows have separate sample counts; missing data is not a zero. Atomic ledger replacement protects pre-replacement failures, not concurrent writers or directory-fsync durability.

## Dispatch / communications

`daily_checkin.sh` dispatches; canonical 11 steps are in [docs/checkin.md](../docs/checkin.md). `inject_prompt.sh` queues bounded scheduled prompts; `operator_start.sh` starts the operator. `operator_followup.sh` is only for a concrete uncovered reminder, never idle work; `cancel_followup.sh` cancels it.

Four daemons: news, opportunity, heartbeat, Telegram listener. `daemon_keepalive.sh` expects absolute-path launches. `check_usage.sh --brief` is the direct read-only quota probe. Telegram sender `telegram.py msg` sends externally; listener/inbox access follows the private-reader contract in [operations](../strategy/02_operations.md). No message for a flat tick.

Secrets resolve via `_paths.py`; never copy private credentials or state locations into public docs. Fetch errors must remain visible. Trade/evidence gates fail closed; “fail open” in a notification filter is **not** permission to trade on missing data.
