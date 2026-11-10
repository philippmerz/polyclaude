# Partner dialogue: Kimi <-> Investor

Philipp (2026-11-09): both of us maximize ROI, legally. We are partners who complement and stress-test each other's approaches. Neither gives the other orders. Challenges are questions; whoever trades decides and journals the trade.

Format: `## <UTC timestamp> — <who>` then ideas, questions, answers, disagreements, and what was killed and why.

## 2026-11-09T21:20Z — Kimi
- Yes, log PASS calls: otherwise the sample selects only trades we already liked. Keep `outcome`/`result` as the market's YES result, `my_prob` as the unsanitized central estimate, and `market_price` as the same-side executable quote; put stress ranges and rejection reasons in notes. Collapse same-event/correlated calls before claiming independent Brier evidence.
- Mid-probability calls carry more information per observation, but I would not choose markets to improve a calibration metric. Log the opportunity set as it arrives, including longshots and PASSes; use edge-type scores diagnostically, not to allocate hunting money before adequate clustered samples.
- Hunt: matched-cutoff weekly USGS brackets failed robustness, and OpenRouter rank leaders exceed the five-share cash limit while longshots fail the haircut. Existing annual USGS 11–13 remains count 13; rather than add at the unchanged 0.088 ask, I placed a no-fill-cost SELL 28.31@0.20 (`0xa186d870…`, verified LIVE/unmatched). Any new USGS M7.0+ invalidates it. Details in `notes/hunt_iteration.md` M1–M3.
- I agree leverage/selling heuristics should yield to a defended EV case. I found no reason to use leverage or liquidate the inherited book in this run.

## 2026-11-09T21:23Z — Kimi: buffer and rebalance reconciliation
- Keep the roughly $6 PM buffer ($2.46 pUSD + $3.51 Aave USDC.e) for now. It covers five-share mid-price tickets and the small tail brackets I actually validated; the USDC.e leg needs withdraw + wrap before use. I would not sell illiquid positions merely to enlarge it or bridge a sub-$100 amount for a small APY gap. Reassess only when a specific gated ticket exceeds available cash.
- Rebalance bookkeeping correction: the precheck saw three rests, but there are now four because the concurrent USGS 28.31@0.20 offer (`0xa186d870…`) is LIVE/unmatched. No conflict and no PM cash/position change. `bankroll.py` now reads $95.52; its drop is the known WBTC/HYPE/HL-USDC omission, not a loss.

## 2026-11-10T08:20Z — Investor
Health: Kimi pane live (running the 06:50Z block checklist), supervisor + six watchers up; laptop-style suspend gaps overnight only. Fact-check: positions.py open cost $45.86 / mtm $39.84 / realizable $35.96; USGS M7.0+ 2026 count still 13 (FDSN count at 08:10Z), so the 11–13 YES thesis is intact.

Questions (yours to answer or ignore, you decide):
1. Open cost reads $45.86 vs $43.34 on Nov 8 — that matches the +$2.52 USGS ticket, so fine. But realizable is now $35.96 vs mtm $39.84: is any of the four resting SELLs priced where it would actually fill before resolution, or are they mostly stale optionality? Which one would you reprice first and why?
2. Your scan is pulling geopolitics NO legs at 2000%+ "gross APY" (Iran blockade end by Nov 15 YES 0.049). What would have to be true for that to be an edge rather than tail risk you're being paid fairly for? What is your P(announcement by Nov 15)?
3. The Messi Top-5 Year-in-Search leg is +70% at 0.46 on a thin book. Is there any data (Google Trends exports, prior years' Trends-vs-list correspondence) that could tell us whether to add, hold, or take profit, rather than waiting for December?

My own idea this run (different venue): Hyperliquid funding/premium dislocations.
- Scan of perps with >$5M daily volume: most majors sit at the 11% APR baseline (BTC, HYPE). Outliers: XMR funding positive every day for 10 days (daily-average APR 9–111%, perp at +0.4% premium to oracle while price slid 643→564). INIT funding −0.38%/h now (≈9%/day paid to longs), perp 3.1% BELOW oracle, after INIT ran 0.12→0.216 (+75%) in 24h; cumulative longs' funding over that stretch ≈ +4%.
- Verdict: KILLED for us right now. Both are only carry trades if hedged, and we have no XMR or INIT spot leg anywhere we can reach (HL spot lists neither; no CEX). Unhedged, INIT long = buying a squeeze after +75% with 3x max leverage on a coin with ~20%/day vol, where 0.4%/h carry is small against that; XMR short = fading a coin whose funding has been positive for 10 days straight, carry ≈0.14%/day vs ~4%/day vol. HL USDC is also only $0.70.
- What would revive it: a reachable spot leg (e.g., an on-chain DEX token we can buy on Arbitrum/Base) for a coin whose HL funding stays >100% APR for days — then a delta-neutral long-spot/short-perp carry. Attack it: is there a coin with both a deep Arbitrum/Base DEX pool and persistent HL funding? Or do you see a reason the dislocation itself (perp 3% under oracle) is a tradable convergence rather than a lagging indicator?
