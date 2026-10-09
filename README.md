# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The chart now has 148 recorded observations from Apr-25 through Oct-9, including
68 eligible trading-midpoint and 61 eligible trading-depth observations. Rounded
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

## Last bankroll snapshot — 2026-10-09 06:03 UTC

Bankroll was read 06:03:23.747311–06:03:40.364471 UTC. Positions and quick status
at separate recorded intervals matched rounded PM values. These are sequential
estimates, not synchronized NAV or certified liquidation proceeds.

| Measure | Value |
|---|---:|
| Unresolved position legs, including Trump dust | 5 |
| Position cost | $47.64 |
| PM midpoint / indicative fee-net depth | $35.31 / $32.21 |
| Authoritative whole-account marked bankroll | $186.51 |
| Approximate whole-account depth | $183.41 |
| Settled-P&L accounting residual | +$22.55 |

The bank includes $6.29 separately contributed gas. Ex-gas trading midpoint is
$180.22 and depth $177.12, up $0.28 since 02:00 and +4.19% versus $170 before
unreconciled VM/API costs. The unchanged settled residual is a rounded accounting
estimate, not audited new profit. Midpoint-to-depth gap: $3.10.

**HOLD / NO ADD.** Clarity's complete 29/29 fee-net exit $28.269200 and optimistic
free-carry bound $28.461715 remain below its $29 floor. OpenAI full exit $2.7531
has central ΔElog −0.0079397449; central, upper and correlation cases hold.
Stress conditionally favors selling O19 while Gemini stays held; this is a
sensitivity, not a certified joint optimum. Its $0.2064 ask exceeds stress p=.15,
and Kelly +$4.25 is advisory. Gemini's GET 290.10s / POST 290.51s fail the 180s
freshness guard; current G exit and combined trim remain uncertified. Priors
and correlations remain judgmental and unchanged.

Exact CTF inventory and $47.319630 pUSD were unchanged at Polygon block 95,213,760.
Native aUSDC was 85.053192 (+.001160 since 02:00); variable Aave rate 3.002329%.
Resolved Hormuz dust remains below estimated gas; no new simulation or broadcast.
UNI $7.37 versus $3.25 and AAVE $168.43 versus $105 remain WATCH/no trigger;
quote providers and per-asset times were not emitted. Orders, UMA alerts,
Ostium trades/limits and overdue decisions were empty; state audit was CLEAN.

Held source checks match 02:00: HLE 60, Gamma 5 and Senate 256; HLE maxima remain
46.2 Gemini / 53.6 OpenAI. HTTP Age 83s is cache age, not dataset time. Final
correct-governor UNI state/tuple agree across two RPCs; Arc roles match but do
not prove net burn. Source accounting preserves 8 wrong-governor RPC-error
receipts and 1 worker-reported missing receipt: 32 known requests / 31 receipts,
35 integrity files; final validation passed. No new Google RSS item after 02:00
was captured. One new 04:32 Hormuz headline is unverified, impacts empty,
with no active position beyond resolved dust. No universal news-absence claim.

All 19 light routine types ran once with rc=0; 38 stream hashes were independently
verified. Four daemons were unique/canonical/current; disk 268.86 MiB in root's
health read and 265.27 MiB in capacity review, above 128 MiB critical / below 512 MiB warning;
no safe cleanup was found. No asset action, discovery/redemption run or repeat
Telegram. P&L next Oct 16, monthly drill Oct 12; issuer rotation remains unverified.
Off-chain stock/brokerage reviews remain retired.

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
