# Frontier-model capital-allocation pilot: corrective autonomy review

This review records the portfolio, benchmark, research correction, live actions and
operating plan as of September 10, 2026. It is the current handover for the pilot's
mandate to maximize legal return through the start-of-2027 evaluation. The reference
capital remains **$170**: $70 contributed on April 25 and $100 on April 29. Separately
contributed gas tokens are excluded from trading performance.[1]

## Decision

The current portfolio should be **held without a new allocation today**. Every economic
position has greater central hold value than its observed complete net exit, while no
reviewed addition clears the combination of evidence quality, price, correlation and
ticket limits. This conclusion does not validate the subjective probabilities. Several
lower-bound cases are negative, and the three remaining Humanity's Last Exam (HLE)
contracts can lose together.

The most consequential finding is a research-instrument failure. The HLE monitor parsed
a stale ten-row table embedded in the server-rendered `agi.safe.ai` page. The chart named
by the contracts is populated in the browser from `dashboard.safe.ai/api/models`. Raw
archives of that API contain 44 rows on July 3 and 52 on August 4; the live API contains
58. It is actively maintained.[2][3] The live chart includes GPT-6 Astra at **53.6**,
Gemini 3.8 Flash at **46.2**, and Gemini 3.1 Pro at **45.9**. OpenAI ≥50 therefore had a
literal chart-based YES result. The former “frozen source” thesis is retired.

An initial review trusted the wrong table and sold the Gemini ≥50 and OpenAI ≥55 NO
positions. Once the real data path was proved, both positions still had positive expected
value under conservative revised probabilities, so they were repurchased. The round trip
cost approximately **$2.44 in spread and fees** and restored 0.286595 fewer Gemini claims.
The error is included in performance and recorded here rather than absorbed into a later
mark.

## Performance against passive funds

The current whole-account marked bankroll is **$183.20**, of which **$6.09** is separately
contributed gas. The PM sleeve marks at $152.31 but has an indicative complete depth and
fee value of $146.72. Replacing the midpoint with that value produces approximately
**$177.61 including gas**, or **$171.52 of trading value excluding gas**. Against $170,
that is about **+$1.52 / +0.9%** before VM or other off-wallet costs. Reads are sequential,
stablecoins and aTokens are valued at par, and the depth result is not a synchronized or
guaranteed executable quote.[4]

The passive comparison is now fixed in a machine-readable policy rather than reconstructed
from memory. Each contribution enters at the first completed US trading session strictly
after its ledger date. That places the $70 lot on April 27 and the $100 lot on April 30;
the latter is deliberately conservative because the April 29 contribution arrived only
about five minutes before the close. Raw closes identify initial fractional shares, while
adjusted-close ratios model distributions and splits. The September 10 session was still
open at retrieval, so valuation uses the completed September 9 close.[5][18]

| Comparator | Value | Return on $170 | Lead over pilot liquidation |
|---|---:|---:|---:|
| Pilot, PM midpoint basis, gas excluded | $177.11 | +4.18% | — |
| **Pilot, depth/fee basis, gas excluded** | **$171.52** | **+0.89%** | — |
| Vanguard Total World Stock ETF (VT) | $180.85 | +6.39% | $9.33 |
| Vanguard Total Stock Market ETF (VTI) | $181.13 | +6.55% | $9.61 |
| State Street SPDR S&P 500 ETF Trust (SPY) | $181.17 | +6.57% | $9.65 |

The economically relevant result is the depth/fee row. On that basis, the pilot trails
the passive funds by roughly **5.5–5.7 percentage points**. Even its more flattering PM
midpoint basis trails them by $3.74–$4.06. The benchmark favors passive investing by
assuming ideal fractional shares, zero commissions, spread, slippage and tax, and no yield
on cash awaiting entry. It relies on one public Yahoo price series whose adjustments can
be revised. Those assumptions are explicit and stable across future runs.[5][18][19][20]

## Transaction audit and recovery

The sell/rebuy sequence was an avoidable research loss, not a portfolio thesis change.

| Step | Action | Exchange result | Settlement evidence |
|---|---|---|---|
| 1 | Cancel Gemini ≥50 NO sell | 59-share maker sell removed | No matched quantity |
| 2 | Sell 59.01 Gemini ≥50 NO | raw .169; $10.02664 gross; about $9.69372 net | order `0x4f0dcb…fb34`; Polygon transaction `0xeb63d8…21a0d` |
| 3 | Cancel OpenAI ≥55 NO sell | 19-share maker sell removed | No matched quantity |
| 4 | Sell 19 OpenAI ≥55 NO | raw .13; $2.47 gross; about $2.384044 net | order `0x7d722e…ef3c`; Polygon transaction `0x51e745…c9763` |
| 5 | Rebuy Gemini ≥50 NO | 58.723405 shares; $11.02 exchange notional | order `0x879a8c…28b9`; Polygon transaction `0x633081…e344` |
| 6 | Fund minimum OpenAI repair | withdraw and wrap $0.50 from Polygon Aave | transactions `0xbef616…bfbe` and `0x2dcb02…3b14` |
| 7 | Rebuy OpenAI ≥55 NO | 19 shares; $3.04 exchange notional | order `0xa3b7e3…91f3`; Polygon transaction `0x226e05…071` |

Wallet debits for the two buys were approximately $11.37809 and $3.14214 including the
fee effect, versus approximately $12.077764 total net sale proceeds. That implies the
reported **$2.44** round-trip cost. The $0.50 Aave withdrawal was an internal collateral
move, not an expense or external contribution. About 0.106 POL of separately contributed
gas was also used during the recovery and remains outside trading-return accounting.[21]

The Gemini entry helper initially returned an ambiguous status because price improvement
delivered more shares than its conservative cash-sized target. The exchange and indexed
position both proved the fill. The helper now permits BUY overfill only for ordinary
cash-capped entries; equal-leg bundles and sells retain exact-quantity reconciliation.
This removes a false failure without weakening cash or structure limits.

## Correct HLE source and contract interpretation

The chart API and the static table are separate products. A July 15 archived page bundle
loads the API for the “AI Progress on Humanity's Last Exam” chart, while raw API archives
show the row inventory changing during 2026. The monitor's table parser was internally
correct but attached to the wrong endpoint. Parser liveness, known-name coverage and
score-change tests could not establish endpoint identity.

OpenAI's own Astra release reports **57.2 HLE with tools**, while the resolving chart
currently reports **53.6**.[6] Google's Gemini 3.1 Pro model card reports **44.4 without
tools** and **51.4 with Search and Code**, while the chart displays 45.9.[7] These are
useful capability and future-update signals, but the chart's current numeric rows govern
the literal source branch. Benchmark configuration must remain attached to every quoted
score.

| Contract held | Current chart fact | Central probability of held NO | Range | Current decision |
|---|---|---:|---:|---|
| Next Gemini Pro debut ≥40 | Existing Gemini 3.1 Pro 45.9 predates the Jul-29 market; a later qualifying Pro row is likely | .20 | .08–.35 | Hold; no add; first HLE trim candidate |
| Highest Gemini score ≥50 | Current Gemini maximum 46.2 | .35 | .20–.55 | Hold 58.723405 NO; no add |
| Highest OpenAI score ≥55 | Astra is 53.6, only 1.4 points below the bar | .30 | .12–.50 | Hold 19 NO; no add |

The debut estimate decomposes to about an 82% chance that another qualifying Gemini Pro
row appears by year-end and a 97% chance it reaches 40 conditional on appearing. This is
subjective. The July 3 archive already contains Gemini 3.1 Pro at 45.9, so that model
cannot be the “next” newly added Pro row. The Google Pro subset stayed unchanged across
July 3, August 4 and September 10 even though the complete chart grew 44→52→58. The correct
claim is therefore “no new Google Pro row yet,” not “the source is frozen.”[2][3][10]

Gemini ≥50 NO has the strongest current exit comparison. Even its .20 lower estimate
implies $11.74 of resolution value for 58.723405 claims, above the approximately $9.59
observed complete net exit. OpenAI ≥55 is weaker: 53.6 is close to the threshold and the
chart has added successive OpenAI results. An independent review estimated .25 NO versus
the stored .30; both support keeping this small ticket, while neither supports adding.
[8][9]

The 169-share debut leg is large relative to its revised edge. A simple illustrative
joint-state stress using `P(debut NO)=.20`, `P(Gemini ≥50 NO)=.35` and 85% overlap found
that selling about 34 shares at the observed bid improved certainty-equivalent wealth by
only about $0.19. At .15 the model favored a much larger trim; at .25 it favored none.
That sensitivity exceeds the precision of the inputs. There is no compelled taker sale
today. A **fresh executable debut-NO bid of at least .18 with meaningful depth** is the
next trim-review trigger, and the chart plus release state must be checked before acting.

## Other positions

| Economic position | Quantity | Indicative complete net exit | Central hold value | Decision |
|---|---:|---:|---:|---|
| Touchscreen MacBook 2026 NO | 49.005 | $17.78 | $26.95 at .55 | Hold; no add |
| Trump out before 2027 NO | 28.33 | $26.63 | $27.48 at .97 | Hold; retain .97 premium sell |
| US acquires part of Greenland NO | 19 | $17.67 | $18.05 at .95 | Hold; retain .98 premium sell |
| Duma 295–339 YES union | 20 equal shares in three buckets | $11.42–$11.51 | $14.40 at .72 | Hold complete set; no add |
| MetaMask FDV structure | Exact configured quantities | $43.32 | about $46.16–$46.80; $44.751 rule floor | Hold complete structure; no add |

Apple's September 9 event omitted a MacBook, but this is weak NO evidence. Same-day
reporting quotes Mark Gurman saying that a missing touch MacBook at that event would not
rule out 2026 because it was only September. The article's claim that products are coming
later in the year is editorial inference rather than a dated on-sale promise. A separate
September 4 roundup still says early 2027 is more likely while preserving a fall-planning
branch.[15][16][17] The exact contract requires a touchscreen product explicitly branded
MacBook to become available for public purchase by December 31; an unveiling alone is
insufficient. The revised **.55 NO** estimate has a wide .35–.70 range. The full net exit
near $17.78 implies roughly .363 per claim, so the central estimate supports holding.

The Duma review found a new September 10 APEK forecast: United Russia at 49–52% of list
votes and 185–195 district wins.[11] Russia elects 225 members from party lists and 225
from single-member districts, with a 5% list threshold.[12] Correctly normalizing list
votes among qualifying parties puts the APEK midpoint near 318 seats if Just Russia
qualifies and 326 if it does not. Wider RASO and turnout uncertainty produce the working
distribution: below 295 **13%**, 295–309 **15%**, 310–324 **32%**, 325–339 **25%**, above
339 **15%**. The held union is therefore .72. Its expected $14.40 payout exceeds the
complete exit, but a five-share addition recently cost about .615 per covered payout
dollar. Both the ≥.75 evidence gate and ≤.57 price ceiling fail. The three legs must remain
equal and be managed as one structure.[11][12][13][14]

MetaMask remains the strongest position supported by payoff structure. Its configured
pairing has a $44.751 payout floor before settlement and protocol risk, above the observed
$43.32 exit. The direct December launch market moved from the stored .115 midpoint to an
indicative .08, reducing central group fair to about $46.16 if conditional FDV estimates
are unchanged. New paired units cost more than their $1 floor and would be directional
yield trades. Hold the existing exact structure and make no addition.

## Portfolio risk and capital use

The PM inventory has 12 unresolved rows, $147.12 data-API cost, $152.24–$152.31 midpoint
value and about $146.72 complete net depth value. Reserves include approximately $15.62
Polygon Aave USDC.e, $7.87 Arbitrum Aave USDC, $1.05 Base USDC, $0.17 pUSD and $0.10
Polygon USDC, plus gas excluded from the trading comparison. The current Polygon Aave
hurdle is **2.8764%**.

Fee-inclusive cost exposure in Apple plus the three live HLE contracts is about $53,
close to the 30% shared-factor cap of roughly $55 at current bankroll. Apple is less
fundamentally correlated with model benchmark progress, but its price can move on the
same technology-release information cycle. There is no capacity for another HLE/Apple
ticket without a whole-cluster review. Apparent single-leg Kelly output must not create
room that the aggregate entry gate forbids.

Current full-size exit comparisons show no central negative edge:

- Gemini debut: hold $33.80 at .20 versus about $17.93 exit.
- Gemini ≥50: hold $20.55 at .35 versus about $9.59 exit.
- OpenAI ≥55: hold $5.70 at .30 versus about $2.38 exit.
- Apple: hold $26.95 at .55 versus about $17.78 exit.
- Trump and Greenland: small remaining edges, with premium maker exits already resting.
- Duma and MetaMask: group hold values and structural floors exceed complete exits.

These comparisons use subjective central probabilities. Lower estimates can make debut,
OpenAI ≥55, Apple and Duma negative. That is why the action is hold/no add rather than a
claim of large safe alpha.

## Repository and control repair

The inherited working tree contained broad rewrites that weakened history, renamed safety
concepts and obscured the portfolio's actual state. A recoverable local backup was created
at branch `backup/pre-cleanup-20260910-1834`, pointing to stash commit
`2afdcce2c13ba57dac27596c7f17370965171915`, before restoring the last reviewed HEAD.
Current mandate, handover and live-state changes were preserved. This avoids treating
unreviewed doctrine edits as authority while keeping every byte recoverable.

Four permanent controls were added:

1. `source_freeze_check.py` follows the HLE chart API, applies one strict parser to live
   and raw archived payloads, fails closed on malformed identities/scores, and supports a
   brief status mode. The full status report runs it against the July 3 pre-market archive.
2. `polyclaude_enter.py` accepts beneficial share overfill only for an ordinary cash-capped
   BUY. Exact bundles and sells remain exact. This matches how price improvement works
   without expanding maximum cash loss.
3. `index_benchmark.py` fixes the contribution schedule, fund set, entry rule, adjustment
   method and January 1 evaluation behavior in a reviewed policy. It rejects in-progress,
   stale, malformed, future or symbol-mismatched price data.
4. `portfolio_kelly.py` now aggregates live fee-inclusive cost by ticket and correlation
   cluster, uses observed cluster exposure as the minimum correlation discount, and suppresses
   scale-in recommendations when they exceed either cap. The live report blocks a former
   $12.93 Trump suggestion because its $2.52 ticket headroom is insufficient. It also states
   $53.19 of `ai-ships-fast-short` exposure against a $54.96 cluster cap and blocks the former
   $10.88 OpenAI suggestion.

The status aggregator also retains bounded stderr diagnostics and surfaces negative-edge,
close-candidate and drawdown rows that its former summarizer could hide. The current HLE
source check is part of the ordinary full status path rather than a one-off research step.
Repository-wide verification passes **673 tests plus 156 money-math checks**. Focused live
checks reproduce the benchmark, the 44-to-58-row HLE update, both Kelly cap suppressions and
a clean 12-position state audit.

## Operating plan through evaluation

Existing event-driven monitors should handle waiting. Each trigger calls for one bounded
review and then stops.

1. **Every full status run:** compare the live HLE API with the July 3 raw archive. Any row
   addition, removal or score change is an underwriting trigger. Inspect the exact chart
   payload before relying on news summaries.
2. **HLE exits:** review the debut leg first if a fresh full-size NO bid reaches .18. Reprice
   all three contracts together after any Gemini Pro or OpenAI model row, score revision,
   criteria change or resolution proposal. Do not add while the factor cap binds.
3. **Apple:** re-underwrite on an official product page, preorder/purchase opening, October
   event announcement, or a sourced delay into 2027. No Apple resting order currently exists.
4. **Duma:** manage all three exact buckets together through election results. Exit the
   complete union if defensible probability falls below the refreshed complete net sale
   break-even; never trade one leg independently.
5. **MetaMask:** preserve exact paired identities and quantities. Reprice the whole payoff
   structure on a token-launch announcement or criteria change.
6. **Passive comparison:** run `scripts/index_benchmark.py --as-of YYYY-MM-DD` with every
   material performance report and at the January 1 evaluation. Lead with depth/fee trading
   value excluding gas; show midpoint only as a secondary mark.
7. **Cash:** leave reserves earning the current hurdle until a fully underwritten candidate
   clears fees, evidence, ticket and correlation gates. Repository pipeline triage found no
   superior executable entry today; that is a bounded result, not an exchange-wide claim.

No Fireworks usage or paid service was needed for this review.

## Limitations

Prediction probabilities are expert judgments, not calibrated distributions. HLE contracts
share source and release risk, Duma sources are forecasts rather than representative outcome
samples, Apple reporting is partly secondary, and thin CLOB books can move between read and
submission. The account aggregate is sequential and values stable balances at par. Full-depth
quotes do not guarantee synchronized liquidation. Passive fund returns use one public adjusted
price provider and ideal execution. The comparison excludes VM, research-service and tax costs
on both sides; including the pilot's real operating costs would worsen its relative result.

## Sources

1. [External-flow ledger](../notes/capital_ledger.md).
2. [Live HLE chart API](https://dashboard.safe.ai/api/models).
3. [Wayback raw July 3 HLE API archive](https://web.archive.org/web/20260703id_/https://dashboard.safe.ai/api/models).
4. [Bankroll calculator](../scripts/bankroll.py) and [position depth calculator](../scripts/positions.py), retrieved September 10 around 18:49 UTC.
5. [Benchmark policy](../notes/index_benchmark_policy.json) and [calculator](../scripts/index_benchmark.py), retrieved September 10 at 18:56 UTC.
6. [OpenAI, GPT-6 Astra release and evaluations](https://openai.com/index/gpt-6-astra/).
7. [Google DeepMind, Gemini 3.1 Pro model card](https://deepmind.google/models/model-cards/gemini-3-1-pro/).
8. [OpenAI ≥55 exact market criteria](https://gamma-api.polymarket.com/markets?slug=will-the-highest-score-achieved-by-an-openai-model-on-humanitys-last-exam-in-2026-be-55-or-higher-20260723225144064).
9. [Gemini ≥50 exact market criteria](https://gamma-api.polymarket.com/markets?slug=will-the-highest-score-achieved-by-a-google-gemini-model-on-humanitys-last-exam-in-2026-be-50-or-higher-20260723192605546).
10. [Next Gemini Pro ≥40 exact market criteria](https://gamma-api.polymarket.com/markets?slug=will-the-next-google-gemini-pro-model-debut-with-a-humanitys-last-exam-score-of-40-or-higher-20260729192434645).
11. [APEK, September 10 State Duma express forecast](https://regcomment.ru/reviews/rezultaty-vyborov-v-gosudarstvennuyu-dumu-ekspress-prognoz-apek/).
12. [State Duma, mixed electoral system and mandate allocation](https://duma.gov.ru/news/52271/).
13. [RASO political-technology committee forecast publication](https://t.me/s/Politteh/3217).
14. [VCIOM party-rating series](https://wciom.ru/ratings/reiting-politicheskikh-partii/).
15. [Touchscreen MacBook exact market criteria](https://gamma-api.polymarket.com/markets?slug=will-apple-release-a-touchscreen-macbook-in-2026).
16. [Macworld, September 9 Gurman timing report](https://www.macworld.com/article/3230458/touchscreen-macbook-homepad-apple-tv-are-coming-but-probably-not-today.html).
17. [Macworld, September 4 touchscreen MacBook timing review](https://www.macworld.com/article/2931833/touchscreen-macbook-pro-m6-design-processor-specs-release.html).
18. [Yahoo adjusted-close definition](https://help.yahoo.com/kb/SLN28256.html).
19. [Vanguard VT](https://investor.vanguard.com/investment-products/etfs/profile/vt) and [VTI](https://investor.vanguard.com/investment-products/etfs/profile/vti) fund pages.
20. [State Street SPY fund page](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy).
21. Polygon recovery transactions: [Gemini sale](https://polygonscan.com/tx/0xeb63d8a433978c060ee36660bd4c2a5c4ea82cf6089ecaff52f1f3953b821a0d), [OpenAI sale](https://polygonscan.com/tx/0x51e74513f6808412372385cfd3b41fd02cd1c5529b409a09f46fdf97479c9763), [Gemini rebuy](https://polygonscan.com/tx/0x633081e32bc587d70e6fb74ea63887ae1de2a9a494034470b43a33c48ce8e344), [Aave withdrawal](https://polygonscan.com/tx/0xbef6166b95c532f973cce9fc1828c99bba3b0d16f41e78ab1ab3b0a214a0bfbe), [wrap](https://polygonscan.com/tx/0x2dcb027d5bb8dd4956e8207862daae3712178300738783e31803767d90ac3b14), and [OpenAI rebuy](https://polygonscan.com/tx/0x226e051d2526c7f8194aea08099e171a5a91e622c7842ce8715b9bbe24938071).
