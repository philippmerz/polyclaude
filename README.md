# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The chart now has 146 recorded observations from the Apr-25 inception through
Oct-8, including 66 eligible trading-midpoint and 59 eligible trading-depth
observations. Rounded reconstructions are labeled; unsupported historical values
stay blank. The [source audit](research/2026-10-06-performance-history.json)
records the remaining gaps and accounting limits.

These views cover **two different wallets**. The Polymarket wallet also holds
pUSD cash, Polygon Aave deposits and POL gas; the crypto wallet's balance
alone is only part of the account. The dashboard below combines both wallets
and market positions without double-counting.

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only
the repository's vetted execution paths.

**Last maintained:** 2026-10-08. Portfolio figures below are a timestamped
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

## Last bankroll snapshot — 2026-10-08 22:02 UTC

The authoritative bankroll read ran 22:02:03.669681–22:02:19.912115 UTC:
PM midpoint $35.08 and fee-net depth $31.70. Positions (22:01:42.233233–
22:01:44.345314) and quick status (22:02:37.767700–22:02:40.553515) separately
reported the same rounded PM values. These sequential observations are not
synchronized NAV; depth is indicative, not certified liquidation proceeds.
The printed/displayed midpoint-to-depth gap was $3.38.

| Measure | Value |
|---|---:|
| Unresolved position legs, including Trump dust | 5 |
| Position cost | $47.64 |
| Polymarket midpoint / bank depth | $35.08 / $31.70 |
| Authoritative whole-account mark | $186.19 |
| Approximate whole-account depth | $182.81 |
| Settled P&L accounting residual | +$22.55 |

The bank includes $6.20 of separately contributed gas. Excluding gas, trading
midpoint is $179.99 and depth is $176.61, or +3.89% versus $170 on depth before
VM/API costs. Trading depth rose $0.08 since 18:00. The settled residual is a
rounded accounting estimate, unchanged since 18:00 and not audited trade profit.

The **Clarity Act Senate vote monotonicity pair** remains 29 over-50 YES and 29
over-58 NO shares against a $29 payout floor. Fee-net full exit is $27.989524;
even the optimistic free-carry sensitivity, $28.179269, remains below the floor.
All 256 Senate rows match the prior review. H.R. 3633's recorded vote 00234
remains rejected cloture on a motion to proceed, not final passage. **HOLD the
complete pair / NO ADD**; never manage either leg independently.

The HLE holdings remain **102.084750 Gemini >=50 NO** and **19 OpenAI >=55 NO**.
Retain judgmental p(NO) priors **.12/.25**, stress **.03/.15**, upper **.25/.38**,
and existing correlation scenarios. Source stability does not calibrate a
posterior; HLE-Diamond interpretation risk remains. OpenAI's fee-net full exit
is **$2.384044**; a full exit changes expected log wealth by −0.009939 in the
central case. Full/prefix exit tests favor hold in central, stress, upper, and
correlation cases. Kelly's midpoint advisory is
**+$5.11**, but the fresh all-in ask **$0.2064** fails the pessimistic EV check
at stress p=.15; **NO ADD**. Gemini's GET book age was **235.41 seconds** and its
one POST attempt **235.85 seconds**, both outside the 180-second guard. No
current Gemini exit or combined trim is certified. OpenAI and Clarity planning
quotes passed freshness only at their receipts; any later action needs a fresh
rewalk. Gemini's drawdown alert is **−81.1%**; its individual Kelly sizing delta
is **−$8.74**.

The exact held inventory and $47.319630 pUSD balance were unchanged. Native
Polygon aUSDC was **85.050858** at block 95,194,464, up 0.001146; the live
variable Aave rate was **2.976343%**. The marginal scan's 2.99% hurdle was cached
from 16 hours earlier. The 0.003571-share Hormuz dust is below estimated gas of
$0.004756–$0.004766 using current gas/POL value and prior simulated units; no
new simulation or broadcast occurred. Watchlist hits were empty: UNI $7.36
versus its $3.25 review gate and AAVE $167.61 versus $105 remain WATCH. Per-asset
quote providers/timestamps were not emitted.

Authenticated orders were empty with a terminal cursor; no decisions were
overdue. UMA reported 38 markets refreshed and 0 alerts; Ostium had zero orders
or trades. Position state was CLEAN. The source review verified 23 captures and
34 hashes: all 60 HLE rows remained unchanged, with maxima of 46.2 Gemini /
53.6 OpenAI. The HLE HTTP cache Age of 1,761 seconds is not dataset time. Senate's 256 rows
were unchanged. Five Gamma markets retained exact identities, rules, and state
despite changed raw hashes. UNI proposal 102 remained executed across two RPCs;
Arc role configuration matched, which does not prove net fee-funded burn. No new
RSS entries after 18:00 and no new structured public alerts; this is not proof of
universal news absence. No priors changed.

Four daemons had exactly one current healthy process each. Free capacity was
323.74 MiB in the worker view and 330.36 MiB in the root view, below the 512 MiB
warning and above the 128 MiB critical threshold. No safe obsolete cache was
identified; the active CLI binary was retained. All 19 light-routine command
types ran once with rc=0; all 38 stream hashes verified, Kelly used the fresh
$186.19 bankroll, and no discovery or redemption run was part of this light
check. **HOLD / NO ADD; no position, order, cancel, signing, transfer, redemption,
or broadcast action occurred.** Weekly P&L is due Oct-9; monthly emergency-path
and fee drill is due Oct-12. The off-chain stock/brokerage Sunday review remains
retired.

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
