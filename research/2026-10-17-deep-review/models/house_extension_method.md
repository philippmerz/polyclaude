# Primary district review — sixteen additional House contracts

October 17. Each exact condition was read in full and matched to the current
district, party, outcome tokens and rule fingerprint. The common rule is party
of the winner **when all 2026 House elections are conclusively called**, with a
most-recent caucus-intent test for a winner without a major-party ballot label.
Credible consensus governs, with FEC official results if ambiguous. It is not
the Senate nominee-replacement template or necessarily an election-night cash
release. Minor and independent candidates can make both major-party YES claims
lose; binary D/R complementarity is not assumed to be a contractual arbitrage.

Source packets include `election_district_sources.json` (with its explicit
NC/OH corrections), `election_extension_sources.json`, its corrected source-URL
copy, `district_depth_followup_sources.json`, `map_pvi_binding_followup.json`,
`house_ballot_final_followup.json`, `house_2024_context_followup.json`,
`wa05_prior_election_followup.json` and both ME02 follow-ups. These are factual
retrieval packets; their author's views did not select forecasts or reject cases.
Each case lists its material specific inputs and gaps below the shared model.

## Map and candidate binding

Cook's official 2026 PVI update explicitly says the new maps' 2020/2024
presidential returns have been recalculated; its current race pages are up to
date while the static April2025 table is not. Therefore stale-looking
November2025 field metadata alone is not a reason to discard FL03/FL07/TN04/AL02.
Current displayed PVIs are respectively R+10/R+5/R+11/R+7. Florida's current
map was signed May4; Tennessee's boundaries changed effective May7. Alabama
uses the restored legislature's2023 map, **not the 2024 court map**. No
independent block-level presidential reaggregation was performed.

The Census2026 boundary statement, plus Virginia's direct election-agency
notice and court record, establish unchanged boundaries for WA, NV, NH, VA,
NY and NE relative to2024. NC01 changed inOctober2025; its old Davis/Buckhout
margin is not transferred to the new district, despite the same candidates.
California also changed its map. Candidate lists and ballot labels are tracked
separately from geography and incumbent names.

Current official ballot evidence is complete for FL03, VA01, VA02, NC01, NE02
and NY22, and district-specific county evidence covers CA06. TN04/NH01/NH02
and NV04 still have attributed secondary final rosters after direct state-source
failures. GA10 has official primary-winner evidence and a certified independent
write-in notice, but no captured full printed general ballot. Those gaps remain
in the forecasts, rather than turning an older group-item label into a fact.

## Transparent primary model

`house_extension_model.py` and its saved results contain all inputs. No prices
or previous screen labels are inputs. These are **uncalibrated primary
sensitivities**, not an authoritative election model. The initial D-margin
center is nationalD+8 plus80% of twice the signed PVI share differential, with
explicit small incumbency/candidate adjustments. Three-point national error
and six-to-seven-point local error are retained. PVI is a relative **share**
measure, so multiplying by2 avoids the earlier share-versus-margin trap.

Where unchanged geography and incumbent history are relevant, the source's
2024 House margin is a separate mixture component with8pp error. It moves by
80% of a national swing from a rounded−2.5D modeling reference to currentD+8.
That reference is an assumption, not a separately recounted official national
popular-vote total; the grid varies it by±2. Historical weights are reduced
when one or both nominees change, and incumbency changes are explicit. New
map old results are never plugged in as current-district results. This is a
way to test candidate overperformance, not to count history and PVI as two
independent measured samples.

The 2024 House Clerk statistics are compiled official candidate counts but
describe themselves as immediate results. Margins are derived from valid
candidate votes, including valid write-ins. NY fusion lines are consolidated
by candidate; blank and void votes are excluded and valid scattering retained.
Its correct derived NY22 margin is9.112pp, not the preliminary9.1223 that omitted
scattering. WA's separate SOS page has Baumgartner60.57/Conroy39.29; its official
same-district presidential count is also captured. That local overperformance
is why WA05 is not forecast from generic ballot/PVI alone.

Poll updates use twice the reported candidate-share MoE/1.96 for margin sampling
SD, plus3–4pp nonsampling and1–6pp age error. Selected same-sponsor polls do not
supply independent precision. CA06's partly documented September poll has26.7%
undecided and a Kiley-aligned sponsor; a1.5pp pro-Pan bias sensitivity and wider
local error are explicit assumptions, not measured house effects. A−4pp
candidate-context adjustment to the D structural prior reflects Kiley's
independent/moderate positioning and the close named poll, not his former party
label. The final D-party chance also separates Pan winning from Kiley winning
and later expressing Democratic caucus intent. CA06 is not CA04's two-Democrat
closed winner set.

AL02 uses the DCCC's **original named46–46 release**, with a2pp shift againstD
and large age/common error. Other selected partisan47–47/45–44 archive reports
are corroborating context, not independent likelihoods. ME02 uses the recovered
Tulchin original50–46 with500LV/4.38pp MoE and a1.5pp anti-D bias sensitivity.
The memo does not disclose its client, mode or full questionnaire; an archive's
Democratic sponsorship label is not original disclosure. The UNH primary
abstract only verifies a statistical tie; secondary51–45 is not added as a
second primary numerical poll. Golden's2024 crossover vote does not transfer
automatically to Dunlap. WA's May poll is old and is combined with same-pair
history with a large age error, rather than overriding that history.

FL07 has no located current final-matchup public poll. A30% local-R-favorable
branch at D margin−5 is a primary sensitivity acknowledging current external
LikelyR assessment and incomplete local evidence, not a calibrated rating-to-win
conversion or a rejection. Every contract remains valued on both sides. A2%
unmodeled symmetric branch and small explicit other-affiliation probabilities
prevent treating normal tails or binary party identity as certain. These weights
are also judgments, not observed failure frequencies.

The saved grid varies national margin4/8/12, PVI transfer.6/.8/1, poll bias±3,
and the history reference. The narrative ranges deliberately cover that grid
and more; they are not confidence intervals, validated floors or evidence of
calibration. More local facts can move a point forecast materially. Shared
national/PVI/turnout errors mean sixteen rows are not sixteen independent edges.

## Economics and follow-up

Both complete ten-share ask walks include per-level fees, ages, minimums, exact
tokens, immediate exit and55-day carry sensitivity. Maker ceilings use the
ordinary10pp reserve before carry, funding and operational margin; they do not
assert every point in the broad range is profitable. Dollar and share minima
must both be checked at actual size. No measured tail is established for K=5.
Primary hypotheses that pass that numerical reserve remain hypotheses requiring
fresh source, identity, UMA, book, account, correlation and monitoring checks.

CA06 NO and ME02 YES merit concrete small-maker review at the captured prices;
VA01 YES is thinner. These are potential expected-return trades, not guaranteed
arbitrages. NC11/OH07 NOs, ME02 YES and VA01 YES load differently on a Democratic
wave, but all still share US-politics data and adjudication risk. Use the existing
cluster and joint exposure accounting, not invented independent labels. Ordinary
maker-or-skip applies; do not buy a nonurgent ask to manufacture a filled result.
Reopen after new October polls, ballot/candidate changes, independent caucus
statements, verified spending/campaign developments or election calls. Normal
late2026 settlement fits January, but all-House-call/certification disputes can
delay payment beyond the planned55-day carry window.
