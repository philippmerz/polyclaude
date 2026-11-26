# Hunt iteration log — 2026-11-08 evening (executor, ~18:50–19:10 CET)
Dry powder (bankroll.py 18:55 CET): pUSD $7.17 deployable; Polygon aUSDC $18.35 + aUSDC.e $3.51 (needs Aave withdraw); USDC $0.11.

## N1 Intraday weather, already-observed-trend vs book (Mexico City MMMX Nov 8 high) — LEAD (not placed: gate)
Intuition: on hot/sunny-highland stations the book anchors on raw GFS/ECMWF max; both run hot at MMMX this week.
Evidence: MMMX obs max Nov4-7 = 26/25/23/23 vs GFS 25.4/25.7/24.6/24.0 (bias mean -0.7C), ECMWF 27.0/27.3/24.9/24.7 (bias ~-1.7).
Today GFS 24.4, EC 25.3 -> bias-corrected ~23.6C. Analogs: noon obs ~20-21C on Nov6/7 -> max 23; Nov5 23@noon -> 25. Today 21@11:44 local (17:44Z METAR 21/09).
Rule: highest routine METAR (SPECI excluded), whole C at MMMX (no T-group). My p: <=22 ~8%, 23 ~27%, 24 ~40%, 25+ ~25%.
Book 18:05Z: 23C YES asks 0.11x15, 0.12x5, 0.14x10; bid 0.06. 24C 0.50/0.69. 25+ 0.18/0.41. Fee 5% * p(1-p) taker (~0.5c at 0.11).
EV at 0.115 eff: +0.155/share (robust p 0.17 still +0.055). Size $2.40 (~21 sh). Downside -$2.40, no exit liquidity (hold to resolution).
Invalidation: any routine METAR >=24 before ~16:00 local (22Z); or 18:4xZ print >=23 with clear skies. Data: /workspace/hunt2.
polyclaude_enter --execute BLOCKED: "canceled order 0x2166d13dca2426b3 lacks affirmative terminal status" (stale Nov-2 Fable reservation in .entry_reservations.json; cancelVerifiedAt set but CLOB order lookup no longer returns 200/CANCELED). Did not bypass the gate.
Added priors entry highest-temperature-in-mexico-city-on-november-8-2026-23c (cluster wx-mmmx-2026-11-08) to portfolio_kelly_priors.json (uncommitted).

## N2 Cancelled-fixture rule arb (soccer "draw" markets resolve YES on cancel) — weak lead
Vitesse–De Graafschap (Eerste Divisie) definitively called off 12:15 CET (NOS/KNVB: will be replayed, date TBD). Riga FC–RFS (Virsliga) cancelled: Riga boycott; LFF disciplinary may give 0-3 technical defeat (rule 4.12.3), committee "next week".
Rule text: canceled / not started by Tue Nov 10 23:59 ET -> Draw=YES, team wins=NO. Awarded-result clause is scoped to ABANDONED games only.
Books: Vitesse draw YES 0.977/0.981; Riga draw YES 0.957/0.984 (20) then 0.985 (1293). Fees ~0.06c.
p(Vitesse YES)~0.985-0.99, p(Riga YES)~0.97-0.98 (UMA could be argued toward awarded 0-3). Edge 0.5-1% on Vitesse, ~0 on Riga. Tiny $ on $7. Not worth gas of attention except as a maker idea; Riga RFS-win at 0.053 ask is the tail (forfeit applied by UMA) — not priced as edge.

## N3 Box-office Sunday estimates vs final actuals (The Numbers) — KILLED
Drummer Boy: Fri 3,533,127 + Sat 3,029,424 actual, Sun est 2,750,000 -> 9,312,551. >=9m needs Sun >=2.437M (-11% vs est). p~0.97; book >=9m 0.73/0.975 -> no taker edge; maker bid would be adverse-selected at Monday actuals.
Ramayana: weekend (Fri-Sun, excl. Thu opening day 3.5M) est 8.65M; 8-9m bracket 0.81/0.88, p~0.83-0.85 -> fair. Rule-gap (Thursday "previews" clause -> 12.16M) priced at 0.12-0.17 for >=9m; The Numbers weekend table excludes Thursday, so I'd not buy the gap either.

## N4 Elon tweet-count brackets (xtracker) — KILLED
Nov7-9: 36 posts in first 25h; 40-64 0.33/0.34, 65-89 0.58/0.59. Nov9-11 ladder smooth 1c spreads. Bot-dominated, history (3-day windows 27-157) gives no obvious misprice. No edge found in 10 min.

## N5 Other intraday highs Nov 8 (KORD, KDEN, KATL, KLGA) — KILLED (fair)
KORD obs 13.3 @17:51Z vs GFS 13.7/EC 12.7 -> peak ~60F; 60-61 at 0.62/0.69 fair.
KDEN obs running GFS +0.6..1.0 -> peak ~68-69F; 68-69 at 0.47/0.57 fair.
KLGA: hourly T-groups max 15.0C so far (6h max 10156 = 15.6 is NOT a T-group), 5-min obs 16C; NWS hourly runs ~3F hot. 62-63 NO ask 0.84/0.85 needs p(NO)>0.86; my p ~0.87-0.90 -> 1-4pp, too thin.

## N6 Rule-gap: Ramayana box office "Thursday previews" clause — KILLED (see N3)

## Independent review — 2026-11-08 ~19:10 CET (Investor)
Not placed yet. Waiting for the ~18:4xZ / 12:44 local routine METAR.

Models at Open-Meteo airport-ish grid (19.5N, 99.0W, elev 2223m), 8 Nov local:
- GFS seamless 31 members: control max 21.8C at 14:00; member maxes 21.0–22.30; rounded {21:6, 22:25}; raw P(23)=0.
- ECMWF IFS 51 members: control max 24.6C at 14:00 (22.7@12:00, 23.9@13:00, 24.6@14–15); rounded {23:2, 24:20, 25:25, 26:4}; raw P(23)=3.9%.
- Combined raw 2/82 land on exactly 23. First-pass "GFS 24.4 / EC 25.3" does not match this GFS control (21.8).

Live obs: latest routine MMMX 081744Z / 11:44 local still 21/09 FEW200 HZY CU ARND. Official high so far 21C. Running ~1C warm vs this GFS (GFS ~20 at 11:44) and ~1C cool vs this ECMWF (~22.3).

Analogs (routine METARs only):
- Nov 2: 21/09 FEW015 HZY @11:43 -> 22@12:42, 23@13:41, 24@14:40, 25@15:50. Max 25 under SKC. Same T/Td/clock as today.
- Nov 6: 21/07 SKC @11:49 -> 23@12:45 then stalled under BKN020CB / TEMPO TSRA. Max 23 (convection-capped; the first-pass analog).
- Nov 7: 20/08 SKC @11:45 -> 22@12:45, 23@13:45, held 23 through 16:40. Max 23.
Today is closer to Nov 2 on dewpoint (9) and has only high cloud (FEW200) plus "CU ARND".

My p(exactly 23): ~18–25%, not 27%. 23 sits in the crack between a GFS/capped regime (~22) and an ECMWF/Nov-2 sunny regime (~24–25). Still +EV vs ~11.5c effective (breakeven ~11.5%) after a haircut, but thinner. A 22C print at 12:44 is the dangerous Nov 2 pace, not an automatic take. Decision tree: take a small ticket ($1–2, not $2.40) only if 18:4xZ is still 21C; pass if >=23 under still-sunny/FEW skies; treat 22C as ambiguous/pass-leaning.

Gate: CLOB get_authenticated_order(0x2166d13dca2426b3…) returns HTTP 200 with body null (not a CANCELED dict). list_authenticated_trades exhausted page (next_cursor LTE=, n=140) has 0 rows mentioning that order. research/2026-11-02-fable-cancel-block-resolution.json already attests size_matched 0 and CANCELED at ~12:27Z on 2 Nov. Did not edit .entry_reservations.json or bypass enter.py yet.

## Independent review update — 2026-11-08 19:26 CET — KILLED
SPECI MMMX 081808Z (12:08 local) printed 23/10 FEW200 HZY CU ARND, wind calm. SPECI does not count under the market rule, but it is a leading indicator: official high is still 21C (081744Z routine). Heating 21→23 in 24 minutes under FEW200 is the Nov 2 hot path, ~90 minutes ahead of Nov 2's first 23C (13:41 local that day).
Decision: do not buy 23C YES. Invalidation hit in spirit (already 23C under clear/high cloud before the 18:4xZ routine). Remaining hours of heating make exactly-23 a stall/convection bet; November is usually dry, and today is not yet BKN020CB the way Nov 6 (max 23) was.
Live book ~18:26Z: 23C YES 0.05/0.10 (21sh at 0.10); 24C 0.48/0.68; 25+ 0.22/0.49 (5@0.49, 21sh avg ~0.50).
Revised p after SPECI: ~12% / ~38% / ~50% on 23 / 24 / 25+. 23 at 10c is roughly fair-to-thin and I don't believe the stall; 24 at 68c is far too expensive; 25+ at 49c is about fair vs ~50%. No order.

## Executor iteration — 2026-11-08 ~19:45 CET
### N7 Mechanical: negRisk YES-sum / NO-basket scan (top ~1500 active events by 24h vol, gamma bestBid/Ask) — KILLED
Script /workspace/hunt3/nr.py. Low YES-sums were all non-exhaustive listings (inactive placeholders / missing "Other"): AFC group E, Lima mayor, Billboard 200, Millennium, Fed Apr-2027. Best top-of-book NO-basket edges: NBA 2027 champ +1.7c over 30 legs, Worlds 2026 +1.0c, Paris/NYC temps <1c. Venue min ~5sh/leg makes the NBA basket ~$145 for <$2.5 gross, and depth beyond top of book wipes it out. No lock that fits $7.
### N8 Millennium Prize "which will AI solve next" (Dec 2027) — KILLED
Navier–Stokes excluded; "No solution" 0.29/0.30. Fresh news flow (OpenAI YM existence claim 26 Oct, Hodge withdrawals, 3-SAT/ETH claims) leaves no documentable misprice, plus 14-month lockup. No edge.
### N9 Billboard 200 #1 week of Nov 14 — KILLED (closest call)
Tracking week Oct 30–Nov 5. HITS Daily Double final: Rodrigo 56,655 vs MJ Thriller 53,130 (+86%, Halloween/vinyl); QOTSA Perfecth 26,387 (so the UK/AU #1 is irrelevant in the US). Thriller is NOT a listed outcome ("Other" inactive), so a Thriller win means NO on Rodrigo. PM Rodrigo 0.72/0.86; Kalshi ~89%. My p(Rodrigo) ~78–85% (HITS-vs-Luminate flips at a ~6% gap are uncommon but real). YES at 0.86 is too high; NO at 0.28 needs p(Thriller)>28%. Inside the spread, no taker edge. Billboard announces Sun/Mon. Also, an unlisted winner creates rule ambiguity.

## Independent note — Billboard N9 — 2026-11-08 19:30 CET
Agree with the kill: Rodrigo YES 0.71/0.86 (mid 0.785); no official Billboard chart yet. Market rules say Billboard updates each Tuesday; the Nov 14 chart should publish around Tue Nov 10, not Sunday. HITS-vs-RGM midweek was ~56k Rodrigo vs ~52–53k Thriller (Nov 4 RGM writeup); Thriller is unlisted and "Other" is inactive, but that does not create ambiguity for a Rodrigo YES/NO market — if Thriller is #1, Rodrigo resolves NO. YES at 0.86 is too rich vs a ~80% prior; NO at ~0.29 needs p(not Rodrigo) > 29%. Watch item for Tuesday's official chart, not a lead tonight.

## Executor iteration 2 — 2026-11-08 ~20:15 CET
### A. Nov 9 weather (39 cities). Raw: /workspace/hunt3/wx9_raw.json, an9.py, chi9_books.txt, prev_kord.json, kord_metar.json
Raw GFS+ECMWF ensemble vs book threw up many "edges" in Asia (Tokyo 14C, Shanghai 17C, Shenzhen 28C at 0.91-0.96). They are ARTEFACTS: those are midnight carryover. RJTT was 14/15C at 00:00 JST and is cooling all day under -RA; ZSPD 17C at 00:00 CST. Ensembles also run cold at the station. KILLED. Miami 84-85: KMIA obs ~2-3F above models today, so the book's warm tilt is justified. KILLED. NYC (NWS 60, NBM 58, ECMWF 57.4 vs 58-59 at 0.59) and Atlanta (NWS 69, NBM 70.5, GFS/HRRR 73.4): model spread covers the book. KILLED.
**LEAD — Chicago KORD Nov 9.** Rule: highest routine-METAR T-group (tenths C, SPECI excluded) at KORD, local date, converted to whole F rounding half up. Forecasts for Nov 9: NWS point 57/58 ("high near 58", mostly sunny, light SW). NBM 56.7, GFS 57.0, HRRR 57.0, ECMWF 56.6, ICON 57.8, GEM 58.1, UKMO 56.6, JMA 59.6, AIFS 59.6. Ensemble 82 members 55.4-59.0 (median 56.8). Day-1 verification Oct 31–Nov 7: NBM error within about ±1.5F, no cold bias (e.g. Nov 7 50.5 vs obs 51.1; Nov 3 73.0 vs 72). Book (walked): 60-61 YES 0.55/0.59; NO asks 0.45x457, 0.46x85,591 (a whale YES bid of about 85k sh at 0.54); 58-59 0.18/0.21; 56-57 YES asks 0.042x25, 0.043x5, 0.044x5, 0.047x30; 54-55 YES 0.017x36. The book is centred ~60.5F vs a consensus ~57.3F.
My p: center 57.5, sigma 2.0 (fat-tailed allowance) → P(>=60) about 12%, P(60-61) about 10-14%, P(56-57) about 33%, P(58-59) about 30%. Haircut by blending 50/50 with the market: P(60-61) about 0.33 → NO fair about 0.67 vs effective 0.462 (ask 0.45 + 1.24c fee).
Caution: today (Nov 8) the KORD book also sits 60-61 at 0.67/0.70 vs day-1 NBM 58.2, with obs 56F at noon CST. Tonight's KORD max is the test of whether models are under-running this sunny-SW regime.
Recommended (Investor to gate):
  polyclaude_enter.py --slug highest-temperature-in-chicago-on-november-9-2026-60-61f --side NO --my-p 0.80 --max-price 0.47 --usd 4.5 --execute
  optional: --slug highest-temperature-in-chicago-on-november-9-2026-56-57f --side YES --my-p 0.25 --max-price 0.047 --usd 1.3
Dry-run (no --execute) returned NEED_REVIEW "candidate lacks a configured correlation cluster". With --edge-haircut 0.5 it returned SKIP (pessimistic p 0.30). Nothing placed.
Kill/invalidations: (1) today's KORD routine max >= 60F (15.6C T-group) with day-1 models at 58 → models under-run this regime; cut p(60-61) to the market's view and pass. (2) The NWS/NBM 00Z run lifts the Nov 9 max to >= 59. (3) The book moves to NO >= 0.60 before entry. Downside: lose $4.50 if KORD prints 60-61F.
### B. Polymarket vs Limitless — KILLED. Raw: /workspace/hunt3/lim*.json
328 active LM markets; most volume is in crypto up/down and FDV-launch markets with no PM twin. LM "prices" are empty-book mids (Greenland "0.4455" is really 0.003/0.888). Matched pairs (walked LM orderbook vs PM): Netanyahu out 2026 LM 0.44/0.48 vs PM 0.46/0.47; Taiwan invasion 2026 LM 0.011/0.025 vs PM 0.016/0.017; Trump out before 2027 LM 0.02/0.035 vs PM 0.028/0.029. All bracket PM, no cross. The only cross is US BTC reserve before 2027: LM bid 0.052 (~1 sh), then 0.051 (~106 sh), vs PM ask 0.039. That is about 1.2c gross per pair, locked to 1 Jan 2027, needs a funded LM account plus LM fees, and the rules are not verified identical. Not worth it at $7.

## Independent review + trade — Chicago KORD Nov 8 58-59F YES — 2026-11-08 19:00Z / 20:00 CET
Live routine METAR KORD 081851Z 26009G17KT 10SM SCT250 14/05 A2993 RMK AO2 SLP135 T01440050: T-group 14.4C = 57.92F -> 58F. Official high so far 58F (SPECI excluded). Heating 09-12 CST: +2.8 / +1.6 / +1.1C; NWS LOT 66,77 nailed 12:00 CST=56 (live 11:51 13.3C/56F) and 13:00 CST=58 (live 12:51). Period forecast "This Afternoon" high near 59; hourly 14=58, 15=59, 16=57. Monday (Nov 9) bumped during the afternoon from high near 57 to high near 58, hourly still peaking 58.
60F requires T >= 15.3C (+0.9C from 14.4). Remaining-max-heating N(0.6C, 0.9C) => P(58-59)~63%, P(60-61)~31%, P(62+)~6%.
Live books ~18:56Z after the 58F print: 58-59 YES 0.06/0.11 (41.6 sh @ 0.11); 60-61 YES 0.67/0.80, NO ask 0.33 x22; 62-63 YES 0.136/0.238; 56-57 correctly dead at 0.001.
Chose 58-59 YES at 0.11 over 60-61 NO at 0.33: same core thesis (do not heat another 0.9C) but much higher ROI (eff cost ~0.115 vs my p 0.63) and smaller cash at risk. 60-61 NO is more robust to a 62+ overshoot (~6%) but worse dollars-of-EV.
TRADE: polyclaude_enter FAK BUY 19 YES @ 0.11, makingAmount $2.09, order 0x4e0ade340ade74651a1afdefb8748ccb2ec6db5a5649d40bff8ceab57f1fe560, tx 0x1bee9dc644dd3557e61ba65d53260264a2b1b0e8dd0b2c323e492eda121f8d22, matched 2026-11-08T18:59:59Z. Taker fee preview 0.49c/sh (~$0.09). Hold to resolution (thin exit). Downside: lose ~$2.18 if official high reaches 60F+.
Nov 9 60-61 NO still a watch (NWS high near 58 / ensembles 0/82 in-bucket vs book ~56c YES) — do not take until today's official high is known. Invalidate Nov 9 if today's routine max >= 60F (15.3C). Next observational checks: 19:51Z and 20:51Z / 21:51Z METARs; peak ~21-22Z.
Fable leftover reservation 1793620888252154939-2093f222 retired before execute via _remove_entry_reservations after fresh proof (research/2026-11-08-fable-reservation-retirement.json plus the Nov 2 cancel-block file): GET 200/null, 0/140 trades, not in open book (3 live SELLs only), 0 positions. Fed #179 row preserved.

## Niche iteration — 2026-11-09 ~09:05 CET (routine)
### Result: Chicago KORD Nov 8 58-59F YES — LOST
Official routine max T-group 16.1C (082051Z) = 61F. Day-1 NBM 58.8 / EC 59.1 under-ran by ~2F; GFS/HRRR 61.1 nailed it. Lesson: in this sunny SW regime at KORD, trust GFS/HRRR + NWS over NBM/EC; the book was right. ~-$2.18.
### K1 Chicago Nov 9 60-61 NO — KILLED
Invalidation hit (Nov 8 printed 61F). NWS now 61; GFS/HRRR 60.1, ICON 58.4, NBM 57.1. Book 60-61 0.66/0.70, 58-59 0.13/0.16, 62-63 0.10/0.12. Model blend ~60 with +2F bias correction -> P(60-61) ~0.55-0.62; NO at 0.34 is at best a few pp. Pass.
### K2 Resolved-but-unsettled Nov 8 weather (Seattle/Denver/LA/SF highs+lows) — KILLED
Winning buckets already bid 0.98-0.999. No spread to harvest.
### K3 Extreme-tail earthquake markets — KILLED/thin
M10+ before 2027 0.015/0.017 (NO ~1.7% over 12 weeks incl. Jan resolution lag); M9+ 0.022/0.025 vs ~1.3% base -> thin.
### L1 USGS M7.0+ count in 2026 — TRADED
Count = 13 (USGS FDSN, minmag 7.0, 2026-01-01..now; Nagqu M7.0 mww reviewed 22 Oct; no pending M6.9 upgrades; M6.5+ since Oct clean). Rule: USGS total M7.0+ Jan 1–Dec 31 2026 ET.
Base rate: USGS 1976–2025, sliding 53-day windows (step 3d): P(0)=0.153, P(1)=0.26, P(2)=0.265, P(3)=0.16, P(4-6)=0.154, P(7+)=0.007. 2026 itself already had two gaps >=53d (Jan1–Feb22, Aug14–Oct9).
Book: 11-13 YES 0.009/0.089 (114.5 sh at 0.089, mid shows 0.049); 14-16 0.54/0.71; 17-19 0.21/0.23; 20+ 0.008/0.031. Taker fee 0bps.
TRADE: BUY 28.31 YES "11-13" at avg 0.089, $2.52, order 0xb43a671fe24cf7c6b7df5379cb8415b9a0a707867f80a7dbd316605d6b57c65a, tx 0x5f9aa09b1fbcfa60af76ee35110b8bb7aa68ab84ed897070305bb25764e4c9fd. p=0.15 vs 0.089 -> EV ~+$1.7 (+68%). Max loss $2.52. Pays ~$28.31 if no M7.0+ worldwide by Dec 31 23:59 ET.
Invalidation: any M7.0+ (USGS) before year-end -> position ~worthless; no exit needed. Watch only for a 6.9→7.0 revision of older events (none pending).
Secondary (not taken): 17-19 NO at 0.79 vs P(NO)~0.85 (~7%, capital heavy); 14-16 YES 0.71 vs 0.685 (no edge).
Generalizable idea for next cycles: count/base-rate markets (earthquakes, hurricanes, named storms, Elon-style counts with long windows) where the book overweights recent rate — compare against long USGS/NOAA catalogs.

## Niche iteration — 2026-11-09 21:20 UTC
### M1 Weekly USGS M5.5+ exact-count brackets — KILLED after matched-cutoff measurement
- Contract/event 1326719: Nov 9 00:00 ET through Nov 15 23:59 ET; <=6, exact 7/8/.../13, >13; USGS FDSN preferred records. Exact 8 is not 8+.
- USGS at 21:00:46Z: 0 qualifying events after 16.01h; M4.5+ control count 12 confirms newer catalog activity. Fresh historical query returned 1,035 unique qualifying events across 114 complete Monday weeks through Nov 9.
- Conditional on 0 at the matched 16.01h cutoff: <=6 = 19/54 (35.2%) all vs 5/23 (21.7%) latest 52; exact 7 = 16.7%/26.1%; exact 8 = 14.8%/13.0%. Quotes: <=6 YES 0.34/0.36; exact 7 0.11/0.14; exact 8 0.09/0.12; taker fee 0.05*p*(1-p).
- Verdict: no robust side. <=6 YES is below its 0.367 fee-inclusive cost on a central pooled/latest blend; exact-8's small central edge disappears at the 0.10 haircut; exact-7 changes sign across cohorts. No order. Raw receipts/analysis: `/tmp/opencode/usgs_weekly_20261109_2125_v2` (the first capture directory failed before network because metadata omitted read_only).
### M2 OpenRouter weekly market-share ranks — KILLED for current cash/robustness
- Official `modality-chart?routeSegment=text`, cached 20:53:33Z, already has partial Nov-9 absolute author data. Current shares: DeepSeek 30.36%, OpenAI 19.08%, Google 14.56%; next labs Z.ai 5.93%, Qwen 5.83%, Anthropic 5.64%. Nov-2 finals were 31.80/19.31/13.64%. Rules skip Others/Stealth and resolve the displayed Nov-9 week when Nov-16 first displays.
- Books: DeepSeek #1 YES 0.953/0.982; OpenAI #2 0.59/0.97; Google #3 0.77/0.98; Google #2 0.002/0.035; OpenAI #3 no bid/0.23. Five-share minimum makes the stable leaders exceed $2.46 free pUSD; current-rank longshots do not survive a 0.10 haircut. No order.
### M3 Existing annual USGS 11–13 YES — premium SELL lead/action
- Count remains 13 (USGS generated 20:53–20:56Z); no M6.5+ near-threshold additions since Nagqu beyond reviewed Vanuatu 6.8/Bonin 6.5. Live YES book 0.004/0.088, fee 0. No add: price is not improved versus the 0.089 entry and a low resting BUY would be adversely selected after a thesis-breaking M7.
- Action: post-only SELL 28.31 YES @0.20, order `0xa186d87014105075a5f6061d3fad64767ba3f4a97859ddd79f8903c030da4af6`, LIVE/0 matched at 21:17Z. Central fair 0.15; 0.20 also exceeds about 0.168 fair sensitivity after 72h with no event. Initial 28.3146 post got HTTP 400 (two-decimal SELL accuracy); authenticated book showed no order before the 28.31 correction. No cash spent or position sold. DEC-0277.
- Resolution: USGS M7.0+ catalog, Jan 1–Dec 31 2026 ET, with the written late-report window. Invalidation: any new M7.0+; retain the underlying ticket to resolution if the premium offer does not fill.

## Niche iteration — 2026-11-10 12:25 UTC

### P1 Iran blockade-end NO by Nov 15 — KILLED on evidence and cash
- Exact market 6282802 / condition `0xf036481613a53faafdc7638824e5dfab03b4dda5b9bf13fbdfa2075e2d4a8bea`; only a definitive official US declaration of general end/suspension qualifies, not a vessel exemption, conditional diplomacy, or actual traffic normalization alone.
- Fresh evidence: Al Jazeera Nov 9 reports another Saudi East-West pipeline attack (operations unaffected, fighting intensifying, Hormuz tightly constricted); CBS Nov 10 says oil dipped partly on hopes that midterms could open a US-Iran deal. The first cuts against a quick end; the second preserves announcement risk before physical normalization.
- My P(qualifying announcement by Nov 15) is about 8%, not the 4.9% YES ask. NO fair about 0.92 vs live NO ask 0.952; no robust edge. Five shares cost $4.76, also above $2.462932 free pUSD. Catalyst worker timed out; primary criteria and articles above were read directly. Invalidation of the fade: an official general end/suspension declaration or credible advanced talks that sharply raise its near-term probability. No order.

### P2 Anthropic best Text Arena model in November — KILLED as source/identity mismatch
- Exact market 4664660 / condition `0xe9d6e58164712e837a5f64114dd2814d73748e6a6f2db09216e66a55bcb28f45`: company owning top Text Arena Overall model, style control off, Nov 30 noon ET.
- Anthropic's Nov 9 Fable 5.2 launch is a genuine capability catalyst, but Arena's official changelog adds Fable 5.2 to **Code Arena WebDev**, not the resolving Text Arena. The exact Text source and raw route return 403, so current rank is unknown. Issuer benchmarks and testimonials cannot substitute for preference rank or a fresh table. The catalyst worker also timed out. YES moved 0.22→0.24 during review; no entry. Reopen only on a dated exact-table observation or Text Arena admission with both-side economics and robust probability.

### P3 Weekly USGS M5.5+ brackets, matched 31.16h cutoff — KILLED on robustness/cash
- Event 1326719; current USGS count is still zero through 2026-11-10T12:09:20Z (31.1556h), while M4.5+ control count 22 confirms newer catalog activity. Historical 1,035 unique events / 114 complete Monday weeks reused from the Nov 9 capture.
- Conditional on zero at the same elapsed cutoff: <=6 = 12/31 (38.7%) all vs 4/14 (28.6%) latest 52; exact 7 = 19.4%/28.6%; exact 8 = 16.1%/21.4%. Full terminal counts remain dispersed, so this is not a lowest-bracket lock.
- Live <=6 YES 0.44/0.49 is rich against a ~0.34 blended central estimate. NO at 0.56 has central probability about 0.66 but costs $2.80 for five shares, exceeds free cash, and is only marginal at a 0.10 stress. Exact 7 at 0.18 and exact 8 at 0.12 both lose robustness after the 0.10 haircut. No order.

### P4 Annual USGS resting SELL — REPRICED, not an add
- FDSN count remains **13** through 11:52Z. Since Oct 22 the only M6.5+ rows are reviewed Nagqu M7.0, Vanuatu M6.8 and Bonin M6.5; no new near-threshold upgrade. Best YES book remains 0.004/0.088 with only $5 market volume24hr, so the midpoint drop is not evidence of a thesis-breaking event.
- No add: 0.088 is not improved and a routine taker lacks urgency; a low resting BUY would be adversely selected after a thesis-breaking M7. Repriced premium SELL 28.31 from 0.20 to **0.18**, strictly above the 0.15 central fair and prior 0.168 72-hour no-event sensitivity. New order `0xbc12b7675b7f32bf5a24fd65ee5672e9838ff3af5d17ac0ce9df278f0ee1b1da`, LIVE/0 matched. Potential $5.0958 cash exceeds $4.2465 central hold value; any new M7.0+ invalidates. DEC-0278.

### P5 Messi held-leg data review and renewal — HOLD, no add, premium exit retained
- Google's 2026 hub remains 404. Current official methodology confirms fastest prior-year-period traffic growth using internal tools, Jan 1–Nov 25 for 2025; it is not raw volume and provides no reproducible scoring export. Public normalized Trends data cannot reconstruct the internal Global Athletes list. Historical absence from displayed 2021–25 top tens was already in the original thesis and is not a new base-rate estimate.
- Fresh football/FIFPRO items supply no ranking measurement. With no new exact full-field observation, retain the unfitted 0.60 central / 0.40 selected-stress estimate as dated, not newly validated. No add at 0.49 and no taker profit at the 0.43 bid.
- Renewed all 5 YES SELL @0.65 before the old order's 18:03Z lifetime boundary: new order `0x6428a01147745e273ff62619c5c3f69e87c0fa135114456ab71ce24331e6809d`, LIVE/0 matched; old `0xdc97243e…` canceled. Potential $3.25 exceeds central $3.00 hold value. Invalidation: official 2026 list/method/cutoff, measured full-field data against Messi, or a known scheduled release inside the quote window. DEC-0279.

## Niche iteration — 2026-11-11 14:00 UTC

### Q1 Messi perennial-baseline re-underwrite — EXITED
- The old 0.60 estimate was unfitted and lacked a measured full-field growth comparison. Google's spike-versus-prior-year method, Messi's absence from the displayed 2022 World Cup-year list, and stronger 2026 breakout competitors do not support that fair. Revised YES to 0.30 central / 0.20 stress; a sustained YES case would require measured internal-growth evidence against Haaland/Liu/Malinin and other breakouts, not more ordinary Messi headlines.
- Sold all 5 YES at 0.41 through guarded FAK SELL; gross $2.05, wallet-verified net **1.98953 pUSD**, above $1.50 central/$1.00 stressed hold. Order `0x76beee0db369615c5686f8d9c85ccf8efe780a2de3964af5ab94cb43325a525b`, tx `0x46f177692340027563f939b4970b2132399cc08b9d08dca3036815ace9e1e95f`; DEC-0280. Premium rest disabled; no re-entry without fresh full-field evidence.

### Q2 PM/Kalshi largest-earthquake nesting — KILLED as a trade
- Nov-11 PM event 1346377 and Kalshi `KXBIGGESTQUAKE-11NOV26` share USGS/ComCat and UTC day, but PM preferred magnitude/nearest-tenth/revisions through 14:00 ET Nov12 differ from Kalshi reviewed/primary-magnitude/expiration rules. Settlement equivalence is not proved.
- Genuine shared-magnitude inclusions exist: `K>=6.2 => PM 6.1+ => K>=6.0`; `K<5.2 => PM Under-5.3 => K<5.4`. PM 6.1+ YES was 0.01/0.92 versus Kalshi >=6.0 YES 0.13/0.17 and >=6.2 YES 0.08/0.11: no violation or cheap reference edge. All 12 PM sides failed the 0.10 haircut at five shares and every quoted five-share debit exceeded available cash; cheapest was $4.570475. Kalshi remains an unfunded reference, not an execution leg. Nov12 had PM event 1354211 but no naturally listed Kalshi counterpart in the 72-event series response.

### Q3 Whole-degree weather rules — WELLINGTON MAKER LEAD; MEXICO LOW KILLED
- The screen already handles SPECI exclusion and rounding; there is no standalone loophole. Wellington is an instance-level model/observation dislocation. Market 6923347, condition `0x3df151e6dc29b77500a1659a2f87564d9e6f3469d06d2007ccc42dd0327272e4`: exactly20C requires routine NZWN Nov12-local qualifying value in [19.5,20.5). Target-date routine max 17C through 13:30Z; deterministic ECMWF/GFS/ICON/GEM/UKMO maxima 17.5/17.4/18.1/17.8/18.4C; raw 82-member ECMWF+GFS ensemble 0/82>=19.5. Six-day bias/wider-error sensitivity remains below threshold.
- Use conservative P(NO)=0.90 (0.80 stress), not the fitted 0.947 central, against NO bid/ask 0.55/0.60. `polyclaude_enter` cleared UMA, robust edge, $3.92 ticket and unique `wx-nzwn-2026-11-12` cluster caps. Posted post-only BUY 7 NO @0.56, **$3.92**, LIVE/0 matched: `0xb3e17d6a7824be37a08aeda80a59403f3552d0d8d44089f0624e5fdbe0d65e09`, DEC-0281. No taker fallback; any routine20C, model shift toward>=19.5 or adverse rewalk cancels.
- Mexico City Nov12 exactly14C NO failed: model disagreement and measured residual gave only ~0.861 stressed NO; five-share taker $4.474475 exceeded cash and maker0.88 was negative under the 0.10 haircut. Scan bound: 91/94 Nov12 events/1,001 bins completed after mapping/HTTP exclusions; only Wellington and Mexico received deep verification, not an exchange-wide zero.

## Niche iteration — 2026-11-20 13:30 UTC

### R1 ANT post-IPO price markets (open Anthropic book): one LEAD traded, one killed
- "Above IPO price at end of first month" (measurement Nov 30 close, IPO $83): ANT pre-market $88.02. 6 sessions at ~5.5% daily σ gives P(Up) ≈ 0.67. Greenshoe stabilization near $83 adds a few points → fair ~0.70 vs a 0.58/0.72 book. **KILLED**: no edge on either side.
- Dec-31 market-cap brackets (negRisk event, nine buckets): the books are hollow (YES asks 0.6–0.7, mids ~0.35 are meaningless). Share basis read from S-1/A2: 13.087B all classes (A+N+T+E+F), ~13.24B after the upsize, so the cap is ~$1.165T at $88. Lognormal bucket fairs (70–100% vol): <750B 3–10%, 0.75–1.0 ~23%, 1.0–1.25 ~36%, 1.25–1.5 ~24%, 1.5–1.75 ~10%, 1.75–2.0 3–6%, 2.0–2.25 ~1%, 2.25–2.5 0.3–1.4%, ≥2.5 <0.5%.
- NO asks vs fair: 2.25–2.5 0.94 vs 0.985 (**TRADED** 7 sh); 1.75–2.0 0.90 vs 0.94–0.97 (vol-sensitive, cash-limited, not traded); ≥2.5 0.97 vs 0.995; 2.0–2.25 0.98 vs 0.99; <750B 0.95 vs 0.90–0.97 (no).
- Re-check: if cash frees up, the 1.75–2.0 NO at ≤0.90 is the next add. Kill it if ANT rallies above $115.
- No arb: the sum of NO asks is 8.58 against an 8.00 payout.


## Evening self-critique — 2026-11-20 18:00 UTC (Investor, sole operator)

**Working**
- Exiting at the source. Reading nasdaq.com's own MarketCap figure (the resolution input), not headlines, let me sell every LOW leg at 0.99+ (1.4T/1.35T this morning, 1.275T tonight). That recycled ~$22 into ~8–9pp edges instead of waiting until Dec 1 for $1.
- Mechanical-calendar and price-tail bets (NDX Fast Entry calendar, Dec-31 cap far brackets) use a 0.03 haircut, not the blunt 0.10. That fixes the BTC-flip miss.

**Not working**
- **Crypto sleeves are unmanaged beta.** WBTC + HYPE + Arb ETH are ~52% of the whole account, and they caused ~$5.8 of today's −$6.83. No one has re-underwritten them since the Nov 9 rebalance, and there's no thesis, invalidation, or hedge on file. They are the dominant P&L driver, yet they get the least attention.
- **Cash starvation costs fills.** The PM sleeve sat at $0.35 pUSD. I found the ≥2.5T NO at 0.90 × 200 (fair ~0.99), but while I was withdrawing from Aave and wrapping, it was lifted to 0.95, so I had to settle for the 2.0–2.25T leg. The 13:30Z session's 1.75–2.0T NO at 0.90 was also cash-blocked. Keeping 3.4% APY on $3.5 of aUSDC.e is worth ~$0.01/month, while a missed 9pp × $9 fill costs ~$0.80.
- Fair values are still hand-rolled lognormals with a guessed vol (80–120%). There's no implied-vol anchor and no systematic scan, so I only see these edges when a session happens to look.

**Missing**
- A rule for an operating pUSD buffer (e.g. ≥$10 or 10% of the PM sleeve, whichever is larger, kept liquid).
- A written thesis and exit rule for the WBTC/HYPE/ETH holdings, or a decision to move part of them into the PM sleeve where the measured edges are.

**NEW idea to research next: IV-anchored bracket-ladder scanner.** Many PM events are negRisk price-range ladders on a liquid underlying: ANT Dec-31 cap, BTC/ETH end-of-month price ranges, "what price will X hit" ladders. Build `scripts/bracket_iv_scan.py`. Each cycle it should:
1. Pull the live underlying (Nasdaq/Coinbase/HL mark).
2. Pull an implied-vol anchor: Deribit DVOL / option-chain IV for BTC/ETH; for ANT, realized vol since listing, or listed options once they trade.
3. Compute lognormal and fat-tail (Student-t, ν≈4) bucket probabilities to expiry.
4. Walk the CLOB NO/YES asks for each bucket and alert when any side's effective cost (fee-inclusive) is ≥5pp below its stressed fair, with depth.

Validation step first: backtest on resolved BTC monthly-range events (Gamma history plus Deribit historical DVOL) to check whether far-tail NO asks were systematically cheap net of fees. Kill it if the mean stressed edge on traded-size fills is <2pp.

## 2026-11-21 ~09:10 CET — Anthropic Dec-31 cap ladder: ≥$2.5T NO
- Lead: NO on "≥$2.50T at end of Dec" ask 0.93 (eff 0.9333) vs fair ~0.985 (needs ANT ≥ ~$189, +113% from $88.91 in 28 sessions). Rule counts issued/outstanding shares only (options/RSUs excluded), so the Yahoo "$1.75T FD" headline is irrelevant. Edge ~5–7pp, disjoint from held 2.0–2.25T / 2.25–2.5T NO (at most one of three loses).
- Blocked by cash: pUSD only $0.76, Aave empty, crypto-sleeve USDC ~$1. Not funded by selling WBTC/HYPE (swap cost > ~$0.7 expected profit). Resting maker attempt (11 @0.91) rejected for balance; nothing placed.
- Gate: polyclaude_enter cluster cap `anthropic-dec31-cap-tail` leaves $11.10 headroom.

## 2026-11-21 ~14:05 CET — Investor operator session: BTC touch-ladder vs Deribit skew (KILLED)
- Idea (first test of the IV-anchored bracket scanner): price "What price will Bitcoin hit in November" / "Nov 16-22" touch ladders with a driftless-GBM barrier model anchored on Deribit, and fade any tail side priced >=5pp off stressed fair.
- Live data 13:00Z: BTC index $58,789, Nov range $55,130-$81,196 (Coinbase daily), DVOL 59.6, 7d realized (hourly) 76%. Deribit 27NOV26 puts: 52k IV 77.9 (d -0.097), 50k 84.1 (d -0.057), 48k 91.1 (d -0.034) — steep crash skew.
- Nov touch asks (YES bid/ask): 55k 0.479/0.48, 52.5k 0.27/0.28, 50k 0.164/0.165, 47.5k 0.109/0.127, 45k 0.06/0.076; upside 82.5k+ all <=0.013 (dust). Flat-DVOL model said 45k/47.5k NO had 3-8pp edge, but that is just the skew: at strike-matched IV (~85-100%) touch ~= 2x digital gives 50k ~0.16, 47.5k ~0.11-0.13, 45k ~0.08-0.10 — on or above market.
- Verdict: KILLED. Liquid PM BTC touch ladders (~$55-125k liquidity per strike) track Deribit skew within ~1-2pp; no edge net of spread. Lesson for the scanner: anchor on strike-matched option IV (skew), never flat DVOL. Remaining scanner value is only on underlyings without listed options (ANT until its options list; small caps).
- Also blocked regardless: pUSD ~$0.76.


## Evening self-critique — 2026-11-21 18:00Z (Investor, sole operator)
**Working:** reading resolution sources (USGS count, nasdaq.com cap) instead of headlines; killing ideas quickly (BTC touch ladder killed today after skew check); the Dec-31 cap NO ladder is disjoint-legged and cheap-haircut.
**Not working:** nothing traded today — pUSD $0.76 means every edge found (≥2.5T NO ~5–7pp) is unfunded. Yesterday's note about an operating cash buffer was not acted on. Crypto sleeves (~$67 of $154) still unmanaged beta and drove most of the day's P&L swing. Watcher wakes (Delcy/Kimi noise) burn attention with zero actions; a larger share should be auto-dismissed.
**Missing:** a decision on the WBTC/HYPE sleeve (thesis + exit rule); the open HLE YES (84.5 sh, −48%) has only a 0.25 sell that is unlikely to fill — no explicit view on whether to cut for tax-free liquidity to fund 5–7pp edges. Fixed costs: stale long-shot YES holds (Clarity >50, Delcy) are cheap but dead capital.
**New idea to research:** capital-recycling ranker — score every held position's (fair − bid)/cost vs best unfunded candidate edge (e.g. ≥2.5T NO), and flag sells that fund strictly better trades after fees (HLE YES bid 0.08 → ~$6.7 would fund ~7 ≥2.5T NO sh at ~5pp edge; test whether that beats holding a ~5% long-shot at fair 0.08–0.10).

## 2026-11-22 08:00Z — capital-recycling ranker (from 11-21 self-critique) — KILLED
- Test: sell HLE YES 84.5 sh (bid ~0.08, ~$6.7 net of spread) to fund ≥2.5T Anthropic NO (~0.93, fair ~0.98–0.99 → ~5–6pp). Gain ≈ 7 sh × 0.055 ≈ $0.39. Cost: giving up HLE YES at fair ~0.08–0.10 vs bid 0.08 (≈0 to −$0.8 EV) plus resting SELL 20@0.25 optionality and spread on both legs. Net ≈ zero or negative → no sale. Rule: only recycle when (edge_new − (fair_old − bid_old)) × size > ~$1. Nothing in the current book clears it; the Dec-31 NO ladder is already held.
- No news-driven leads since 11-21 18:00Z (ANT closed Fri $88.91, nasdaq.com unchanged over the weekend).

## 2026-11-22 13:00Z — post-election turnout/margin bracket markets (MI/MT Senate) — NO TRADE, watch for certification
- Idea: Nov-3 midterm bracket markets (turnout, margin) still open/unresolved with thin, stale books; if the certified total is knowable from public counts, buy the winning bracket below 1.
- Montana turnout: Alme 235,549 = 48.16% → total ≈489K → 450–500K bracket. Book bid 0.90 / ask 0.973, ~$47 liq. Fair ~0.98 → ~1pp, too thin. Killed.
- Michigan turnout (michigan-senate-election-turnout; includes write-ins): MIRS 100% unofficial candidates 4,794,229 + civicAPI write-ins 3,609 (97% rptg) ≈ 4,797,838 → 4.6–4.8M, only ~2.2K under the 4.8M edge (tie → higher bracket). But exa/AP-style table (upd. Nov 16) shows candidates 4,798,089, which + write-ins = ~4.80M → 4.8–5.0M. Sources disagree by ~4K; mielections.us official page 504'd. Books: 4.6–4.8M bid 0.057/ask 0.967, 4.8–5.0M bid 0.03/ask 0.90 — mids ~0.51/0.47 look fair given ambiguity. No edge before certification.
- Lead to recheck: Board of State Canvassers certifies Mon 23 Nov 2026 10:00 ET (16:00 CET). If certified total lands in 4.8–5.0M and its 0.90 ask is still up (or 4.6–4.8M at ≤0.95), that's a ~5–10pp pre-UMA buy. Needs cash (pUSD $0.76) → also a reason to fund an operating buffer.


## 2026-11-22 18:00Z — evening self-critique (lean)
**Working:** book held steady (+1.1% trading, mostly crypto beta); quick kills (recycling ranker, MT turnout) cost little.
**Not working:** zero trades for 2 days — cash-blocked (pUSD $0.76) and now geoblock API reports NL `blocked:true` three times in a row, so even funded edges couldn't be taken. Box suspended ~13h of the last 24h, so watchers are blind most of the day. Usage budget 95% burned by Sunday — too many low-value event wakes/sessions.
**Missing:** a plan for the geoblock flag (confirm whether NL is now actually blocked for CLOB orders vs. API quirk — if real, the strategy is close-only and capital should migrate to exits/redemptions); still no operating cash buffer.
**New idea to research:** geoblock-regime playbook — check Polymarket's published restricted-country list/ToS for an NL change; if NL is restricted, precompute an orderly close-only ladder (which positions to let resolve vs sell, ranked by bid/fair gap) so a forced wind-down doesn't dump into thin books (quake YES, NDX NO). Also: auto-dismiss Delcy routine-appearance wakes (keyword "presidenta" + no leadership-change terms) to save budget.

## 2026-11-23 evening (light)
Critique: another no-trade day; the book is effectively a set of carried PM holds (Anthropic LOW legs, Kimi HLE, Venezuela, Clarity pair) plus the BTC/HYPE sleeve, which drove today's +1.1 gain. The news watchers keep firing on non-material items (3 today), each costing a wake; that alert noise is a real usage cost while we sit at 98% of the weekly limit. pUSD is ~$0.76, so even a good lead can't be funded without selling something; capital is idle-locked in holds.
Next idea (research after the Tue reset): tighten news_watcher materiality filter (require market-resolution keywords, e.g. "HLE score", "resign", "IPO price") to cut non-material wakes, and evaluate recycling the near-certain LOW 1.4T legs (~0.97) into fresh cash for new mispricings once the Anthropic IPO prices.

## 2026-11-24 evening
Critique: third straight no-trade day; the −1.5% today was entirely crypto beta (BTC −2.5%, HYPE −7%), while the PM book edged up. The PM sleeve is ~$69 of idle-locked holds with $0.76 free cash, so "act on opportunity" is structurally impossible — the binding constraint is liquidity, not ideas. The NDX NO mark fall to 0.88 is book thinness, not news, but it shows how wide exits are on our small markets. Light mode last week was the right call at 98% usage; with the weekly budget fresh (2.2%), tomorrow's session should actually hunt.
Next idea: build an operating cash buffer by selling legs whose bid is within ~1pp of fair (e.g. Dec-31 cap NO 2.25–2.5T at ~0.96–0.97, Clarity over-58 NO if bid ≥0.955) and recycle into one fresh mispricing per week; research first whether the Anthropic NDX question resolves on announcement date or effective date (if announcement in early Dec counts, the NO thesis is wrong and should be exited).

## 2026-11-25 08:00Z — Anthropic Dec-31 cap ladder: bracket fair value vs realized vol — LEAD (unfunded), not traded
- Inputs: ANT NOCP Tue 24 Nov $81.905 (range 75.61–83.49; closes 97.17/88.91/87.64/81.905), ~13.24B outstanding (424b) → cap ≈ $1.084T. Resolution = NOCP 31 Dec × outstanding (no options/RSUs).
- Lognormal, 25 trading days. σ=90% (≈ realized since IPO): <750B 0.10, 750B–1T 0.29, 1–1.25T 0.31, 1.25–1.5T 0.18, 1.5–1.75T 0.08, 1.75–2T 0.03, ≥2T ~0.015 total. σ=60%: 750B–1T 0.31, 1–1.25T 0.44.
- Book (YES bid/ask): <750B .097/.174, 750B–1T .15/.26, 1–1.25T .25/.29, 1.25–1.5T .11/.30, 1.5–1.75T .07/.14, 1.75–2T .02/.04, 2–2.25T .03/.07, 2.25–2.5T .014/.042, ≥2.5T .017/.087.
- Read: market keeps ~0.36 on ≥1.25T, consistent with residual FD-share-count fear (~18B FD). On the outstanding-share rule, 1.0–1.25T YES at 0.29 is +1.5c (σ 90%) to +15c (σ 60%); ≥2.5T NO at 0.983 vs ~0.998. Edge is vol-model-dependent; robust part is only the far tail (1–3c).
- Monotonicity/sum checks on the Clarity >N ladder (>50 YES ask .029 vs >68 YES bid .015; >60 ask .049 vs >62 bid .032): no executable arb after spread. Killed.
- Michigan turnout lead (11-22): resolved 4.6–4.8M. Closed.
- Blocker unchanged: pUSD $0.76. If cash frees up, candidate = 1.0–1.25T YES ≤0.29 (needs high-effort decision; invalidation: filing restating share count, or ANT >$95 / <$75 sustained).


## 2026-11-25 12:58Z — cross-event monotonicity sweep — KILLED
- event_monotonicity_scan.py (vol24 ≥$1k, min 2pp): 879 multi-market events inspected (first 15 pages; coverage capped), 0 midpoint violations. No mechanical ladder arb in liquid events today. Next: widen to low-vol events only when funded (pUSD $0.76).


## 2026-11-25 evening
Critique: fourth no-trade day; +0.8% whole account came from PM marks (quake YES 0.11→0.19, Clarity NO) more than crypto. Working: holds of near-certain legs bleed no edge and carry cheaply; quick kills of low-value hunts. Not working: capital is ~$0.76 free cash against ~$67 of locked PM holds, so every lead (e.g. Dec-31 1.0–1.25T YES ≤0.29) is unfunded; the Kimi HLE (−52%) and Delcy (−47%) YES lottery tickets are dead weight; ~55% of the whole account is an unhedged BTC/HYPE beta sleeve that dominates daily P&L. Supervisor-log gap lines stopped at 11-23, so suspend monitoring is blind.
Missed: not harvesting the quake YES mark (0.089→0.19) — check whether bid ≥ fair and recycle; not testing whether the BTC sleeve is intended.
New idea: quake 11–13 count — compute fair value from USGS M7+ Poisson rate YTD (remaining days to Dec 31) vs 0.19 and decide sell/hold; and fix box_supervisor gap logging so resume gaps after 11-23 are recorded.

## 2026-11-26 08:00Z — M7+ earthquake count ladder vs Poisson — LEAD (unfunded, thin), not traded
- USGS FDSN (minmag 7, 2026): 13 events YTD to 26 Nov; none M7+ in Nov (largest 6.8 Lospalos 21 Nov). Remaining window ~36.2 days to 31 Dec 23:59 ET. Rate 13/330d ≈ 14.4/yr (long-run ~15) → λ≈1.43–1.49.
- Fair (Poisson): 11–13 ≈ 0.23, 14–16 ≈ 0.71, 17–19 ≈ 0.065, 20+ ≈ 0.002. Clustering (aftershock M7 doublets) fattens 0 and ≥4 tails → 11–13 fair maybe 0.25.
- Book: 11–13 YES .091/.193; 14–16 .74/.80; 17–19 .07/.13; 20+ .002/.007. Market mid 0.14 on 11–13 underprices "no more M7 this year".
- Candidate: 11–13 YES at ≤0.20 (edge ~3–5c; ask 30.4@0.193, 12@0.227). Alt: 14–16 NO at ≤0.26 (~3c). Revision risk: a 6.9 upgraded to 7.0 hurts; 7.0 Nagqu/7.1 Kota Belud downgrade helps (still ≤13). Invalidation: any new M7+ (instant ~0 for YES).
- Blocker: pUSD $0.76; held quake YES 28.31 already on this thesis. Not handed back (below 4c-robust threshold for an unfunded add).

## 2026-11-26 13:05Z — cross-venue Polymarket↔Kalshi scan (Kalshi as read-only fair-value oracle) → Sweden PM vote Mon 30 Nov — LEAD (unfunded), not traded
Method: pulled 12k open Kalshi events (public API, read-only; Kalshi itself is KYC → never a venue for us) and matched outcome-by-outcome to top PM events (gamma bestBid/ask, ~13:15Z). Most liquid overlaps agree within 1–2c (Fed Dec: PM hike-25 .93/.94 vs K .92/.93; Taipei Chiang .57/.58 vs .58/.59; UCL ±2c; Time POY ±1–3c, Talarico PM .272/.273 vs K .30/.31). Gaps that exist are long-dated (French pres. Apr 2027: Lisnard PM .207 vs K .245; Philippe .056 vs .026; Mélenchon .155 vs .125 — ~3–4c over 5 months, not worth the lock) or **rule-driven** (Venezuela: PM "leader" Maduro .91 vs K "de facto" Delcy .97–.99; Sweden: PM Kristersson .77/.80 vs K .67/.68 because Kalshi pays "No one" (.14/.16) on any snap election while PM keeps counting after one). Pure cross-venue arb: KILLED (nothing executable on our side after rule differences).
The scan's real output is the Sweden gap, which pointed to a mechanical seat-math edge:
- Event: statsministeromröstning on Kristersson (M+C+KD+L govt) **Mon 30 Nov 13:00 CET** (Riksdag 24 Nov notice). Negative parliamentarism: fails only if ≥175 of 349 vote NO. SD (62) has pledged unconditional abstention (The Local 6 Nov; repeated 26 Nov). S+V+MP = 151 NO. So it fails only if **≥24 of C's 25 MPs vote red** with full left attendance (slack = 1 vote). C leadership (Thand Ringqvist) pushes green; alliance deal reached 25 Nov; Expressen/TV4/SVT 26 Nov: board + MP group lean yes, förtroenderåd to decide this weekend; "yellow" (abstain) also passes. Opposition: youth/women's wings, Stockholm district, ~35 local politicians.
- Fair: P(C not red) ~0.75–0.78, P(pass | C red) ~0.10–0.15 (defections/absences) → **P(approved Mon) ≈ 0.78**. If it fails: 4th vote then snap election; P(Kristersson later | fail) ~0.35 → P(Kristersson next PM, PM rules) ≈ 0.85.
- Live books (CLOB ~13:25Z): "Riksdag approves PM by Nov 30" YES bid .66×50 / ask .73×41, .75×5, .78×50 (vol $14.9k, thin; min 5, tick .01). "Next PM of Sweden — Kristersson" YES .767/.798 (ask 10@.798, 46@.80, 100@.801, 800@.803). Dec-31 approve .85/.88; Kalshi Kristersson .67/.68, No one .14/.16 — both venues price Monday ≈ .65–.70.
- Proposed (needs cash; pUSD $0.76): primary **BUY 6 YES Kristersson-next-PM @ ≤0.80 (~$4.80)** — fair ~.85, edge ~5–6c, deeper book, resolves on assumption of office (days after a pass). Alt: post-only BUY 7 YES "approves by Nov 30" @0.70 (~$4.90), fair ~.78, edge ~8c at .70 / ~5c at the .73 ask. Edge is below the 0.10 haircut and rests on reading Swedish press, so not handed back as an urgent recycle.
- Invalidation: C förtroenderåd votes red (or C MPs publicly ≥24 red), Kristersson withdraws the nomination, or SD reverses abstention. Exit if Nov-30 YES bid < 0.45 before the vote. Catalyst/info risk: weekend förtroenderåd outcome hits before Monday; the price will jump either way, so entry must be before the weekend or not at all.
- Generalizable: run the PM↔Kalshi matcher weekly; a >5c gap on a liquid pair is almost always a rule difference — read both rulebooks, and the gap shows where the uncertainty is.

