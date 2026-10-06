# Polyclaude Long-Term Watchlist

> Living document for multi-year (~1-5y) generational-mispricing candidates. Created 2026-05-08 in response to user directive: scan and analyze across stocks / crypto / other categories; invest from polyclaude where accessible; surface IBKR-side candidates for user's personal sleeve.
>
> Reference pattern: SanDisk 2023-2025 — memory-cycle bottom + AI-compute secular demand + Western-Digital-spinoff catalyst + margin of safety = generational return. Hunt for analogous convergences elsewhere.

## 2026-09-15 trigger review

- **CCJ:** the quote reached $93.26 and crossed the stored $95 IBKR-surface
  gate. The automatic fresh vet returned **2/4 PASS** and rejected entry at the
  current valuation. The live trigger is now **$75** and still requires uranium
  term pricing above $80/lb plus intact production guidance; the alternative is
  Q4-2026 evidence that Westinghouse cash flow is recovering without materially
  larger capital needs. Suggested size is **0% now** and a **1-2% IBKR-sleeve
  starter** only after that revised gate clears. Telegram 955 surfaced the
  result to the operator.

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

## 2026-08-30 weekly digest (domains: biotech-health, trade-regulation, markets-corporate — oldest, 20d)

No domain was literally unrun for four weeks: this oldest trio last ran Aug-10, while the
other six ran Aug-16/Aug-23. The least-recent rotation was run so the scheduled review still
advanced.

Themes:

- **Pan-RAS pancreatic-cancer commercialization (MED):** FDA approved RVMD's RASONQUE after
  13.2-month median survival versus 6.7 months for chemotherapy in a 500-patient trial.
  The clinical signal is real; the equity setup is not cheap after the approval rerating.
- **AI buildout power/electrical bottleneck (MED):** NVIDIA's disclosed supply/capacity
  commitments rose to $279B and it is supporting 4.25 GW of Ohio IT load, while explicitly
  naming power/land/shell constraints. This corroborates the existing AI-power theme; ETN
  was selected as the unvetted electrical-equipment expression.
- **AI-infrastructure financing/concentration risk (LOW):** noted but not promoted or traded;
  it is a hedge thesis without a sufficiently bounded instance edge.

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **RVMD (new)** | **2/4** | PASS | RASONQUE launch + broader RAS platform | $207.88 is near the high at ~$44.6B market cap. Reassess at **≤$120** only after two quarters of payer-covered uptake. Added an IBKR-surface research trigger. |
| **ETN (new)** | **2/4** | PASS | AI/grid electrical bottleneck | Demand/backlog are strong, but $402.78 is ~31x forward earnings and Boyd raised leverage. Reassess at **≤$300** with positive electrical orders and declining net debt, or after the expected 2027-Q1 Mobility/Dana close. Added an IBKR-surface research trigger. |

Trigger-state: the live monitor fully priced all 30 candidates and found **zero hits**.
Direct CoinGecko reconciliation confirmed the nearest crypto names still above their gates:
STX $0.2438 vs $0.22, EIGEN $0.1971 vs $0.18, UNI $5.20 vs $3.25, and SKY $0.0707
vs the tightened $0.050 gate. Precautionary fresh checks on UNI and SKY both remained **2/4 PASS**; SKY's
research gate was tightened to **$0.050**. Neither new equity trigger is an authorization
to buy—each only reopens underwriting at a materially safer valuation. No polyclaude capital
action. Telegram message 880 surfaced the weekly result.

## 2026-09-03 trigger re-vet — LRCX

The original LRCX research gate fired at **$279.26 <= $280**, routing to the operator's IBKR
surface. The automatic fresh fundamental check returned **2/4 PASS**, not an entry: Lam still
trades at roughly 50x trailing earnings near a semiconductor-equipment cycle peak, so the old
25–30x-forward framing did not provide the margin of safety it was meant to encode. The price-only
trigger is tightened to **<=$190** (roughly 25x FY26 EPS before any earnings reset), with an
alternative research trigger after a material WFE-order correction if Lam retains share, balance-
sheet strength, and service revenue. **No buy recommendation at $279; suggested size is $0 until
one of those gates is met.**

## 2026-09-06 weekly digest (domains: critical-minerals-commodities, energy-power-infrastructure, geopolitics-security — least recent, 21d)

No domain was literally unrun for four weeks: this least-recent trio last ran Aug-16, while the
other six ran Aug-23/Aug-30. The least-recent rotation was run so the scheduled review still
advanced.

Themes:

- **PJM dispatchable-generation scarcity (MED):** two DOE emergency orders in eleven days,
  including the Aug-21 order coordinating with Constellation to keep Eddystone units 3 and 4
  available through Nov-20, reinforce the option value of reliable capacity. CEG was re-vetted.
- **Grid interconnection and HVDC equipment (MED):** the North Plains Connector final EIS covers
  a 422-mile, 525-kV, 3-GW HVDC line, while federal grid-planning and emergency interventions
  corroborate a multi-year transmission buildout. PWR was selected as the clean listed
  transmission-engineering expression.
- **Allied heavy-rare-earth supply (LOW):** recorded in the world-state digest but not promoted
  or vetted because it did not meet the requested MED/HIGH-confidence threshold.

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **CEG (existing)** | **2/4** | PASS | Dispatchable power / nuclear scarcity | $298.96 is roughly 22-26x forward/2026 adjusted EPS, not a cycle-bottom valuation. Reassess at **<=$225** only if investment-grade ratings and the Crane 2027 restart schedule remain intact, or after actual restart at <=~20x forward EPS. The machine gate was tightened from $230. |
| **PWR (new)** | **2/4** | PASS | Grid/HVDC/data-center buildout | $620.06 is roughly 34x forward earnings after a 65% one-year rerating. Reassess at **$430-470** with electric backlog and 2027 visibility intact, or after two quarters of positive FCF/integration evidence without backlog deterioration. Added an IBKR-surface research trigger at $470. |

Trigger-state: the pre-update live monitor priced all 30 existing candidates and found **zero
entry hits**. PWR becomes candidate 31; its $470 gate is well below the fresh $620.06 check price.
These are research triggers, not buy authorizations. Current machine gates supersede historical
narrative levels. Both candidates route to the operator's IBKR surface; no polyclaude capital
action.

## 2026-09-13 weekly digest (domains: macro-fiscal-labor, tech-ai-chips, crypto-on-chain — least recent, 21d)

No domain was literally unrun for four weeks: this least-recent trio last ran Aug-23, while the
other six ran Aug-30/Sep-6. The least-recent rotation was run so the weekly review still advanced.

Themes:

- **Persistent energy-inflation / restrictive-rate risk (HIGH):** August energy CPI was +16.3%
  YoY, final-demand PPI +5.4% and core PPI +4.7%, while the ECB raised rates. The facts challenge
  an easy global-easing narrative, but the proposed energy-equity implementation is already
  late-cycle. XLE was selected as the diversified listed expression and rejected at its current
  price.
- **AI bottleneck broadens to leading-edge supply and optical interconnect (MED):** TSMC August
  revenue rose 53.3% YoY and NVIDIA guided $108B quarterly revenue excluding China, alongside
  co-packaged-optics ramps. This corroborates the existing TSM watch; COHR was selected as the
  unvetted optical expression and rejected at its current valuation.
- **L2/lending usage growth with selective token accrual (MED):** Aave TVL rose 24.8% over one
  month, Base and Arbitrum secure $14.51B/$12.23B and L2s post 97.5% of Ethereum blob data. This
  supports the existing selective-value-accrual doctrine rather than a blanket L2-token buy.
  STRK's isolated unlock short was LOW confidence and was not promoted.

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **XLE (new)** | **1/4** | PASS | Energy inflation / oil disruption | $65.14 is 1.6% below its 52-week high after a 53.8% one-year return. Reassess at **≤$50** only if forward P/E stays below 13x and oil/inventories show a real cycle trough rather than a temporary geopolitical premium. Added an IBKR-surface research trigger. |
| **COHR (new)** | **2/4** | PASS | AI optical interconnect / CPO | $305.37 follows a 196% one-year rerating; ~72x trailing earnings, weak current FCF and dilution defeat margin of safety. Reassess at **≤$190** with Datacenter & Communications growth above 25% and falling net debt, or after two positive-FCF FY27 quarters validate CPO/1.6T conversion. Added an IBKR-surface research trigger. |

Trigger-state: the 14:00 live monitor priced all 31 existing candidates and found **zero hits and
zero missing prices**. The two new gates are far below the fresh vet prices; a post-update monitor
also found no hit. Both route to the operator's IBKR surface and are research prompts rather than
buy authorizations. No polyclaude capital action.

## 2026-09-20 weekly digest (domains: biotech-health, trade-regulation, markets-corporate — least recent, 21d)

No domain was literally unrun for four weeks. This least-recent trio last ran Aug-30, while the
other six ran Sep-6/Sep-13, so the due rotation was used.

Themes:

- **Persistent nominal-price pressure / duration risk (MED):** CPI, PPI and core-PCE facts argue
  against assuming a rapid nominal-yield decline. TIP was the clean long expression and failed the
  generational-mispricing test; it remains a portfolio hedge rather than a return candidate.
- **Energy/freight input pass-through (MED):** fuel and logistics costs are accelerating. XLE's
  fresh Sep-13 1/4 PASS and unhit $50 gate stand; JETS/IYT are tactical shorts with heterogeneous
  pass-through and were not added as long-term longs.
- **Early-stage biotech optionality (LOW):** the FDA pilot is not investable before sponsor
  disclosure. The digest misidentified Fayuvi's sponsor ticker as `ULGN`; the FDA identifies
  Ultragenyx (**RARE**), which was vetted as the only new company-specific candidate.

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **TIP** | **2/4** | PASS | Inflation protection / positive real carry | $105.27 is at its 52-week low and carries a 2.61% issuer-reported real yield, but the ETF has no compounding engine or forced re-rating catalyst. Consider only as an inflation hedge at real yield >=2.5%; a stronger tactical price gate is **<$100**. Not added to the generational watchlist. |
| **RARE (new)** | **3/4** | WATCH | Rare-disease launch optionality after GTX-102 failure | $14.51 after a 50% one-year fall. Reassess **below $12.75 only after Q3 confirms post-restructuring runway and launch guidance**, or after GENGLYCOS/FAYUVI uptake plus a credible path to 2027 profitability. Cash burn, dilution and Crysvita concentration prevent entry now. Added an IBKR-surface research trigger. |

The pre-update monitor found **zero live hits across 33 existing gates**. RARE's new $12.75 gate is
below its $14.51 Sep-18 close, so it is also unhit. No entry or portfolio action followed.

## 2026-09-27 weekly digest (domains: critical-minerals-commodities, energy-power-infrastructure, geopolitics-security — least recent, 21d)

No domain was literally unrun for four weeks. This oldest trio last ran Sep-6,
while the other six ran Sep-13/Sep-20, so the due least-recent rotation was
used.

Themes:

- **U.S. LNG export-capacity buildout (HIGH):** EIA forecasts gross exports
  rising from 15 Bcf/d in 2025 to 17 in 2026 and 19 in 2027; FERC advanced
  Sabine Pass Stage 5 and Corpus Christi Stage 4 environmental review and
  approved 1.175 million Dth/d of pipeline capacity. LNG and NEXT were vetted
  as the direct listed expressions; neither has a current margin of safety.
- **Grid bottleneck / transmission equipment (MED):** repeated DOE reliability
  orders and 31 planned grid projects reinforce the existing PWR/ETN/HUBB
  theme. Fresh Sep-6/Sep-20 PWR and ETN checks remain valuation-gated, so a
  redundant re-vet had no incremental value.
- **Hormuz disruption optionality (MED):** official sources confirm physical
  shipping stress while OPEC+ held October output requirements flat. The theme
  is directional oil beta already represented by valuation-gated XLE/XOM
  research, not a new issuer-specific long.
- Nuclear optionality was LOW confidence; critical-minerals and defense facts
  lacked an issuer-specific earnings catalyst and were passed.

| Candidate | Score | Verdict | Theme | Entry |
|---|---|---|---|---|
| **Cheniere ($LNG, new)** | **2/4** | PASS | Contracted LNG export growth | $268.54 is only 10.7% below its 52-week high and not a cycle-bottom valuation. Reassess at **≤$215** while contracted coverage and DCF guidance remain intact, or after a fully financed Sabine Pass Expansion FID with sufficient SPAs. Added an IBKR-surface research trigger. |
| **NextDecade ($NEXT, new)** | **2/4** | PASS | Rio Grande LNG commissioning | $6.56 prices a pre-revenue, highly leveraged construction equity. Reassess at **≤$4.75** only with construction/funding on schedule and a favorable FERC appeal, or after verified Train 1 LNG and stable operations. Added an IBKR-surface research trigger. |

The pre-update live monitor found **zero hits across 34 existing gates**. Both
new gates are below their fresh check prices; a trigger is permission to
re-underwrite, not a buy authorization. Both candidates route to the operator's
IBKR surface, and no polyclaude capital action followed.

## 2026-09-30 — non-Polymarket opportunity review requested by operator

The daily discovery pipeline is predominantly Polymarket; a quiet scanner
result is not evidence that equities, crypto or cash alternatives lack
reasonable investment theses. This bounded review used independent crypto
and venue specialists plus a primary-source equity review. No position,
order or probability prior changed, and no Fireworks/API spend was incurred.
The existing generational-mispricing score is not a requirement that every
positive-EV investment be at a cycle bottom.

### Ranked theses and entry limitations

1. **Cheniere (LNG): strongest operating-business thesis in this review.**
   [Completed CCL Stage 3](https://lngir.cheniere.com/news-events/press-releases/detail/345/cheniere-announces-substantial-completion-of-ccl-stage-3)
   raises capacity by over 20%; the last train was turned over August 28.
   [Q2 guidance](https://lngir.cheniere.com/news-events/press-releases/detail/343/cheniere-reports-second-quarter-2026-results-and-raises)
   puts company distributable cash flow at $5.3–5.8B and records $1.1B H1
   share repurchases. The September 29
   [Petrobras SPA](https://lngir.cheniere.com/news-events/press-releases/detail/346/cheniere-and-petrobras-sign-long-term-lng-sale-and-purchase)
   adds 0.8 mtpa of contracted sales over 22 years; no immediate quarterly
   cash-flow increment is assumed. At the $268.05 indicative quote / $56.16B
   equity capitalization near 17:00 UTC, guided DCF is about 9.4–10.3% of
   equity value. This is not a shareholder cash yield: DCF excludes expansion
   capex, and capital also funds debt reduction and projects. Q3 earnings and
   2027 cash-flow guidance are useful evidence events, with no release date
   asserted. Capacity execution, debt/project commitments and global LNG
   oversupply remain risks. Retain the prior $215 price review gate or the
   funded-FID evidence gate; no demonstrated vetted spot-equity route exists
   for this portfolio, so current access is the operator's brokerage.

2. **UNI: clearest dated near-term catalyst, but considerable anticipation.**
   The official [Arc proposal](https://gov.uniswap.org/t/temp-check-protocol-fee-expansion-arc/26287)
   extends fee collection and burn across v2/v3/v4. Independent public RPC
   reads of the officially documented GovernorBravo
   `0x408ED6354d4973f66138C91495F2f2FCbd8724C3` verified proposal 102 as
   Active, unexecuted and uncanceled at block 26,091,743 (17:18:59 UTC),
   with 10.931M UNI For against 40M quorum. Its creation transaction
   [identifies the Arc proposal](https://etherscan.io/tx/0x51fac05c65aa5a8be704316a82b55f82b1cbe475b56756b9198f9e3cf22d3d29).
   The authoritative end is block 26,109,012, estimated near Oct-3 03:10 UTC
   at the sampled block rate; passing still requires quorum and subsequent
   queue/execution. The [official app](https://app.uniswap.org/vote/2/15)
   separately lists it active.
   Public CoinGecko/DefiLlama prices near 17:09–17:13 UTC were $8.98, with
   +74.2% over 30 days and about $5.57B circulating capitalization. The
   [fee-burn mechanism](https://developers.uniswap.org/docs/protocols/protocol-fee/overview)
   is real, but holders receive no cash dividend. Trailing public holder
   revenue was $15.68M/30d, approximately $191M annualized, versus the
   [20M UNI annual treasury growth budget](https://blog.uniswap.org/unification),
   worth about $180M at spot. Treasury distribution is neither new minting
   nor guaranteed selling; gross burn is nevertheless insufficient evidence
   of net float scarcity. The seven-day revenue pace was weaker.
   A read-only Arbitrum V3 $20 USDC round trip returned $19.878689,
   a 0.607% drag before gas/funding; Polygon direct pools were not demonstrated.
   Retain $3.25 as the valuation review gate. $7.50 alone is not a buy or a
   replacement gate: even sustained $20M/month burn implies only about 1.93%
   annual net float reduction after the treasury budget at that price.
   Verify actual Arc execution and sustainable net burn before revising value.

3. **PWR: grid construction and power bottlenecks, with valuation risk.**
   [Q2 results](https://investors.quantaservices.com/news-events/press-releases/detail/402/quanta-services-reports-second-quarter-2026-results)
   report $53.4B total backlog, $33.6B remaining performance obligations,
   $0.9B quarterly FCF and adjusted diluted EPS of $4.24. These support a
   real demand-to-earnings channel, but growth includes acquisitions and
   backlog is not all contracted near-term revenue. The indicative $646.40
   quote / $98.54B equity capitalization near 17:00 UTC leaves little room
   for treating the theme itself as an undiscovered edge. Backlog conversion,
   integration and 2027 guidance are the relevant evidence; retain the
   $430–470 review range and prior FCF/integration gate. Brokerage access only
   through the currently established routes.

**AAVE / HYPE alternatives:** AAVE at $161.56 has lower dilution than HYPE,
but V4 and Arc deployment have already occurred. The
[April buyback pause](https://governance.aave.com/t/arfc-pause-aave-buybacks/24686)
is established; the
[August/September funding allowances](https://governance.aave.com/t/direct-to-aip-august-september-2026-funding-update/25597)
do not independently verify restarted recurring purchases. A funded, executed
buyback program with incident liabilities addressed is the useful catalyst.
A public Arbitrum $20 round trip lost 0.612% before gas/funding. HYPE at about
$90.83 has real Assistance Fund token accrual, but the public price snapshot
shows ~$20.19B circulating cap versus ~$86.71B diluted value. Neither a
new dated Q4 catalyst nor a primary-source near-term distribution schedule
was established; no new venue setup is justified by this screen.

### Cash/index outside option and venue feasibility

At an illustrative 3.2% Aave rate, cash earns roughly 0.81% over 93 days.
UNI/AAVE thus require more than about 1.4% gross return simply to match cash
after the observed two-way swap quote cost, before gas, funding and token risk.
The specialists' broad subjective return branches did not establish a
reliable excess return. Scenario weights are not calibrated probabilities;
no precise alpha claim or buy sizing is derived from them.

Fresh public [Ostium pair](https://builder.prod.bedrock.ostium.io/v1/pairs)
and depth reads around 17:12–17:14 UTC show 1x US500 technically available
with $5 minimum collateral, 1bp opening fee and roughly 5.897% annualized
long rollover. At a constant current rate, 93-day carry is about 1.503%;
opening plus snapshot spread raise direct drag to about 1.52%, before gas.
It needs about 2.34% index price appreciation merely to match Aave. Gold's
corresponding hurdle is about 2.83%; US100 had no long capacity in the last
quote. These are USDC-settled synthetic perps without ETF dividends. Future
carry is variable, not an exact prepaid lifecycle charge.

Current [Ostium terms](https://docs.ostium.com/legal/terms-of-use) restrict
EU location, residence or citizenship and include API/code use in Services.
Finland VM relocation alone does not establish account-owner eligibility.
The operator offered relocation and supplied additional private residence
context. This does not establish every owner-eligibility criterion; no blanket
owner restriction is inferred from the present VM location. No relocation was
performed, and the legacy writer remains blocked pending eligibility plus
safe allowance/slippage/final-fill support.
The prior spot-index route needs a fresh all-in quote if reconsidered at the
larger deployable cash balance; its Sep-10 costs are not current quotes.

### Sep-30 17:40–17:47 UTC — dYdX venue shortlist and broad crypto exposure

dYdX was initially scoped on June 2, but no account integration or funded
position was created. Refreshed its public mainnet indexer successfully from
the present VM: 296 perpetual markets, with BTC/ETH active. Snapshot oracle
prices were about $83,988/$2,679 and quantity increments .0001 BTC/.001 ETH
(about $8.40/$2.68). These are increments, not independently verified minimum
order tickets. [Current endpoints](https://docs.dydx.xyz/interaction/endpoints)
and [market metadata](https://indexer.dydx.trade/v4/perpetualMarkets).

[Published base fees](https://docs.dydx.xyz/concepts/trading/rewards) are
1bp maker/5bps taker at our volume tier, before rebates or discounts.
Trading itself has no gas fee; funding and deposit/withdrawal/bridge costs
are separate. Do not budget an incentive until eligibility and the current
on-chain rate are verified. Sep-30 17:44 orderbook snapshots had roughly
2.38bps BTC and 9.71bps ETH top-of-book spreads; displayed first-level depth
was thin, so these are not full-size executable quotes.

The 168 hourly settled funding rows Sep-23 18:00 through Sep-30 17:00 sum to
+0.0082% BTC and -0.02055% ETH. Simple annualization is +0.43%/-1.07% of
perpetual notional, respectively; positive pays shorts, negative pays longs.
These are historical observations, not forward rates. A hedged BTC carry
position would also tie up spot capital plus collateral. This sample does
not establish an attractive cash-and-carry alternative to Aave.
[BTC history](https://indexer.dydx.trade/v4/historicalFunding/BTC-USD?limit=168),
[ETH history](https://indexer.dydx.trade/v4/historicalFunding/ETH-USD?limit=168),
[funding mechanics](https://docs.dydx.xyz/concepts/trading/funding).

Both managed EVM wallets were re-read. ARB on Arbitrum and WETH on
Arbitrum/Base/Polygon are zero. Native ETH totals about .000513 and POL
50.141866, about $7.02 combined at fresh validated prices, held for gas.
Aave USDC/aUSDC.e deposits total about $46.39; these are dollar credit and
protocol exposure, not long BTC/ETH. No deliberate broad BTC/ETH/SOL
position exists in the managed portfolio records. This is a check of known
wallets/assets, not an exhaustive unknown-token inventory or an audit of
the operator's personal accounts.

Add dYdX to the venue shortlist for directional shorts, tactical positions
and attractive hedged funding. Compare spot BTC/ETH against a
fully collateralized perpetual for any broad directional allocation; the
venue does not itself establish a return thesis. Its
[software terms](https://dydx.exchange/v4-terms) do not list a blanket EU
restriction like Ostium's, but owner eligibility and the selected service's
terms still require verification before funding. No account, key, transfer,
order or new execution path was created.


### Sep-30 20:25 UTC — LNGx access correction and small-account route costs

Cheniere has an issued decentralized tracker, [LNGx](https://api.xstocks.fi/api/v2/public/assets/LNGx),
with [issuer reserves](https://api.xstocks.fi/api/v2/public/proof-of-reserves/LNGx)
reporting 418 underlying shares versus 387.3067 circulating units at 19:45.
Original token: `0xdce993f8a6dbce7f27434874f5dfe9a8d58509c9`;
V2 wrapper: `0x52987e7bf8d84136ab6501d437cd743652f5772e`.
This corrects the earlier brokerage-only assumption, but does not establish
an executable investment: native-USDC V3 pools and Kyber routes checked on
ETH/Arb were absent for $20/$50. No accessible economical route was verified.
Product restrictions still apply independently of technical transferability;
no owner-eligibility conclusion or direct-issuer redemption access is assumed.

[SPYx metadata](https://api.xstocks.fi/api/v2/public/assets/SPYx) confirms Arbitrum
deployment, but its checked wrappers have zero supply and no quoted routes.
Ethereum V1 aggregator buy/sell quotes around 20:01 returned $19.229 from
$20 and $45.505 from $50; quoted swap gas makes round-trip losses about
7.63%/10.70% before approval/bridge/slippage. Direct vetted V3 single-hop
quotes are worse. No allocation justified by a generic equity-risk premium.
Higher-rate stablecoin routes were also reviewed: direct Polygon Morpho
WBTC lending has a modest premium but concentrated withdrawals and a
completed Compound/Gauntlet wind-down; no reserve migration justified.
The active search did produce DEC-0182's small Swift maker opportunity,
recorded in the journal, with cash reserved but no filled position assumed.

### Oct-3 06:00 UTC — UNI Arc vote succeeded; execution and valuation gates remain

Completed the Sep-30 post-deadline review. Two independent public Ethereum
RPCs agree at block **26,109,905** (06:05:47 UTC): GovernorBravo proposal
**102** is **Succeeded**, with **46,262,383.08 UNI For**, zero Against/Abstain,
and **40M quorum**. Deadline block **26,109,012** was mined at 03:06:59 UTC.
Root's independent read agrees. The proposal has eta zero and executed false:
**not queued, not executed**. The exact Governor is verified against the
[official technical reference](https://developers.uniswap.org/docs/ecosystem/governance/technical-reference),
and all three action targets match the [Arc proposal](https://gov.uniswap.org/t/temp-check-protocol-fee-expansion-arc/26287).

The [documented Arc mainnet RPC](https://docs.arc.io/arc/tools/node-providers)
at block **24,004,532** (06:05:53 UTC) still reports v2 `feeTo()` zero,
v3 owner equal to the Wormhole receiver rather than the fee adapter, and
v4 `protocolFeeController()` zero. **The proposed Arc fee activation has
not occurred at this snapshot.** The vote removes one governance uncertainty;
it does not yet establish fee revenue or UNI burn from this expansion.

Fresh validated CoinGecko UNI is **$9.17** at 06:04:10 UTC, **2.82 times**
the retained **$3.25 valuation review gate**. No price trigger was hit.
Retain NO ENTRY: actual execution/activation and sustained net fee-funded
burn must accompany valuation. Gross burn still needs reconciliation with
the **20M UNI/year** treasury growth budget; protocol revenue is not a token
holder cash dividend. The Sep-30 route-cost comparison remains dated and
would require fresh executable quotes before allocation. No automatic entry,
new account, transfer or order. Existing scheduled checks/news cover changes.
Public chain/quote evidence: `data/periodic_20261003T0600_uni.json`, independent
root read `data/periodic_20261003T0600_uni_root.json`.

## 2026-10-04 Sunday review — macro, AI/chips and crypto

No domain meets the requested four-week cutoff: these three last ran Sep13,
the other six Sep20/Sep27. Refreshed the three least recent, with the fallback
disclosed. The 14-source digest and both requested candidate vets completed.

**MED AI/foundry demand** supports business fundamentals, without establishing
a mispriced share or an edge through January 2027. TSMC's reported August
revenue grew 53.3% y/y; September is still unpublished. Its
[calendar](https://investor.tsmc.com/english/financial-calendar) lists September
sales on Oct8 and Q3 results on Oct15. ASML's
[Q2 release](https://investor.asml.com/news-releases/news-release-details/q2-2026-financial-results)
supports the EUV/DUV capacity thesis; [Q3 results](https://investor.asml.com/quarterly-results)
are scheduled Oct14. Capacity plans and earnings estimates are forecasts.

| Candidate | Fresh vet | Oct2 close (USD) | Review condition and current decision |
|---|---|---:|---|
| **ASML — new explicit watch** | 3/4 WATCH | $1,867.31 | Review at ≤$1,400 if demand, earnings and capacity utilization remain intact. Alternative: proven earnings growth brings forward P/E to ≤25x with adoption and cash-flow evidence. AI capex reversal, export controls and customer concentration remain material. No entry. |
| **TSM — existing watch refreshed** | 2/4 PASS | $472.78 | Review $325–350 with leading-edge utilization, yields and AI demand intact; machine gate $350. Earnings/ramp confirmation must include margins and free cash flow. Taiwan disruption and overseas capex risks remain. No entry. |

Added ASML and TSM to the machine config as **conditional 2–3y brokerage
research**. No lawful, economically executable project route was verified for
either in this review. The four-dimension scores are research summaries,
not calibrated return estimates or independent investment prohibitions.
Neither check supplies a robust net excess-return case for this project's
January evaluation at the observed prices.

Root independently dated both closing prices using Yahoo history. Multiples
are not consistent across vendors: TSM's vet quotes 32.9x trailing, whereas
Yahoo reports 35.3x trailing/21.6x forward; ASML's vet reports 58.9x/33.7x
versus Yahoo 64.9x/32.1x. At $350, TSM is about 26.2x Yahoo's current trailing
EPS, **not** the vet's stated 22–25x. Price gates require fresh EPS, cash-flow
and thesis review when hit. Forward EPS is an estimate. The vets' subjective
five-year scenarios do not match their three-year headers and are not used
for Kelly sizing or January alpha. Detailed node/fab and customer adoption
claims not independently verified are excluded from the entry decision.

**Existing trigger review:**

- **Price: 0/38 hit, zero missing.** The original monitor covered 36 candidates;
  the two dated root quotes add TSM and ASML without rerunning the universe.
  The original monitor omitted individual quote timestamps; weekend equity
  session dates are inferred except for these two confirmed Oct2 closes.
- **TLT: partial research flag, no long entry.** The old Aug23 labor condition
  is supported by [October 2 employment data](https://www.bls.gov/news.release/empsit.nr0.htm):
  +29k payrolls and 60k downward revisions. But the
  [September Fed hike](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm)
  and inflation conflict with a simple duration long. The digest's MED
  higher-for-longer theme also supplies no priced short/option edge. No new
  price gate, order or third longterm vet; retain a conditional hedge watch.
- **UNI: new queueing milestone, no qualifying entry.** Two public Ethereum
  RPCs agree at block **26,120,123** (Oct4 16:15:23 UTC): GovernorBravo
  `0x408ED6354d4973f66138C91495F2f2FCbd8724C3`, proposal **102**, state
  **Queued**, unexecuted, earliest eligible execution **Oct5 11:59:35 UTC**.
  Eta is eligibility, not a promised execution. Arc block **24,246,905**
  (16:15:27) still shows v2 feeTo zero, v3 owner the Wormhole receiver rather
  than the proposed fee adapter, and v4 protocolFeeController zero. The
  [Arc proposal](https://gov.uniswap.org/t/temp-check-protocol-fee-expansion-arc/26287)
  has not activated fees at this snapshot. UNI **$9.02** is above **$3.25**;
  actual activation and sustainable net burn after the 20M/year treasury
  budget remain separate conditions. No allocation follows from queueing.
- Selected ARB/AAVE holder-accrual, XLE, COHR and NVDA event gates supplied
  no qualifying new entry evidence. This is a bounded review of relevant
  conditions, not an exhaustive audit of every company's future catalysts;
  Aave buyback absence was not proved by a chain-wide transaction scan.

The digest's **LOW crypto-unlock** theme is not promoted: aggregate vendors
cover different windows/universes, and no token-specific schedule, float or
executable short was vetted. TVL/volume movements alone do not establish
holder returns. No asset action, new account or recurring task.

Public local evidence: `data/weekly_20261004T1600_watchlist.json`,
`data/weekly_20261004T1600_equity_quotes.json`,
`data/weekly_20261004T1600_event_review.json`,
`data/weekly_20261004T1600_uni_chain.json`; command metadata and reports in
`logs/weekly_20261004T1600/`. Root's chain proof supersedes the event helper's
dated-state limitation for UNI only. Existing scheduled checks cover changes.


### Oct-5 14:00 UTC — UNI102 executed; Arc activation remains unproved

Two independent public Ethereum RPCs agree at block **26,126,641** (14:04 UTC):
GovernorBravo `0x408ED6354d4973f66138C91495F2f2FCbd8724C3`, proposal **102**,
state **7 / Executed**, getter `executed=true`, `canceled=false`. Root decoded
both exact raw tuples independently. This advances the Oct4 queued milestone;
the elapsed 11:59:35 eligibility did not itself establish execution.

At Arc block **24,401,661**, v2 `feeTo` remains zero, v3 factory owner remains
`0xbca30b5429935205037069cf5b8a165f55d05a75` (not the proposed fee adapter
`0x927c7fd078fc406059957a691c21f6e0fc4a959c`), and v4
`protocolFeeController` remains zero. The
[Arc governance proposal](https://gov.uniswap.org/t/temp-check-protocol-fee-expansion-arc/26287)
has reached execution, but the checked controls do not establish Arc fee
activation. **Partial catalyst condition hit; no qualifying entry.** Monitor
UNI **$9.00** remains above **$3.25**. Require actual activation, sustained net
fee-funded burn after the 20M UNI/year treasury budget, and fresh lawful
route/depth/funding/gas checks. No price gate or sizing rule changed.

The 38-candidate price sweep had **37 WATCH + one AFMJF NO_DATA**. One bounded
retry of the original **AFMJF/USD** symbol returned **$0.985**, above its
**$0.85** threshold, closing this run’s missing-value gap. No source quote
time was supplied, so this is not a verified OTC last sale. The
[issuer](https://www.alphaminresources.com/) and
[TMX list](https://www.tsx.com/en/trading/market-data-and-statistics/market-statistics-and-reports/tsx-tsxv-moc-eligible-stocks)
confirm the primary TSXV:AFM/JSE:APH listings; the
[OTC AFMJF page](https://www.otcmarkets.com/stock/AFMJF/quote) could not load its
quote. OTC current trading status is unverified. A feed miss is not delisting,
and the CAD primary listing is not substituted for the USD trigger.

Evidence: `data/checkin_20261005T1400_sources/uni102_arc_current.json`,
`data/checkin_20261005T1400_afmjf.json`, and exact captures in
`logs/checkin_20261005T1400/`. No asset action or new scheduled follow-up.


### Oct-5 22:00 UTC — UNI Arc control configuration observed; no qualifying entry

The configuration catalyst advanced. Two Ethereum RPCs agree proposal102 is
Executed at fixed block **26,129,031**. Both return identical `getActions(102)`
responses; root canonically decoded all three peer/dispatch calls and the
embedded Arc `setFeeTo`, `setOwner`, `setProtocolFeeController` calls. Their
exact targets and destination addresses match the
[official Arc proposal](https://gov.uniswap.org/t/temp-check-protocol-fee-expansion-arc/26287).

Arc block **24,457,758**, independently reread by root at **24,458,129**:

| Control | Current documented destination |
|---|---|
| v2 feeTo | TokenJar `0xfd39ac616e630e9db03efb2c9a4fe63edb949233` |
| v3 factory owner | V3OpenFeeAdapter `0xa59ffbb55d91fc32b44a06f0b9cc6036a4afbce2` |
| v4 protocolFeeController | V4FeeAdapter `0x2f2bd3f43880b9644211f16d861b0672aab23782` |

All three changed since18:00, with nonempty runtime code at the destinations.
This proves intended control configuration; it does not quantify actual pool
collections, Releaser operations or sustainable net UNI burn. Reconcile burn
with the [20M UNI annual growth budget](https://blog.uniswap.org/unification)
before increasing valuation. Fresh CoinGecko UNI **$9.16**, timestamp
**22:04:40 UTC**, remains above the **$3.25** valuation review threshold.
No independently calibrated positive January excess-return case was established;
no project allocation, funding move or new position. Route/depth/gas evidence
from Sep30 remains dated and must be refreshed before any allocation.

**Address correction:** the Oct5 14:00 note misidentified `0x927c...959c`
as the proposed fee adapter. That is the proposal getter's proposer; the
published and encoded V3OpenFeeAdapter is `0xa59f...bce2`. Preserve the dated
raw observations: v2/v4 were zero and v3 belonged to the receiver then, so the
earlier inactive-control conclusion does not rely on that mistaken label.
Current rationale supersedes the old label without changing price/size gates.

Initial watchlist coverage was30 WATCH/eight crypto NO_DATA after CoinGecko429
and stale Blockstack fallback. One original-ID batch returned all eight fresh
prices (70–90s old at the22:05:50 read), closing the gaps; all remain above
unchanged price gates. AFMJF **$.970 USD** versus **$.85**, with last-sale/OTC
status and per-equity quote timestamps still unverified. No price trigger hit.

Evidence: `data/periodic_20261005T2200_uni_control_followup.json`, root Arc
revalidation and eight-ID price follow-up JSON. Direct implementation-source
Etherscan/Sourcify reads were blocked/unsupported; no implementation-source
verification or actual pool-fee/burn measurement is claimed. Worker follow-up
ended at model capacity; root completed the captured action/primary-role audit.
