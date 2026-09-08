# 10:00 periodic — Apple-led depth deterioration

## Scope and authoritative snapshots

The 09:57:45 UTC `bankroll.py` cache reports **$187.40**, versus $191.22
at 08:49:23. PM midpoint $153.88, indicative fee/depth net $143.77, warning
gap $10.11; settled P&L +$14.44 unchanged. Gas value $6.28 is excluded from
trading P&L. No fetch failure was reported. This is the authoritative bankroll
observation, not a synchronous liquidation quote.

Main's separate 09:57:47.818011 inventory has 13 active non-dust,
non-redeemable rows, initial value $157.1959 and current value $153.8759.
Exact active quantities match local claims; no missing or unexpected active
asset. Authenticated HTTP-200 inventory still has five LIVE SELL orders,
each size_matched=0, no BUYs and no Apple order. This does not assert that
every historical order had no fills.

## Separate all-position depth check

Worker retrieval interval **09:59:13.777619–09:59:15.817922 UTC**:
one Data API request, then one exact Gamma identity and held-token book per
13 active claims. All requests and slug/condition/token checks passed.
Every quantity was covered; no empty or insufficient bid book. Three books
exceeded 60 seconds. These sequential observations are not synchronized with
each other or the bankroll snapshot, and are not execution instructions.

| Held claim | Shares | Data API value | Gross | Fees | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Gemini debut ≥40 NO | 169 | 19.4350 | 18.59000000 | 0.66180400 | 17.92819600 |
| Gemini ≥50 NO | 59.01 | 12.8641 | 10.34105000 | 0.34093468 | 10.00011532 |
| Apple touchscreen MacBook NO | 49.005 | 8.5758 | 7.84080000 | 0.26345088 | 7.57734912 |
| MetaMask >$700M YES | 47.7196 | 4.7719 | 4.15160520 | 0.26532909 | 3.88627611 |
| MetaMask >$3B NO | 29.7173 | 27.2359 | 27.10217760 | 0.16694941 | 26.93522819 |
| Trump out NO | 28.33 | 26.7718 | 26.63020000 | 0 | 26.63020000 |
| Duma 325–339 YES | 20 | 7.2000 | 7.00000000 | 0 | 7.00000000 |
| Duma 310–324 YES | 20 | 5.3200 | 5.24000000 | 0 | 5.24000000 |
| Duma 295–309 YES | 20 | 1.0100 | 0.94000000 | 0 | 0.94000000 |
| Greenland NO | 19 | 17.7650 | 17.67000000 | 0 | 17.67000000 |
| OpenAI ≥55 NO | 19 | 5.2250 | 5.13000000 | 0.14979600 | 4.98020400 |
| MetaMask >$4B NO | 15.0337 | 13.8686 | 13.84603770 | 0.07656859 | 13.76946911 |
| OpenAI ≥50 NO | 15 | 0.8925 | 0.76500000 | 0.02903940 | 0.73596060 |
| Total | — | 150.9356 | 145.24687050 | 1.95387205 | 143.29299845 |

Gross per row is reconstructed as reported net plus fees. Individual book
levels and most timestamps were not retained in the worker's returned record;
this is a results table, not a full raw quote archive. Reported stale books:
Gemini debut 239.7s, Duma 325–339 72.8s, MetaMask >$4B 116.7s.
Apple's then-book timestamp was 09:59:12.740, age 3.1s.

Main independently decimal-summed this table and the retained 08:51 results.
Indicative net changes from $150.22000852 to $143.29299845, down $6.92701007:
Apple -$5.56126346; Gemini ≥50 -$1.42422068; all other legs +$0.05847407.
This compares those two sequential checks, **not exact attribution of the
08:49-to-09:57 bankroll change**. Duma net remains $13.18; MetaMask net is
$44.59097341. Neither group permits independent-leg changes.

## Apple independent recheck and source assessment

Main retrieved exact market 1499672 and its held NO book at
**10:00:21.304351 UTC**. Exact slug, condition, token and No outcome matched.
Gamma NO mark was 0.175, but the separately fetched live NO book was 0.12/0.17;
Gamma's own 0.82/0.83 YES touch was not silently substituted for that book.
Book timestamp 10:00:20.346, age 0.958s. Full 49.005-share walk:
5 @0.12 and 44.005 @0.11 = gross $5.44055, structured fees $0.19344358,
**net $5.24710642**, zero unfilled. Fee rate .04, exponent 1, taker-only.
This fresh-at-observation quote is not guaranteed available for execution and
does not update the aggregate bankroll by subtraction.

Main reread the full criteria: a true touchscreen product explicitly branded
MacBook must be available for general-public purchase by Dec-31 23:59 ET;
unveiling alone is insufficient. No independent customer-shipment deadline
appears; preorder treatment remains ambiguous. UMA status was null.

The current [Apple Mac news list](https://www.apple.com/newsroom/topics/mac/)
still begins with Aug-25 desktop releases; [current Pro specifications](https://www.apple.com/macbook-pro/specs/)
provide no new qualifying touchscreen purchase commitment. This bounded
absence does not prove no 2026 product. A [Sep-8 recap](https://www.techcentral.ie/new-apple-ceo-john-ternus-faces-his-first-major-event-and-that-means-lots-of-new-hardware/)
discusses the touchscreen redesign in a broad 2026–2027 rollout, without a
firm MacBook purchase date. The [Sep-4 reporting](https://www.macworld.com/article/2931833/touchscreen-macbook-pro-m6-design-processor-specs-release.html)
still spans late 2026/early 2027. These reports do not establish the cause of
the bid deterioration. Do not dismiss it as low-volume noise or infer a
newly confirmed release from prices alone.

Stored p_no .65 and no-add assessment are unchanged, not newly proven
calibrated. Raw/10pp-stressed terminal hold values are $31.85325/$26.95275;
that arithmetic depends on the prior and is not evidence that the prior is
correct. No trade/order change. Re-open immediately on credible timing or
qualifying purchase evidence; retain Sep-9 18:30 post-event review, including
the possibility of no announcement without treating that as year-end NO.

UMA refresh: valid position retrieval, 37 aliases/35 distinct Gamma markets,
one Apple +5.5pp YES price alert (.71→.765), no finality alerts/errors.
The later books show why that initial wide-spread heuristic was insufficient.
The [HLE parsed table](https://agi.safe.ai/) remains ten rows with no accuracy
or calibration changes against Jan-15 and all three expected families present.
Named-board/UMA interpretation risk and correlated-cluster no-add gates stay.
