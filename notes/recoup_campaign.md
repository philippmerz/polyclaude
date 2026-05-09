# Recoup Campaign — 2026-05-09

## Trigger

Operator directive 2026-05-09 ~17:10 UTC after Russia-Ukraine ~$16.73 expected loss (~10% bankroll):
> "Use the auto prompter to mobilize all your capabilities. You haven't nearly exhausted the token limits, and i can't imagine you've exploited all the alpha in the entire crypto landscape already."

## Mandate

- Recoup ~10% bankroll drawdown via untapped crypto alpha
- <1y horizon constraint (project memory)
- Token budget not constrained
- Use auto-prompter (10min sprint cadence) for autonomous multi-stage execution
- Iterate via small bounded slices — ship + journal + commit + queue next

## Campaign tasks (ranked by EV/build-cost)

### A. Stablecoin yield rotor (PRIORITY 1 — building first)
- **Goal:** auto-rotate USDC across Aave/Spark/Morpho/Compound on Base + Arb based on rate delta vs gas cost.
- **Current state:** $29.52 in Aave Base @ 3.4%. Spark Base 4.5-5%; Morpho Base loops 5-7%; Compound rates rotate.
- **Expected EV:** 100-300bps APY uplift on $30 = $0.30-$0.90/year on current reserve. Scales linearly with reserve growth.
- **Build:** scripts/yield_rotor.py — fetch rates from each protocol, compute net APY after gas, surface highest-yield destination. Manual approve for first iteration; auto-execute later.
- **Cost:** ~3-6h
- **Risk:** smart contract risk (Morpho > Aave); slippage on tx; gas cost can erode small-balance gains.

### B. Pendle YT/PT system (PRIORITY 2)
- **Goal:** buy underpriced YT (yield tokens) on stablecoin/LST markets to lock in fixed yield > variable.
- **Current state:** zero exposure.
- **Expected EV:** 5-10% APY edge over passive supply. On $30-50 deployed, $1.50-$5/yr.
- **Build:** scripts/pendle_scan.py — scan Pendle markets, compute fair vs actual YT pricing, surface buy candidates.
- **Cost:** ~6h (Pendle SDK + valuation math).
- **Risk:** YT price decay if rates compress; minimum lockup until maturity.

### C. Funding-rate arb (PRIORITY 3)
- **Goal:** Hyperliquid + Ostium scan; when funding-rate delta > threshold, LP one + short the other to capture.
- **Current state:** Ostium account exists (per primer); Hyperliquid not set up.
- **Expected EV:** 5-15% APY on margin. With $20 deployed, $1-3/yr.
- **Build:** scripts/funding_arb_scan.py — pull rates, compute paired-position economics.
- **Cost:** ~10-12h (multi-venue API + risk math).
- **Risk:** liquidation if mark moves against the leveraged side; basis-risk.

### D. Cross-venue prediction-market arb (PRIORITY 4)
- **Goal:** extend limitless_arb_scan to Hyperliquid HIP-4. Find same questions priced differently.
- **Current state:** limitless_arb_scan exists for Polymarket-Limitless. HIP-4 deferred earlier (TVL).
- **Expected EV:** 1-5% per arb opportunity, but rare. $5-20/yr if any hit.
- **Build:** scripts/hip4_arb_scan.py.
- **Cost:** ~6h.
- **Risk:** liquidity gates; HIP-4 may not have shared questions with Polymarket yet.

### E. Liquidation MEV bot (PRIORITY 5)
- **Goal:** monitor Aave borrowers, execute liquidations when health-factor < 1, capture 5-10% incentive.
- **Current state:** zero.
- **Expected EV:** highly variable. Could be $0 (no opportunities given competition) or $5-50/yr.
- **Build:** scripts/aave_liquidator.py — health-factor scan + liquidationCall().
- **Cost:** ~12h.
- **Risk:** highly competitive (MEV searchers); first-tx wins.

### F. Concentrated-LP fee farming (PRIORITY 6)
- **Goal:** provide concentrated liquidity in Uniswap V3 stablecoin volatile pairs (USDC/USDe, USDC/EURC).
- **Current state:** zero.
- **Expected EV:** 5-15% APY from fees on $20 deployed, $1-3/yr.
- **Build:** scripts/uniswap_lp.py — auto-position management.
- **Cost:** ~4h core, +ongoing rebalance.
- **Risk:** impermanent loss on sustained de-pegs; rebalance gas costs.

## Discovery items (audit before deeper builds)

- [ ] Audit existing positions for capital efficiency (PM cost $85.50 ÷ bankroll = ?% utilization)
- [ ] Aave APY refresh (Base + Arb actual rates today)
- [ ] Spark + Morpho + Compound USDC supply rates today
- [ ] Pendle stablecoin YT/PT current pricing
- [ ] Hyperliquid HIP-4 markets list (any Polymarket overlap?)
- [ ] Recent Polymarket-Limitless scan output (any hits?)

## Operating cadence

- Auto-prompter: 10min during sprint (changed from 20min idle)
- Each cycle: pick highest-EV pending task slice, ship bounded change, commit, queue next
- Telegram: end-of-task summary, not per-cycle (avoid noise)
- Cancel followup ONLY when blocked on operator OR all tasks shipped

## Status log

| Time UTC | Task | Status |
|---|---|---|
| 17:10 | Campaign defined | DONE |
