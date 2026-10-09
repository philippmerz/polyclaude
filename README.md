# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The chart now has 147 recorded observations from Apr-25 through Oct-9, including
67 eligible trading-midpoint and 60 eligible trading-depth observations. Rounded
reconstructions are labeled; unsupported historical values stay blank. The
[source audit](research/2026-10-06-performance-history.json) records remaining
gaps and accounting limits.

These views cover **two different wallets**. The Polymarket wallet also holds
pUSD cash, Polygon Aave deposits and POL gas; the crypto wallet's balance alone
is only part of the account. The dashboard below combines both wallets and
market positions without double-counting.

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only the
repository's vetted execution paths.

**Last maintained:** 2026-10-09. Portfolio figures below are a timestamped
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

## Last bankroll snapshot — 2026-10-09 02:03 UTC

Bankroll was captured 02:03:23.556584–02:03:39.970070 UTC: PM midpoint $35.17,
fee-net depth $31.93, and total marked bankroll $186.32. Positions at
02:03:01.089513–02:03:05.365115 and quick status at 02:03:56.731343–02:03:59.179123
separately reported matching rounded PM values. These are sequential indicative
observations, not synchronized NAV or certified liquidation. Printed gap: $3.24.

| Measure | Value |
|---|---:|
| Unresolved position legs, including Trump dust | 5 |
| Position cost | $47.64 |
| PM midpoint / indicative depth | $35.17 / $31.93 |
| Whole-account marked bankroll | $186.32 |
| Approximate whole-account depth | $183.08 |
| Settled-P&L accounting residual | +$22.55 |

The bank includes $6.24 separately contributed gas. Ex-gas trading midpoint is
$180.08 and depth $176.84, down $0.58 on depth for the week and +4.02% versus
$170 before unreconciled VM/API costs. The rounded settled residual is an
accounting estimate, not audited new profit.

**HOLD / NO ADD.** The Clarity 29/29 pair's $27.989524 fee-net exit and $28.179213
free-carry bound remain below its $29 floor. OpenAI's $2.7531 fee-net full exit
has central ΔElog −0.0079397449; only the conditional G-held stress sensitivity
favors selling all 19 OpenAI shares (+0.000722507 without carry, +0.000826955
with carry). Gemini quotes aged 472.471079s (GET) and 473.054585s (one POST),
so no current Gemini exit or combined trim is certified. OpenAI ask $0.2064
exceeds the stress p=.15; Kelly +$4.25 remains advisory. Priors remain
judgmental and uncalibrated.

Exact CTF/pUSD inventory was unchanged; pUSD was $47.319630 at Polygon block
95,204,194. Native aUSDC was 85.052032 at that block, +0.001174 since Oct-8
22:00; the separate earlier routine read was 85.052023. Live Aave rate was
2.981704%. The 0.003571-share Hormuz winning dust is below gas estimated at
$0.004847–$0.004857; no new simulation or broadcast occurred. UNI $7.30/$3.25 and AAVE $166.43/$105 remained
above their maximum entry-review prices; watchlist had no hits and providers/times were unavailable.
Orders were empty, UMA had 0 alerts, Ostium had 0 orders/trades, and no decision
was overdue. No validated discovery entry emerged; consistency coverage was
limited to 14 of 181 live groups requested and only 3 quoted.

The source audit is partial: 24 receipts from 25 requests (22 HTTP 200, two
HTTP 429), with one UNI proposal response uncaptured. Held HLE/Gamma/Senate source checks passed; UNI dual-RPC validation remains
incomplete. HLE's 30-second HTTP cache age is not dataset time. One new Google/Lancet AMIE article at 22:30 was
not HLE; a Tier-2 Hormuz alert at 00:23 was unverified with impacts empty. Four
canonical daemons were healthy. Free capacity was 297.75 MiB, above the 128 MiB
critical and below the 512 MiB warning threshold; no safe cleanup was found.

The full routine had 20 types and 21 invocations: the initial state audit
returned rc=1, then one targeted follow-up returned CLEAN (rc=0); other routine
commands returned rc=0. All 42 stream hashes were independently verified. No position, order,
transfer, redemption, or broadcast action occurred. Weekly P&L is next due
Oct-16; monthly emergency-path and fee drill is due Oct-12. Credential-issuer
rotation remains unverified. Off-chain stock/brokerage review remains retired.

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
