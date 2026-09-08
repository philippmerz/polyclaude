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
