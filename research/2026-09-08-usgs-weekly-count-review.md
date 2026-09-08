# USGS weekly earthquake count — 2026-09-08 02:54–03:01 UTC

**Outcome: no entry, no calibrated forecast.** A measurable source exists, but
the apparent YES edge depends on the historical window. No current portfolio
prior, order, position, or strategy rule changed.

## Exact contract and current observation

[Gamma market 4223844](https://gamma-api.polymarket.com/markets/4223844) is
**six or fewer**, not exactly six, worldwide earthquakes of magnitude **≥5.5**.
Slug `will-there-be-6-earthquakes-of-5pt5-or-above-magnitude-worldwide-copy-copy`;
created Sep-4 18:44:44.634788 UTC; condition
`0x9a98524b9b3c92df212408993583404c8b7a7c9296eef9b6aacc5422fd26d6a6`.

The literal interval is Sep-7 00:00 through Sep-13 23:59 **ET**, corresponding
to Sep-7 04:00 through Sep-14 03:59 UTC. Gamma's endDate Sep-14 23:59 UTC is
not the literal counting cutoff. Resolution waits until the interval ends;
the rules allow 24 hours for final-day magnitude revisions and up to 48 hours
for a substantial delayed event. Total source absence at the 48-hour deadline
resolves to the lowest bracket. None of those fallback conditions is active.

The [USGS query interface](https://earthquake.usgs.gov/fdsnws/event/1/) accepts
explicit time zones and otherwise defaults to UTC. Used minmagnitude=5.5,
eventtype=earthquake, no contributor/catalog restriction, preferred event
records, and unique IDs. The current-window query through **02:54:56.479495 UTC**
returned **one** event: `us7000teu1`, M5.5, southeast of the Loyalty Islands,
Sep-7 05:50:44.529 UTC, reviewed, last updated 07:56:59.549 UTC. The exact
threshold magnitude is still subject to revision; reviewed does not mean final.
[Timestamped query](https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2026-09-07T04:00:00Z&endtime=2026-09-08T02:54:56.479495Z&minmagnitude=5.5&eventtype=earthquake&orderby=time-asc).

## Quote snapshot, not a standing executable promise

Both exact-token books were received at **02:56:27 UTC**, with asset and condition
IDs checked. Their snapshot timestamp was 1788836182012, about six seconds old.
Fresh Gamma structured fee rate .05 / exponent 1 gives fee .05 × p × (1−p).

| Side | Top ask / shares | Fee-inclusive cost per share | Raw p required after 10pp stress, before other costs |
| --- | ---: | ---: | ---: |
| YES | .25 / 44.91 | .259375 | >.359375 |
| NO | .78 / 103.99 | .788580 | >.888580 |

YES token `14932035906628239972698772998699250517943278077449455611075822441898720020558`;
NO token `111241994161502715320737359766551615998056442504705556718291750905021116433484`.
Book minimum 5 shares, negative-risk true. Reads were sequential; no paired-
execution claim. These thresholds do not include a full sizing/cash/entry check.

## Descriptive history and temporal sensitivity

[Historical query](https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2024-09-02T00:00:00-04:00&endtime=2026-09-07T00:00:00-04:00&minmagnitude=5.5&eventtype=earthquake&orderby=time-asc&limit=20000)
returned **960 features / 960 unique IDs**, well below the requested 20,000 cap.
Main independently reproduced the worker's statistics at 02:59 UTC. The response
omits metadata.count; the separate [count endpoint](https://earthquake.usgs.gov/fdsnws/event/1/count?format=text&starttime=2024-09-02T00:00:00-04:00&endtime=2026-09-07T00:00:00-04:00&minmagnitude=5.5&eventtype=earthquake)
also returned **960**. All records passed magnitude/type checks.

Bins are 105 complete local Monday-to-Monday weeks, DST-aware. The first-period
cutoff is 22h 54m 56.479495s after each local Monday midnight, matching
the current observation's elapsed time. These full-week bins are a historical
proxy, not an interpretation of the contract's final-minute boundary. Each event
is included once; the sum of weekly counts is 960.

| Cohort | Weeks | Mean / population variance | Total ≤6 | Remaining ≤5 | Total ≤6 when first-period count =1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| All | 105 | 9.143 / 45.037 | 33/105 (31.43%) | 40/105 (38.10%) | 14/34 (41.18%) |
| Older | 53 | 8.623 / 69.782 | 23/53 (43.40%) | 24/53 (45.28%) | 10/15 (66.67%) |
| Latest | 52 | 9.673 / 19.259 | 10/52 (19.23%) | 16/52 (30.77%) | 4/19 (21.05%) |

The pooled conditional rate clears the quoted YES threshold; the latest-year
conditional rate fails even before the ordinary 10pp stress. Its NO complement
is only about .7895, barely above .78858 before stress and other costs. Neither
direction supplies a robust edge across these basic alternatives. Do not select
the older/pooled sample just because it makes a trade look good, or declare the
recent sample uniquely correct. Counts are strongly overdispersed; clustering,
aftershocks, small conditional samples, revised historical data versus live
publication, and borderline magnitudes prevent treating frequencies as a
validated forecast. No Poisson shortcut or permanent population edge is claimed.

Recheck once in the existing **Sep-13 22:00 UTC** periodic run, when substantially
less of the window remains. Read the exact catalog/timeframe and fresh book;
reassess revisions and delayed publication before any probability or entry gate.
No new scanner, daemon, cron, funding action, or repeated minute-by-minute query
is justified by this lead. Delete the dated reminder after that review.

## Archived derived counts

Tuples are `(whole-week count, first-period count)`, in local Monday order from
2024-09-02. These preserve this retrieval's sufficient statistics; they are not
a raw catalog archive or a forecast/calibration ledger.

```text
(5,0),(8,0),(6,2),(4,2),(5,1),(4,2),(7,0),(6,1),(3,0),(9,0),
(4,1),(4,1),(4,0),(16,0),(7,3),(6,2),(9,1),(10,2),(6,1),(3,1),
(9,2),(5,1),(9,3),(4,0),(6,0),(5,0),(5,0),(5,0),(10,2),(10,1),
(13,1),(5,1),(10,0),(9,0),(12,0),(8,2),(7,0),(8,0),(10,0),(9,1),
(8,0),(4,0),(7,3),(8,0),(2,1),(20,3),(18,2),(63,3),(12,1),(9,0),
(8,2),(9,3),(4,1),(5,1),(17,1),(9,2),(8,1),(24,1),(7,2),(8,1),
(10,3),(21,5),(4,1),(7,0),(6,0),(8,0),(10,6),(10,2),(9,1),(7,0),
(10,1),(6,1),(6,2),(10,6),(8,0),(8,0),(12,4),(6,2),(10,1),(4,2),
(13,0),(7,1),(17,1),(2,1),(9,1),(8,2),(3,0),(11,2),(7,0),(12,1),
(7,2),(13,1),(10,6),(10,2),(10,0),(10,1),(6,2),(14,2),(8,3),(16,0),
(7,0),(20,2),(14,1),(7,2),(12,1)
```
