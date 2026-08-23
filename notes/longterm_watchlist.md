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

### Sunday 2026-06-07 weekly digest (critical-minerals + energy-power + geopolitics-security)

Rotated to the 3 stalest domains (critical-minerals 5-08, energy/geopolitics 5-10), confirmed via git history. HIGH/MED themes:
- **Copper structural deficit (HIGH):** ICSG first refined-copper deficit since 2009 (El Teniente depression + Grasberg -35%) vs AI/EV demand, yet LME copper *falling into* the shortage. Plays: FCX, COPX, TECK.
- **Uranium structural undervaluation (HIGH):** ~67kt demand vs ~55-65kt production deficit; AI-datacenter nuclear race + US enrichment buildout. Plays: CCJ, URA/URNM, SPUT.
- **Oil supply shock / Hormuz (HIGH):** Strait blocked since Feb 28 (15.8 mbpd stranded), accelerating US draws, Brent ~$106 underpricing a supply response that physically can't materialize in months. Plays: CVX/COP/EOG (XOM already tracked @ $125).
- **Memory-chip undersupply 2+yr (HIGH):** DRAM prices doubled since early-2025 as Samsung/SK Hynix/Micron reallocate to AI/HBM; smartphone/PC bottleneck persists to 2027. Plays: long MU (tracked @ $520); short consumer-electronics (AAPL/DELL/HPQ).
- **Lithium tightening (MED-HIGH):** interim 2026-2029 tightness mispriced as onshoring capacity is 3-5y away. Plays: ALB (tracked @ $150), LIT.

| Candidate | Score | Verdict | Entry trigger |
|---|---|---|---|
| Cameco ($CCJ) | **4/4** (↑ from 3.5/4 on 5-10) | WATCH | $95-100 (uranium → $75-80/lb) OR aggressive $75-85 if spot <$70; current **$114 = FAIR, don't scale**. Thesis strengthened: McArthur River full production Jun-26, 1.9Blb deficit to 2045, 49% Westinghouse optionality. (trigger already set @ $95) |
| Freeport ($FCX) | 2.5/4 | PASS (NEW) | $40-45 (copper normalizes $10.5-11k/MT → 20-25x P/E) OR $50-55 macro pullback. At record/peak now ($63.27, 44.6x P/E, no cushion). **Added to watchlist_triggers @ $45.** |

Trigger-hits this week (existing, all route=ibkr_surface): SOL $64.85, ARB $0.082, STX $0.186, EIGEN $0.176 — all ≤ entry-max; EIGEN still mid-washout post-Jun-1 unlock (wait). These are surfaced for the operator's IBKR sleeve, not polyclaude capital.

Pattern holds: 12+ candidates vetted across rotations, all PASS/WATCH at current prices — valuations broadly stretched cyclewide. The HIGH themes (copper/uranium/oil/memory) are real multi-year stories, but the equities are mid/late-cycle, not bottoms. Discipline: wait for the dip triggers; no chasing at peak.

Next weekly: 2026-06-14 — rotate to the now-stalest (macro-fiscal-labor + tech-ai-chips last ran 5-17; biotech-health + crypto-on-chain 5-24). Pick the 2-3 oldest then.

### 2026-06-09 trigger hit: ALB (Albemarle / lithium) — re-vetted 3.5/4 WATCH

ALB hit its $140-150 entry band at $149.84 (after a ~13% weekly drop from $171.77). Fresh longterm_check UPGRADED it 3/4 → **3.5/4 WATCH**: margin-of-safety upgraded WEAK→OK (net debt $3.2B→$1.9B, 1.0x leverage, $2.7B liquidity, fwd P/E 13.6x), and the crux **$20+/kg lithium-pricing condition is now MET** (~$20-26/kg LCE; Q1-26 EPS $2.95 +127% beat, surplus→deficit 2026). Both revised-entry conditions (price $140-150 AND $20+/kg) satisfied → entry-eligible for a **STARTER tranche** on the operator's IBKR sleeve at the favorable low end of the band; reserve full size for spot >$22/kg or an ESS-capex/2027-estimate catalyst. Downside: lithium reverts $12-15/kg → 60-70% EBITDA cut (~5% thesis-broken, fortress B/S). Surfaced to operator (msg 434). watchlist_triggers entry_max lowered 150→140 to re-alert on the add-lower tranche. IBKR-route, no polyclaude capital.

## 2026-06-21 weekly digest (domains: macro-fiscal-labor, tech-ai-chips, crypto-on-chain)

Run during outage-recovery (creds had expired ~43h). Themes surfaced, all IBKR-SURFACE (operator's
equity/macro sleeve — none are polyclaude-PM-actionable or <1y-crypto-EVM):
- **Inflation stickiness / Fed policy-error (HIGH conf):** CPI 4.2% YoY (3yr high), core 2.9%; Fed held
  Jun-17 at 3.50-3.75%, ECB+BoJ hiking. Play = SHORT long-duration (TLT), bull steepener. Horizon 3-6mo.
  Standout theme. → operator IBKR.
- **Semi-equipment overcapacity (MED):** NVIDIA zero China Hopper, "diversification" masking demand
  composition; TSMC $56B capex bet; SEMI billings +14%YoY but +1%QoQ (decel). Play = SHORT semi-equip
  (ASML/LRCX) vs NVDA. → operator IBKR (note: contradicts our memory-shortage CCJ-adjacent long thesis;
  watch for confirmation either way).
- **Dollar strength / EM stress (MED-HIGH):** Fed-divergence → LONG USD, SHORT EM/CNY. China H1 GDP
  mid-July is the catalyst. → operator IBKR.
- **Crypto risk-off (MED):** BTC -21%/4wk, spot-ETF outflows $402M May; trading as risk-on not inflation
  hedge. CONTEXT for our book (no action — no decentralized short venue, don't hold spot as thesis). Note:
  mildly supports keeping idle capital in Aave/stables vs deploying into crypto-beta now.

PM-actionable check (our lane): digest flagged "Fed July hike underpriced vs pause narrative" — FALSE on
live Polymarket prices: market already prices July-hike 17.5% / 2026-hike 61.5% (NOT a pause narrative).
No mispricing to fade; Fed legs are anti-edge regardless. No polyclaude entry. Discipline win: checked the
digest's market-state assumption against live prices rather than trusting it.

## 2026-06-28 weekly digest (domains: biotech-health, trade-regulation, markets-corporate)

Themes (most plays are SHORTs → NOT polyclaude-actionable, no decentralized short venue; the LONG plays are equities → operator IBKR):
- **Rare-earth / export-control reshoring (MED-HIGH):** Annex-C export controls + structural REE supply constraint. Play = LONG rare earth. → **MP Materials = the standout (below).**
- **Long-duration → short-duration rotation (MED-HIGH):** SHORT long-duration biotech (2026 IPOs) / LONG short-duration + high-dividend (utilities, staples). SHORT side not actionable; LONG defensive side diffuse (no single high-conviction ticker).
- **GLP-1 / mature-pharma maturation (MED):** SHORT Novo/Lilly (long-term) / LONG generics (Teva, Sandoz, Viatris). → Teva vetted (below).
- **Energy short on Iran-deal closure (MED):** SHORT energy equities / oil puts, conditional on deal closure. Not actionable (short + uncertain timing; our own Iran NO legs are the live exposure to this theme).

longterm_check verdicts:

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **MP Materials ($MP)** | **3.5/4** | **ENTER NOW** | Rare-earth reshoring | Pentagon-backed ($400M equity + $150M loans + 10X off-take); structural REE constraint; sequenced catalysts (Dy/Tb H2-2026 → Apple 2027 → 10X 2028); 3-5x base / 5-20% max DD over 3yr; size 3-4%. Alt entry: dip <$45 OR H2-26 Dy/Tb commissioning proof. **→ SURFACED to operator (IBKR); the first ENTER-NOW verdict since the watchlist began (all prior = WATCH/FOLLOW-UP).** |
| Teva ($TEVA) | 2.75/4 | FOLLOW-UP | GLP-1/generics maturation | Rallied 94% YoY ($31.48), catalysts (Olanzapine LAI FDA late-2026) priced in, 265% D/E = weak margin of safety. Entry $25-27 dip. WATCH → IBKR. |

Existing trigger-hits this week (watchlist_monitor, all IBKR-surface, previously surfaced — no new action): SOL $70.85 (≤$80), STX $0.169 (≤$0.22), PLTR $112.93 (≤$120), ALB $133.70 (≤$140), NVDA $192.53 (≤$200).

**Net:** MP Materials is the actionable output — a 3.5/4 ENTER-NOW Pentagon-backed rare-earth play surfaced to the operator's IBKR sleeve. No polyclaude (<1y, decentralized) entry warranted — all candidates are multi-year equities. Digest's own next-steps (Bitcoin, pharma-M&A, Ebola) all self-flagged "wait/not-yet."

## 2026-07-05 weekly digest (domains: critical-minerals-commodities, energy-power-infrastructure, geopolitics-security)

Themes: **grid-stress/coal-capacity (MED)** — PJM drawing emergency reserves in summer heat + DOE $350M coal restart program → capacity pricing upside for grid-heavy names; retail blindspot = ESG bearishness vs real near-term stress. Cobalt (LOW, pass — deficit priced). Digest also suggests a lithium SHORT on supply additions — **tension note for the ALB long thesis** (ALB's entry condition is lithium >$20/kg holding; a supply-driven fade below that breaks it — watch spot at the ALB re-checks).

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **CEG (re-vet — TRIGGER FIRED @ $239.25)** | **3.5/4** | WATCH | AI-power/nuclear + grid-stress | Down 42% to fair (13.3x EV/EBITDA); secular STRONG, catalysts HIGH (TMI/FERC Q4-26). Wait: **$220-230 dip OR Q4 TMI-waiver clarity**. entry_max 250→230. Surfaced. |
| AEP (new) | 2.5/4 | WATCH | Grid capex / capacity pricing | $138.45 = 52wk high, mid-cycle. Entry $120-125 pullback OR >60GW load-pipeline + rate-case wins. |

Trigger-state changes: **SOL recovered ABOVE its $80 trigger ($81.32, +15% off the Jun-28 low — un-hit naturally)**; PLTR exited the hit list (>$120). Persistent hits (previously surfaced, unchanged): STX $0.17, ALB $135.56, NVDA $194.83. Coal producers (ARCH/BTU) skipped: structurally-declining upside cap per the digest's own confidence note; AEP is the cleaner expression. Crude/nickel futures plays inaccessible (no decentralized venue).

## 2026-07-12 weekly digest (domains: macro-fiscal-labor, tech-ai-chips, crypto-on-chain)

Themes — all already-tracked, directional-beta, or not-at-trigger; NO new polyclaude-actionable candidate:
- **Crypto capitulation-bottom → LONG BTC/ETH (MED-HIGH):** strongest theme, but directional crypto BETA, not our instance-mispricing edge; we don't hold spot as a thesis (no decentralized short venue to pair). Our ARB (+30%) is already the crypto-L2 expression. Operator's IBKR/personal call if they want BTC/ETH beta.
- **RWA institutional yield (MED) → LONG RWA protocols / stablecoin yield:** ONDO is the flagship + on-EVM, but $0.328 vs its $0.28 trigger (NOT hit) and 2-5y IBKR-route. The "stablecoin yield" sub-angle is what our Aave reserve already captures. No entry.
- **EUR carry unwind (MED) → SHORT EUR / LONG USD:** not actionable (forex, no venue, directional).
- Digest's own note: themes A/B/D/E/F already in this watchlist (NVDA/semis/crypto-L1L2/RWA). Confirmed.

Trigger-state changes (all IBKR-surface, previously surfaced): **SOL re-dipped below $80 ($77.41)** (was above last wk); STX $0.173 persistent; **ALB $126.05 (−7% from last wk's $135.56), nearing the deep-conviction $120 zone** — BUT flag: last week's digest saw lithium supply-additions pressure, and ALB's entry thesis needs lithium >$20/kg; a supply-driven fade below that would make "cheaper" = "thesis-ERODING," not a better entry. Operator: weigh the lithium spot before treating the ALB dip as an add. CEG/NVDA/PLTR off the hit-list.

## 2026-07-19 weekly digest (domains: biotech-health, trade-regulation, markets-corporate)

Themes — one new candidate vetted, rest pass/already-tracked:
- **Biotech gene-therapy / rare-disease approval acceleration (MED-HIGH):** clustered approvals (sickle-cell Jul-1, oral PCSK9 Jul-17, blood-cancer immunotherapy Jun-30) + AI-designed drugs entering phase 1-2 + XBI at cycle highs. Vetted CRSP → **3.5/4 WATCH**.
- Oil majors rebound XOM/CVX (MED): directional energy beta, no instance edge, IBKR-route. Pass.
- Healthcare-insurer GLP-1 cost pressure (MED-HIGH): already priced into sector guidance per digest; execution risk high. Pass.
- Brazil tariff shock (MED): EM/materials, no decentralized venue. Pass.

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **CRSP (new)** | **3.5/4** | WATCH | Gene-therapy approval-cycle inflection | No trigger met NOW. **Q2 earnings Aug-10 = the inflection**: ENTER $48-55 (1% Kelly) IF Casgevy 2026 guidance ≥$130M holds; PASS→wait $35-45 dip if guidance <$100M. CTX310 Ph2 positive (2026-27) = upgrade. 2-5y → IBKR-surface. |

Trigger-state (all IBKR-surface, previously surfaced): SOL $74.65, STX $0.166, ALB $118.37 (now inside the deep-conviction ≤$120 zone — but the lithium-spot caveat from Jul-05/12 stands: confirm spot >$20/kg before treating as an add, else "cheaper = thesis-eroding"), CCJ $84.84 (below the $85-95 band; uranium-spot leg unverified). All 4 surfaced to operator at the 14:00 tick.

## 2026-08-02 weekly digest (domains: macro-fiscal-labor, tech-ai-chips, crypto-on-chain — stalest, 3wk)

Themes — one new candidate vetted, rest pass/already-tracked:
- **AI-capex ROI proof-point cycle (MED-HIGH):** TSMC raised 2026 capex guidance (+40% sales growth target), SEMI equipment billings +14% YoY, Google lifted 2026 capex to $185-205B. The theme has rotated from "is capex coming?" (2025) to "does capex CONVERT?" (Q3-Q4 2026 earnings). Vetted GOOG → **3.75/4 WATCH**.
- **Real wages flat / consumer de-risking (MED):** 3.5% wage growth ≈ 3.5% CPI = zero real gain; weak payroll flow. Play is SHORT cyclicals (XLY/AZO) — directional macro beta, no instance edge, and shorting isn't the IBKR sleeve's shape. Pass.
- **Fed real rates ≈0 = still stimulative (MED):** 3 dissents for a hike on Jul-29. Directly relevant to PM Fed markets — but my July N=1 says the market prices Fed better than I do; the September market already sits at 0.525 hike. Explicit pass, not an oversight.
- **Stablecoin deleveraging (MED):** USDT −$6B over 60d, orderly (peg held), DeFi TVL flat. TOUCHES US: idle capital lives in Aave aUSDC. Assessed — $7.85 in the single most senior, overcollateralized layer of the largest lending market; a leverage unwind stresses borrowers and RAISES supply APY. No action, no exposure change.
- **BoJ carry unwind (LOW-MED):** forex, no venue. Pass.

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **GOOG (new)** | **3.75/4** | WATCH | AI-capex ROI conversion; Cloud backlog $514B, +82% growth | No forced entry at P/E 16.9. **Q3 earnings (late Oct) = the proof-point**: entry justified if Cloud growth holds ≥50% AND 2027 capex guidance is disciplined. **Dip trigger $280-285 (P/E ~14) = strong buy.** Risks: capex/revenue 15-17% unrecovered, antitrust appeal late-26/early-27 (Chrome divestiture push), Gemini 2nd in AI-search share. 2-5y → IBKR-surface. |

Trigger-state: ALB $117.53, CCJ $87.79, NVDA $195.74 all surfaced to operator Jul-30 with the lithium-spot caveat ($21.6/kg — holds, but at the edge). No new hits this week.

**Cross-read against a LIVE position (honest):** the GOOG vet cuts mildly AGAINST my Gemini-HLE NO. $185-205B of capex and a shipping 3.x cadence make an intermediate Gemini clearing 50% on HLE more plausible than my original "unannounced miracle model" framing — the same correction kimi made yesterday. The position's edge now rests on the resolution-source pillar (agi.safe.ai listing zero 2026 models), not on capability. Prior already revised to 0.70; this reinforces WHY tranche-2 was declined.

## 2026-08-10 weekly digest (domains: biotech-health, trade-regulation, markets-corporate — stalest, 3wk; OWED from the Aug-9 outage)

Themes:
- **Tariff pass-through bifurcation (HIGH):** 50% Canada tariff effective Aug-19, 25% Brazil since Jul-22; June capital/consumer/pharma imports −1.8% with a 36% late-July front-loading spike that reverses into a Sept-Oct supply deficit. Domestic producers gain relative cost advantage; import-dependent retail margins compress. Directional equity macro — no decentralized venue, no instance edge → IBKR-surface note only, no vet (the play is a whole-sector tilt, not a ticker with a trigger).
- **Outbreak tail risk (MED):** see below — the one PM-ACTIONABLE theme, and it failed its fresh-fact gate.
- Skipped: WHO mpox (declining), general trade escalation (priced), NIH restructuring (low impact).

**PM-actionable candidate found and KILLED (the review's real work):** "Which countries will have an Ebola case in 2026" (13 legs, $32k vol, $9.5k liq — mechanical resolution: any officially confirmed case in-territory by Dec-31). Was building a NO basket on the far-from-Africa legs (US 0.805 NO, China 0.81, India 0.86) against a hard historical base rate — ebola has never been confirmed in China or India across ~30 outbreaks in 50 years; the US only during the 28,000-case 2014-16 epidemic. **Fresh check killed it:** the digest's facts were stale (Uganda's outbreak ENDED Jul-28 at 20 cases, not "378 and growing"), the actual epidemic is DRC at 4,053 cases/1,850 deaths and fastest-growing on record, and **France already has a confirmed exported case** — which directly refutes the never-happens prior the whole basket rested on. With exportation demonstrated and the epidemic still growing, ~20% on US/Canada/China is defensible; I hold no differentiated epidemiological edge. Scored skip, ledger N=45.

Trigger-state: SOL/STX/ALB flagged during the outage window by the fallback — all route=ibkr_surface multi-year repeats at ~unchanged prices, no re-ping warranted.

## 2026-08-16 weekly digest (domains: critical-minerals-commodities, energy-power-infrastructure, geopolitics-security — due in rotation, 3wk)

Themes (all multi-year -> IBKR-surface per venue constraint):
- **Cobalt deficit structural (HIGH):** DRC quota 87k T/yr vs 292k T demand = hard-cap deficit widening 15%->25%; spot +69% YoY; China miners petitioning for quota. Plays (Glencore/Sherritt) have no decentralized venue. Surface-only.
- **Uranium policy-demand inelasticity (HIGH):** term $90/lb highest since 2008, 15 reactors online 2026, Palisades restart precedent. CCJ (the vetted class pick) ran +15% THROUGH its band to $97.74 while the entry stayed gated on the unverified spot leg — recorded as the cost of that caveat. NOT vetting laggards (DNN/UUUU): chasing the cheaper name after the leader ran is the favorite-fade error in sector form. Surface-only.
- **Rare-earth processing bottleneck (MED-HIGH):** the binding constraint is refining (China 90%+), not mining; export-control list at 24 firms. MP/RTX plays — surface-only.
- **Oil floor reset (MED):** WTI $81 with the "4 mb/d surplus" narrative masking 8.3 mb/d of Gulf production below baseline. CORROBORATES DEC-0077 (Hormuz closure persistent, no resolution path visible EOY-2026 per IEA).
- **Natgas trough (MED):** record production + record inventories; policy-capped ceiling. No venue, no edge on LNG cycle timing. Pass.

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **CRSP (re-vet)** | **3/4 (was 3.5)** | WATCH | Gene-therapy inflection | **Original trigger TECHNICALLY MET** — Casgevy Q2 $76.4M +151% YoY (≥$130M pace) with price $53.55 in the $48-55 band — but the fresh vet DOWNGRADED: not cycle-bottom, dilution ahead, R/R 1:1.5 vs 1:2 target. Better entry $40-45; hold-trigger = Q4 guidance ≥$300M run rate. Multi-year -> operator's IBKR call, surfaced with both facts. |

Trigger-state: GOOG $343.54 (dip trigger $280-285 — far), ALB $136.15 (LEFT the ≤$120 zone), CCJ $97.74 (left $85-95 band). No actionable PM candidates from these domains this week.

## 2026-08-23 weekly digest (domains: macro-fiscal-labor, tech-ai-chips, crypto-on-chain — stalest, 3wk)

Themes (per venue constraint, multi-year -> IBKR-surface only):
- **Late-cycle labor warning (MED):** payrolls declining while unemployment holds — the classic
  pre-recession sequence; NVDA-led valuations assume no recession, labor data disagrees. The
  DATED CATALYSTS are the tradeable part: Warsh Jackson Hole speech Aug-28, Aug employment
  report Sep-4. Plays (long vol / TLT) are IBKR-side. PM angle: none found — Fed family is a
  standing pass and no listed market resolves on the Sep-4 print directly.
- **TSMC structural-vs-cyclical (MED):** capex to $60-64B (+22%) with discipline vs hyperscaler
  77% — read as structural AI demand floor; TSM undervalued vs NVDA capex-adjusted. Needs
  earnings confirmation.
- Passed: DeFi TVL floor (fact basis thin, digest's own NEXT-STEPS agrees).

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **TSM** | vet | WATCH | TSMC structural AI floor | Valuation justified but not attractive; 22% Taiwan-conflict tail by 2027 demands sub-Kelly + hedge. Entry on dip or earnings-confirmation catalyst. IBKR-side. |
| **TLT** | 2.5/4 | WATCH | Late-cycle duration hedge | Entry conditional on labor deterioration confirming (Sep-4 print); Warsh-Fed reaction function is the wildcard. IBKR-side. |

Trigger-state: NOT re-priced this week (stooq blocked from VM; domains rotated away from the
commodity names). Last states stand: GOOG far from $280-285 dip, ALB left ≤$120, CCJ left
$85-95, CRSP awaiting $40-45 with Q4-guidance hold-trigger. No trigger-hit flags.
