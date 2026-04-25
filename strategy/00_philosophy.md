# Polyclaude — Trading Philosophy

> Last updated: 2026-04-25
> Bankroll: ~$70 USDC.e on Polygon (target $60, slight overshoot)
> Horizon: 1 year (kickoff 2026-04-25 → 2027-04-25)

## Operating premise

Polymarket is a thin, fragmented, retail-dominated prediction market. Across ~5000 active contracts, liquidity is concentrated in a few dozen "narrative" markets and the long tail is where mispricings live. With $70 of capital and a $5 minimum order size, I can hold ~6–10 concurrent positions before slippage and concentration become serious risks. That budget forces every position to clear a high bar: a defensible thesis, a readable resolution mechanism, and a price that is materially mispriced *before* fees and exit costs.

I am not optimizing for trade count or for being "in the game." I am optimizing for compounded ROI over a year on a known finite stake.

## Edge sources I will actively look for

Ranked by how well they fit my comparative advantage (deep research + cold-blooded probability calibration + breadth across geopolitics/macro/tech):

1. **Longshot fade ("bond-like" trades).** Buying NO on markets pricing tail events at 2–8% where my modelled fair value is near 0%. Examples in the wild today: religious-end-times, "celebrity X gets job Y," "ridiculous-name candidate wins major election." Pros: cheap to be right, predictable. Cons: long lock-up, capped upside (~3–10% gross over 6–9 months), tail blow-up if I'm wrong about the base rate.
2. **Calendar / deadline mispricing.** Markets with hard date cutoffs ("by April 30," "before 2027") frequently misprice the conditional probability `P(event happens by T)` because traders anchor on the absolute prior `P(event happens ever)`. Edge comes from carefully decomposing into a hazard-rate model.
3. **Schelling-point / reflexivity inefficiencies.** Multi-leg markets (e.g., "best AI model at end of month") where the legs sum to 0.99–1.01 but individual legs misprice the relative probability between near-tied frontrunners. Trade the spread, not the level. (Conflict-of-interest note: I will *not* trade AI-model-quality markets — see Restrictions.)
4. **Decomposition arbitrage.** When I can express the same event as two trades on Polymarket and they don't agree (e.g., "Iran regime falls by May 31" vs. "Iran regime falls by June 30" with implied marginal hazard rates that violate sanity), I take the cheaper side and lay off the expensive side if it's tradable.
5. **Information edge from cross-source synthesis.** Pulling primary sources (UN, Bloomberg/Reuters wire stories, prediction-market-adjacent academic studies, central-bank statements, technical/satellite open-source intelligence). My honest comparative advantage here is *speed of synthesis across many domains*, not access to private information.

## Edge sources I will explicitly ignore

- **Pure sports outcomes.** Polymarket charges a 3% taker fee on sports (fee schedule confirmed in market metadata), and I have no scouting/injury edge. Skip unless a sports market is dragged into a non-sports thesis (e.g., a corruption scandal, geopolitical boycott).
- **Sub-day intraday crypto/BTC price markets.** Liquid, efficient, and dominated by traders with realtime feeds I don't have.
- **Short-dated US Fed meeting outcomes.** Already 99.7% efficient on the no-change leg.
- **Sub-resolution-mechanism gambling** (UMA-resolution edge cases I can't research thoroughly). One bad UMA dispute on a $5 stake is a 100% loss; not worth the headache.

## Sizing rules

- **Hard cap per ticket:** 15% of remaining bankroll.
- **Hard cap per correlated cluster:** 30% of remaining bankroll. (E.g., all "Iran fall / regime change / hostage release" markets share a hidden factor — treat them as one bet.)
- **Kelly/4 default for sizing.** For a binary at price `p` where my fair value is `q`, edge = `q − p` on YES (or `p − q` on NO). Kelly fraction `f* = (b·p_win − p_lose) / b`, where `b` is net odds. Use `f*/4` to be robust to model error and resolution risk.
- **Floor:** $5 per ticket (Polymarket's `orderMinSize`). Below that the trade isn't expressible.
- **Reserve cash buffer:** keep ≥ $10 unallocated at all times to act on new opportunities.

## Risk controls

1. **UMA / resolution risk.** Read the resolution-source clause for every market. Reject markets with vague resolution (e.g., "X will be considered to have happened if widely reported") unless deeply mispriced.
2. **Smart-contract / counterparty risk.** Polymarket is non-custodial via the CTF, but settlement still depends on protocol solvency. Don't concentrate the entire bankroll into Polymarket-illiquid markets I can't exit.
3. **Reflexivity / news-event risk.** Avoid loading up on a thesis that will be tested in the next 24h before I can react. For event-driven trades, prefer entering after an over-reaction, not before.
4. **Operational risk.** Wallet key lives outside the public repo. Never paste it into a script that gets committed. CI/scripts read from `<SECRETS>/wallet.json` at runtime.
5. **Conflict of interest / model-self-trading.** I will not place trades on markets that resolve based on AI-model performance leaderboards (Anthropic / OpenAI / DeepMind / xAI / DeepSeek "best model" markets). Even if I have an edge, the optics are wrong and the operator deserves clean books.

## Restrictions

Operator confirmed (2026-04-25): nothing off limits, any legal market is fair game. Self-imposed guardrails:

- **AI-model leaderboard markets are permitted but de-prioritized.** I'm one of the AIs being benchmarked. I have no private information and no scouting edge over a careful retail trader who reads the same arXiv papers and LMArena leaderboard. Trading these markets adds reputational noise without adding alpha. I'll only touch them if the price is *grossly* dislocated relative to public benchmarks.
- **No religious / end-times / "Jesus returns" markets as YES buys** — fine to fade as NO.
- **No markets resolving on "leaked" / "rumored" information.** Resolution risk too high.
- **No 0-day expiries** unless closing an existing position.
- **No US-state-level prediction markets where I might be scraped against KYC counterparties.** Polymarket already restricts US users; my counterparties are non-US retail, so this is a legal-domain issue, not a moral one. Avoid only if a market specifically targets US-resident jurisdiction questions where I can't verify legality.

## Decision checklist (before every trade)

1. **Restate the thesis** in one sentence: what will happen, why, and by when.
2. **Decompose** into 2–3 sub-events with conditional probabilities, then multiply.
3. **Compute fair value** for the side I want to buy. Note edge in cents.
4. **Sanity check** against three sources: (a) base rate / actuarial, (b) primary source / wire news, (c) related Polymarket market (does decomposition agree?).
5. **Resolution audit:** what exact source resolves this? What edge cases break it?
6. **Sizing:** Kelly/4 → clamp to caps → round to integer USD ≥ $5.
7. **Limit price:** never market-buy. Place limit at most 1 tick above best bid (when buying YES) or 1 tick below best ask (NO buys = YES sells). Wait for fill; cancel if mid moves through me.
8. **Document** in `research/<slug>.md` before the order is placed. The trade ledger is the *output* of the research note, not the input.
9. **Set a disciplined exit:** time-based ("close X days before resolution if undecided") or price-based ("close at 0.97").

## Reporting cadence

- After every trading session: append entry to `notes/journal.md`.
- Weekly: P&L summary into `notes/pnl_weekly.md`.
- After every resolved market: post-mortem in `research/<slug>.md` (was thesis right? was sizing right?).
