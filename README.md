# polyclaude

- [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Polymarket wallet on DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
- [Separate crypto wallet on DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)
- [Live performance chart](https://philippmerz.github.io/polyclaude/) — [CSV and methodology](docs/README.md).

The chart now has 141 recorded observations from the Apr-25 inception through
Oct-8. Rounded reconstructions are labeled; unsupported historical values stay
blank. The [source audit](research/2026-10-06-performance-history.json) records
the remaining gaps and accounting limits.

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

## Last bankroll snapshot — 2026-10-08 02:03 UTC

The authoritative bankroll read ran 02:02:33.233–02:02:54.496 UTC. It reports
PM midpoint $36.76 and net depth/fee value $31.65. The separate positions run
(02:02:12.367–02:02:14.834) reported $36.76/$31.66, and quick status
(02:03:13.209–02:03:15.726) reported $36.76/$31.95. Sequential depth walks are
indicative rather than synchronized or guaranteed proceeds; the bank read had
no missing-token/provider warning.

| Measure | Value |
|---|---:|
| Unresolved position legs, including Trump dust | 5 |
| Position cost | $47.64 |
| Polymarket midpoint / bank depth | $36.76 / $31.65 |
| Authoritative whole-account mark | $188.09 |
| Approximate whole-account depth | $182.98 |
| Settled P&L accounting residual, before VM/API costs | +$22.54 |

The bank includes $6.42 of separately contributed gas. Excluding gas, indicative
trading midpoint is $181.67 and depth is $176.56, or +3.86% versus $170 before
VM/API costs. Trading midpoint is up $1.01 and depth is down $0.53 since Oct-7
22:00; settled P&L is unchanged. These figures do not represent settled cash.

The held **Clarity Act Senate vote monotonicity pair** remains 29 over-50 YES
and 29 over-58 NO shares, $28.32893 all-in against a $29 payout floor. Its
fee-net full exit is $28.2692 ($28.4543 with an optimistic free-carry
sensitivity), still below the floor. The Oct-8 criteria reread confirmed both
literal descriptions and the 29/29 floor; all 256 official Senate roll-call
rows remain unchanged. H.R. 3633’s only recorded vote is rejected cloture on a
motion to proceed, not final passage. **HOLD the complete pair / NO ADD**; never
manage either leg independently.

Remaining HLE holdings are **102.084750 Gemini >=50 NO** and **19 OpenAI >=55
NO**. Judgmental p(NO) priors remain **.12/.25**, stress **.03/.15**, with
upper **.25/.38** and the existing correlation scenarios. The current 60-row
source is unchanged; Gemini and OpenAI maxima remain 46.2 and 53.6. HLE-Diamond
still creates material equivalent-metric interpretation risk, and source
stability is not a calibrated posterior. Fee-net full exits are **$1.901821 /
$2.384044** for Gemini/OpenAI. The central joint model rejects full, partial and
combined trims, including the optimistic free-Aave-carry case. Stress separately
shows a small Gemini trim as a per-leg alternative (23.43 shares / $0.472834;
25.17 / $0.507953 with free carry); it is not a joint optimum, while the OpenAI
stress case favors holding. Both new buys fail the stress EV check. The planning
books were 3.07–36.90 seconds old within the 180-second guard; any later action
still requires a fresh rewalk. **HOLD / NO ADD**, without a price-recovery
assumption.

The **0.33 Trump-out NO** remains, with p(NO) 0.97 and no open orders. Its
Oct-8 reread matched the prior market description; an earlier resignation or
removal announcement qualifies, while temporary Section 3, unsustained Section 4
and impeachment without removal do not. The any-period/permanent-removal wording
tension remains an interpretation risk. The captured White House releases feed
showed Oct-7 presidential activity but no qualifying announcement; that is a
limited-source observation, not proof of universal absence. Historical
Congress/medical claims were not newly reverified.

All **$47.319630 pUSD** is uncommitted. Native Polygon aUSDC was **85.045147** at
block 95,146,631, up 0.001138 from the prior fixed-block reading; the live
supply rate was 2.844507%. The cached 2.85% marginal hurdle is 20 hours old and
is not the live reserve rate. Gemini's current mark is $0.046, down 70.6% on
cost; the drawdown alert remains. No overdue decision or new watchlist trigger.

UNI at $7.92 remains above its $3.25 review gate; AAVE at $174.11 remains above
$105. Both are WATCH, not entry instructions. The validated route prefers CoinGecko
and has a fresh DefiLlama fallback, but output omits which provider supplied
each quote and its update time. Proposal 102 remains Executed on two
Ethereum RPCs at block 26,144,560; Arc getter roles at block 24,826,640 match
the published TokenJar and fee adapters. Configuration does not establish
collections, releaser activity or sustainable net burn.

The Oct-8 official-source window returned HTTP 200 for all 24 captures. The HLE
API and all 60 parsed rows match the Oct-7 baseline; the five held market
identities/criteria/status fields and all 256 Senate rows are unchanged. One new
Google RSS article, about UK fuel prices, is unrelated to HLE. Captured structured
alerts had no qualifying post-22:00 entry; this check does not prove universal
absence of news. UNI/Arc configuration matches the published roles, with the
same limits on inferring fee collection or burn.

The corrected discovery review produced no lead for live pricing or entry. Its
primary comparison used the default top 80 and the thin-tail comparison used
liquidity 500; the earlier top-40/liquidity-100 captures were retained, then
corrected passes and offline packets were preserved. Primary and thin-tail
literal questions/descriptions were unchanged; their new criteria-object fields
were resolution-source additions only. Sports consensus produced no positive
lead above 3pp, and the consistency scan was incomplete. Omissions do not prove
market closure.

The archived Hormuz NO claim remains **0.003571** winning shares. Using the
Oct-8 gas price and prior 175,036-unit estimate gives indicative fees of about
$0.005054–$0.005065 against the payout; this was not a fresh gas simulation.
The Oct-8 indexed redemption dry-run found 0/7 winners and skipped three
losing/uncertain rows; nothing was broadcast. Four daemons were current and
unique. Disk was 404.8 MiB, below the 512 MiB warning and above the 128 MiB
critical threshold; the scoped capacity review found no safe obsolete artifact.

The routine's first position-state audit flagged overdue Trump criteria; a
follow-up reread also found Clarity criteria due, then both were reread and the
final audit was CLEAN. The initial audit returned rc=1. Follow-up command
intervals were not recorded, so no times are inferred from their capture-file
mtimes. Weekly P&L is due around Oct-9 and the monthly emergency-path/fee drill
around Oct-12. Off-chain stock/brokerage monitoring and its Sunday rotation
remain retired.

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
