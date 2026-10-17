# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The local performance CSV now has 200 recorded observations from Apr-25
through Oct-17. Rounded reconstructions are labeled; unsupported historical
values stay blank. The [source audit](research/2026-10-06-performance-history.json)
records remaining gaps and accounting limits.

These views cover **two different wallets**. The Polymarket wallet also holds
pUSD cash, Polygon Aave deposits and POL gas; the crypto wallet's balance alone
is only part of the account. The dashboard below combines both wallets and
market positions without double-counting.

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only the
repository's vetted execution paths.

**Last maintained:** 2026-10-17. Portfolio figures below are a timestamped
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

## Last bankroll snapshot — 2026-10-17 ~18:04 UTC

Bankroll own-component window: 2026-10-17T18:04:08.931921–18:04:24.094923 UTC.
These rounded sequential estimates are not synchronized NAV or a certified
liquidation; VM/API costs are excluded.

| Measure | Value |
|---|---:|
| Trading capital reference | $170.00 |
| Total marked bankroll | $196.46 |
| Separately funded gas | $5.82 |
| Trading midpoint / indicative depth | $190.64 / $188.67 |
| PM midpoint / indicative depth | $30.98 / $29.01 |
| Whole-account approximate depth | $194.49 |
| Remaining open-position cost | $29.86 |
| Settled accounting residual | $19.53 |

Since 14:00, trading midpoint/depth rose $0.23/$0.52 and the settled residual
rose $0.01 at displayed precision. This is not a synchronized return measure.

Retain OpenAI NO 9 shares and Clarity 29/29; no trade or prior change. OpenAI
priors remain 25%/15%/38%. The receipt-time book was $0.25/$0.28, accepted by
GET at 51.76 seconds; fee-net full exit was $2.1825. With no carry, central and upper cases favor holding while stress favors selling
all 9. Idealized free Aave carry makes a 5-share central trim better by only
0.00000749 conditional log-growth; actual funding/deployment costs and joint-risk
calibration are unproven, so retain all 9. This is not a global optimum. Clarity's current paired
net exit was $26.83184 against a conditional $29 floor; even idealized free,
constant carry raises the exit only to $27.00151. Keep both legs and do not add.

At the fixed block, pUSD was $24.996890 and aUSDC $122.110518; live Aave rate
was 3.05530437%. The Gemini 50 market is final YES; its 4.034750 losing NO shares remain held at
zero payout/value, with no rebook or burn. Keep the $0.003571 Hormuz claim: the point gas
estimate $0.00447662 exceeds payout using the dated 175,036-unit simulation
and rounded FX; no new simulation or broadcast.

The bounded source check made 17 GET requests: 14 returned HTTP 200 and three
direct OpenAI pages returned 403, and the OpenAI news-browser source remains a
coverage gap. Existing official pages added no new threshold evidence. All 65 HLE
objects and sampled held criteria, Senate rows, article cores and AA 57/44 were
stable. No new sampled RSS/public-tail rows appeared; this is bounded coverage. The completed 3,000-row diagnostic
still has 217 source flags without follow-up and 2,716 unpriced rows; it does
not establish that opportunities are absent. No discovery or research scan ran
in this light check.

All 19 routine commands returned zero; 38 timed streams were hash-verified and
the position audit is CLEAN. Four daemons are current; heartbeat age was 1,613s
within its 3,600s cadence and news-state age was 32s. Disk free was 341.88 MiB,
below the 512 MiB warning and above the 128 MiB critical threshold; no cleanup
or restart was performed. Seventy-seven decisions remain pending, none overdue.
Weekly review is due Oct 23, monthly Nov 12, and the next light check is 22:00.
Manual issuer-account credential rotation remains blocked. See the [18:00 check
journal](notes/journal.md), [risk review](data/periodic_20261017T1800_risk.json),
[source report](logs/periodic_20261017T1800/sources/report.md), [source summary](data/periodic_20261017T1800_sources.json), [routine receipts](data/periodic_20261017T1800_routine.json), [finality check](data/periodic_20261017T1800_G_finality.json), and [gas check](data/periodic_20261017T1800_hormuz_gas_rpc.json).

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

On Oct 17, a finite diagnostic completed **3,000 primary-model first-pass
screens**, including 73 full literal-rule or PDF reviews and 17 family
investigations at varying depth. Most markets remain unpriced; this is not
3,000 fully underwritten rejections. The pass found and fixed a category-routing
bug: substring ETH matched “whether”, ordinary dollar thresholds matched crypto,
and “primary source” boilerplate matched politics. Forty-seven focused checks
passed. The frozen sample changed 971 labels; that is not a gold-set accuracy or
ROI result. Routine discovery had selected 2,691 conditions but documented only
four full literal reviews. Selection totals do not measure substantive coverage.
No new entry was justified by the detailed checks; no order was placed. See the
[individual ledger](research/2026-10-17-primary-market-review.csv),
[audit and case findings](research/2026-10-17-primary-market-review.json), and
[frozen public rules](research/2026-10-17-primary-market-review-rules.jsonl.gz).
The [review checkpoint](notes/market_review_checkpoint.json) indexes incremental
local ledgers and the unresolved queue for resumption after compaction.

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
