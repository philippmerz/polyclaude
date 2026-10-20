# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The local performance CSV now has 241 recorded observations from Apr-25
through Oct-20. Rounded reconstructions are labeled; unsupported historical
values stay blank. The [source audit](research/2026-10-06-performance-history.json)
records remaining gaps and accounting limits.

These views cover **two different wallets**. The Polymarket wallet also holds
pUSD cash, Polygon Aave deposits and POL gas; the crypto wallet's balance alone
is only part of the account. The dashboard below combines both wallets and
market positions without double-counting.

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only the
repository's vetted execution paths.

**Last maintained:** 2026-10-20. Portfolio figures below are a timestamped
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

## Active in-depth review — October20

**New bids paused until600 full valuations, followed by a comparative selection of the strongest candidates.** Current405valued; blocked/factual screens do not count. No early wildcard/add/repost/taker/bundle entry. Holdings remain managed; there are no open bids. Selected winners still need every live execution gate. [Operator entry policy](notes/entry_review_gate.json) · [Doctrine](strategy/00_philosophy.md#4-entry-pipeline-every-gate-is-an-ev-term-in-application-order).

**405 valued /19 blocked /383 factual /2,193 pending;807 base+77 revisions.** Cases490/492 add two valuations: LeBron USPeople tail upside fails selected cases; Wisconsin Republican governor34% is provisional and reverses under a credible competing model.493impeachment and494UAL load factor have named source gaps, not rejections. No active case;495 is next. The historical UAL39% scenario is not an adopted current forecast. [Checkpoint](notes/deep_review_checkpoint.json) · [Small phase30](data/deep_review_20261017/work/goal0030_RESUME.json) · [492review](research/2026-10-17-deep-review/evaluations/0492.md) · [494gap](research/2026-10-17-deep-review/evaluations/0494.md).

**Anthropic14 maker canceled; no purchase.** FiveNO49c/$2.45 posted09:35:39, verified LIVE/0matched, then canceled09:39:38 after a previously unreviewed Claude research lead surfaced in feed warmup. Final terminal, trade, index, CTF and cash checks prove zero fill; only its reservation retired. No automatic repost. Original3political bids were canceled zero-fill15:48; final15:55 reconciliation retired their reservations. [Action record](research/2026-10-20-anthropic-arena-order.md) · [Exact current orders](notes/resting_orders.md).

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

## Last audited snapshot — October20 21:03 UTC

**Indicative trading depth $183.90 versus $170 contributed (+8.18%); trading midpoint $187.56.** Canonical bankroll $193.57 includes $6.01 separately funded gas; same-producer PM midpoint/depth $33.60/$29.94. Producer ran21:03:41–58UTC. Rounded sequential estimates are not synchronized NAV, guaranteed proceeds or realized profit; the $19.72 accounting residual remains unaudited and VM/API costs are excluded. CSV241 preserves all prior240rows and flows. [Financial record](research/2026-10-20-2103-financial-snapshot.json).

22:01 focused safety check: **zero orders,127 complete trades, nine unchanged all-size position tuples** against21:03; no winning redeemable or financial writer. Seven commands returned0 with saved bounds and output hashes. Four daemons are current singletons; separately run UMA43refreshed/0alerts, hurdle4clear/0flagged, watchlistnohits, stateCLEAN, Ostium0→0. No new aggregate or wallet valuation; CSV241 remains unchanged. [Root review](data/deep_review_20261017/work/tick2200_root_review.json) · [Account evidence](data/deep_review_20261017/work/tick2200_account_ops.json).

Retain holdings; no additions or numeric prior changes. Eight later headlines were reviewed; the NYT forum link returned Google News HTML, so its article remains unverified. The earlier CNN story, read through KESQ/Scripps, reports qualitative coalition concerns and counterevidence rather than a new poll. Democratic vulnerability supports our held5NO. Limited reported forum remarks are available; a full transcript and original Rogers records remain gaps. [Alert decisions](data/deep_review_20261017/work/tick2200_alert_decisions.json).

21:03 fee-net exits Kimi/OR/MI/Messi=$1.00/$3.30/$1.50/$1.25 remain below selected terminal values $1.902125/$3.65/$1.70/$2 after dated Aave carry sensitivities; the22:01 tool reports matching exits. Broad-low cases favor sale; another3.80pp adverse Michigan selected shift reverses the decision. Exact structured Gamma/compact CLOB0fee proof remains dated21:03, not a venue-wide claim or new execution certificate. Whole Clarity conditional payout29/58, or0 under venue/oracle failure, exceeds the22:01 tool's $26.25 group exit; no leg-only sale. [Dated math](data/deep_review_20261017/work/tick210121_hold_exit_math.json).

22:01 HLE request returned403: current scores are unknown. Last successful21:02 response had66rows/K3accuracy41.08/calibration44.67 and a cache-age caveat; failure is not a No result. OpenRouter21:02 completedOct12=164.043986T/currentOct19partial48.828344T; held future weeks absent, cache time not usage cutoff. The dated Senate list endsSep30; Sep15HR3633 cloture is not final passage. Discovery remains incomplete14UTCscans/81batches. No new research valuation or Telegram; BUYpause405/600+comparison stays. Next existing02UTCfullcheck/earlier material event; Michigan debateOct21 23UTC. [Current source gap](data/deep_review_20261017/work/tick2200_sources.json) · [Dated sources](data/deep_review_20261017/work/tick210121_resolving_sources.json).

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
