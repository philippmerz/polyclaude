# polyclaude

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only
the repository's vetted execution paths.

**Last maintained:** 2026-09-30. Portfolio figures below are a timestamped
snapshot; run the status commands for live state.

## Start here

1. Read [`MANDATE.md`](MANDATE.md).
2. Read [`strategy/00_philosophy.md`](strategy/00_philosophy.md) and
   [`strategy/01_lessons.md`](strategy/01_lessons.md).
3. Read [`strategy/02_operations.md`](strategy/02_operations.md) for wallets,
   daemons, Telegram, execution, and emergency procedures.
4. Run `.venv/bin/python scripts/polyclaude_status.py`.

This file is the current dashboard and entry point. Chronology belongs in
[`notes/journal.md`](notes/journal.md), pending work in
[`notes/backlog.md`](notes/backlog.md), and dated analysis in `research/`.

## Mandate and constraints

- Reference trading capital: **$170**. Separately contributed gas is tracked
  independently in [`notes/capital_ledger.md`](notes/capital_ledger.md).
- Each project position must fit a **less-than-one-year** holding horizon.
  Multi-year ideas route to the operator's personal brokerage watchlist.
- Normal Dec. 31 resolutions redeemed in the first days of January count for
  the start-of-2027 evaluation. Do not cross a costly spread merely to print
  cash on Dec. 31.
- Venues must be lawful and decentralized; no CEX or KYC venue.
- Expected return, fees, depth, correlation, uncertainty, settlement time,
  and operational risk all enter each decision.
- Scheduled runs are bounded. Cron and event watchers handle waiting between
  reviews.

## Last audited snapshot — 2026-09-30 22:05 UTC

| Measure | Value |
|---|---:|
| Unresolved position legs | 6 |
| Position cost | $89.91 |
| Polymarket midpoint | $77.41 |
| Indicative depth/fee value | $70.28 |
| Authoritative whole-account mark | $165.68 |
| Cumulative realized P&L | +$1.20 |

The held **Clarity Act Senate vote monotonicity pair** remains 29 over-50 YES
plus 29 over-58 NO shares at $28.32893 all-in against a criteria-consistent
$29.00 payout floor; manage it only as a complete position. Its complete
exit at the earlier 21:12 rewalk was about $28.25. The fresh lobbying article
supplies no qualifying final-passage vote, and both contracts retain their
exact criteria.

The three HLE p(NO) priors remain **.15/.20/.25** for next Gemini Pro debut,
Gemini >=50 and OpenAI >=55. The latest 60-row source matches the evening
research snapshot, with no qualifying new Pro row. Gemini's highest is 46.2
and OpenAI's 53.6, below the 50/55 bars. OpenAI's fee-net exit at the earlier
21:12 rewalk was about $3.31 versus $4.75
central and $2.85 pessimistic terminal value. No qualifying resolving update
was found. The correlated HLE positions remain **HOLD / NO ADD**; a joint
adverse source update can cause terminal losses. The Gemini debut 45/50
threshold alert was revalidated, but its signed fee-inclusive pair cost
moved to $1.12918 before execution, above its $1 payout floor. No new pair.

DEC-0182's post-only bid for **10 Swift album-2026 NO at 0.56** was
**cancelled unfilled** during the 22:00 check. Reconciliation completed at
22:09 UTC: terminal order state, exhaustive trade history, indexed buys and
on-chain balance all confirm zero fills. The $5.60 reservation is retired;
no trade fees or trading profit were incurred, and the unresolved album
forecast remains ungraded. No renewal or price chase. The sole live order is
the zero-fill maker sell for **28 Trump-out NO at 0.97**. All **$33.762410
pUSD is uncommitted**; there are still six held legs.
See [`notes/resting_orders.md`](notes/resting_orders.md) and
[`notes/journal.md`](notes/journal.md) for identity and source evidence.

Another **$35.00 native aUSDC** earns the Polygon Aave rate; existing legacy
aUSDC.e is about $3.50. The midpoint-to-depth gap in the timestamped
snapshot is $7.14; approximate whole-account depth-realizable value is
$158.54. This includes $6.97 of separately funded
gas; excluding it gives about $151.57 versus $170 trading capital (-10.8%),
before VM/API operating costs. The Sep. 30 Arena cutoff has passed: the exact
source still shows Anthropic first and market 3008499 is now UMA proposed.
The expired OpenAI entry watch is retired; proposal is not final settlement.
The next dated research review is UNI Arc after proposal 102's deadline at
block 26,109,012, estimated Oct. 3. dYdX remains an unfunded venue candidate;
the managed book has no deliberate broad BTC/ETH/SOL allocation.

Midpoints and sequential depth walks are planning estimates, not guaranteed
cash proceeds. `.venv/bin/python scripts/bankroll.py` is the authoritative
marked total; `scripts/positions.py` supplies the Polymarket depth view.
Crypto valuation uses complete, fresh CoinGecko batches with a high-confidence
DefiLlama fallback. Incomplete or stale batches fail visibly; emergency swaps
abort before approval if neither source passes validation.

## Operating model

- **Reactive:** `news_watcher.py` and `opportunity_watch.py` monitor material
  events and can trigger a bounded review.
- **Scheduled:** full checks run at 02:00 and 14:00 UTC; light checks run at
  06:00, 10:00, 18:00, and 22:00 UTC. Sunday rotates long-term source domains.
- **Health:** `heartbeat_watch.py` checks daemon freshness, session progress,
  and disk headroom.
- **Interactive:** authenticated Telegram messages enter the same ordered
  operator queue.

Discovery snapshots can be organized with `scripts/market_context_batches.py`.
Its offline batches carry no model or execution authority and do not replace
complete scanner, literal-criteria, or live-book review.

Broad book scanners use `scripts/clob_books.py` to chunk public `POST /books`
reads at the venue's 500-token limit and join only on `asset_id`. Missing,
conflicting, stale, malformed, or crossed books fail closed. These non-atomic
snapshots are advisory; any action still requires a fresh final book rewalk.

New Polymarket buys must use `scripts/polyclaude_enter.py`, which enforces
identity, criteria, fee, robust-EV, ticket, cluster, collateral, and reservation
checks. Direct raw buys are blocked. Existing-position sells and verified
cancels use `scripts/clob_v2.py`. Protected multi-leg structures come from
`_groups` in [`notes/portfolio_kelly_priors.json`](notes/portfolio_kelly_priors.json)
and must be managed as complete economic positions.

The `clob_v2.py orders` display annotates an order with its canonical slug only
when both condition ID and token ID exactly match the position snapshot. Unknown
or duplicate identities remain explicitly unmapped or ambiguous.

Resting orders are reconciled against the authenticated CLOB every check.
The news watcher includes validated pending BUY exposure as well as holdings;
unavailable Polymarket inventory passes alerts through for review.
Ordinary public-information positions may rest maker sells at or above fair.
Hidden-information positions require a documented premium strictly above fair;
all scheduled-catalyst orders are pulled before the event. See
[`notes/resting_orders.md`](notes/resting_orders.md).

Emergency actions follow the three-layer check in
[`strategy/02_operations.md`](strategy/02_operations.md): independent source
corroboration, consistent market reaction, and on-chain ground truth.

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

The full catalog and usage notes live in [`scripts/README.md`](scripts/README.md).

## Canonical records

| Path | Purpose |
|---|---|
| [`notes/backlog.md`](notes/backlog.md) | Current work and dated triggers |
| [`notes/journal.md`](notes/journal.md) | Chronological actions and evidence |
| [`notes/decisions.json`](notes/decisions.json) | Structured decisions and outcomes |
| [`notes/portfolio_kelly_priors.json`](notes/portfolio_kelly_priors.json) | Priors, clusters, and group topology |
| [`notes/resting_orders.md`](notes/resting_orders.md) | Maker-order policy and audit trail |
| [`notes/position_condition_ids.json`](notes/position_condition_ids.json) | Exact held-market identities |
| [`notes/pnl_weekly.md`](notes/pnl_weekly.md) | Weekly performance reviews |
| [`notes/longterm_watchlist.md`](notes/longterm_watchlist.md) | Brokerage-side candidates |
| [`notes/capital_ledger.md`](notes/capital_ledger.md) | Contributions and external flows |
| [`notes/primary_sources.md`](notes/primary_sources.md) | Curated world-state sources |

Repository layout: `strategy/` holds durable doctrine, `scripts/` holds tooling,
`research/` holds dated audits, `notes/` holds operating state, and gitignored
`data/` and `logs/` hold generated artifacts.

Public sleeves: [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
and [multi-chain wallet](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6).

## Telegram

Outbound shell replies use `.venv/bin/python scripts/telegram.py msg --stdin` with a
single-quoted heredoc so currency and shell metacharacters remain literal.
Inbound prompts use the private one-time reader: `ALREADY_CLAIMED` means take
no action and send no duplicate; `EXPIRED` means request a fresh resend without
acting on unrevealed text.
