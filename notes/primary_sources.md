# Primary fact sources for first-principles world-state digestion

> Curated list of high-quality FACTUAL sources organized by domain. Used by `scripts/world_state_digest.py` to assemble bare-fact world-state snapshots that bypass narrative-outlet framing.
>
> **Principle.** Retail-analyst pipeline (outlet → analyst → market → retail) has 3-4 layers of narrative compression. LLM operating from bare facts skips the narrative step. Pre-made inferences from outlets serve as PUBLIC-OPINION data (useful for reflexivity/Schelling) not truth (useful for fundamental valuation). Source quality determines edge.
>
> Created 2026-05-08. Iteration cadence: review monthly, add sources as new factual primaries appear.

## Selection criteria

Each source must:
- Publish RAW facts: numerical data, official statements, regulatory filings, primary statistics — not editorial framing
- Update on a regular cadence so a periodic digest catches changes
- Be reasonably stable (URL longevity, not behind hard paywalls for the digest)
- Provide depth in a specific domain rather than thin coverage of everything

## Domain: Macro / fiscal / labor

- **BLS** (Bureau of Labor Statistics) — CPI, employment, wages: https://www.bls.gov/news.release/
- **BEA** (Bureau of Economic Analysis) — GDP, personal income/spending, trade: https://www.bea.gov/news
- **Fed** — FOMC statements, dot plots, beige book: https://www.federalreserve.gov/newsevents.htm
- **CBO** — fiscal projections, budget scoring: https://www.cbo.gov/about/products
- **Treasury** — TIC data, debt issuance schedules, FX intervention: https://home.treasury.gov/news
- **ECB** — eurozone monetary policy, inflation: https://www.ecb.europa.eu/press/pr/html/index.en.html
- **BoJ** — yen monetary policy: https://www.boj.or.jp/en/announcements/index.htm
- **PBOC** — China monetary aggregates, FX reserves: https://www.pbc.gov.cn/en/3688110/index.html

## Domain: Energy / power infrastructure

- **EIA** (Energy Information Administration) — oil/gas/coal/electricity production + consumption + prices: https://www.eia.gov/
- **DOE** — loan program, SMR funding, advanced nuclear allocations: https://www.energy.gov/news
- **NRC** (Nuclear Regulatory Commission) — reactor licensing, restart approvals (e.g., Three Mile Island): https://www.nrc.gov/reading-rm/doc-collections/news/index.html
- **FERC** — capacity markets, interconnection queue, rate cases: https://www.ferc.gov/news-events
- **IAEA** — global nuclear inventory, enrichment, IAEA-Iran reports: https://www.iaea.org/news
- **OPEC** — production quotas, monthly oil-market reports: https://www.opec.org/opec_web/en/press_room/index.htm

## Domain: Critical minerals / commodities

- **USGS** (US Geological Survey) — Mineral Commodity Summaries, critical minerals list: https://www.usgs.gov/programs/mineral-resources-program
- **State Dept FORGE** — minerals diplomacy bilaterals, MOUs: https://www.state.gov/key-topics-bureau-of-energy-resources/
- **DFC** — equity stakes, project finance announcements: https://www.dfc.gov/who-we-are/news
- **LME** — base metals warehouse stocks, prices: https://www.lme.com/Market-Data
- **CME** — agricultural / metal futures: https://www.cmegroup.com/markets.html
- **USDA WASDE** — global ag supply/demand monthly: https://www.usda.gov/oce/commodity/wasde

## Domain: Trade / regulation

- **USTR** — trade-act actions, tariffs, plurilateral pacts, Section 301: https://ustr.gov/about-us/policy-offices/press-office
- **Commerce Dept BIS** — export controls (chips, AI, biotech): https://www.bis.doc.gov/index.php/2018-03-11-21-23-30
- **OFAC** — sanctions designations: https://ofac.treasury.gov/recent-actions
- **CFIUS** — investment screening (annual report + announced cases): https://home.treasury.gov/policy-issues/international/the-committee-on-foreign-investment-in-the-united-states-cfius

## Domain: Tech / AI / chips

- **NVIDIA earnings + 10-Qs** — datacenter revenue, Hopper/Blackwell shipments: https://investor.nvidia.com/financial-info/financial-reports/default.aspx
- **TSMC monthly revenue + capex** — advanced node demand: https://investor.tsmc.com/english/announcement
- **SEMI** — global fab equipment shipments: https://www.semi.org/en/news/billing-report
- **AI policy: NIST AI Safety Institute, Center for AI Safety, OSTP** — for fact-collection on government posture

## Domain: Biotech / health

- **FDA** — approvals, breakthrough designations, adverse-event databases: https://www.fda.gov/news-events/fda-newsroom/press-announcements
- **NIH** — funding announcements, clinical trial registrations: https://www.nih.gov/news-events/news-releases
- **WHO** — disease outbreak news (DON), pandemic declarations, framework conventions: https://www.who.int/emergencies/disease-outbreak-news
- **CDC MMWR** — surveillance data, weekly: https://www.cdc.gov/mmwr/index.html
- **EMA** (European Medicines Agency) — EU approvals: https://www.ema.europa.eu/en/news

## Domain: Geopolitics / security

- **DoD official briefings + press releases** — Pentagon posture, troop deployments: https://www.defense.gov/News/
- **State Dept** — diplomatic readouts, sanctions, treaty filings: https://www.state.gov/department-press-briefings/
- **CRS reports** — congressional research, neutral analytical framing: https://crsreports.congress.gov/
- **NATO official + summit communiqués** — alliance posture: https://www.nato.int/cps/en/natohq/news.htm
- **UN Security Council** — resolutions, presidential statements: https://www.un.org/securitycouncil/

## Domain: Crypto / on-chain

- **DefiLlama** — TVL, fees, revenue per protocol: https://defillama.com/
- **Etherscan / Polygonscan / Solscan** — on-chain raw data
- **Dune dashboards** — community-curated metrics
- **Tokenomist** — vesting schedules, unlock calendars: https://tokenomist.ai/
- **CoinGecko / CoinMarketCap** — market caps, price history (factual not editorial)
- **L2Beat** — L2 TVL + risk profiles: https://l2beat.com/

## Domain: Markets / corporate

- **SEC EDGAR** — 10-K, 10-Q, 8-K filings: https://www.sec.gov/edgar/searchedgar/companysearch
- **Fed FRED** — economic data series: https://fred.stlouisfed.org/
- **FactSet earnings calendar** (or via brokerage): forward earnings dates
- **Polymarket gamma-api** — prediction market raw data: https://gamma-api.polymarket.com/

## Wire services (factual reporting baseline)

These are CLOSER to facts than opinion outlets — used for breaking factual events with caveat that even wires have framing:

- **Reuters Top News + Markets**: https://www.reuters.com/world/, https://www.reuters.com/markets/
- **Bloomberg Markets** (paywall but headlines free)
- **AP** (Associated Press): https://apnews.com/

## Explicit EXCLUSIONS (narrative-heavy, use only as opinion-tracking)

- Twitter/X: signal-to-noise too low at scale
- Cable news (CNN/Fox/MSNBC): heavy narrative
- Political opinion outlets (NYT op-ed, WSJ op-ed): editorial framing
- Substack newsletters / blogger ecosystem: useful for theme-spotting but high noise
- Crypto-Twitter influencer takes: pure narrative

These can serve as "what is the crowd believing?" data when the question is reflexivity-related, but NEVER as primary fact sources for fundamental valuation.

## How `world_state_digest.py` uses this list

Periodic digest:
1. Pulls latest factual updates from N sources per domain (rotating to keep token cost bounded)
2. Aggregates into a single document with timestamps + source attribution
3. Spawns `claude -p` with the document + prompt: "what asset categories or specific tickers are underpriced given THESE FACTS?"
4. Output: structured candidate list to feed into `longterm_check.py` for individual-ticker vetting

Cadence: weekly Sunday baseline + on-demand for specific themes.

## Iteration

This list will evolve. New primary sources discovered → add. Sources that turn out to be heavily narrative → demote to opinion-tracking. Quarterly review.
