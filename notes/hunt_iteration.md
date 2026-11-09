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
