# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Performance chart and CSV](docs/README.md) — static site prepared; enable GitHub Pages on `main /docs` to publish.

These views cover **two different wallets**. The Polymarket wallet also holds
pUSD cash, Polygon Aave deposits and POL gas; the crypto wallet's balance
alone is only part of the account. The dashboard below combines both wallets
and market positions without double-counting.

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only
the repository's vetted execution paths.

**Last maintained:** 2026-10-04. Portfolio figures below are a timestamped
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

## Last bankroll snapshot — 2026-10-04 18:07 UTC

| Measure | Value |
|---|---:|
| Unresolved position legs, including Trump dust | 5 |
| Position cost | $47.64 |
| Polymarket midpoint | $36.03 |
| Indicative depth/fee value | $32.93 |
| Authoritative whole-account mark | $187.73 |
| Approximate whole-account depth value | $184.63 |
| Cumulative settled P&L, before VM/API costs | +$22.52 |

The held **Clarity Act Senate vote monotonicity pair** remains 29 over-50 YES
plus 29 over-58 NO shares at $28.32893 all-in against a criteria-consistent
$29.00 payout floor; manage it only as a complete position. Its complete
exit is about $28.25. Both contracts retain their exact criteria; the current
official Senate HTML index lists 256 roll calls, with no qualifying final
passage found. Direct XML access returned 403, so a full XML row comparison
was unavailable. Voice-vote and unanimous-consent branches retain the paired
floor.

Remaining HLE holdings are **102.084750 Gemini >=50 NO** and **19 OpenAI
>=55 NO**. Their p(NO) priors remain **.12/.25**, stressed **.03/.15**.
Google's official
[Gemini 4 Argon announcement](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/)
contains no Pro label or HLE score. The resolving 60-row source is unchanged:
Gemini's maximum is 46.2, OpenAI's 53.6. These probabilities are judgmental
and remain uncertain. The separate September 22
[HLE-Diamond release](https://agi.safe.ai/blog/hle-diamond) reports scores on
a refined 1,000-question subset. The current homepage still connects its
HLE Accuracy chart to the original dataset/API. Diamond creates material
interpretation risk under the contracts' equivalent-metric clause; it has
not demonstrably replaced the resolving leaderboard. HOLD / NO ADD includes
that uncertainty.

The **Gemini Pro debut NO position is closed**, with zero on-chain balance.
Its .25 prior remains archived and the forecast is unresolved. Full fee-net
G/O exits are about **$2.00/$2.75** in the separate 18:09 quote. Central
joint models favor holding,
including partial-trim analysis and free Aave redeployment sensitivity.
The pessimistic model favors separate trims of about 23.45 Gemini
shares or sale of all 19 OpenAI shares; a full Gemini exit loses in that case.
Central probabilities reject full and partial exits. **HOLD / NO ADD**
remains a model-sensitive judgment, with no price-recovery assumption. Both
new buys fail pessimistic EV at current asks.

**0.33 Trump-out NO remains** in value, cost and claim-insurance records. Complete
authenticated inventory has **no open orders**. All **$47.319630 pUSD is
uncommitted**. Identity, transaction and source evidence are in
[`notes/resting_orders.md`](notes/resting_orders.md) and
[`notes/journal.md`](notes/journal.md).

About **$85.02 native aUSDC** earns the Polygon Aave supply rate (2.795% read
during this 18:00 run, variable); existing legacy aUSDC.e is about $3.50.
No additional cash transfer was made. The midpoint-to-depth gap in the
timestamped snapshot is about $3.10. Approximate whole-account depth value
excludes sub-lot dust from immediately executable cash and includes $6.83 of
separately funded gas. Excluding gas gives about **$177.80 versus $170 trading
capital (+4.59%)**, before VM/API operating costs. The separate Oct-4 weekly
review confirms UNI Arc proposal 102 is **queued, unexecuted** at 16:15 UTC;
its earliest eligible execution is Oct-5 11:59:35 UTC. Arc fee controls
were inactive in that 16:15 check. UNI $9.02 remains above the retained
$3.25 valuation review gate; queueing alone does not justify allocation.
The [weekly watchlist](notes/longterm_watchlist.md) adds ASML and explicit TSM
price-review gates; none of the 38 price gates was hit in the checked snapshots.
dYdX remains an unfunded venue candidate; the managed book has no deliberate
broad BTC/ETH/SOL allocation.

The strict Oct-1 passive benchmarks are **VT $178.95, VTI $181.40 and
SPY $182.00** for the same timed contributions. Current indicative trading depth
is **$1.15/$3.60/$4.20 below VT/VTI/SPY** at those dated values.
This comparison mixes timestamps and excludes operating costs;
see the current [`weekly report`](notes/pnl_weekly.md).

An archived Hormuz NO claim holds **.003571 winning shares**. At 18:17 its
gas/price estimate is $.005263, above the payout, using the earlier simulated
gas units rather than a new transaction simulation. The earlier
exact-asset redemption dry-run succeeded. Retain the unexpired claim for
lower fees; there is no cash need or expiry.
Standard CTF redemption now verifies the exact asset, collateral and positive
on-chain payout before preparing a transaction.

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

## Telegram

Outbound shell replies use `.venv/bin/python scripts/telegram.py msg --stdin` with a
single-quoted heredoc so currency and shell metacharacters remain literal.
Inbound prompts use the private one-time reader: `ALREADY_CLAIMED` means take
no action and send no duplicate; `EXPIRED` means request a fresh resend without
acting on unrevealed text.
