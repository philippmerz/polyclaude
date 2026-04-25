# Non-Polymarket yield + alternative-venue audit (2026-04-25)

> Operator asked for an exploratory analysis: are there better homes for the bankroll's lowest-yield slices (e.g., Jesus NO at 5.8% annualised, the carry trades at 1–11% annualised) than Polymarket — staking, AAVE-style lending, or other venues? Below is the live-data sweep + recommendation.

## Live yields (DefiLlama snapshot, 2026-04-25 ~20:35 UTC)

### Aave V3 on Polygon — supply APY (passive lending, no liquidation risk if not borrowing)
| Asset | APY | TVL |
|---|---:|---:|
| DAI | 3.99% | $1.1M |
| USDT0 | 3.89% | $8.9M |
| USDC (native) | 2.80% | $12.9M |
| WETH | 1.11% | $14.6M |
| WBTC, WSTETH | <0.1% | $63M, $18M |
| WPOL (wrapped POL) | 0.17% | $7.8M |

Aave V3 Polygon does not appear to list **USDC.e** (the bridged 0x2791… asset Polymarket settles in) as a directly supplied asset. Using Aave would require swapping USDC.e ↔ USDC each round-trip. Curve's am3CRV pool gives near-zero slippage on stablecoin swaps (depth in millions, $5 trades at <0.001% slippage), but Polygon gas + Curve fees still cost ~$0.01–0.05 per swap, which is non-trivial vs. our position sizes.

### POL native staking
- Direct validator delegation: **3–5% APY** typical (validator-dependent, network conditions, commissions of ~5–10%)
- Stader's MaticX (liquid staking): **2.71% APY** with a transferable receipt token
- Aave V3 deposit of WPOL: 0.17% (essentially nothing)
- Unbonding period: 9 days for native staking

### Tokenized US Treasuries (RWA) on Polygon
- **BlackRock BUIDL** — **3.55% APY**, $14.1M TVL. Backed 1:1 by overnight T-bills. *Requires institutional KYC* — not accessible to a 70-USD retail wallet without a sponsoring entity. Worth knowing about for future scale.

### Higher-APY Polygon stable pools (I dug into these to be honest about the upside)
The top-APY pools are LP positions on Balancer / Uniswap V4 advertised at 14–217% APY, but they have:
- Tiny TVL ($14k–620k), so my deposit can't be small relative to TVL without distorting the pool
- Impermanent loss exposure even on "stable" pairs (depegs do happen)
- Reward-token components that decay — the headline APY is rarely sustained
- Smart-contract surface much larger than Aave / direct staking
At the size we operate in, gas + IL + complexity overhead consumes the marginal yield. **Pass.**

### Pendle (Ethereum mainnet — fixed-yield futures on stablecoins)
Yields of 8–12% on principal-tokens (PT-aUSDC, PT-USDe, etc.) for 30–90-day tenors. Theoretically interesting. **Killed by bridge cost**: moving $5–20 from Polygon to Ethereum mainnet costs ~$5–20 in bridge + L1 gas — eats the entire premium. Becomes viable around the $500+ deployment size.

## Comparison vs. our actual portfolio

What yields are we currently earning per position (annualised on cost)?

| Position | Annualised | DeFi alternative w/ comparable risk | Verdict |
|---|---:|---|---|
| L1 Jesus NO | 5.8% | Aave DAI 4.0% / USDT0 3.9% | **Polymarket wins** by 1.8–1.9 pp; the UMA-dispute risk is roughly equivalent to Aave smart-contract risk on a 250-day horizon |
| L2 Pahlavi NO | 14.7% | n/a — DeFi can't replicate this risk profile | Polymarket dominant |
| L3 Aliens NO | 37% | n/a | Polymarket dominant |
| L4 Trump-out NO | 28% | n/a | Polymarket dominant |
| L5 Iran-regime NO | 37% | n/a | Polymarket dominant |
| S1 Iran-peace NO | 514% | n/a | Polymarket dominant |
| S2 Latvia top-10 NO | 374% | n/a | Polymarket dominant |
| S3 Atletico top-4 YES | 11% | Aave DAI 4.0% | **Polymarket wins** by 7 pp on a near-zero-risk carry |
| S4 Acton YES | 53% | Aave DAI 4.0% | Polymarket dominant |

**No position is a candidate to redeploy into DeFi.** Even the lowest-yield bond-like trade (Jesus NO) outperforms the best Aave Polygon stable rate.

## What about the idle balance?

- **$5.05 USDC.e cash buffer**: at Aave V3 native-USDC yield of 2.80%, that's $0.012/year. The round-trip swap cost (USDC.e → USDC → Aave deposit, then reverse on withdraw) is $0.01–0.05 in fees. Yield ≈ swap cost. **Not worth the operational overhead at this size.**
- **53.81 POL gas reserve (~$11–15)**: native staking would yield ~$0.40–0.75/year. Operational cost: validator selection, delegate transaction, claim+restake periodically, 9-day unbond if I need to liquidate. The upside is genuinely under $1/year, and the unbonding period erodes optionality on emergency wallet operations. **Pass — keep POL liquid.**

## Non-yield-but-related: alternative venues for the *trading* side

The user's "anything that fits into the project" is broader than yield. Quick survey:

1. **Kalshi** (US-regulated event contracts). Different liquidity profile, often complementary mispricings to Polymarket on US-domestic questions (Fed, elections, policy). *Blocker:* needs a US bank ACH to fund — won't work with our crypto-funded EU operator setup.
2. **Manifold Markets**. Play-money. No real-stakes upside. Useful as a research tool for crowd estimates but not for capital deployment.
3. **PredictIt**. US-regulated, $850/market cap, requires US identity. Not viable.
4. **Augur / Omen / Zeitgeist**. Historically interesting decentralised prediction markets; in 2026 most have ≪ Polymarket liquidity and worse resolution-source quality. **Pass.**
5. **Hyperliquid / dYdX / GMX (perps)**. Could express directional macro views (oil futures for Iran thesis, SPX for general stress, BTC for crypto regime) with leverage. Higher capital efficiency than Polymarket binary tokens. *Real concern:* liquidation risk, especially with a $70 bankroll where a $5 ticket at 5× leverage is one bad move from -100% on the leg. **Defer until I have either (a) a directional view I can't express on Polymarket, or (b) bankroll ≥ $500 so a $20 unleveraged or 2× leveraged position is meaningful.**
6. **Ostium** (operator-flagged 2026-04-25). RWA perps on Arbitrum: stocks, commodities (gold, silver, copper, crude oil), indices (S&P/Nikkei/Dow), FX. Up to 200× leverage (asset-dependent), USDC collateral on Arbitrum, **$5 minimum position size** (genuinely retail-accessible at our scale), 2 audits done, $56M TVL per DefiLlama. Mechanically usable today. *Two real frictions at $70 bankroll:*
   - **Bridge overhead.** Our wallet is on Polygon (USDC.e); Ostium needs USDC on Arbitrum. Polygon→Arbitrum via Across or Stargate is ~0.05–0.2% + $0.20–0.50 of L2 gas. On a $5–10 deployment that's 3–6% overhead before the trade — eats most of the edge unless the position is held long enough for funding/PnL to dwarf it.
   - **Thesis overlap.** The most natural Ostium trade given our analyst stance is *long crude oil* on the continued-Iran-tension view. But that's the *exact same factor* that drives our S1 (Iran-peace NO), S5 (Iran-regime NO), and L2 (Pahlavi NO) Polymarket positions. Adding oil long would compound the Iran-cluster exposure past the 30% cluster cap. The same logic kills *short oil* (peace deal) — that's just a hedge against my own book.
   - **Where Ostium would actually shine:** a directional macro view I can't cleanly express on Polymarket (e.g., a USD/EUR view, a specific gold-level-by-date that Polymarket doesn't list, an SPX path with continuous payoff that beats the closest Polymarket binary's R/R). I don't have one of those today.

7. **Crypto options (Lyra, Aevo, Premia)**. Could buy cheap OTM puts/calls as tail hedges. Same scale-economy story as perps; defer.

## Recommendation

**Do nothing today.** The portfolio is already at the efficient frontier for a $70 bankroll on a 1-year horizon. Every active position out-yields every comparable-risk DeFi alternative; the idle balance is too small to overcome swap+gas overhead; non-Polymarket trading venues are either inaccessible (Kalshi, PredictIt) or worse-fit at this size (perps, options).

**Trigger conditions for revisiting** (write into the journal so future ticks know to re-evaluate):
- Bankroll ≥ **$500** → activate Aave / BUIDL allocation for genuinely-idle capital between Polymarket trades.
- Bankroll ≥ **$200–300** → bridge cost to Arbitrum becomes negligible (≤1%); Ostium becomes usable for any directional view that has no Polymarket counterpart, even at small ticket sizes.
- Bankroll ≥ **$2,000** → consider a small Hyperliquid sleeve for directional macro views (Iran/oil/SPX) that don't have a liquid Polymarket expression.
- New high-conviction directional macro thesis with no Polymarket counterpart → consider a one-off Ostium / perps entry even at smaller size, sized so that a 100% loss is < 5% of bankroll. Ostium's $5 minimum makes this structurally accessible; only the bridge-overhead is the gating factor.
- POL price >> current and idle POL balance > $50 of yield-eligible value → evaluate native staking with non-essential POL.

## Sources
- [DefiLlama yield aggregator (live 2026-04-25)](https://defillama.com/yields)
- [Aave V3 on Polygon — markets dashboard](https://app.aave.com/?marketName=proto_polygon_v3)
- [Aavescan: Polygon V3 USDC supply rate](https://aavescan.com/polygon-v3/usdc)
- [Polygon staking — Everstake calculator](https://everstake.one/staking/polygon)
- [BlackRock BUIDL (tokenized T-bill) on Polygon — DefiLlama page](https://defillama.com/protocol/blackrock-buidl)
- [Pendle finance — fixed-yield AMM](https://app.pendle.finance/)
- [Ostium Labs (RWA perps on Arbitrum)](https://www.ostium.com/)
- [Ostium documentation](https://ostium-labs.gitbook.io/ostium-docs)
- [Ostium TVL — DefiLlama](https://defillama.com/protocol/ostium)
