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
| 17:30 | DEC-0019 May-11 NO opened ($14.475) | DONE |
| 17:30 | scripts/sports_pm_scan.py shipped | DONE (commit d9a6059) |
| 17:50 | scripts/kelly_size.py shipped + DEC-0015 scale ($8.74) | DONE (commit 8cecebd) |
| 18:25 | Bridge $25 Aave Base→Polygon + DEC-0021 Regime-fall scale ($21.25) | DONE (commit 1230390) |
| 18:50 | scripts/portfolio_kelly.py + priors shipped | DONE (commit 8f1805e) |
| 19:10 | portfolio_kelly --constrained + arb scanner false-pos fixes | DONE (commit 15b4410) |
| 19:30 | DEC-0022 Trump-out scale ($3.56) + bookie-consensus integration | DONE (commit 2e23453, 2e462cf) |
| 19:50 | portfolio_kelly wired into daily_checkin step 4 | DONE (commit 67e2af9) |
| 19:50 | scripts/macro_pm_scan.py + CME FedWatch integration | SHIPPED-DEGRADED — v1 shipped with --no-consensus default (CME FedWatch is JS-rendered, haiku hallucinated +27.4pp delta vs ground-truth +1.5pp; consensus disabled until v2 ZQ-futures parser) |

## Cumulative metrics

- **Trades opened/scaled this session:** 4 (DEC-0019, 0015-scale, 0021, 0022) = $48.02 deployed
- **Tools shipped:** 5 (kelly_size, portfolio_kelly, sports_pm_scan with consensus, macro_pm_scan, limitless_arb_scan fixes)
- **Cron wiring:** 2 (sports_pm_scan into step 6, portfolio_kelly into step 4)
- **Expected EV from new positions:** ~$11-15 over 22-235d horizon
- **Effective recoup rate:** ~67-90% of R-U $16.73 in expected value

## Pending campaign items

- Limitless wallet setup for arb execution (operator-touching: requires fund routing decision)
- Funding-rate arb scanner (Hyperliquid + Ostium delta capture)
- Pendle YT scanner
- Liquidation MEV monitor (high variance, defer)
- Cross-venue HIP-4 extension (defer until HIP-4 has TVL)
- polyclaude_enter.py — single-command entry helper (catalyst_check + Kelly + execute)

---

## CAMPAIGN CLOSE-OUT — 2026-06-01

**Status: effectively complete.** The May-31 Iran-peace NO redeemed +$5.62 (2026-06-01), the last of the campaign's recoup trades to settle.

**Realized scorecard vs the R-U −$16.73 hole:**
- R-U loss: −$16.73
- Campaign + ambient realized wins since: May-11 NO +$0.525, May-15 NO +$3.54, Latvia +$0.706, gold TP +$1.17, NDX-SHORT TP +$1.96, SPX-LONG close +$1.17, Jesus +$0.19, May-31 NO +$5.62, minus small (Aliens-abort −$0.08, Atletico −$0.07)
- **Net cumulative realized ≈ −$2.0** — the −$16.73 hole is ~88% refilled in realized terms.
- Held book: 5 long-dated NOs to Dec-31 (~+$11 combined expected) + Satoshi NO. Expected to flip cumulative realized clearly positive at year-end.

**Durable infra delivered (the campaign's real legacy, beyond the $):**
- Sizing: kelly_size, portfolio_kelly --constrained, brownian_bridge_fv
- Safety: uma_status_check (closes the actual R-U root cause), polyclaude_enter robust-edge gate + live-ask gate + tick-rounding
- Sourcing: world_state_digest + longterm_check weekly review; discover_markets 10× fetch-cap fix; watchlist auto-revet
- Scanning: sports_pm_scan +consensus, macro_pm_scan, event_monotonicity_scan
- Frameworks (strategy/00): term-structure-as-UMA-signal, Kelly-vs-Brownian-bridge (+ Bayesian-conditional EV gotcha), edge-bar = robust-EV
- Process: ostium_state_diff, news_watcher tier-2 body-fetch CRITICAL re-val, capital_ledger

**Strategy shifts banked:** mechanical-resolution-only filter; 60/40 scrapped (operator); edge bar 10pp → robust-EV (operator); idle-home = same-chain Aave.

Remaining "pending campaign items" (Limitless/Hyperliquid/Pendle/MEV scanners) are deferred new-venue expansions, not recoup-critical — they live in notes/backlog.md now. This tracker is closed.
