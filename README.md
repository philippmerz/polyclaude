# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The local performance CSV now has 199 recorded observations from Apr-25
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

## Last bankroll snapshot — 2026-10-17 ~14:17 UTC

Bankroll own-component window: 2026-10-17T14:17:33.394116–14:17:49.150538 UTC.
These rounded sequential estimates are not synchronized NAV or a certified
liquidation; VM/API costs are excluded.

| Measure | Value |
|---|---:|
| Trading capital reference | $170.00 |
| Total marked bankroll | $196.27 |
| Separately funded gas | $5.86 |
| Trading midpoint / indicative depth | $190.41 / $188.15 |
| PM midpoint / indicative depth | $30.75 / $28.49 |
| Whole-account approximate depth | $194.01 |
| Remaining open-position cost | $29.86 |
| Settled accounting residual | $19.52 |

Since 10:00, trading midpoint/depth rose $0.07/$0.21 and residual rose $0.82 at
cent precision. Against the pre-trade 14:00 mark, midpoint/depth fell $0.46/$0.53;
the displayed OpenAI NO midpoint moved from $0.265 to $0.24 between sequential
snapshots. On the 10-share sale, $2.425 net proceeds exceeded the recorded $1.60
basis by about $0.825. The sale proceeds and residual movement are not a forecast
or a synchronized return measure.

The OpenAI NO position is now 9 shares after a verified FOK sale of 10 at $0.25
(gross $2.50, fee $0.075, net $2.425 pUSD). The order filled once; no open orders
remained. The transaction is `0x8119f07f1ab1008f0afd5693553f2f387932a5f13bce897ade650dcd43916b12`, included at Polygon block 95694171; balances verified at block 95694198. The 25%/15%/38% priors were unchanged. The conditional expected-log-growth grid showed a small central trim advantage, about 0.00030, assuming AI results and Senate votes were distinct drivers; a one-point probability shift or adverse correlation reverses it. Stress favored a full exit and the upper case favored holding. This was a partial risk trim, not a source-thesis break or a calibrated joint optimum.

Clarity remains 29/29, with no add. Its full-pair exit/carry is unknown: C58 GET/POST ages of 406.84/407.10 seconds exceeded the 180-second guard; the fresh C50-only net quote of $0.83624 at 64.38 seconds does not price both legs. Keep the conditional $29 floor and require a fresh paired quote before another decision.

The mounted HLE page still loads the same bundle/API, defaults to original HLE Accuracy and offers Diamond separately. All 65 raw objects match 10:00; Argon is 55.6 HLE / 56.9 Diamond and OpenAI maximum is 53.6, below 55. Three direct OpenAI pages returned 403 and remain coverage gaps. The five held Gamma criteria/state, 256 Senate rows, article cores and AA 57/44 are unchanged. RSS and each sampled last-80 public alert tail had no timestamped row strictly after 10:02; this is bounded coverage. API Age is cache metadata, not publication time.

The Gemini 50 market is final YES, but its 4.034750 losing NO shares remain at zero payout; no rebook or burn. The 10-share OpenAI sale left pUSD at $24.996890 and the other verified CTF balances unchanged. The $0.003571 Hormuz claim remains held. The $0.004605 gas estimate uses the dated 175,036-unit simulation and captured gas/rounded FX; no new simulation or broadcast.

All 19 routine commands returned zero; 38 streams are timed and hashed. The post-trade position audit is CLEAN after refreshing the recorded snapshot to 9 shares. Four daemons are current; the 14:02 health sample showed heartbeat age 1,447s within its 3,600s cadence, news age 105s, and 484.07 MiB disk space. That is below the 512 MiB warning and above the 128 MiB critical threshold. The prior bounded census found no safe disposable candidate; capacity remains unresolved and the hourly guard stays active. Seventy-seven decisions are pending, none overdue.

The 14:00 discovery was capped and filtered: 2,691 unique selected conditions, with 2,687 lacking a documented exact-criteria review. It identified two factual leads, neither validated for entry: Rays–Guardians has an 8:00 PM ET Gamma start versus MLB's 8:08 PM listing; Saints–Giants lacked a timestamped consensus quote and the scanner returned no consensus. The consistency screen validated 7 of 20 requested groups; 194 eligible groups were not requested. These are coverage limits, not market-wide absence. No probability or entry inference follows.

No new timestamped RSS or public alert-tail rows appeared after 10:02 in the bounded checks. Weekly review is next due Oct 23, monthly Nov 12, and the next light check is 18:00 UTC. Manual issuer-account credential rotation remains blocked. See the [check journal](notes/journal.md), [14:00 source report](logs/checkin_20261017T1400/sources/report.md), [14:00 discovery audit](data/checkin_20261017T1400_discovery.json), [post-trade verification](data/checkin_20261017T1400_posttrade.json), and [post-trade chain census](data/checkin_20261017T1400_posttrade_chain.json).

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
