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
