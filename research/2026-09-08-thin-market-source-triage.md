# Thin-market source triage — 2026-09-08 02:20–02:26 UTC

Outcome: **no entry or new probability estimate justified**. Reused the 01:50:55
1,572-row thin shortlist; did not rerun discovery or treat this bounded review
as exhaustive. Quota probe: 93% main headroom. No order/funding path was invoked.

## HIP-3 open interest: promising measurement question, source gate unfulfilled

- [Exact Gamma market 1185735](https://gamma-api.polymarket.com/markets/1185735),
  slug `will-hyperliquid-hip-3-open-interest-hit-5b-in-2026`, created
  **2026-01-14T21:54:58.022006Z**. Old listing, newly reviewed here—not newly listed.
- Condition `0x3b6ef460b4d6b718240f3d044675d7c1f4a2db41de56e235c87af7c3f37d29dc`.
  Direct Gamma read: open, accepting orders, no UMA proposal; YES/NO .704/.296,
  vol24 ~$535, liquidity ~$783, structured fee rate .07 / exponent 1.
  These are metadata/midpoints, **not executable asks or a complete entry check**.
- The event is any qualifying 2026 daily value at least $5B. It specifically uses
  **Total** on the **HIP-3 DEXs by Open Interest** daily bar chart at
  [Artemis](https://classic.artemis.ai/asset/Hyperliquid?tab=hip_3), and a bar is
  finalized only after the following day's point is published. Intraday aggregate
  OI, general Hyperliquid OI and trading volume are different measurements.
- Web reader failed; direct public HTTP returned 200 and an 86,370-byte client
  application shell. Its embedded page props contained assetId/seoDescription,
  not the daily series. No chart values or 2026 maximum were recovered. This is
  **our retrieval limit**, not evidence that Artemis is permanently unavailable.
  Thus the contract's permanent-unavailability fallback was not activated.
- Bounded primary-domain search returned historical Artemis commentary, not the
  required current/finalized daily history. Discordant third-party OI snippets
  cannot replace the named measurement. Neither $5B having already been reached
  nor a defensible year-end hitting probability was established.

Next useful action is to obtain the exact dated Total series and its following-
day publication evidence, then check the 2026 maximum and model the remaining
window if necessary. No new browser/data-pipeline infrastructure, paid access or
standing order is justified solely by this unmeasured lead. A later intraday
headline alone is not the trigger. Any eventual entry still needs an independent
probability, fee/depth walk and the existing ticket/cluster/cash gates.

## Other saved leads: exact criteria banked, no fresh edge established

| Exact market | Verified mechanics | Triage result |
| --- | --- | --- |
| [3701624](https://gamma-api.polymarket.com/markets/3701624), `next-white-house-press-secretary-announced-by-september-11-2026` | Created Aug-18 16:15:31.055864Z. Trump/administration must announce a replacement for Karoline Leavitt by Sep-11 23:59 ET. Acting/interim excluded; starting service later is allowed. | YES/NO .044/.956 metadata. An imminent deadline alone supplies no probability edge; no verified new personnel fact in this review. |
| [2661524](https://gamma-api.polymarket.com/markets/2661524), `will-the-bank-of-russia-increase-the-key-rate-after-the-september-meeting-20260623013926069` | Created Jun-24 00:25:59.138745Z, not the slug's date-like suffix. Uses the official Sep-11 meeting decision relative to the prior rate; absent a decision by the following meeting's end date, the no-change bracket wins. | Direct YES/NO .016/.984. A separate no-change sibling does not itself establish an increase-NO anomaly. No fresh rate fact or structural contradiction established. |

At these saved NO marks, even p=1 stressed by the ordinary instance haircut of
10pp would be below cost before fees. This is a screening observation, **not a
live book/pipeline verdict**. It does not reject complementary YES research if
a real fresh fact supplies a defensible prior; no such prior was formed here.
No numerical forecast was invented from the low price or short deadline.

## Cross-venue scope check

The existing 01:31 Limitless report contains 709 flagged priced leaves and 18
matched rows, zero verified IDENTICAL, execution_ready=false. Its PM side covers
only the first 3,000 active volume-ranked markets. The displayed positive
midpoint leads were DIFFERENT propositions, not transferable hedges. Do not call
this an exchange-wide zero or open a venue/fund a wallet to pursue these rows.

## 02:36–02:43 follow-up: Chicago housing, no calendar edge established

Read [exact market 2760585](https://gamma-api.polymarket.com/markets/2760585),
created Jul-1 19:56:40.929967 UTC. Condition
`0xb2ad342889b7f07217f3740344ae50b9eb645365e801a7b5396093d64146cb2a`;
slug `will-the-median-home-value-in-the-chicago-metro-be-between-340000-and-345000-on-september-30-20260630182304849`.
At 02:42 UTC, YES/NO metadata .285/.715, liquidity ~$639, vol24 ~$407,
structured fee rate .05 / exponent 1; open and no UMA proposal. No books walked
and these marks are not executable entry prices.

Despite the median-home-value headline, the literal measurement is Chicago
Metro all-property-type **Parcl_ID 2899845 Sales Price Index × 1,500 sqft** on
Sep-30. It is not Zillow, Case-Shiller, a generic regional median transaction
price, or Chicago's year-over-year percentage change. Boundaries go to the
higher bracket: algebraically the $340k–$345k range maps to PPSF
**[226.666666…, 230)** before any source rounding, which remains unverified.
The rules say Sep-30 data are expected that day, but explicitly allow publication
through **Oct-10 23:59 ET**; only absence of that dated observation by the latter
deadline invokes the most-recently-published-data fallback.

[Parcl's dataset page](https://www.parcllabs.com/datasets/sale-price-index)
describes a daily USD/sqft series. Direct HTTP visible HTML also explicitly
labels it pricefeed v3; that sentence was absent from the web reader's extracted
page, so search-snippet-only evidence was independently checked. The generic
[API data overview](https://docs.parcllabs.com/data_overview.html) says preceding-
day daily observations are available each afternoon. That is not a guaranteed
publication timestamp for this contract, but it does not support the suspected
monthly-release mismatch. Monthly revisions are explicitly documented; daily
historical finality and any first-versus-revised print settlement policy remain
unverified. The older [price-feed whitepaper](https://www.parcllabs.com/articles/parcl-labs-price-feed-whitepaper)
describes filtered moving medians, dynamic windows, timely-data blending and
seven-day smoothing, not same-day closed-sale sampling. Do not assume every
legacy methodological detail carries unchanged into the current feed.

The named [resolution page /54](https://www.parcllabs.com/prediction-market-resolutions/54)
redirects app→www and returns HTTP 200 with visible **Market not found** here.
The live [official directory](https://www.parcllabs.com/prediction-market-resolutions)
still lists Chicago Sep-30 and links to /54: no replacement URL found. Its
resolved Chicago June-30 control /46 also returns Market not found. This is an
observed detail-page retrieval limit, not proof the entire source is unavailable
or grounds to activate the October fallback now. No exact current Chicago PPSF
level or dated history was recovered. The homepage's YoY growth cannot supply it.

**Pass pending actual measurement, not an opportunity recommendation.** No
numerical prior, calendar arbitrage, or robust entry edge was established. Reopen
only with the exact dated series and publication/revision evidence; no paid
access, new browser infrastructure, account setup or repeated polling for this
unmeasured optional lead. No orders, trades, priors or portfolio state changed.

## 03:39–03:42 UTC follow-up — Sweden S vote-share bracket

**Pass: no robust probability edge established.** This is the previously surfaced
candidate, not a newly discovered listing. Delegated bounded primary-poll lookup;
main independently checked source passages, the full contract and exact books.
Quota refreshed to 84% main headroom before the discretionary work.

[Gamma market 3562236](https://gamma-api.polymarket.com/markets/3562236) asks whether
the Swedish Social Democratic Party (S) receives 27–30% of valid parliamentary
votes on Sep-13. Exact boundaries go to the higher bracket: **[27%,30%)**.
The denominator is all valid election votes, not bloc support, seats, turnout,
or all survey respondents. Only votes attributed to S count, apart from the
specified formal-successor exception. Credible-reporting consensus is primary;
ambiguity falls back to Valmyndigheten. If results are not definitive by Dec-31
23:59 ET, the lowest bracket wins. The Sep-13 00:00 UTC Gamma endDate is not
poll closing time or a promised settlement timestamp.

The [Election Authority's press information](https://www.val.se/servicelankar/servicelankar/pressrum)
says polls close Sep-13 at 20:00 local (18:00 UTC); initial counting is preliminary,
and final parliamentary results are expected about a week later. Preliminary
reporting covers report parties, whereas final results include all participating
parties. Do not mechanically use a partial report-party denominator as all valid
votes, or promise cash availability on election night. This does not impose a
new final-certification requirement on an otherwise unambiguous market consensus.

| Primary poll | S share | Fieldwork | Sample |
| --- | ---: | --- | ---: |
| [Novus, Sep-7](https://novus.se/valjarbarometer-arkiv/l-over-4-okar-sakerstallt-s-och-m-bryter-nedatgaende-trenden/) | 27.0% | Sep-1–5 | 2,888 |
| [Verian/SVT, Sep-3](https://www.veriangroup.com/sv/news-and-insights/valjarbarometer-september-2026) | 29.2% | Aug-20–Sep-2 | 3,069 |

Both sample eligible/adult Swedish voters and weight their results; Novus uses
primarily Kivra/SMS plus telephone for the oldest group, Verian online/telephone.
The accessible pages did not give an S-specific numerical uncertainty interval.
Their reported undecided/non-party shares also differ (Novus 1%, Verian 12.5%),
so these are not interchangeable raw random draws from final valid ballots.
Novus reports a 1.2pp increase from its prior wave: neither that movement nor
the cross-pollster difference can be projected mechanically to election day.

At **03:40:51 UTC**, both exact-token books passed identity, schema and the
existing freshness gate; their shared book timestamp was 1788838850276, received
at ages 1.59s/1.63s. Sequential reads are not a fill guarantee. Gamma's structured
fee is .04, exponent 1; minimum size is five shares.

| Side | Best ask / available shares | Five-share fee-inclusive cost | Per-share cost | Raw p needed after 10pp stress |
| --- | ---: | ---: | ---: | ---: |
| YES | .58 / 300 | $2.948720 | .589744 | >.689744 |
| NO | .43 / 398.43 | $2.199020 | .439804 | >.539804 |

Condition `0x35e937709794b25202be03105093aef831d7532d3252bfa11a6f51da10a395df`;
YES token `99651778517916963441459208598519583860483475242015325647224805941293647284639`;
NO token `24202442957019196017081698246499895180158615177287509625999858273864320023142`.

Novus's point estimate sits exactly on the lower boundary; Verian's is inside
but only 0.8pp below the upper boundary. Neither a poll's location in the band
nor an average of the polls supplies a calibrated band probability. Sampling
error alone omits common polling error, turnout, late movement and method
differences. No evidenced error model was obtained that supports either required
probability robustly. This is a limit of this bounded underwriting, not proof
the market is efficient or that no forecasting model could work.

Both minimum taker costs also exceed the last measured idle pUSD ($2.115500 at
02:01 UTC; not remeasured here). Reserve funding is not justified by the evidence.
This is not a claim that a maker quote cannot fit the cash balance: a passive
quote has different economics and future-information risk, and no maker edge
was underwritten. No entry gate, order, transfer, prior change, scanner or new
scheduled reminder. Reopen only with materially better forecast evidence or
relevant election results, not repeated minute-by-minute poll reads.

## 03:56–03:59 UTC — basket quote-failure follow-up

The scheduled 03:54:49 consistency report inspected 5,000 open markets and
requested 20 structural groups: eight quoted nonpositive, 12 quote-failed,
with another 200 structural groups unquoted. No positive live-depth observation;
coverage remains incomplete. A worker checked the recorded failure reasons and
scanner code while main made two narrow public-market/book reads, not a full scan.

The **first reported** failures were eight missing asks and four book-age
rejections (Beijing 1211.3s, Tel Aviv 318.1s, Florida Senate turnout 322.7s,
Warsaw 366.5s). This does not establish that later legs would pass, or that
unquoted groups have no edge. The live time budget was not exhausted.

- Jinan event 980687, [market 4320176](https://gamma-api.polymarket.com/markets/4320176),
  lowest temperature ≤12°C NO: at **03:57:32 UTC**, exact asset/condition matched,
  timestamp 1788839840229 (~12s old), **asks empty**. All 11 event members have
  identical description hashes. Several other legs have very wide YES metadata
  spreads; their mids are not entry prices. No complete or subset basket edge
  was established by this check.
- Beijing event 973885, [market 4274564](https://gamma-api.polymarket.com/markets/4274564),
  lowest temperature ≤12°C NO: at **03:58:20 UTC**, exact asset/condition matched,
  still open/accepting, timestamp 1788838451252 (**1449.5s old**) and **asks empty**.
  The existing freshness guard rejected it. An old book timestamp does not by
  itself prove a stale HTTP cache; do not bypass the guard or invent missing asks.

The two complete-basket entry paths remain unvalidated. No relaxed safeguards,
repeat full scan, new polling task, trade, order or funding action. Existing
scheduled scans may observe naturally changed liquidity; no further immediate
retry is justified by these unchanged blockers.
