# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The chart now has 136 recorded observations from the Apr-25 inception through
Oct-7. Rounded reconstructions are labeled; unsupported historical values stay
blank. The [source audit](research/2026-10-06-performance-history.json) records
the remaining gaps and accounting limits.

These views cover **two different wallets**. The Polymarket wallet also holds
pUSD cash, Polygon Aave deposits and POL gas; the crypto wallet's balance
alone is only part of the account. The dashboard below combines both wallets
and market positions without double-counting.

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only
the repository's vetted execution paths.

**Last maintained:** 2026-10-07. Portfolio figures below are a timestamped
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
  Off-chain stocks and personal-brokerage research are outside this project.
- Normal Dec. 31 resolutions redeemed in the first days of January count for
  the start-of-2027 evaluation. Do not cross a costly spread merely to print
  cash on Dec. 31.
- Venues must be lawful and decentralized; no CEX or KYC venue.
- Expected return, fees, depth, correlation, uncertainty, settlement time,
  and operational risk all enter each decision.
- Scheduled runs are bounded. Cron and event watchers handle waiting between
  reviews.

## Last bankroll snapshot — 2026-10-07 06:02 UTC

Positions ran 06:01:28–33 UTC; bankroll ran 06:01:53–06:02:15 and matches
those PM fields. These are sequential readings without per-asset quote times.
A separate 06:02:31–34 quick status also showed PM midpoint $37.83 and depth
$35.97; the bankroll observation remains the financial snapshot.

| Measure | Value |
|---|---:|
| Unresolved position legs, including Trump dust | 5 |
| Position cost | $47.64 |
| Polymarket midpoint | $37.83 |
| Indicative depth/fee value | $35.97 |
| Authoritative whole-account mark | $189.25 |
| Approximate whole-account depth value | $187.39 |
| Settled P&L accounting residual, before VM/API costs | +$22.53 |

The held **Clarity Act Senate vote monotonicity pair** remains 29 over-50 YES
plus 29 over-58 NO shares at $28.32893 all-in against a criteria-consistent
$29.00 payout floor; manage it only as a complete position. Its complete
exit is about $28.25. Both contracts retain their exact criteria; the current
official Senate XML returned all 256 unique roll calls. H.R.3633’s only
recorded vote remains rejected cloture on a motion to proceed, not final
passage. Voice-vote and unanimous-consent branches retain the paired floor.

Remaining HLE holdings are **102.084750 Gemini >=50 NO** and **19 OpenAI
>=55 NO**. Their judgmental p(NO) priors remain **.12/.25**, stressed **.03/.15**.
The resolving 60-row source and all IDs/accuracy/calibration values are
unchanged: Gemini’s maximum is 46.2, OpenAI’s 53.6. Google’s official
[Gemini 4 Argon announcement](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-4-argon/)
contains no Pro label or HLE score. The separate September 22
[HLE-Diamond release](https://agi.safe.ai/blog/hle-diamond) uses a refined
1,000-question subset; the mounted HLE Accuracy chart still uses the
original dataset/API. Diamond creates material interpretation risk under
the contracts’ equivalent-metric clause. HOLD / NO ADD includes that risk;
source stability supplies no newly calibrated posterior.

The **Gemini Pro debut NO position is closed**, with zero on-chain balance.
Its forecast remains archived and unresolved. Full fee-net G/O exits are
about **$4.97/$2.75** in separate current planning quotes. Central joint models
reject full, partial and combined exits even with optimistic free Aave
redeployment. The pessimistic model separately favors all 102.084750 Gemini
shares or all 19 OpenAI shares, with or without
carry; these are not a joint optimum. **HOLD / NO ADD** remains a
model-sensitive judgment, with no price-recovery assumption. Both new buys
fail pessimistic EV at current asks. Gemini's later midpoint drawdown is
65.0%; this alarm remains subject to source and joint-risk review.

**0.33 Trump-out NO remains** in value, cost and claim-insurance records.
Complete authenticated inventory has **no open orders**. All **$47.319630
pUSD is uncommitted**. Identity, transaction and source evidence are in
[`notes/resting_orders.md`](notes/resting_orders.md) and
[`notes/journal.md`](notes/journal.md).

About **$85.04 native aUSDC** earns the variable Polygon Aave supply rate
(2.848% read during this run); legacy aUSDC.e is about $3.50. The
displayed midpoint-to-depth difference is $1.86; the tool prints $1.85 from
its less-rounded inputs. Excluding $6.53 of separately funded gas gives
indicative trading depth **$180.86 versus $170 (+6.39%)**, before VM/API costs.
This is up $3.62 since 02:00; settled P&L is unchanged. Trading midpoint
is $182.72, up $2.14. Exact held quantities and pUSD are unchanged; native
aUSDC 85.039548 accrued .001113 since the prior fixed-block check.

Two Ethereum RPCs confirm UNI Arc proposal 102 remains **Executed** at
block 26,138,587. Arc controls at block 24,684,740 retain the
[published TokenJar/fee-adapter roles](https://gov.uniswap.org/t/temp-check-protocol-fee-expansion-arc/26287).
Configuration alone does not verify collections, releaser activity or
sustainable net burn. UNI $8.17 remains above the $3.25 review gate;
no allocation follows from that milestone. The active project watchlist now
contains UNI and AAVE review gates (AAVE $175.68 versus $105). Current validated
CoinGecko quotes produced no fallback warning; individual provider timestamps
were not emitted by the watchlist command. Off-chain
stock/brokerage monitoring and its Sunday rotation were retired on Oct 6. See the
[`project watchlist`](notes/longterm_watchlist.md); the prior mixed research
is retained as a dated archive.
dYdX remains an unfunded venue candidate; the managed book has no deliberate
broad BTC/ETH/SOL allocation.

The strict Oct-1 passive benchmarks are **VT $178.95, VTI $181.40 and
SPY $182.00** for the same timed contributions. Current indicative trading
depth is **$1.91 above VT and $.54/$1.14 below VTI/SPY** at those dated values.
This comparison mixes timestamps and excludes operating costs;
see the [`weekly report`](notes/pnl_weekly.md).

An archived Hormuz NO claim holds **.003571 winning shares**. Its gas/price
estimate is about $.00501–.00502, above the payout, using current gas, the rounded
same-run POL mark and prior simulated gas units rather than a new simulation.
The Oct-7 02:02 indexed redemption dry-run found zero winning claims; current exact
claim quantities and resolution states are unchanged. Retain the archived
claim for lower fees; there is no cash need or expiry. Standard CTF redemption verifies exact
asset, collateral and positive on-chain payout before preparing a transaction.

The Oct-7 02:00 full discovery review emitted 1,295 context rows across 73 batches.
No verified entry surfaced. Both sports leads failed the uncertainty-adjusted
entry check after exact criteria, live books and fee review. Displayed VLR odds
also fail the uncertainty margin; OLIMPBET's direct page returned an app shell.
Arbitrage book coverage remains bounded and incomplete. Thin-tail cohort
parameters match the preceding scan, but shortlist omissions still do not
establish market closure. Two unheld Spanish-election contracts added tie-break
criteria; this supplies no calibrated fair-value edge.
Midpoints and sequential depth walks are planning estimates, not guaranteed
cash proceeds. The HLE source
returned HTTP200 on its initial request; its full captured dataset is unchanged.
This periodic check found no new source change, watchlist trigger or overdue
decision. Four daemons remain current and unique; disk was initially about
527 MiB and later 513 MiB, above the 512/128 MiB guards. No trade or extra
discovery run was warranted.
This bankroll read was complete without a token-valuation warning or retry;
individual asset-price timestamps
were not emitted. `.venv/bin/python scripts/bankroll.py`
is the authoritative marked total; `scripts/positions.py` supplies the
Polymarket depth view.

## Operating model

- **Reactive:** `news_watcher.py` and `opportunity_watch.py` monitor material
  events and can trigger a bounded review.
- **Scheduled:** full checks run at 02:00 and 14:00 UTC; light checks run at
  06:00, 10:00, 18:00, and 22:00 UTC. On-chain opportunity research is on demand.
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
| [`notes/longterm_watchlist.md`](notes/longterm_watchlist.md) | Project on-chain candidate review gates |
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
