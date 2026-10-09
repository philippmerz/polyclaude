# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The chart now has 151 recorded observations from Apr-25 through Oct-9, including
71 eligible trading-midpoint and 64 eligible trading-depth observations. Rounded
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

## Last bankroll snapshot — 2026-10-09 18:02 UTC

Successful bankroll interval 18:02:47.111395–18:03:02.911594 UTC; separate
positions and quick status matched rounded PM values. Sequential indicative
estimates are not synchronized NAV or guaranteed liquidation.

| Measure | Value |
|---|---:|
| Unresolved position legs, including Trump dust | 5 |
| Position cost | $47.64 |
| PM midpoint / indicative fee-net depth | $35.99 / $32.05 |
| Authoritative whole-account marked bankroll | $187.22 |
| Approximate whole-account depth | $183.28 |
| Settled-P&L accounting residual | +$22.55 |

Gas $6.31; ex-gas trading midpoint/depth $180.91/$176.97. Depth +$0.21 since
14:00, +4.10% versus $170 before unreconciled VM/API. Settled residual remains
a rounded accounting estimate. Midpoint-to-depth gap: $3.94.

**HOLD / NO ADD.** G/O judgmental priors remain .08/.25 (stress .01/.15).
Named HLE source60 rows/G46.2/O53.6 and AA Argon High57% unchanged. Current
G/O complete fee-net exits $1.3980/$2.5685: central and correlation joint
cases hold; 1% G downside favors selling. G/O asks fail pessimistic entry.
Clarity exit/free-carry $28.2692/$28.4741 remains below $29 floor. See the
[evidence and risk review](notes/journal.md).

Exact inventory/pUSD unchanged; native aUSDC85.056763 at Polygon95,242,552,
live Aave3.1702%. Orders, UMA, Ostium and overdue decisions empty; state CLEAN.
No asset action. All19 routine types pass on latest attempt; five initial
interpreter failures retained. Critical resolving-source checks passed; broader
capture partial with30 missing HTTP-metadata bodies. Four daemons current;
free189.88 MiB above128 critical/below512 warning, no safe cleanup. No new
Telegram/discovery/redemption. P&L nextOct16; monthly drillOct12.

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
