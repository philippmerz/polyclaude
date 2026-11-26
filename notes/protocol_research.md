# Protocol research — living doc (VC-style, product-first)

Owner intent (Philipp, 2026-11-26): "expert VC intuition, not an auto-invest script… Which protocols actually
create value for the user?" Metrics are a pre-screen only; the call is made on the product.
Thesis only, not advice. Every number has a source + date; **[unverified]** = company/third-party claim not checked on-chain.

Pass 1: 2026-11-26 (Amsterdam). Market backdrop: BTC ~$60.6k (−30% 1y, −24% 30d), ETH ~$1,696 (−42% 1y).
Deep bear; almost every alt −20–60% in 30d. Relative-strength outliers over 1y (CoinGecko 2026-11-26):
VVV +2531%, HYPE +78%, NEAR +64%, ZEC +46%, XMR +31%, GEOD +16%. Privacy + AI-with-real-revenue + Hyperliquid
are the only things the market has paid for this year.

---

## 1. Venice post-mortem (what a good VC would have seen in late 2025)

Facts at the bottom (sources: CoinGecko history; Sacra; Eon Capital Apr-2026; Venice blog):
- VVV ~$1.02 / **mcap ~$42M on 2025-12-01** (ATL $0.92 that day). Now $27.6 / mcap $1.36B (FDV $2.25B; circ 49.3M of 81.3M total).
- Venice revenue ~**$10M annualised at end-2025** (Sacra estimate) → token traded at ~4x ARR of a profitable,
  self-funded consumer AI app. Now: $200M annualised claimed 2026-11-23 by Voorhees **[unverified — Raziel/AI Receipts
  label it "reported, not verified"]**; $70M+ at July Series A ($65M, Dragonfly, $1B post). → ~6.8x claimed ARR.
  **The 30x came almost entirely from revenue growth (~20x), not multiple expansion.**
- Product visible in late 2025: private/uncensored multi-model chat + OpenAI-compatible API, ~1.3M registered users
  (Oct 2025, r/VeniceAI year-in-review), founder Erik Voorhees (ShapeShift), no VC money, profitable.
- Token design visible in late 2025: stake-VVV-for-API-capacity (real utility for devs/agents), DIEM launched Aug 2025
  (1 DIEM = $1/day of credits forever; mintable only by locking sVVV), revenue buy-and-burn announced Nov 2025
  (first burn 2025-12-10), emissions already being cut (14M → 8M → 6M → 3M → 2M/yr by Oct 2026).
- Usage proof today: 5M users, >1T tokens/day in Oct 2026 (KR1 RNS 2026-11-12, citing Venice); OpenRouter-attributed
  ~2.52T tokens/month (routers.vantage.sh). Verifiable on-chain link to token is still thin: DefiLlama burn ≈ $1.05–1.08M/month
  (Oct/Nov 2026), ~$5.0M cumulative; ~70% of mcap staked.

Generalisable lessons:
1. **Paying users of a product people would use without a token** (privacy + no censorship + model choice), growing fast,
   at a tiny valuation (<5x ARR) — that is the whole setup. The token was cheap because the market treated it as an
   airdrop dump, not because the business was weak.
2. **Token must be the access key or the cash sink, not decoration.** Stake-for-compute + DIEM + revenue burns + falling
   emissions made usage growth mechanically reach the token. Ask "if usage 10x, what *forces* token demand?"
3. **Founder-market fit + no VC overhang + profitability** — survivable through a bear, no unlock cliff, no pressure to dump.
4. **Bear-market capitulation of a token with improving fundamentals** is the entry. Momentum (price) lagged the product by
   ~1 quarter (Jan–Mar 2026), so there was time to buy after the evidence turned.
Anti-lessons (don't overfit): Venice took a $1B equity round in Jul 2026 → equity is now a competing claim on the business;
the token captures only a policy-set slice (5% of credit purchases + per-sub burns + 10% of Minds markup).

---

## 2. Candidate universe (pass 1) and kills

Prices/mcap: CoinGecko API 2026-11-26 ~12:30 Amsterdam. Revenue: DefiLlama API same day unless noted.

| Area | Candidate | Verdict | One-line reason |
|---|---|---|---|
| Perps infra | **Hyperliquid (HYPE)** | **PICK (core)** | Best product in crypto; 99% of fees buy back HYPE ($79M/30d); see §3 |
| AI | **Venice (VVV)** | **PICK (small)** | Product winning; token has real sinks; price already prices a lot; see §3 |
| DePIN | **GEODNET (GEOD)** | **PICK (small)** | Non-crypto B2B customers (RTK positioning), ~8% burn yield; see §3 |
| DEX | **Aero (AERO)** | **PICK (speculative)** | Base's dominant venue at ATL, 100% revenue to stakers; revenue trend is the risk; see §3 |
| Privacy | Zcash (ZEC) | WATCH | Real private-money use (4.9M ZEC / ~29% shielded) but no cash flow; $12.4B after −77% from ATH; buy only on product catalyst |
| Privacy | Railgun (RAIL) | WATCH | Real product (private DeFi, $153M gross/30d, $4.1M/yr fees), fees to stakers ~10% yield, but revenue flat for 12 months; $92M mcap ≈ 22x |
| Consumer payments | ether.fi (ETHFI) | WATCH | Cash card is real (~$243M spend MTD Nov [DefiLlama-derived]); total rev ~$3.8M/30d vs $434M mcap (~9.5x); buyback tiny ($2.3M cum.) and recycled to stakers |
| Lending | Morpho (MORPHO) | WATCH | Excellent product (Coinbase Borrow ~$1.6–1.7B outstanding) but fee switch OFF → token captures $0; FDV $1.6B. Re-open if switch votes |
| Launchpad | Pump.fun (PUMP) | WATCH/KILL | Cheapest on holders-rev (~$219M/yr buyback vs $930M mcap) but revenue −37% m/m, supply +29.5% YTD despite $407M buybacks, product is extractive gambling; spot only on Solana |
| AI | Bittensor (TAO) | KILL | Subnet revenue ~$54–70M/yr vs ~$300M/yr emissions — usage is subsidised |
| AI | Chutes (SN64) | KILL | Cheap inference is paid for by TAO emissions; OpenRouter-attributed revenue ~$0.8–0.9M/yr. Incentive-driven, not product-driven |
| AI | Pearl (PEARL) | KILL | "Useful work" mostly synthetic (<1% blocks real AI [Blockworks/Dorm DAO]); ~86% more supply 2027; ~$760M mcap |
| AI | Virtuals, Kaito, io.net, Aethir, Gensyn | KILL | −56% to −78% 1y, no evidence users pay for the product beyond token farming (not individually underwritten this pass) |
| Stablecoin | Ethena (ENA) | KILL | USDe shrank to ~$4.5B, below $7.5B fee-switch trigger → no buybacks; −64% 1y |
| Stablecoin | Sky (SKY) | KILL | ~$2B USDS redeemed 2026-11-19, supply ~$3.1B; emergency buybacks = stress, not demand |
| Payments chains | Plasma (XPL), Stable, Tron | KILL | Stablecoin-rail value accrues to Tether/issuers, not chain tokens; XPL −77% 1y; TRX ~100x holder rev, centralised |
| Perps | Lighter (LIT), Aster | KILL | Real volume but fighting HL with incentives; LIT ~$11M/week unlocks, FDV 4x mcap; ASTER FDV 3x mcap, −54% 1y |
| Perps | Papertrade (PAPER) | KILL | "Revenue" = trader losses; PAPER only mintable by losing, non-transferable → can't buy; reflexive farming |
| Options | Derive (DRV) | KILL | $7.45B Q3 notional but take rate falling; buyback ~$3.2M/yr vs 500M new DRV minted |
| DEX | Uniswap (UNI) | KILL (for now) | Fee switch live but ~$6M/month burns vs $2.9B mcap (~40x); aggregation share gain is real but priced |
| DePIN | Helium (HNT) | KILL | Helium Mobile sold to Noble (Jun 2026), subscriber buyback stopped Jan 2026, −90% 1y |
| Restaking | EigenLayer (EIGEN) | KILL | −82% 1y; no user-facing product pull |
| Prediction mkts | Polymarket / Kalshi / Limitless | NO TOKEN / KILL | Polymarket has no token (help centre 2026-06-24; POLY trademark only). Exposure = HYPE (HL outcomes fees buy HYPE). Our own PM activity is free optionality on any future airdrop **[speculative]** |
| Wallets | MetaMask "MASK", Base token | NO TOKEN | Neither exists; any "MASK" on market is Mask Network, unrelated |
| L1 | NEAR | WATCH | Intents $4.1B/30d real cross-chain volume, but $1.3M/month buyback vs issuance; $4.0B mcap |

---

## 3. Deep dives

### 3.1 Hyperliquid (HYPE) — keep as anchor; first in line for any core rebalance
- **User value:** self-custodial perps/spot with CEX-grade UX, no KYC, deepest on-chain liquidity; HIP-3 lets anyone list
  markets (equities via trade[XYZ]; HIP-3 = 43.8% of Nov volume [HRC data]); outcome markets. Users come for execution,
  not points — the airdrop ended in 2024 and volume kept growing (perps category Oct-2026 ≈ 9x Oct-2025, Apeiros).
- **Value accrual:** 99% of perp/spot/outcome fees (ex-builder codes) → Assistance Fund buys HYPE, burned.
  $79.0M bought in 30d to 2026-11-25 (+24% m/m, Castle Labs/DefiLlama); $682M revenue trailing 1y (DefiLlama).
- **Supply:** circ ~238M (CoinGecko) of ~950M total; team unlock schedule 9.92M/month but only ~180k actually distributed in
  Nov [cryptoticker]. Daily buyback ~21.2k HYPE vs ~26.9k staking emission → mildly net inflationary day to day [coinperps].
- **Valuation:** $14.4B circ / $57.6B FDV vs ~$960M annualised holder revenue → ~15x circ, ~60x FDV.
- **Risks:** FDV overhang if insiders start selling; competitor incentive wars (Lighter/Aster); regulatory (no MiCA licence;
  HL ToS restricts US/Ontario/sanctioned only); validator centralisation; a hack.
- **Invalidation:** 30d holder revenue < $40M for two consecutive months, or insider distributions > 2M HYPE/month sold to market.

### 3.2 Venice (VVV) — still the best AI×crypto product; small, buy weakness
- **User value:** private + uncensored chat/media + OpenAI-compatible API in one wallet; 5M users, >1T tokens/day (Oct 2026,
  Venice via KR1); 2.52T tokens/month routed via OpenRouter (third-party estimate). People pay $18–200/month for it —
  that is not incentive farming.
- **Value accrual:** 5% of API-credit purchases + $2/$5/$10 per new Pro/Pro+/Max sub + 10% of Venice Minds markup buy & burn
  VVV; DIEM (needs locked sVVV) gives $1/day credits → ~70% of mcap staked. Verifiable burns ~$1.05–1.08M/month (DefiLlama);
  weekly buybacks $628k Nov 9–15 [CMC coverage]. Emissions 2M VVV/yr since 2026-10-01 (~4% of circ) — burns (~40–50k VVV/month at
  current prices) still below emissions → not yet net deflationary.
- **Valuation:** $1.36B circ / $2.25B FDV; ~6.8x claimed ARR [unverified]; equity marked $1B in July at ~$70M ARR.
- **Risks:** equity/token misalignment (the company can grow without the token); claimed revenue unverified; content-liability
  (deepfakes → app store / payment processor risk); upstream model dependence; 32M non-circulating VVV (composition not checked).
  Price is momentum-driven right now (HTX listing, Hayes $40 target) → bad entry timing.
- **Why now:** emission cut just took effect; Minds marketplace adds a new burn source; but wait for a pullback.
- **Invalidation:** monthly on-chain burn falls below $0.7M for 2 months, or any move to route value to equity instead of VVV,
  or OpenRouter-attributed tokens drop >40% from Nov 2026 level.
- Note: **DIEM** (~$2,100, Base, Aerodrome DIEM/VVV ~$10M liq) = perpetual $365/yr inference-credit stream (~17% gross if
  monetised at par; wstDIEM vault reports ~10.5% APY). Interesting fixed-income-like instrument; not for us at this size.

### 3.3 GEODNET (GEOD) — real B2B DePIN, cheap, low overhang
- **User value:** centimetre-level RTK GNSS corrections for drones, tractors, survey, construction, robots. 22k+ base
  stations in ~174 countries; 165+ enterprise customers; DroneDeploy integration (Apr 2025). Customers are not crypto users and
  pay because it is cheaper/wider than incumbent RTK networks [company-reported ARR $10.64M, Oct 2026 — **unverified**].
- **Value accrual:** 80% of data-service revenue (definition unclear vs 2025 filing: 50% to Foundation × 80%) buys & burns GEOD.
  DefiLlama burn-derived "revenue" ~$0.9M/month (Oct 2026 $0.94M; Q3 burns $2.22M, +127% y/y but only +7% q/q).
- **Supply:** CoinGecko circ 754M / total 926M / max 1B → FDV only ~1.2x circ. (Ravel Oct-2026 cited much lower circ — reconcile next pass.)
  Mining rewards still ≈ burns on a daily basis (84.5k minted vs 70k burned on 2026-10-24).
- **Valuation:** $135M mcap / $166M FDV; ~8% annualised burn/mcap; ~10x circ / ~12x FDV on burn-derived fees (~$13.5M/yr).
- **Liquidity/venue:** Polygon QuickSwap GEOD/USDT0 ~$370k liquidity, $115k/24h (DexScreener) — fine for $5–10. On Polygon,
  where we already hold POL gas.
- **Risks:** revenue only visible via burns (self-referential); growth slowed in Q3; Trimble/Hexagon/John Deere incumbents;
  token can go nowhere even if business wins.
- **Invalidation:** two consecutive months of burn < $0.6M, or evidence revenue-share was reduced.

### 3.4 Aero (AERO) — Base's liquidity hub at an all-time low (speculative)
- **User value:** 58–66% of Base DEX volume in Nov 2026 (Vantemio daily); Coinbase app swap integration completed 2026-11-07, plus
  0x/KyberSwap routing. Traders don't "choose" Aero — aggregators route to the best liquidity — so the moat is liquidity +
  distribution, bought with emissions. That is weaker than Venice/HL-style product pull.
- **Value accrual:** 100% of exchange revenue to sAERO stakers; avg sAERO APR 27.4% (Dromos, 2026-11-13). Momentum Fund buys
  (110.9M AERO lifetime; only 911k burned so far).
- **Supply:** 2.15B total, 50.2% staked; emissions gauge-capped to revenue (hard cap 20%/yr); MrNasDog estimates +10% supply in
  the last 90 days (incl. Velodrome swap) and ~+5% next 90.
- **Valuation:** $0.40 × 2.15B ≈ $870M (CoinGecko's $91M mcap only counts the old token — wrong). Revenue: DefiLlama ~$85M
  trailing 1y; Aero's own Dune dashboard shows **quarterly revenue down from $111M (Q4-24) to $25.8M (Q3-26)**; Q4-26 projected $21.4M.
  → ~10x trailing revenue but on a shrinking base.
- **Risks:** revenue decline tracks Base meme/activity cycles; merger complexity; Uniswap v4 hooks on Base.
- **Why now:** ATL ($0.37 on 2026-11-21, −53% from post-merger top), fresh Coinbase distribution.
- **Invalidation:** Q4-26 revenue < $18M or Base DEX share < 45% for a month.

---

## 4. Ranked shortlist + proposed basket (research only — NOT traded)

Account ~$156 (2026-11-25 review): PM ~$70, WBTC ~$56, Arbitrum ETH ~$13, HL HYPE ~$10, HL USDC $0.70. Free cash ~$1.

| Rank | Pick | Size | Venue (no KYC) | Rule |
|---|---|---|---|---|
| 1 | HYPE | keep; next core rebalance goes HYPE-first (e.g. +$5 from WBTC) | Hyperliquid spot | thesis §3.1 |
| 2 | VVV | $6 starter, +$4 if −30% from entry with burns intact | Base (Aerodrome/Uniswap VVV/WETH, ~$7M+ liq) | stop if invalidation §3.2 hits |
| 3 | GEOD | $5 | Polygon QuickSwap | §3.3 |
| 4 | AERO | $4 (optionally stake as sAERO) | Base | §3.4; hardest stop |
| — | ZEC / RAIL / MORPHO | $0 now, watchlist | HL perp (ZEC) / Ethereum (RAIL) / Base (MORPHO) | trigger-based |

- **Total new sleeve ~$15 (≈10% of account)**, funded by trimming WBTC $56 → ~$41 (+$5 to HYPE if we do it), keeping total
  crypto ≈ unchanged. Bridge path: Arbitrum ETH/WBTC → Base via Across (do NOT use the dirty `scripts/across_bridge.py`
  30-gwei tip version); Polygon USDC → GEOD on QuickSwap.
- **Hedge logic:** spread across 3 uncorrelated value drivers (AI subscriptions, physical-world B2B, Base DEX fees) + the
  BTC/ETH/HYPE core. A beta hedge (short ETH perp on HL) is not worth it at this size (HL USDC $0.70); revisit if sleeve > $40.
- **Legal (NL):** spot DEX swaps on Base/Polygon from a self-custodied wallet; HL ToS restricts only US/Ontario/sanctioned
  but HL holds no MiCA authorisation — same footing as our existing HL use. No VPN/proxy. HL perps cost ~0.00125%/h funding
  (~11%/yr) → prefer spot.
- Gas: Base/Polygon swaps cost cents; batch.

---

## 5. Research cadence (proposed)
- **Every operator session:** one protocol deep-dive (product → user evidence → value accrual → supply → valuation → kill/keep),
  appended here under §6 with date. Rotate: watchlist triggers first, then new categories.
- **Weekly (Mon evening review):** re-underwrite every held pick against its invalidation lines; refresh the §2 table numbers.
- **Monthly:** relative-strength scan (1y/90d winners in a down market) → ask "what product is behind this?" — this is the
  scan that would have flagged VVV by Feb–Mar 2026.
- Sources to reuse: DefiLlama API (`/summary/fees/<slug>?dataType=dailyRevenue`), CoinGecko API, Castle Labs buybacks,
  routers.vantage.sh (OpenRouter share), DexScreener (liquidity), project dashboards (Aero Dune, Railscan, Helium snapshot).

## 6. Log
- 2026-11-26 pass 1: universe of ~35, 4 picks, 6 watch, rest killed. Next: reconcile GEOD circulating supply; check sAERO
  liquidity/lock terms; Venice OpenRouter share trend; NEAR Intents fee capture; look for a privacy-app token with paying users.
