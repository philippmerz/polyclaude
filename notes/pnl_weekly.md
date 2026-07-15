# Polyclaude — Weekly P&L and Decision Log

> Append-only. Most recent at bottom. Each entry is a verbose-decision-log per the spec in `strategy/00_philosophy.md`: P&L + position table; every market considered (incl. rejections); reasoning trail per active position; mistakes/mis-calibrations; next-week outlook; sources.

---

## Week 0 — kickoff (2026-04-25, Saturday)

> This is an inaugural / kickoff entry rather than a full trading week — the project began this morning, and the first cron check-in is firing the same Saturday afternoon. Subsequent entries will cover trailing 7 days. Detail here intentionally restates the kickoff so future entries can reference it as the baseline.

### 1. Headline P&L

| Metric | Value |
|---|---|
| Bankroll start (2026-04-25) | $70.00 USDC.e |
| Capital deployed (cost basis) | $64.95 |
| Cash buffer | $5.05 USDC.e (+ 53.81 POL gas, $0.04 used so far) |
| Mark-to-market portfolio value | $64.61 |
| **Unrealised P&L** | **-$0.34 (-0.52%)** |
| Realised P&L | $0.00 (no resolutions yet) |
| Bankroll trajectory | $70.00 → $69.66 (-0.49%) |
| Max upside if all NO/YES win | $76.28 (+17.45% on bankroll, +17.45% on cost) |

The -0.52% drag is entirely the 1-cent maker/taker spread snap-back on fills (we lifted the ask on most positions). It mean-reverts as soon as the books refresh; it is **not** a thesis update.

### 2. Position table (end of Week 0)

| # | Sleeve | Market | Side | Entry | Mark | Cost | MTM | Resolves | Yield-to-resolve |
|---|---|---|---|---|---|---|---|---|---|
| L1 | Long | Jesus returns 2027 | NO | 0.962 | 0.962 | $10.00 | $9.99 | 2026-12-31 | +3.95% / 250d |
| L2 | Long | Pahlavi leads Iran 2026 | NO | 0.907 | 0.906 | $10.00 | $9.99 | 2026-12-31 | +10.3% / 250d |
| L3 | Long | US confirms aliens 2027 | NO | 0.800 | 0.795 | $9.00 | $8.94 | 2026-12-31 | +25.0% / 250d |
| L4 | Long | Trump out 2027 | NO | 0.840 | 0.835 | $7.00 | $6.96 | 2026-12-31 | +19.0% / 250d |
| L5 | Long | Iran regime falls 2027 | NO | 0.800 | 0.795 | $7.00 | $6.96 | 2026-12-31 | +25.0% / 250d |
| S1 | Short | US x Iran permanent peace deal by May 31 | NO | 0.670 | 0.665 | $6.99 | $6.94 | 2026-05-31 | +49.3% / 35d |
| S2 | Short | Latvia top 10 Eurovision 2026 | NO | 0.830 | 0.810 | $5.00 | $4.88 | 2026-05-16 | +20.5% / 21d |
| S3 | Short | Atletico Madrid La Liga top 4 | YES | 0.991 | 0.989 | $4.97 | $4.96 | 2026-05-30 | +0.9% / 35d |
| S4 | Short | Amy Acton Ohio Dem primary | YES | 0.987 | 0.987 | $4.99 | $4.99 | 2026-05-05 | +1.3% / 9d |

Long sleeve: 5 positions, $43.00 cost, $42.84 MTM, +$6.74 max upside (+15.7%).
Short sleeve: 4 positions, $21.95 cost, $21.77 MTM, +$4.59 max upside (+20.9%).

### 3. Markets considered this week (full set, including rejections)

Sourced from a 6,980-row Gamma-API dump filtered to (a) non-sports unless otherwise noted, (b) liquidity ≥ $5k, (c) non-AI-model leaderboards. ~80 long-horizon shortlisted, 99 short-horizon shortlisted. Of those, 9 placed, ~13 explicitly rejected with notes. Listing rejections + reasons:

**Long-sleeve rejects:**
- *NATO withdrawal by 2027 (YES at ~12%).* Initially flagged as a tail-fade. Killed because the resolution clause counts "halted-implementation-still-counts-as-withdrawal" partial scenarios; combined with Trump's April 2026 NATO escalation rhetoric, fair value is closer to 11–12% than my modelled 4–5%. No edge.
- *Anthropic > $500B valuation by 2027 (YES at 93.6%).* Conflict-of-interest market (I'm an Anthropic model). Self-imposed pass per philosophy §Restrictions, even though edge would arguably be small (I have no private info on Anthropic financials).
- *NVIDIA 2027 dominance markets.* Same equity-class as above; I have no scouting edge over a careful retail trader; passed.
- *2026 US Midterm composition (R-House at 15%, D-House at 85.5%).* Interesting — directional play deferred to a later session because I want to read CNN/538 redistricting analysis before sizing. Parking, not killing.
- *Brazil 2026 election (Lula vs. Bolsonaro family at ~38% each).* Same — directional, needs a model. Parking.
- *Religious end-times markets at YES <5%.* Eligible per §Edge taxonomy (NO buys allowed) but Jesus-returns NO already covers the cluster; no diversification benefit from buying a second.

**Short-sleeve rejects:**
- *Hormuz blockade lifted by May 15 (NO).* Strongly correlated with S1; would double the Iran-cluster exposure. Passed to keep the cluster cap.
- *UK top-5 Eurovision (NO).* Dominated by Latvia top-10 NO — same Eurovision-model risk, lower yield. Passed.
- *Atletico Champions League final (YES at very high prices).* No edge; CL outcomes are scouted exhaustively by sports specialists.
- *Iran ceasefire holds through end of April (YES at ~80%).* Redundant with the rest of the Iran cluster on the YES side; sleeve cap blocks.
- *Sports fade markets generally.* Polymarket charges 3% taker fee on sports; that wipes out the carry-trade economics on prices ≥ 0.97. Skipped systematically.
- *Sub-day BTC price ladder markets.* Liquid, efficient, no edge per §Edge sources I will explicitly ignore.

The 9 placed positions represent the highest-edge survivors after these filters.

### 4. Per-active-position reasoning trail

#### L1: Jesus returns 2027 NO @ 0.962 — hold
- **Thesis.** Bond-like cash management. NO is a near-certainty; the YES bid is essentially "literal-believer floor + UMA dispute-risk premium."
- **Prior:** YES ≤ 0.5%. **Mark:** 3.85%. **Edge:** ~3 cents.
- **Evidence this week.** None. No religious-event catalyst.
- **Move:** none. Held at $10 (slightly above the new sleeve cap of $7; grandfathered per §01_horizon_split).

#### L2: Pahlavi leads Iran 2026 NO @ 0.907 — hold (high conviction)
- **Thesis.** Even conditional on regime fall (~8% over 250d), P(Pahlavi takes power | regime falls) ~15–20%. Joint ~1.4%. Market 9.35% is Schelling-point figurehead pricing.
- **Prior:** YES 1–2%. **Mark:** 9.4%. **Edge:** ~7–8 cents.
- **Evidence this week.** Iran FM in Pakistan for mediator talks (Apr 25). No regime-instability indicator. Pahlavi himself remains in DC area; no on-the-ground apparatus reported.
- **Move:** none.

#### L3: US confirms aliens 2027 NO @ 0.80 — hold
- **Thesis.** Resolution requires Cabinet/agency-level statement. AARO has been consistently hedged; no path to a Pentagon/NASA disclosure on a 250-day horizon absent a Trump tweet (~2–3%).
- **Prior:** YES 5–9%. **Mark:** 20.5%. **Edge:** ~12 cents.
- **Evidence this week.** No AARO release; no UAP press conferences scheduled.
- **Move:** none.

#### L4: Trump out before 2027 NO @ 0.84 — hold
- **Thesis.** Mortality (79yo, overweight, war stress) + assassination tail + ~0% impeachment/25A path. Modelled ~7–8% YES.
- **Prior:** YES 7–8%. **Mark:** 16.5%. **Edge:** ~9 cents.
- **Evidence this week.** Walter Reed hospitalisation rumours from Apr 4 denied by White House. Dem 25th-Amendment chatter is rhetorical; the structural path is closed (R-Senate, R-Cabinet). No clinical event reported.
- **Move:** none.

#### L5: Iranian regime falls before 2027 NO @ 0.80 — hold (be ready for vol)
- **Thesis.** Khamenei mortality (~10–13% over 250d) × P(regime falls | Khamenei dies) (~10–20%) ≈ 1.5%; civil war 3–5%; coup 1–2%; US invasion <1%. Sum ~7–10%.
- **Prior:** YES 7–10%. **Mark:** 20.5%. **Edge:** ~10–13 cents.
- **Caveat (carried forward from Day 1 review):** if Khamenei passes, this mark spikes to 0.30–0.40 even if regime ultimately survives. I will *not* panic on intra-window volatility.
- **Evidence this week.** No Khamenei health news; ceasefire holding.
- **Move:** none.

#### S1: US x Iran permanent peace deal by May 31 NO @ 0.67 — hold (highest conviction in book)
- **Thesis.** Resolution requires *permanent* cessation; temporary ceasefires explicitly disqualified. Path to YES needs a signed-and-labelled treaty; no negotiating channel beyond working-level Pakistani mediation; Iranian internal consensus absent; US blockade still up.
- **Prior:** YES 8–12%. **Mark:** 33%. **Edge:** ~21–25 cents.
- **Evidence this week.** Apr 19: Iran rebuffed Trump's plan for a new round of talks. Apr 21: Trump extended the truce 3–5 days for an Iranian counter-proposal — that window expires today/tomorrow. Apr 25: Iran FM in Pakistan; MFA spokesperson explicitly said no US-Iran meeting scheduled. **Net: thesis confirmed; if anything fair value drifted lower (more bullish for NO).**
- **Move:** none. Already at sleeve cap; resist temptation to add until cash rebuilds.

#### S2: Latvia top 10 Eurovision 2026 NO @ 0.83 — hold (lower conviction than fades)
- **Thesis.** Latvia post-2010 modern-era top-10 base rate ~5%. Market 19.5% probably encodes some 2026-specific entry-quality signal I don't have.
- **Prior:** YES 10–15% (risk-managed up from base rate). **Mark:** 19.0%. **Edge:** ~4–9 cents.
- **Evidence this week.** Rehearsal-week press hasn't started (May 5–14). Will scan May 5+.
- **Move:** none. May close early if rehearsal reviews are strong.

#### S3: Atletico Madrid La Liga top 4 YES @ 0.991 — hold
- **Thesis.** Atletico in top 4 with 5 matches left; ~99% lock per current standings.
- **Prior:** YES 99%. **Mark:** 98.9%. **Edge:** ~0.
- **Evidence this week.** No surprises; no injuries/match-fixing scandals reported.
- **Move:** none. Cash-equivalent carry.

#### S4: Amy Acton Ohio Dem primary YES @ 0.987 — hold
- **Thesis.** No credible challenger; market priced as a coronation.
- **Prior:** YES 99%. **Mark:** 98.7%. **Edge:** ~0.
- **Evidence this week.** No new entrants; no scandal.
- **Move:** none. Resolves May 5 — first realisation event in the book.

### 5. Mistakes / mis-calibrations identified this week

1. **Took taker prices on most fills.** All 5 long-sleeve fills lifted the ask. Cost: ~$0.05 of slippage across the book. Rule for Week 1+: place maker bids 1¢ inside best ask; only cross to taker if the book moves through me within an hour.
2. **Cash buffer breach.** Target ≥ 10% ($7); actual $5.05 (7.2%). Acceptable for week 0 (deliberately deployed at maximum to test sizing), will rebuild on Acton (S4) resolution May 5.
3. **No directional bets yet.** Portfolio is entirely fade/carry. This is a deliberate week-0 stance, but if I never put on a directional view I forfeit the largest single category of edge. Action for Week 1: produce a model for either US Midterms or Brazil 2026 election; size only if model materially disagrees with market.
4. **Latvia entry sizing rationale was thin.** Should have gathered 2026 song/artist-quality signal *before* placing, not after. Adopted as a rule: for short-sleeve catalyst plays, do catalyst-specific research before sizing.

### 6. Next week (2026-04-26 → 2026-05-02) — outlook and watch list

**Catalyst calendar:**
- Apr 25–28 (rolling): Trump's truce-extension window expires. If hostilities resume, S1 prints harder; long-sleeve Iran cluster moves *away* from YES.
- Apr 26–May 2: Iran FM continues mediator shuttle in Pakistan. Watch for any joint US-Iran statement (would move S1 sharply against me).
- ~May 1: La Liga matchweek 35 — confirm Atletico still in top 4 (S3).
- Start of May: Eurovision rehearsal-week previews begin to drop (S2 catalyst).

**Positions I expect to potentially roll/close:**
- S4 (Acton) resolves May 5 — first realisation. Will free $5 of cash and (assuming win) +$0.07 P&L.
- No long-sleeve closures expected.

**Research targets for the week:**
- 2026 US Midterm models (House majority, Senate seats). Goal: form a directional view to deploy reserve cash if/when the Acton win lands.
- Brazil 2026 first-round model (Lula coalition strength, Bolsonaro-family coordination). Lower priority; deeper into the year.
- Sweep new short-sleeve markets every 2–3 days. Specifically watch for Iran-related markets that surface around the truce-window expiration.

**Operational targets:**
- Confirm cron is firing daily (today is the inaugural tick; verify the Sun/Mon ticks land).
- Once S4 resolves: rebuild cash buffer to ≥$10 (~$5.07 after Acton + ~$5 of headroom from any natural mark drift on long sleeve).

### 7. Sources

- [2026 Iran war ceasefire — Wikipedia](https://en.wikipedia.org/wiki/2026_Iran_war_ceasefire)
- [2026 United States naval blockade of Iran — Wikipedia](https://en.wikipedia.org/wiki/2026_United_States_naval_blockade_of_Iran)
- [Iran rebuffs Trump's plan for new round of peace talks (CNBC, Apr 19)](https://www.cnbc.com/2026/04/19/iran-says-talks-continue-while-it-retains-control-of-strait-of-hormuz-.html)
- [Trump refuses to lift Hormuz blockade until Iran deal agreed (Euronews, Apr 20)](https://www.euronews.com/2026/04/20/trump-says-he-will-not-lift-blockade-on-iranian-ports-until-peace-deal-struck-with-tehran)
- [Day 56 of Middle East conflict — US-Iran peace talks uncertainty (CNN, Apr 24)](https://www.cnn.com/2026/04/24/world/live-news/iran-war-trump-israel-lebanon)
- [White House addresses Trump Walter Reed health-crisis claims (Daily Beast)](https://www.thedailybeast.com/white-house-forced-to-address-claims-of-donald-trump-health-crisis-at-walter-reed-medical-center/)
- [I'm an expert on presidential health — 25th Amendment is not an option (STAT News, Apr 21)](https://www.statnews.com/2026/04/21/25th-amendment-trump-physician-medical-decline/)
- Polymarket Gamma-API survey (raw snapshots gitignored at `data/snapshots/2026-04-25_*.json`).
- Internal: `research/_long_initial.md`, `research/_short_initial.md`.

---

## Week 1 — 2026-04-25 → 2026-05-02

### Headline

| Metric | Value |
|---|---|
| Polymarket sleeve cost | $64.95 |
| Polymarket sleeve MTM | $66.49 |
| Polymarket P&L | +$1.54 (+2.37%) unrealized, $0 realized |
| Crypto sleeve idle | ~$1.50 (USDC + ETH gas) |
| Crypto sleeve in Aave | $84.50 ($55 Arb @ 4.15% + $29.50 Base @ 3.375%) |
| Ostium sleeve collateral | $14.68 (3 positions × $4.89) |
| Ostium sleeve MTM | $14.81 (+$0.13, +0.9%) |
| **Total project MTM** | **$167.28** on $164.13 deployed = +$3.15 (+1.92%) |
| Bankroll trajectory | $170 deployed Apr 25 → $167.28 (mostly unrealized P&L; some Ostium fees + a tx fee) |

### Position-level table

| Position | Side | Entry | Mark | Cost | MTM | %P&L | Resolves |
|---|---|---:|---:|---:|---:|---:|---|
| Iran-peace deal by May 31 | NO | 0.670 | 0.775 | $7.00 | $8.09 | +15.67% | May 31 |
| Aliens confirmed by 2027 | NO | 0.800 | 0.825 | $9.00 | $9.28 | +3.12% | Dec 31 |
| Trump out before 2027 | NO | 0.840 | 0.865 | $7.00 | $7.21 | +2.98% | Dec 31 |
| Amy Acton OH Gov primary | YES | 0.987 | 0.994 | $4.99 | $5.03 | +0.66% | **May 5** |
| Atletico top-4 La Liga | YES | 0.991 | 0.989 | $4.97 | $4.96 | -0.25% | ~May 25 |
| Jesus returns by 2027 | NO | 0.962 | 0.965 | $10.00 | $10.02 | +0.26% | Dec 31 |
| Pahlavi leads Iran 2026 | NO | 0.907 | 0.905 | $10.00 | $9.98 | -0.17% | Dec 31 |
| Iranian regime falls 2027 | NO | 0.800 | 0.795 | $7.00 | $6.96 | -0.62% | Dec 31 |
| Latvia Eurovision top-10 | NO | 0.830 | 0.825 | $5.00 | $4.97 | -0.60% | May 16 |
| Ostium XAU/USD long 5x | LONG | $4544 | ~$4571 | $4.89 | ~$5.07 | +3.6% | TP/SL or 30d |
| Ostium SPX/USD long 5x | LONG | $7167 | ~$7226 | $4.89 | ~$5.10 | +4.3% | TP/SL or 30d |
| Ostium NDX/USD short 5x | SHORT | $27369 | ~$27447 | $4.89 | ~$4.84 | -1.0% | TP/SL or 30d |

### Markets considered this week (rejected)

The hurdle filter (added 2026-04-30) provides a clean record of considered-then-skipped:
- **Russia-Ukraine ceasefire May 31 NO** — 162% APY at 02:08 cron (price 0.917). Skipped via skeptic surfacing May 9 Victory Day catalyst risk + thematic correlation with Iran-peace NO. **Skip retrospectively right** — price moved away from us toward fair value (0.917 → 0.939 → 0.929). DEC-0014 records the skip for calibration. Re-evaluated 14:00 + 02:00 ticks: still passes hurdle but catalyst now 7d away.
- **Hormuz traffic returns by May 15 / end of May / end of June** NO — 342–4379% APYs but all push Iran cluster past 30% cap. Skipped.
- **Iranian regime falls May 31 / June 30** NO — redundant with existing Iranian-regime-2027 NO. Skipped.
- **China invade Taiwan 2026 NO** — 11.4% APY, 244d. Marginal. Pass on lock-up.
- **Powell out as Fed Chair by May 14 NO** — 121% APY, 12d, clean mechanical. Bankroll constraint blocks. Re-evaluate post-Amy-Acton.
- **Fed-rate-change ±50bps NO** at 0.99x — fail hurdle once annualized.
- **Various Amazon-mcap, Shelton-confirmed NOs** — fail hurdle.

### Reasoning trail per active position

**Iran cluster ($31 cost, 48% of PM sleeve)** — 4 positions: Pahlavi NO, Iranian regime falls 2027 NO, Iran-peace by May 31 NO, plus loosely-correlated Aliens NO and Trump-out NO. Cluster sits AT 30% cap if you include just the 3 hard-correlated (Pahlavi/regime/peace) totaling 47% (interpretation: cluster cap should be on POSITIONS, not on % of sleeve, and these are 3 positions clustered = at cap). Tight discipline: no add. Iran-peace NO is the standout (+15.67%) because the original entry at 0.67 was a real pricing inefficiency (market was pricing 33% YES on a 5-week PERMANENT peace deal during active blockade — implausible). Mark drifted with Hormuz news cycle: peaked +23% on Trump's "blockade could last months" rhetoric, then -8pp on a Putin-Trump call adjacent rhetoric, then back. Hold to resolution.

**Bond-like long sleeve ($30, 46%)** — Jesus returns NO, Aliens NO, Trump-out NO, Pahlavi NO, Iranian regime NO. Pure carry. Average 0.5% drift, all within ±3.5%. No catalysts moved the theses materially this week.

**Short sleeve ($15, 23%)** — Iran-peace NO ($7), Atletico-top4 YES ($5), Amy-Acton YES ($5). Atletico waiting on La Liga results; clinched mathematically pending. Amy-Acton **resolves Tuesday May 5** — first calibration data point of the project.

**Ostium sleeve ($14.68 collateral)** — Volume rotation for Stork-points farming, NOT directional alpha. Pair-trade structure (long SPX + short NDX) keeps me ~delta-neutral on US-equity-vs-tech. XAU long is the directional bet (gold supports war/instability). Funding scanner finding (2026-05-01): SPX long + NDX short are funding-collection-side; XAU long is funding-paying-side (small, monitoring).

### Mistakes / mis-calibrations identified

1. **Polymarket consistency scanner — phantom-arb trap caught on first run.** Initial scanner output showed 113 candidates with +25–47% net edge based on gamma-api midpoints. Live CLOB validation killed every single one (NO asks all sat at $0.99, displayed midpoints were calculated between $0.01 stub bids and real asks). Mistake was trusting the displayed price without live-orderbook validation. Lesson saved as feedback memory; scanner now validates every candidate before flagging. Saved real-money mistake on a strategy class that doesn't exist at our scale.
2. **Skeptic-monoculture bias.** Used skeptic agent alone for 4 days before operator flagged the structural problem (every action gets pressure to add caveats / hold off; over time tilts toward inaction). Now paired with champion. Methodology study showed convergence priming itself biases outcomes; pure role-only adversarial debate + external moderator fact-grounding is the refined pattern.
3. **Hurdle rate not formalized at kickoff.** Day 1 portfolio includes some positions (Pahlavi NO -0.17%, Eurovision -0.60%, Atletico -0.25%) that may be fair-priced or marginal, where putting the capital in Aave at 4.15% APY would have been better risk-adjusted. The hurdle was formalized 2026-04-30. Going forward every new entry gets the APY check.
4. **Iran-peace entry slightly early.** Mark dropped from peak +23% to +15% on Hormuz news cycle. Hold-to-resolution thesis intact but better entry would have been after a Trump rhetoric escalation, not before. This is the kind of mis-calibration that only shows on resolution; flagged for post-mortem.

No mistakes large enough to change positioning. Calibration data thin (0/14 resolved); first real signal arrives May 5.

### Decisions tracker summary

```
total=14  resolved=0  pending=14
by type:    open_position=12  scaffolding=1  skip=1
by confidence: high=9  medium=5  low=0
pending capital: $135.00
```

First resolutions land Tue May 5 (Amy Acton). Calibration product begins next week.

### Outlook for next week (May 2 → May 9)

**Hard catalysts:**
- **Tue May 5**: Amy Acton resolves YES (high confidence). Frees $5 of capital. First DEC-update.
- **Fri May 9**: Putin Victory Day. Either ceasefire framework announcement OR no-show. Russia-Ukraine ceasefire NO market reprices.

**Soft catalysts:**
- Hormuz crisis remains live. Any Iran-peace breakthrough or escalation moves Iran-peace NO meaningfully.
- Powell-out-by-May-14 market: I expect price to drift toward 0.99 as we approach his May 15 term end without a Trump firing announcement.

**Positions I expect to roll/close:**
- Amy Acton YES: resolves May 5, redeploys.
- Possibly Powell-Fed-Chair NO entry on May 5-6 if price still ≥ 0.97 (~$5 size).
- Hold everything else.

### Sources used this week

- Polymarket gamma-api + CLOB orderbook (live)
- Bloomberg / Reuters / WaPo / Kyiv Independent / Modern Diplomacy / Al Jazeera / BBC / NPR / Guardian (RSS via news_watcher; full URLs in `notes/news_alerts.jsonl`)
- Limitless API (cross-venue arb scan, no live-trade signal this week)
- Ostium subgraph (funding-rate scan)
- Aave V3 pool data (rates, balances)


## Week 3 + 4 (May 9 → May 18) — catch-up consolidated entry

**Cadence note:** weekly cadence slipped during the R-U miss + recoup-campaign sprint. This entry consolidates ~10 days of activity (May 9–18). Next full weekly: 2026-05-24 (Sunday).

### Bankroll snapshot

- **2026-05-09 reference:** ~$170 (per project memory; PM ~$66 cost, Aave ~$30, Ostium ~$15 collat, crypto ~$60 cash)
- **2026-05-18 02:00 UTC actual:** ~$148 MTM (PM cost $78.72 / MTM $84.46, Aave ~$10, Ostium ~$5 collat, crypto+poly cash ~$48)
- **Net delta:** −$22 = R-U realized loss (−$16.73) + bridge/swap friction (~$1) + MTM swings (~−$4) offset by realized wins (+$7.83) and unrealized gains in held book (+$5.75 currently)

### Realized P&L (May 9 → May 18)

| Date | DEC | Position | Realized |
|---|---|---|---:|
| 2026-05-10 | 0023 | Atletico top-4 YES early close | −$0.07 |
| 2026-05-11 | 0018 | **R-U Iran-Russia tunnel YES (UMA dispute → YES)** | **−$16.73** |
| 2026-05-12 | 0019 | May-11 Iran-peace NO redeemed | +$0.525 |
| 2026-05-12 | 0025 | Ostium gold (XAU) LONG 5x TP-triggered | +$1.17 |
| 2026-05-13 | 0007 | Latvia Eurovision NO partial close | +$0.706 |
| 2026-05-15 | 0015+0020 | May-15 Iran-peace NO redeemed (incl. scale-in) | +$3.54 |
| 2026-05-18 | 0026 | ~~Ostium NDX SHORT 5x TP-triggered | +$1.96 (est)~~ **[CORRECTED 2026-06-10: was a STOP-LOSS on 2026-05-14, realized −$1.95 — subgraph-verified; see Weeks 5–7 corrections block]** |
| | | **NET REALIZED** | **−$8.90** ~~~~ **[CORRECTED 2026-06-10: −$12.81 with the NDX sign error fixed]** |

### Held book MTM (2026-05-18 02:00 UTC)

| Position | Side | Entry | Mark | Cost | MTM | %P&L | Resolves |
|---|---|---:|---:|---:|---:|---:|---|
| Iran regime falls 2027 | NO | 0.837 | 0.825 | $28.25 | $27.84 | −1.44% | Dec 31 |
| US-Iran peace deal May 31 | NO | 0.678 | 0.925 | $11.82 | $16.13 | **+36.43%** | **May 31** |
| Trump out before 2027 | NO | 0.856 | 0.905 | $10.56 | $11.16 | +5.70% | Dec 31 |
| Reza Pahlavi leads Iran 2026 | NO | 0.907 | 0.925 | $10.00 | $10.20 | +2.04% | Dec 31 |
| Hantavirus pandemic 2026 | NO | 0.909 | 0.928 | $9.09 | $9.29 | +2.15% | Dec 31 |
| Aliens confirmed by 2027 | NO | 0.800 | 0.875 | $9.00 | $9.84 | +9.37% | Dec 31 |
| Ostium SPX LONG 5x | LONG | 7167 | ~7167 | $4.89 | ~$4.89 | ~flat | TP/SL or 30d |
| **TOTAL PM book** | | | | $78.72 | $84.46 | **+7.30%** | |

### Strategy pivot (mid-window)

2026-05-11 R-U miss triggered a strategy reset (post-mortem in journal):
- **Mechanical-resolution markets only** — skip subjective "permanent peace deal / qualifies-as-X" markets that depend on UMA interpretation
- **10pp+ edge bar at entry** (was 5pp)
- **`polyclaude_enter.py` mandatory** for every new entry — enforces umaResolutionStatus check + catalyst_check resolution-criteria injection + Kelly+ρ sizing
- **Max 5 concurrent positions** (currently at 6 inherited)
- **Target allocation: 60% Aave reserve (3.4-3.8% APY hurdle) / 40% PM selective**

### Infrastructure shipped (recoup campaign)

| Tool | Purpose | Why ship |
|---|---|---|
| `scripts/uma_status_check.py` | Polls gamma-api umaResolutionStatus + outcomePrice for held positions; alerts on transitions + >5pp moves | Would have caught R-U dispute 18h earlier |
| `scripts/polyclaude_enter.py` | Unified gamma-lookup + UMA-reject + catalyst_check + Kelly + execute | Single-entry-point enforces post-R-U filters |
| `scripts/portfolio_kelly.py --constrained` | Per-position Kelly+ρ + budget-bound constrained portfolio | Replaces naive cluster-cap (double-counted risk on anti-correlated Iran tails) |
| `scripts/brownian_bridge_fv.py` | Hazard-rate fair-value pricing: `fair(t) = p^(1-t/T)` | Per-position SCALE_UP/TRIM/HOLD verdicts using time-decay math |
| `scripts/sports_pm_scan.py --with-consensus` | Sports mid-market scan w/ bookie-consensus delta | Validated on Latvia (close +$0.706 after consensus disagreement) |
| `scripts/macro_pm_scan.py` | Macro markets ≤60d (Fed/CPI/etc.) | DEGRADED: --no-consensus default (CME FedWatch JS-render hallucinates) |
| `scripts/event_monotonicity_scan.py` | Multi-market event monotonicity arb scanner | 225 events / 0 violations in first week; collecting prospective data |
| `scripts/world_state_digest.py` + `scripts/longterm_check.py` | Sunday domain digests + per-ticker generational-mispricing framework | Watchlist surfacing — 12 candidates seeded, all route=ibkr_surface per <1y horizon |
| `scripts/watchlist_monitor.py` + `notes/watchlist_triggers.json` v2 (`route` field) | Entry-trigger price alerts | Fired 3x on CEG/LEU/CCJ; all needed manual fresh longterm_check + tighter revised triggers |
| `scripts/ostium_state_diff.py` | Ostium open-trades count change detector | Catches TP/SL/manual closes — caught XAU and NDX TPs |
| `news_watcher` tier-2 CRITICAL re-validation | Article-body fetch + second-pass agent eval | Fix for 2026-05-09 false directional miscalls |

11+ tools shipped over 10 days. All wired into daily_checkin.sh + cron + Telegram.

### Markets considered, rejected

- **R-U Iran-Russia tunnel YES re-entry post-resolution**: skipped, market closed
- **Various Hormuz / Iran-cluster NOs** (May-15, May-31, June-30 peace-deal variants): added 2 (DEC-0015, DEC-0024); skipped multiple regime-fall + uranium-transfer markets due to cluster cap
- **Russia-Ukraine ceasefire NO (post-Victory Day)**: not re-entered after May 9 — Victory Day passed without framework announcement, NO mark moved away from us
- **Sports candidates** (Atletico, La Liga + UCL): closed Atletico early, skipped all others (cluster fees + off-season)
- **TLT, NVDA, CCJ, LEU, CEG** (long-term watchlist triggers fired): all returned to WATCH/PASS via fresh longterm_check; route=ibkr_surface = surfaced to operator IBKR

### Mistakes / mis-calibrations identified

1. **R-U miss (−$16.73)** — three documented mistakes per DEC-0018 post-mortem:
   - Scale-in error on news (read mark crash as overreaction, not new info)
   - Investigation gap (didn't fetch gamma-api/markets/{id} for umaResolutionStatus)
   - Resolution-criteria interpretation gap (operated under loose "permanent peace" framing while criteria explicitly said "regardless of whether ceasefire officially starts afterward")
   All three FIXED via infra ship (uma_status_check, polyclaude_enter umaResolutionStatus reject, catalyst_check resolution-criteria injection).

2. **macro_pm_scan CME FedWatch hallucination** — haiku WebFetch on JS-rendered CME page returned nothing → invented +27.4pp delta vs ground-truth +1.5pp. Disabled consensus comparison; v2 plan to parse ZQ futures.

3. **limitless_arb_scan false positives** (Neymar/Messi + Cristiano Ronaldo): fixed via `_proper_nouns()` filter + Jaccard 0.35→0.55.

4. **Watchlist trigger-fire pattern (CEG/LEU/CCJ 3-of-3)**: static price triggers fired on drop, but fundamental fair value also adjusted down → no margin of safety opened. Lesson: always run fresh longterm_check on trigger-fire; revise entry_max per fresh fair-value. All 3 watchlist entries now properly tightened.

5. **Over-cancellation of autoprompter**: was cancel_followup at every idle turn → operator flagged "haven't seen continuation checks." Fixed: stop routine cancel, let 20-min cycle fire naturally + 1-in-4 meta-reflection rotation via hook.

6. **strategy/00_philosophy.md staleness** (caught 2026-05-17 meta-reflection #4): header said bankroll $70 + framed calibration as "actual product" — operator explicitly pivoted to ROI-only on 2026-05-14. Patched with current-state banner + inline operator-pivot note.

### Decisions tracker summary

```
total=26  resolved=10  pending=16
by type: open_position=17 (7 resolved) · size_change=4 (1) · close_position=3 (2) · scaffolding=1 (0) · skip=1 (0)
by confidence: high=21 (10 resolved) · medium=5 (0 resolved)
pending capital: $158.62
lessons recorded: 10
```

Notable lessons (selected): R-U three documented mistakes (above); TP-set-at-entry leaves upside in major shocks (XAU TP'd at +24% during Hormuz blockade); capital reallocation between high-conviction near-resolution positions captures alpha; Brownian-bridge fair-value identifies marginal-edge ranking.

### Outlook for next week (May 18 → May 25)

**Hard catalysts:**
- **May 31 (~13d):** May-31 Iran-peace NO resolves. Currently at mark 0.925, +36.43% on cost, ~$1.31 more expected at lock-in. Dominant near-term P&L event.
- **Trump-Xi-Iran-mediation watch:** daily — early-close trigger at mark < 0.83.
- **Sunday May 24:** next weekly long-term review (rotation to trade-regulation, biotech-health, crypto-on-chain, markets-corporate).

**Soft catalysts:**
- Ostium SPX LONG 5x still open (DEC-0011, trade 1848511). NDX SHORT just TP'd **[CORRECTED 2026-06-10: it had STOP-LOSSED on 05-14, not TP'd]**; pair-trade now naked SPX-long. Could TP at +8% (~7742) or SL at −8% (~6595). Monitor.
- Iran-cluster news flow (Hormuz, regime stability) shapes Pahlavi + regime-fall NO marks.

**Positions to roll/close:**
- None planned. May-31 NO will resolve naturally; everything else holds.

**Capital next:**
- $43.79 cash on PM sleeve + ~$17 expected from May-31 NO resolution = ~$60 to deploy into Aave Base post-May-31 (60/40 strategy rebalance). Bridge in one batch to amortize friction.

### Sources used this week

- Polymarket gamma-api + CLOB orderbook + data-api (live)
- News: Reuters / Bloomberg / WaPo / BBC / NPR / Al Jazeera / Kyiv Independent / Times of Israel / SCMP (RSS via news_watcher; full URLs in `notes/news_alerts.jsonl`)
- World-state digest: 2 Sunday domain rotations (energy-power-infrastructure + geopolitics-security on 2026-05-10; tech-ai-chips + macro-fiscal-labor on 2026-05-17)
- Catalyst checks: haiku-WebSearch via `scripts/catalyst_check.py` (~10-15 invocations this window)
- Bookie consensus: haiku-WebFetch via `sports_pm_scan --with-consensus` (Latvia Eurovision was the validating signal)
- UMA Optimistic Oracle status (gamma-api + on-chain): via `scripts/uma_status_check.py`
- Aave V3 pool data (Base + Arbitrum supply APYs)
- Ostium subgraph + OpenSDK


---

## Weeks 5–7 (May 18 → Jun 10) — catch-up consolidated entry

*Process note: the step-9 weekly cadence slipped 23 days (last report 2026-05-18). This entry consolidates three weeks; the slip itself is logged under Mistakes.*

### Bankroll snapshot

- **2026-05-29 corrected reference:** $162.24 (PM $83.84 + Aave $71.10 + idle $2.55 + POL $4.74)
- **2026-06-10 02:00 UTC actual: ~$172** = PM book MTM $110.98 (cost $107.77) + Aave $52.68 ($30.55 Polygon/PM-sleeve + $17.59 Arb + $4.54 Base) + pUSD $1.81 + USDC dust ~$1.6 + ~51 POL @ ~$0.089 ≈ $4.5 + ETH dust ~$1.3
- **vs $170 kickoff: ~+1%. The 2026-05-11 R-U loss (−$16.73) is fully recouped.**

### Realized P&L (window)

| Event | Date | Realized |
|---|---|---|
| May-31 Iran-peace NO redeemed (tx 0xef8766ab) | Jun 1 | **+$5.62** on $11.82 cost (+47.5%) |
| Ostium SPX long manual-closed @ $7,511.14 (final leg; perp sleeve flat since) | May 28 10:42Z | **+$1.07** net of rollover (subgraph-verified) |
| Ostium NDX short — restatement of the May-18 week's books | May 14 00:30Z | **−$1.95** (was wrongly booked +$1.96 "TP"; it STOP-LOSSED) |

May-31 NO was the window's defining trade: entered as a pricing inefficiency, survived a −47pp adverse swing (0.815 → 0.345 on Trump's "largely negotiated" headline) on explicit Brownian-bridge conditional-fair-value HOLD logic, and resolved $1.00. Hold-through-catastrophe validated the framework end to end.

**Corrections to prior entries (2026-06-10 backfill pass, all 8 overdue decision records resolved against primary sources — subgraph/gamma/on-chain):**
- **DEC-0026 sign error:** the NDX short close booked 2026-05-18 as "TP +$1.96" was actually a **STOP-LOSS on 2026-05-14 at $29,564 (+8.02% adverse), realized −$1.95** (payout $2.945284, subgraph-verified directly). The Week 3+4 NET REALIZED restates −$8.90 → **−$12.81**.
- **SPX close:** manual Market close 2026-05-28 10:42Z (not "TP-closed ~May 27"); net of rollover +$1.07 (not +$1.17). Pair total (SPX+NDX): **−$0.88** — the dispersion view inverted.
- **Cumulative realized restated:** the 2026-06-01 journal's "May-31 win flips cumulative to roughly break-even" was wrong on the old books; corrected cumulative realized since kickoff ≈ **−$0.4** post-May-31 (R-U −$16.73 the dominant loss, May-31 +$5.62 the dominant win). Total bankroll is unaffected (it reads live balances — $171.87, +1.1% vs kickoff); this is attribution, not balance.
- Calibration ledger now current: 19/31 decisions resolved, 0 overdue. The error mechanism (booking a perp close from a trade-count diff + assumed direction) is captured as the DEC-0026 lesson; `ostium_state_diff.py` already closes the detection gap and the new rule is: no perp P&L gets written without the subgraph order record.

### Held book (2026-06-10 02:30 UTC, post scale-ups)

| Position | Side | Entry | Mark | Cost | MTM | %P&L | Resolves |
|---|---|---|---|---|---|---|---|
| Iranian regime fall before 2027 | NO | 0.837 | 0.875 | $28.25 | $29.53 | +4.5 | 2026-12-31 |
| Trump out as president before 2027 | NO | 0.881 | 0.895 | $24.96 | $25.36 | +1.6 | 2026-12-31 |
| US acquires part of Greenland 2026 | NO | 0.870 | 0.865 | $19.14 | $19.03 | −0.6 | 2026-12-31 |
| US confirms aliens before 2027 | NO | 0.807 | 0.865 | $10.70 | $11.46 | +7.1 | 2026-12-31 |
| Reza Pahlavi leads Iran 2026 | NO | 0.907 | 0.946 | $10.00 | $10.42 | +4.2 | 2026-12-31 |
| Hantavirus pandemic 2026 | NO | 0.909 | 0.946 | $9.09 | $9.46 | +4.0 | 2026-12-31 |
| Satoshi identity revealed by Dec 31 | NO | 0.940 | 0.955 | $5.64 | $5.73 | +1.6 | 2026-12-31 |
| **Total** | | | | **$107.77** | **$110.98** | **+3.0** | max payout $124.35 |

### Actions this window

- **Jun 1:** redeemed May-31 NO; $16.50 of proceeds → Aave Polygon (no-deferral idle rule).
- **Jun 5:** fade-basket deployment: aliens NO $10.70 @ 0.807 + Greenland NO $12.18 @ 0.870 (favorite-fade class, validated 2026-06-02, backtest N=1513).
- **Jun 10:** scale-up batch (DEC-0032/33): Trump-out NO +$14.40 @ 0.90 (skeptic+champion gated; size cap-bound by the 15%-per-ticket rule, NOT Kelly's +$25.63) + Greenland NO +$6.96 @ 0.87 (fresh catalyst gate, +5.5pp robust). Funded by one $23 Aave-Polygon withdraw + pUSD wrap.
- **Jun 10:** evaluated and REJECTED US-Iran-peace-by-Jun-15 NO fade: favorite_fade scanner said +3.4pp; catalyst gate said −8pp at central (P(YES) 12% vs market 4.5%). The mandatory gate killed a scanner artifact — working as designed.

### Mistakes / mis-calibrations identified

1. **Idle-capital blindness ($22 vs $75.68).** Journal repeated "~$22 idle in Aave" for 5 days; true idle was $75.68. Root cause: `wallet_status.py`/`crypto_status.py` never queried aTokens or pUSD, so every delegated tick was blind to the largest idle sleeve and "capital-bound" skips were decided on a wrong number. Fixed 2026-06-10 at source (both scripts now print aUSDC/pUSD lines; verified live). Lesson: status tooling must enumerate every asset *home*, not just hot-wallet balances.
2. **Haiku catalyst death-tail error.** The Trump-out check priced P(death/incapacity) at 0.3% for a man turning 80 within the week (SSA-table, halved for presidential medicine: 1.5–2.2%). Caught by the skeptic in the >$10 skeptic+champion pass, which cut the add from $25 to $14.40. Lesson: actuarial inputs from cheap-model checks need a life-table sanity pass before they feed sizing.
3. **Weekly cadence slip** — this report is 23 days late; operator's primary P&L visibility was journal-only for 3 weeks.
4. **Doc drift, flagged not fixed:** `strategy/00_philosophy.md` says max-5 concurrent positions; the book has run 6–7 since the Jun-5 entries (today's adds change ticket sizes, not position count). Either the rule or the book is wrong — operator call; not silently rewriting the doc.

### Decisions tracker summary

31 decisions / 11 resolved / 12 lessons recorded. New this window: DEC-0028 (Satoshi NO) through DEC-0033 (today's two scale-ups). 8 outcome backfills overdue (incl. DEC-0011 Ostium SPX) — queued for a focused session against authoritative data only.

### Outlook (Jun 10 → Jun 17)

- **Jun 15/16:** Iran peace-deal / Kharg / airspace markets resolve (none held, but Iran-cluster marks will move); **ARB DAO revenue-share vote Jun 16** (persistent watchlist hit, route=ibkr).
- **Jun 24:** Trump ceasefire-extension expiry → standing Iran-leg reassessment trigger (>5pp mark move or UMA change).
- **Jun 30:** regime-fall-by-Jun-30 + nuclear-deal markets resolve; methodology N=20 prospective experiment concludes → final per-variant analysis owed, then the deferred methodology_stress_test pagination fix.
- Dry powder: $52.68 Aave + $1.81 pUSD. Bar unchanged: robust-edge at the pessimistic bound; no forcing.
- Operator-gated threads: ALB starter tranche (msg 434), EIGEN unlock washout (427), ETH-long question (426), git-history filter-repo decision.

### Sources used this week

- Polymarket gamma-api + CLOB orderbook + data-api (live walks on every flagged arb/fade)
- News: RSS via news_watcher (full URLs in `notes/news_alerts.jsonl`); catalyst checks via haiku+WebSearch (`scripts/catalyst_check.py`)
- UMA Optimistic Oracle status via `scripts/uma_status_check.py`
- Aave V3 aToken balances (Polygon/Arbitrum/Base, direct on-chain reads — now wired into status scripts)
- Brownian-bridge + constrained-Kelly internal frameworks (`brownian_bridge_fv.py`, `portfolio_kelly.py`)

---

## Week of 2026-06-10 → 2026-06-24 (14d; cadence slipped across two outages + a marathon session)

**Bankroll:** $163.13 (`bankroll.py`) vs $172.19 Jun-10 close = **−$9.06 (−5.3%)**; vs $170 kickoff −4.0%. PM MTM $96.62; Aave $48.22 (Poly $26.08 + Arb $17.60 + Base $4.54); pUSD $11.70; natives/dust ~$6.6.

**Realized this fortnight: −$10.05.**
- **DEC-0038 peace-deal-Jun-15 NO: −$11.31.** Entered Jun-12 @0.863 after the YES 0.035→0.145 deal-pivot repricing; RESOLVED YES Jun-17 when the US-Iran MoU was *signed* ("permanent termination of military operations" + Hormuz reopening). The **permanence-near-date trap**, 2nd instance after R-U; now codified in doctrine §4.4 + a `polyclaude_enter.py` tool-warning.
- DEC-0037 aliens-2027 NO closed **+$1.09** (mark drifted above bridge-fair pre the Aug/Oct UAP catalysts; locked the gain).
- DEC-0036 regime-fall trim **+$0.17** (honest near-term-direction miss — trimmed on the Jun-11 escalation spike; mark then *rose* on de-escalation; ~$0.45 opportunity-cost was the overcaution tax, but capping correlated-cluster exposure during a live war was sound ex-ante).

**Unrealized:** 6 NO bond-like fades, cost $92.28 / MTM $96.62 = **+$4.34** open, all resolving Dec-31 2026 (~190d): regime-fall/Trump-out/Greenland 0.905, Pahlavi 0.958, hantavirus 0.960, Satoshi 0.968. All guards clean every tick (UMA / marginal-APY / redeemable / monotonicity / consistency).

**Decisions tracker (`decisions.py summary`):** 38 total / 21 resolved / 19 lessons. Fixed a `decisions.py list`/`pending` KeyError:'confidence' crash (60aca63, Jun-23) — the primary review path had been dying mid-list on auto-logged records (DEC-0029+); verified the 9-record outcome-backfill complete.

**Dominant-loss pattern (reinforced):** every realized loss to date is the **permanence-near-date trap** — R-U −$16.73 + DEC-0038 −$11.31 = **−$28.04**, both NO-fades on (permanence-qualifier × near-date × active-dealmaking) that flipped YES via an announcement/signing, *not* a strict-criteria failure. Crucially, the May peace-deal NOs that WON (+$9.69 combined: DEC-0006/0024 +$5.62, -0007 +$3.54, -0016 +$0.525) were the *same structural fade* but with NO high-probability signing event inside their window. The trap is specifically the dealmaking-momentum overlap; §4.4 now gates it (weight loose ≥0.5 or skip).

**Outlook (Jun-24 → ~Jul-01):**
- **Jun-30:** regime-fall-by-Jun30 + nuclear-deal + Hormuz-normal-by-Jun30 markets resolve (none held); methodology N=20 prospective experiment concludes → owed final per-variant analysis, then the deferred `methodology_stress_test` pagination fix.
- **~Aug-16:** US-Iran MOU 60-day window expires → new Iran hard-reassessment checkpoint. **Jul-27:** EU sanctions review.
- ARB delegated entry armed at ≤$0.075 (currently $0.079); HYPE funding-harvest + trend-following parked (deploy at ~$500 scale / Dec-31 capital-free).
- Dry powder: ~$11.70 pUSD + $48.22 Aave. Bar unchanged: robust-edge at the pessimistic bound, no forcing.

### Sources used this week
- Polymarket gamma-api + CLOB orderbook + data-api (live walks on every flagged arb/fade); discover/favorite-fade/consistency/monotonicity scanners
- News: `news_watcher` RSS (`notes/news_alerts.jsonl`); WebSearch for the Jun-24 Iran ceasefire-extension status (Jun-17 MOU = 60d extension confirmed)
- UMA Optimistic Oracle via `uma_status_check.py`; Aave aToken on-chain reads; `bankroll.py` authoritative total

---

## Week of 2026-06-24 → 2026-07-02 (8d; due Jul-01, 1d late — outage #4 ate Jun-29→Jul-02)

**Bankroll:** $164.95 vs $162.38 Jun-24 = **+$2.57 (+1.6%)**; vs $170 reference **−3.0%** over the full ~9 weeks (capital ledger correction from the audit: both deposits were week-one, so the honest counterfactual is Aave-flat ≈ +0.8% → true underperformance ≈ **−3.8pp**). Benchmark currently LOST; Dec-31 is the accountability date.

**Realized this week: +$0.65** — closed hantavirus NO @ 0.974 (DEC-0042, +7.2% on $9.09 cost), triggered by the audit's guard fix (leg was NEGATIVE_EDGE at own prior: mark 0.9745 > p_no 0.97, catastrophe-tail class at a discount). ARB starter +5.1% vs entry (unrealized). The rest of the book gained through both a live war escalation AND a 4-day outage: 5 remaining NO legs, cost $83.19, all above entry, marks migrating toward NO (the predicted pull-to-par signature).

**The week's real event — operator-requested approach audit (skeptic+champion, full writeups in journal 2026-07-02):**
- Verdicts: champion SOUND-with-evolution / skeptic NEEDS-CORRECTION; consensus on the fixes.
- Hard bug found + fixed: `check_marginal_apy.py` was win-assumed (no P(loss)) with a stale 3.4% hurdle — the daily "6/6 clear" green light was mathematically vacuous. Now expectation math vs priors; first honest run: only Trump-out + Greenland clear the 5% hurdle.
- Core allocation error (verified): the validated edge (N=1513) is at ≤7d-to-resolution (+2.8-4.8pp, 3-5σ), NEGATIVE at 30d-out; the Dec-31 book is outside backtest coverage and yields ~4.3%/yr at own priors < Aave. **Repointing: stop growing the long-dated book; harvest the validated short-dated bucket with a prospective ledger.**
- Ops: 4th outage (~7.5/21 days dark). Dead-man switch shipped: heartbeat_watch now alerts the operator directly (Telegram, LLM-independent) when the journal goes stale while injects still flow.
- Iran arc closed well: HOLD through the entire escalation validated — regime-fall NO 0.905→0.915 through 2 nights of US strikes + Iran hitting Bahrain/Kuwait; the bias-corrected catalyst_check (fixed Jun-27) worked in its first live test.

### Decisions tracker
42 decisions / 23 resolved / 19+ lessons. New: DEC-0042 (hantavirus close). Methodology experiment 19/20 resolved — zero_shot +0.29/$ (100% win on takes) vs all four multi-agent variants ≤~0; final per-variant analysis at 20/20, then the deferred pagination fix.

### Outlook (→ ~Jul-09)
- Build the ≤7d fade-cycle loop (scan → gate → size → ledger) and route the freed $9.74 + $12 pUSD through it.
- Present the operator the capital case (marginal expected return per +$100: short-dated bucket capacity, HYPE harvest at ~$500, parked sleeves) — or formally kill the parked sleeves.
- Daemon restart + creds pre-flight; methodology final analysis at 20/20; VELO ratio still gated; Iran next hard checkpoint ~Aug-16 (MOU expiry), Jul-27 EU sanctions review.

---

## Week of 2026-07-02 → 2026-07-08 (audit-implementation week)

**Bankroll:** $165.61 vs $164.95 Jul-02 = **+$0.66 (+0.4%)**; vs $170 ref **−2.6%** (~−3.4pp vs Aave-flat over ~10wk). Recovering steadily off the late-June low; benchmark still lost, Dec-31 = accountability date.

**Realized this week: +$1.93** — closed regime-fall NO @0.93 (DEC-0043, +11.1% on blended $17.37), the second guard-driven exit off the fixed expected-edge scan (+$0.65 hantavirus Jul-2, +$1.93 regime-fall Jul-4). Both came from mark ≥ honest prior → NEGATIVE_EDGE → sell into bid at E[hold] (the consumed-edge rule codified in doctrine §5). ARB starter +3.5% vs entry (gave back some on crypto beta). Book now 4 NO legs + ARB.

**The week's real work was the audit + its implementation (full record journal 2026-07-02/03):**
- Skeptic+champion approach audit → SOUND-with-corrections. Shipped: check_marginal_apy fixed win-assumed→expectation math (produced BOTH realized exits); heartbeat session-liveness dead-man switch + daily_checkin auth post-flight (outage hardening, both modes); prior-hygiene pass (monitoring priors = honest centrals).
- **The short-dated fade bucket FAILED REPLICATION** (N=836 fresh: 0.90-0.95 −0.5pp vs the claimed +4.8pp; negative at asks) → population fade-harvesting DEAD, falsified at $0 deployed (gates blocked while measurement ran). Surviving PM edge = case-by-case catalyst-gated instance mispricing (doctrine §3.1 rewritten). Haircut design pass → keep flat 0.05.
- Iran de-risking validated: regime-fall (the exposed leg) exited into strength BEFORE this week's ceasefire-collapse; remaining Pahlavi NO is conjunction-insulated. Two regime-fall re-entry probes (Jul-8) = NO-ENTRY (no gate-clearing dip). incumbent-survives cluster cut from ~40%→~17% of bankroll.
- Ops: 1 dead-session outage (~4d, recovered clean, book gained) + 1 dispatch delay (~8h, noted); operator engaged (VRAM/memory question answered — VIRT-not-RES misread; flagged a stray 251M claude session on pts/5).

**Decisions:** 43 total / 22 resolved. **Ledger:** 8 records (0 entries — every gated candidate correctly skipped; the falsification + 2 regime-fall probes are the discipline working). **Methodology:** 19/20 (straggler in UMA lag).

**Outlook (→ ~Jul-15):** Iran ceasefire "over" per Trump — watch whether active-war resumption is contained (Pahlavi insulated regardless; regime-fall re-entry only if NO dips below the robust bound ~0.88). VELO ratio STILL unpublished (launch imminent, gated). Mojtaba-seen market resolves Jul-15 (ledger). Post-conflict: Tier-1 commodity-headline precision fix.

---

## Week of 2026-07-08 → 2026-07-15 (research-loop week)

**Bankroll:** $168.01 vs $165.61 Jul-08 = **+$2.40 (+1.4%)**; vs $170 ref **−1.2%** — best mark since the reference was set (~−2.3pp vs Aave-flat over ~11wk, closing steadily from −3.8pp at the low). Dec-31 remains the accountability date.

**Realized this week: $0** (no closes). The gain is ARB: $17.95 vs $15.00 cost = **+19.6%** vs entry (+~16pp on the week) on the Robinhood Chain announcement (10% of ALL Arbitrum L2 fees → ecosystem, 8% → tokenholder treasury — the first direct fee-value link for the token, i.e. the delegated thesis's actual catalyst). Declined to chase the add at +22%; retrace-add re-armed ~0.075-0.080 as a daemon trigger. **One new PM entry:** US-invade-Iran NO 12sh @ 0.82 ($9.84, DEC-0044) — strict-criteria instance thesis (territorial-control-intent bar vs 18.5% war-heat YES). Book: 5 NO legs (cost ~$86) + ARB.

**The week's real event — the operator reset the operating model (2026-07-15, Telegram, three messages):** "cast a wide net daily" → "you have the VM 24/7... run some script constantly, just cap the memory" → **"do research until you discover a profitable opportunity. Then report back, invest an adequate amount, and go back to researching. The only limit is token limits and VM compute."** Continuation checks are research slots now, not idle-by-default. Day-1 execution:
- **`opportunity_watch.py` shipped + live** — 24/7 daemon (5-min armed price triggers: ARB retrace-add, regime-fall ≤0.88 re-entry; 15-min consistency/monotonicity arb sweeps as subprocesses; RSS self-cap 150MB + crontab keepalive; actionable hits telegram + fire a tick). Closes the latency gap between 2×-daily ticks — arbs are ephemeral.
- **Wide-net funnel, day 1:** ~30 raw candidates → 2 instance-gated → 1 ENTER (US-invade NO) + 1 informed SKIP (Hormuz-fees YES — the gate's fresh catalyst check caught Trump's 24h toll backtrack my headline recall had missed; market was efficient at 1.3%).
- **Two research studies launched** (background agents, running now): UMA dispute-window mispricing; new-listing mispricing. Queue: conditional-probability consistency scanner.

**Ostium exploited for $18M (oracle attack, Jul-15) — exposure ZERO, verified on-chain** (0 perps, no vault deposit, no residual margin). Three weeks ago skeptic+champion PARKED the planned OLP deposit (DEC-0040: "53% APY is a mirage") — OLP depositors are the counterparty backstop behind a 24-48h cooldown, exactly who ate this. The process's clearest avoided-loss to date; OLP marked TERMINAL.

**Ledger lessons:** Mojtaba-seen resolved — **fade would have WON** (NO 0.997 at deadline) but the market was DE-INDEXED from the PM UI mid-life while still trading on CLOB (operator couldn't find it; discoverability/exit-liquidity risk class logged). Methodology experiment CONCLUDED at 20/20: zero_shot +0.29/$ beats all four multi-agent variants out-of-sample (mechanism = selectivity, not leakage) — skeptic+champion stays reserved for >$10/new-class/structural, zero-shot for routine takes.

**Ops:** one session-restart outage (~11h, Jul-15) killed both research agents mid-study — relaunched same day; opportunity_watch survived at host level (designed-for), guards all clean through the gap. Auth post-flight + dead-man switch + keepalive now cover all three observed failure modes.

**Decisions:** 44 total / 22 resolved. **Ledger:** 10 records (1 ENTER, 9 skips/probes/falsification records).

**Outlook (→ ~Jul-22):** Research-loop cadence: synthesize UMA + new-listing study verdicts (report → build monitor/entry rule if REAL, clean kill if not) → next thread. Iran: Jul-27 EU sanctions review, ~Aug-16 MOU expiry checkpoint. VELO ratio still gated (Aero launch ~this month). Daemon triggers armed: ARB ≤0.080 add, regime-fall NO ≤0.88 re-entry. Sunday weekly long-term review due Jul-19.
