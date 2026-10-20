# Polymarket consistency scan — 20261020T104732Z UTC

Coverage: **INCOMPLETE analysis (market_cap; 190 structural groups unquoted; 16 structural groups quote-failed)**. This is a volume-ranked ROI slice unless the keyset cursor was exhausted.

- filters: `{"closed": false, "end_date_max": "2027-01-05T23:59:59Z", "end_date_min": "2026-10-20T10:46:44Z", "exclude_tag_id": ["1"], "liquidity_min": null}`
- live quote selection: `balanced`; requested priority/exploration groups: {'priority': 9, 'exploration': 11}; legs: {'priority': 94, 'exploration': 99}; attempted groups/legs: 20/193; prior exact-history records: 177
- 32 pages / 36.3 MiB streamed; projected peak memory 68.5 MiB
- cursor_exhausted=false, stop_reason=market_cap, invalid_neg_risk_events=0

> **Coverage is incomplete. A zero below means no hit in the scanned slice; it is not a comprehensive exchange-wide zero.**

Universe slice: 5001 open markets scanned, 3165 validated neg-risk markets retained, 360 neg-risk groups, 292 midpoint-violations > 0.5%.

- **0 PROVISIONAL positive structural baskets (sequential CLOB depth; revalidation required)**
- 210 sum>1 (midpoint), 82 sum<1 (midpoint, directional)

> WARNING: gamma-api `outcomePrices` shows midpoints between stale stub bids (often $0.01) and real asks. Most midpoint-only "free arb" signals evaporate when orderbook asks are checked. Positive live-depth observations below are sequential and non-atomic: independently refresh every leg before any decision; this report is not an execution instruction.

## PROVISIONAL structural baskets (revalidation required)

Computed by walking CLOB asks for buy-all-NO of every member at one common size no smaller than any validated leg minimum. Reported economics are per basket unit; snapshots are sequential, not atomic. Profit assumes exactly one YES wins.

No positive provisional candidate in the scanned slice. Analysis is incomplete, so this is not a comprehensive zero.

## Midpoint-only sum>1 candidates (likely stale orderbooks)

Sorted by midpoint net edge. These are NOT executable; included for diagnostic only.

| Mid Edge | Live Edge | YES-sum | Members | Liquidity | Title |
|---:|---:|---:|---:|---:|---|
| +39.43% | no asks for market 5852924 | 2.4775 | 6 | $562 | What will the biggest earthquake be on October 20, 2026? |
| +23.18% | book validation failed for 5853668: CLOB book is stale (986.0s) | 2.9570 | 11 | $3,880 | Lowest temperature in Taipei on October 20? |
| +17.96% | book validation failed for 5913665: CLOB book is stale (2960.1s) | 2.6200 | 11 | $947 | Lowest temperature in Istanbul on October 21? |
| +17.74% | no asks for market 5853872 | 2.5700 | 11 | $1,277 | Lowest temperature in Shenzhen on October 20? |
| +17.25% | book validation failed for 5854030: CLOB book is stale (3211.2s) | 2.5405 | 11 | $1,194 | Lowest temperature in Jeddah on October 20? |
| +15.40% | book validation failed for 5853799: CLOB book is stale (2302.9s) | 2.3980 | 11 | $404 | Lowest temperature in Wuhan on October 20? |
| +15.28% | book validation failed for 5853997: CLOB book is stale (1435.6s) | 2.3890 | 11 | $522 | Lowest temperature in Busan on October 20? |
| +10.85% | book validation failed for 5853987: CLOB book is stale (685.5s) | 2.0600 | 11 | $1,286 | Lowest temperature in Istanbul on October 20? |
| +6.26% | no asks for market 5853532 | 1.6115 | 11 | $1,504 | Lowest temperature in Wellington on October 20? |
| +5.08% | live leg cap | 1.7270 | 15 | $3,850 | Which company has the best Image Edit AI end of November? |
| +4.45% | live leg cap | 1.4455 | 11 | $1,363 | Lowest temperature in Karachi on October 20? |
| +4.27% | live leg cap | 1.6640 | 16 | $3,491 | Which company has the best Image-to-Video AI end of November |
| +3.66% | live leg cap | 1.3970 | 11 | $5,414 | Lowest temperature in London on October 20? |
| +2.57% | live leg cap | 1.3015 | 11 | $2,691 | Donald Trump # Truth Social posts October 23 - October 30, 2 |
| +2.51% | live leg cap | 1.2875 | 12 | $4,626 | #1 AI lab by OpenRouter market share week of October 19? |
| +2.02% | live leg cap | 1.1800 | 8 | $4,597 | Argentina Monthly Inflation - October |
| +1.78% | live group cap | 1.1020 | 5 | $38,335 | Israel Election: Yisrael Beiteinu vote share? |
| +1.65% | live leg cap | 1.2060 | 11 | $5,447 | Lowest temperature in Seoul (Incheon) on October 21? |
| +1.57% | live leg cap | 1.3075 | 18 | $4,543 | Golden Joystick Awards: Ultimate Game of the Year Winner |
| +1.26% | live leg cap | 1.1365 | 11 | $4,832 | Lowest temperature in Tokyo on October 20? |
| +1.11% | live leg cap | 1.1120 | 8 | $79,502 | TX-36 House Election Margin of Victory |
| +1.08% | live leg cap | 1.1475 | 11 | $6,163 | Lowest temperature in Tokyo on October 21? |
| +1.07% | live leg cap | 1.1435 | 10 | $4,893 | PPI YoY - October 2026 |
| +1.06% | live leg cap | 1.3670 | 30 | $142,119 | Elon Musk # tweets October 23 - October 30, 2026? |
| +1.04% | live group cap | 1.1070 | 7 | $7,286 | "Wildwood" Opening Weekend Box Office |
| +1.02% | live leg cap | 1.1270 | 10 | $2,327 | Zelenskyy # posts October 16 - October 23, 2026? |
| +0.99% | -3.98% | 1.0675 | 5 | $33,493 | Serbia Parliamentary Election: Turnout |
| +0.97% | live group cap | 1.0230 | 3 | $6,460 | When will the next Google Gemini Pro model be released? |
| +0.96% | live leg cap | 1.1220 | 10 | $78,818 | TX-30 House Election Margin of Victory |
| +0.94% | live leg cap | 1.1295 | 11 | $27,521 | Highest temperature in Miami on October 22? |

## Midpoint-only sum<1 candidates (directional, missing-mass risk)

| Mid Edge | YES-sum | Members | Liquidity | Title |
|---:|---:|---:|---:|---|
| +341.85% | 0.2190 | 6 | $56,662 | Who will Trump endorse for President of Brazil? |
| +22.23% | 0.7915 | 9 | $37,686 | NJ-03 House Election Margin of Victory |
| +14.10% | 0.8680 | 11 | $10,858 | Highest temperature in Chongqing on October 20? |
| +13.92% | 0.8505 | 9 | $116,376 | RI-02 House Election Margin of Victory |
| +13.87% | 0.8505 | 10 | $129,815 | TX-18 House Election Margin of Victory |
| +13.16% | 0.8610 | 5 | $3,950 | DICK'S Sporting Goods Q3 Dick's business comparable sales gr |
| +13.13% | 0.8555 | 9 | $73,716 | MI-02 House Election Margin of Victory |
| +12.11% | 0.8650 | 8 | $104,085 | NE-02 House Election Margin of Victory |
| +7.80% | 0.9100 | 12 | $3,062 | #2 AI lab by OpenRouter market share week of October 19? |
| +6.88% | 0.9140 | 7 | $2,621 | Alphabet’s Market Cap end of October 2026? |
| +6.84% | 0.9200 | 3 | $103,175 | Bitcoin vs. Gold vs. S&P 500 in 2026 |
| +5.13% | 0.9255 | 7 | $5,636 | Elon Musk Net Worth on October 31? |
| +4.77% | 0.9545 | 22 | $557,912 | Next leader out of power before 2027? |
| +3.86% | 0.9345 | 8 | $119,513 | Alaska Senate Election: Turnout (First Round) |
| +3.50% | 0.9510 | 16 | $2,202,752 | Venezuela leader end of 2026? |
