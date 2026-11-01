# Strategy sweep — neglected opportunity classes (operator-requested 2026-11-01)

Framing: the resting-sell policy existed in doctrine since April but had no
machinery until today. Generalized: **any policy that is still executed
manually at ticks is a candidate automation/edge gap.** Screened 14 classes
against (a) existing tooling, (b) doctrine skip-list and failure lessons,
(c) honest EV mechanics at a $190 bankroll. Verdicts: BUILD (1), QUEUE (3),
COVERED (6), SKIP (4). No high-value class is entirely absent; the largest
gaps are latency/automation around edges we already hold.

## BUILD — source_watch (primary-source polling per held/watched market)

Every current thesis resolves on a named primary source we check by hand at
ticks: agi.safe.ai (Kimi HLE), official Venezuelan channels (Delcy), Google
Year-in-Search (Messi), Senate records (Clarity). The 2026-08-01 HLE
resolution-source-lag lesson proved the repricing lag is minutes-to-hours
after a source updates. A daemon that polls each named source on a bounded
cadence (5–15 min), diffs content, and fires a tiered alert (source changed →
wake a check-in; source confirms thesis → trade before repricing) converts our
manual daily glance into the same edge at machine latency. Cheap (httpx +
hash-diff), low risk (read-only), direct fit with doctrine (anchor on literal
resolution criteria). This is the highest-EV item in the sweep. Spec: config
per market = {source url(s), diff selectors, alert tier, cooldown}; reuse
news_alerts.jsonl + telegram; skeptical first-class alerts require the agent.

## QUEUE

- **Buy-side resting rests** (resting_watch follow-up): discounted maker bids
  below the pessimistic bound on whitelisted watched markets, via the gated
  `polyclaude_enter.py --maker` path. Each whitelist entry needs its own
  underwriting (pessimistic bound, catalyst, alert keys) — the machinery from
  today is 80% reusable.
- **Hazard-mismatch scanner**: date-series siblings of one event (Fed at
  multiple meetings, event-by-month series) systematically flagged where the
  implied P(by T) chain is inconsistent with a hazard-rate decomposition.
  Doctrine item #4 exists; only the per-position `brownian_bridge_fv.py`
  math is manual. A scanner emitting ranked candidates would make calendar
  mispricing a discovery output instead of an analyst recall task.
- **Funding-harvest hedge spec** (crypto sleeve): Oct-29 review measured
  extreme single-name perp funding (unhedgeable) and ~5% on metals
  (directional). A delta-neutral harvest needs a vetted stock/index hedge
  writer, which does not exist. Research task: spec the cheapest lawful
  hedge route; until then the funding is directional carry and stays out.

## COVERED (existing scans/watchers already serve these)

- Structural arbs: `event_monotonicity_scan.py`, `polymarket_consistency_scan.py`,
  `limitless_arb_scan.py`, run daily, armed via opportunity_watch.
- Sports vs bookie consensus: `sports_pm_scan.py --with-consensus`; no edge
  found historically, kept on the tick list.
- New listings: opportunity_watch's catalyst-family listing watch.
- Redemption/redeployment: `redeem-all` on ticks; redeployment is gated anyway.
- Cross-source synthesis / macro visibility: macro_pm_scan, catalyst_check.
- Premium resting sells: resting_watch (new today).

## SKIP (documented reasoning, do not re-litigate without new evidence)

- **Continuous two-sided market making** in thin binaries: adverse selection
  concentrates in a single thesis where diversified MMs average it out; the
  niche is empty because the strategy is negative-EV at any scale, not because
  small scale fixes it. Codified 2026-11-01 in strategy/03.
- **UMA dispute-window trading**: gate 2 bans entering proposed/disputed
  markets; adjudication outcomes are a different game than thesis underwriting.
- **Oracle-posting latency front-running**: same family as source-lag but
  execution-side; subsumed by source_watch at our scale, and behaviorally
  adjacent to gaming the venue — no.
- **Airdrop/activity farming, fee-tier gaming**: off-mandate or sub-$1/yr.

## Meta-lesson

The April→November resting-sell gap had three causes: (1) policy lived in
prose, no daemon skeleton was ever created; (2) cron-tick execution made
"someone will do it at the next tick" a stable failure mode; (3) the
October-19 quote-lifetime rules raised the per-order justification bar high
enough that ad-hoc placement felt risky, so nothing rested even when
doctrine-sanctioned. The standing fix: every manual policy gets a named
owner (script or explicit "operator does this at tick N"), reviewed when a
tick notices it drifting. Applied today to resting sells; next in line per
the BUILD/QUEUE list above.
