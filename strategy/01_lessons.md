# Lessons ledger — compact, searchable edition

> Read this after `strategy/00_philosophy.md` for the failure patterns that
> explain the current rules. The complete pre-consolidation ledger is retained
> at `docs/archive/strategy-01-lessons-legacy.md`; use it for dates, examples,
> and provenance, not as current authority. Operational mechanics belong in
> `strategy/02_operations.md`.

### Historical detail map

Use the archive only when the compact rule needs its original incident or
measurement:

- [Execution, fees, and books](../docs/archive/strategy-01-lessons-legacy.md#execution-mechanics-the-fee-decides-almost-everything)
- [Priors and calibration](../docs/archive/strategy-01-lessons-legacy.md#priors--calibration)
- [Surviving edges](../docs/archive/strategy-01-lessons-legacy.md#edges-that-survived-and-their-fine-print)
- [Sizing and risk](../docs/archive/strategy-01-lessons-legacy.md#sizing--risk)
- [Daemon/resource failures](../docs/archive/strategy-01-lessons-legacy.md#daemons-resources--liveness)
- [Write paths and drills](../docs/archive/strategy-01-lessons-legacy.md#write-paths-drills--outward-side-effects)
- [Parsing and verification](../docs/archive/strategy-01-lessons-legacy.md#parsing-venue-data--verifying-my-own-output)
- [Loop/coverage failures](../docs/archive/strategy-01-lessons-legacy.md#parsing-venue-data--verifying-my-own-output)
- [Operator covenant and bounded cadence](../docs/archive/strategy-01-lessons-legacy.md#process--operator-covenant)
- [Instrument/guard failures](../docs/archive/strategy-01-lessons-legacy.md#verifying-my-own-instruments--guards--the-2026-08-2528-cluster)
- [Prior/fact hygiene](../docs/archive/strategy-01-lessons-legacy.md#prior--fact-hygiene--the-2026-08-1012-cluster)
- [Display honesty](../docs/archive/strategy-01-lessons-legacy.md#self-flattering-numbers--display-honesty--the-2026-08-1320-cluster)
- [Stale constants and tests](../docs/archive/strategy-01-lessons-legacy.md#stale-constants--the-birth-of-the-test-suite--the-2026-08-1422-cluster)
- [Regime judgment](../docs/archive/strategy-01-lessons-legacy.md#verified-mechanics--regime-judgment--2026-08-1620)

## Execution, fees, and books

- **Fee semantics:** use the market’s structured `feeSchedule` through
  `pm_fees.py`: rate × `[p × (1-p)]^exponent` per share. Charge fees at each
  actual fill level; `fee(avg_fill) × requested_size` is wrong, especially with
  nonlinear curves and unfilled remainder. Limitless BUY fees reduce received
  contracts, so match net shares; its raw sizes are micro-contracts, NO asks
  mirror YES bids, and missing parent prices are not 50c. Its public inspector
  remains screening-only with a conditional 3% fee bound.
- **Three exit choices:** resolution (no fee/spread), taker depth walk, and a
  post-only maker sell above fair. Midpoints and best bids are not liquidation
  values. Preserve public requested-size averages, but report actual walked
  depth and unfilled portions honestly. A sequential depth estimate is
  indicative, not synchronized or freshness-verified.
- **Maker/hidden information:** premium-to-fair resting sells are permitted;
  at-or-below-fair sells on hidden-information markets are not. Resting bids
  fill under future information and require current crux coverage plus
  re-verification after unexplained moves. Pull all resting orders before a
  scheduled binary catalyst. Verify cancels against the subsequent book.
- Use integer shares and tick-rounded prices: round up for taker buys and down
  for maker bids. Never market-buy. Never enter or exit a mutually exclusive
  equal-share set one leg at a time; put pairing and group behavior in tools,
  not only in a note.

## Priors, criteria, and evidence

- A prior needs a dated, accessible source and an explicit clock. Re-reading
  criteria is not re-verifying facts; source-diffing proves fidelity, not
  recency. Search for newer reporting when a fast story has an old source or a
  sustained unexplained adverse move. Unfetchable URLs and aggregate summaries
  are leads, not verification.
- Write `key_facts` as atomic claims with source and `source_date`; do not hide
  independent assertions in a bundled narrative or put measured numbers only
  in free-text notes. A point value in a slow document becomes false when the
  quantity moves faster than the review cadence; preserve stable mechanisms or
  ranges and remeasure.
- For a conditional market, identify the precondition and use its sibling price
  rather than inventing that term. A named resolution source matters only when
  its resolving variable is measurable now; terminal-only sources offer no
  current information edge. Exact proposition identity beats event membership.
  On rolling windows, separately record eligible start, reset/start cutoff,
  and completion. Threshold ladders are monotone; exact-value buckets are not.
- Distinguish fact bets from interpretation/UMA bets. The latter are lottery
  tickets, not confident mechanical edges. Re-read the literal criteria when
  the world moves, a position moves materially, or a prior changes. Benchmark
  scores are configuration- and source-scoped; never promote a no-tools or
  narrow leaderboard result to “any surface.”
- A market move must first be shown to be real (volume/spread/depth). If the
  resolving state is hidden and cannot be checked, presume informed flow and
  do not fade. If the bar is mechanically checkable and freshly unchanged, a
  move may be rumor flow. Check implication siblings before attributing it.

## Calibration and economics

- Score decisions by return per dollar committed, not skip hit rate: favourite
  fades have small wins and full-loss tails. N=1 outcomes and repeated updates
  are not calibration. Group shared catalysts (the five SDCC contracts were
  one event); do not claim independence from a larger row count.
- A measured prior drift can justify a class-specific entry haircut, but small
  samples do not justify a universal hold haircut or uniform correction. A
  calibration change must be applied to current strongest beliefs as a test,
  not only future trades. A new prior requires a re-size check.
- A model’s correct arithmetic can still be misapplied: validate semantic
  side, survival versus occurrence, immutable entry prior, timing, and regime
  before trusting output. A detector needs both correctness and an economic
  materiality floor; test both positive and known-negative cases.

## State, parsing, and operations

- Treat empty output as a failure until the response shape and count are
  checked against an independently known truth. Validate every new detector’s
  structural claim, not only its prices. For “nothing changed” conclusions,
  prove parser coverage with known additions and known inventory; liveness is
  not coverage. Inspect success and failure markers together.
- Data-API activity is the fill/redemption authority; wallet arithmetic with
  resting orders is not. Positions can de-index mid-resolution, so retain exact
  condition/token snapshots and use the resolution-state path. State audit
  reconciles claims, triggers, priors, and acknowledged holds; a note-only
  trigger is not armed.
- Before writing after a rewind, inspect `git status` and per-file direction;
  never blanket-restore. Daemons require exact-one process checks, absolute
  script paths, progress/state-mtime checks, and the
  `scripts/daemon_keepalive.sh` / `strategy/02_operations.md` restart
  procedures. A live PID does not prove progress. Serialize model-spawning
  work and keep at least 500MB available before spawning; inspect existing
  workers.
- Every write path needs a real dry-run. Follow
  the [emergency reference](../docs/reference/emergency.md), and ensure
  dry-run suppresses Telegram/webhook alarms as well as orders. Emergency
  exits need a 3-layer sanity check. For an emergency exit
  of an ungrouped position, partial fills can be preferable to FOK refusal;
  protected groups retain their atomicity guard. Never redeem from a
  simulation-success shortcut without final winning-side and nonzero-balance
  checks.
- Fallback paths must be exercised with the real working directory, fresh
  session, and no inherited assumptions. Queue acknowledgement means persisted,
  not executed. Scheduled check-ins are bounded: finish due work and stop;
  cron/event watchers provide waiting, and no indefinite goal or idle follow-up
  is created.

## Reporting covenant

Lead with whole-account net liquidation versus contributed capital, then marked
bankroll, realized P&L, and what is fragile. Gas and operating costs stay
separate. Enumerate every display layer when changing a metric; a corrected
producer can still feed a stale status/Telegram formatter. Journal each full or
non-trivial run, but quiet periodic health checks may remain journal-free; keep
the weekly P&L current and make Telegram **material-only**. Flat ticks
are journal-only; health daemons own liveness. Preserve the distinction between
an unexitable claim and a worthless claim, and between a signal and a decision.
