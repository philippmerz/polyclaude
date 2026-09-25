# polyclaude

Autonomous, agent-directed trading pilot. The mandate is to maximize legal
expected compounded return through the start-of-2027 evaluation, using only
the repository's vetted execution paths.

**Last maintained:** 2026-09-25. Portfolio figures below are a timestamped
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
  Multi-year ideas route to the operator's personal brokerage watchlist.
- Normal Dec. 31 resolutions redeemed in the first days of January count for
  the start-of-2027 evaluation. Do not cross a costly spread merely to print
  cash on Dec. 31.
- Venues must be lawful and decentralized; no CEX or KYC venue.
- Expected return, fees, depth, correlation, uncertainty, settlement time,
  and operational risk all enter each decision.
- Scheduled runs are bounded. Cron and event watchers handle waiting between
  reviews.

## Last audited snapshot — 2026-09-25 22:03 UTC

| Measure | Value |
|---|---:|
| Unresolved position legs | 9 |
| Position cost | $132.30 |
| Polymarket midpoint | $118.37 |
| Indicative depth/fee value | $108.78 |
| Authoritative whole-account mark | $160.67 |
| Cumulative realized P&L | -$2.57 |

The held **Clarity Act Senate vote monotonicity pair** remains 29 over-50 YES
plus 29 over-58 NO shares at $28.32893 all-in against a criteria-consistent
$29.00 payout floor; manage it only as a complete position. Both legs now show
the same Jan. 2 operational end metadata while retaining the same written
before-Jan. 1 vote cutoff. The MetaMask monotonicity structure is likewise
managed only as a complete economic group. Sep. 25 Clarity articles recap the
already-reviewed Sep. 15 failed cloture vote; both contracts
explicitly exclude cloture and motions to proceed, so it does not change the
pair's resolution state or floor.

All other central-arithmetic exit screens remain holds after exit-cost,
stressed-prior and joint portfolio-risk review. Executed adverse flow across
the three HLE markets moved their p(NO) priors to **.15/.20/.25** for next
Gemini Pro debut, Gemini >=50 and OpenAI >=55. The exact source now has 63
rows. New GPT-6 Sol, Claude Opus 5.5 and Grok 4.7 rows have no HLE Accuracy;
scored Gemini remains below 50 and OpenAI below 55. Their $50.52 of central
terminal value exceeds $8.40 of current fee-net exits. The OpenAI leg remains a
hold at its .15 range floor, and the Dec. 31 hold-only rule blocks enlargement.
The source monitor retains the unscored identities and will report a later
score population as a change while malformed payloads continue to fail closed.
Apple's final executable balance closed on Sep. 25. A fresh .37 bid covered the
entire 8.925-share residual; the authoritative fee curve and carry valued an
exit near $3.229 versus $3.124 of central hold value, clearing the $0.089
one-tick materiality floor by only about $0.016. The venue accepted 8.92 NO
FOK for $3.217230 net and left 0.005077 token dust below its size precision.
Official Apple sources still showed no qualifying product, so this was a
price/carry exit rather than a thesis break; do not re-enter without a fresh
robust edge. The only live order is a zero-fill maker sell for **28 Trump-out
NO at 0.97**. Deployable pUSD is $22.608930. The midpoint-to-depth gap is
$9.59; the approximate whole-account depth-realizable value is $151.08. Duma
resolved and closed on Sep. 21; the next active portfolio catalyst is the exact
Arena Text Overall source snapshot on Sep. 30.

Midpoints and sequential depth walks are planning estimates, not guaranteed
cash proceeds. `.venv/bin/python scripts/bankroll.py` is the authoritative
marked total; `scripts/positions.py` supplies the Polymarket depth view.

## Operating model

- **Reactive:** `news_watcher.py` and `opportunity_watch.py` monitor material
  events and can trigger a bounded review.
- **Scheduled:** full checks run at 02:00 and 14:00 UTC; light checks run at
  06:00, 10:00, 18:00, and 22:00 UTC. Sunday rotates long-term source domains.
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
| [`notes/longterm_watchlist.md`](notes/longterm_watchlist.md) | Brokerage-side candidates |
| [`notes/capital_ledger.md`](notes/capital_ledger.md) | Contributions and external flows |
| [`notes/primary_sources.md`](notes/primary_sources.md) | Curated world-state sources |

Repository layout: `strategy/` holds durable doctrine, `scripts/` holds tooling,
`research/` holds dated audits, `notes/` holds operating state, and gitignored
`data/` and `logs/` hold generated artifacts.

Public sleeves: [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)
and [multi-chain wallet](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6).

## Telegram

Outbound shell replies use `.venv/bin/python scripts/telegram.py msg --stdin` with a
single-quoted heredoc so currency and shell metacharacters remain literal.
Inbound prompts use the private one-time reader: `ALREADY_CLAIMED` means take
no action and send no duplicate; `EXPIRED` means request a fresh resend without
acting on unrevealed text.
