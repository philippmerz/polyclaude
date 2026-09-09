# Polyclaude — Trading Doctrine (canonical compact edition)

> This is the live mandate. The pre-consolidation full text is preserved in
> `docs/archive/strategy-00-philosophy-legacy.md`; the companion lesson ledger
> is `strategy/01_lessons.md`, with its full historical text in
> `docs/archive/strategy-01-lessons-legacy.md`.

## Objective

Maximize expected compounded realized return on the bankroll over the project
horizon. Reinvestment makes expected log growth (Kelly), not a one-bet EV
leaderboard, the operative objective. Resolution is the cleanest cash
conversion: $1 per winning share, no spread or trading fee. Do not manufacture
a settlement by crossing a thin book merely to improve a report.

Lead performance reporting with indicative whole-account net liquidation versus
contributed capital, separating gas-token value and VM/other costs. Show the
authoritative marked bankroll and realized P&L as secondary decompositions;
neither is settled cash. Depth-walk estimates are sequential and indicative,
not synchronized or guaranteed executable proceeds. A metric informs judgment;
it never replaces it or changes a decision because a top-up/evaluation is
pending.

## Operator boundary conditions

- Legal, decentralized, no-KYC venues only; never optimize these constraints away.
- Positions held by this project must be under one year. Multi-year theses route
  to the operator’s IBKR sleeve through the watchlist process.
- The operator evaluates performance at the start of 2027. Positions resolving
  or redeeming in the first days of January count; do not force a value-
  destructive Dec-31 exit. Any possible ~$500 top-up is conditional on that
  evaluation, not current bankroll or sizing capacity.
- Public repository: no secrets, credentials, private paths, or raw tokens.
- Telegram and emergency-exit protocols follow `strategy/02_operations.md`.

## §3.1 Where edge may come from

1. Case-by-case, instance-level mispricing: read the literal resolution
   criteria, verify the load-bearing fact, run the catalyst check, price UMA
   ambiguity, and pass the robust-edge gate. Population favorite/longshot
   bucket harvesting failed replication at executable asks and is not an edge.
2. Decomposition, consistency, date/threshold monotonicity, and cross-venue
   arbitrage are worth scanning because they cost little, but act only on
   exact proposition identity, live books, depth, fees, and a material net edge.
3. Sports versus external bookie consensus is a candidate source, not an
   automatic edge: require exact market/side, auditable and fresh odds, and
   net advantage after fees and slippage.
4. Calendar/hazard-rate decomposition can expose P(event by T) errors. A
   named source is useful only when the resolving variable is measurable now.
   Reading headlines alone is not differentiated information.

Anti-edges include passive market making on thin binaries, sub-day crypto
price markets, near-certain macro legs without a measured dislocation, and
anything whose only thesis is a headline everyone can see.

## §4 Entry pipeline

Every entry uses `scripts/polyclaude_enter.py`; raw CLOB writes bypass the
controls. In order: (1) include existing exposure in the ticket; (2) reject
proposed/disputed UMA states; (3) anchor the catalyst analysis to literal
criteria and independently verify facts; (4) price interpretation risk rather
than banning it; (5) require positive EV at the pessimistic probability bound;
(6) beat the current Aave/riskless hurdle plus gas, bridge, spread, and fees.

### §4.4 Resolution-criteria and UMA risk

For subjective criteria use `P(YES)=0.7 strict + 0.3 loose` only when that
split is defensible. A permanence/finality qualifier near a deadline with
active progress is a UMA-loose trap: use loose weight at least 0.5 or skip.
The default instance/catalyst haircut is 0.10; 0.05 is reserved for measured
tail/monitoring fades. For measured p≥0.90 bond fades, `1−5(1−p)` may replace
the flat haircut only when the measurement is first-hand and the horizon is
short enough for its regime to bind. An unquantifiable haircut or unclear
high-stakes catalyst means small size or no trade.

Multi-leg mutually exclusive structures are one synthetic position: verify the
common event, exact equal shares, identities, payout rules, fees, depth,
rollback budget, and group caps before any leg. Never enter or exit a covered
set one leg at a time.

## §5 Sizing and exits

Use constrained half-Kelly by default, quarter-Kelly for fuzzy estimates, and
ρ-discount genuinely shared factors. Correlated catastrophe exposure deserves
extra caution; anti-correlation credit requires an explicit opposite-factor
case. Current entry-time guardrails are 15% of bankroll per ticket and 30% per
correlated cluster. They constrain new cost, not subsequent ratio drift; no
position-count cap exists. Respect the venue’s $5 minimum and maintain a small
same-chain operational float.

Use tick-rounded limit orders and live CLOB asks/bids, never midpoint or market
price. For exits compare: hold-to-resolution at the appropriate conditional
fair value, taker net after actual depth/fees, and a post-only maker sell at a
price above fair. A consumed edge can be sold when the bid clears hold value;
sub-hurdle or illiquid exits remain judgment calls. Brownian-bridge survival
math applies only to an immutable entry prior and the correct survival/side
semantics. Resolution is preferable when spread costs exceed the benefit of
early redeployment. On hidden-information markets, premium-to-fair resting
sells are allowed, but at-or-below-fair sells are not; public-information
maker orders require their own fair-value and execution checks.

## §6–8 Process, risk, and reporting

Use primary records: live books, activity feeds, Gamma resolution state, and
on-chain balances. Match reasoning depth to stakes: routine small decisions
use one bounded evaluation; large, new-class, or structural decisions use
parallel skeptic/champion review, then enforce hard gates manually. Record each
non-trivial action with thesis, prediction, size, resolution date, and outcome.

Risk is priced through status checks, source freshness, book depth, cluster
limits, and a three-layer emergency sanity check (independent sources,
market reaction, on-chain ground truth). Every write path needs a genuine
dry-run; simulations must suppress alerts as well as orders. Follow the
[emergency reference](../docs/reference/emergency.md) and distinguish
read-only rehearsal from an actual write-path test and its side effects.
Daemons need exact-one liveness and progress checks.

Journal each full or non-trivial run and maintain weekly P&L; quiet periodic
health checks may remain journal-free because health daemons own liveness.
Score calibration only as a debugging byproduct. Telegram is material-only;
flat ticks are journal-only. Scheduled and event-triggered runs are bounded:
finish the due check and concrete verification, then stop. Do not create an
indefinite goal or idle follow-up; cron and watchers provide waiting.
