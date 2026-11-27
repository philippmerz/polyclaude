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
| Privacy | Railgun (RAIL) | WATCH (deep-dived §3.5, 2026-11-26) | Best paying-user privacy product on EVM (record 13.9k tx/month, stablecoins 77% of flows, no incentives) at $91M/$1.52, but only ~45% of fees reach stakers (USDC/USDT fees undistributed), 40M mintable overhang, live RICO default suit. Triggers in §3.5 |
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


### 3.5 Railgun (RAIL) — the real private-dollar rail; token is a leaky claim (WATCH, armed triggers)
Data 2026-11-26 ~14:00 Amsterdam: CoinGecko, DefiLlama API (fees/holdersRevenue/TVL), DexScreener, Alea Research (4 Nov 2026,
on-chain), CourtListener docket 1:26-cv-00179.
- **User value (product pull, not incentives):** zk-SNARK shielded pool on Ethereum (+Arbitrum/BSC/Polygon, Base approved):
  private balances, transfers, swaps and, since wallet SDK 11.2.0 (30 Sep), private DeFi positions (Aave/Morpho) through
  single-use EIP-7702 accounts; wallets adopted it within a week (weekly unshields to the old shared relay 612 → 21, single-use
  accounts 0 → 559 [Alea]). Users pay 0.25% to shield and 0.25% to unshield, and there are **no liquidity-mining or points
  incentives**. Usage: record 13,918 private tx in Sep 2026 (+65% y/y), Jan–Sep 94.7k (+58%); Sep stablecoin flows $117.5M
  (+94% y/y), **stablecoins = 77% of flow value** (payroll/treasury/trader privacy, i.e. private dollars). TVL $97M (ETH $93M).
  Distribution: Railway, Terminal, Anon (mobile); Ambire via EF's Kohaku toolkit is next (demoed at Devcon 3 Nov, no ship date;
  the Kohaku repo lists Railgun as "under maintenance" while Privacy Pools/Tornado show as available).
- **Revenue:** DefiLlama fees $4.13M trailing 1y; monthly 2026 ($k) Jan 353, Feb 331, Mar 319, Apr 382, May 331, Jun 294, Jul
  329, Aug 305, Sep 386, Oct 345, **Nov 356 MTD (26 d) → ~$410k pace, best month of 2026**. In $ terms fees are flat-to-down vs
  2025 (Aug–Oct 2025 $462–566k) because ETH fell; in transactions and stablecoin terms usage clearly grew. The token
  price did not follow: RAIL −38% 30d / −50% 1y while fees rose (CryptoBrief: fees +63% w/w the week RAIL fell 24%).
- **Value accrual (the weak link):** every fee goes to an on-chain treasury; every 2 weeks 4.2% (2% before the 22 Jul vote) of
  the treasury's **WETH, DAI and RAIL** becomes claimable by stakers. **USDC/USDT are outside the schedule** [Alea], and those are
  now ~77% of flows → only part of the fee intake reaches stakers. DefiLlama holders revenue $1.76M trailing 1y, $176–225k/month
  since July (~$2.4M/yr run rate ≈ 45–55% of fees). Oct 21 payout: 35.0 WETH + 15.7k DAI + 88.8k RAIL. No buyback or burn.
- **Supply:** 100M max, 60M minted; the DAO can mint the other 40M by vote (it minted 2.5M to the treasury with the July vote).
  Staked 42.5M (70.9%). There are no VC unlock cliffs, but the mint headroom is a governance-controlled overhang (+67% potential).
- **Valuation:** $1.52 → mcap $91.3M, $152M at the 100M cap. ~21x trailing fees (35x at cap); **~38x holder cash** (run rate).
  Staker cash yield ≈ $2.4M / $64M staked ≈ 3.7%, plus ~2.3M RAIL/yr of recycled treasury RAIL (≈5% of staked; a transfer from
  non-stakers, not income). Comparables: HYPE ~15x circulating holder revenue, GEOD ~10x burns, ZEC $12.4B with zero cash flow.
  So RAIL is cheap as a privacy asset (≈1/130 of ZEC) but not cheap as a cash claim.
- **Risks:** (1) **Legal:** Kim v. Railgun DAO (D.D.C., RICO + negligence, terrorism-judgment creditors of DPRK; FBI tied $60M+
  of Harmony-hack ETH to Railgun in Jan 2023). Clerk's default entered 10 Apr 2026; default-judgment motion sought $193.5M /
  124,923 ETH; **order on it entered 19 Nov (ECF 23, content not public to me), notice of voluntary dismissal 24 Nov (ECF 25;
  scope unknown, maybe DCG only)**. Staking = voting = "DAO member" exposure on Ooki-style theories. (2) Compliance-first
  competitors with no token (0xbow Privacy Pools) ship first in Kohaku, and Ethereum-native privacy could commoditise the pool.
  (3) PPOI circuit flaw disclosed Oct 2026 (zkNoX; fixed). (4) Token liquidity: ~$6M DEX liquidity on Ethereum mainnet
  (Uniswap v2/v3 RAIL/WETH $1.07M/$3.95M, Sushi $0.89M), ~$118k/day volume.
- **Why now / why not:** the product inflection (private stablecoins + private DeFi positions + wallet distribution) is real and
  the token is −37% since the 27 Oct Alea piece while usage set records. That is the Venice-2025 shape. It is not yet the
  Venice-2025 *token*: the token gets less than half the fees, can be diluted by vote, and carries an open RICO docket.
- **Verdict: WATCH, not a conviction pick. No entry today.** Arm a $5 entry (Ethereum mainnet Uniswap v3 RAIL/WETH via Kyber;
  Across Arbitrum→Ethereum; gas ~0.15 gwei ≈ cents; hold unstaked at first) only when **(a)** a passed protocol request adds
  USDC/USDT to the staker distribution or adds a buyback (holder cash ~2x → ~20x), **or (b)** the docket shows default judgment
  denied or the whole case dismissed, **plus (c)** monthly fees ≥ $400k for two months (Nov pace qualifies if it holds).
  Price guide: ≤ $1.60 with (a) or (b). **Kill** if a default judgment is granted against the DAO/treasury, a mint beyond 2.5M/yr
  passes, or monthly fees < $280k for two months.

### 3.6 Maple Finance (SYRUP) — on-chain credit at −75% 1y; cheap on revenue, broken on trust (WATCH, armed triggers)
Data 2026-11-27 ~09:30 Amsterdam: CoinGecko, DefiLlama API (revenue/holdersRevenue/TVL), DexScreener, Bitquery investigation
(syrupUSDC loans), OnChain Benchmark (redemptions to 15 Nov), Alea Q3-2026 benchmark, Maple transparency page (Network Firm, 24 Nov),
Cointelegraph/FinScans (12–13 Nov exits).
- **User value (real, but concentrated):** syrupUSDC/syrupUSDT = permissionless deposits lent over-collateralised (BTC/ETH/XRP)
  to trading firms and prime brokers (Bitquery traces cash to FalconX, Galaxy, an exchange reserve). Depositors earn ~5% (Q3
  4.96%, ~1pp over T-bills); borrowers pay ~5.9–6.2%. This is genuine demand from both sides — no points farming needed for
  borrowers — but the deposit side was dominated by a few allocators (Sky's Spark/Grove/Obex held 63% of syrupUSDC at Jun 30).
- **Organic vs incentive:** deposits partly rode DeFi integrations (Aave/Morpho/Pendle loops, Drips points earlier). The test is
  happening now: TVL $2.81B (20 Sep) → **$1.84B (27 Nov)**; syrupUSDC net redemptions $177.5M in 30d to 15 Nov (−16.7% tokens);
  transparency page shows syrupUSDC deposits **$617M** (24 Nov) vs $1.01B at Sep 30. Sky/Spark exited.
- **Trust problem (the real reason for −57% 30d):** Bitquery (Nov): on 7 Apr **70% of syrup loans ($1.75B) were owed by six
  Maple-run wallets at ~2.7%** vs ~7% for trading firms, tagged "AMM liquidity / T-bills / intercompany"; coverage dipped to 75.6%
  of loans on 1 Mar; cost to depositors $4–18M of foregone interest. Now $93M at 1.6% (a third of syrupUSDT's book). Co-founder/
  exec chair Joe Flanagan and COO Ryan O'Shea quit over a strategy rift with CEO Sid Powell (12 Nov; O'Shea effective today 27 Nov);
  Powell is pivoting to fintech receivables / mortgage-backed loans (more credit risk, less transparency).
- **Revenue:** DefiLlama revenue ($k/month) Oct-25 1,298 · Jan 1,150 · Apr 1,322 · May 799 · Sep 1,625 · Oct 1,556 · Nov 1,176 MTD
  (≈$1.3M full-month pace). Trailing 1y $14.8M. Management fee raised Aug (8.33% → 15% syrupUSDC) — revenue held up by taking a
  bigger cut from shrinking deposits. Forward run-rate with deposits −35–60% from peak: ~$9–12M/yr.
- **Value accrual:** token holders get only the buyback (≈25% of revenue → stSYRUP). DefiLlama holders revenue: $3.0M trailing 1y,
  Jul–Nov $103–325k/month (~$2.4M/yr run rate). Maple Inc. (the company) keeps the rest; SYRUP is not equity.
- **Supply:** 1.268B total / 1.167B circ (92%); FDV $94M — little cliff overhang. Ongoing staking emissions (historically ~5%/yr
  to stSYRUP **[unverified current rate]**) roughly offset the buyback.
- **Valuation:** $0.0745 → mcap $87M. **~6x trailing revenue, ~9x forward run-rate, but ~36x holder cash** (~$2.4M). Comps:
  JUP ~$823M mcap / $38M holders rev ≈ 22x; PENDLE ~$215M / $8.4M ≈ 25x; HYPE ~15x; RAIL ~38x. So SYRUP is cheap only if you
  believe the business, not the token, gets valued — and the token has no claim on the business beyond a discretionary buyback.
- **Liquidity/route:** Ethereum Uniswap SYRUP/ETH ~$0.98M liquidity, $171k/24h; Base Aerodrome ~$16k. A $5 buy is trivial
  (Arbitrum→Ethereum via Across, cents of gas).
- **Risks:** (1) run dynamics — callable one-day loans (~1.2x Obex's balance in Oct) cover redemptions today, but a further leg
  down shrinks revenue and the buyback mechanically; (2) related-party lending and governance (founder exit, no chairman named);
  (3) pivot into opaque fintech/mortgage credit = real default risk, which is what killed Maple v1 in 2022 (Orthogonal);
  (4) emissions vs buyback; (5) competition: Morpho/Aave institutional vaults and tokenised T-bill products at similar yield.
- **Why now / why not:** it is the "good product, token −75%" shape, and on revenue it is the cheapest lender on-chain. But
  unlike Venice-2025 the product metrics are **deteriorating**, the drop has a specific governance cause, and the token's claim
  is thin. Falling knife until deposits stop leaving.
- **Verdict: WATCH (not a conviction pick). No entry.** Review trigger (all of): (a) DefiLlama TVL ≥ $1.6B and flat-or-up for
  4 consecutive weeks; (b) monthly revenue ≥ $1.1M for Dec and Jan; (c) a governance change that raises holder capture (buyback
  ≥ 50% of revenue, or emissions cut) **or** an independent attestation that related-party loans are wound down (< 5% of book).
  Then $5 at ≤ $0.08 on Ethereum Uniswap. **Kill** if TVL < $1.2B, any loan impairment/default or depositor loss, or Powell exits.

---

## 4. Ranked shortlist + proposed basket (pass-1 proposal; superseded by §7 decision 2026-11-26)

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

## 7. Decision 2026-11-26 ~13:30 Amsterdam (fresh-eyes re-underwrite; Philipp t79u: "elite… not a random gambler")

**Result: bought nothing today. No WBTC trim. Two conditional entries armed in `notes/watchlist_triggers.json`; AERO killed.**

Live check (CoinGecko ~13:20, Kyber/Across quotes ~13:25):
- VVV $27.82 (+10.7% 24h, +20.4% 7d); GEOD $0.1795 (−8.9% 7d, −26% 30d); AERO $0.402 (−40.5% 30d); BTC $60.6k; HYPE $60.5.
- Execution is NOT the constraint: Kyber quotes $5 USDC→GEOD (Polygon) out $4.985 + $0.012 gas (~0.5%); $6 USDC→VVV (Base)
  ~0.0% impact + $0.006 gas; WBTC→USDC (Arbitrum) ~0.0% + $0.02; Across Arbitrum→Polygon $0.007, →Base $0.004 (min deposit $0.50).
- Burns (DefiLlama monthly, Nov MTD to 26th): Venice $1.08M (Oct $1.06M); GEODNET $0.76M (Oct $0.94M).

Open items resolved:
- **GEOD supply:** CoinGecko's circulating figure jumped from ~460M (mid-Oct) to ~745M (1 Nov) → methodology catch-up, not a
  surprise mint: Blockworks shows mining 100%, investors 100%, team 95% unlocked. ~754M circ / 1B max. Remaining: **15.94M
  cliff on 2026-11-28** (12.5M = last team tranche, ≈2.1% of circ, ≈$2.9M vs ~$0.44M daily volume), then ~3.44M/month
  (ecosystem/public sale/vendors). Ravel's lower October circ was the stale CG number.
- **AERO staking:** sAERO is an ERC-721 lock of 6 months–4 years (perpetual = 4y countdown to exit); no early unstake; NFT
  transferable but illiquid. Plain spot AERO receives **none** of the exchange revenue and is diluted by LP emissions.

Per name:
- **VVV — skip at $27.8, armed at ≤ $22.** Best product in the set, but at this entry I'd be buying a listing/"Hayes $40"
  momentum leg, not the Dec-2025 setup (4x ARR, unknown). Burns are ~1%/yr of mcap; the rest is narrative + DIEM demand. It
  swings ±20% within days (high $30.47 on 11-25, low $24.54 same day), so patience is cheap. Trigger needs monthly burn ≥ $0.9M.
- **GEOD — wait 2 days, then $5 if ≤ $0.20.** Most Venice-like fundamentals (non-crypto paying customers, near-fully vested), but
  buying 48h before the final team cliff is avoidable. Also burns dipped in Nov — needs Nov ≥ $0.70M to keep the thesis.
- **AERO — KILL (for us).** Revenue accrues only to locked sAERO (≥6-month illiquid lock); spot is diluted; revenue base
  shrinking ($111M Q4-24 → $25.8M Q3-26). Revisit only if a liquid sAERO wrapper appears AND Q4-26 revenue ≥ $21M.
- **HYPE:** unchanged core; still first in line if the core is rebalanced.

Honest read: none of today's names is an asymmetric Venice-2025 setup; they are good businesses at roughly fair prices. The
asymmetric hunt continues (§5 cadence; relative-strength-in-a-bear scan; privacy apps with paying users).

Accounting on entry: bankroll.py does not read VVV/GEOD. Until it is extended, the evening review must add
`balanceOf` × CoinGecko price for VVV (Base `0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf`) and GEOD (Polygon
`0xAC0F66379A6d7801D7726d5a943356A172549Adb`) on the crypto-sleeve address, same as the WBTC/HYPE lines.

## 6. Log
- 2026-11-26 13:30: §7 decision — no buys; VVV ≤$22 and GEOD post-11-28 ≤$0.20 triggers armed; AERO killed (lock).
- 2026-11-26 pass 1: universe of ~35, 4 picks, 6 watch, rest killed. Next: reconcile GEOD circulating supply; check sAERO
  liquidity/lock terms; Venice OpenRouter share trend; NEAR Intents fee capture; look for a privacy-app token with paying users.
- 2026-11-26 14:15: §3.5 Railgun deep dive → **WATCH** (no buy). Product pull is real (record tx, 77% stablecoin flows, no
  incentives, Nov fees ~$410k pace) at $91M / $1.52, but stakers get ~45–55% of fees (USDC/USDT undistributed), ~38x holder cash,
  40M mintable, open RICO docket (ECF 23 order 19 Nov, ECF 25 dismissal notice 24 Nov, contents unread). Trigger: stablecoin fees
  added to distribution OR buyback, or suit dismissed/denied, + fees ≥$400k x2 months → $5 at ≤$1.60. Next: read ECF 23/25;
  NEAR Intents fee capture.
- 2026-11-27 09:40: §3.6 Maple (SYRUP) deep dive → **WATCH** (no buy). Real two-sided credit product, ~6x revenue at $87M, but TVL −35% since Sep, Bitquery related-party-loan exposé, founder/COO exits, token gets only ~25% buyback (~36x holder cash). Trigger: TVL ≥$1.6B flat 4w + rev ≥$1.1M/mo ×2 + holder-capture or related-party fix → $5 ≤$0.08. Next: NEAR Intents fee capture; JUP (22x holder cash, 50% buyback) as next lender/aggregator comp.
