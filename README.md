# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The local performance CSV has 337 recorded observations through Oct-26. Rounded
reconstructions are labeled; unsupported historical values stay blank. The
[performance source audit](research/2026-10-06-performance-history.json) records
remaining gaps and accounting limits. Two initial stablecoin receipts confirm the
$170 trading reference: $70 Polygon USDC.e on Apr-25 13:12:44 UTC and $100
Arbitrum USDC on Apr-29 19:16:57 UTC. Separately funded gas is excluded; an
unattributed $0.000099 inbound is not counted. [Funding audit](research/2026-10-25-initial-funding-audit.json).

These views cover **two different wallets**. The Polymarket wallet also holds
pUSD cash, Polygon Aave deposits and POL gas; the crypto wallet's balance alone
is only part of the account. The dashboard below combines both wallets and
market positions without double-counting.

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only the
repository's vetted execution paths.

**Last maintained:** 2026-10-26. Portfolio figures below are a timestamped
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

The [compact handoff](notes/current_context.md) indexes the completed selection,
current orders and dated financial evidence; check its expiry and source hashes.
The active lessons guide is condensed; its [original ledger](strategy/archive/01_lessons_2026-10-12.md)
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

## Completed-universe selection — October21

**The broad experiment ended at 422 completed unique valuations; no 600-case wait or queue continuation.** There is no active native goal (verified13:25UTC). Counts: 422 valued, 394 factual exclusions, 21 blocked, 2,163 unfinished pending; 837 base records plus 78 revisions. Case529 is unfinished and excluded. Policy v2 permits autonomous selection from the completed universe, subject to primary comparison, exact selected outcome tokens, hashed report and every live entry gate. [Policy](notes/entry_review_gate.json) · [Selection and comparison](research/2026-10-21-completed-review-allocation.json).

**Current allocation:** Delcy (#300) holds 28 YES/$5.04; October Fed no dissent (#179) holds 19.993158 YES/$4.798358 after two confirmed maker fills near 24¢; December Fed (#511) holds 20 YES/$3.80. pUSD is $5.612932; no visible open orders. The exact 179 order still returns JSON `null`, so its terminal state is unknown; keep the full $4.80 reservation and global BUY block. [Fill proof](research/2026-10-22-1208-fill-reconciliation.json) · [Latest order status](notes/resting_orders.md).

**Management:** Retain holdings; no add, trade, prior/date, control or decision-record change. Three explicit IDs and two post-boundary rows reviewed; Michigan and gas details remain linked to source facts. [Check](research/2026-10-26-1030-check.json).

## Mandate and constraints

- Reference trading capital: **$170**, verified from the initial on-chain
  stablecoin receipts. Separate gas and funding costs are excluded; see the
  [`capital ledger`](notes/capital_ledger.md).
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

## Last audited snapshot — October 26 10:31 UTC

**Bankroll:** $197.80 includes $5.64 gas. Trading $192.16 midpoint / $189.47 indicative fee-net depth (+11.5% return vs $170 reference, not vs prior); PM $51.79 / $49.10. Residual $19.79 is producer arithmetic, not verified settlement/profit. CSV has 337 rows, exact prior prefix; chart 10/10. [Snapshot](research/2026-10-26-1031-financial-snapshot.json) · [Funding audit](research/2026-10-25-initial-funding-audit.json).

**Account and protection:** 12 financial tuples, 132 trade IDs, selected balances and pUSD 5.612932 match prior; zero open orders. #179 API size is 19.9931 versus exact trade/CTF size 19.993158; HTTP 200/null leaves terminal status unknown. Keep its full $4.80 reservation and global BUY block; do not cancel/prune/repost/release/burn without affirmative terminal proof. Two zero-value claims remain unburned; DEC223 $1.02 is historical booked value. All six controls match baseline. [Check](research/2026-10-26-1030-check.json) · [Orders](notes/resting_orders.md).

**Risk and source:** Retain holdings. No fresh independent Michigan vote observation; gas evidence does not add a measured upward shock to the existing policy-risk model. OpenRouter’s repeated acquisition headline is not a new volume signal. [Check](research/2026-10-26-1030-check.json) · [Source review](data/deep_review_20261017/work/tick20261026_103014/combined_source_review.json).

**Review and operations:** Two rows post-boundary; three explicit requested IDs across six feed observations and 75 older selected rows reviewed. Caps and omissions do not establish absence. Twenty-three canonical CLI receipts include 21 rc 0 and two local pre-append failures; one separate wrapper collision occurred before child launch. 34 HTTP 200, two completed SDK results with unknown wire status and zero capture failures. UMA 0 alerts / 46 refreshed / 48 tracked. Next full 14 UTC, light 18 UTC; no active goal or idle follow-up.

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
- **Storage:** snapshots use compact gzip JSON; shared batch context is stored
  once. Scheduled check-ins losslessly archive closed artifacts. The
  [October21 pass](research/2026-10-21-storage-efficiency.json) reclaimed498MB
  while preserving exact evidence and financial hashes.
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
