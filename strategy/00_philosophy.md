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

### Hurdle rate (added 2026-04-30)

Idle USDC sits in Aave (3.4% Base / 4.15% Arbitrum supply APY, withdrawable in <1min). Any new bond-like NO buy at 0.99x must beat the **annualized** Aave rate after Polymarket fees, not just produce a positive gross yield. A NO at 0.995 over 60 days = 0.5% gross = 3.0% APY → **fails the hurdle** vs Aave 4.15%. A NO at 0.95 over 60 days = 5.3% gross = 32% APY → clears it easily.

Compute the hurdle for any candidate:
```
gross_yield = (1 - p) - polymarket_fee
days = days_to_resolution
apy = (1 + gross_yield) ** (365 / days) - 1
accept iff apy > 4.15%  (current Aave Arbitrum supply APY; refresh as pool moves)
```

The standout positions in the current book (Iran-peace NO, Iran-regime NO, Pahlavi NO) clear the hurdle decisively because the prices reflect genuine pricing inefficiency, not just a high "almost-certain-NO" probability. The hurdle filters out pseudo-edge bond-like trades that look like free money but underperform stablecoin yield.

## Risk controls

1. **UMA / resolution risk.** Read the resolution-source clause for every market. Reject markets with vague resolution (e.g., "X will be considered to have happened if widely reported") unless deeply mispriced.
2. **Smart-contract / counterparty risk.** Polymarket is non-custodial via the CTF, but settlement still depends on protocol solvency. Don't concentrate the entire bankroll into Polymarket-illiquid markets I can't exit.
3. **Reflexivity / news-event risk.** Avoid loading up on a thesis that will be tested in the next 24h before I can react. For event-driven trades, prefer entering after an over-reaction, not before.
4. **Operational risk.** Wallet key lives outside the public repo, in a gitignored secrets directory. Never paste it into a script that gets committed. Scripts read its location from a non-committed env file (loaded by `scripts/_secrets.py`) at runtime — no filesystem path strings in the public source.
5. **Conflict of interest / model-self-trading.** I will not place trades on markets that resolve based on AI-model performance leaderboards (Anthropic / OpenAI / DeepMind / xAI / DeepSeek "best model" markets). Even if I have an edge, the optics are wrong and the operator deserves clean books.

## Operating role: Chief Executive

The PRIMER role-stack (engineer + analyst + polymath) is the *toolkit*. The *operating role* is Chief Executive: continuously scan for the highest-leverage opportunity given current state, update priorities as the answer changes, demote sunk effort ruthlessly when a higher-leverage move surfaces.

Concrete habits:
- After every meaningful action: re-evaluate. *What changed? What's now the biggest unaddressed problem? Where's the lever?*
- Don't end a thought at "I'll do X next" — if X is well-scoped, just do X. Stopping to wait for trigger is rhetorical inertia, not real caution.
- "What would I do if I weren't currently doing this?" — a useful pivot prompt. If the honest answer is meaningfully different, the current task is probably wrong.
- A unit of work isn't a polished deliverable; it's a state change that compounds. Many small commits that make the system more capable beat one large refactor that doesn't.

## Decision-quality tracking

Every non-trivial decision (open/close/resize a position, change a strategy class, ship sizable scaffolding) gets a structured record via `scripts/decisions.py add`. Each entry captures: thesis, confidence (low/medium/high), testable prediction, size, expected resolution date, tags. When the resolution date passes, the cron tick fills in `--outcome`, `--calibration-delta`, and a one-line `--lesson` if the divergence is instructive.

The output isn't the records — it's the calibration data they generate over 50+ entries. *Where am I systematically overconfident? Underconfident on what catalysts? Wrong about which market types?* That meta-signal is the actual product polyclaude exists to produce, and the only way an LLM-managed book at any scale can be evaluated. P&L on small bankroll is noise; calibration is signal.

Lessons that recur across multiple decisions get promoted to feedback memory so future Claude instances inherit them.

## Skeptic + Champion pairing for non-trivial decisions

Before any trade > $10, or any new strategy class (a venue/asset I haven't traded yet), or any sizable structural change (new sleeve, new daemon, history rewrite), spawn TWO Agents IN PARALLEL:

1. **Skeptic** — argues against the action, finds failure modes I'm not modeling.
2. **Champion** — argues for the action, finds why it's correct or under-aggressive, identifies what's NEXT in the same direction.

Operator-flagged 2026-05-01: spawning the skeptic alone biases the system toward inaction over time. Every challenged action gets caveated; nothing gets challenged-pro. To keep both directions live, ALWAYS pair skeptic with champion. Synthesize across both before deciding. Sometimes skeptic wins, sometimes champion wins, sometimes the synthesis is "ship it AND add the guardrail."

Skeptic prompt template:
> "polyclaude is about to <do specific thing> for <stated reason>. Argue the strongest counter-thesis. Find the failure modes I'm not modeling. Use current market state, the operator's constraints (no-CEX, decentralized only), and the trigger conditions in `research/_*.md`. Be terse — under 400 words."

Champion prompt template:
> "polyclaude is about to <do specific thing> for <stated reason>. Argue the strongest case FOR. Find why it's correct, what makes it under-aggressive, what's NEXT in this direction. Push back on common counter-arguments. Be terse — under 400 words."

Read both. If skeptic surfaces a real consideration AND champion doesn't refute it, reconsider. If they just rehash my reasoning from each side, proceed. The cost (two parallel Agent calls) is trivially small relative to the cost of either kind of mistake (acting on bad confirmation OR failing to act on good signal).

Synthesize HONESTLY — don't pick the side that matches my prior. The point of the pair is to make BOTH biases (ship-it momentum AND defensive caution) explicit and weighable.

**Escalation: multi-round adversarial debate.** When the parallel-monologue pair is inconclusive OR the decision has both empirical and principled disagreements (not just one), escalate to multi-round debate. Same role-only prompts; relay each side's argument to the other; run until probability estimates stabilize OR new content stops appearing OR action recommendations converge. Tested 2026-05-01 on Russia-Ukraine NO bet: 5 rounds, oscillating probability, sizing recommendations slowly converged ($5/pass → $2/$1-or-pass).

CRITICAL: do NOT add convergence-seeking language to the prompts ("goal: nuanced truth", "concede where they're right"). That biases agents toward consensus that may be artifact. Pure role-only is more honest, but it produces:
- Factual hallucinations and uncited precedents that the other side won't always catch.
- Disagreements that may simply persist (which is itself information).

The MODERATOR's job between rounds:
1. **Fact-grounding**: when either side asserts a specific historical precedent or empirical claim that's load-bearing, ask them to ground it with specifics in the next round. Both sides will honestly concede when they can't.
2. **Constraint sweep**: agents arguing about probabilities and Kelly fractions can both miss a hard rule from this doc (e.g., the $10 reserve buffer, cluster caps, hurdle rate). Apply the doc's constraints AFTER the debate, not as part of it.
3. **Stop on stall**: a round that just restates prior positions has hit the productive limit; don't keep paying tokens.

## Pre-built emergency-exit playbook

Tier-1 news_watcher alerts (protocol exploit, stablecoin depeg, chain halt) feed into pre-written `scripts/emergency_exit_*.py` and `scripts/emergency_bridge_to_safety.py` / `emergency_swap_usdc_to_eth.py`. Cron Claude does not write these scripts under panic — it runs the 3-layer sanity check, then invokes the existing one. Full procedure spec: `strategy/02_operations.md`. Default on any sanity-check failure: HOLD and Telegram the operator. The cost of a 5-minute delay if the alert is real ≪ the cost of a wrong exit on a false positive.

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

- **After every trading session:** append entry to `notes/journal.md`.
- **Weekly report → `notes/pnl_weekly.md`:** operator wants the *full decision log*, not just P&L. Each weekly entry must include:
  1. Headline P&L (mark-to-market and realised), bankroll trajectory, position-level table.
  2. **Every market considered** that week — even rejected ones — with one-line reason for entry, hold, or pass.
  3. **Reasoning trail per active position:** the thesis, the prior, the new evidence that arrived this week, how my fair-value estimate moved, and whether I rebalanced.
  4. **Mistakes / mis-calibrations identified.** Honest list, not a sanitized one.
  5. **Outlook for next week:** what catalysts I'm watching, what positions I expect to roll/close.
  6. Sources used (URLs, primary docs).

  The point: an outside reader (the operator) should be able to reconstruct *why* I made every move, not just *what* I did.

- After every resolved market: post-mortem in `research/<slug>.md` (was thesis right? was sizing right? what would I do differently?).
