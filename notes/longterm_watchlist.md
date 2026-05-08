# Polyclaude Long-Term Watchlist

> Living document for multi-year (~1-5y) generational-mispricing candidates. Created 2026-05-08 in response to user directive: scan and analyze across stocks / crypto / other categories; invest from polyclaude where accessible; surface IBKR-side candidates for user's personal sleeve.
>
> Reference pattern: SanDisk 2023-2025 — memory-cycle bottom + AI-compute secular demand + Western-Digital-spinoff catalyst + margin of safety = generational return. Hunt for analogous convergences elsewhere.

## Operating model

**Cadence.** Weekly review (Sunday cron extension or manual sweep). Add/update candidates with fresh thesis. Monthly: prune stale entries. Quarterly: realized-vs-prediction calibration check.

**Selection framework.** A "generational mispricing" candidate scores on FOUR dimensions; need at least 3 of 4 strongly:

1. **Cyclical position.** Asset is at or near a multi-year bottom (e.g., post-glut/post-bear). Avoid mid-cycle / euphoria.
2. **Secular tailwind.** Multi-year demand driver that markets haven't fully priced (e.g., AI compute, on-chain RWA, energy transition).
3. **Specific catalyst within window.** Identifiable event (product cycle, mainnet launch, regulatory shift, spinoff, M&A) that forces a re-rating.
4. **Margin of safety.** Downside is bounded — strong balance sheet, profitable already, low debt, hard-asset backing, or low-multiple entry. Generational doesn't mean YOLO.

**Decision criteria (polyclaude-accessible candidates).**
- Position size per name: ~5-10% of allocated long-term sleeve (TBD; not yet allocated).
- Time horizon: 1-5 years.
- Exit triggers: thesis broken (catalyst missed, secular driver evaporates), or +3-5x reached, or capital better deployed elsewhere.

**For IBKR-side candidates.** Surface to user via Telegram + this doc. Include: entry price reference, thesis (3 sentences), catalyst timeline, exit triggers, downside scenario.

## Accessibility map

Polyclaude wallets can deploy directly to:
- **Crypto-native tokens** on Polygon/Arbitrum/Base/Optimism/Ethereum (anything Uniswap-V3-listed with reasonable liquidity)
- **Solana ecosystem** (would need new wallet — not currently set up)
- **Tokenized real-world assets** via Backed Finance (bSPY, bCSPX on Polygon/Base/Gnosis), dShares (USDC.e-quoted on Arbitrum), Centrifuge RWA pools

NOT directly accessible without manual user intervention:
- **Traditional equities** (NYSE/NASDAQ): user's IBKR sleeve only
- **OTC pink sheets**: same
- **Private placements / pre-IPO**: same
- **Specific commodity futures**: Ostium covers gold/SPX/NDX; not e.g. uranium, lithium

**Tokenized-equity caveats.** Backed/dShares wrappers carry counterparty risk (the issuer must hold the underlying). Liquidity is thin. Spreads can be 0.5-2%. For long-term holds these are tolerable, but verify accessibility + book depth before committing capital.

---

## Active candidates

### Crypto-native (polyclaude-accessible)

> Initial scan from parametric knowledge through Jan 2026 + recent web context. Each entry needs catalyst-check + book-walk before any actual entry. These are RESEARCH SEEDS not buy lists.

#### A. **Solana ($SOL)** — Layer-1 ecosystem cyclical+secular convergence
- **Cyclical:** Major drawdown 2022 → recovery 2023-2024 → consolidation 2025. If 2026 brings DePIN + mobile-payments breakout, parabolic potential.
- **Secular:** On-chain transaction volume leadership; consumer-grade UX; integration with mobile (Saga) and Pokt-like infrastructure.
- **Catalyst:** Firedancer mainnet (validator-client diversity, TPS scaling), Solana Mobile Saga 2 wider rollout, native USDC on Solana adoption growth.
- **Margin of safety:** High network revenue / fee burn; institutional adoption (Visa, Shopify); TVL near multi-year highs.
- **Polyclaude access:** Wrapped SOL on Ethereum / Polygon (lower liquidity); native SOL would require new Solana wallet setup. **Defer until I set up Solana sleeve OR use wrapped via Wormhole/Allbridge.**

#### B. **Layer-2 ETH-native picks** — Arbitrum ($ARB), Optimism ($OP), Base ecosystem
- **Cyclical:** ETH-L2 tokens crashed 2024-2025 post-airdrop unwinds; bottoming pattern.
- **Secular:** ETH scaling thesis, growing DeFi + NFT-on-L2 + onchain consumer-app TVL.
- **Catalyst:** EIP-4844 already live; next wave is enshrined-rollups research, app-specific L3s, cross-L2 unified liquidity.
- **Margin of safety:** L2 fees + sequencer revenue accruing; ARB DAO has $3B+ treasury; OP has Optimism Foundation backing + ENS partnership.
- **Polyclaude access:** ARB/OP tradeable on Uniswap V3 Arbitrum/Optimism. **HIGH accessibility.** Worth catalyst-checking.

#### C. **Restaking ecosystem** — EigenLayer ($EIGEN), restaked-ETH derivatives
- **Cyclical:** EIGEN airdrop saw post-launch volatility; restaking TVL plateaued 2025.
- **Secular:** Modular blockchain thesis — AVS layer needs restaked security; growing AVS count.
- **Catalyst:** EigenDA + rollups using restaking; first major slashing event (test of thesis).
- **Margin of safety:** Lockup mechanics keep float low; institutional involvement (a16z, Polychain).
- **Polyclaude access:** EIGEN on Uniswap-V3 Ethereum mainnet (high gas) + Arbitrum bridge. Medium accessibility.

#### D. **Bitcoin Layer-2s** — Stacks ($STX), Bitlayer, Babylon ($BABY)
- **Cyclical:** BTC-L2s lagged main BTC run 2024; sector mid-bear.
- **Secular:** "Make BTC programmable" thesis; ordinals/runes momentum; institutional BTC yield demand.
- **Catalyst:** Babylon mainnet activation, Stacks Nakamoto upgrade unlock.
- **Margin of safety:** STX has ~$2B mcap, treasury, real BTC-pegging mechanism.
- **Polyclaude access:** STX on most CEXs but limited DEX presence on EVM; Babylon native chain. Medium accessibility.

#### E. **Real-world assets (RWA) infrastructure** — Centrifuge ($CFG), Ondo ($ONDO), Maple ($MPL)
- **Cyclical:** RWA tokens consolidated 2024-2025; real on-chain volume growing.
- **Secular:** Tokenized treasuries ($BUIDL, $USDY) growing TVL; institutional adoption.
- **Catalyst:** SEC stance softening under current admin; tokenized stock launches; tokenized REIT pilots.
- **Margin of safety:** Real cash flows + treasury holdings backing protocols; Ondo has BlackRock partnership.
- **Polyclaude access:** ONDO + CFG on Uniswap V3 Ethereum + bridges. High accessibility.

### Tokenized equities (partial polyclaude access, full IBKR access)

These wrap traditional equities on EVM chains. Useful to bridge polyclaude exposure to specific traditional names, with caveats (counterparty + liquidity).

Backed Finance issues `b<TICKER>` tokens redeemable for underlying:
- **bSPY** (S&P 500): broad-market exposure on Polygon/Base
- **bCSPX** (Core S&P 500 ETF): same exposure cheaper TER
- **bNVDA** (Nvidia): individual mega-cap
- **bTSLA**: liquidity varies

Use these sparingly — they're for SPECIFIC long-term theses, not blanket diversification (just hold USDC + Aave for that).

### Traditional equities (IBKR only — surface to user)

> Each candidate gets a full memo: thesis (3 sentences), catalyst, timeline, exit triggers, downside scenario.

#### Reference: **SanDisk** (the seed example)
- Memory-cycle bottom 2023 + AI compute demand → 2024-2025 generational run. Pattern: cyclical + secular + catalyst convergence with strong balance sheet entry.

#### F. **Memory + storage adjacent** (similar pattern to SanDisk)
- **Micron ($MU)**: HBM3e leadership; CapEx cycle peaked 2024; AI-server demand secular.
- **SK Hynix** (Korea-listed): same HBM thesis; ADR access via 000660 OTC.
- **Western Digital** ($WDC) post-spinoff: storage-cycle play.

Status: parametric knowledge through Jan 2026; needs fresh catalyst-check for current valuations.

#### G. **Power infrastructure for AI compute** — secular tailwind
- **Constellation Energy ($CEG)**: nuclear baseload provider; multi-year datacenter PPAs.
- **Vistra ($VST)**: similar nuclear + gas peakers.
- **GE Vernova ($GEV)**: gas turbines + grid.
- Margin of safety: regulated cash flows + AI-driven demand inflection.

Status: needs fresh research; SanDisk-pattern fit is medium (secular driver clear, cyclical position less obvious).

#### H. **Defense + dual-use tech**
- **Palantir ($PLTR)**: gov + commercial AI ops; thesis hinges on continued Trump-admin contract flow.
- **Anduril** (private; tracks via secondaries / specific funds).
- **Booz Allen ($BAH)**: defense-IT services.

Status: speculative; thesis depends on geopolitical cycle.

---

## Backlog (research items)

- **Solana wallet setup**: enables direct SOL access if multi-year SOL thesis confirmed. ~1h setup. Currently low priority — wrapped-SOL on EVM is a workaround.
- **Tokenized-equity book-walk**: verify book depth on bSPY / bCSPX / bNVDA before any entry. Liquidity could be 5-10x worse than displayed.
- **Catalyst-check pipeline extension**: `catalyst_check.py` currently targets event-driven Polymarket questions with explicit resolution criteria. For long-term equity/crypto, the framework needs adaptation — there's no "resolution date" or oracle, just a multi-year hold horizon. May need a separate script `longterm_thesis_check.py` that queries 1-3-5y outlook + downside scenarios + analogous-historical-cases.
- **IBKR sleeve interface**: how do I surface candidates? Live doc + Telegram alerts on thesis-significant news. User executes manually.

## Last updated

2026-05-08 — initial bootstrap. Seed candidates are RESEARCH SEEDS not buy lists. Each candidate needs fresh catalyst-check + accessibility verification before any real-money commitment.
