# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The local performance CSV now has 193 recorded observations from Apr-25
through Oct-16. Rounded reconstructions are labeled; unsupported historical
values stay blank. The [source audit](research/2026-10-06-performance-history.json)
records remaining gaps and accounting limits.

These views cover **two different wallets**. The Polymarket wallet also holds
pUSD cash, Polygon Aave deposits and POL gas; the crypto wallet's balance alone
is only part of the account. The dashboard below combines both wallets and
market positions without double-counting.

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only the
repository's vetted execution paths.

**Last maintained:** 2026-10-16. Portfolio figures below are a timestamped
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

The [compact current handoff](notes/current_context.md) indexes active work and
blockers with explicit review/expiry times and source hashes. The active lessons
guide is condensed; its [original ledger](strategy/archive/01_lessons_2026-10-12.md)
remains historical evidence. `scripts/context_packet.py` builds bounded packets
for four task scopes without loading full history or live state. Packets are
orientation only; the required strategy reads and live execution checks remain.

Writing default for replies, handoffs and maintained documents:

- Lead with the result; use concise bullets with one claim or action each.
- Preserve relevant facts, numbers, identities, dates, assumptions, uncertainty,
  conditions and evidence links. Shorten wording, not information.
- Keep a detail when it changes interpretation, a decision, uncertainty or
  verification; otherwise link supporting material instead of repeating it.
- Remove repetition and filler; retain enough grammar to read once. Use tables
  for comparisons and short headings for navigation; avoid cryptic shorthand
  and multi-topic bullets. Follow a specifically requested format when it differs.

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

On-demand copper research on Oct 10 verified Ostium XCU/USD and Hyperliquid
XYZ `xyz:COPPER` listings. Copper remains a [manual candidate](notes/longterm_watchlist.md):
recurring carry, the January horizon and route/eligibility requirements do not
establish an allocation. No position or new watcher was added.

## Last bankroll snapshot — 2026-10-16 ~14:02 UTC

The bankroll call ran 14:02:03.334702–14:02:19.171545 UTC. These are rounded,
sequential marks, not synchronized NAV or certified liquidation.

| Measure | Value |
|---|---:|
| Trading capital reference | $170.00 |
| Total marked bankroll | $196.74 |
| Gas token mark | $6.02 |
| Trading midpoint / fee-net depth | $190.72 / $188.90 |
| PM midpoint / fee-net depth | $33.49 / $31.67 |
| Whole-account approximate depth | $194.92 |
| Remaining open-position cost | $31.46 |
| Settled accounting residual | $18.69 |

Trading midpoint and depth declined $0.91 and $0.57 versus10:00; residual was
unchanged at rounded precision. These are sequential accounting marks, not cash
profit; VM/API costs are excluded. The weekly review is complete; next review
Oct23.

- Retain OpenAI NO19 and complete Clarity29/29; no add. The official board's
  OpenAI maximum remains HLE53.6<55. Judgmental NO priors remain .25 central,
  .15 stress, and .38 upper; stress favors O19 exit while central/upper hold.
  Captured POST book was .20 bid/.27 ask, with fee-net full exit $3.67840.
  The all-in ask .277884 exceeds the .25 central prior. Receipt age was104.43s at
  capture; this is planning only and needs a fresh signing-time rewalk. Clarity
  remains conditional on the unchanged $29 floor, but current pair exit/carry
  are unknown: C50Y books were stale at643.83s GET and644.16s POST, beyond the
  180s guard. C58N exit net26.59462 was current at9.32s but cannot price the
  full pair. Retention does not prove optimality.
- HLE API65 full raw objects, mounted bundle URL/bytes and default-HLE/separate-
  Diamond semantics match10:00. Google Argon is HLE55.6/Diamond56.9; OpenAI
  max53.6. API Age2319s is cache age, not publication time. Five held Gamma
  criteria/state fields, Senate256 rows, article cores and AA57/44 are unchanged.
  Three direct OpenAI pages returned HTTP403 coverage gaps. Gamma3072352 YES
  price snapshot moved .750→.765 (+1.5pp since10:00), with no criteria change.
- Gamma3072356 is final YES at fixed block95635991 (denominator1, YES1/NO0);
  4.034750 losing NO tokens remain at zero, with no rebook or burn. The required
  redeem-all call found0/4 winning positions, skipped one losing/uncertain row,
  and returned redemptions=[] with no broadcast; it was not a dry-run. Polygon
  block95635991 shows aUSDC122.098370 (+1,761 raw units) at APY3.1562647%;
  pUSD/CTF are unchanged. Hormuz dust payout .003571 remains below the
  .004671710756 point-gas estimate using dated simulation/current gas/rounded
  FX; no new simulation or broadcast.
- Routine19 ran once, all rc0; all38 main streams are timed/hashed and match
  their manifest; final position audit CLEAN4+1. Orders/UMA/watch/Ostium/overdue
  checks were quiet; 76 decisions remain pending. Two stat-only health attempts
  failed before inspection with captured raw output; a third succeeded once.
  Four current daemons remain; heartbeat1525s is within3600s cadence, news
  state101s old, disk free619.12MiB. The risk-summary helper first failed rc1
  because system Python lacked httpx, before network/account calls; the .venv
  invocation passed and the first raw streams were not retained. Root sent one
  material Telegram update1152; it was not repeated. See the [14:00 source report](logs/checkin_20261016T1400/sources/report.md),
  [discovery review](logs/checkin_20261016T1400/discovery/review.md),
  [root risk review](data/checkin_20261016T1400_risk.json), and
  [routine record](data/checkin_20261016T1400_routine.json).
- The bounded discovery review selected3031 unique conditions; page caps and
  filters leave incomplete coverage, with3028 current conditions lacking
  documented literal review. Fulham–Hull market5263885 is a factual source lead:
  the official fixture is Oct17 14:00 BST; scanner .530 matches Oddschecker’s
  AI Probability label, not proved bookmaker consensus. No forecast or entry
  follows. Narrow source-validation work is recorded in the backlog.

## On-demand Base stock-token review — Oct 9 11:10 UTC

Coinbase B20 AAPLc/MSFTc/NVDAc have small-ticket Slipstream quotes losing about
0.10% on a buy/reverse pair before gas and funding. MSFTc/NVDAc are
[manual on-chain candidates](notes/longterm_watchlist.md); no allocation was
made. Issuer redemption requires KYC vesting, so a no-KYC position relies on
DEX liquidity and must account for issuer controls and legal eligibility.
The measured route still needs a vetted Slipstream writer and a return thesis
through January. The review also repaired the existing Base Uniswap quoter
and Router02 call configuration; 15 focused tests passed. See the
[research and validation record](notes/journal.md).

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

The [Oct 12 opportunity-method review](research/2026-10-12-opportunity-method-review.md)
fixed discovery filter ordering, exposed incomplete coverage, removed the failed
favorite-population forecasts and diversified bounded basket quoting. The
[review workflow](strategy/03_opportunity_method.md) uses cheap factual triage,
then primary judgment on both-side economics and all accessible on-chain
alternatives. Wider discovery counts establish additional review work, not
profitable trades.

The [finite-context architecture](research/2026-10-12-finite-context-architecture.md)
adds an offline shadow prototype for reusable source analysis, versioned case
memory and joint-scenario projections. One eleven-contract replay reduced full
packet bytes by 41.1% with lossless supplied rules and tested invalidation. No forecast
quality, live edge or token-billing savings are established by that replay.

That implementation is an offline prototype. Live model-review routing and a
prospectively validated source-family strategy remain proposed work; neither
has been deployed as an automatic trading controller.

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
| [`notes/current_context.md`](notes/current_context.md) | Compact handoff with editorial expiry and source hashes |
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
