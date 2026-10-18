# OpenRouter calendar-week model — October 18 revision

The recovered Top Models chart supports an initial **60% YES for case35** and
**11% YES for case112**, replacing case35's historical-data block and case112's
9% estimate. These are primary judgments with sensitivities15–85% and0.5–80%,
respectively, and a15-point entry reserve. They are not calibrated posteriors,
probability floors, independent bets or trade approval. [Exact calculations](openrouter_calendar_weeks_1115.json).

## Source binding and what changed

The actual [Top Models chart](https://openrouter.ai/rankings#top-models) calls the
[no-argument chart endpoint](https://openrouter.ai/api/frontend/v1/rankings/model-rankings-chart).
It returns53 Monday-labelled points, each containing nine named model series plus
Others. The separate models leaderboard's rolling-week endpoint is not the chart.
Earlier failed date selectors and a401 on another dataset did not establish that
this public history was unavailable. Primary independently checked the response
hash, all raw series sums and date sequence. The oldest range-edge point and the
unfinished October12 week are excluded from completed-week growth statistics.

Raw totals for September28/October5/October12 are165.856050/171.842502/152.318277T.
The browser directly showed October5 **Total172T**, different from171.91T obtained
by summing its individually rounded model labels. October12 showed **Total152T**
and a separate hatched **Weekly Pace165T (+12.6T)**. Use each week's displayed
Total for settlement; do not substitute rounded model-label sums or the forecast.
Current historical values are not archived first-display snapshots.

The current-week forecast adds12.550647T to the raw total, producing164.868924T.
Its published formula uses UTC weekday weights and the hour of the server's
`cachedAt` reference; that timestamp is not a documented observation cutoff.
The separate leaderboard's October17 usage date cannot be assigned to the chart.
The forecast is a presentation aid, not an observed final total or binding payout.
[Browser, screenshots and code evidence](../../../data/deep_review_20261017/openrouter_chart_live_display_1113.json).

## Shared scenario model

Current-week completion has three explicit scenarios:45% uses a full Sunday of
volume anchored by the supported day leaderboard's18.338T aggregate,45% uses the
observed UI pace addition12.551T as a noisy remainder proxy, and10% uses a0–36T
remainder. The first two have log-sigmas.25/.35. These weights and the mapping from
leaderboard volume to chart completion are assumptions, not recovered backend facts.
The resulting current-week mean is168.65T, median168.06T, with a simulated5–95%
interval159.72–180.14T. None is an observed completed week.

Weekly growth shares one regime over the five future weeks:

| Regime | Weight | Mean weekly log growth | Innovation SD |
|---|---:|---:|---:|
| Moderation |45%|.035|.065|
| Continued growth |35%|.080|.095|
| Release boom |10%|.200|.100|
| Disruption |10%|−.150|.150|

The weekly innovations have.25 correlation through a shared normal factor; each
future week compounds from the preceding level. The recent four completed log
returns, September7–October5, have mean.0761/SD.0583; twelve, July13–October5,
have mean.0839/SD.0919. These are descriptive, nonstationary samples. Choosing the
regimes, weights, future correlation and current completion distribution remains
primary judgment, not a fitted or holdout-tested model. The repeated source uses
one joint path; it does not multiply four independent probabilities.

Case35 adds the September28/October5 raw totals, modelled October12 completion and
October19 future week. Case112 sums modelled October26/November2/November9/November16.
An additive95%Normal(0,2T)/5%Normal(0,10T) sensitivity represents rounded weekly
totals and unmeasured revisions. It is not an identified rounding-error distribution
or assurance that revisions cannot be larger. Using separately rounded weekly Total
values is the literal rule; raw sums are a scale proxy inside that sensitivity.

With200,000 reproducible paths, case35's band probability is59.54%, rounded60%,
and case112's10.7795%, rounded11%. Case35 median total683.64T and simulated5–95%
range645.37–727.74T explain sensitivity to completion and the lower675T boundary.
Case112 median807.90T and range405.49–1453.40T explain the NO thesis: continued
rapid growth can overshoot775T, while weak demand can fall below725T. Model error
is far larger than Monte Carlo arithmetic error.

## Countermodels and entry judgment

Case35 becomes68.83% if the entire latest complete-day volume remains, or51.89%
if the UI pace proxy alone supplies the remainder. It is not a precise near-certain
YES. Case112 remains10.75–11.17% under those completion alternatives; moderation-
only gives16.99%, continued-growth-only8.60%, boom0.42%, disruption1.46%.

A four-week total centred at750T with log-sigma.03 instead yields73.36% YES.
That concentrated alternative reverses the NO trade. Historical weekly dispersion
and uncertain future growth provide evidence for broader totals, but do not prove
a minimum future variance. The15-point entry reserve is roughly equivalent to
putting24% weight on that countermodel alongside an11% YES base. This is a useful
stress interpretation, not an empirical probability bound; the full sensitivity
range still includes large NO losses. Primary read both balanced chart advisories,
including their initial factual corrections about the separate leaderboard cutoff.

Case112 may justify a **tiny five-share NO maker investigation**, maximum68c and
preferably near64c, if independent current gates and management still support it.
At64c, risk3.20, central EV1.25 and selected74% NO EV0.50 precede carry/operations;
at68c they are3.40,1.05,0.30. Full principal can be lost. No position, prior,
reservation or order is created by this model. Case35's dated offers leave no
useful selected margin after carry; illustrative future YES39c/NO20c require
fresh underwriting. Shared traffic, model releases, display/revision and AI/HLE
risks get no diversification or hedge credit. Variable Aave3.119% is a dated cash
alternative, with actual funding and gas still relevant.
