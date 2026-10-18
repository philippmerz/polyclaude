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

## Active in-depth review — Oct 17

The operator authorized primary in-depth valuations across the frozen 3,000-market
universe, retaining all candidates beyond clearly factual exclusions. The
[live index](research/2026-10-17-deep-review/INDEX.md) and
[resume checkpoint](notes/deep_review_checkpoint.json) update after each completed
evaluation. The first 100 substantive reviews are an inspection milestone; valued,
blocked and factual exclusions are reported separately. Earlier screens do not
reject markets or count as completed valuations.

The [first100 inspection report](research/2026-10-17-deep-review/MILESTONE_100.md)
was sent in chat and Telegram. At00:17UTC October18,167valuations,2blocked and327
factualexclusions are saved;2,504remainpending, no active case. Everycase updates the
index before the next. Fivepost-onlyBUYbids were independently verified LIVE,
zero-matched:ME02YES10@38c,CA06NO50@3c,MT01YES10@33c,NY01YES10@12c,
andToddAchillesIdahoSenateYES34@3c. Pending **$10.82**, uncommitted14.176890pUSD;
allcandidatebalances0. These are commitments, not purchases/profit. Anthropic
largestIPO NO5@62c was canceledzero-fill on unresolvedrevenueinputs; its old24/76
forecast requires review. Idaho20%central is speculative;maximumcashloss1.02,
source-regimeadversescenariosnegative. **Pullby00:00UTCOct20** beforeknownforum.
Read [entryfollow-up](research/2026-10-17-deep-review/candidate_followup.md),
[corrections](research/2026-10-17-deep-review/CURRENT_REVISIONS.md) and
[restingorders](notes/resting_orders.md). Lastfullheld-thesischeck22:00;
reviewbidseachtick/earliernews. CurrentSenatemodel D56/R43/Other1,DD52/RR15,
withwidespecificationranges; chambers producednoorder. NoISRG/Spotifyorder.

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

## Last bankroll snapshot — 2026-10-17 ~22:00 UTC

Bankroll own-component window22:00:36–22:00:52UTC. Rounded sequential marks
are not synchronized NAV or a freshness-certified liquidation; VM/API costs
are excluded. The separate positions command marked PM at30.80 rather than
bankroll's30.94 because its observation window differs.

| Measure | Value |
|---|---:|
| Trading capital reference | $170.00 |
| Total marked bankroll | $196.37 |
| Separately funded gas | $5.76 |
| Trading midpoint / indicative depth | $190.61 / $188.56 |
| PM midpoint / indicative depth | $30.94 / $28.89 |
| Whole-account approximate depth | $194.32 |
| Remaining open-position cost | $29.86 |
| Settled accounting residual | $19.53 |

Since18:00, trading midpoint/depth changed−$0.03/−$0.11; settled residual is
unchanged. Retain OpenAI HLE NO9 with priors25%/15%/38%; current23c/26c
book passed at20.00s byPOST, fee-net full exit2.00624. The conditional central
and upper cases hold; stress exits9. This is not calibrated joint optimization.
Clarity29/29 retains its conditional29 floor, but both books failed180s on
GETandPOST (about340/423s); there is **no current paired-exit price certificate**.
Keep both/noadd. AtPolygon95712709, pUSD24.996890/aUSDC122.112198 and live
variable Aave3.05351963%. Gemini50 is finalYES; losingNO4.034750 remains
zero value/no burn. Retain Hormuz0.003571dust: point gas0.00460968 exceeds
payout using dated175036units and roundedFX, not a new simulation.

All26 sampled sources were captured/hashed;65HLE objects, five Gamma rules,
256Senate rows and article/AA comparisons match18:00. OpenAI maximum53.6<55;
Diamond is separate. Three direct OpenAI pages returned403 coverage gaps.
Root consumed the knownCA06powder alert and Oct13partisanMTdebate release;
neither established a ballot/withdrawal change. No universal no-news claim.

Nineteen routine command types ran once;38timed streams verified. Eighteen
returned0; state audit returned1 for four priors attached to verified LIVE,
unfilled bids. These are expected pending-order judgments, not lost holdings;
no prior deletion or false closure note. Eight financial records were unchanged.
All four daemons are current; disk193.88MiB remains below512warning/above128
critical.81decisions pending,0overdue. WeeklyOct23/monthlyNov12 remain due;
next existing scheduled check02:00UTC. The finite in-depth review continues.
See [root judgment](data/periodic_20261017T2200_root_judgment.json),
[risk](data/periodic_20261017T2200_risk.json),
[sources](data/periodic_20261017T2200_sources.json),
[routine](data/periodic_20261017T2200_routine.json), and [journal](notes/journal.md).

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
