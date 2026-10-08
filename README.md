# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The chart now has 145 recorded observations from the Apr-25 inception through
Oct-8, including 65 eligible trading-midpoint and 58 eligible trading-depth
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

## Last bankroll snapshot — 2026-10-08 18:03 UTC

The authoritative bankroll read ran 18:03:00.381656–18:03:16.646884 UTC:
PM midpoint $35.03 and fee-net depth $31.62. Positions (18:02:39.011187–
18:02:41.032596) and quick status (18:03:33.490882–18:03:36.049834) separately
reported those same rounded PM values; these sequential readings are not
synchronized. Depth is indicative, not guaranteed proceeds. The printed and
displayed PM gap is $3.41.

| Measure | Value |
|---|---:|
| Unresolved position legs, including Trump dust | 5 |
| Position cost | $47.64 |
| Polymarket midpoint / bank depth | $35.03 / $31.62 |
| Authoritative whole-account mark | $185.93 |
| Approximate whole-account depth | $182.52 |
| Settled P&L accounting residual | +$22.55 |

The bank includes $5.99 of separately contributed gas. Excluding gas, trading
midpoint is $179.94 and depth is $176.53, or +3.84% versus $170 on depth before
VM/API costs. Depth fell $0.07 since 14:00. The rounded accounting residual
rose $0.01; no cash or position transaction occurred, so this is not new settled
trade profit. These marks and sequential depth estimates are not settled cash or
certified executable liquidation proceeds.

The **Clarity Act Senate vote monotonicity pair** remains 29 over-50 YES and 29
over-58 NO shares, $28.32893 all-in against a $29 payout floor. Fee-net full
exit is $27.989524 ($28.177689 under the optimistic free-carry sensitivity),
still below the floor. **HOLD the complete pair / NO ADD**; never manage either
leg independently. All 256 official Senate rows and exact criteria matched the
prior review; H.R. 3633's recorded vote remains rejected cloture on a motion to
proceed, not final passage.

The HLE holdings remain **102.084750 Gemini >=50 NO** and **19 OpenAI >=55 NO**.
Retain judgmental p(NO) priors **.12/.25**, stress **.03/.15**, upper **.25/.38**,
and existing correlations. Source stability does not calibrate the posterior;
HLE-Diamond interpretation risk remains. OpenAI's fee-net full exit is
**$2.384044**; all central, stress, upper, and correlation cases favor hold at
this price. Kelly's midpoint advisory shows **+$5.10** toward OpenAI's individual
optimum, but the fresh all-in ask **$0.2064** fails the pessimistic EV check at
stress p=.15; **NO ADD**. Gemini's GET book age was **193.23 seconds** and its
one POST attempt **193.77 seconds**, outside the 180-second guard. No current
Gemini exit or combined trim is certified. OpenAI and Clarity quotes passed
freshness only at their receipts; later action needs a fresh rewalk. Gemini's
drawdown alert is **−81.4%**; its individual Kelly sizing delta is **−$8.71**.

Authenticated orders were empty, no decisions were overdue, UMA reported 0
alerts, and Ostium had zero trades/limits with no state change. Watchlist hits
were empty: UNI $7.04 versus its $3.25 review gate and AAVE $161.14 versus $105
remain WATCH. Per-asset quote providers/timestamps were not emitted. Native
Polygon aUSDC was **85.049712** at block 95,184,902, up 0.001139; instantaneous
native-USDC supply rate was **2.945411%**. All $47.319630 pUSD remained
uncommitted. The 0.003571-share Hormuz dust claim is below estimated gas of
$0.004682–$0.004692, using current gas and rounded POL value with prior
simulated units; no new simulation or broadcast occurred.

All **25 official-source captures** returned HTTP 200 and passed integrity
checks. HLE's 60 rows, 256 Senate rows, five Gamma identity/criteria/status
records, and UNI/Arc configuration matched 14:00. HLE's HTTP cache Age was
1,832 seconds, not dataset time. Two new Google RSS articles were reviewed and
contained no HLE/model-benchmark fact; source checks found no new structured
public alert after 14:00, which does not establish universal absence of news.
No priors changed. Four daemons were current and unique. Free disk was 329.89 MiB,
below the 512 MiB warning and above the 128 MiB critical threshold; no safe
obsolete cleanup candidate was found. The active CLI binary was retained; the
hourly guard stayed on its 24-hour warning cadence, and no daemon was restarted.

All 19 light-routine command types ran once with rc=0; all 38 captured stream
hashes verified. Kelly received the fresh $185.93 bankroll. Position state was
CLEAN. **HOLD / NO ADD; no position, order, cancel, signing, transfer, redemption,
or broadcast action occurred.** No discovery or redemption run was part of this
light check. Weekly P&L is due around Oct-9 and the monthly emergency-path/fee
drill around Oct-12. The off-chain stock/brokerage Sunday review remains retired.

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
