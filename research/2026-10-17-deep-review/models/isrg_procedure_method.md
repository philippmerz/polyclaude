# Intuitive Q3 2026 procedure growth: primary joint valuation

October 17. The complete frozen descriptions for 222, 812, 1262, 1672 and 1983
are identical, with five different brackets of one metric. The target is
**worldwide da Vinci procedure growth, year over year, for Q3 2026**. Ion,
combined procedures, revenue, system placements and earnings are different
metrics. Use the most precise explicitly reported specified metric, not an
analyst's reconstructed ratio; exact boundaries select the higher bracket.
Omitted metric or no Q3 materials by November 30 ET selects the lowest bracket.
Later revisions are ignored; the stated webcast fallback remains available.

The scheduled October 20 call is 20:30 UTC, before the 22:00 UTC metadata end.
That metadata is **not** the literal late-publication cutoff: the rule explicitly
allows Q3 materials through November 30. The exact Q3 press-release time was
not found. Normal October resolution fits January; missing data and disputes
can extend the lockup.

## Load-bearing evidence

The July 16 official release reports da Vinci growth about 15%, Ion about 36%
and combined growth about 16%. It guides annual da Vinci growth 13.5–15.5%,
expecting closer to the midpoint. That is annual guidance, not a Q3 or H2
forecast. Eight historical quarterly da Vinci figures are about 18, 18, 17, 17,
19, 17, 16 and 15% from Q3 2024 through Q2 2026. The deceleration is real;
these few rounded, nonstationary observations do not calibrate a tail.

Root independently read the SEC Q2 table: Q2 2026/2025 estimated procedures
889k/775k; H1 1,737k/1,507k. The reported growth column is whole-percent 15%.
The footnote says counts are rounded to thousands and growth uses unrounded
approximate estimates. Q1 847k plus Q2 889k is 1,736k, whereas independently
rounded H1 is 1,737k; this is not evidence of a missing thousand procedures.
Official supplemental history gives 2025 Q3 797k, Q4 849k, full year 3,153k.
Derived count ratios are **forecast inputs only**, not more precise reported
settlement figures. SEC's account also describes estimation/reporting error.

The latest checked SEC/IR lists add no later written procedure guide. The
September 9 Wells Fargo conference was listed but not listened to; an oral
update remains a specific coverage gap. Some direct investor-host requests
returned 403 and the legacy supplement host failed DNS; the captured SEC 10-Q
and browser-rendered official table provide the underlying facts. No inference
comes from an error page. Sources and receipts are indexed in
`isrg_procedure_guidance_detail.json` and `earnings_metric_history_sources.json`.

## Primary model, assumptions and precision

At a mathematical annual midpoint of 14.5%, the approximate-count bridge is
`(3153*1.145 - 1737)/(3153-1507) - 1 = 13.802%` H2 growth. This does not mean
management guided H2 or Q3 to 13.802%. The model uses a 75% guidance-anchor
regime with that center, primary annual-center SD 0.5pp amplified into H2,
1pp Q3-versus-H2 allocation uncertainty and 0.2pp count/input uncertainty.
Combined SD is about 1.40pp. A 20% persistence/guide-beat regime centers Q3 at
15.2% with 1.2pp SD; 5% disruption centers it at 11.5% with 3pp SD. Weights and
spreads are primary judgments, not measured regime frequencies. The persistence
branch admits sustained recent activity; the bridge admits the lower annual
guide and harder comparison. A 0.3% omission/delay branch selects the lowest
bracket. These assumptions can be wrong together.

Historical materials report whole percentages. The model gives 85% weight to
that presentation continuing and 15% to a more precise explicitly reported
metric. Thus a reported 15% selects 15–17.5, while an underlying 14.7% that is
only published as 15% does not select 12.5–15. No self-calculated ratio overrides
the official reported value. This precision fork changes probability materially.

The resulting unrounded partition is 1.70%, 15.14%, 46.65%, 35.53%, 0.97% for
the ascending five brackets. Largest-remainder rounding preserves unit mass:
2%, 15%, 47%, 35%, 1%. A 2,187-scenario grid varies annual center and spread,
quarter allocation, persistence/disruption weights, precision and fallback.
The reports' wider ranges are scenarios, not confidence intervals or floors.
The full reproducible arithmetic is in `isrg_procedure_model.py/results.json`.

## Economics and management

Each child has both-side ten-share walks with the captured 4% rate, exponent 1
taker fee, depth, minimums, ages and exit estimates. Maker fees are zero only
for a genuine post-only fill. At the dated quotes, the 15–17.5 child has a
potential small passive YES case: primary 35%, default-stressed 25%, versus a
23c bid/24c ask. This is a thin, assumption-sensitive expected-return thesis,
not a lower-bound arbitrage. The other children do not clear the ordinary
reserve at their captured offers. Missing asks are unavailable routes.

Before any money, resolve the unreviewed conference gap as far as practical,
run independent advisory challenge, establish real source coverage, and recheck
current criteria, UMA, exact tokens, fees, books, account, reservations and caps.
The quarter is already over and actual results are private before publication;
an unexplained move may be informed. Pull any resting quote before the known
earnings window and reconsider immediately on news. All five legs share one
issuer/metric risk; do not size them independently. Six-day constant Aave carry
is only an alternative sensitivity, not free deployment or a payout promise.
No order, canonical prior or reservation is created by the model.


## October 17, 21:23–35 UTC — ISRG conference follow-up and advisory correction

The September9 official event/player shell was located; no issuer transcript,
captions or audio was independently reviewed. The publicly captured secondary
StockAnalysis/Quartr transcript attributes a reaffirmed13.5–15.5% annual global
range, nearer midpoint, to CFO Jamie Samath. He declined regional guidance and
said harder H2 comparisons and ACA effects were already in that range. This
does not supply a numeric Q3 da Vinci-only forecast; Ion-inclusive commentary
is not the settlement metric. The primary retains the35% point for case1262
and the original broad3–80% scenario range. Reaffirmation supports the existing
guide anchor and is not an independent second likelihood. The archived report's
unreviewed-conference statement is superseded only to this limited extent.

Root caught an independent advisory note's incorrect Q3'25 growth16% claim;
actual official Q3'25 was19%, and16% belonged to Q1'26. The note preserves the
error and appends an explicit correction. The primary model had already used
the correct797k/19% history; it is unchanged. No ISRG order, prior or reservation
has been created. Source packets `isrg_conference_followup.json` and official
historical figures in `earnings_metric_history_sources.json` retain access gaps.
