# Opportunity method review — October 12, 2026

The pipeline has useful execution controls and evidence-preserving batches, but
its discovery coverage was weaker than its review volume suggested. A quiet
scan supports a scoped result, not a conclusion that accessible opportunities
do not exist. The main improvements are to expose omissions, stop using a
falsified probability curve, and spend limited quotes on more than the same
midpoint-ranked baskets. More repeated reasoning on unchanged holdings is not
a substitute for independently verified candidate economics.

This review changed discovery/review tooling and guidance. It placed no order,
changed no forecast, moved no funds and certified no new investment. Three
bounded independent audits used retained public-data artifacts; the primary
review checked the changes and a matched-input selection diagnostic.

## Findings and changes

| Stage | Finding | Resulting change |
|---|---|---|
| Discovery | Survivors were volume-ranked and capped before the optional dominant-side carry filter. A nonqualifying high-volume row could occupy a slot that a lower-volume qualifying row needed. Fetch/filter/top omissions were unmeasured. | Carry filter now precedes top-N; snapshots report actual fetch termination and disjoint first-failed-filter counts, eligible-before-top, selected and omitted counts. `--top 0` keeps all filter survivors. Gamma liquidity no longer claims to guarantee a fill. |
| Context | Verified identity/criteria hashes demonstrated packet fidelity, not universe completeness. Price deltas alone were not a current-opportunity queue. | Packets expose upstream pagination/cap limits separately from integrity, and invalidate delta comparability across selection-policy versions. Guidance requires complete scanner review, explicit unreviewed states, case dispositions and re-review on source/cost/horizon changes even without a 3pp move. |
| Favorite-price profile | The June calibration failed July replication, yet still generated win-rate, edge, APY, selection and ranking. Its prose also specified a stale instance haircut. | Removed the curve and all probability/edge/APY fields and population-derived default category exclusions. The transparent price/horizon profile supplies exact identities, both-side context and explicit non-execution flags. Legacy `--min-edge-pp` warns and is ignored. |
| Monotonicity | A middle-page request failure could be skipped without incomplete-coverage telemetry or nonzero exit. Malformed/unknown inputs could resemble clean exhaustion. | Reports attempted/successful/failed pages, actual stop and completeness. Fetch/schema failures return nonzero while preserving observations; caps and unknown list sources remain incomplete. |
| Basket consistency | Midpoint rank and group size consumed a bounded validation budget repeatedly; incomplete coverage was already correctly reported. | Default balanced selection reserves group and leg capacity for priority and exploration, rotates least-recently-attempted exact membership/criteria fingerprints, then backfills unused capacity. Historic timestamps do not count as current attempts. Quote identity/fee/depth checks and hard resource caps are preserved. |
| Economic evaluation | Active guidance conflated a five-share order minimum with $5, and an old sports fee percentage with the per-market curve. | Guidance and discovery metadata now distinguish share quantities from route USD minimums and use current nonlinear fee evidence. No execution limits were removed. |
| Entry handoff | Uncapped taker execution could reuse the earlier ask when its final ask read failed; single-entry probability/bound checks were weaker than bundle checks. | Missing final taker asks now stop before reservation/order. Single-entry finite probability and pessimistic-bound validation prevents invalid/NaN inputs from passing comparisons. Valid-input sizing, fee math and caps are unchanged. |

The basket selector retains `--live-selection midpoint` for comparison. The
favorite profile remains a bounded, liquid short-window sample, not a new
predictive strategy. Scanner gross thresholds are discovery screens; no general
1pp entry floor was added. Historical forecasts, backtests, financial records,
priors and losses are preserved.

The entry correction closes the specific missing-final-ask fallback and invalid
numeric-input paths. It does not make the legacy ask reader independently prove
book timestamp, exact condition identity, settlement horizon, probability truth
or the best alternative. The analyst still supplies current complete evidence
before using a vetted writer; a signed price ceiling alone is not that evidence.

## What the retained full check covered

The October 12 02:00 collection fetched 997 primary markets and 41,028 embedded
thin-tail markets, retained 80 and 1,721 rows, and emitted 1,304 rows in 74 context
batches. Proof checks covered those batches and all 1,801 retained raw rows;
matched criteria hashes changed zero times. Six thin-tail rows lacked an
execution term. This is evidence of reviewed snapshot fidelity, not all-venue
recall or execution readiness.

The consistency scan found 219 relevant structural groups in a capped slice.
It requested 20, obtained valid quotes for 6, failed 14 and left 199 unquoted.
Its zero positive result therefore covered only a small validated subset.
Sports had 51 filter survivors, 7 surfaced cases and external consensus for at
most the top 3; one of those was unavailable. Macro surfaced 6 with no automated
external consensus. The Abstract June/September 2027 date basket lacked a
substantiated January exit/early-settlement case; a positive provisional floor
was not enough. No January-horizon net-edge case was independently validated
from those receipts.

## Matched-input selection diagnostic

One read-only 20-page event fetch ran at **07:42:55–07:43:01 UTC**. All 20 requests
succeeded; 2,000 event responses contained 40,569 unique market rows after 609
duplicates. It stopped at the configured page cap: **pagination incomplete**.
No live book or model probability was requested for the following comparison.
All profiles used the same fetched data and clock. The 2.9904% cached carry
parameter was from October 11 10:05 UTC, a context input rather than a verified
current alternative or fixed future yield.

| Profile | Retained rows | Metadata deadline by Jan 3 |
|---|---:|---:|
| Old thin-tail CLI: top 3,000, then win-assumed carry filter | 1,598 | 1,334 |
| Corrected filter order, same 3,000 cap | 3,000 | 2,453 |
| Same liquidity/volume/spread filters, no carry filter or top cap | 6,309 | 5,379 |
| Also relax the spread filter for a diagnostic | 7,050 | 5,984 |
| Also remove liquidity/volume floors for a diagnostic | 30,745 | 25,377 |

The old ordering discarded 1,402 rows after selecting its top 3,000. There were
3,316 carry-filter survivors in total; the corrected cap still omits 316. The
6,309-row profile contains **4,711 additional rows** versus the old CLI. These
are missing review opportunities, not 4,711 mispricings. A January metadata
deadline is not a verified settlement date, and the wider population includes
many routine sports and crypto-price questions. No additional-row profit or
future ROI improvement is asserted.

Retained local input: compressed public market JSON, 15,526,024 bytes;
uncompressed SHA-256
`cff013d9cfb60403bed986e2b816e1b211d3d3c852dc0da8ae2ca47af897906a`.
Profile comparisons were corrected/replayed offline to reproduce the old
post-top carry filter literally; there was no second network fetch.

## Evaluation method going forward

[The operating method](../strategy/03_opportunity_method.md) now connects
declared coverage to exact cases, independently dated evidence, both-side
probabilities, all-in dollar economics, joint portfolio judgment and guarded
execution. Cheap workers do bounded factual triage/source collection; the
offline organizer calls no model. Primary judgment owns promotion, uncertainty,
size and orders. Repeated cases refer back to exact identity/source-version
dispositions and explicit recheck conditions rather than an old narrative.

The most valuable next information is what can resolve a case's blocker. A
listing without lawful access or a writer is a route-development candidate,
not a present allocation. A remote price target needs a January return thesis.
An inaccessible named source is unobserved. A measured endpoint is not proof
that all configurations or a broader release landscape were searched. A
probability supplied to the entry wrapper still needs upstream validation.

PM is the most developed path, not the whole universe. Reachable spot, lending,
tokenized assets and derivatives share one net-return comparison. The current
on-chain watchlist retains UNI/AAVE, Base stock-token and copper cases with
specific blockers. Historical quoting does not remove those blockers. Aave is
the investable default/floor, not a veto on higher-return accessible candidates;
total marked bankroll is not deployable cash. Retired stock/brokerage recurring
research remains retired. No new timer, watcher or durable goal was created.

A tiny structured case index may later be worthwhile if repeated source/cost
reviews remain the bottleneck. This change uses existing dated case records
and adds exact recency to basket quotes; it does not pretend to have built an
automated all-venue candidate database. More raw rows, tests or model calls
alone cannot demonstrate higher ROI. Track verified cases, economic verdicts,
fillable approved entries, net outcomes and genuinely independent calibration.

## Validation and evidence limits

Validation passed: **245 targeted tests plus 169 money-math regression checks**;
shell syntax and diff-whitespace checks passed. DEC-0190 records this scaffolding
decision and the observed validation, without claiming a profitable strategy.
All 189 preceding decision rows and the other financial/prior/watchlist records
were preserved.

Offline tests cover top/filter counterexamples, filter-count reconciliation,
caps versus exhaustion, malformed fetch pages, both-side identity and legacy
flag invariance, false historical-attempt counts, criteria-change requeue,
leg-budget starvation, invalid/model-parsed probabilities, missing final taker
asks, rollback/pair and watcher compatibility, and the existing money-math
suite. Live validation in this review is the public discovery
diagnostic only; basket scheduling has not yet demonstrated improved live
quote yield or net profitability. Sequential old portfolio quotes were not
used to authorize an action. The ad-hoc quick status showed PM midpoint/depth
$36.54/$34.02, unchanged at rounded precision; no complete new bankroll snapshot
was synthesized.

Local audit artifacts: `logs/scanner_review_20261012/{coverage,evaluation,alternatives}_audit.*`;
matched-input evidence: `data/scanner_review_20261012/selection_probe.json` and
the saved input/profile files. Original full-check command streams remain in
`logs/checkin_20261012T0200/routine/`; these are bounded observations, not future
execution evidence. Current share-minimum semantics were independently checked
against [Polymarket's order documentation](https://docs.polymarket.com/trading/place-orders).
