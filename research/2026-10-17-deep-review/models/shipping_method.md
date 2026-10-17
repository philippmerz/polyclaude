# Primary shipping valuation — October 17, 2026

The primary read all five complete contracts (5, 19, 40, 61 and 215). These are
claims on the named IMF series, not on a minister's use of “open,” shipping
capacity, a vessel count from another provider, or the signature of a ceasefire.
The source packet and mechanical source arithmetic are
`data/deep_review_20261017/portwatch_fullwindow_sources.json`; the original
agreement statements and historical contracts are in `hormuz_sources.json`.
`shipping_scenarios.py` reproduces the arithmetic behind the judgments below.

## Observations and qualification

The official IMF-owned ArcGIS daily layer contains 165 consecutive dates for
each chokepoint, April 30–October 11. Its October 14 data-edit timestamp is not
an October 14 traffic observation. Each count is the sum of container, dry bulk,
general cargo, roll-on/roll-off and tanker ships. `n_cargo` already aggregates
four categories; adding it to those categories would double count them.

For Bab's December closure contract, 95 complete trailing means on or after its
July 9 creation range from 23.714 to 42.286. The latest is 198/7=28.286. The
claim requires a mean at or below 10, equivalent to at most 70 ships across a
complete seven-day window under this averaging convention. A normal weak week
is insufficient. For Hormuz, the August 10 creation windows of cases 19/40 have
63 means, maximum 6.000 and latest 29/7=4.143. The May 6 creation window of case
61 has 159 means, maximum 31.857 on June 29. None of these reconstructed current
windows crosses its own contract threshold. That is not proof that no earlier
published chart qualified before a later upward/downward revision. The contracts
preserve a previously published qualifier under their respective revision rules.
Current daily rows are not an archive of every publication state. Chart rendering
and historical revision coverage remain genuine source limitations.

[The June 17 MOU text](https://en.irna.ir/news/86186085/Islamabad-Memorandum-of-Understanding-between-Iran-and-US)
promised best efforts toward safe navigation, initially over 60 days, with a
gradual implementation period. [CENTCOM's July 13 notice](https://www.centcom.mil/MEDIA/PUBLIC-RELEASES/Article/4542098/us-forces-to-resume-naval-blockade-against-iran/)
resumed the port blockade on July 14. The measured seven-day mean peaked at
31.857 during the June reopening interval, below the contract's 60. The
[October 17 Iranian offer](https://www.presstv.co.uk/Detail/2026/10/17/778543/Iran-Abbas-Araghci-Tehran-conveyed-seven-day-plan-reopen-Strait-of-Hormuz-choice-rests-with-US)
is attributed to the foreign minister through state media; it is a conditional
seven-day proposal, not verified US acceptance or measured restored traffic.
It supports an active negotiation branch, with substantial implementation risk.

## Independent forecast construction

All weights here are explicit primary judgments, not small-model scores, market
prices, calibrated hazard estimates, or empirical probability floors. Current
prices are considered only after constructing the forecasts.

* Bab closure by December 31: assume a 15% chance of a materially more restrictive
  disruption regime in the remaining roughly 75 days. Give that regime a 50%
  chance of producing the specified sustained collapse; give the continuing
  regime 0.5%. This yields 7.925%, rounded to **8%**, scenario range **1–30%**.
  The wide range reflects unobserved attacks, transit decisions and source
  revisions. Ninety-five overlapping non-events are not 95 independent trials.
* Hormuz by October 31: a 10% new bilateral-deal branch, with 30% quick enough
  implementation to produce a complete 60-ship mean, plus a 1% no-deal
  normalization branch. This gives 3.9%, rounded to **4%**, range **0.5–20%**.
  A deal on the final day cannot instantly supply a prior seven-day average.
* Hormuz by November 30: a 30% deal branch, split equally between material and
  nominal/obstructed implementation. Conditional threshold probabilities are
  80% and 5%; the no-deal branch is 2.5%. Result 14.5%, rounded to **15%**, range
  **3–45%**. The June experience is why the nominal branch carries so little.
* Hormuz by December 31: a 45% deal branch, split equally between material and
  nominal implementation, with 90% and 15% threshold probabilities; the no-deal
  branch is 5%. Result 26.375%, rounded to **26%**, range **8–65%**. More time
  helps, but it does not make a signed agreement sufficient for normalization.
* Bab October 19–25 total below 170: all 23 complete same-weekday weeks in the
  captured history exceed this threshold; their minimum is 173. The last eight
  totals are 206,184,178,191,173,190,207,198 (mean 190.875, sample SD 12.380).
  A continuity-corrected normal sensitivity gives about 4.2% below 170. It is
  not a fitted event model: the sample is small, serial dependence matters, and
  a new regime need not be normal. Mix that with an eight-day disruption hazard
  obtained by spreading the judgmental 15%/75-day hazard, an 80% threshold chance
  in that branch, and a separate 3% adverse regime/source branch. Result about
  8.35%, rounded to **8%**, range **1–30%**. Zero of 23 is not a zero tail.

The Hormuz curves are monotone across deadlines, and all share negotiation,
military and publication shocks. Bab and Hormuz exposures also share regional
war risk. Buying both NO sides is not independent diversification. Treat these
as one correlated Middle East shipping family when evaluating caps and sizing.

## Economics, time and entry discipline

Each case preserves both complete ten-share ask walks, exact token identities,
fee curve, age, minimum size, depth and immediate exit estimate. The original
18:35/18:38 books are dated research observations. Maker ceiling `p-0.10` is a
default sensitivity before carry, gas and operational margin, not a proof that
every point in the scenario range clears entry. For a price c, zero-fee maker
entry needs a defensible p above c plus the chosen estimation reserve and costs.
Taker break-even adds the full per-level curve; a top ask alone is insufficient.

The official daily series is six days behind the research date. Refresh it before
any action, and establish source coverage plus a way to pull a resting order at
a material change. An announcement can improve negotiations while leaving the
measured traffic below threshold. These are ordinary instance forecasts; no K=5
tail treatment or smaller reserve is justified by these unmeasured branch weights.
Existing December-book hold-only policy remains in force, pending a separately
reasoned policy decision. Research probability differences do not silently amend it.

Normal settlement fits January. The 14-calendar-day data fallback and clerical
correction window can delay redemption, especially for December 31. Dated Aave
3.0553% is a variable-rate alternative with funding costs, not guaranteed free
deployment. The candidate with the clearest short-horizon watch is case 215 NO
at a sufficiently low maker price; its range, stale daily data, small expected
dollar gain and source coverage must still be assessed before committing funds.
