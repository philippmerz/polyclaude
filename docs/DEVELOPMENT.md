# Development and operations

Internal notes for someone running or extending this repository. The public project story lives in the root [README](../README.md). The performance chart method is in [README.md](README.md) in this directory.

## Mandate, in brief

Reference trading capital is **$170**, verified from the initial on-chain stablecoin receipts. Separate gas and funding costs are excluded; see the [`capital ledger`](../notes/capital_ledger.md). Positions are meant to fit a less-than-one-year holding horizon. Normal 31 December resolutions redeemed in early January still count for the start-of-2027 evaluation; do not cross a costly spread merely to print cash on 31 December. Venues must be lawful and decentralized. Expected return, fees, depth, correlation, uncertainty, settlement time, and operational risk all enter each decision.

## Entry and exit

New Polymarket buys go through `scripts/polyclaude_enter.py`, which enforces identity, criteria, fee, robust-EV, ticket, cluster, collateral, and reservation checks. Direct raw buys are blocked. Existing-position sells and verified cancels use `scripts/clob_v2.py`. Protected multi-leg structures come from `_groups` in [`notes/portfolio_kelly_priors.json`](../notes/portfolio_kelly_priors.json) and must be managed as complete economic positions.

`notes/entry_review_gate.json` is the live entry-gate configuration. A finished valuation list is not a token allowlist.

The `clob_v2.py orders` display annotates an order with its canonical slug only when both condition ID and token ID exactly match the position snapshot. Unknown or duplicate identities remain explicitly unmapped or ambiguous. Do not run `clob_v2.py cancel` on an order that is already absent from the live book: that can write a persistent reconciliation block.

Resting-order policy and the audit trail are in [`notes/resting_orders.md`](../notes/resting_orders.md). Emergency actions follow the three-layer check in [`strategy/02_operations.md`](../strategy/02_operations.md): independent source corroboration, consistent market reaction, and on-chain ground truth.

## Essential commands

```bash
.venv/bin/python scripts/polyclaude_status.py
.venv/bin/python scripts/bankroll.py
.venv/bin/python scripts/positions.py
.venv/bin/python scripts/wallet_status.py
.venv/bin/python scripts/crypto_status.py
.venv/bin/python scripts/clob_v2.py orders
.venv/bin/python scripts/exit_analysis.py
.venv/bin/python scripts/portfolio_kelly.py --constrained
```

The full catalog and usage notes live in [`scripts/README.md`](../scripts/README.md). `bankroll.py` omits wrapped Bitcoin, Hyperliquid HYPE, and Hyperliquid USDC; whole-account marks add those sleeves and exclude gas from trading value.

## Watchers and scheduled work

Reactive monitors watch for material news and armed opportunities. Ordinary news is reviewed on the next scheduled session; critical and safety leads can wake a bounded review immediately. Health checks watch daemon freshness, session progress, and disk headroom.

Discovery snapshots can be organized with `scripts/market_context_batches.py`. Offline batches carry no model or execution authority and do not replace a complete scanner, literal-criteria, or live-book review. Broad book scanners use `scripts/clob_books.py` against the public books endpoint; those snapshots are advisory, and any action still requires a fresh final book rewalk.

## Canonical records

| Path | Purpose |
|---|---|
| [`notes/backlog.md`](../notes/backlog.md) | Current work and dated triggers |
| [`notes/current_context.md`](../notes/current_context.md) | Compact handoff with editorial expiry and source hashes |
| [`notes/journal.md`](../notes/journal.md) | Chronological actions and evidence |
| [`notes/decisions.json`](../notes/decisions.json) | Structured decisions and outcomes |
| [`notes/portfolio_kelly_priors.json`](../notes/portfolio_kelly_priors.json) | Priors, clusters, and group topology |
| [`notes/resting_orders.md`](../notes/resting_orders.md) | Maker-order policy and audit trail |
| [`notes/position_condition_ids.json`](../notes/position_condition_ids.json) | Exact held-market identities |
| [`notes/pnl_weekly.md`](../notes/pnl_weekly.md) | Weekly performance reviews |
| [`notes/longterm_watchlist.md`](../notes/longterm_watchlist.md) | Project on-chain candidate review gates |
| [`notes/capital_ledger.md`](../notes/capital_ledger.md) | Contributions and external flows |
| [`notes/primary_sources.md`](../notes/primary_sources.md) | Curated world-state sources |

Repository layout: `strategy/` holds durable doctrine, `scripts/` holds tooling, `research/` holds dated audits, `notes/` holds operating state, and gitignored `data/` and `logs/` hold generated artifacts.

## Telegram

Outbound shell replies use `.venv/bin/python scripts/telegram.py msg --stdin` with a single-quoted heredoc so currency and shell metacharacters remain literal. Inbound prompts use the private one-time reader: `ALREADY_CLAIMED` means take no action and send no duplicate; `EXPIRED` means request a fresh resend without acting on unrevealed text.

## Security

Keys, wallet files, `.home/`, and `secrets/` stay private and must never be printed, pushed, or committed. Run gitleaks before every push. Do not commit `scripts/across_bridge.py` when it is dirty.
