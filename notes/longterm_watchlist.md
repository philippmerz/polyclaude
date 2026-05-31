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

## Verdicts (deepened 2026-05-08 ~21:00 UTC via `scripts/longterm_check.py`)

Ran the new tool on 10 candidates across crypto + equity. Full per-candidate reports in `notes/longterm_log.md`. Complete summary table:

### Crypto-native (polyclaude-accessible)

| Candidate | Score | Verdict | Entry trigger / next event |
|---|---|---|---|
| Solana ($SOL) | 3.5/4 | WATCH | $92 now / $110 breakout / $75-80 dip; Western Union USDPT consumer rollout Q2-Q3; Alpenglow Q3 |
| Arbitrum ($ARB) | 3/4 | WATCH | $0.12 now (50% conviction) / $0.09-0.10 dip / wait for March 2027 token-unlock completion (key inflection) |
| Optimism ($OP) | 2/4 | FOLLOW-UP | Below threshold; reassess mid-July post-vesting + Interop launch + Q2/Q3 sequencer revenue |
| Ondo ($ONDO) | WATCH | WATCH | $0.25-0.28 dip + fee-switch DAO vote H2 2026 (currently $0.44) |
| Centrifuge ($CFG) | 3.5/4 | WATCH | Post-Coinbase-catalyst stabilization; do NOT chase rally; RWA narrative intact |
| EigenLayer ($EIGEN) | 2.5/4 | FOLLOW-UP | Reassess Q3 2026 post-EigenDA scaling + first AVS fee metrics |
| Stacks ($STX) | 3/4 | WATCH | $0.18-0.22 dip OR proof of Bitcoin staking adoption Q2-Q3 2026 |

### Traditional equities (IBKR-only)

| Candidate | Score | Verdict | Entry trigger / next event |
|---|---|---|---|
| Micron ($MU) | 2/4 | WATCH | $450-520 entry (30-40% from current $743); Q4 FY2026/Q1 FY2027 AI-extension proof |
| Constellation ($CEG) | 2.75/4 | WATCH | $265-280 entry (12-15% from current $307) + TMI NRC milestone + PJM clarity Q4 2026 |
| Vistra ($VST) | 3/4 | WATCH | Escalate to ENTER if Cogentrix closes + H2 2026 deleverage; if 2027 guidance confirmed early 2027 → re-rate to $210-230 |
| Palantir ($PLTR) | 3.5/4 | WATCH | $110-120 entry (20-30% pullback); 111x forward PE current with $6B insider selling = bad R/R now |

### Crypto-perps venues (operational DD vs token thesis)

| Candidate | Score | Verdict | Note |
|---|---|---|---|
| Drift ($DRIFT) | 3/4 FOLLOW-UP | NOT DEPLOYABLE NOW | $286M DPRK-linked exploit April 1 2026; deposits/withdrawals SUSPENDED; relaunch May-June 2026 with Tether $148M recovery fund. Reassess June 15 post-relaunch with TVL re-entry data. |
| Hyperliquid ($HYPE) | 2.5/4 WATCH | $20-25 entry vs current $42.86 | Top perps DEX (44-70% share). Launched HIP-4 zero-fee outcome markets targeting Polymarket. NOT NOW: mid-cycle pullback, supply overhang (54% locked through Dec 2027), high P/S 29-88x, regulatory tail risk. Wait for cycle reset OR HIP-4 traction proof OR ETF approval. |

**Operational venue conclusion (2026-05-08): NO new perps venue setup warranted today.** Drift is post-exploit non-deployable; Hyperliquid is mid-cycle without margin of safety. Continue with existing venues (Polymarket + Ostium + Aave). HIP-4 (Hyperliquid's outcome markets) is a Polymarket-arb angle worth monitoring — same markets with potentially different prices. Backlog: extend limitless_arb_scan.py pattern to scan Hyperliquid HIP-4 vs Polymarket.

**Pending in next batch (less obvious / wider net needed):** SK Hynix, Western Digital ($WDC), GE Vernova ($GEV), Babylon ($BABY), Wolfspeed (compound semis), Anduril/Kratos/AeroVironment (defense-tech), Rocket Lab/AST SpaceMobile (space economy), DeFi blue chips at depressed multiples (UNI, AAVE, MKR), BTC-mining infra.

### Sunday 2026-05-10 weekly digest additions (geopolitics-security + energy-power-infrastructure)

| Candidate | Score | Verdict | Theme | Entry trigger |
|---|---|---|---|---|
| Exxon Mobil ($XOM) | 2/4 | PASS at \$144 | Oil Supply Shock (Hormuz closed, OPEC+ damaged) | \$110-125 on Q2/Q3 earnings disappointment OR oil correction; \$90-100 generational |
| Cameco ($CCJ) | 3.5/4 | WATCH at \$116-123 | Advanced Nuclear (DOE Jul 4 deadline, TerraPower, AI data centers) | \$100-110 on 20% pullback OR spot uranium >\$95/lb + Q2 beat |

**Other digest themes (not run via longterm_check yet):**
- LNG Export Leverage (MED conf): Cheniere ($LNG), Sempra ($SDG), Star Bulk ($SBLK), Golden Pass benefit. Multi-year repricing on Hormuz closure.
- Data Center Power Bottleneck (MED conf): Duke ($DUK), NextEra ($NEE), AEP, Emerson ($EMR), Eaton (\$ETN). FERC interconnection reform + Virginia demand spike.

Plus Oil Supply Shock alternatives: Chevron ($CVX), Marathon ($MPC), Phillips66 ($PSX). And uranium alternatives: Uranium Energy ($UEC), Energy Fuels ($UUUU).

Run longterm_check on alternatives in subsequent weekly reviews.

### Artifact-derived candidates (added 2026-05-08 ~21:30 UTC)

User shared a research artifact distilling underreported geopolitical phenomena + nth-order effects + mispriced asset implications (FORGE/Pax Silica critical-minerals pact, Eastern DRC tin squeeze, Sodium-ion battery deployment, SMR pipelines, Legacy pollutant remobilization, GLP-1 food demand reset, BBNJ ocean treaty Jan 2026, Perovskite-silicon tandem, BIOSECURE Act biotech decoupling, Room-temp quantum + AI seismic). Framework: identify low-visibility-but-high-impact themes → derive nth-order consequences → extract mispriced equities. Strong intellectual artifact — surfaced non-obvious sub-categories that pure ticker scans miss.

Ran longterm_check on 5 novel actionable candidates (1 batched VIE timed out, retry separately):

| Candidate | Score | Verdict | Theme | Entry trigger |
|---|---|---|---|---|
| Alphamin Resources ($AFMJF / AFM.V) | **4/4** | WATCH | DRC tin (Eastern DRC squeeze) | $0.75-0.85 dip OR sustained 18k+ tonnes Q3 (+ stable security) |
| Centrus Energy ($LEU) | 3/4 | WATCH | HALEU enrichment (SMR fuel monopoly) | 10-15% dip from $203 OR DOE Phase III contract Q2-Q3 2026 |
| Twist Biosciences ($TWST) | 3.25/4 | WATCH | Gene synthesis (BIOSECURE onshore) | $42-48 entry OR post-Q4-FY2026 EBITDA-breakeven beat |
| Ivanhoe Mines ($IVN.TO) | 3/4 | WATCH | Non-CN copper (FORGE/Pax Silica jurisdictional premium) | CAD 8-9 dip OR Kamoa production targets confirm post-seismic |
| Albemarle ($ALB) | 3/4 | **WATCH (closest to ENTER)** | Lithium cycle bottom + storage thesis | "Currently at entry-trigger price IF storage thesis durability believed"; accumulate <$180 on weakness; full-conviction on H2 2026 BESS data |

**ALB stands out** — verdict reads "currently at entry-trigger price IF [thesis] is believed" + "accumulate on any weakness below $180." Closest thing to ENTER NOW across all 17 candidates analyzed today. The lithium-cycle-bottom + sodium-ion-substitution-overpriced thesis converges with storage-deployment secular tailwind. Worth specific attention.

**AFMJF is the highest-scoring (4/4)** but still WATCH because of recent 27% rally pricing in some of the squeeze. DRC-tin thesis intact; entry at $0.75-0.85 dip.

**Framework verdict.** The artifact-driven seed-extraction adds genuine value. The nth-order consequence chains surface candidates the canonical-list scan misses (BIOSECURE onshore = TWST; DRC tin + Western JVs = AFMJF; HALEU monopoly vs broad nuclear = LEU). However, even with these novel candidates, the SanDisk PATTERN holds: visible mispricings today are mid-cycle, not bottom — all 5 require dip or catalyst confirmation. **Continue using the framework methodology** (artifact → ticker extraction → longterm_check verdict) as a recurring weekly process; it's compounding.

**Pattern reinforced across all 10 surveyed candidates: NONE triggered ENTER NOW.** The SanDisk PATTERN is real and the framework correctly identifies analogous candidates, but the SanDisk MOMENT — bottom-of-cycle entry — has passed across the visible candidate set. Specifically:

- **Memory/storage cycle** (Micron 62x P/E peak-cycle euphoria) → already had its run.
- **AI-power infrastructure** (CEG / VST) → mid-thesis, needs catalyst clarity + margin of safety dip.
- **AI software / defense** (PLTR 111x forward PE + $6B insider selling) → too rich.
- **Crypto L1/L2 ecosystem** (SOL / ARB / OP / STX) → at WATCH for specific entry triggers (price levels OR token-unlock completions OR catalyst execution proof).
- **Crypto RWA** (ONDO / CFG) → at WATCH for catalyst confirmation + pullback. Don't chase.
- **Crypto restaking** (EIGEN) → premature, fee economics not proven yet.

**Translation.** The user's directive was timely (start hunting for the NEXT generational opportunity), but the visible candidates today are POST-bottom or PRE-catalyst. Discipline = wait for trigger conditions; don't force entry on already-visible names. **The next batch needs to widen the net** to less-obvious categories (specialty semis outside memory: SiC / advanced packaging; lithium cycle bottom: ALB; defense-tech sub-sectors: KTOS / AVAV; space economy: RKLB / ASTS; DeFi blue chips at depressed multiples: UNI / AAVE / MKR; BTC mining infra: CIFR / HUT).

**Operational implication for polyclaude.** No immediate capital deployment from the long-term axis warranted today. The watchlist becomes a set of **price-trigger / event-trigger alerts** to monitor. When SOL hits $80 OR ARB unlock completes (March 2027) OR ONDO dips to $0.28 OR Micron retests $500 OR PLTR pulls back 20-30% — that's when conviction-sized entries make sense.

**Mechanism for monitoring.** Need a script `scripts/watchlist_monitor.py` that checks current prices on watchlist names and flags any that have hit entry triggers. Wire into cron tick step 3. Bounded ~50 LOC. Backlog-worthy.

## Last updated

2026-05-08 ~21:00 UTC — first analytical pass across 6 seeds via longterm_check.py. Tool validated end-to-end: produces structured 4-dimensional thesis with entry triggers + scenario probabilities + sources. All current verdicts: WATCH or FOLLOW-UP, none ENTER NOW. Hunt continues for less-obvious convergences.

### Sunday 2026-05-17 weekly digest additions (tech-ai-chips + macro-fiscal-labor)

| Candidate | Score | Verdict | Theme | Entry trigger |
|---|---|---|---|---|
| NVIDIA ($NVDA) | 3/4 | WATCH at \$224 | AI Capex Plateauing | \$180-200 weakness OR post-Q3 2026 capex slowdown confirmation OR May 20 earnings catalyst |
| iShares 20+Y Treasury ($TLT) | 1/4 | PASS at \$83.66 | (digest theme: SHORT direction) | LONG only if 10-yr yields panic-spike to 5.0%+ AND Fed pivots; otherwise hold cash / IEF / SHY |

**Other digest themes (not run via longterm_check yet):**
- Inflation Resurgent + CB Divergence (HIGH conf): CPI 3.8% (+50bps), Fed dissent 8-4, ECB hike discussion, BoJ split 6-3. SHORT-duration / LONG-yield. Plays: TBT, short TLT puts. Digest claim validated by TLT 1/4 PASS verdict (long-TLT thesis fails).
- Real Wage Erosion → Demand Cliff (MED): real wages -0.3% YoY. SHORT consumer discretionary (XLY, Tesla).
- GDP Stalling + Fiscal Drag (MED): Q1 2026 GDP +2.0% miss. SHORT growth equities (QQQ, ARKK).

Plus AMD as alternative AI exposure (less leverage to capex peak); SOXL inverse if SMH short thesis confirms via NVDA May 20 earnings.

Last weekly: 2026-05-10 (geopolitics + energy-power). Next weekly: 2026-05-24 (rotate to remaining: trade-regulation, biotech-health, crypto-on-chain, markets-corporate).

### Sunday 2026-05-24 weekly digest additions (biotech-health + crypto-on-chain)

| Candidate | Score | Verdict | Theme | Entry trigger |
|---|---|---|---|---|
| Eli Lilly ($LLY) | 1.5/4 | **PASS** at ATH | GLP-1 Oral Expansion (HIGH conf) | \$745-800 (52w low + discount) OR event entry on Mounjaro share<50% / retatrutide P3 fail |
| EigenLayer (EIGEN) | 3/4 | WATCH at \$0.227 | Restaking Dominance (HIGH conf) | \$0.12-0.16 post-June-1-unlock washout (3-4% position, stop \$0.10) |

**Other digest themes (not run via longterm_check yet):**
- Base L2 Winner-Take-Most (HIGH conf): Base TVL 3x in 4mo, Arbitrum+Base = 77% of L2 liquidity. Plays: Long COIN (Base ecosystem), Underweight ARB. ARB already in watchlist at \$0.10 entry; consider rebalance away if both exist in IBKR sleeve.
- Boehringer Ingelheim PDE4B (MED conf): Jascayd first-in-class IPF treatment in 10+ years. Play: BFVAF (OTC), hard to size given liquidity.

Last weekly: 2026-05-17 (tech-ai-chips + macro-fiscal-labor). Next weekly: 2026-05-31 — Saturday — likely won't fire on the May-31-NO-resolution day; consider 06-01 manual sweep.

### Sunday 2026-05-31 weekly digest (trade-regulation + markets-corporate)

5 themes, none HIGH-conf — and notably most are SHORT/sector-rotation/tactical (IBKR-discretion ideas, not generational-LONG candidates):
- **Oil Repricing (MED-HIGH):** Brent $120→$92.56 (-20%); war premium repricing out. Short energy-intensive industrials (airlines ALK/DAL/LUV, chemicals DD/APD/ECL, fertilizer CF/MOS); long renewables (NEE/ICLN). Tactical, Jun-Sept.
- **Semi Equipment grace-period (MED):** export-control grace through Dec 31 + AI capex. AMAT/LRCX/ASML long into the window, China-exposure risk post-Dec. → LRCX vetted: **2.5/4 WATCH @ $318**, entry $250-280.
- **USMCA auto RoO (LOW-MED):** rules-of-origin tightening; short F/GM/STLA Mexico exposure. Forward-looking, specifics unknown.
- **Pharma MFN pricing erosion (MED):** $35-40B branded-pharma revenue cut; short JNJ/PFE/MRK/ABBV, long generics/PBMs.
- **China ag commitments (LOW-MED):** $17B/yr purchases; long ADM/BUNGE (consensus-priced) + niche ag-input names.

| Candidate | Score | Verdict | Entry |
|---|---|---|---|
| Lam Research ($LRCX) | 2.5/4 | WATCH @ $318 | $250-280 (25-30x fwd P/E) OR capex-guidance miss |

LRCX added to watchlist_triggers ($280). The short/tactical themes are surfaced for operator IBKR discretion — they don't fit the generational-LONG longterm_check framework and aren't polyclaude-deployable.

Pattern: 8 candidates vetted across the weekly rotations, 7 returned PASS/WATCH at current prices (only none ENTER). Valuations broadly stretched cyclewide; discipline holds.

Next weekly: 2026-06-07 — rotate to the oldest-run slugs (critical-minerals 5-08, geopolitics/energy 5-10).
