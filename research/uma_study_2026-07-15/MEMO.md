# UMA dispute-window mispricing study — 2026-07-15

**VERDICT: FALSE — killed.** Dispute-window prices are conditionally well-calibrated; every
ex-ante-executable entry variant is ≤0 after costs. No entry rule ships. The defensive layer
stays (and gained the study's priors).

Background research agent, ~55min. Ground truth: on-chain Polygon `DisputePrice` events from
BOTH oracles Polymarket uses (OOv2 `0xee3a…` + managed fork `0x2c03…`), 2025-06-01 → 2026-07-15,
joined to gamma outcomes + CLOB prices-history. **N=2,246 resolved determinate disputed markets**
(target was ≥20). Small artifacts here; bulk (860MB closed-markets crawl) was ephemeral in
/tmp/uma_study/.

## Population facts (keep — these are the reusable priors)

- **Proposal-stood base rate 72.7%** [70.9–74.5]. NO-side proposals 77.9% vs YES-side 67.6%;
  "50/50" proposals stand only 31%; vol>$1M 80.8%. By dispute count: 1× 71.8%, 2× 79.6%,
  3× 40%, ≥4× 0%.
- **Time-to-finality is bimodal, not "48-72h"**: median 4.2h (1st dispute usually = adapter
  reset → re-proposal → 2h liveness); DVM path (2+ disputes) median ~91h; >4wk tail =
  premature-proposal cases (only 56% stand). The R-U May-2026 experience was a 24h reset-path
  case, not a DVM vote.
- ~167 disputed markets/month (~50-90 with vol≥$100k); live list is ONE gamma call:
  `/markets?uma_resolution_status=disputed&closed=false` (17 today).

## The kill

Buying the proposed side 15-60min post-dispute (N=622, vol≥$100k): **aggregate EV −5.3%**;
median entry 0.970 (no panic-to-0.5 exists). Best bucket (0.85-0.95) = +1.3% raw, **+0.06%
after 1c spread/fees** (t=0.36). ≥0.95 bucket: 98% stand but you pay ~0.999 and eat rare
−100%s → −1.0%.

- **Crash-reversion (the R-U pattern) is INVERTED**: price crashes ≥10pp on dispute → proposal
  stands only **22%**; buying the crash = **−31%**. Crashes are information, not panic.
- **Pure DVM-window variant** (enter at 2nd dispute): −7.1%; if the 2nd proposal flips from
  the 1st it stands 47% (buying = −33%).
- The one positive cell (+39%, N=27) is a June-2026 Iran-war correlated cluster — vanishes
  under the DVM entry definition. Multiple-comparisons artifact.
- Ex-post bound: buying the eventual winner during windows = +93% avg — the variance exists,
  the ex-ante predictability doesn't. Disputes select for genuine ambiguity and the crowd
  prices the specifics better than any base rate (the big flips are political — Zelenskyy-suit
  $242M, US-Iran-ceasefire-ext $204M — exactly this agent's habitat, and it still loses).

## Disposition (all shipped 2026-07-15)

- No entry rule. `uma_status_check.py` now attaches `dispute_priors` to disputed-status alerts
  (stand rates + the crash-is-information warning) — for HELD-position risk sizing in the
  moment it matters, never as an alpha signal.
- What would reopen: demonstrated discretionary rules-lawyering edge on specific resolution
  criteria faster than the crowd (case-by-case, catalyst-gated) — not this systematic pattern.
