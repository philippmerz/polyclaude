# Crypto landscape audit — separate $50 bankroll, < 6 month horizon (2026-04-27)

> Operator asked: where would a *new, separate* ~$50 sleeve get the highest EV in crypto over a < 6 month window, fees and compute included? This memo is *not* the polyclaude $70 Polymarket book — it's a clean-slate exploration covering the entire crypto landscape from blue-chip yield to sub-$30M-FDV speculation. Verdict at the bottom; tier-ranked plays in between.
>
> **TL;DR.** At $50 / < 6mo / fully-decentralized self-custody, two plays clear the fee-and-compute screen with structural retail edge AND are 100% Claude-executable: **(1) Ostium points-farming on Arbitrum** (no token yet, $25B cumulative volume, Jump+General-Catalyst-backed — the single strongest novel bet) and **(2) Limitless ↔ Polymarket prediction-market arbitrage on Base** (zero-gas, $1B/mo notional, structural liquidity-fragmentation edge). **Default split: $30 Ostium / $15 Limitless / $5 gas reserve.** Bittensor / TAO is **dropped permanently** — operator's no-CEX/no-KYC constraint rules out the only viable funding rail at $50; on-chain bridges (TaoFi at $192K TVL) charge 5-15% slippage at our size. New crypto-sleeve wallet generated 2026-04-27 — address `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6`, credentials stored in the gitignored secrets directory (mode 0o600). Operator's only required action: send $50 USDC.e to that address on Polygon. Skip pump.fun retail sniping, HLP, funding-rate arb, LRTs (post-Kelp), inscriptions/runes, MOVE, Plasma post-July.

---

## 1. What the constraint set actually allows

Hard limits at $50 + 2 CPU / 2 GB / Polygon-self-custody-with-Across-bridge:

- **Ethereum L1 is dead.** $3-12 deposit + $4-15 withdraw kills any < $200 strategy that touches mainnet. Verified live gas snapshots ([PolygonScan](https://polygonscan.com/chart/avg-txfee-usd), [Arbiscan](https://arbiscan.io/chart/gasprice)).
- **Polygon, Arbitrum, Base, Optimism all clear** the < $0.50/tx bar. Solana effectively gas-free.
- **Bridging:** Polygon→Arbitrum/Base via Across is ~$0.04 + $0.005 source gas at $50 notional. Polygon→Solana via Wormhole CCTP $0.30-0.80. Cross-bridge round-trip cost is 0.1-1.6% of bankroll — non-trivial but not disqualifying.
- **HFT / latency-critical strategies are out.** Mempool-monitoring memecoin sniping, MEV, statistical arbitrage all need infra we don't have and competition with AWS-collocated bots.
- **Perp basis trade is mechanically infeasible.** Hyperliquid BTC min order ~$10, ETH $10, SOL $10 — at $50 split spot+perp you're at 2-3 perps, dust funding payments, no margin headroom.
- **Compute on a 2 CPU / 2 GB VM is fine for periodic API calls.** All recommended strategies are fund-and-watch with weekly-or-less rebalance.

## 2. Market regime context (verified 2026-04-23 to 04-27)

Spot levels: BTC ~$77,750 (dominance 56-57%), ETH ~$2,317, SOL ~$85.66. **HYPE $42.49 / FDV $39.5B** (rank #13, already 2x'd Q1 — late entry); **TAO $329 / MC $3.55B** (+86% / 30d on Jensen Huang AI-compute endorsement, then -20% on Apr 10 from Covenant AI exit from Bittensor). BTC DVOL ~40-41 (moderate, contango term structure). Sources: [CoinMarketCap](https://coinmarketcap.com/), [Phemex Q1](https://phemex.com/blogs/q1-2026-crypto-report-card-top-performing-tokens), [Hyperliquid info API](https://api.hyperliquid.xyz/info).

Stablecoin landscape: total $320.65B (ATH ~Apr 11). USDT 59.19% / USDC ~24% / **USDe $3.82B (-34% on April 19 Kelp DAO contagion)**. No USDT/USDC depegs in last 90d ([DefiLlama](https://defillama.com/stablecoins)).

**Two recent hacks materially affect strategy choice:**
- **Kelp DAO drained $293M, April 19 2026** — LayerZero EndpointV2 exploit on rsETH, ~18% of supply hit, Lazarus suspected ([CoinDesk](https://www.coindesk.com/tech/2026/04/19/2026-s-biggest-crypto-exploit-kelp-dao-hit-for-usd292-million-with-wrapped-ether-stranded-across-20-chains)). **De-rates the entire LRT/restaking sector.**
- **Drift Protocol $286M, April 1 2026** — oracle manipulation via fake CVT, DPRK-linked ([Elliptic](https://www.elliptic.co/blog/drift-protocol-exploited-for-286-million-in-suspected-dprk-linked-attack)). De-rates Drift directly; Solana ecosystem mildly contagioned.
- Earlier: **Resolv $25M exploit March 22 2026** — unauthorized USR mint of 50M unbacked tokens. Skip Resolv until trust restored.

Capital flows ranked (cap commanded right now): RWA tokenization $27-29B on-chain (+300% YoY), perp DEXs (Hyperliquid Q1 vol $493B), AI/agents (sector cap $11.3B, down 44% from Jan-2025 highs), memecoins ($33.7B sector, cooling), prediction markets ($63.5B annual run rate, doubled in 2025).

Catalysts in the next 6 months that matter:
- **Apr 28-29:** FOMC (Powell's last meeting; 99.9% no-change priced); CLARITY Act markup
- **Apr 30:** **MegaETH MEGA TGE** (post-KPI-2 confirmation, [Crypto Briefing](https://cryptobriefing.com/megaeth-token-generation-event-set-for-april-30-2026/)). Polymarket implies > $600M FDV at 97% confidence. Largest near-term catalyst.
- **May 4:** CME launches SUI futures
- **Q2-Q3:** Ethereum Glamsterdam upgrade (gas reduction, PBS reform)
- **July 28:** Plasma (XPL) 25% supply unlock to US public-sale buyers — bearish, do not buy XPL before this
- **TBD 2026:** Polymarket POLY token + airdrop confirmed by CMO, no date

## 3. Strategy-class scoreboard

| # | Strategy | Mechanism | Realistic 6mo return | Fee/compute pass at $50? | EV-rank |
|---|---|---|---|---|---|
| 1 | Ostium points-farming + RWA-perp directional | Trade RWA perps on Arbitrum, accumulate retroactive-airdrop points | Optionality; 2-10x airdrop precedent for similar projects | YES (sub-cent gas, $5 min trade) | **Tier 1** |
| 2 | Bittensor subnet alpha (SN64 Chutes via TAO) | Directional bet on top emission subnet w/ revenue | 0.5x-5x; 200-400% subnet swings observed in 30d windows | YES (TAO purchase + bridge ~$1) | **Tier 1** |
| 3 | Limitless ↔ Polymarket arbitrage | Same political/sports markets priced differently across the two venues | 5-15% per crossed cycle, modest size cap | YES (Base zero-gas) | **Tier 1** |
| 4 | Pendle PT-sUSDe-Jun-2026 (Arbitrum) | Lock 4-5% fixed for ~50 days at maturity | ~0.7% absolute over 50 days | YES (Arbitrum gas trivial) | **Tier 2 (yield floor)** |
| 5 | MegaETH MEGA TGE Apr 30 | Buy at TGE if mispriced in first hours | Variance-heavy; binary — could be 0.5x or 5x | YES if disciplined size | **Tier 2 (event)** |
| 6 | PLUME directional (RWA narrative) | Buy a 95%-drawn-down RWA-chain native token on continued sector inflows | 1.5-5x if sector rotation hits, 0 if not | YES (DEX on Plume) | **Tier 2** |
| 7 | Aave V3 stable lending Polygon | Passive 3-4% USDC/USDT | 1.5-2% absolute over 6mo | YES | Tier 2 (boring floor) |
| 8 | Akash / GEODNET / WeatherXM (sub-$200M FDV DePIN) | Directional sector beta | 1-3x if AI-compute / mapping narratives reignite | YES | Tier 2 |
| 9 | Hyperliquid HLP vault | Provide MM/liquidation inventory, earn flow fees | -55% to +50% range (12mo realized) | YES (any size, 4d lock) | Tier 3 (risk profile wrong) |
| 10 | LRTs (weETH/rsETH/ezETH) | Restaking + ETH beta + airdrop residual | -10% to +5% likely; airdrop value largely paid | NO (post-Kelp risk re-rate) | Tier 3 (avoid) |
| 11 | Funding-rate basis trade | Long spot, short equal-notional perp, harvest funding | 5-13% APR if size permits | NO (perp-min disqualifies $50) | **Tier 3 (mechanically OOS)** |
| 12 | Pump.fun memecoin sniping | Snipe new launches, ride pump | 97% of users < $1K profit ([Bitget data](https://www.bitget.com/news/detail/12560604161427)) | YES gas-wise but negative-EV | **Tier 3 (negative-EV at retail)** |
| 13 | Inscriptions/Runes | Trade BRC-20 / Runes alts | Sector dead, ~150K daily tx vs 750K peak | NO (BTC fees + slippage at $50) | Tier 3 |

## 4. Tier 1 deep-dives

### 4a. Ostium points-farming + RWA-perp directional (Arbitrum) — *highest single conviction*

**What it is.** Ostium is an on-chain perpetual-futures venue on Arbitrum specialized in real-world assets: gold, silver, oil, FX, S&P/Nikkei/Dow indices, and **22 individual US equities** (NVDA, AAPL, TSLA etc.) — 54 RWA-perp pairs total, up to 200x leverage, USDC collateral, **$5 minimum position size**. TVL $58M, **$25B cumulative volume**. Backed by Jump Crypto + General Catalyst at ~$250M post-money private valuation. **No public token yet**; an active points program is documented and explicitly retroactive-airdrop-shaped. ([Ostium](https://www.ostium.com/), [The Block Series A](https://www.theblock.co/post/381241/harvard-alumni-founded-ostium-lands-24-million-in-fresh-funding-to-scale-onchain-perpetuals-for-rwas), [DefiLlama TVL](https://defillama.com/protocol/ostium))

**Why it's the top pick.**
- The *trade* is the points-farming, plus optionality on a credible airdrop in next 12-18 months. Comparable retroactive-airdrop precedents (Hyperliquid, Jito, Jupiter, dYdX) returned 5-50x of cumulative-fee paid for active retail farmers.
- Real product traction ($25B cumulative is not vapor) — risk of "rug" or "no token" is materially lower than typical airdrop farms.
- Arbitrum gas is sub-cent on opens/closes — at $50 with 5-10x leveraged $5 tickets you can rotate 50-100 trades over 6 months without fee drag.
- Bridge cost from Polygon (one-time): $0.04 via Across.
- The directional perp side is upside on top — operator can express macro views (gold/oil/SPY) that don't exist on Polymarket.

**How to size it.** Bridge $25-30 of USDC to Arbitrum. Open a sequence of $5-10 leveraged positions on RWA pairs with a held duration of days, not minutes. Goal: maximize **(volume × held-time)** which is the standard points-formula proxy. Don't over-trade on one direction; mix long and short to avoid getting wiped on a single macro move.

**What can go wrong.**
- Token may never launch, or launch with terms unfavorable to retail farmers (cliff, vesting, low pct).
- Liquidations at high leverage at $50 wipe the sleeve. **Cap leverage at 5x and per-trade size at $7.** A 20% adverse move on 5x = 100% loss on the leg.
- Smart-contract risk: Ostium has 2 audits but is < 2 years old. If TVL is $58M and you have $25, you're 0.04% of the TVL — not the marginal risk in a hack scenario.

### 4b. Bittensor subnet alpha — directional Tier-1 alt-bet

**What it is.** Bittensor's dTAO upgrade made the 128 subnets each have their own tradeable "alpha" token, automatically minted from emissions and traded via on-subnet liquidity pools. Total subnet alpha cap ~$1.12B (≈27% of TAO market cap). Top performers in last 30 days ([CoinPedia](https://coinpedia.org/news/top-10-bittensor-subnets-to-watch-as-tao-surges-90/), [CoinGecko top subnets](https://www.coingecko.com/learn/top-bittensor-subnets-dtao)):

- **SN64 Chutes (Rayon Labs)**: serverless AI inference, **9.1T tokens served, 400K users**, dominant emission share. MC $132M. **Cleanest cashflow story** (auto-staking buys SN64 alpha from platform revenue). +54% / 30d.
- **SN3 Templar**: trained Covenant-72B onchain. +444% / 30d. **Operator risk after Covenant AI exit on April 10.** Skip.
- **SN24 OMEGA Labs** +440%, **SN114 Level** +280%, **SN15 BitQuant** +230%, **SN68 Nova** +218%, **SN81 Grail** +211% — all under $50M MC.

**The $50 mechanics.** Buy ~$30 TAO on Coinbase or Kraken, withdraw to a Subtensor-compatible wallet (Polkadot.js / Talisman), stake into the SN64 alpha pool. Spreads on individual subnets are 5-15% — that's the cost of entry. Position-size for 50%+ daily swings — this is volatile.

**Easier alternative for $50:** just buy spot **TAO** on a CEX. You get diversified exposure to all 128 subnets via emissions, no on-chain wallet hassle, no spread cost. Less upside than picking the right alpha but less variance and zero operational drag. Recommend this if you don't want to deal with Subtensor wallets.

**What can go wrong.** Subnets can underperform, exit, get de-emissioned. Operator/team risk is real (Covenant exit was a sub-day -20% move in TAO). dTAO mechanism is new (live since 2024) — second-order failure modes are unknown.

### 4c. Limitless ↔ Polymarket prediction-market arb (Base)

**What it is.** Limitless on Base is the second-largest prediction market by volume — **$1B monthly notional Q1 2026**, ~$35-40M/day, up ~10x in < 12 months ([BitcoinFoundation report](https://bitcoinfoundation.org/news/prediction-markets/prediction-market-limitless-volume-base/)). Coinbase subsidizes gas → trading is **zero-fee on the gas leg**. They have substantially the same political/sports/macro markets as Polymarket, often with materially different prices on identical events because liquidity providers and trader bases differ.

**The trade.** Watch a basket of identical markets across Polymarket and Limitless. When the spread between identical YES tokens exceeds the Polymarket fee (which is edge-aware, ~1-3.6% per side depending on price), buy the cheap side and sell the expensive side. At resolution both pay $1, you pocket the spread.

**Why it works at $50.** Zero gas on Base + Polymarket's fee dropped to 0.072% at p ≥ 0.95. Identical-market spreads of 2-4% are reportedly observed weekly on contested politics/sports markets ([Limitless](https://limitless.exchange/)). At $10-15 per side, even a 2% gross spread - 1% Polymarket fee = 1% net ≈ $0.10-0.15 per crossed cycle. If you find one cycle a day, that's 50-100x the bankroll's risk-free rate over 6 months.

**Where this fails.** Resolution-source mismatch: occasionally Polymarket and Limitless resolve the "same" market differently because their wording or oracle source diverges. **Always verify resolution criteria are byte-identical before crossing.** Also — Limitless markets may be lower-liquidity, so "buy the cheap side" may not fill at the marked price.

**Operational lift.** Build a tiny Python script (3-4 hours) that polls Polymarket gamma-api + Limitless markets API every 5 min, tags markets that match by question-hash, computes the spread, and pings Telegram when spread > 2%. Capital: $20-25 split between Polymarket (already funded) and Limitless on Base. Net of bridging once, ~$0.10 cost.

## 5. Tier 2 plays (worth considering, briefer)

### 5a. Pendle PT-sUSDe-Jun-2026 (Arbitrum) — yield floor
4.31% fixed APR ([Pendle](https://app.pendle.finance/trade/markets)). 50 days to maturity. Locks ~$0.30 of yield on a $20 position over the holding period. Boring but smart-contract-clean and the lowest-vol option here. Skip if you'd rather all-in on Tier 1 — at $50 even the yield baseline is < $0.50.

### 5b. MegaETH MEGA TGE — April 30 event play (3 days from now)
[Crypto Briefing confirms TGE Apr 30](https://cryptobriefing.com/megaeth-token-generation-event-set-for-april-30-2026/). Polymarket prices > $600M FDV at 97% confidence. Mechanics like every TGE: opening pump-and-fade pattern is common, but real takeoffs (Hyperliquid airdrop $2 → $32) happen too. **Cap exposure at $5-10. Wait for first 30-60 minutes of trading to see if there's order-book follow-through; don't FOMO into the first wick.** Set a 30% trailing stop.

### 5c. Plume Network (PLUME) directional — RWA narrative beta
$0.0138, ~95% off March-2025 ATH of $0.2475. 259K RWA users, **$645M assets onchain**, growing. Sector cap is climbing; PLUME has not yet recovered. Asymmetric retail RWA bet. Position size $5-10. ([CoinMarketCap PLUME](https://coinmarketcap.com/currencies/plume/), [RWA.xyz Plume](https://app.rwa.xyz/networks/plume))

### 5d. Akash / GEODNET / WeatherXM — sub-$200M FDV DePIN
Akash (AKT) is the cleanest GPU-DePIN with revenue-paying tenants and FDV ~$200M. GEODNET (RTK GPS) and WeatherXM (WXM) are micro-caps with growing physical-device counts. Skip Hivemapper (only ~242 active contributors, fragile) and Nosana (thin orderbooks → 1-3% slippage at $50). $5-10 single ticket.

## 6. Tier 3 — actively skip, with reasons

| Skip | Why |
|---|---|
| **Pump.fun memecoin sniping** | Retail edge gone. Only 0.63% of pump.fun launches "graduate"; only 3% of sniper-traders earn > $1K. Negative-EV at $50 ([Bitget data](https://www.bitget.com/news/detail/12560604161427)). |
| **HLP vault on Hyperliquid** | 12-mo realized max DD **−55%**, all-time DD −70%. Risk profile is trend-following CTA, not yield. Wrong tool. |
| **Funding-rate basis trade** | Mechanically infeasible at $50 — perp min orders + dust funding payments + need ≥ $1.5K to be capital-efficient. Becomes viable around $5K. |
| **LRTs (weETH/rsETH/ezETH)** | Kelp DAO drained April 19; rsETH took 18% supply hit, Aave froze WETH on related bad debt. Major airdrops (EIGEN, ETHFI, REZ) already paid. Forward thesis is now restaking-without-airdrop-and-with-tail-risk-priced — bad R/R. |
| **MOVE (Movement)** | -99% from ATH, 1.1% of holders in profit, founder-fraud allegations, delisting risk ([CoinGecko MOVE](https://www.coingecko.com/en/coins/movement)). |
| **Plasma (XPL) before July 28** | 25% supply unlock to US public-sale buyers will distribute. Wait until post-unlock dust settles; entry could be much cheaper. |
| **Sei (SEI)** | Supply inflation 1.5-2%/month structurally bearish. |
| **Inscriptions / Runes / BRC-20** | Sector dead. Daily Runes tx fell from 750K peak to 150K. BTC fees alone wreck a $50 trade. |
| **Resolv (USR/RLP)** | $25M exploit March 22 2026 (unauthorized 50M USR mint). Avoid until trust mechanically restored. |
| **Hivemapper, Nosana** | Hivemapper has only 242 active contributors (fragile). Nosana orderbook 1-3% slippage at our size. |
| **MarginFi** | Outstanding team-trust issues, not resolved. |
| **Curve/Convex stable LPs** | Top APRs are on Ethereum L1 (gas-disqualified). Polygon Curve liquidity has degraded. |
| **Bittensor subnet SN3 Templar** | +444% / 30d but Covenant AI exit April 10 = operator/concentration risk. SN64 is the cleaner pick. |

## 7. Recommended portfolio ($50 total)

**Default (lean concentrated, 100% on-chain, zero CEX dependency):**
- **$30 → Ostium** on Arbitrum: $5-10 RWA-perp positions (5x leverage cap), volume-rotated for points
- **$15 → Limitless** on Base for active arb against Polymarket on identical markets (operated via a Polymarket↔Limitless spread-monitor script feeding Telegram)
- **$5 → gas + reserve** spread across Polygon / Arbitrum / Base

This split is the explicit minimum-operator-effort plan: every component is something Claude can deploy and manage from the existing wallet without further input. No CEX, no Subtensor wallet, no extra KYC.

**Optional add-ons (all on-chain, Claude can execute without operator input):**
- *+ $10 PLUME* directional buy on Plume DEX (RWA narrative beta). Default off because Tier-1 plays already cover the budget.
- *+ $3-5 MegaETH MEGA* on Apr 30 TGE if first-hour pricing leaves runway. Default off — fade FOMO unless operator explicitly opts in.

**Removed: TAO / Bittensor subnet alpha.** Original draft had this as Tier-1, then optional. With operator's no-CEX/no-KYC constraint (2026-04-27), the only on-chain funding rail is TaoFi (Bittensor EVM, $192K TVL → 5-15% slippage at $10) — not worth it. The diversified Bittensor exposure thesis remains valid; it is unreachable at our size under the decentralization constraint. Re-evaluate if a deeper on-chain TAO bridge or higher-TVL DEX wrapper appears.

**Yield-floor variant** (if operator wants ~half the capital in capital-preservation mode): swap $15 of Ostium for $15 in Pendle PT-sUSDe-Jun-2026 (Arbitrum, 4.31% APR locked, $0.30 yield over the 50-day window — small in absolute terms but smart-contract-clean). Activate this on operator request only.

## 8. What the operator actually does — and what Claude does

Operator's full task list:
1. **Send $50 USDC.e to the new crypto-sleeve wallet** `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` on Polygon. One on-chain transfer. (Greenlight already given by the same instruction; no separate "go" needed.)

That's it. No CEX work, no bridge UI clicks, no monitoring scripts to babysit, no manual rebalances. The new wallet was generated locally on 2026-04-27 with credentials stored in the gitignored secrets directory (mode 0o600), separate from the existing Polymarket wallet — operator's preference for clean ledger separation honored.

Claude's tasks (no further input needed after greenlight):
- Bridge $20-25 USDC → Arbitrum (Across), open Ostium account, deposit, ladder $5-10 RWA-perp positions (5x leverage cap, mixed long/short to avoid macro wipeout), cycle volume for points
- Bridge $15 USDC → Base (Across), fund Limitless, **build the Polymarket↔Limitless spread-monitor script** (4 hours of dev work, reuses existing news_watcher Telegram pipeline). Auto-cross when net-of-fee spread > 2%
- Maintain $5 in reserve gas across Polygon/Arbitrum/Base
- Track positions in `notes/positions_crypto.md` (parallel to existing Polymarket positions tracking), append journal entries on each material trade, weekly P&L summary in `notes/pnl_weekly.md` alongside Polymarket
- Cron-tick (existing 02:00 + 14:00 UTC schedule already covers this; no new infra) checks Ostium points balance, Limitless arb captures, Pendle PT mark (if applicable). Telegram-alert on > $5 PnL move or any liquidation risk
- 30-day review on 2026-05-27: aggregate points/PnL, decide rebalance
- Trigger conditions (memo §9) executed without further operator input — e.g., if Kelp-style hack hits Ostium, pull capital immediately

If at any point operator wants to redirect, change strategy, or claw back capital, a single Telegram message or tmux interaction is all that's needed.

## 9. Trigger conditions for revisiting

- **Bankroll grows to ≥ $200**: re-evaluate funding-rate basis trade and Hyperliquid HLP (size becomes capital-efficient).
- **Any of the recommended Tier 1 positions returns > 3x in < 30 days**: take 50% off and re-deploy half to next-best opportunity.
- **Major sector hack or de-rate (similar to Kelp / Drift / Resolv)**: immediately pull from any position in that protocol's correlation cluster.
- **MegaETH TGE goes badly (down > 50% day-1)**: that's a regime signal — assume primary-market sentiment is exhausted, lighten Tier 2 specs.
- **Ostium TGE actually drops**: capture the points-airdrop, then re-evaluate whether to re-deploy capital into the next farming cycle or take profit.
- **Polymarket POLY token launches** (CMO has confirmed it's coming, no date): the polyclaude project itself has accumulated farmable activity — separate consideration but strong upside.
- **BTC dominance < 50%** (currently 56-57%): altseason regime; tilt aggressive split toward TAO/PLUME/Akash and away from Pendle floor.
- **Reverse**: if BTC dominance > 62% or BTC < $65K, retreat toward Pendle/Aave floor — alts will bleed harder than the floor in a deeper drawdown.

## 10. Custody / wallet decision

**Decided 2026-04-27: new wallet for the crypto sleeve.** Operator confirmed full agency, including wallet generation. New keypair created locally on the VM via `eth_account.Account.create_with_mnemonic(num_words=12)`:

- **Address**: `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6`
- **Credentials**: stored in the gitignored secrets directory, mode 0o600, schema `{address, private_key, mnemonic}`. Path resolved at runtime via `scripts/_paths.py` from a non-committed env file — no filesystem path strings in the public source. See `strategy/02_operations.md` for the full path-resolution pattern.
- **Gitignore**: defensive patterns added (`wallet_crypto.json`, `*mnemonic*`) on top of the existing `wallet.json` exclusion

Existing polyclaude (Polymarket) wallet `0x9032…267B` is untouched. The two sleeves now have clean separation: distinct keypairs, distinct ledgers, distinct journal narratives. If at any point a strategy needs to move capital across sleeves, that's an explicit operator-or-Claude decision, not an accident.

## 11. What this audit explicitly does *not* recommend

- **No CEX funding-rate desk strategies**: too small + no margin headroom.
- **No NFT trading / sniping**: thin retail edge at $50.
- **No staking-as-yield on validators (POL, SOL, ETH spot)**: yield is < the operational drag at $50.
- **No automated MEV / liquidation hunting**: compute and infra disqualify us.
- **No options strategies (Lyra, Aevo)**: bid-ask + size minimums break the bankroll.
- **No yield-aggregator vaults (Yearn, Beefy, Idle)**: no rate edge over picking the underlying directly at our size.

## 12. Why I'm confident in this ranking

- The fee-structure analysis is the *same lens* that proved the polymarket-algo audit on April 26 — at small size, the fee/rebate math determines feasibility before strategy quality does.
- Tier 1 plays each have **a specific structural edge** retail at $50 can capture: Ostium = retroactive airdrop on a real product; SN64 = revenue-driven token; Limitless arb = liquidity-fragmentation between two real markets.
- Tier 3 rejections are quantitatively grounded (DD, fee, hack-event, supply-unlock) — not vibes.

## 13. Sources (deduped, all April 23-27 2026 unless noted)

**Market data:** [CoinMarketCap](https://coinmarketcap.com/), [CoinGecko](https://www.coingecko.com/), [DefiLlama protocols](https://api.llama.fi/protocols), [DefiLlama yields](https://yields.llama.fi/pools), [DefiLlama stablecoins](https://defillama.com/stablecoins), [Hyperliquid info API](https://api.hyperliquid.xyz/info).

**Yield protocols:** [Aave V3](https://app.aave.com/), [Pendle markets](https://app.pendle.finance/trade/markets), [Ethena USDe / sUSDe on CoinGecko](https://www.coingecko.com/en/coins/ethena-usde), [Across bridge](https://across.to/blog/polygon-bridge-guide-2025), [PolygonScan tx fee](https://polygonscan.com/chart/avg-txfee-usd), [Arbiscan gas tracker](https://arbiscan.io/gastracker), [CoinGlass funding](https://www.coinglass.com/FundingRate).

**Ostium specifics:** [ostium.com](https://www.ostium.com/), [Ostium Series A — The Block](https://www.theblock.co/post/381241/harvard-alumni-founded-ostium-lands-24-million-in-fresh-funding-to-scale-onchain-perpetuals-for-rwas), [Ostium TVL DefiLlama](https://defillama.com/protocol/ostium), [Ostium docs](https://ostium-labs.gitbook.io/ostium-docs).

**Bittensor specifics:** [Top 5 Bittensor Subnets dTAO — CoinGecko](https://www.coingecko.com/learn/top-bittensor-subnets-dtao), [Top 10 Bittensor Subnets — CoinPedia](https://coinpedia.org/news/top-10-bittensor-subnets-to-watch-as-tao-surges-90/), [Bittensor Ultimate Guide 2026 — tao.media](https://www.tao.media/the-ultimate-guide-to-bittensor-2026/), [TAO Bittensor — CoinDesk](https://www.coindesk.com/tech/2026/03/25/bittensor-ecosystem-tokens-value-hit-usd1-5-billion-as-jensen-huang-endorsement-supports-tao-rally), [Webopedia post-Covenant subnets](https://www.webopedia.com/news/markets/the-top-bittensor-subnets-after-the-covenant-ai-shakeup/).

**Limitless / prediction markets:** [Prediction Market Limitless Volume — Bitcoin Foundation](https://bitcoinfoundation.org/news/prediction-markets/prediction-market-limitless-volume-base/), [limitless.exchange](https://limitless.exchange/), [Marketplace on Kalshi/Polymarket perps](https://www.marketplace.org/story/2026/04/22/kalshi-polymarket-to-start-offering-perpetual-futures-markets).

**RWA / DePIN:** [Plume CoinMarketCap](https://coinmarketcap.com/currencies/plume/), [Plume RWA.xyz](https://app.rwa.xyz/networks/plume), [Solana DePIN March 2026 — Syndica](https://blog.syndica.io/deep-dive-solana-depin-march-2026/), [DePIN Sector 2026 — KuCoin](https://www.kucoin.com/blog/en-depin-crypto-sector-2026-how-decentralized-physical-infrastructure-surpassed-oracles).

**Hacks / risk:** [Kelp DAO $293M — CoinDesk](https://www.coindesk.com/tech/2026/04/19/2026-s-biggest-crypto-exploit-kelp-dao-hit-for-usd292-million-with-wrapped-ether-stranded-across-20-chains), [Drift $286M — Elliptic](https://www.elliptic.co/blog/drift-protocol-exploited-for-286-million-in-suspected-dprk-linked-attack), [Resolv $25M — Messari](https://messari.io/copilot/share/understanding-resolv-labs-usr-stablecoin-d5313b18-07c4-45a5-8597-54b70359b32f), [USDe Oct-2025 depeg — CoinDesk](https://www.coindesk.com/markets/2025/10/11/ethena-s-usde-briefly-loses-peg-during-usd19b-crypto-liquidation-cascade).

**Speculation / TGEs:** [MegaETH TGE Apr 30 — Crypto Briefing](https://cryptobriefing.com/megaeth-token-generation-event-set-for-april-30-2026/), [Backpack BP TGE — CoinDesk](https://www.coindesk.com/business/2026/03/23/backpack-launches-bp-token-on-solana-with-25-airdrop-no-insider-allocation), [pump.fun retail data — Bitget](https://www.bitget.com/news/detail/12560604161427), [pump.fun $2B daily Q1 — Yahoo](https://finance.yahoo.com/news/pump-fun-dex-volume-hits-132415661.html).

**Fed / macro:** [Federalreserve.gov FOMC March 18](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260128a.htm), [Polymarket FOMC April probabilities](https://polymarket.com/event/fed-decision-in-april), [BTC ETF flows April 2026 — 24/7 Wall St](https://247wallst.com/investing/2026/04/25/bitcoin-btc-spot-etfs-pulled-3-7b-over-8-weeks-after-4-months-of-outflows/), [BlackRock ETHB launch — FinTech Weekly](https://www.fintechweekly.com/news/blackrock-ibit-bitcoin-etf-inflows-ethb-staked-ethereum-nasdaq-march-2026), [SOL ETFs — Helius](https://www.helius.dev/blog/solana-etfs).
