# Primary Senate and joint-chamber model — research v1

**Later evidence:** the [23:39 Idaho source revision](senate_idaho_revision_2337_method.md) gives current rounded D56/R43/Other1, DD51/RR15. The v1 values below remain the original dated model; no immutable case was rewritten.

This readable version preserves the primary judgment; the initial text is retained in [the dated original](senate_primary_method_initial.md). The primary finalized the research model at 2026-10-17 23:22:42.816170 UTC. Its rounded control values are Republican (R) 42%, Democratic (D) 57%, and Other 1%. Judgment ranges are R 15–75% and D 25–85%; these are specification ranges, not calibrated confidence intervals. For the binary Republican-control claim, NO is 58% because it combines D and Other outcomes. D Senate plus D House is 52%, conditional on a separately imposed 80% House marginal. No venue price entered the model. Call the Map (CTM) displays 56% D and 52.6% without Nebraska; this is an overlapping-source comparison, not an independent measurement or an input probability.

## Frozen claim and seat arithmetic

The primary read all frozen Senate clauses for cases 52 and 73. There are 33 Class II regular contests: 13 D-held and 20 R-held. Adding the Ohio and Florida special elections gives 35 contests total: 13 D-held and 22 R-held. The remaining fixed seats are 34 D-aligned and 31 R. The model asserts all 100 seats in every draw. The old packet's “35 regular plus specials” count is superseded. Source packets link state officials, Senate.gov class lists, and the separate special-election correction.

All qualifying November contests scheduled as of October 31 count, including a runoff held later. A contested seat retains its election party; a noncontested seat is fixed by party on Election Day. Vacancies use the specified last-holder convention. Additional qualifying special elections scheduled by October 31, and affiliation changes before Election Day, remain small, unmodeled risks. Elections scheduled after the rule’s cutoff are not included simply because they later occur in November.

D needs 51 seats. An ordinary 50 D / 50 R result goes to R through the Republican Vice President. Unassigned Independents remain voting seats. If neither party has control—including D 50 / R 49 / I 1—the result follows the affiliation of the first selected Pro Tempore. An Independent counts for a party through a formal caucus or, for a newly elected member, an announced intent to caucus. If that intent is initially unknown, the contract may remain open until an announcement or January 4, 2027, at 23:59 ET; without an announcement by then, the member remains unassigned. An Independent's win or a Democratic endorsement alone does not meet that rule. A Pro Tempore may be affiliated with neither major party, so R NO and D YES are distinct claims; the four major-party joint claims do not exhaust every possible payout. The rules specify adjudication and credible-reporting sources but do not guarantee November redemption. January 4 and organization ordinarily fit the project's January horizon; court, runoff, or dispute delays could exceed it.

## Evidence, corrections, and coverage

All 35 state entries were examined through the current directory and primary sources. The directory is a source pointer, not binding or forecast authority. Current original polling covers Maine, North Carolina, Ohio, Texas, Iowa, New Hampshire, Michigan, Georgia, Minnesota, Nebraska, Kansas, Florida, South Carolina, Arkansas, and South Dakota. Minnesota's underlying source is original, but the displayed remainder/chart method is unresolved. Alaska's October result is an attributed transcript; the direct original-source request returned HTTP 403. Additional original partner releases cover Illinois, Massachusetts, Virginia (an older hypothetical Warner matchup), and Tennessee. Candidate certification remains incomplete in several states. Kentucky, Rhode Island, Alabama, and Oklahoma rows remain secondary or limited and receive capped weight. New Jersey, Delaware, Colorado, Oregon, West Virginia, and Wyoming have no current matched poll in the reviewed directory; that is a bounded coverage observation, not proof of universal absence. Every seat remains modeled.

The primary added two close Kansas Hamilton/Marshall polls before finalizing. Florida uses Angie Nixon, not older Vindman matchups. All three New Mexico directory links were opened and found to report Haaland/Hull governor polls; none was reinterpreted as Senate data for Lujan/Marker. For South Dakota, the primary visually read the original Concord image: Bengs 43 / Rounds 42 / Other 5 / Don't Know 10, n=400 likely voters, fielded October 6–8, with a ±4.9 percentage-point share margin of error. The initially reversed source packet remains archived with an explicit superseding correction. A misspelled Kyle Achilles search was corrected to Todd; a current campaign-hosted CBS title supports no-party-caucus intent, while the transcript gap remains.

Official South Dakota listings show Bengs (I) and Rounds (R) active and Beaudion (D) withdrawn. Montana's official filings list Alme (R), Bankhead (D), Bodnar (I), and Austin (Libertarian), plus a write-in; filing is not final certification. Idaho's official final ballot was not recovered. The original ATR three-way poll reports Achilles 45.5 / Risch 39.4 / Loesby 4.5, n=700 registered voters, September 13–16; the newer Peak directory attribution reports I 24 / R 49, but is unverified. Mississippi's official qualifying list is not the final ballot. Its original August three-way poll reports Hyde-Smith 49.4 / Colom 42.7 / Pinkins 7.9. A post-biography two-way test and an unverified October two-way result were not substituted for the full field.

Louisiana's 2026 Senate election uses spring closed-party primaries and a November plurality general election, as separately verified with the official Secretary of State. Old House/open-primary rules were not carried over. The latest Hart row remains campaign-sourced secondary evidence; its full instrument and ballot are unavailable. Oklahoma's directory's “special” label and current nominee remain unresolved officially; official Class II succession supports one upcoming seat, not a duplicate.

The 2024 FEC workbook, all 51 jurisdiction totals, and hashes were checked. Its national all-vote D-minus-R margin is −1.471909 points. Official Clerk totals differ, so candidate personal-overperformance differences use same-source Clerk state presidential and candidate denominators rather than mixing counts. Brown +7.588648 points, Osborn +13.785791, and Peltola +11.098962 are descriptive context only; Alaska is first-choice House candidate support, not a final-round ranked-choice margin. Source-precision, nominee, and candidate-field limitations remain explicit in the inputs.

## Model construction and assumptions

For ordinary D/R seats, the prior center is:

> 2024 state D–R margin + 0.8 × (judgmental generic D8 − 2024 national D–R margin) + declared candidate adjustment + 0.75 × observed personal overperformance, where applicable.

Generic D8 is a judgment informed by original Fox certain-vote D6 and YouGov loose/strict D8/D11 results; it is not a trained aggregate. The candidate adjustments—Maine −10, North Carolina +3, Texas +3, Iowa +1, New Hampshire −3, Michigan −2, Minnesota −2, and Georgia +1 points—are judgmental. Maine −10 is not claimed to be a retrieved 2020 result. Personal-retention values from 0 to 1 are tested, but causal retention is not identified.

| Component | Primary treatment |
|---|---|
| Poll variance | Candidate-share MOE is conservatively doubled to obtain a margin standard error; disclosed source and age uncertainty are added, followed by a shared-source floor of 1.5 points. |
| Missing precision | Assumed values, including subgroup precision, are labeled sensitivity assumptions, not publisher-reported MOEs. |
| Prior/poll blend | Bayesian-style blend with a 7-point prior SD; weak-provenance evidence has a capped weight. |
| Poll/cycle error | Mean poll shift −1.5 points; shared poll-bias draw SD 1 point; national SD 3 points; regional SD 1 point; future residual SD 2 points. These are uncalibrated primary choices. |
| Dependence | Each physical poll enters once. Older same-pollster context is not counted as independent confirmation. |

Historical presidential priors can miss a new candidate. Breadth of current evidence and sensitivity analysis matter more than nominal simulation precision.

Idaho and South Dakota are modeled as explicit Independent-versus-R contests; no Democratic nominees are invented. Idaho alternates equally between the original ATR result and the unverified Peak regime: margins +6.1 and −25 points, with residual SDs 8 and 12. Equal weights are judgment, and both extreme weights are tested. South Dakota uses 85% weight on the latest primary Concord reading and 15% on the older secondary counter-reading, with margins +1 and −4.5 and residual SDs 7 and 10. These Independent races receive national and poll-bias loadings of 0.5, rather than the D-candidate loading.

Montana uses a relative R/I/D/Libertarian margin-utility model, not a vote-share forecast. Its primary local report is R 45.1 / I 26.1 / D 18.9, with newer secondary context. The 10% strategic-consolidation branch is an explicit, unfitted judgment tested at 0% and 25%; it is not an empirically estimated frequency.

| Independent winner | Future D caucus | Future R caucus | Neither |
|---|---:|---:|---:|
| Nebraska (NE) | 35% | 10% | 55% |
| Montana (MT) | 10% | 5% | 85% |
| Idaho (ID) | 5% | 5% | 90% |
| South Dakota (SD) | 2.5% | 2.5% | 95% |

South Dakota's direct statement and Idaho's campaign-hosted title indicate no-party-caucus intent. Reversal probabilities are judgments about future behavior, not current party pledges. Actual first-Pro-Tem selection is endogenous; the central conditional branch is 45% D / 45% R / 10% Other, with extremes tested. Tiny minor-candidate or write-in wins are not separately simulated in ordinary states; that is specification risk, not a literal zero probability.

The joint House model uses completed case 10's 80% marginal and a 0.70 shared-national normal loading; it is not a new 435-district simulation. Loadings 0.35 and 0.85 are tested. House Speaker fallback and rare Independent House organization remain case 10 range risks. See the [code](senate_primary_model.py), [inputs](senate_primary_inputs.json), [results](senate_primary_results.json), [skeptic](../advisories/senate_fullfield_skeptic.md), and [champion](../advisories/senate_fullfield_champion.md). A corrected shorthand distinguishes the branches: ordinary 50/50 uses the Vice President; the Pro Tempore branch applies when D is below 51 and R is below 50.

## Results and sensitivity

The primary ran 24 scenarios × 60,000 draws, with exact-seat and joint-mass assertions. Central raw outcomes are D 56.845%, R 42.0217%, and Other 1.1333%. Ambiguous-organization mass is 11.405%; mean D-aligned seats are 50.494; the 10th/50th/90th seat quantiles are 47/51/54.

| Senate / House result | Central probability |
|---|---:|
| D Senate / D House | 52.270% |
| D Senate / R House | 4.575% |
| R Senate / D House | 26.873% |
| R Senate / R House | 15.149% |
| Other Senate / D House | 0.920% |
| Other Senate / R House | 0.213% |

The four ordinary major-party cells omit Other-Senate mass. Zero sampled safe-seat wins are finite-draw results, never literal impossibilities. Binomial Monte Carlo error is about 0.2 points and much smaller than parameter uncertainty.

| Sensitivity | D-control result |
|---|---:|
| Mean poll bias 0 / −3 points | 66.99% / 46.13% |
| Generic D6 / D10 | 50.54% / 63.07% |
| No / full personal-overperformance retention | 49.33% / 59.25% |
| Ambiguous organization assigned to R / D | 51.63% / 63.04% |
| No / all new Independent D credit | 56.29% / 63.55% |
| ID all ATR / all Peak regime | 58.79% / 54.90% |
| MT 0% / 25% consolidation | 56.64% / 57.07% |

The “no new Independent D credit” extreme sets both D and R credit to zero, leaving every newly elected Independent unassigned; it does not shift all of them to R. For House loading 0.35 / 0.85, D Senate plus D House moves to 48.75% / 53.88% while the Senate marginal stays fixed.

Two stacked assumption scenarios show how several judgments can compound. The adverse-D case (generic D6, −3-point poll bias, zero personal retention, no new Independent D credit, and R-favoring Pro Tempore) gives D 27.617% / R 72.383%. The favorable-D case (generic D10, zero mean poll bias, full personal retention, all new Independent D credit, and D-favoring Pro Tempore) gives D 80.353% / R 19.647%. These are assumption scenarios, not likelihood-weighted confidence bounds.

The primary adopts rounded R42 / D57 / Other1 with broad ranges. For standalone chamber control and DD, a 15-point entry reserve adds five points to the ordinary 10-point reserve for uncalibrated chamber and organization mapping; it cannot guarantee protection from every model failure. Case1822 uses the ordinary10-point reserve for RR: its declared scenario movement is about6 points, smaller than the standalone/DD variation. The individual report documents that choice before its quote, retains a wider3–35% specification range, and places no order. Per-case reserves govern rather than a blanket reserve for every joint event. The work flags shared U.S. politics risk with four existing House bids and claims neither a measured hedge nor free capital. Any action remains maker-only and requires current fee, order-book, account, whole-fill-cap, source-catalyst, and monitoring checks. The source calendar includes all-state poll releases, debates/early voting, the October 31 qualifying-election cutoff, the November 3 election, Georgia runoff/certification/caucus announcements, and first Pro Tempore selection. Resting orders should not remain through known information windows without revaluation. Cost, carry, and still-unfilled resting orders are separate from research fair values.
