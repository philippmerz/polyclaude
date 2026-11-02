# Thin-market mispricing: measurement-first exploitation plan

Operator request (2026-11-02, via Grok Bot): design a measured way to
systematically find and exploit low-liquidity mispricings, sizing for thin
books, with an honest monthly-return estimate. Rule (b) applies to this plan
itself: every number below is either measured (cited) or labeled an
unmeasured hypothesis with its measurement design. No unmeasured numbers
presented as expectations.

## 1. Measured baseline (what the evidence actually says)

- Realized P&L since kickoff: +$15.82 on $170 over 191 days = **+9.3%
  ≈ 1.45%/month average** (`scripts/bankroll.py`, journal 2026-04-25→11-02).
- The last 30 days were **negative**: settled +$20.36 (2026-10-27 backlog) →
  +$15.83 (11-02), i.e. ≈ −2.3%/month, driven by the October Fed resolution
  (−$4.80). The 9.3% total was earned May–Sep; recent run-rate is ~zero.
- The one systematic signal ever measured in this universe (Grok's hazard
  backtest, `research/2026-11-02-sweep-verification/`): trading toward a
  constant-hazard fit at 5pt gaps made +4.67/share on 86 trades at mid with
  no fees, event-bootstrap P(≤0) ≈ 0.15; **negative at 15pt gaps**; the
  market prices the ladders better than the fit (Brier 0.2132 vs 0.2276).
  Corrected twice: first pass said $401 (arithmetic error, multiplying
  the total by the trade count); Grok's second review caught that +4.67 is
  the TOTAL per-share P&L summed over all 86 trades (a share cannot earn
  more than $1 per trade), i.e. ~$4.67 gross across the whole backtest
  window (~10 months of ladder resolutions). At any size that is cents per
  month - dead before costs. C6 is the only pre-registered SYSTEMATIC TEST
  COMPLETED, and its result is thin with doubtful robustness - hence no
  capital. Calling it 'the only measured systematic signal' overstated a
  failed test; corrected here and in the registry.
- Conclusion: uninformed flow exists in thin books, but a general
  fade-the-gamblers rule has been tried and retired here (favorite-fade
  calibration failure, 2026-10-12 review; Grok's hazard result confirms the
  market beats naive structural models). Per-strategy realized P&L
  (2026-11-02 breakdown of notes/decisions.json, 29 of 105 trade records
  parsed with explicit dollar outcomes; canceled-unfilled excluded):
  underwritten instance entries +$15.77 net (carrying the -$4.80 October
  Fed loss), tail/carry fades -$10.89, HLE class small/negative (one leg
  -66% at 2026-08-04 mark, journal :4579; leg exits not dollar-parsed),
  politics/structural records still open or unfilled. So 'underwritten
  instances worked' is measured for REALIZED P&L; it is not yet measured
  for the open book (Clarity pair, Delcy, Kimi all unresolved). The plan
  measures per-slice and gates capital per claim.

## 2. Plan: claims registry → data → gates → size

**Phase 0 — claims registry (no capital; this week).**
`notes/strategy_claims.jsonl`: every live or candidate slice gets a
testable claim, metric, data path, pre-registered capital gate, review date.
Seeded:

| id | claim | data | capital gate |
|---|---|---|---|
| C1 source-lag | a resolving-source change precedes a ≥5pp midpoint move within 30 min, ≥3 events | logs/source_watch_history.jsonl (collecting since 11-02) | 3 events → wake-and-trade runbook, ≤25% of book depth per order |
| C2 instance entries | gated instance entries resolve at/above the pessimistic bound ≥55% | decisions.json outcomes (Dec-31 book scoring is the full test) | 20 scored entries above 55% |
| C3 buy-side rests | fills below the pessimistic bound are +EV by construction; ≤2 fills/month | resting_watch state + mark-at-fill log (datum 1: Kimi 42@0.13, mark 0.135–0.14) | 5 fills, none below bound |
| C4 premium sells | ≤1 fill/quarter, each ≥ post-jump fair | resting_watch log (post_jump_fair enforced since 11-02) | n/a (free option; no gate needed) |
| C5 panic-cycle | UNREGISTERED — needs a written claim before any capital | — | standing rule (operator directive b) |
| C6 hazard-gap | tested 11-02 | Grok's backtest | FAILED → SKIP, recorded |

**Phase 1 — data (2–4 weeks, runs itself).** source_watch history;
mark-at-fill logging added to resting_watch fill detection; paper-tracked
thin-tail criteria reads (candidates from the existing thin-tail pass,
scored at resolution with zero capital — the cheapest evidence purchasable).

**Phase 2 — deployment gates (pre-registered).** A slice gets capital only
after clearing its gate; then: quarter-Kelly; per-ticket ≤15% of bankroll;
**thin-book sizing cap: order ≤25% of displayed depth at the limit**; exit
priced at best-bid-minus-5pp (pessimistic exit); hold-to-resolution only
with literal clean criteria; every fill logged with mark-at-fill and
mark-at-resolution into decisions.json for the slice's running score.

**Phase 3 — review.** Monthly in the weekly P&L: claim vs data per slice;
slices that miss their metric lose capital (config flip, not debate).

## 3. Honest return estimate

- With the system running and one slice clearing its gate: **2–4%/month
  expectation, high variance** (P&L arrives in resolution lumps; 1–3
  events/month carry it). Floor ≈ Aave carry on idle (~0.3%/month) when no
  slice qualifies.
- **Double-digit %/month is not an estimate I can defend.** It requires
  ≈$19/month sustained; the measured density of exploitable edge at our
  capacity (C6's +4.67/share×86, C1's yet-unmeasured lag, C3's ≤2
  fills/month) sums to single-digit dollars, not nineteen. If a measured
  slice ever shows double digits, the gates scale into it automatically —
  that is the system's job, not the forecast's.
- The binding constraint is bankroll, not ideas: at $190, even a real
  10%/month edge pays $19. The plan's return comes from compounding
  measured evidence while not donating to thin-book adverse selection.

## 4. What I will NOT do (pre-registered rejections)

- No blanket behavioral-fade strategies (retired class; needs fresh
  pre-registered claim + data, per C5 rule).
- No size into books where the pessimistic exit loses money.
- No strategy without a registry row gets a dollar (operator directive b,
  codified in the registry file itself).
