# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The local performance CSV now has 201 recorded observations from Apr-25
through Oct-18. Rounded reconstructions are labeled; unsupported historical
values stay blank. The [source audit](research/2026-10-06-performance-history.json)
records remaining gaps and accounting limits.

These views cover **two different wallets**. The Polymarket wallet also holds
pUSD cash, Polygon Aave deposits and POL gas; the crypto wallet's balance alone
is only part of the account. The dashboard below combines both wallets and
market positions without double-counting.

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only the
repository's vetted execution paths.

**Last maintained:** 2026-10-18. Portfolio figures below are a timestamped
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

## Active in-depth review — October 18

The operator authorized primary in-depth valuations across the frozen 3,000-market
universe, retaining candidates beyond documented factual exclusions. The
[live index](research/2026-10-17-deep-review/INDEX.md) and
[resume checkpoint](notes/deep_review_checkpoint.json) update after each completed
evaluation. The first 100 substantive reviews are an inspection milestone; valued,
blocked and factual exclusions are reported separately. Earlier screens do not
reject markets or count as completed valuations.

The [first100 inspection report](research/2026-10-17-deep-review/MILESTONE_100.md)
was delivered in chat and Telegram. The [milestone-200 report](research/2026-10-17-deep-review/MILESTONE_200.md)
remains the dated inspection record for that checkpoint. At the 10:39 UTC checkpoint, the frozen 3,000-market review had **213 valued, 3 blocked, 328 factual exclusions and 2,456 pending** across 544 records; case 113 is active and included in pending. This is progress, not a new milestone notification. Since pushed HEAD `33e9fac`, five records were appended: cases 96, 101, 106 and 112 valued; 97 factually excluded after official final MLB results. Case 112 is a priority investigation, not entry approval; its 9% YES estimate has a 0.5–80% sensitivity range after a concentrated countermodel, and the 15-point reserve is not a floor. Case 92 remains blocked because its complete post-creation CME active-month daily-high history is unresolved. The live [index](research/2026-10-17-deep-review/INDEX.md), [checkpoint](notes/deep_review_checkpoint.json) and [audit 1039](data/deep_review_20261017/ledger_audit_1039.json) govern status.

Nine valuations were added after milestone 200: 1602, 1607, 1826, 1910, 2058,
2077, 2153, 2822 and 2962. All 15 exact conditions in the compound source
manifest are now valued; shared oil, diplomacy and Senate inputs do not make
those cases independent. Case 2153's agreement cutoff is October 23, while
2077's is November 2. Cases 1910 and 2058 have different no-session branches:
1910 pays 50–50 on the whole binary, while 2058 uses the prior trading-day close.
Their reports preserve raw normalized-payout expected values 0.4173816971709 and
0.41696652982 and explicit raw EVs. The bounded EIA/CME observations are proxies;
preliminary CME CL is not the specified ICE Europe WTI/Pyth CLL fixing. See the
[compound source manifest](data/deep_review_20261017/remaining_compounds_manifest_0210.json),
[oil follow-ups](data/deep_review_20261017/oil_barrier_primary_facts_0230.json),
[terminal data](data/deep_review_20261017/oil_terminal_data_followup_0238.json),
[Senate follow-up](data/deep_review_20261017/senate_current_state_sources.json),
and [audit 0244](data/deep_review_20261017/ledger_audit_0244.json). No order or
financial prior was added from these nine valuations. Case 92 was separately
blocked after review because the April 30–October active-month CME High history
could not establish whether $147.27 had already been exceeded; its current price
and headline search do not prove no prior breach. The 03:00 CME browser timestamp
is approximate page-read time, not a timed HTTP capture; packet 0238 retains its
separate timed receipt. See [case 92](research/2026-10-17-deep-review/evaluations/0092.md)
and [incremental audit 0305](data/deep_review_20261017/ledger_audit_0305.json). Case 96 was completed at 0.5% YES, with no entry; its full rule, forecast, source analysis and dated quote economics are in [case 0096](research/2026-10-17-deep-review/evaluations/0096.md). Audit [0316](data/deep_review_20261017/ledger_audit_0316.json) checks its frozen identity and report hash, the 540-record ledger, CSV/checkpoint and protected financial files. The newer [oil option proxy crosscheck](research/2026-10-17-deep-review/models/oil_option_proxy_crosscheck_0325.md) adds preliminary CME CL DEC26 American-option sensitivities; they challenge the low-oil mass but do not estimate physical ICE Europe WTI/Pyth CLL probabilities or replace the dated joint cases. The separate [Oct. 18 fallback](research/2026-10-18-fallback-checkin.md) completed at 10:00 UTC; its 09:36 bankroll and order figures are dated, not a live account check. OpenRouter source correction: the public weekly API is a rolling-week, one-row-per-model-variant ranking; its 174.020765T and 168.339265T row sums are neither five daily observations nor displayed settlement totals. The DeepSeek rows match rounded displays 36.8T/35.9T. case 35 remains blocked on unavailable fixed Monday–Sunday history, not zero; see [case 112 source follow-up](data/deep_review_20261017/openrouter112_source_followup_1030.json).

Case 64 is valued at 30% YES, with a 5–80% range and a 20-point reserve. Root’s
review of four recent channel images/poster did not establish an authenticated,
newly captured appearance; the full video was not reviewed. See the individual
[case reports](research/2026-10-17-deep-review/INDEX.md), dated
[source follow-up](data/deep_review_20261017/mojtaba_appearance_primary_followup_0212.json)
and [image receipts](logs/deep_review_20261017/mojtaba_appearance_primary_followup_0213/manifest.json).

**Eight post-only BUY bids were LIVE and zero-filled in the 02:01:40 UTC check.**
This is a dated order-state snapshot, not proof of current status. Pending cash was
$14.72; arithmetic uncommitted pUSD was
$10.276890. The separate fixed-block proof at01:58:50–01:59:01/block95722257
confirmed all11 reviewed candidates have zero balances in both outcomes. The newest bid is Lionel Messi Global Athletes
TOP 5 YES, 5 shares at 27¢ ($1.35; DEC-0213). The other seven bids are the four
House bids, Idaho YES 34 at 3¢, Michigan Senate NO 5 at 31¢ and Sedgwick County
YES 5 at 20¢. These are commitments, not purchases or profit; full identities,
proofs and pull plans are in [resting orders](notes/resting_orders.md).

The [02:00 full held-source check](data/checkin_20261018T0200_sources.json)
found no change in 65 raw HLE model objects, the five held Gamma criteria, 256
Senate rows, or the compared Google article cores and AA HLE pair. The mounted
leaderboard still lists Gemini Argon at 55.6 and OpenAI Astra at 53.6; Diamond
is a separate metric. Gamma outcome-price snapshots moved from 75.5% to 77.5%
for OpenAI HLE 55%, from 5.5% to 5.0% for Clarity over 50, and from 8.0% to 7.5%
for Clarity over 58; these are API snapshots, not executable quotes. Gemini's
market remains resolved and closed. Three direct OpenAI pages returned HTTP 403
and remain coverage gaps. The bounded public alert review found no material or
critical held match; this does not establish global absence of news. No source
discovery was added.

Continue saving and indexing each primary valuation before beginning the next.
The last full held-source check completed
at 02:00 UTC; the next existing check is 06:00 UTC. Weekly and monthly reviews
are not due until October 23 and November 12. Entry verification does not replace
a scheduled full review. See [current revisions](research/2026-10-17-deep-review/CURRENT_REVISIONS.md)
and [root risk](data/checkin_20261018T0200_risk.json) for current judgments.

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

## Last audited snapshot — October 18, 09:36 UTC

The authoritative `bankroll.py` ran 09:36:31–09:36:46 UTC. Marks and books are
sequential, rounded observations, not synchronized NAV or certified liquidation.
VM/API costs remain unreconciled and excluded.

| Measure | Value |
|---|---:|
| Trading capital reference | $170.00 |
| Total marked bankroll | **$196.43** (−$0.05 since 02:01) |
| Separately funded gas | $5.83 |
| Trading midpoint / indicative depth | $190.60 / $188.44 |
| Polymarket midpoint / fee-net indicative depth | $32.47 / $30.31 |
| Whole-account approximate depth | $194.27 |
| Open-position cost / accounting residual | $31.41 / $19.53 |

The fallback verified **Michigan Senate NO 5 at 31¢**, $1.55 net spent, in the
[02:55:41 UTC receipt](https://polygonscan.com/tx/0x755f0bd530de3bd25f3f2a6dec18af06f41229b19ee25a629f1abeb20376d916).
There are five open PM legs: Michigan NO5, OpenAI HLE NO9, Clarity 29/29 and
Trump NO0.33. Retain them with no add; OpenAI's central/stress exit comparison
remains sensitive. No new order, sale, transfer or winning redemption occurred.

**Seven remaining BUY bids were LIVE and zero-filled:** four House bids, Idaho,
Sedgwick and Messi; $13.17 committed, pUSD23.446890, arithmetic free10.276890.
Michigan's fill reservation was reconciled and its claim insurance added.
Numerical priors/group topology are unchanged. The current held HLE API has65
unchanged model objects; OpenAI's maximum remains53.6<55. Access gaps remain.

All required discovery profiles ran once with explicit caps and unreviewed cases;
no new entry was certified. Four daemons passed exact-one/current-code checks.
Quota headroom was75%; Ostium has no trade, limit or allowance. Weekly P&L is
next due October23. See the [fallback check and risk record](research/2026-10-18-fallback-checkin.md),
[source facts](research/2026-10-18-fallback-sources.md),
[discovery coverage](research/2026-10-18-fallback-discovery.md) and
[order policy/current fill](notes/resting_orders.md).

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
