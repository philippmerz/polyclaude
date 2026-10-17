# Worlds 2026: primary assumptions and source correction

This is a dated, uncalibrated primary scenario model, not a bookmaker consensus
or an official Riot championship forecast. No market prices enter it. The
source-only assistants collected facts; the primary read the complete rules,
original pages, formula image, current match objects and tournament regulations.

## Correct event and current state

The initial standings URL with tournament ID `113475452383887518` was **Worlds
2025**. Its embedded match timestamps prove that identity. The earlier claim of
future Swiss results conflicting with the 2026 schedule was an investigation
error. The old packet is retained; the explicit correction is
`data/deep_review_20261017/lol_2026_playin_correction_addendum.json`.

The actual 2026 tournament is `115660540725177488`. The dated
[official schedule](https://lolesports.com/en-US/leagues/wqs) records five
completed play-in series, leaving KC versus MVK on October 18. C9 and FUR have
been eliminated; their modeled title probability is zero conditional on those
results standing. The model includes LOS directly and only KC/MVK as possible
play-in advancers. The 2026 Swiss stage has not started.

[Riot's rules](https://cdn.sanity.io/files/dsfx7636/news_live/faa5ce974e58615911fbee931c6123e2785a8b46.pdf)
and the [October primer](https://lolesports.com/en-GB/news/worlds-2026-primer)
establish the Swiss seed pools and best-of format. Initial cross-pool opponents
cannot share a region. Later matches pair equal records without rematches,
except an official waiver if no legal draw exists. Advancement/elimination
matches use BO3, other Swiss matches BO1. Eight advance; two undefeated teams
draw 3–2 opponents in opposite knockout halves. All knockout series are BO5.
The simulation preserves those restrictions; it does not multiply independent
title probabilities or independently add the four Korean teams.

## Strength input and uncertainty

[Current Riot GPR](https://lolesports.com/en-US/gpr/2026/current), calculated
October 17 at 05:00 UTC, supplies every remaining team's score. HLE leads at
1540, GEN is 1519, BLG 1513 and G2 1478. The complete input table is in the
model and the saved factual packet. GPR already incorporates performance,
opponents and regional strength; individual final scores are not added again
as independent likelihoods. In particular, both MSI HLE–BLG series matter,
not only HLE's championship win. The current international schedule also shows
GEN losing to G2 in March and LYON taking HLE to five games in July. These
observations undermine treating a Korean champion as an automatic outcome.

The original [2024 developer explanation](https://lolesports.com/en-US/news/dev-diary-unveiling-the-global-power-rankings)
blends team and regional Elo 80/20. Its actual expected-result image uses a
**600**, not the usual assumed 400, denominator. The current 2026 implementation
and the exact game-versus-series unit are not proved by that old explanation.
Its claimed directional accuracy is not a calibration certificate for these
probabilities. Preserve that uncertainty rather than silently turn the GPR
score into an official per-game probability.

Three primary specifications therefore receive subjective weights: 50% direct
series mapping with denominator 600, 35% per-game mapping at 600 followed by
binomial BO3/BO5 conversion, and 15% sharper per-game mapping at 400. The direct
series branch reduces deviation from 50% for shorter formats. Each simulation
draw adds one persistent regional normal shock with score SD 50 and one
persistent team shock with SD 65. These describe patch/roster/form uncertainty;
they are chosen assumptions, not fitted standard deviations. There is no
measured side-selection, draft, injury or patch-specific player model. The
Swiss draw implementation approximates Riot's procedural draw by a uniform
valid matching, a remaining specification difference.

The reproducible seed and 12,000 draws per branch quantify this model's
arithmetic. They do not narrow uncertainty in its assumptions. Every draw
checks distinct entrants, equal-record matches, eight qualifiers, correct
undefeated counts and one champion. The resulting title mass sums to one;
regional probabilities are sums within the same tournament draws.

The current mixture gives GEN 14.544% and LCK 46.016% before resolution risk.
The primary uses rounded **GEN 14%** after a 1% conditional failure-to-declare
or exceptional-adjudication allowance through November 28, and **LCK 46%**
after a 0.5% allowance through December 31. These small allowances and the
rounding are judgmental, not estimated event frequencies. Broader sensitivity
ranges are 5–40% for GEN and 25–80% for LCK. They admit structural error beyond
the three central specifications and are not confidence intervals.

Use at least a **15 percentage point** ordinary entry reserve for these new,
unvalidated sports-model claims, rather than a measured-tail exemption. A
reserve does not prove calibration or make all adverse scenarios profitable.
New Swiss draws, patch/roster information and played series require a fresh
forecast before an order. Existing cash/Aave remains the comparison after fees,
carry, monitoring and source/adjudication risk. No order or canonical prior is
created by this module or its research reports.

## Different contracts

Case 54 has a November 28 ET no-champion fallback, alphabetical winner tie
rule, and Riot information with credible-reporting fallback. Case 150 runs
through December 31 ET and names Fandom, with no explicit automatic fallback
when that site is unavailable. Its direct source returned 403. League region
is the team's region, not the players' citizenship. These are related payoff
claims, not an exact fungible pair or identical deadline. A GEN title ordinarily
implies an LCK title, but the distinct source/deadline clauses prevent assuming
an unconditional cross-market arbitrage. GEN NO and LCK NO share the same
championship factor; they are not independent diversifiers.
