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

## Final-window recheck — 2026-09-13 22:00–22:04 UTC

The exact named-source query through 22:01 UTC returned **three** qualifying
events, leaving just under six hours until the literal Sep-14 03:59 UTC cutoff:

- `us7000teu1`, M5.5, Sep-7 05:50:44.529 UTC, southeast of the Loyalty Islands;
  reviewed, last updated Sep-8 05:56:40.942 UTC.
- `us7000tgl2`, M5.9, Sep-11 11:56:23.115 UTC, east-northeast of Lospalos;
  reviewed, last updated Sep-12 12:04:14.404 UTC.
- `us7000tgrk`, M6.5, Sep-11 21:23:55.907 UTC, north-northeast of Teluknaga;
  reviewed, last updated Sep-12 21:29:59.017 UTC.

A broader M5.0 query found one reviewed M5.4 and five reviewed M5.3 events in
the week, but none near the closing boundary and none whose promotion alone
would threaten the <=6 outcome. The M5.5 threshold event and all catalog
history remain revision-sensitive. Indeed, the same two-year historical query
now returns 959 qualifying events rather than the Sep-8 snapshot's 960, direct
evidence that retrospective counts can change.

The historical final-six-hour slice contained four or more new events in 2/105
weeks; among the five weeks with three events at the matching cutoff, none
finished above six. Hourly rolling six-hour windows had >=4 events in 93/17,494
(0.532%); after a preceding 48 hours with zero events, as now, the rate was
5/1,886 (0.265%). Those overlapping positives represent only a few clusters,
and a Poisson benchmark gives 0.036%, so none is a calibrated tail probability.
A broad honest range leaves only a small possible central YES edge and material
model uncertainty.

The exact token/condition identities still match. The latest book timestamp was
21:57:12 UTC, already about four minutes old at inspection. YES offered only
eight shares at .990; its .05 x p x (1-p) taker fee makes the all-in cost
**.990495**. NO offered 15.18 shares at .069, or **.072211** all-in. YES therefore
needs p>.990495 before funding and operating costs; even a .995 point estimate
earns only about 2.3 cents at the five-share minimum, while the applicable tail
stress makes it decisively negative. The wallet has only .173070 pUSD, so an
Aave withdrawal and wrap would cost more than that optimistic sliver. NO is far
below its executable break-even under every defensible estimate.

**Final verdict: SKIP both sides, size zero.** No order, reservation, funding or
new monitor is warranted. The dated Sep-13 reminder is closed; ordinary
resolution monitoring can handle the final catalog/revision window.
