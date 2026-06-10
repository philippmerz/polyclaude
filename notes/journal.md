# Polyclaude Journal

> Append-only log. Most recent at bottom. Each entry: time (UTC), what happened, why, what's next.
> Older entries (kickoff through 2026-05-19) live in git history; this file keeps ~the last 2 weeks.

---

<!-- older entries dropped 2026-06-04 to reduce context cost; full history in git -->

## 2026-05-20 ~02:00 UTC — Wednesday 02:00 cron tick (quiet, May-31 +1pp favorable)

**Material:**
- May-31 NO +1pp favorable (0.895→0.905), MTM $15.61→$15.78, +33.48% on cost, 10.9d to resolution.
- Regime-fall NO -1pp adverse to 0.815. Aliens -1pp adverse to 0.855.
- Total MTM $83.95→$83.73 = -$0.22 within noise.
- 1 news_alert overnight (Trump-turns-to-allies, MATERIAL favorable). No CRITICAL alerts (logging confirmed via grep — no new CRITICAL re-val events).

**Considered + skipped:** Iranian-regime-falls-by-May-31 NO surfaced from discover_markets at $0.987 mark, 47.8% APY, 10.9d. Bond-like-fade lens looks attractive but FAILS post-R-U 10pp edge filter (edge=1.3pp) + already cluster-capped on iran-regime (regime-fall-2027 + Pahlavi = $38.25 cluster cost). Disciplined skip.

**Cron outcomes:** UMA clean, Ostium unchanged, no watchlist hits, no redeems, macro Fed-June markets efficient (99% no-change). Kelly+BB output consistent with yesterday's framework note — Kelly flags May-31/Aliens "trim" but Brownian-bridge holds (May-31 fair_BB 0.962 vs mark 0.905 = SCALE_UP per time-decay; Aliens fair 0.86 vs mark 0.855 = HOLD).

**Net:** no actions. Position approaching resolution as planned.

## 2026-05-20 ~14:00 UTC — Wednesday 14:00 cron tick (quiet)

**Material:** essentially none. MTM $83.73→$84.07 = +$0.34 over 12h. May-31 NO unchanged at 0.905. Regime-fall +1pp recovery to 0.825. Hantavirus +0.4pp to 0.943. Pahlavi -0.4pp to 0.929.

**Cron outcomes:** Zero news_alerts in 12h. Zero CRITICAL re-vals. UMA clean. Ostium unchanged. No watchlist hits. No redeems. discover_markets: 0 hurdle-clearers (filter narrowed since Iranian-regime-may31 closed/de-prioritized). Sports: only non-consensus or spread markets surfacing. No actions.

10.4 days to May-31 resolution.

## 2026-05-21 ~02:00 UTC — May-31 NO 0.83 trigger HIT, catalyst_check, HOLD decision

**Trigger event:** May-31 NO mark dropped 0.905 → 0.805 (-10pp adverse) overnight. Crossed the 0.83 early-close trigger threshold (per backlog 2026-05-15 protocol).

**Protocol followed:**
1. Fresh catalyst_check spawned (commit pending — output /tmp/cc_may31_v2.txt)
2. Verdict: central P(YES) = 10% (range 5-18%), **DOWN from 13% on 2026-05-19**
3. Key drivers: Khamenei rejected Trump nuclear proposal May 16 ('excessive and outrageous'); Rome talks broke down; Israel reported preparing strike; uranium enrichment + sanctions deadlocked
4. Multiplicative: P(breakthrough)=18% × P(formal signature|agreed)=65% × P(permanent language|signed)=85% = 10%

**Analysis:**
- Catalyst_check fundamentals IMPROVED for NO (10% vs prior 13%) while market price WORSENED (mark 0.805 vs prior 0.905). Pure divergence.
- Mark of 0.805 implies P(YES)=19.5%; catalyst_check central=10%. **9.5pp edge on NO.**
- Brownian-bridge with updated P_NO=0.90, t/T=0.65: fair_BB = 0.964 vs mark 0.805 = -15.9pp SCALE_UP.
- UMA-resolution-criteria risk: ZERO (criteria explicit "permanent only; temporary will not qualify"; no ambiguity).

**Decision: HOLD.**
- DON'T close: trigger condition is mark-based, but underlying protocol requires "mark + UMA-resolution-criteria risk materially raises P(YES)" — UMA-risk is zero, mark drop is noise/speculation against fundamentals.
- DON'T scale: edge 9.5pp just below 10pp post-R-U filter; cluster cap on iran-peace cluster already binding ($50+ exposure on $170 bankroll).

**Updated:** prior P_NO 0.87 → 0.90 in portfolio_kelly_priors.json (matches catalyst_check central). Both portfolio_kelly + brownian_bridge_fv now use updated prior via the slug-prefix-match fix shipped 2026-05-19.

**Position state:** cost $11.82, mark $0.805, MTM $14.04, +18.73% on cost (was +33.48% yesterday).

**Cron tick 20260521T020002Z completed.** Remaining steps after trigger-hit handling: 0 redeems, 0 discover candidates, macro Fed-June markets all 99%+ efficient. Telegram alert (msg 315) substituted for routine tick-summary per action-only filter — the trigger event is the substantive message; a separate 'MTM +X' tick-summary would be noise.

## 2026-05-21 ~02:15 UTC — Eighth meta-reflection cycle

**One pattern observation worth flagging to backlog.**

**Pattern: catalyst_check is the stable fundamental anchor when mark volatility spikes.** Today was the SECOND time in 4 days catalyst_check decided a May-31 NO trigger event (2026-05-19 mark 0.855 → P(YES)=13%; 2026-05-21 mark 0.805 → P(YES)=10%). Both times the fundamental verdict was stable while the market mark bounced 0.805-0.925. Insight: for positions with sustained mark volatility, catalyst_check provides the anchor; mark noise alone shouldn't trigger action.

Could codify into cron step 2 (news-alert processing): on held position with mark move >5pp since last cron tick AND <30 days to resolution → auto-spawn catalyst_check. Rate-limit 24h per position to bound haiku cost. Bounded ~30 LOC. Saves manual protocol-follow each time + ensures protocol fires consistently. Adding to backlog as moderate-priority.

**Other items:** Doc/staleness scan returned clean (just updated portfolio_kelly_priors.json _updated to 2026-05-21; strategy/00 + README current). Macro_pm_scan v1 still --no-consensus default — accurate status. No new findings on scripts/notes/strategy.

Brief idle after this.

## 2026-05-21 ~14:00 UTC — Wednesday 14:00 cron tick (recovery + body-fetch validated + log-redirect fix)

**Material:**

- **May-31 NO recovered** 0.805 → 0.820 (+1.5pp favorable since 02:00 trigger hit). MTM $14.04 → $14.30 = +$0.26. Still +20.94% on cost. Operator dialogue concluded with fresh Opus-level research (msgs 321 + supporting refs) confirming P(YES)=10% central, holding thesis intact, no factual basis for market 19.5% YES pricing.

- **Body-fetch CRITICAL re-validation WORKS in production**: BBC Iran-Hormuz article ("Iran steps up claim to control Strait of Hormuz") was first-pass tagged CRITICAL on iran-peace; body-fetch (3692 chars) succeeded and second-pass DOWNGRADED to MATERIAL. The shipped logic (commit 9223226 + logging commit c97a467) catches chain-inference CRITICAL alerts at the second-pass stage. First production validation of the body-fetch path.

- **Bug found + fixed: daemon log redirect**. The body-fetch re-val log line WAS firing but going to a stale `/tmp/claude-*/tasks/*.output` file from the bash background task that originally invoked `news_watcher.py start` two days earlier. The script defined LOG_PATH but never used it — `cmd_start` relied on caller's shell redirect. Fixed: explicit `os.dup2()` in cmd_start to point stdout/stderr at LOG_PATH (logs/news_watcher.log). Bounded ~10 LOC. Future audits will find re-val outcomes in the canonical log. Daemon restarted PID 773362; new fd 1 → logs/news_watcher.log confirmed.

**Cron outcomes:**
- UMA: 1 PRICE_MOVE alert (May-31 YES 0.095 → 0.180, +8.5pp; reflects overnight drop, already handled)
- Ostium: unchanged. Watchlist: 0 hits. Redeems: 0.
- discover_markets: only May-31 NO (held) + Norway WC 2026 NO at 97.5% (15% APY, too thin)
- Sports/macro: no candidates pass filter.

**Kelly with updated P_NO=0.90:** May-31 edge 8.0pp = scale-in candidate but 8pp < 10pp post-R-U filter + cluster cap blocks. Iran-regime-fall 10.5pp edge but also cluster-capped. Aliens -0.5pp (trim candidate per Kelly) but Brownian-bridge HOLD per yesterday's framework doc.

**Net MTM:** $81.64 → $82.60 = +$0.96 over 12h. No actions.

## 2026-05-21 ~16:14 UTC — Off-schedule tick (Tier-1 false-positive autofire)

**Trigger:** news_watcher fired Tier-1 on CoinTelegraph BTC-price article ("Bitcoin due '5%+' move...") because keyword "us-iran peace deal" matched in the body summary. Article had ZERO actual US-Iran peace deal content — just mentioned the geopolitical context in passing while discussing BTC price drivers.

**Fix:** removed "us-iran peace deal" from tier1_keywords. The keyword was too generic — matches ANY mention rather than state-change events. Config already had the qualified variants ("us iran peace deal signed", "iran peace agreement signed", "permanent ceasefire iran") which are actual book-resolving signals. The unqualified version was redundant + false-positive prone. Bounded 1-line config change. Daemon re-reads config on every poll cycle, so no restart needed.

**Position state (off-schedule):** May-31 NO mark dropped further 0.820 → 0.775 (-4.5pp adverse since 14:00). MTM $14.30 → $13.52 = -$0.78. Total MTM $82.60 → $81.81 = -$0.79 over ~2h. Still +14.30% on cost; mark now 5.5pp below 0.83 trigger. NO action — research confirmed P(YES)=10% this morning, holding per discipline. Operator already has full picture from morning dialogue.

**Cron outcomes:** UMA clean, no watchlist hits, no redeems. Continued downward drift on May-31 mark but no NEW fundamental info; consistent with speculation/profit-taking pattern.

## 2026-05-22 ~02:00 UTC — Thursday 02:00 cron tick (May-31 recovery continues)

**Material:**
- May-31 NO recovered 0.775 → 0.815 (+4pp favorable since 16:14 false-trigger tick). MTM $13.52 → $14.21 = +$0.69. Now 1.5pp below 0.83 trigger (was 5.5pp below). Trend reversing.
- Regime-fall +1pp recovery to 0.835.
- Total MTM $81.81 → $82.86 = +$1.05 over ~10h.

**Body-fetch CRITICAL re-val fires correctly (now visible in logs):** Guardian article "Oil markets nearing red zone" — first-pass CRITICAL on us-iran-peace, body-fetch 4000 chars, second-pass DOWNGRADED to MATERIAL. Log line in logs/news_watcher.log (post-fix from yesterday 14:00 commit 6649a62). Re-val infrastructure working as designed: chain-inference CRITICALs get caught.

**Kelly with current marks:** May-31 edge dropped 12.5pp → 8.5pp as mark recovered, now back below 10pp filter. Iran-regime-fall edge 9.5pp (just below filter). Aliens -0.5pp trim per Kelly, but Brownian-bridge HOLD per yesterday's framework doc.

**Cron outcomes:** UMA clean, Ostium unchanged, 0 watchlist hits, 0 redeems, discover surfacing only held positions, macro Fed-June markets all efficient. No actions.

## 2026-05-22 ~14:00 UTC — Thursday 14:00 cron tick (SECOND material adverse move on May-31)

**Material adverse:** May-31 NO mark dropped 0.815 → 0.735 (-8pp). MTM $14.21 → $12.82 = -$1.39 unrealized. Now +8.40% on cost (was +33% peak). Market YES at 29.5% — beyond yesterday's catalyst_check upper bound (18%).

**Fresh Opus research (2nd round, complementing yesterday's):**
- NEW: Trump quote "most points agreed except nuclear" (the only point that mattered) — Iran "unyielding"
- NEW: Iran FM "agreement just inches away" but criticized "maximalist demands" from US
- NEW: Rubio May 22 hardline on Hormuz tolls "not acceptable"
- NEW: Iran reviewing latest US proposal (May 21); Trump willing to wait "a few days"
- UNCHANGED: Khamenei May 16 rejection still standing on nuclear
- UNCHANGED: Wikipedia ceasefire article confirms no permanent agreement, original framework was 15-20d temporary negotiations
- KEY: any MOU signed in 9d will structurally include 30-day-further-negotiation window — that's TEMPORARY per resolution criteria ("explicitly temporary will not qualify")

**Updated prior P_NO 0.90 → 0.85** (P(YES) 10% → 15% central, range 10-25%). Slight upward revision driven by Trump's "most agreed" rhetoric + Iran FM "inches away," but core nuclear sticking point unresolved.

**Market reading 29.5% YES**: I see no factual basis. Likely market is (a) discounting the strict "permanent" criterion, (b) reading Trump's pressure tactics as deal-imminent, (c) speculative.

**EV math at P(NO)=0.85:**
- Hold to resolution: 0.85 × $17.44 + 0.15 × $0 = $14.82 expected
- Close now: $12.82 realized
- Hold advantage: +$2.00 EV

**Decision: HOLD per analysis** but ESCALATE to operator (this is the second material adverse move; operator override appropriate). Sending Telegram update — concise vs morning's full dialogue.

**Cron outcomes:** UMA 1 PRICE_MOVE alert (May-31 YES 0.185 → 0.295, +11pp — captured the move). Ostium unchanged. 0 watchlist hits. 0 redeems. Total MTM $82.86 → $82.09 = -$0.77 (May-31 alone -$1.39, other positions +$0.62 in offsetting moves: Pahlavi +2.6pp, Regime-fall +1pp).

## 2026-05-22 ~14:40 UTC — Term-structure framework lesson + prior update

Operator surfaced new Iran-peace sub-markets (May 22 = 5%, May 26 = 18%). Fetched full event term structure (14 sub-markets). Key insight:

**Dec 31 sub-market priced 73% YES.** A strict reading of "permanent" criterion would put Dec 31 P(YES) at 30-40% max; the 73% pricing implies market expects UMA-LOOSE interpretation (framework MOUs with further-negotiation windows count as "permanent"). This is the same UMA-interpretation risk that bit R-U 2026-05-11 (-$16.73 realized).

**Framework lesson shipped to strategy/00_philosophy.md** (alongside yesterday's Kelly-vs-Brownian-bridge framework note):
- Section: "Term-structure-as-UMA-interpretation-signal"
- Rule: when longest-dated sub-market > 60-70% YES on a "by date X" event, weight prior 70% strict / 30% loose
- Example: May-31 NO prior shifted from P_NO=0.85 (strict) → P_NO=0.81 (UMA-adjusted)
- EV impact: hold advantage shrunk +$2.00 → +$1.31 but still positive

**Decision unchanged:** HOLD May-31 NO. New sub-markets (May-22, May-26) fail 10pp post-R-U filter after UMA adjustment.

Compounds: future multi-date events get correct prior calibration without re-deriving. Operator-flagged signal (term structure) made into reusable framework rule.

## 2026-05-23 ~02:00 UTC — Friday 02:00 cron tick (May-31 reversion confirmed)

**Material:** May-31 NO recovered 0.735 → 0.865 since yesterday's 14:00 worst-case (+13pp favorable). MTM $12.82 → $15.09 = +$2.27 unrealized. Now +27.58% on cost; back above 0.83 trigger by 3.5pp. Yesterday's HOLD decision validated — adverse pricing was speculation/short-term flow as analysis indicated.

**Kelly vs BB framework holding:** With UMA-adjusted P_NO=0.81:
- Kelly static edge: -4.5pp (mark 0.855 vs P_NO 0.81) → "trim candidate" per static frame
- Brownian-bridge time-decay: fair_BB(0.81, t/T=0.60) = 0.92 vs mark 0.855 = -6.5pp SCALE_UP

Yesterday's framework note (commit ecf554c) explicitly says: for late-stage bond-like NO, use BB not Kelly for hold/trim signals. Position has 8d to resolution; mark should continue migrating toward 1.0 absent deal signing. **Hold.**

**Cron outcomes:** UMA 1 PRICE_MOVE alert (capturing favorable reversion); Ostium unchanged; 0 watchlist hits; 0 redeems. discover_markets only surfaces held May-31. 2 body-fetch CRITICAL re-vals overnight (Guardian + CBS articles, both downgraded or CRITICAL-confirmed as appropriate).

**Net MTM:** $82.09 → $83.86 = +$1.77 over ~12h. No actions.

## 2026-05-23 ~14:00 UTC — Saturday 14:00 cron tick (May-31 pullback again)

**Material:** May-31 NO mark pulled back 0.865 → 0.815 (-5pp adverse since 02:00). MTM $15.09 → $14.21 = -$0.88. Still +20.19% on cost. Mark just below 0.83 trigger by 1.5pp. Pattern: now established mark volatility 0.735-0.925 over 5 days; bouncing in this range.

- Iran-regime-fall -2pp adverse to 0.815. Pahlavi -1.5pp. Hantavirus +0.4pp recovery.
- Total MTM $83.86 → $82.15 = -$1.71 over 12h.
- 0 news_alerts in 12h (very quiet news flow).

**Kelly + BB framework:** Kelly edge -0.49pp = static near-neutral. BB at P_NO=0.81, t/T=0.65 = 0.93 fair vs mark 0.815 = -11.5pp = SCALE_UP. Per framework note: BB is the right frame for late-stage holds, ignore Kelly's near-neutral signal. **Hold.**

**Last catalyst_check** was 2026-05-21 02:21 at mark 0.805 (gave P_YES=10%). Today mark 0.815 = within 1pp of last check basis — NO re-run warranted per "mark move >5pp" threshold.

**Cron outcomes:** UMA clean, Ostium unchanged, 0 watchlist hits, 0 redeems. discover only surfaces May-31 (held). Macro Fed-June 50bps cut YES 0.0045 = trivial. No actions.

7.4d to resolution.

## 2026-05-24 ~01:50 UTC — Saturday late night — CATASTROPHIC ADVERSE EVENT on May-31 NO

**Event:** Trump announced (Sat May 23) deal "largely negotiated" with Iran. Multiple major sources confirmed (NPR, Fox, NBC, Al Jazeera, Times of Israel, NBC). Qatar mediators in Tehran. Trump said "final aspects being discussed, will be announced shortly."

**Market reaction:** May-31 NO mark dropped 0.815 → 0.345 (-47pp catastrophic). MTM $14.21 → $6.01 = **-$8.20 unrealized**. Position now -49.13% on cost. Term structure shifted ALL durations: May 26=57.5% YES, May 31=65.5% YES, Dec 31=88% YES. Volume 6M on May-31 sub-market today.

**Fresh research:**
- Deal STRUCTURE per news: MOU ending war + **30-day nuclear negotiation window** = structurally TEMPORARY per resolution criteria
- catalyst_check verdict: P(YES strict) = 11% (range 4-22%). Multiplicative: P(announcement by May 31) = 65% × P(announcement qualifies as permanent|announced) = 17% = 11%
- Opus WebSearch confirms: deal includes "two-month negotiations on Iran's nuclear program" — temporary structure
- R-U PATTERN RISK explicit: same UMA-loose interpretation that lost -$16.73 on R-U could play out here

**Updated P_NO via UMA-risk weighting:**
- 70% strict × 0.89 + 30% loose × 0.35 = **P_NO = 0.73**

**EV math at P_NO=0.73:**
- Hold to resolution: 0.73 × $17.44 + 0.27 × $0 = $12.73
- Close now: $6.01 realized
- **Hold advantage: +$6.72 EV**

**Robustness:**
- At market view P_NO=0.345: hold EV $6.02 ≈ close
- At my UMA-adjusted P_NO=0.73: hold +$6.72
- At 50/50 weighting P_NO=0.62: hold +$4.81
- Hold is EV+ across all reasonable P_NO scenarios (>0.345)

**Decision: HOLD per EV math and strict-reading favor.** Operator escalation sent (msg 331). Default = hold, operator override welcome.

**Prior updated** 0.81 → 0.73 in portfolio_kelly_priors.json. Catalyst_log.md updated.

**Reflection:** This is the exact R-U pattern — UMA-loose interpretation risk against me. My strict-reading analysis says hold; market signal says I'm wrong about UMA. The decision turns on whether UMA will rule MOU-with-30-day-window as "permanent" (loose) or "temporary" (strict). Polymarket criteria language favors strict but UMA voters can rule either way.

**Total MTM:** $82.15 → $76.27 = -$5.88 over 12h. May-31 dominant driver.

**Cron tick 20260524T020001Z** routine steps post-event-handling:
- portfolio_kelly with P_NO=0.73: edge 35.5pp on May-31 = HUGE scale-in signal. Brownian-bridge: fair 0.92 vs mark 0.375 = -54.88pp SCALE_UP. Both tools say scale. BUT: not acting unilaterally — operator just received catastrophic event Telegram (msg 331) and may prefer close-to-limit-bleed. Wait for operator response before scaling.
- Iran-regime-fall NO: YES dropped 0.185 → 0.115 (+7pp favorable). Mark 0.835 → 0.885. +$1.62 MTM on this position offsetting May-31 partial. Favorable for our NO.
- 0 redeems. Discover only shows May-31 (held). Sports: USA WC 2026 NO at $0.989 = 6.5% APY (below filter). Macro: Fed-June markets all 99%+ efficient.

Telegram tick-summary subsumed by msg 331 catastrophic event escalation. Routine summary would be noise on top.

## 2026-05-24 ~14:00 UTC — Sunday 14:00 cron tick — May-31 partial recovery

**Material:** May-31 NO mark 0.345 → 0.505 (+16pp favorable since 02:00). MTM $6.01 → $8.81 = +$2.80 unrealized recovery. Position now -25.52% on cost (was -49% at low). UMA cache confirms YES dropped 0.625 → 0.495 (+13pp favorable).

5 news alerts since 02:00, ALL MATERIAL on iran-peace ("largely negotiated", "Rubio significant progress", "Pakistan offers next talks"), all directionally adverse for our NO. Yet market RECOVERED — suggests market is absorbing the rhetoric and finding equilibrium. Either: (a) profit-taking on YES side, (b) realization that signing isn't actually today, (c) UMA-criterion-strict reading reasserting in market psychology.

Regime-fall NO also recovered: +1pp to 0.895. Total MTM $76.27 → $79.41 = +$3.14 over 12h.

**Kelly with P_NO=0.73:** May-31 edge now 22.5pp at mark 0.505 (was 35.5pp at 0.345). Still well above 10pp filter. BB fair=0.92 vs mark=0.505 = -41.5pp SCALE_UP. NOT scaling per yesterday's decision (R-U pattern risk + variance amplification on falling-knife position).

**Cron outcomes:** UMA 1 PRICE_MOVE alert (favorable). Ostium unchanged. discover_markets surfaces Strait-of-Hormuz-traffic-returns-by-end-May NO at $0.912 (NEW candidate) — 6.4d to resolution. Need fresh evaluation if scaling cluster room available.

**Position note:** Aliens NO mark 0.855 → 0.845 (-1pp). Edge dropped to +0.5pp per Kelly. BB at p=0.85: fair=0.86 vs mark 0.845 = +1.5pp — within noise. Hold.

7 days to May-31 resolution. **HOLD decision stands. No scale. Awaiting actual signed-MOU text to make ultimate call.**

## 2026-05-24 ~14:30 UTC — Sunday weekly long-term review

Ran world_state_digest on biotech-health + crypto-on-chain (both 4-week-unrun domains).

**4 themes surfaced (3 HIGH conf):**
- HIGH: GLP-1 Oral Formulation Expansion (EMA approved oral Wegovy May 22; addressable market expansion)
- HIGH: EigenLayer Restaking Dominance (93.9% market share, $15.258B TVL)
- HIGH: Base L2 Winner-Take-Most (Base TVL 3x in 4mo; ARB+Base = 77% of L2 liquidity)
- MED: Boehringer Ingelheim PDE4B (Jascayd first-in-class IPF treatment in 10+ years)

**longterm_check on top 2:**
- **LLY 1.5/4 PASS at ATH** — fwd P/E 31x, debt $40.9B (+43% YoY), valuation already prices 20%+ obesity growth perpetually. Entry $745-800 OR event-driven on Mounjaro share drop / retatrutide P3 fail. Same pattern as CCJ/LEU/CEG/NVDA — valuations stretched.
- **EIGEN 3/4 WATCH at $0.227** — cyclical/secular strong, margin-of-safety weak (supply dilution, pre-revenue). Hard catalyst: **June 1 unlock cliff (300M+ tokens)**. Entry $0.12-0.16 post-washout (3-4% position with $0.10 stop) OR $0.20-0.25 small core now.

**Watchlist additions:**
- LLY entry_max $800 (route: ibkr_surface)
- EIGEN entry_max $0.18 (route: ibkr_surface — post-unlock washout target)

**Pattern observed:** 5 weekly digest rotations now done (2026-04-25 onward); 5-of-6 longterm_check runs on surfaced top candidates returned PASS/WATCH at current prices. Consistent: valuations are stretched in this cycle. Discipline holding: no IBKR-side entries triggered for operator. EIGEN is the most interesting — crypto with hard catalyst (June 1 unlock) creates a defined entry opportunity.

Pre-end-of-May journal split flagged: file now 3344 lines; will batch on 2026-06-01.

Next weekly: 2026-05-31 (likely no fire due to weekend cron + May-31 resolution event); manual sweep 2026-06-01 covering trade-regulation + markets-corporate (remaining unvisited slugs).

**Brief meta-reflection note:** No new structural findings beyond what's been shipped recently (term-structure framework, body-fetch re-val, daemon log fix, prior updates). May-31 position management is active; framework holds. Brief idle on reflection cycle.

## 2026-05-25 ~02:00 UTC — Monday 02:00 cron tick (May-31 dramatic recovery, term structure reverted)

**MAJOR recovery on May-31 NO:**
- Mark 0.505 → 0.795 (+29pp favorable since 14:00)
- MTM $8.81 → $13.86 = +$5.05 unrealized recovery
- Position now +17.25% on cost (was -49.13% at low → -25.52% → now +17.25%)
- UMA confirms YES dropped 0.495 → 0.205 (+29pp)

**Term structure ALSO reverted:**
- May 26: YES 0.575 → 0.075 (-50pp)
- May 31: YES 0.655 → 0.205 (-45pp)
- Jun 7: YES 0.69 → 0.275
- Jun 30: YES 0.735 → 0.465
- Dec 31: YES 0.88 → 0.76 (-12pp)

This is decisive confirmation that yesterday's catastrophic move was SPECULATION/OVERREACTION, not a fundamental shift. Trump tempering + Tehran pushback brought it all back. The catalyst_check + Opus research framework worked correctly: identified the MOU + 30-day-window structure as TEMPORARY per criteria; market initially priced loose interpretation; reverted as no signing materialized.

**Kelly vs BB framework hits real test:**
- Kelly with P_NO=0.73: edge = -6.5pp (mark 0.795 > prior 0.73) → "trim/close candidate"
- BB at t/T=0.78: fair_BB(0.73, 0.78) = 0.73^0.22 = 0.933 → mark 0.795 = -13.8pp SCALE_UP

Per strategy/00 framework note (added 2026-05-19, commit ecf554c): **use BB for late-stage bond-like NO**. Don't trim on Kelly's static signal — at t/T=0.78 mark should be migrating toward 1.0, BB captures this. HOLD.

**Position EV from current MTM:**
- Hold to resolution: 0.73 × $17.44 + 0.27 × $0 = $12.73
- Close at MTM: $13.86 realized
- Close advantage: +$1.13 per static EV

But: BB time-decay model says conditional P(NO from t=0.78 onward | no deal yet) ≈ 0.94 (via hazard-rate model p^(1-t/T)). At that conditional probability, hold EV = $16.36 vs close $13.86 = hold +$2.50 advantage. The Bayesian update for "no deal happened in 78% of window" is what BB captures.

**Decision: HOLD per BB-framework dominance over Kelly-static for late-stage NO.** 5.9d to resolution.

Total MTM $79.41 → $83.02 = +$3.61 over 12h. Iran-regime-fall also -2pp on regime-stays-stable signal (favorable for NO). Other positions stable.

**Lesson reinforced:** Yesterday's framework framework lessons (term-structure-as-UMA-signal + Kelly-vs-BB) both validated through this volatility event. The HOLD decision (msg 333) was correct despite the catastrophic intermediate drawdown.

## 2026-05-25 ~02:15 UTC — Meta-reflection: Bayesian-conditional-update note added to strategy/00

The May-31 volatility event (0.815 → 0.345 → 0.795 within 24h) revealed the underlying mechanism behind Brownian-bridge's "use BB for late-stage NO" rule: it's a Bayesian update via hazard-rate model. Conditional on "no YES event happened in 78% of the window," the probability of NO over the remaining 22% is `p^(1-t/T)` — strictly higher than the unconditional prior. At t/T=0.78 with P_NO=0.73, conditional ≈ 0.94.

Updated the existing 2026-05-19 framework note in strategy/00_philosophy.md to make the mechanism explicit. This is a real reasoning refinement (not just doc cleanup) — the unconditional vs conditional probability distinction matters for future late-stage positions. Bounded ~5-line addition. Compounds.

No other findings this cycle.

## 2026-05-25 ~14:00 UTC — Monday 14:00 cron tick (May-31 adverse again, -7.5pp)

**Material:** May-31 NO mark 0.795 → 0.720 (-7.5pp adverse since 02:00). MTM $13.86 → $12.56 = -$1.30 unrealized. Position +6.19% on cost. UMA shows YES moved 0.205 → 0.280.

**Driver:** "Rubio says 'solid' Iran deal may come on Monday" (today). Market is pricing in the Monday hint. Counter-signals: "Iran denies deal imminent" + Iran chief negotiator pushback. Mixed = volatility.

**Cross-position recovery offset:** Iran-regime-fall NO +3pp favorable to 0.885 (regime-stays-stable on deal-progress signaling). +$0.61 MTM. Total MTM $83.02 → $82.73 = only -$0.29 over 12h.

**Body-fetch CRITICAL re-val production:** 3 more downgrades fired today across iran-peace alerts. System working.

**Kelly + BB framework (post-Bayesian-mechanism note):**
- Kelly edge: 1.0pp (mark 0.720 vs prior 0.73) → near-neutral
- BB at t/T=0.80: fair=0.93^0.20 = 0.938 vs mark 0.720 = **-21.8pp SCALE_UP**
- Per framework: hold per BB, ignore Kelly's near-neutral signal. Conditional-update interpretation: at t/T=0.80 with no deal yet, P(NO in remaining 5.4d) ≈ 0.94 — strongly favors NO.

**Decision:** HOLD. 5.4d to resolution. Monday-deal-rumor is the catalyst risk; if no deal materializes today, expect reversion.

Macro: only 2 Fed-June markets, no-change at $0.9765 = efficient.

## 2026-05-26 ~02:00 UTC — Tuesday 02:00 cron tick (May-31 -4.5pp more, BB still strongly SCALE_UP)

**Material:** May-31 NO mark 0.720 → 0.675 (-4.5pp adverse since 14:00). MTM $12.56 → $11.77 = -$0.79. Position now -0.45% on cost (essentially breakeven, vs +17.25% on Mon 02:00). UMA no alert (move just under 5pp threshold). Total MTM $82.73 → $80.62 = -$2.11 over 12h.

**Iran-regime-fall NO:** +1pp favorable to 0.845; small offset.

**News flow today NET NO-favorable but market moved adverse:**
- "Nuclear issue remains key obstacle" (MATERIAL favorable)
- "Both sides downplay rapid deal" (MATERIAL favorable)
- "Trump's deal outline sparks alarm in Israel" — Israeli pushback adds friction
- "Negotiations proceeding" (CRITICAL, body-fetch downgraded)
- "Iran chief negotiator denies imminent deal" (yesterday, still standing)

Market continues drifting adverse despite favorable-for-NO news. Pattern: when no signing materializes in 24-48h after Trump rhetoric, market should revert (as it did Mon overnight). Today is +24h from Rubio "Monday" hint; if no signing by Tue evening, expect reversion.

**Kelly + BB framework:**
- Kelly edge: 5.5pp (mark 0.675 vs prior 0.73) → modest entry candidate (below 10pp filter)
- BB at t/T=0.81: fair=0.73^0.19 = 0.943 vs mark 0.675 = **-26.8pp SCALE_UP**
- Per Bayesian-mechanism note: conditional P(NO in remaining 4.9d) ≈ 0.94 — strongly favors NO

**Catalyst_check skipped:** last ran 2026-05-24 02:00 (P_YES strict = 11%). News flow since is net NO-favorable. Re-running would likely produce similar verdict. Sticking with current prior.

**Decision: HOLD.** EV math at P_NO=0.73: hold $12.73 vs close $11.77 = +$0.96 hold advantage (thin but positive). BB framework dominant for late-stage. 4.9d to resolution.

## 2026-05-26 ~14:00 UTC — Tuesday 14:00 cron tick (May-31 partial recovery, term structure tells story)

**Material:** May-31 NO mark 0.675 → 0.725 (+5pp favorable since 02:00). MTM $11.77 → $12.64 = +$0.87 unrealized. Position +6.93% on cost. Iran-regime-fall NO +2pp favorable. Total MTM $80.62 → $82.14 = +$1.52 over 12h.

**Term structure interpretation (most informative signal):**
- May 26 (today, 4h remaining): YES 0.055 — market basically certain no deal today
- May 31: YES 0.275 (recovered from 0.345 Sunday peak, 0.205 yesterday low, 0.295 today AM)
- Jun 7: YES 0.395
- Jun 15: YES 0.485 (was 0.335 Sunday — UP)
- Jun 30: YES 0.545 (was 0.465 Sunday — UP)
- Jul 31: YES 0.695
- Dec 31: YES 0.805 (was 0.760 Sunday — UP)

Pattern: probability mass is moving OUT in time. Market expects deal but NOT specifically by May 31. NO-favorable for our position. May-31 sub-market still well below Dec-31 base rate (0.805) suggesting "yes eventually but not in 4d."

**News flow today (5 alerts, NET NO-favorable):**
- Iran: "contradictory statements from US hindering deal"
- US attacks near Strait of Hormuz (escalation)
- Rubio "hopefully we can pull it off" (less confident than yest)
- Missile strike in Hormuz (escalation)

**Kelly + BB:**
- Kelly edge 0.5pp at mark 0.725 vs P_NO 0.73 — neutral
- BB at t/T=0.83: fair=0.947 vs mark 0.725 = -22.2pp SCALE_UP
- Per framework + Bayesian mechanism: conditional P(NO in remaining 4.4d | no deal yet) ≈ 0.947 — strongly favors NO

**EV math at P_NO=0.73:** hold $12.73 vs close $12.64 = +$0.09 (essentially indifferent per static EV). BB conditional says hold strongly favorable.

**Decision:** HOLD per BB framework. 4.4d to resolution. Market collectively believes deal NOT by May 31.

**Cron outcomes:** UMA clean, Ostium unchanged, 0 watchlist hits, 0 redeems. Discover: Strait-of-Hormuz-traffic-returns-by-end-May NO at $0.975 = 571% APY — interesting bond-like fade with mechanical resolution + 4.4d window, but iran-cluster cap binding for any new entry. Macro: no candidates.

## 2026-05-27 ~02:00 UTC — Wednesday 02:00 cron tick (May-31 stable around 0.755-0.775)

**Material:** May-31 NO mark at 0.755 (slight drift from 0.775 earlier this hour). Position +14% on cost. UMA clean. No new news_alerts since the 4 NO-favorable ones overnight (Trump "not to rush", Iran ceasefire complaints, "did Trump oversell" framing).

**Kelly + BB:** Kelly edge -2.5pp at mark 0.755 vs P_NO 0.73 = trim candidate (static). BB at t/T=0.84 conditional: fair 0.952 vs mark 0.755 = -19.7pp SCALE_UP. Per Bayesian-mechanism framework: conditional P(NO in remaining 3.9d | no deal yet) = 0.952 — strongly favors NO. Hold.

**Cron outcomes:** Ostium unchanged. 0 watchlist hits. 0 redeems. Discover: only Senegal-WC NO at 4.2% APY (below filter). No actions.

3.9d to resolution. Mark stable in 0.72-0.78 range = market consensus "deal not by May-31."

## 2026-05-27 ~14:00 UTC — Wednesday 14:00 cron tick (May-31 stable +2pp, MTM +\$0.66)

**Material:** May-31 NO mark 0.755 → 0.775 (+2pp favorable). Position +14.30% on cost. Iran-regime-fall +1pp favorable. Total MTM $82.7 → $83.36 = +$0.66.

2 news alerts (mixed: Lebanon escalation NO-favorable, Rubio "hopefully we can pull it off" NO-adverse). Body-fetch downgrade fired on Lebanon article.

Kelly edge -4.5pp = trim per static. BB at t/T=0.86 conditional: fair 0.957 vs mark 0.775 = -18.2pp SCALE_UP. Per framework: HOLD.

3.4d to resolution. No actions.

## 2026-05-28 ~02:00 UTC — Thursday 02:00 cron tick (May-31 strong recovery +10pp)

**Material:** May-31 NO mark 0.775 → 0.875 (+10pp favorable since 14:00). MTM $13.52 → $15.26 = +$1.74 unrealized. Position +29.05% on cost (best since pre-Sunday-catastrophe peak). UMA confirms YES dropped 0.225 → 0.125 (+10pp NO favorable).

**Drivers:** Trump "tell negotiators NOT to rush" (escalation from "Monday deal" to "be patient"). Trump threatening to bomb Oman over Strait of Hormuz impasse — major escalation. Both confirm deal not imminent by May 31.

**Kelly + BB:**
- Kelly edge: -14.5pp at mark 0.875 vs P_NO 0.73 = trim per static
- BB at t/T=0.88: fair=0.962 vs mark 0.875 = -8.7pp SCALE_UP (still)
- Per framework: hold per BB. Conditional P(NO in remaining 2.9d) ≈ 0.96

**Note:** Static EV math says close (close $15.26 > hold $12.73). But BB conditional says fair value is $16.78 ($17.44 × 0.962). The hazard-rate mechanism captures the "no deal yet despite 88% of window passing" Bayesian update. Hold per framework.

Iran-regime-fall NO: minor drift -1pp to 0.865. Other positions stable. Total MTM $83.36 → $84.74 = +$1.38 over 12h.

**Position trajectory recap:**
- Sunday low: $6.01 (-49% on cost)
- Today peak: $15.26 (+29% on cost)
- Resolution in 2.9d at $17.44 if NO wins

No actions. Hold per BB framework. Discover/macro nothing new.

## 2026-05-28 ~02:30 UTC — Brief reflection cycle: framework EV-computation clarification

Caught a sloppy application of the framework in last cron tick (commit 278c0b3): wrote "static Kelly EV says close (\$15.26 > \$12.73)" using unconditional P_NO=0.73 × \$17.44. The correct EV at t/T=0.88 uses CONDITIONAL fair_BB=0.962, giving expected payout \$16.78 vs close \$15.26 = +\$1.52 hold advantage. Decision was right (hold per BB framework explicit override) but the reasoning chain had a confused step.

Added explicit gotcha note to strategy/00 framework section: "EV = unconditional × max_payout" is WRONG at intermediate time; must use conditional fair_BB. Kelly `edge = p - mark` is a sizing input, not a payout estimator.

Bounded ~3-line addition. Compounds: prevents future LLM reads from making the same confused step in late-stage NO position EV-comparisons.

## 2026-05-28 ~14:00 UTC — Thursday 14:00 cron tick (May-31 NO at all-time high mark)

**Material:** May-31 NO mark 0.875 → 0.925 (+5pp favorable since 02:00). MTM $15.26 → $16.13 = +$0.87. Position **+36.43% on cost** — all-time high since entry. UMA confirms YES dropped 0.125 → 0.075. Total MTM $84.74 → $85.27 = +$0.53.

**Drivers (5 news alerts, all NO-favorable):**
- US/Iran trade air strikes — Trump dismisses Hormuz deal
- US launches new strikes (day 90)
- Trump threatens to "blow up" Oman over strait
- Trump: "I don't care about war impact"

Massive escalation = deal near-impossible by May 31 (2.4d). Market collectively agrees — 92.5% NO pricing.

**Kelly + BB:**
- Kelly edge: -19.5pp at mark 0.925 vs P_NO 0.73 (trim per static)
- BB at t/T=0.89: fair=0.9664 vs mark 0.925 = -4.1pp SCALE_UP
- Per framework + EV-gotcha note (commit 4d06e15): EV(hold) = 0.966 × $17.44 = $16.84 vs close $16.13 = +$0.71 hold advantage

**Decision: HOLD.** 2.4d to resolution. If NO wins: +$1.31 more at lock-in.

Iran-regime-fall NO -1pp to 0.855 (trade-off: same news that hurts iran-peace YES helps iran-regime YES via escalation = destabilization risk; small per-position offset). Position still +28.6% on cost.

**Cron outcomes:** 0 redeems, 0 watchlist hits, 0 discover candidates, Ostium 0 open (closed yest). Trump-out NO holding 0.895 / +19.8%, others stable.

## 2026-05-29 ~02:00 UTC — Friday 02:00 cron tick (May-31 mark stable 0.885, 1.9d to resolution)

**Material:** May-31 NO mark stable at 0.885 (vs 0.885 at midnight, -4pp from yest 14:00 peak 0.925). Position +30.53% on cost. Other positions stable.

**Kelly + BB:** Kelly -15.5pp trim (static), BB at t/T=0.91: fair 0.971 vs mark 0.885 = -8.6pp SCALE_UP. EV(hold) = 0.971 × $17.44 = $16.94 vs close $15.43 = +$1.51 hold advantage. Per framework + EV-gotcha: HOLD.

**Cron outcomes:** UMA clean, Ostium 0 open (closed Wed), 0 watchlist hits, 0 redeems, 0 discover candidates. Macro: efficient. No actions.

1.9d to resolution. Market still implies 11.5% YES probability for permanent deal in <2d.

## 2026-05-29 ~14:00 UTC — Friday 14:00 cron tick (May-31 +3pp; "60-day ceasefire" framing = TEMPORARY per criteria)

**Material:** May-31 NO mark 0.885 → 0.915 (+3pp favorable). MTM $15.43 → $15.96 = +$0.53. Position +34.95% on cost. Total MTM $83.94 → $85.13 = +$1.19.

**KEY news framing:** 5 alerts converge on "**60-day ceasefire framework / ceasefire EXTENSION**" — this is EXPLICITLY temporary per Polymarket resolution criteria ("agreements that are explicitly temporary will not qualify"). Even if signed by May 31, it would NOT meet permanent-deal threshold. NO-favorable strong.

Body-fetch CRITICAL re-val fired on Vance article, downgraded to MATERIAL with explicit "ceasefire extension" reasoning. Infrastructure correctly identifying loose vs strict deal framings.

**Kelly + BB:**
- Kelly -18.5pp trim (static)
- BB at t/T=0.92: fair 0.976 vs mark 0.915 = -6.1pp SCALE_UP
- EV(hold) = 0.976 × $17.44 = $17.02 vs close $15.96 = +$1.06 hold advantage

**Decision: HOLD.** 1.4d to resolution. The "60-day ceasefire" framing emerging in news flow is increasingly aligned with my strict-criterion thesis. Market correcting toward my view.

Other positions: Iran-regime-fall unchanged 0.855. Pahlavi-NO recovery to 0.936 (+0.1pp). Hantavirus -1pp drift.

## 2026-05-29 ~late — Operator strategy session (model switched to Opus 4.8) + robust-edge gate

Operator live session (not cron). Three strategy changes + one self-caught refinement:

1. **Scrapped 60/40 Aave/PM target** (operator: "Scrap the 60/40 target. I will leave it entirely up to you"). The post-R-U defensive ratio had stopped binding — cluster cap + filters already enforced discipline. Idle now defaults to Aave (yield + withdrawability); filter-passing PM entries drain Aave without ratio limit. Commit 1889d8a. Memory: feedback_allocation_freedom.

2. **Edge bar reasoning interrogated** — operator asked the basis for filter strictness, then noted "wasn't the R-U loss due to wrong API use?" Correct, and it exposed that I'd over-stated the 10pp bar's R-U justification. R-U was dominantly an API-observability failure (didn't check umaResolutionStatus on gamma-api when the position vanished from data-api), already fixed by uma_status_check.py. Thicker edge wouldn't have helped.

3. **Edge bar relaxed** (operator: "Why not relax it to >0+operational cost"). Retired the flat 10pp. Commit dc6eb14.

4. **Self-caught flaw on Opus-4.8 review:** "positive EV after op-cost" on the CENTRAL p estimate is fragile — p is itself uncertain and Kelly punishes overbetting a believed-but-wrong edge. Shipped a **robust-edge gate** in polyclaude_enter.py: take iff +EV at the pessimistic bound `p − edge_haircut` (default 0.05). Self-scales the effective floor to estimate confidence (small haircut for tight mechanical-market estimates clears thin edges; large haircut for fuzzy estimates demands fat edges). The ±5% sensitivity machinery already existed but was never gated on — now it is. Commits + push done. Memory: feedback_edge_bar_relax (rewritten to robust form).

Net effect: discipline moved from {flat 10pp + 60/40 ratio} → {robust-pessimistic-EV gate + confidence-scaled haircut}, with mechanical-resolution / cluster-cap / max-5 / polyclaude_enter / uma_status_check retained. More principled, captures marginal +EV the flat bar forwent, but blocks noise-dominated thin-edge bets. Flagged to operator that this is a recalibration (not pure loosening) — would have blocked the current May-31 NO at its 4.5pp entry under default haircut. Awaiting operator on whether to default the haircut looser.

May-31 NO resolves ~2026-05-31 (1.4d). MTM $83.84, +6.5% on book.

## 2026-05-29 ~late — Opus-4.8 meta-reflection: 3 real findings (Aave model, gas bug, bankroll correction)

Reflection with sharper lens surfaced genuine items, not busywork:

1. **Robust-edge gate shipped** (covered above) — gated entry on pessimistic-p bound, not point estimate.

2. **Stale "Aave home = Base" mental model.** Discovered while checking discover_markets hurdle consistency. crypto-sleeve Aave actually holds $34.10 (Base $4.53 + Arb $29.57), not the ~$0/"$14.5" I'd been stating — I'd undercounted by ~$20 and carried a "drained to ~0" belief. AND the PM-sleeve idle $38 USDC.e (Polygon) had sat at 0% for ~2 weeks awaiting a phantom "batch-bridge-to-Base after May-31" that was premised on the wrong home model. Aave Polygon takes USDC.e directly (~2.7%, zero bridge, same chain as PM = instantly available). Supplied $37 (tx 0xff82063d). Same-chain strictly beats bridge-to-Base for sub-$100 (bridge cost > yr of rate gap). Violated my own 2026-05-28 no-deferral rule — now corrected in strategy/01 + memory.

3. **aave_deposit.py gas bug.** Hardcoded maxPriorityFeePerGas ~0; Polygon validator min is ~25 gwei → supply bounced. Fixed with chain-aware _gas_fields helper. Every future Polygon Aave op now works.

4. **Bankroll correction — material, owed to operator.** Earlier (msg 356) I told operator "~$150, -12% vs $170 ref". TRUE bankroll = $162.24 (PM positions $83.84 + Aave $71.10 + idle $2.55 + POL $4.74). That's **-4.6%**, not -12%. Two errors compounded: undercounted Aave by ~$20 (stale belief), and over-valued POL gas tokens at $0.20 when live is $0.089. Reconciles with P&L: $170 + realized(-7.62) + unrealized(+5.12) ≈ $167.5, minus ~$5 friction/POL-drift = ~$162. The R-U loss is real but the book is ~flat-to-slightly-down vs reference, not down 12%.

Lesson meta-point: I'd been reporting position-level numbers accurately each tick but the AGGREGATE bankroll picture drifted on stale sub-totals (Aave, POL price) that the per-tick positions.py view doesn't surface. polyclaude_status.py should be the source of truth for aggregate; I'd been hand-assembling from memory. Flagging to consider a true-bankroll line in status output. (Backlog, not urgent.)

## 2026-05-29 ~late — Reflection: stale rules in the OPERATIONAL cron prompt (higher-leverage than doc cleanup)

Consistency sweep after today's heavy strategy churn. strategy docs were clean (only retired-marked refs to 10pp/60/40). But found two stale assumptions in scripts/daily_checkin.sh — the prompt every forked headless cron tick reads as its literal instructions, so higher-leverage than doc staleness:

1. **Line 91 still said "Calibration data is the actual product — your reasoning quality across 50+ entries is what evaluates whether the LLM architecture works at scale."** This is the EXACT framing the operator overrode 2026-05-14 (ROI is the only goal; calibration-as-product is Goodhart's law). I patched strategy/00 on 2026-05-17 but missed the cron prompt — meaning every autonomous tick for the last 12 days was being instructed to over-weight calibration, contradicting the operator's most important strategic correction. Fixed: now states calibration is a debugging byproduct, ROI is the objective.

2. **Line 93 said "score new candidates against the same edge thresholds the initial portfolio used"** — stale after the edge-bar evolution (initial → 5pp → 10pp → robust-EV gate 2026-05-29). Updated to the current filter set (mechanical-resolution + robust-edge gate via polyclaude_enter + cluster cap + max-5).

Meta-lesson (recurring this session): when a strategy/rule changes, the fix must propagate to the OPERATIONAL path (cron prompt, entry script), not just the human-readable strategy docs. The forked tick doesn't read strategy/00 — it reads daily_checkin.sh's prompt. Doc-only patches leave the autonomous behavior on the old rule. Worth a standing habit: on any rule change, grep daily_checkin.sh + polyclaude_enter.py for the old rule, not just strategy/.

## 2026-05-29 ~19:23 UTC — Empirical check: relaxed edge bar admits nothing new today

Re-ran discovery (top-12 broad, not just hurdle-clearers) against the new robust-EV gate to test whether the edge-bar relax unlocked any trade the old 10pp bar blocked. Result: NO. Universe today is:
- World Cup longshot NO fades (0.1-0.4% YES): mechanical-resolution but ~1-1.7% APY over 51d — now BELOW the ~2.7% Aave idle rate, so correctly fail the hurdle (worse than idle yield).
- Same-day tennis/cricket/IPL: coinflips, no edge for me.
- Held May-31 NO + a subjective Hormuz-blockade-announcement market.

Confirms: binding constraint is opportunity SOURCING, not the filter. Also re-validates that hurdle (beat idle yield) + robust-edge gate (edge robust to estimation error) are complementary and both correctly reject today's universe. The relax was the right call in principle but has no actionable consequence yet — it widens admission for when a genuinely mispriced mechanical market surfaces, which today's tape doesn't contain. No trade.

## 2026-05-29 ~20:42 UTC — MAJOR sourcing fix: discover_markets was blind to 90% of the market

Chased the "sourcing is the binding constraint" thread from the prior reflection to its root and found a real bug with project-life-long impact.

**The bug:** gamma API hard-caps every response at 100 rows regardless of the `limit` param. discover_markets requested limit_per_page=500 → page 0 returned 100 < 500 → tripped the `len(batch) < limit_per_page` short-batch break → loop exited after ONE page. So every scan ever run saw only the top 100 markets by volume (vol24h ≥ ~$225k). The entire long tail — markets ranked 100-1000+ by volume, down to ~$15-40k vol — was NEVER fetched. This directly contradicted the strategy's core edge thesis ("the long tail is where mispricings live"): the sourcing tool was structurally biased AWAY from the edge zone, running at ~10% of intended breadth.

Probed the API directly to confirm: limit=500 returns 100; offset=100 → vol $90-224k; offset=200 → $57-90k; offset=300 → $37-56k. A deep, liquid, never-scanned tail.

**Fix (commit pushed):** limit_per_page 500 → 100 (the API's true page size) so pagination walks the tail across max_pages. Verified: **fetched 996 markets (was 100)**.

**Coupled tuning:** min_vol24 default 2000 → 500. For a taker lifting a resting ask, fillability = book depth (--min-liquidity $20k), NOT recent volume; the high volume floor re-excluded the quiet neglected tail. Liquidity + spread floors keep junk out.

**Result:** default hurdle-clearing candidate count jumped from 4-8 → **37**. The opportunity funnel now reaches the documented edge zone. Flows automatically into the cron (daily_checkin step 6).

**Next-tick plan (NOT rushed tonight, May-31 resolving in ~1.2d):** methodically work the 37 through the full filter stack — drop sports (no edge), require mechanical resolution, run catalyst_check on the survivors, apply robust-edge gate + cluster cap + max-5, size via Kelly+ρ. Expect most to fail (sports/subjective/cluster-correlated), but even 1-2 genuine mispriced mechanical fades from a 10× funnel is the first NEW alpha source since the recoup campaign. This is the ROI-generative activity that was missing — the book was idle-on-discipline partly because discovery was broken, not only because the universe was dry.

Session meta-arc: the Opus-4.8 reflection's recurring win was distrusting assumed state and re-deriving from ground truth — caught the bankroll misreport, the Aave-home model error, the gas bug, three stale-rule instances, and now the sourcing cap. The last is the highest forward-ROI: it compounds on every future scan.

## 2026-05-29 ~20:55 UTC — Triaged the 37 (funnel fix validated: surfaced real non-cluster alpha)

Screened the 37 hurdle-clearing candidates from the fixed (10×) discovery funnel:
- **25 sports** → drop. No edge; mostly sub-hurdle World Cup longshots (4-13% APY, below ~2.7% idle once you account for 51d lock + fees) or same-day coinflips.
- **8 iran-cluster** (June-7/15 peace, Hormuz-traffic, regime-fall-by-June, blockade-announce, Dec-31 peace) → skip. Cluster cap binding; already heavily exposed via the 5 held positions.
- **4 other:** Fed rate markets (99%+ efficient, skip per philosophy); Aliens-by-June-30 NO (35% APY — shorter-horizon dup of held Aliens-2027 NO); Hantavirus (already held).
- **1 GENUINE NEW non-cluster candidate: "MicroStrategy sells any Bitcoin by June 30, 2026?" NO** — ~$67-69k liquidity, ~32d, mechanical-ish. Saylor/MSTR never-sold-BTC + stated never-sell policy = strong NO prior. This is exactly the neglected-tail mechanical fade the funnel fix targeted — validates the fix surfaced real alpha, not just sports noise.

**MSTR-sells-BTC NO — next-tick evaluation plan (NOT rushed; 32d = zero time pressure):**
1. Pull exact resolution criteria from gamma-api — "sells ANY bitcoin" is broad; check whether tax-loss harvesting, collateral liquidation, subsidiary/treasury ops, or accounting reclassification could trigger YES. R-U lesson: read the literal criteria, not the headline.
2. Walk the live CLOB orderbook (per the midpoints-unreliable memory) — confirm a real fillable NO ask, not a stub midpoint behind the gamma APY.
3. catalyst_check for the 32d window (any MSTR earnings / forced-sale / margin event).
4. If criteria are clean + ask is real + robust-edge gate passes at the pessimistic-p bound → size via Kelly+ρ (own cluster: "crypto-treasury", ρ≈0 to existing book) and enter via polyclaude_enter.

Net: funnel fix → 1 genuine candidate on its first scan. Even a modest hit rate on a 10×-wider funnel is the first NEW alpha source since the recoup campaign. The triage is analysis (done now, no capital committed); the entry decision is correctly methodical-next-tick given the 32d horizon.

## 2026-05-29 ~21:05 UTC — MSTR candidate DROPPED on diligence (stale prior, inverted edge) — discipline win

Did the cheap decisive diligence on the MSTR-sells-BTC NO lead BEFORE committing capital. Result: thesis was inverted; dropped.

**Term structure (the tell):** sells-BTC-by May 31 = 18% YES, June 30 = 67% YES, Dec 31 = 88% YES. Market strongly expects a near-term sale — opposite of my "Saylor never sells" prior.

**Why (60-sec web search confirmed):** BTC fell 23% in Q1 2026 ($87.5k→$67.7k); MSTR carries a $7.6B unrealized loss + $2.2B deferred-tax-asset opportunity under FASB fair-value accounting. **Saylor stated on the Q1 2026 earnings call MSTR "is ready to sell bitcoin"** for tax-loss harvesting, with direct 2022 precedent (sold 704 BTC for the same reason). "Sells ANY bitcoin" + stated intent + tax incentive + precedent = the 67%/88% pricing is correct.

**My prior was 2 years stale** (HODL-forever narrative, obsolete since the Dec-2022 tax-loss sale). Buying NO at 0.326 would have been the R-U mistake exactly: trading my framing against a market pricing current information I lacked. The "683% APY" gamma figure was the naive-annualization / implied-risk trap, not free money. DROPPED — and no YES trade either (no edge on sale *timing* within window beyond what the 67→88 term structure already prices).

**Net of tonight's funnel work:** the 10× sourcing fix is a permanent forward-ROI win and surfaced this candidate (invisible before); diligence correctly killed it. Zero trades, process worked as designed. The MSTR markets are now "checked, no edge — stale-prior trap" so future scans shouldn't re-lead on them.

**Reinforced lesson (add to the R-U family):** a high gamma-APY on a bond-like fade is a *question*, not an answer — it often means the market prices real risk my prior is ignoring. Always read the term structure across sibling by-date markets + a 60-sec catalyst search BEFORE the prior hardens into a thesis. The relaxed edge bar makes this MORE important, not less, because more thin/high-APY candidates now clear the funnel.

## 2026-05-30 ~02:00 UTC — Saturday 02:00 cron tick (quiet, May-31 resolving in ~0.9d)

May-31 NO stable at 0.945 (+39.37% on cost, all-time high), ~0.9d to resolution. UMA clean (no dispute as resolution approaches — the R-U risk window is passing cleanly). 0 news alerts, 0 redeems, Ostium 0 open. Book +8.66%.

Discovery fix live in cron (fetched 996 vs old 100) but 0 candidates clear hurdle+3d-floor this tick — the high-APY tail entries are all either <3d (floor-excluded), iran-cluster (capped), or sports (no edge). Consistent with last night's triage: MSTR was the only genuine non-cluster lead and diligence correctly killed it (stale-prior/inverted-edge). No new actionable candidate.

No actions. May-31 NO resolves tomorrow (~2026-05-31); redeem-all wired into cron will handle it. Expected: NO wins → lock $17.44 (+$0.96 from current MTM, +$5.62 from $11.82 cost). Post-resolution: ~$17 freed → Aave Polygon same-chain (per corrected idle-home rule).

## 2026-05-30 ~14:00 UTC — Saturday 14:00 cron tick (May-31 NO 0.966, ~0.4d to resolution)

May-31 NO at 0.966 (+42.47% on cost), ~0.4d to resolution. UMA clean. 2 news alerts both thesis-confirming ("uncertainty remains over Iran ceasefire extension" — no permanent deal materialized). 0 redeemable, 0 new candidates clearing filters (998 fetched). Book +9.13%, all 6 positions stable/favorable. No actions. Redemption cron-wired for when it resolves (~tonight/tomorrow).

## 2026-05-31 ~02:00 UTC — Sunday cron tick (RESOLUTION DAY for May-31 NO)

May-31 NO at 0.980 (+44.46% on cost), resolves end of today UTC. Not yet redeemable (0/6; UMA settlement follows resolution). UMA clean. Book +9.62%.

Two candidates cleared hurdle (995 fetched via funnel fix):
- Netherlands win WC 2026 NO — sports, no edge, skip.
- "Satoshi's identity revealed by Dec 31?" NO @ 0.945, 9.4% APY, 214d, $25k liq — evaluated (relaxed bar admits it) but SKIP on mechanical-resolution filter: "identity revealed" is subjective (a splashy unproven claim could trigger UMA-loose YES — the exact R-U risk category) + thin ~3.5pp edge barely beats ~2.7% Aave idle over a 214d lockup. Logged as checked/skip.

No actions. May-31 NO resolves today; redeem-all cron-wired. Post-resolution: ~$17 → Aave Polygon (same-chain). Will be the first realized confirmation of the held-NO thesis through the full volatility cycle (0.815 → 0.345 catastrophe → 0.980 recovery, HOLD validated).

## 2026-05-31 ~late — FIRST funnel-fix entry: Satoshi NO (operator challenge → conceded over-caution)

Operator pushed on my Satoshi skip ("how could this go wrong? would voters affirm a fake?"). Worked the concrete failure modes:
- Genuine reveal ~1-1.5%/214d (legitimate loss, not "wrong").
- UMA affirms a fake: LOW (~0.5-1%) — strict "definitively proven / wallet transfer" primary criterion + dispute mechanism + 15yr of failed claims (Newsweek 2014, Craig Wright legally ruled NOT Satoshi 2024, HBO doc 2024) all failing the consensus bar.

Conceded: I overstated the UMA tail (~2-3% → ~0.5-1%) — the skeptic-bias-toward-inaction the memory warns about, over-applying the R-U scar to a market where the subjective channel is genuinely weak. Honest P(NO) ~0.98, edge ~4pp at the real 0.94 ask, ~9% annualized.

**ENTERED: 6 shares Satoshi NO @ 0.94 = $5.64** (DEC-0028, tx 0x2c4d5a5b). Sized small (well below $58 Kelly) for the residual tail. First entry sourced from the fixed discovery funnel — validates the funnel-fix → relaxed-bar → diligence → entry pipeline end-to-end.

**Execution friction logged (3 retries):**
1. polyclaude_enter posted at gamma midpoint 0.935 → rejected (tick-size 0.01). It uses the gamma mid as limit price, which is often off-grid.
2. clob_v2 buy $8/0.94 → rejected (share count >4 decimals). Need usd_size that yields clean 2-dec maker / 4-dec taker amounts.
3. Real blocker: CLOB collateral is wrapped pUSD, NOT raw USDC.e. Exchange saw only $5.80 usable (residual pUSD); the $10 USDC.e I'd withdrawn from Aave was NOT usable without a CollateralOnramp.wrap (no script for it). Sized the buy to the available $5.80 pUSD ($5.64) — cleaner anyway. Redeposited the unneeded $9 USDC.e back to Aave Polygon (tx 0x0fa47fcd).

Backlog-worthy: (a) polyclaude_enter should round limit price to the market tick size; (b) no pUSD-wrap script exists — entries depend on residual pUSD or a manual wrap.

## 2026-05-31 ~late — polyclaude_enter gate now walks the LIVE ASK (closes phantom-edge hole)

Reflection finding: the robust-edge gate evaluated EV at the gamma midpoint (`mark`), contradicting the polymarket-midpoints-unreliable lesson (mids sit between stub bids and real asks). The Satoshi entry exposed it (gate saw 0.935, real ask 0.940). Trivial gap there — but the 10x funnel fix now surfaces thin-liquidity tail markets where the stub-mid↔real-ask gap can be multi-point, so the gate could pass phantom edge that evaporates on fill (the exact phantom-arb trap).

Fix (committed): added `_best_ask(token)` hitting the CLOB book API directly; polyclaude_enter now uses the live lowest ask as `mark` for the gate (falls back to gamma mid only if the book is unreachable), and prints the mid→ask delta.

Immediately validated: re-running the Satoshi market now shows live ask 0.95 (my $5.64 buy lifted the 0.94 level) → gate correctly SKIPs (p_robust 0.95 ≤ mark 0.95, no robust edge), whereas the old gamma-mid 0.935 path would have passed. So the fix just prevented a phantom-edge decision in real time, and confirms my 0.94 fill was at the viable edge — adding more at 0.95 would be -EV. Every future entry now gates on the price it would actually pay.

Net: the funnel→gate→entry pipeline is now honest end-to-end (real ask in the gate + tick-rounded on-grid execution). Two of the three Satoshi-surfaced frictions fixed (tick-rounding + live-ask gate); pUSD-wrap script remains queued (not blocking).

## 2026-05-31 ~14:00 UTC — Sunday 14:00 cron tick (May-31 resolving end-of-day; quiet)

May-31 NO at 0.985 (+45.20%), resolves end of today UTC, 0/7 redeemable (settlement follows). UMA clean. 7 positions, book +9.86%. Satoshi NO (DEC-0028) holding at ~spread. 1 recycled-Hormuz news alert (no action). discover: 1 candidate (cluster/sports per recent pattern, skip). No actions. redeem-all cron-wired for when May-31 settles (~June 1).

## 2026-05-31 ~late — Sunday weekly long-term review (trade-regulation + markets-corporate)

Ran world_state_digest on the two never-run slugs. 5 themes, none HIGH-conf, and most are SHORT/sector-rotation/tactical (not generational-LONG, not polyclaude-deployable):
- Oil Repricing (MED-HIGH): Brent -20% to $92.56; short energy-intensive industrials, long renewables.
- Semi Equipment grace-period (MED): export-control grace to Dec 31 + AI capex; AMAT/LRCX/ASML.
- USMCA auto RoO (LOW-MED): short F/GM/STLA Mexico exposure.
- Pharma MFN erosion (MED): $35-40B branded cut; short JNJ/PFE/MRK, long generics/PBMs.
- China ag commitments (LOW-MED): long ADM/BUNGE + niche ag-input.

longterm_check on the one clean LONG (LRCX): **2.5/4 WATCH @ $318** — secular AI-capex real, but peak cycle + 53.9x P/E + weak margin of safety. Entry $250-280 OR capex-guidance miss. Added to watchlist ($280, ibkr_surface).

Surfaced the short/tactical themes for operator IBKR discretion (they don't fit the generational-LONG framework). Pattern holds: 8 candidates vetted across rotations, 7 PASS/WATCH at current prices — valuations broadly stretched; discipline holds, 0 ENTER-NOW.

Portfolio: 7 positions, MTM ~$92.5, +9.6% on cost. May-31 NO at 0.989 (+45.8%), resolves end-of-day, redemption cron-wired (~June 1). Next weekly 2026-06-07 (rotate to oldest-run: critical-minerals, geopolitics/energy).

## 2026-06-01 ~02:00 UTC — June 1 02:00 cron tick (May-31 NO at 0.998, settlement imminent)

May-31 NO at 0.998 (+47.12%), ET deadline (11:59 PM ET May 31 = ~04:00 UTC) ~2h out, then UMA settles. Still 0/7 redeemable. News confirms no permanent deal ("Trump seeking edits to US-Iran deal" — still negotiating, nothing signed). Thesis fully validated through the full cycle (0.678 entry → 0.345 catastrophe → 0.998). UMA clean, Ostium 0, 0 new candidates (990 fetched). Book +9.76%. No actions; redeem-all will fire on the next post-settlement tick (~14:00 June 1) locking +$5.62 on cost.

## 2026-06-01 ~14:00 UTC — May-31 NO REDEEMED: +$5.62 realized (+47.5%), HOLD-through-catastrophe validated

redeem-all settled the May-31 Iran-peace NO: **17.44 USDC.e received** (tx 0xef8766ab), realizing **+$5.62 on $11.82 cost (+47.5%)**. (Label-bug cosmetic note: logs "yes_redeemed 17.44" — burned 17.44 NO shares for $17.44 since NO won; functionally correct.) DEC-0006 updated with outcome + calibration + lesson.

This closes the dominant position of the whole period and fully validates the HOLD decision through the catastrophe: entry 0.678 → 0.345 (-49% mark) on the 2026-05-24 Trump "largely negotiated" shock → 1.00 settle. The thesis (strict "permanent deal" criterion vs the 60-day-ceasefire reality) held; the mid-cycle crash was speculation/UMA-loose-pricing that reverted exactly as analysis predicted. The term-structure-as-UMA-signal + Kelly-vs-Brownian-bridge frameworks were built from this position and validated by it.

**Capital redeployed immediately** (no-deferral idle-home rule): $16.5 of the freed $18.44 USDC.e → Aave Polygon same-chain (tx 0x370b7af4), ~$1.9 buffer left.

Book now: 6 PM positions (5 long-dated NOs + Satoshi NO) + Aave. The 5 held NOs ride to Dec 31 (~$11 combined expected). Realized P&L since kickoff now: prior -$1.999 (incl R-U) + this +$5.62... net the May-31 win flips cumulative realized to roughly break-even-to-slightly-positive. uma_status_check GAMMA_LOOKUP_FAILED on the resolved May-31 slug is benign de-indexing (cache self-cleans).


---

## 2026-06-02 ~00:10 UTC — Meta-reflection

Two genuine findings documented (not forced):

**1. Strategy refinement → philosophy edge-source-1 (tail-correlation filter).** The longshot-fade
class needs an idiosyncratic-vs-correlated-tail distinction. Sell NO on idiosyncratic-tail longshots
(aliens, Greenland, GME-eBay — if they hit, nothing else in the book moves); demand a much bigger
premium for, or skip, correlated-catastrophe tails (China-Taiwan invasion, pandemic, NK-invades-SK)
— those pay out exactly when broad risk-off also craters the crypto+Aave book (max loss when capital
is scarcest). On 2026-06-01 took aliens-NO 0.85 + Greenland-NO 0.87 (~13-15% premium, idiosyncratic)
but skipped China-Taiwan 6.6% / hantavirus 5.3% / NK-SK 5.2% despite similar "APY". Fade class is a
BASKET play (diversify idiosyncratic tails). See notes/fade_basket.md.

**2. Process gap → wired arb scanners into daily_checkin step 6.** event_monotonicity_scan.py
(decomposition arb / edge-source #4) and polymarket_consistency_scan.py (multi-leg sum mispricing,
live-CLOB-validated) were NOT in the routine (sports_pm_scan + macro_pm_scan already were). I eyeballed
~1000 markets and missed them until operator pushed "nothing in 1000 markets?" — they exist so discovery
is systematic, not eyeballed. Now run every cron tick. (Found 1 marginal arb this session: Multipli.fi
Jul-2027 0.615 > Oct-2027 0.495, +5.66pp net but >1y/thin.)

**Session capital actions (for the record):** built scripts/wrap_pusd.py (unlocks pUSD funding;
was locked out of venue); deployed 2-fade basket aliens-NO $10.70 + Greenland-NO $12.18; gate caught
GME-eBay as -EV (active hostile bid, P(YES)~18%); confirmed rest of universe broadly efficient
(consistency=none, macro tight, Iran cluster coherent). ~$22.50 left idle in Aave (no qualifying edge).

**Future idea (not yet actionable, low priority):** a dedicated behavioral-fade scanner that auto-finds
overpriced idiosyncratic longshots (YES in meme-premium range on near-impossible events), auto-runs the
catalyst gate, ranks by premium×APY, and flags idiosyncratic vs correlated tails. discover_markets +
manual gating works for now; only build if the basket grows enough to need it.

No other material findings.


---

## 2026-06-02 02:00 UTC — Cron tick

No-action tick. Guards all clean: uma_status_check 15 tracked / 0 disputes; check_marginal_apy 7 positions / 0 below hurdle; redeem-all 0/7 redeemable; arb scanners (monotonicity + consistency, now wired into step 6) found 0 real net-positive arbs. News flow = Iran/Israel/Hezbollah crisis headlines (fresh US-Iran strikes, Trump mediating Israel-Hezbollah) — relevant to pre-existing Iran cluster (regime-fall NO $28.25 = biggest book position, Pahlavi NO $10, Trump-out NO $10.56) but ongoing strikes are already priced, no regime collapse, no Tier-1 alert fired → monitor, no action (no info edge over headline-watchers per philosophy). PM book: 7 NO positions, cost $86.41 / MTM $89.45 / +$3.04 (+3.51%), max upside +16.1% to Dec-31. Aave idle ~$22 (no qualifying edge). No new entries (comprehensive scan + 2 fade deployments were ~4h ago this session).

---

## 2026-06-02 ~10:50 UTC — Investigation: mechanical favorite-longshot strategy (operator request)

Operator (telegram) asked to investigate mechanical/systematic trading, example: buy the >80% side
across all markets, reshift when less extreme. Built scripts/longshot_calibration_backtest.py — pulls
resolved binary PM markets (gamma closed=true, vol>=20k), reads decisive outcome, takes YES-token
CLOB price at (closedTime - lookback) as entry, buckets by favorite-side price, computes empirical
win-rate vs implied. Ran N=599 at 7d and 30d lookbacks.

RESULT — no robust favorite-longshot edge on PM (it's a sharp market):
  bucket   7d edge    30d edge
  0.50-60  -2.6 (ns)  +8.3 (1.9SE)
  0.60-70  +4.2 (ns)  +16.4 (2.9SE, likely artifact)
  0.70-80  +1.7 (ns)  -4.7 (ns)
  0.80-85  +4.0 (ns)  +5.2 (ns)   <- operator's "80/20"; within 1 SE = noise
  0.85-90  -5.7 (ns)  -4.9 (ns)
  0.90-95  -0.8       -0.3        <- calibrated
  0.95-98  -3.4       -3.5        <- CONSISTENT slight OVER-pricing of extreme favs (opposite of bias)
  0.98-99  +1.1       -0.1
  overall favorites won ~83%.

Conclusions:
1. Buying extreme favorites (>80%) = NO edge. All >=0.80 buckets within ~1 SE; PM favorites calibrated.
   Naive 'buy all extremes' would earn ~0 EV while loading the fat tail (win 15c/lose 85c) + correlation.
2. Only persistent directional signal: 0.95-0.98 favorites slightly OVERpriced (-3.4/-3.5pp, both lookbacks)
   = weak FADE-the-favorite / buy-the-2-5%-longshot hint — opposite of the idea, too weak + fat-tailed to trade.
3. 30d mid-favorite (0.60-0.70) +16pp is likely a fallback/selection artifact (markets younger than 30d
   default to early, less-informed prices) + high variance. Flagged for a cleaner follow-up (filter to
   markets >=Nd old), NOT traded.
4. STRATEGIC: my aliens/Greenland fades work as SPECIFIC behavioral/meme mispricings caught case-by-case
   by catalyst_check, NOT a generic favorite bias. So the thing worth mechanizing is the GATE (auto-detect
   overpriced idiosyncratic-tail longshots + filter), not blind favorite-buying. Truly mechanical riskless
   edge stays the arb scanners (monotonicity/consistency/cross-venue).

Caveats: recent-resolution sample (selection), single-snapshot entry, no fee/slippage, multiple-comparison
across 8 buckets. Directional, not definitive — but the broad calibration result is robust enough to
reject the naive strategy.

---

## 2026-06-02 ~11:25 UTC — Follow-up: the 30d mid-favorite "curiosity" is a confirmed artifact (operator asked to check)

Added --require-full-lookback to longshot_calibration_backtest.py (skip markets younger than the lookback
instead of falling back to their OPEN price). Re-ran 30d, N=353 clean:
  - 0.60-0.70 bucket: +16.4pp (artifact-prone) -> -5.6pp (clean). SIGNAL VANISHED.
  - 0.50-0.60: +8.3 -> +14.2 (N=19, SE 10.7, noise).
CONFIRMED: the +16pp "mid-favorite drift" was the open-price fallback artifact — short-lived markets open
near 0.50 and drift to the eventual winner; the fallback read that open price as a "30d-ago favorite,"
manufacturing fake drift. NOT a real edge, not tradeable.

Clean set shows a faint 0.90-0.95 hint (+5.1pp, ~2.7SE) but NOT trusted: small survivorship-selected
subsample (only >=30d-old markets), contradicts both the 7d (-0.8pp) and full-30d (-0.3pp) cuts for that
bucket, and ~24 bucket-tests across runs make a 2.7SE blip expected by chance. Chasing it = rabbit hole.

FINAL: PM is calibrated; no robust mechanical favorite-longshot edge survives scrutiny across cuts. The
real edges remain (a) gate-selected idiosyncratic meme-fades, (b) riskless arb scanners. Investigation closed.

---

## 2026-06-02 ~11:45 UTC — CORRECTION: favorite-longshot edge IS real at large N (operator: "run it all the way")

Earlier today I concluded "PM calibrated, no mechanical favorite edge" from N=600. That was UNDERPOWERED.
Operator pushed to run it all the way (cheap to check). Ran N=1513 (7d) + 747 (30d), clean (--require-full-lookback).

7d-before-resolution, clean, large-N:
  0.50-0.60  N=218  53.7% vs 54.6%  -1.0   (calibrated)
  0.60-0.70  N=193  61.1% vs 64.0%  -2.9   (~calibrated)
  0.70-0.80  N=198  71.7% vs 74.4%  -2.7   (~calibrated)
  0.80-0.85  N=80   85.0% vs 82.2%  +2.8   (noise, 0.7σ)
  0.85-0.90  N=91   89.0% vs 87.5%  +1.5   (noise)
  0.90-0.95  N=111  97.3% vs 92.5%  +4.8   (3.2σ)  <-- REAL
  0.95-0.98  N=156  99.4% vs 96.6%  +2.8   (4.7σ)  <-- REAL
  0.98-0.99  N=152  100% vs 98.9%   +1.1   (152/152; partly luck)

FINDING: classic favorite-longshot bias IS present on PM, but only visible at large N and CONCENTRATED in
the extreme-favorite zone (0.90-0.98), entered NEAR resolution (7d). The 2-5% longshot side carries a
persistent lottery premium -> the 95-98% favorite is underpriced by ~3pp. Survives Bonferroni (16 tests).
This is a structural/capital-efficiency risk premium (locking 96c for 7d to make 3c isn't worth it to most
capital, so near-certain favorites trade at a discount) -> exactly the bond-like-fade in philosophy edge-source-1,
now EMPIRICALLY VALIDATED + localized to the 0.90-0.98 / short-horizon sweet spot.

30d lookback: weaker/mixed (0.90-0.95 +3.7pp/1.9σ; 0.95-0.98 calibrated; mild favorites 0.50-0.70 strongly
NEGATIVE -10 to -12pp -> mild favorites 30d out are NOT reliable). => enter NEAR resolution, high-confidence only.

Caveats (tradeable but narrow): (1) fees/slippage ~1-1.5pp -> 0.90-0.95 nets ~+3pp, 0.95-0.98 thins to ~+1.8pp;
(2) fat tail: win ~3c / lose ~96c, a correlated cluster of upsets hurts -> needs diversification + small (fractional-
Kelly) sizing + the resolution-criteria (R-U) & tail-correlation filters; (3) require-full-lookback selection;
(4) 0.98-0.99 100%-won is partly luck. NOT a free lunch — a risk premium, which is why it persists.

ACTION: this validates + sharpens the existing bond-like-fade (my aliens/Greenland/Iran NO already live in
this zone). Refining philosophy edge-source-1 with the localization. A dedicated mechanical scanner (auto-find
0.90-0.97 favorites ~1-2wk out, filtered) is now worth building (revises earlier 'low priority') — but it's a
new strategy CLASS for auto-deployment, so flag for operator sign-off, don't unilaterally auto-trade.
Lesson: small-N noise hid a real 3-5σ effect; when a check is cheap, run it to adequate power before concluding.

---

## 2026-06-02 14:00 UTC — Cron tick

Guards clean: uma_status_check 15 tracked / 0 disputes; check_marginal_apy 7 positions / 0 below hurdle;
redeem-all 0/7. PM book MTM $89.27 (cost $86.41, +$2.86 / +3.31%); -$0.18 since 02:00, noise.
News: Iran nuclear-DEAL flavored (Grossi "next deal looks different", Trump "talks moving fast") —
mildly FAVORABLE to my Iran-cluster NOs (regime-fall NO $28, Pahlavi NO) since deal/de-escalation = status
quo = NO wins. No Tier-1, no action.

OPERATIONAL FIX shipped: the monotonicity arb scanner (wired into the routine yesterday) flagged a +37.5pp
"Propr launch a token" Jun-2027 vs Sep-2027 violation — but the Sep leg had $0 vol24hr = stale-midpoint stub,
not an executable arb (all 9 flagged violations were the same illiquid-2027-token-launch pattern: Propr,
Multipli, Concrete). Root cause: the scanner used gamma midpoints with no liquidity filter (unlike the
consistency scanner which validates against live CLOB). Added --min-leg-vol24 (default $500, require BOTH
legs to have real 24h volume). After the gate: 0 violations — confirming all were stubs. Routine scanner is
now trustworthy. Follow-up (backlog): a full live-CLOB-validation pass would be even more robust than the
vol filter (a market can have volume but still a stale midpoint vs real asks).

No new entries (comprehensive scan 09:27 found only out-of-mandate longshot legs; nothing changed in 4.5h).
Aave idle ~$22. Awaiting operator go on the favorite-fade mechanical scanner.

---

## 2026-06-02 ~15:05 UTC — favorite-fade scanner built + category-refined (operator: capture alpha, iterate, no permission needed)

Built scripts/favorite_fade_scan.py: finds liquid binary favorites trading (LIVE CLOB ask, not gamma
midpoint) in the validated 0.90-0.98 zone, short horizon, edge from the calibration curve net of slippage,
compute-bounded book-walks. Surfaces ranked buy-list; exec still via polyclaude_enter.py gates.

ITERATION — category-segmented backtest (--by-category, fav>=0.90, N=1277) to find WHERE the edge lives:
  other/meme    N=389  +1.9pp (4.8sigma)  <- most robust (aliens/GME-type idiosyncratic)
  politics/geo  N=76   +2.3pp (100% won, small-N)
  sports        N=70   +1.6pp (100% won)  <- positive even at heavy-favorite end (surprised me; my
                                              earlier sports_pm_scan only showed mid-market efficiency)
  crypto/price  N=115  +0.4pp (ns)        <- EFFICIENT, no edge (BTC-$72k "+4.4pp" was spurious)
=> scanner now excludes crypto/price + macro by default (--exclude-cats).

HONEST DEPLOY ASSESSMENT (not forcing activity): the edge is REAL but THIN (+1-3pp gross, ~+1pp net of
slippage) with a FAT TAIL (win a few c / lose ~the stake). Realizing it needs MANY diversified bets (LLN);
at ~$160 bankroll / ~$22 deployable + bridge/wrap friction, a handful of bets is variance-dominated and
friction-eaten. Current live candidates are: thin sports (friction/variance), Iran/Israel-cluster politics
(correlated w/ my book + R-U resolution risk — US-Iran-PEACE NO is the exact market type that cost 10%), or
thin Elon-tweet metas. None is a clean big-edge idiosyncratic deploy at this scale. So the scanner is
FORWARD-LOOKING INFRA: wired into cron step 6 (--min-edge-pp 3) to continuously surface candidates; deploy
when a BIG-edge idiosyncratic one appears (single-bet edge beats variance) or capital grows enough to
diversify. Deployment stays judgment-gated (catalyst_check for R-U + tail-correlation), never auto-trade.

Meta: the favorite-fade is fundamentally a SCALE strategy (small edge x many bets). At current capital the
discretionary big-mispricing fades (aliens/Greenland: ~13-15pp meme premia) are far better $/bet than the
mechanical thin-favorite fade. Keep both; lead with the big idiosyncratic mispricings while small.

---

## 2026-06-02 ~15:35 UTC — Non-PM venue scoping (operator request: Ostium / dYdX / Hyperliquid APIs?)

All three have APIs: Ostium (integrated, ostium_client.py); Hyperliquid (public REST, no-auth reads — pulled
live; trading via py SDK + wallet sig); dYdX v4 (public indexer REST + v4 trading client). 

BEST non-PM opportunity = DELTA-NEUTRAL PERP FUNDING HARVEST (cash-and-carry: short the perp + long the
spot on the same venue = directionally flat, collect funding). Live Hyperliquid funding (annualized) now:
  HYPE +36% (OI $1.5B, huge liq)   XMR +48% (OI $40M)   VVV +31%   [positive => longs pay shorts => SHORT perp + LONG spot collects]
  negative-funding (LONG perp + SHORT spot collects): TRX -174%, DOT -54%, many small alts (illiquid/squeezy).
HYPE is the standout: +36% market-neutral on the most-liquid HL asset, single-venue (HL has spot+perp), ~12x
Aave's 3% on idle capital. Ostium funding imbalances also large (BTC book 98% short -> longs paid; NDX/CL/
forex 90%+ long -> shorts paid) but directional unless cross-venue-hedged.

Caveats (NOT risk-free, NOT set-and-forget): funding flips negative (then you pay) -> active monitoring +
exit; spot-perp basis blowout -> perp-leg liquidation risk, needs margin buffer; venue/contract risk (HL is a
newer L1); spot-leg custody + token risk (HYPE). Market-neutral in DIRECTION, not in all risks.

Mandate fit: decentralized (no CEX/KYC) ✓, <1y ✓, market-neutral yield that SCALES (unlike the thin PM
favorite-fade). At ~$22 deployable the absolute $ is small, but as a yield HOME for the idle crypto sleeve
it crushes Aave. NEW venue + strategy -> DD-first per process (backlog 2026-05-08 venue-DD item: surface
findings before wallet creation / capital). NEXT: run the HL funding-harvest DD (mechanics, liq depth at my
size, historical funding stability, liquidation math, bridge path) + small pilot if it confirms.

---

## 2026-06-02 ~15:45 UTC — HL funding-harvest DD (gating step): snapshot oversold it

Pulled 21d Hyperliquid funding HISTORY (the snapshot can mislead):
  HYPE: mean +8.2% / median +11% APR, 83% of hours positive, range -83% to +140% (the +36% snapshot = spike)
  XMR:  mean +26% / median +11%, 97% positive (most persistent) — BUT no clean on-chain XMR spot to hedge
        within no-KYC/decentralized mandate => NOT executable delta-neutral. Out.
  VVV:  mean +11.3%, 81% positive.
Executable majors (HYPE/VVV; HL has spot) realistically harvest ~8-11% mean funding, NOT 36%.

VERDICT: funding harvest is real, market-neutral, and SCALABLE, but ~2-3x Aave (not 12x), and it carries new-
venue setup (HL bridge + trading SDK), ongoing monitoring (funding goes negative ~17-19% of hours -> you pay),
+ basis/liquidation/venue risk. At ~$22 deployable a ~5-8pp pickup over Aave = ~$1-2/yr for a big build +
monitoring burden -> setup/$ ratio does NOT justify it now. It's the right strategy to SCALE INTO as capital
grows, not a build-now at current size. DD saved; revisit at larger capital or a persistent + spot-hedgeable
high-funding setup. Reinforces: funding snapshots oversell — always check history before sizing (same family
as the gamma-midpoint and small-N-noise lessons: verify before trusting a single-point signal).

---

## 2026-06-02 ~15:55 UTC — Directional crypto DD: systematic trend has a real edge (operator probe)

Operator asked re directional crypto/RWA. Built scripts/crypto_momentum_backtest.py (HL daily candles,
900d, lookahead-safe SMA-crossover long/flat, costs). Two-part answer:
1. Directional on a VIEW = no edge (efficient liquid mkts; I have no forecast edge). Don't gamble.
2. Systematic medium-horizon TREND (SMA 40-50 long/flat) = real, robust-ish historical edge:
     BTC: Sharpe 0.93 vs 0.64 buy&hold; maxDD -26% vs -50%; CAGR 28% vs 21%
     ETH: Sharpe 0.99 vs 0.25; maxDD -44% vs -64%; CAGR +39% vs -6%
   Robustness sweep 30-80d: 40-60 is a PLATEAU on both BTC+ETH (not a lone SMA-50 spike) -> not pure overfit.
   Main value = DRAWDOWN AVOIDANCE (sidesteps sustained bear stretches, halved DDs). FAILED on SOL.

Caveats (why not deploy): single 2.5yr period (one cycle) -> needs OUT-OF-SAMPLE / walk-forward + longer
history (HL only has ~900d; use Binance klines for years); still directional (crypto-beta, -26 to -44% DD);
trend-following is crowded/decaying. At ~$22 capital the directional-beta variance is a real cost.

Notable: the trend signal RIGHT NOW (BTC/ETH in drawdown, likely below 40-50d SMA) reads FLAT = stay out of
crypto = exactly my current stance. Adopting trend wouldn't change today's position; its payoff is staying
out of further downside + re-entering on the next sustained uptrend.

VERDICT: promising directional candidate, more robust than my prior expected — validate walk-forward on
longer history before any capital; deploy (small) only if it holds out-of-sample. META: 'check don't dismiss'
has now corrected my too-quick 'no edge' prior TWICE (favorite-fade, momentum). Updating toward empirical
checks over dismissive priors — but balancing against the opposite trap (funding snapshot OVERSOLD; small-N
favorite-fade UNDERSOLD). Lesson: single-point signals mislead both ways; always pull the distribution/history.

---

## 2026-06-02 ~16:12 UTC — Trend walk-forward (5.5yr) REVERSES the 900d result: no directional alpha

Pulled 2001d (2020-2026, CryptoCompare) and ran the FIXED SMA-50 long/flat rule by calendar year:
  BTC full: trend ret 31% / Sharpe 0.92 / maxDD -58%  vs  buy&hold 27% / 0.70 / -77%
  ETH full: trend ret 26% / Sharpe 0.71 / maxDD -55%  vs  buy&hold 25% / 0.68 / -79%
By year: trend UNDERperforms strong bulls (2021 ETH +54% vs bh +399%; 2023-24 BTC gave up upside),
loses-less but still badly in choppy bears (2022 BTC -50%, Sharpe -2.24 — WORSE risk-adj than bh -1.28),
wins in flat/down years (2025, 2026). Regime-dependent.

VERDICT (supersedes the 2026-06-02 ~15:55 '900d promising' entry): over a FULL cycle, trend ~= buy&hold on
RETURN (ETH Sharpe 0.71 vs 0.68 = no edge). The 900d window (2023-26) FLATTERED trend. The only robust
benefit is ~20pp drawdown REDUCTION (-58% vs -77%) — a RISK OVERLAY for holding crypto, NOT alpha. And it's
moot for me: I have no directional forecast edge so I don't hold directional crypto -> no drawdown to reduce.
=> NO real directional crypto alpha (views=no edge; trend=no return edge full-cycle). Original prior was right.

META (important calibration): 'check don't dismiss' CONFIRMED the favorite-fade edge but the walk-forward
KILLED the momentum edge as a favorable-window artifact. Both directions of rigor matter: (1) check empirically
(don't dismiss on prior), AND (2) validate OUT-OF-SAMPLE / full-cycle before believing a favorable window.
Single-window backtests mislead (like funding snapshots + small-N). Always pull the full distribution/history.
crypto_momentum_backtest.py default window (900d) should not be trusted alone -> use multi-year + by-regime.

---

## 2026-06-03 02:00 UTC — Cron tick

No-action. Guards clean: UMA 15/0 disputes; marginal-APY 7/0 below hurdle; redeem 0/7; monotonicity 0
violations (vol-filter holding — no stub artifacts); consistency 0 real arb. PM book MTM $88.86 (cost
$86.41, +$2.45 / +2.83%; -$0.41 vs prior tick, noise). favorite_fade_scan surfaced 13 candidates (tennis
NO-fades +7pp, SC-governor, Elon-tweet) — NOT deployed: thin+fat-tailed, variance-dominated at ~$22 capital
(established 2026-06-02); forward-infra. No new in-mandate big mispricing.

NEWS / Iran watch: crisis intensifying BOTH ways — Rubio says Iran ready to discuss nuclear deal (de-escal,
favorable to my Iran-cluster NOs = status quo) AND US fired a missile at a tanker heading to Iran amid Hormuz
tension (escalation). Net: volatile but no regime-threatening development; no Tier-1 alert. Iran-cluster NOs
(regime-fall $28 = biggest book position, Pahlavi $10) price the ongoing tension already -> HOLD, no action.
WATCH THRESHOLD: re-evaluate the regime-fall NO + cluster only if escalation turns regime-threatening (direct
strikes on Iran leadership/territory or a leadership-change trigger), NOT on tanker/strait incidents.

---

## 2026-06-03 14:00 UTC — Cron tick

Guards clean: UMA 15/0; marginal-APY 7/0 below; redeem 0/7; monotonicity 0; consistency 0. MTM $88.85
(cost $86.41, +$2.44 / +2.82%; stable).

IRAN ESCALATION (news 09:56): "Kuwait airport hit by Iranian drones as US-Iran talks stall." Notable step-up
(regional strike + talks stalling, reversing the earlier deal-talk). Repricing check: regime-fall NO mark
0.875->0.865 (YES 12.5%->13.5%, +1pp) — MINOR/proportionate, market does NOT read it as a regime-threat.
Assessment HOLD: Iran attacking Kuwait != Iran's regime falling; external war often CONSOLIDATES a regime
(rally-round-flag). Mixed for the book: peace-deal NOs MORE likely to win (talks stalled = no deal); regime-
fall NO neutral-to-slightly-worse (+1pp YES). Still +3.3% MTM, comfortable.

WATCH ELEVATED with concrete triggers for the regime-fall NO ($28, biggest position): re-eval/TRIM if EITHER
(a) news of strikes ON Iran territory/leadership (the 2003-Iraq external-regime-change path — distinct from
Iran attacking others), OR (b) regime-fall NO mark drops below 0.80 (YES >20%, vs 13.5% now) = market pricing
real regime risk. Below those, HOLD (don't react to ongoing-crisis headlines; act on state-change — R-U lesson).
No action this tick.

---

## 2026-06-04 02:00 UTC — Cron tick

No-action. Guards clean: UMA 15/0; marginal-APY 7/0 below; redeem 0/7; monotonicity 0; consistency 0.
MTM $89.05 (cost $86.41, +$2.64 / +3.05%; stable). Iran: QUIET — no new news_watcher alert in ~12h
(daemon verified alive, log written 01:38Z, correctly suppressing non-material crisis-noise). Regime-fall
NO ~0.87 (YES ~13%), above the 0.80 trim trigger; cluster fine. No new in-mandate mispricing.
Session remains marathon-length; fresh session still recommended (see 2026-06-03 continuation-hallucination
incident — root-caused + memory'd; positions never affected).

---

## 2026-06-04 14:00 UTC — Cron tick

No-action. Guards clean: UMA 15/0; marginal-APY 7/0 below; redeem 0/7; monotonicity 0; consistency 0.
MTM $89.27 (cost $86.41, +$2.86 / +3.31%). Iran news (12:49): "US House votes to curb Trump on Iran war as
talks stall" — net FAVORABLE/neutral for the book: House curbing Trump's war powers makes US strikes ON Iran
(the regime-change path / my watch-trigger) LESS likely -> regime-fall NO safer; stalled talks help peace-deal
NOs. Regime-fall NO steady 0.865 (above 0.80 trigger), unmoved. Daemon confirmed alive (fired the 12:49 alert).

---

## 2026-06-04 ~16:50 UTC — Meta-reflection + repo-refinement recap

Repo-prune shipped this session (063e95b + 6743869): ~8000 lines cut — dead prompter subsystem removed;
journal/logs truncated to recent (full history in git); 3 scripts' hardcoded secret-dir wallet-path
defaults scrubbed -> `_paths.path("POLYCLAUDE_WALLET")`; leaked session-id + real-username paths redacted
from operator_start.sh. HEAD is clean, but those values PERSIST in git history — full removal needs
filter-repo + force-push (operator's call, flagged, not done unilaterally). Also fixed portfolio_kelly.py
--help crash (unescaped % in argparse help).

Reflection findings: (1) cleanup — pruned backlog Calendar of resolved past-dated reminders (05-09→05-31)
+ corrected stale ~Nd counts. Minor known-debt left as-is: `macro_pm_scan.py --with-consensus` is a
broken v1 flag (CME FedWatch JS-rendered → haiku hallucinates); already documented + run with
`--no-consensus`, not worth a fix while unused. (2) alpha — no genuine NEW source surfaced; not forcing
one. Live candidates already tracked in backlog (HL delta-neutral funding-harvest DD, crypto-trend OOS
walk-forward, event_monotonicity live-CLOB validation pass). Book quiet + healthy per today's ticks
(MTM +3.3%, Iran cluster stable, daemon alive). Calendar now anchors the 2026-06-30 methodology-experiment
conclusion (validates the reasoning-depth rule that governs when I spend tokens on skeptic+champion).

operator_start.sh carries the operator's local `--model sonnet`→opus runtime edit, preserved uncommitted.
Session is very long; fresh session still recommended.

---

## 2026-06-05 02:00 UTC — Cron tick

No-action (trading). Guards all CLEAN: UMA 15/0, marginal-APY 7/0 below hurdle, redeemable 0, monotonicity
0/202 events, consistency 0 real arb. MTM $89.30 (cost $86.41, +$2.89 / +3.35%); 7 NO positions, Ostium
flat. Watchlist 3 hits all IBKR-route (SOL/ARB/STX, multi-year → operator sleeve, not polyclaude). The
aliens-NO Kelly flag (-0.5pp / -$10.70) is the known static-Kelly-vs-Brownian-bridge artifact on a
late-stage bond-like NO → HOLD, not TRIM (per 2026-05-19 framework note). Prospecting surfaced candidates
(favorite_fade: South-Africa-win NO 7.3pp @0.90, Israel/Iran-airspace NOs; sports: Knicks NO +50% APY)
but none auto-cleared, and PM-sleeve deployable cash is ~$0.12 → no entry (correct). Fixed `decisions.py
summary` crash (KeyError 'confidence' on the 3 non-trade record types). Backlogged 8 overdue
decision-outcome backfills (do with authoritative data, not memory). Data gathered via a fresh subagent
(marathon-session anti-hallucination grounding). Fresh session still recommended.

---

## 2026-06-05 14:00 UTC — Cron tick

No-action (trading). All guards CLEAN (UMA 15/0, marginal-APY 7/0, redeemable 0, monotonicity 0/237,
consistency 0). MTM $89.25 (cost $86.41, +3.28%) — ~flat vs 02:00 (−$0.05); 7 NO positions, Ostium flat.
`decisions.py summary` confirmed fixed (runs clean post today's patch). aliens-NO Kelly −0.5pp = the same
known static-Kelly/Brownian-bridge artifact → HOLD. Prospecting: none cleared for entry (thin meme/geo
favorite-fades + Iran-correlated names; ~$0.12 PM deployable).

NEW watchlist hit: EIGEN $0.163 ≤ $0.18 trigger — IBKR-route (operator sleeve, NOT polyclaude capital).
Still mid-washout from the June-1 token unlock: −27%/7d, lower each of the last 3 days
($0.21→$0.18→$0.163). Per the trigger's own pre-set "wait for unlock washout" plan, NOT an entry yet
(falling knife). Surfaced to operator via Telegram (msg 427) with the grounded read + offer to set a
stabilization alert or run a longterm re-vet. Data gathered via a fresh subagent.

---

## 2026-06-06 02:00 UTC — Cron tick (Saturday)

No-action (trading). All guards CLEAN: UMA 15/0, marginal-APY 7/0, redeemable 0, consistency 0;
monotonicity 1 sub-bar hit (+0.66pp net on a thin Elon-tweet-count market, below action threshold). MTM
$89.71 (cost $86.41, +3.82%) — drifted up +$0.46 vs 14:00; 7 NO positions, Ostium flat. Watchlist: same 4
IBKR-route hits, EIGEN $0.164 unchanged (still mid-washout; not re-surfacing). aliens-NO Kelly −0.5pp =
standing static-Kelly/Brownian-bridge artifact → HOLD. Prospecting: none cleared (favorite-fades
Iran-correlated or thin; ~$0 deployable).

Weekly methodology (Saturday step 10): `prospective_resolve` = 13/20 resolved (7 open, ~June 30). Variant
ranking stable and CONFIRMING the retrospective N=30 finding: zero_shot leads (+0.348/$, 3 takes 100%),
more reasoning depth → lower per-$ (parallel_pair +0.129, unconscious_terse +0.092, adversarial_3round
+0.033). The out-of-sample (ground-truth-blind) result is validating the reasoning-depth rule that governs
when I escalate to skeptic+champion. Final analysis still gated on all-20 (~June 30).

Op note: `sports_pm_scan --with-consensus` (cron step 6) spawns claude-p-haiku per market (~30–120s each,
with a correct 120s timeout) — too slow for the delegated subagent's 90s cap, so the mid-market
bookie-delta signal was skipped this pass; immaterial at ~$0 deployable. NOT a bug (script handles
timeouts). For future delegated ticks: budget more time or run --no-consensus + note the gap. Tick
grounded via fresh subagent.
No new in-mandate mispricing. Session still marathon-length; fresh session recommended.

---

## 2026-06-06 14:00 UTC — Cron tick + scanner coverage-bug fix

No-action (trading). Guards CLEAN (UMA 15/0, marginal-APY 7/0, redeemable 0, monotonicity 0, consistency
0 real). MTM $89.83 (+3.95%), 7 NO positions, Ostium flat, EIGEN unchanged. No prospecting entry.

HIGH-LEVERAGE FINDING + FIX (verified, committed). The delegated consistency scan pulled only 100/5000
markets. Root cause: gamma-api hard-caps every page at 100 rows regardless of the `limit` param (verified
live: limit=500 → 100 on BOTH /markets and /events; offset pagination is clean). Scanners requesting
limit=500 were silently crippled two ways: (a) consistency_scan broke on the short first page → only ever
100 markets; (b) event_monotonicity / macro_pm_scan / sports_pm_scan used offset=page*500 stride, which on
a 100-row cap SKIPS 80% of records (rows 0-99, 500-599, 1000-1099…). Same class as the discover_markets
100→996 fix (2026-05-29); discover_markets + favorite_fade were already correct (limit=100).
FIX: limit=100 + offset stride page*100 (match the server cap) across consistency/monotonicity/macro/
sports; bumped monotonicity max_pages 10→15 for full event coverage. VERIFIED: consistency 100→5000
markets (8→1415 events); monotonicity 218→851 multi-market events inspected. Full re-scan on the
now-complete universe: 0 real arb, 0 monotonicity violation (every gamma-midpoint flag evaporates under
live CLOB asks — the known stub-bid pattern). No capital action today, but the riskless-arb + discovery
scanners now actually cover the universe they claim to (was 2-20%) → they'll catch a real
multi-leg/decomposition arb if one appears, instead of being blind to most of it. All 6 gamma scanners
checked; class fully swept. Tick grounded via fresh subagent.

---

## 2026-06-06 14:20 UTC — gamma-cap class sweep (completeness pass; corrects "fully swept" above)

A completeness grep (`offset*500` / `limit:500` across scripts/) found 3 MORE instances beyond the 4
scanners — including the most consequential ones:
- **catalyst_check.py** `_fetch_resolution_description` — the PRE-TRADE R-U gate. Was silently skipping the
  resolution-criteria lookup for any market outside the top ~600 by volume → degraded literal-criteria
  anchoring exactly for less-traded markets (where edges hide). This is the gate whose whole value is the
  98%→2.2% strict-criteria swing.
- **polyclaude_enter.py** `fetch_market_by_slug_or_question` — slug lookup (primary) is fine; the
  question-search FALLBACK had the offset*500 skip → a question-based entry could miss its target market.
- **limitless_arb_scan.py** `fetch_polymarket_universe` — limit=500 + break-on-<500 → only 100 markets.
All three fixed (limit=100 + contiguous stride / early-exit) and VERIFIED: limitless universe 100→3000;
catalyst_check + polyclaude_enter now resolve a rank~700 market the old gappy reach missed.
**methodology_stress_test.py** also has the pattern (lines ~74, ~744) but is DEFERRED — its prospective N=20
set is already snapshotted, so the in-flight experiment (13/20, ~June 30) is unaffected, and a fresh
universe-scrape change could confound it → backlogged for post-June-30.
NET: 7 gamma tools fixed (4 scanners + gate + entry + limitless), 2 already-correct (discover_markets,
favorite_fade), 1 deferred. Lesson: the completeness critic earned its keep — stopping at the 4 scanners
would have left the pre-trade gate + entry path silently broken.

---

## 2026-06-07 02:00 UTC — Cron tick (Sunday)

No-action (trading). All guards CLEAN: UMA 15/0, marginal-APY 7/0, redeemable 0, monotonicity 0,
consistency 0 real. MTM $89.75 (cost $86.41, +3.86%) — flat vs 14:00 (−$0.08); 7 NO, Ostium flat. Marks
all within ~1pp (aliens NO 0.855). EIGEN $0.167 (immaterial, still IBKR-route). aliens-NO Kelly −0.5pp =
standing artifact → HOLD. Prospecting: none cleared (~$0 deployable). decisions.py summary runs clean.

GAMMA-CAP FIX VALIDATED LIVE (full coverage now confirmed in the cron context): monotonicity 959 events
fetched / 766 multi-market inspected (was ~218 gappy); consistency 5000 markets / 1417 events / 148
candidates walked live → still 0 real arb (gamma midpoints evaporate under live CLOB asks, as always). The
fixes work and break nothing. Note: separate limitless_arb cron (01:31) flagged Reya FDV net_edge 6.17% but
verdict UNCERTAIN / 0 verified-identical → below bar, not actionable. Tick grounded via fresh subagent.
(The Sunday 16:00 world-state review is a separate cron — not this tick.)

---

## 2026-06-07 14:00 UTC — Cron tick (Sunday)

No-action; all guards CLEAN (UMA 15/0, marginal-APY 7/0, redeemable 0, monotonicity 0/829, consistency 0
real on 5000 mkts/1417 events). MTM $89.76 (+3.87%), flat vs 02:00; 7 NO positions, Ostium flat, marks all
<5pp wiggle (Trump-out 0.895, aliens 0.865), EIGEN $0.171 unchanged. No prospecting entry (~$0 deployable).
Grounded via fresh subagent. CADENCE NOTE: with the operator away (7 unanswered cron/Q pings) and the book
quiet, switching to journal-only on FLAT no-action ticks — Telegram reserved for actions / material moves /
decisions (decision-feed, not heartbeat-spam). Sent one terse heartbeat (msg 431) flagging the change.

---

## 2026-06-07 16:00 UTC — Sunday weekly long-term review

Rotated the 3 stalest world-state domains (critical-minerals 5-08, energy-power + geopolitics-security 5-10;
last-runs git-reconstructed since the log was truncated in the prune). HIGH themes surfaced: copper
structural deficit (FCX/COPX/TECK), uranium undervaluation (CCJ/URA/SPUT), oil supply shock/Hormuz
(CVX/COP, XOM tracked), memory-chip undersupply 2+yr (MU long / consumer-electronics short); + lithium
tightening (MED-HIGH, ALB/LIT). Vetted top 2 via longterm_check:
- CCJ 4/4 WATCH (↑ from 3.5/4 on 5-10 — thesis strengthened: McArthur River full production Jun-26, 1.9Blb
  deficit to 2045, 49% Westinghouse optionality; but 104x PE, current $114 = FAIR, entry $95-100, don't scale).
- FCX 2.5/4 PASS (copper at record/peak $63.27, 44.6x PE ~81% above mean, no downside cushion; entry $40-45
  on copper normalization or $50-55 macro pullback).
Watchlist updated: added FCX @ $45 trigger (NEW, ibkr_surface); CCJ trigger already @ $95 (matches today's
read). Trigger-hits this week (existing, all IBKR-route, persistent): SOL $64.85 / ARB $0.082 / STX $0.186 /
EIGEN $0.176 — all ≤ entry-max; EIGEN still mid-washout post-Jun-1 unlock (wait). All IBKR-surface (operator
sleeve), NO polyclaude capital. Telegram summary sent (msg 432). Discipline: 12+ candidates vetted across
rotations, all PASS/WATCH — valuations stretched cyclewide, no bottoms; wait for dip triggers, no chasing.
Domains/digest/longterm_check run via fresh subagent (grounded).

---

## 2026-06-08 02:00 UTC — Cron tick (Monday) + proactive Iran-cluster risk-check

No-action (trading). All guards CLEAN: UMA 15/0, marginal-APY 7/0, redeemable 0, monotonicity 0/795,
consistency 0 real (5000 mkts). MTM $89.73 (+3.84%), flat vs 14:00 06-07; 7 NO, Ostium flat, all marks <5pp.
EIGEN $0.184 — just ABOVE its $0.18 trigger (NOT a hit; correcting earlier "persistent EIGEN hit" — it's a
WATCH, not currently triggered). No prospecting entry (~$0 deployable).

PROACTIVE RISK-CHECK (substantive): active Israel/Iran escalation in short-dated June markets → ran
catalyst_check on our DOMINANT hold, the Iran-regime-fall NO (33.75 sh, cost $28.25, mark 0.870 = ~13% YES
implied). [Gate fix confirmed: fetched 1371 chars of literal criteria.] Central P(YES) = 6% (low 2 / high
14); breakdown 18% trigger × 25% loses-control × 70% new-govt ≈ 3.2%, adj to 6% for current instability.
The literal criteria require ACTUAL regime dissolution — strikes/war / Supreme-Leader succession (to son
Mojtaba) / coups that preserve core structures are ALL EXCLUDED; external strikes can rally-around-flag and
REDUCE collapse odds. Verdict: thesis INTACT — P(YES) 6% << 13% mark, so the stable mark is correct (not
lagging); the NO is mildly UNDER-priced (fair ~0.94). HOLD, no trim/exit. Only breach path: regime-ending
ground invasion or visible IRGC/security-force defection (neither imminent) → watch-item. CORRECTION: this
market resolves 2026-12-31 (end-2026, ~206d), NOT end-2027 as notes loosely said. Cluster note: Iran paths
anti-correlated (regime-fall would hurt this NO but help the peace NOs) — not a concentrated tail. Surfaced
to operator (msg 433). Tick + check grounded via fresh subagents.

---

## 2026-06-08 14:00 UTC — Cron tick (Monday)

No-action; all guards CLEAN (UMA 15/0, marginal-APY 7/0, redeemable 0, monotonicity 0/926, consistency 0
real). MTM $89.93 (+4.07%), slight positive drift vs 02:00; 7 NO, Ostium flat. IRAN WATCH (from the 02:00
escalation): holds STABLE — regime-fall NO 0.875 (+0.5pp), Pahlavi NO 0.947 (flat), both well inside the
5pp re-check trigger, UMA clean on both. Corroborated by the proximate "regime fall by June 30" market
sitting at YES 0.017 (NO 0.983) — the market itself confirms escalation has NOT raised regime-fall odds,
consistent with the 02:00 catalyst_check (6%). Thesis intact → HOLD. EIGEN $0.184 (still above $0.18, not a
hit); FCX no hit; no new watchlist hit. No prospecting entry (~$0 deployable). No Telegram (flat / no
material move, per the cadence; the 02:00 Iran assessment msg 433 stands — absence of a ping = nothing
breached).
Op note: the fixed consistency_scan now pulls 5000 mkts so it runs ~150s (was fast at 100); gave the
delegated subagent 90s → timed out then passed on a 150s retry. Budget ~180s for consistency_scan in future
delegated ticks. Grounded via fresh subagent.

---

## 2026-06-09 02:00 UTC — Cron tick (Tuesday) + ALB trigger-hit re-vet

No-action on the PM book; all guards CLEAN (UMA 15/0, marginal-APY 7/0, redeemable 0, monotonicity 0 action
[1 sub-bar -1.14pp], consistency 0 real on 5000 mkts). MTM $89.80 (+3.92%), ~flat; 7 NO, Ostium flat. Iran
legs stable (regime-fall NO 0.875 flat, Pahlavi 0.946 -0.1pp; the proximate "regime fall by June 30" market
at YES 0.015 keeps corroborating the hold).

NEW: watchlist trigger hit — ALB (Albemarle/lithium) $149.84 ≤ $150 band, after a ~13% weekly drop. Re-vetted
via longterm_check: UPGRADED 3/4 → 3.5/4 WATCH. Margin-of-safety WEAK→OK (net debt $3.2B→$1.9B, 1.0x lev,
$2.7B liquidity, fwd P/E 13.6x). CRUX condition MET: lithium recovered ~$20-26/kg LCE (>$20/kg threshold);
Q1-26 EPS $2.95 +127% beat, rev +33%, market flipping surplus→deficit. So BOTH revised-entry conditions
(price $140-150 AND $20+/kg) satisfied; ALB at favorable low end of band. Still WATCH not high-conviction
ENTER (tool: enter-on-weakness; reserve full size for spot >$22/kg or ESS-capex/estimate catalyst). IBKR-route
(operator sleeve, NOT polyclaude capital) → surfaced to operator (msg 434). watchlist_triggers: ALB entry_max
150→140 (re-alert add-lower tranche), revised 06-09. Downside: lithium reverts $12-15/kg → 60-70% EBITDA cut
(~5% thesis-broken, fortress B/S). Data note: longterm_check internally used a stale $164.65; real price
$149.84 (yfinance + the live trigger). Tick + re-vet grounded via fresh subagents.

---

## 2026-06-09 14:00 UTC — Cron tick (Tuesday)

No-action; all guards CLEAN (UMA 15/0, marginal-APY 7/0, redeemable 0, monotonicity 0 action [1 sub-bar
-1.82pp], consistency 0 real on 5000 mkts). MTM $89.75 (+3.86%), flat vs 02:00; 7 NO, Ostium flat. Iran legs
flat/stable (regime-fall NO 0.875, Pahlavi 0.946). Only mark move: Satoshi NO -0.7pp (within bar). ALB did
NOT dip to ≤$140 (the lowered trigger is working as intended — no noisy re-flag). No new watchlist hit, no
prospecting entry. Journal-only per flat-tick cadence (no Telegram). Grounded via fresh subagent.
## 2026-06-10 ~02:00 UTC — Wednesday 02:00 cron tick: 2 scale-ups executed, bankroll blindness fixed, weekly P&L written

ACTION tick (first trades since Jun 5). Delegated gathering: guards CLEAN (UMA 15/0, marginal-APY 7/0,
redeemable 0/7, monotonicity 0/890, consistency 0 real on 5000 mkts), Ostium 0, no >5pp moves, MTM flat
$89.74 pre-trade. 2 MATERIAL news alerts (Iran downed US Army helicopter near Hormuz Jun 9, Trump vowing
response) on regime-fall + Pahlavi NOs → fresh catalyst_check on regime-fall: P(YES) central 5.5% (2.5–10%)
vs mark 12.5% — INTACT/HOLD, consistent with Jun-8 read (6%); breach paths still regime-ending-invasion /
IRGC-defection only. Marks unmoved 0.875/0.946.

**Bankroll correction (mistake owned):** "~$22 idle in Aave" repeated since Jun 5 was WRONG — direct aToken
reads: $53.55 Aave Polygon (PM sleeve) + $17.59 Arb + $4.54 Base = $75.68 idle. Root cause: wallet_status/
crypto_status never queried aTokens/pUSD → delegated ticks blind to the idle sleeve. FIXED at source (both
scripts now print aUSDC + pUSD lines; verified live). True bankroll ~$172 vs $170 kickoff = R-U loss fully
recouped.

**Peace-deal-Jun-15 NO fade: evaluated, REJECTED at gate.** favorite_fade said +3.4pp; catalyst_check said
P(YES) 12% central (5–22%) vs market 4.5% → negative edge at every point of the range. Scanner-artifact
killed by the mandatory gate.

**Scale-up batch (skeptic+champion gated, both >$10-rule and pairing memory honored):**
- Trump-out NO +$14.40 @ 0.90 (16 sh, tx 0xb388..4306, DEC-0032). Pair synthesis: corrected P(YES) ~3%
  central (haiku's 0.3% death tail was 5–7x low — Trump turns 80 Jun 14; SSA-halved 1.5–2.2%); calendar
  edge structural (Dem House flip seats 2027-01-03 AFTER 2026-12-31 resolution). Size CAP-BOUND at 15%/
  ticket (ticket now $24.96 = 14.7%), not Kelly's +$25.63 — skeptic's catch. Skeptic's defer-for-dip
  overruled (158k bid at 0.89 = dip-fill is adverse selection).
- Greenland NO +$6.96 @ 0.87 (8 sh, tx 0x0cdc..f9e8, DEC-0033). Fresh gate: P(YES) 2.5% (1–6%), 4-step
  conjunction; +5.5pp robust at pessimistic bound; idiosyncratic tail.
- Funding: $23 Aave-Polygon withdraw (tx 0xf432..) → pUSD wrap (tx a5fe..). pUSD residual $1.81.
- Book post-trade: 7 NOs, cost $107.77, MTM $110.98 (+2.98%), max payout $124.35. Aave left: $52.68.

**Also:** priors file trued (trump-out cluster_frac 0.05→0.18 war-linkage per skeptic; greenland/satoshi
entries added; resolved markets pruned). Weekly P&L written (23d overdue — cadence slip logged as mistake).
Doc-drift flag for operator: philosophy max-5 vs 7-position book (pre-existing; adds are count-neutral).
Watchlist: SOL/ARB/STX persistent IBKR hits only (ARB DAO vote Jun 16). Satoshi NO: no adds despite Kelly
deficit (subjective-resolution R-U class — now codified in priors).

## 2026-06-10 ~03:10 UTC — continuation: 3 backlog items shipped + 8 decision backfills applied (one books RESTATEMENT)

Infra (all backlog-sanctioned, bounded): (1) `scripts/bankroll.py` — single authoritative bankroll
total with WARNINGs for unvalued components; verified $171.87 (+1.1% vs $170 kickoff); wired into
daily_checkin step 1 (second instance of the hand-assembled-aggregate failure class was this morning's
$22-vs-$75.68). (2) polyclaude_enter.py existing-exposure guard — live data-api check by conditionId,
warns with combined-ticket-vs-15%-cap math (DEC-0029 lesson codified); verified live on held trump-out.
(3) Backlog groomed: bankroll + exposure-guard + stale wrap_pusd entries closed. Also fixed decisions.py
update --help crash (unescaped % — same class as portfolio_kelly's).

**Decision backfills: all 8 applied (DEC-0008/10/11/12/14/24/26/27), 0 overdue remain.** Delegated
read-only gathering against primary sources (gamma resolutions, journal git-history, Ostium subgraph);
parent re-verified the load-bearing row directly before writing.

**BOOKS RESTATEMENT (material to records, not balance):** DEC-0026 had booked the NDX short close as
"TP +$1.96"; the subgraph shows a STOP-LOSS on 2026-05-14 00:30Z at $29,564 (+8.02% adverse), payout
$2.945284 = realized −$1.95. Sign error (~$3.91) sat 3+ weeks, propagated into the 05-18 journal +
pnl_weekly (now visibly corrected, not silently rewritten). Error mechanism: booked from a trade-count
diff + ASSUMED direction/level. Rule going forward (DEC-0026 lesson): no perp P&L written without the
subgraph order record (orderAction/profitPercent/amountSentToTrader). Corrected cumulative realized
since kickoff ≈ −$0.4 post-May-31 (not "break-even"); live bankroll unaffected ($171.87 reads balances).
Also restated: SPX was a MANUAL close May 28 (+$1.07 net, not "TP ~May 27 +$1.17"); the SPX/NDX pair
netted −$0.88 (dispersion view inverted). DEC-0014 lesson worth keeping: when a skip is motivated by the
skeptic's tail scenario, record THAT as the prediction — the R-U skip's stated "resolves NO" was wrong
while the skip itself was right for the stated reason.

## 2026-06-10 ~03:55 UTC — meta-reflection: 3 bounded fixes from tonight's frictions (none forced)

All three findings came from real friction in tonight's session, not hunting: (1) `clob_v2.py
redeem-all --dry-run` added + verified (0/7) — the gathering subagent had to hand-roll a data-api
fallback because the real command is state-changing; delegated ticks can now check redeemables safely.
(2) `ostium_state_diff.py` now auto-prints the authoritative subgraph order rows (orderAction/profit%/
amountSentToTrader, executed since prior tick) on any detected close — kills the DEC-0026 error
mechanism (count-diff + assumed direction = the −$1.95-booked-as-+$1.96 sign error) at the source;
forced-close test correctly surfaced all 3 historical rows incl. the NDX StopLoss. (3) CLOSED header on
notes/recoup_campaign.md — every continuation check was re-deriving "it's closed"; now it says so.

Backlogged (not unilateral): philosophy-doc refresh pass pending the operator's max-5 ruling (also
covers the stale "$70 of capital" on line 14). Alpha-source review: nothing new since the last
reflection — fade+gate working (book +2.98%), arb scanners persistently 0 (likely arbed out at our
scale; scans stay because they're cheap), favorite-fade needs near-resolution candidates the current
long-dated book doesn't generate. The scanner-vs-gate disagreement on peace-deal-Jun-15 (+3.4 vs −8pp)
is a known-class artifact, already journaled; the mandatory gate is the control, no build needed.

## 2026-06-10 ~12:40 UTC — DOCTRINE REWRITE (operator directive): pure expected-return maximization

Operator (local session): "revise the entire direction-setting docs to purely enforce expected return
maximization. There are no other hard rules except for the ones downstream from that one." Executed as
DEC-0034:

- **strategy/00_philosophy.md fully rewritten** (212 → ~210 lines but restructured): §1 objective =
  expected log growth (the Kelly derivation is what makes ER-max ≠ all-in-on-best-EV); §2 operator
  boundary conditions (legal, no-CEX/KYC, <1y horizon, public repo) separated from strategy — they're
  the feasible set; §3 live edge sources ranked by evidence; §4 entry pipeline with each gate as an EV
  term + honest enforcement map; §5 sizing/exits (Kelly+ρ, $-caps as model-error guardrail PARAMETERS,
  BB-vs-Kelly); §6 information-process rules; §7 risk pricing; §8 reporting + the 2027-04-25 eval
  baselines.
- **DELETED: max-5 count cap** — no ER derivation (diversification across independent gated edges raises
  growth; monitoring automated; binding limits are 15%/30% $-caps + $5 floor). Resolves the doc-vs-book
  drift without an arbitrary new number. Re-derive trigger: ~15+ positions.
- **REPLACED: "mechanical-resolution only" ban → priced UMA-loose haircut** (0.7×strict + 0.3×loose,
  modulated by the longest-dated sibling's YES; unquantifiable → small or skip). The ban forfeited +EV
  that survives the haircut; the book already held a rational priced exception (Satoshi small).
- **01_horizon_split.md folded in + deleted** (horizon boundary → §2; idle-home same-chain rule → §4.6;
  eval baselines → §8; two-sleeve history → git).
- **Adversarial review pass** (1 reviewer on the diff; decision itself was operator's, so no
  pair needed): caught a BLOCKER — my draft claimed polyclaude_enter "enforces #2–#5 mechanically" when
  the catalyst gate silently skips on --my-p and the UMA haircut is analyst process (exact DEC-0016
  failure mode). Fixed with an honest enforcement map. + 5 reference fixes (debate-moderator rules
  restored, eval baselines restored, term-structure modulation clause, recoup_campaign + backlog
  supersession notes, polyclaude_enter's stale "line 43" pointer).
- **Transparency flag for operator:** old doc-body said "Kelly/4 default"; the tools have run
  half-Kelly (quarter for fuzzy) since May. Rewrite resolves in the tools' favor — practice unchanged,
  documented default doubled.
- daily_checkin.sh step-6 filter text updated to match. decisions.py: DEC-0034 (prediction: no
  count-cap friction, no regression to banned-category heuristics, no UMA-class loss attributable to
  the ban removal; eval 2026-09-10).

## 2026-06-10 ~13:55 UTC — meta-reflection: bankroll-figure plumbing (one genuine finding)

Post-doctrine residue, the one real broken assumption left: doctrine names bankroll.py the
authoritative number, but polyclaude_enter.py + portfolio_kelly.py both carried static
--bankroll defaults of 170 → silent Kelly mis-sizing the moment the bankroll drifts. Fixed:
bankroll.py now writes notes/.bankroll_cache.json (total + timestamp); both sizing tools default
to the cached total when fresh (<24h, with an age-stamped stderr line), warn + fall back to 170
otherwise. Verified end-to-end: cache $172.22 → kelly scales by 172.22/269.07, enter's 15% cap
= $25.83 live. Explicit --bankroll still overrides everywhere.

No alpha-source findings forced: the doctrine change IS the new surface (subjective-resolution
markets priced not banned; no count cap) and the 14:00 tick exercises it through the normal funnel.
