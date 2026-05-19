# Polyclaude Backlog

Operator-maintained list of pending items. One line per item. Date-tagged. Closed items are deleted (git history preserves).

Reviewed at end of every turn + by the cron tick (step 4: decision tracker review).

---

## Active

> **End-of-turn discipline (2026-05-08+).** If the current thread isn't fully resolved, run:
> ```bash
> ./scripts/operator_followup.sh "anything else on <topic>?" 20
> ```
> The auto-followup fires after 20 min and re-injects via `inject_prompt.sh`. When the thread is fully resolved, run `./scripts/cancel_followup.sh` to stop the loop. Periodic 6/10/18/22 UTC cron checks ("anything else to take care of?") catch anything I miss between turns.

- ~~**2026-05-08** — Cluster cap formal skeptic+champion review (user-authorized).~~ **DONE 2026-05-08 ~18:30 UTC, journal entry above.** Conclusion: KEEP existing 30%-of-bankroll topic-cluster rule. Iran cluster at 19.8% bankroll ($33.71 / $51 cap), with $17.29 headroom. Within-cluster diversification is genuine (4 positions resolve on differentiated factors across peace-deal/regime-fall/Pahlavi-conditional). Topic-level cap captures correlated-drawdown risk in tail scenarios; doesn't over-constrain because it's $-cap not count-cap. Refinement banked: when adding a 5th Iran position, prefer a different primary resolution factor (e.g., uranium-transfer, US-invade) than existing peace-deal/regime-fall holds.
- **2026-05-08** — Non-PM venue DD: Drift / Kalshi / Hyperliquid (user-authorized). Multi-hour structural research; surface findings before any wallet creation / capital deployment.

- ~~**2026-05-08** — Long-term watchlist iteration (weekly)... `catalyst_check.py` adaptation needed for multi-year-horizon thesis-checking.~~ **DONE 2026-05-08 ~21:00 UTC**: shipped `scripts/longterm_check.py` (commit `77ddfed` + `e0c45e9`). Validated end-to-end across 12 candidates (10 watchlist seeds + Drift + Hyperliquid for venue DD). ALL verdicts WATCH/FOLLOW-UP, none ENTER NOW. Pattern: SanDisk PATTERN real but visible candidates today are mid-cycle. Weekly iteration cadence still pending as ongoing process — first weekly review Sunday May 17.

- ~~**2026-05-08** — `scripts/watchlist_monitor.py`~~ **DONE 2026-05-08 ~22:00 UTC**. Reads `notes/watchlist_triggers.json` (12 candidates seeded from longterm_watchlist verdicts). Pulls live prices: CoinGecko for crypto (SOL/ARB/ONDO/STX), yfinance for equities (MU/CEG/PLTR/AFMJF/LEU/TWST/IVN.TO/ALB). Smoke test: 12/12 fetched, 0 hits today. Wired into daily_checkin.sh step 3 with `--hits-only` flag. ALB closest to trigger (~13% above $180 entry).

- **2026-05-08** — Hyperliquid HIP-4 vs Polymarket arb scan. Discovered during venue DD: Hyperliquid launched zero-fee outcome markets targeting Polymarket. Same questions, potentially different prices = arb opportunity. Extend the `scripts/limitless_arb_scan.py` pattern to Hyperliquid (different venue, same logic). Bounded ~60 LOC. Once shipped, the cross-venue scan auto-surfaces opportunities to operator. Defer until HIP-4 has meaningful TVL (currently early days; not yet at scan-worthy depth).

- **2026-05-08** — Wider net for longterm watchlist seeds (next batch). Less-obvious categories where the cycle bottom may not yet be priced: SiC / advanced packaging (Wolfspeed), lithium cycle bottom (Albemarle), defense-tech sub-sectors (Kratos, AeroVironment, Anduril secondaries), space economy (Rocket Lab, AST SpaceMobile), DeFi blue chips at depressed multiples (UNI / AAVE / MKR), BTC mining infra (Cipher Mining, Hut 8). Run `longterm_check.py` on each. Goal: find candidates that DO trigger ENTER NOW — the visible names today don't.
- ~~**2026-05-08** — `scripts/world_state_digest.py` v1 shipped + Sunday cron wired.~~ **DONE 2026-05-08 ~21:40 UTC, commit `e1d52e1`**. notes/primary_sources.md (~46 curated factual URLs across 9 domains) + scripts/world_state_digest.py + Sunday 16:00 UTC cron entry rotating 2-3 domains/week. V1 smoke test on critical-minerals surfaced 6 themes including 2 HIGH-conf (lithium structural deficit, heavy-REE scarcity). Lesson source: 2026-05-08 user articulation on bare-facts/first-principles edge over retail narrative-compression layer.
- ~~**2026-05-08** — `discover_markets.py` hardcodes hurdle `HURDLE_APY = 0.0415`...~~ **DONE earlier 2026-05-08** (now 0.034 default + `--hurdle-apy` CLI override at line 25/250).
- ~~**2026-05-08** — `discover_markets.py` 7-day floor on hurdle filter...~~ **DONE earlier 2026-05-08** (now `HURDLE_DAYS_FLOOR_DEFAULT = 3` at line 32).
- **2026-05-08** — Bridge $20-30 from Aave Arbitrum → Polygon (Across) → wrap to pUSD to restore the Polymarket reserve buffer (currently $0.39 actionable post-DEC-0015). ~~Not urgent if no immediate next trade.~~ Partially done 2026-05-08 ~14:30 UTC: bridged $19.99 USDC Arb→Polygon, transferred crypto→polymarket sleeve. Remaining hop: native USDC → USDC.e (DEX swap on Polygon) → wrap to pUSD. Deferred swap until a trade lines up — sunk-cost friction is now $0.45, marginal swap cost ~$0.50.

- ~~**2026-05-08** — `scripts/across_bridge.py`: when bridging to Polygon, prefer `--token USDC.e`...~~ **DONE 2026-05-08, commit pending.** Added `--token-out` flag (default = same as `--token`); --token-out USDC.e for Polygon destination lands as bridged-USDC-variant directly, bypassing the USDC→USDC.e swap step.

- ~~**2026-05-08** — `scripts/across_bridge.py`: support `--recipient` flag...~~ **DONE 2026-05-08, commit pending.** Added `--recipient` flag (default = depositor address). Allows cross-wallet bridging — e.g. crypto sleeve withdraws Aave, bridges with `--recipient=<polymarket-sleeve-addr>`, lands as deployable Polymarket buffer with no extra ERC20 hop.

- ~~**2026-05-08** — Re-evaluate DEC-0003 (US confirm aliens before 2027 NO @ entry 0.80, current mark 0.815).~~ **DONE 2026-05-08 ~16:00 UTC.** Ran `catalyst_check.py` (see `notes/catalyst_log.md`). Findings: 2 HIGH-impact catalysts in the window — (1) 2026-08-18 Trump-EO 300-day declassification deadline; (2) 2026-10-31 annual DNI UAP report. Central P(YES) = 16% vs market 18.5% YES = NO has small positive edge (~$0.45 EV on $9 cost over 237d, ~7.7% APY). **Decision: HOLD.** Add Aug 18 to calendar as reassessment trigger — if market YES drifts up materially toward the deadline, reconsider close.

- ~~**2026-05-08** — Add to `strategy/00_philosophy.md` edge-source-1 ("longshot fade"): explicit rule that bond-like fades require 5-minute web search for window-specific catalysts BEFORE sizing.~~ **DONE 2026-05-08, commit `6c9d171`** — philosophy updated with mandatory catalyst_check.py pre-trade gate. discover_markets.py also got `--check-catalysts N` flag for auto-prefilter on hurdle-clearance candidates.

- ~~**2026-05-08** — Cron-tick auto-check for marginal-APY-below-hurdle on held positions.~~ **DONE 2026-05-08, commit pending.** `scripts/check_marginal_apy.py` shipped — pulls from data-api, computes `(1-mark)/mark × 365/days`, flags CLOSE_CANDIDATEs vs configurable hurdle (default 3.4% Aave Base). Wired into `scripts/daily_checkin.sh` cron prompt step 3 as a mandatory check. Smoke-tested: all 9 current positions clear; if Jesus 2027 NO (closed earlier) hadn't been closed, it would've been the only flag.

- ~~**2026-05-08** — `scripts/catalyst_check.py` prompt enhancement: for multi-conditional questions ("Will X happen by date" where X = "Y AND Z"), require haiku to show the multiplicative breakdown explicitly.~~ **DONE 2026-05-08, commit `11e89bb`.**

- ~~**2026-05-08** — `scripts/catalyst_check.py` enhancement: auto-fetch the market's resolution description from gamma-api...~~ **DONE 2026-05-08, commit pending.** Implemented `_fetch_resolution_description(question)` — searches gamma-api active markets for exact-match question, returns description or None. Prompt template now includes a "LITERAL RESOLUTION CRITERIA" block when fetch succeeds. Validated end-to-end: re-running US-invade-Iran NO check shifted central P(YES) from 98% (loose framing) → 2.2% (strict criteria with multiplicative breakdown). Same query, 95pp swing. Tool now anchors on oracle language, not media framing. The skip decision on US-invade-Iran was preserved (UMA-interpretation prior unknown), but for future bond-like fades the tool will correctly distinguish strict vs loose interpretations.
- **2026-05-08** — `news_watcher.py` dedup-by-title-hash within 24h window. Currently dedups by GUID, so same WaPo-syndicated story across feeds fires N alerts (saw 9× of "Trump shelved Project Freedom"). ~30 LOC. Low priority — Tier-2 only, no false-positive emergency response.
- **2026-05-15** — Trump-Xi summit watch (today's "pragmatic on Iran" framing). If a US-Iran framework emerges via China mediation over next 16 days (before May-31), May-31 NO at mark 0.905 is at risk. Daily check via web search for "Trump Iran agreement signed" + monitor mark drift. If May-31 mark drops below 0.83 (>5pp), re-evaluate via catalyst_check.py — consider early close if mark + UMA-resolution-criteria risk materially raises P(YES).
- **2026-05-15** — Event-monotonicity arb scanner. Polymarket has multi-market EVENT containers (e.g. /event/us-x-iran-permanent-peace-deal-by/ with child markets for may-11/may-15/may-31/june-30/etc.). Same question across monotonic dates SHOULD have P(YES_t1) ≤ P(YES_t2) when t1 ≤ t2. Operator flagged 2026-05-15 UI glitch transiently showed June-30 priced lower than May-15 (cache stale, not real). But a real monotonicity violation would be pure decomposition arb. Extend limitless_arb_scan to query gamma-api /events endpoint for event children + check monotonicity. Bounded ~2h build. Captures rare arb + serves as defensive UI-cache-check.
- ~~**2026-05-09** — `news_watcher.py` tier-2 agent-filter precision: enhance CRITICAL-tag path to WebFetch article body BEFORE tagging.~~ **DONE 2026-05-17, commit 9223226.** Added `_fetch_article_body()` (httpx + bs4 paragraph extraction, 15s timeout, fail-OPEN) + `_revalidate_critical_impacts()` (second haiku pass against body; CONFIRM/MATERIAL/MINOR/NONE verdict). Only fires on CRITICAL impacts (MINOR/MATERIAL pass through to keep cost bounded). Daemon restarted PID 577758.

## Calendar

- **2026-05-09** (~tomorrow): Russia Victory Day. Catalyst for DEC-0014 re-eval window.
- **2026-05-10** (~2d): Atletico vs Celta Vigo (home) — DEC-0008.
- **2026-05-13** (~5d): Osasuna vs Atletico (away) — DEC-0008.
- **2026-05-14** (~6d): Eurovision Semi-Final 2 — Latvia must qualify (DEC-0007 gating). Same day, **Trump-Xi summit** with Iran a central agenda item — major catalyst for DEC-0006 (Iran-peace May 31) and DEC-0015 (Iran-peace May 15). Post-summit market repricing likely.
- **2026-05-15** (~7d): DEC-0015 resolves (Iran-peace May 15 NO).
- **2026-05-16** (~8d): Eurovision Grand Final — DEC-0007 resolves.
- **2026-05-17** (~9d): Atletico vs Girona (home) — DEC-0008.
- **2026-05-24** (~16d): Villarreal vs Atletico (away, final La Liga matchday) — DEC-0008 effectively resolves.
- **2026-05-25** (~17d): DEC-0008 Atletico La Liga formal resolve.
- **2026-05-31** (~23d): DEC-0006 Iran-peace May 31 NO resolves.
- **2026-06-24** (~47d): Trump ceasefire-extension expiration — Iran cluster reassessment trigger.
- **2026-07-27** (~80d): EU sanctions on Iran review — Iran cluster reassessment.
- **2026-08-18** (~102d): Trump UAP-EO 300-day declassification deadline. Reassessment trigger for DEC-0003.
- **2026-10-31** (~176d): Annual DNI UAP report deadline. Final pre-resolution catalyst for DEC-0003.
- **2026-11-03** (~179d): US midterm elections. Catalyst for DEC-0004 (Trump-out NO) — even if Dems take House, Senate conviction implausible.
- **2026-05-10** (~2d): DEC-0014 Russia-Ukraine NO re-eval window opens. Plan from May 1 skip: re-evaluate at NO 0.95+ once Victory Day passes without framework announcement.
- **2026-05-15** (~7d): DEC-0015 resolves. Iran-peace-by-May-15 NO.
- **2026-05-16** (~8d): DEC-0007 Latvia Eurovision resolves.
- **2026-05-25** (~17d): DEC-0008 Atletico La Liga resolves (~).
- **2026-05-31** (~23d): DEC-0006 Iran-peace-by-May-31 NO resolves.

## Recently closed (last 7d, for context — older deletes silently)

- 2026-05-08: DEC-0015 opened (Iran-peace-May-15 NO @ $0.81, $9.72 cost, 12 shares).
- 2026-05-08: User-authorized capital reframe — found 3 compounding errors (cluster cap on bankroll not sleeve, hardcoded hurdle stale, 7d floor suppressing catalysts).
- 2026-05-07: Peer-detection deadlock fixed (commit 1e346e1 — bash guard in daily_checkin.sh).
- 2026-05-07: Prompter authorship-laundering rules added (commit 863f9ce).
- 2026-05-07: News-watcher 'aave hack' keyword tightened (commit 75ba0c5).
- 2026-05-07: Repo cleanup — journal split, stale memos deleted (commit acaea5d).
- 2026-05-07: Operator clock-anchor hook in `~/.claude/settings.json`.
- ~~**2026-05-17** — Auto-re-vet on watchlist trigger fire.~~ **DONE 2026-05-18, commit pending.** Pattern confirmed 3-of-3 (CEG/LEU/CCJ) needed manual fresh longterm_check + revised trigger after static fire. Codify: on hit, watchlist_monitor.py auto-spawns longterm_check, posts verdict (PASS/WATCH/ENTER) to Telegram, optionally suggests revised entry_max. NVDA was just added at $200 — when fires, this would auto-vet. Bounded ~45min. Saves ~10min × weekly. Modest compounding.

- **2026-05-18** — **Ostium SPX LONG pair-trade unraveled.** DEC-0026 closed the NDX SHORT leg (TP at -7.99% NDX, +$1.96 est). Remaining SPX LONG (DEC-0011, trade 1848511) is now naked — pair-trade thesis ("delta-neutral on US-equity-vs-tech dispersion") is invalidated. Three operator-decision paths: (a) close SPX LONG now to lock pair-trade realization (whole pair is net positive given NDX TP), (b) re-open NDX SHORT to re-establish delta-neutral pair-trade, (c) hold SPX LONG as a directional bet (no current thesis). Position size is small ($4.89 collat / $24 notional, 5x leverage, TP at 7742 / SL at 6595). Volume-rotation purpose unchanged — points farming still works on the naked leg. Surfacing rather than auto-deciding because the choice depends on operator's view on continued Ostium-points campaign + SPX direction. Default = hold if no operator input.

- **2026-05-18** — news_watcher tier-2 MATERIAL second-pass with resolution-criteria context. Today's 3 MATERIAL Iran-cluster alerts had agent reading direction plausibly but my manual eval used resolution-criteria + time-to-resolution to decide "hold" on all 3. Agent lacks visibility into UMA resolution language + days_to_resolve. Mirrors CRITICAL body-fetch enhancement (commit 9223226). Build: fetch gamma-api resolution criteria + days_to_resolve per position, re-prompt haiku with those + body, override only "thesis under pressure" reads (skip "thesis affirmed" to save cost). Bounded ~50 LOC. Compounds across every MATERIAL eval — saves manual journal evaluation time. Moderate priority; defer until next MATERIAL miscall surfaces a wrong directional read worth $5+.

- **2026-05-19** — Document Kelly-vs-Brownian-bridge framework distinction for late-stage bond-like NO. Post-priors-fix this morning (commits 98a5e43 + 993b1c4), portfolio_kelly now correctly shows May-31 edge=-2.5pp and Aliens edge=-1.5pp (marks above updated priors). But Brownian-bridge fair_BB at same priors shows May-31 -4.9pp = SCALE_UP, Aliens +0.4pp = HOLD. Divergence is real: Kelly is static (edge=P_win-mark, time-agnostic); Brownian-bridge is time-discounted (fair=p^(1-t/T), approaches 1 as t→T). For bond-like NO close to resolution, mark should rise toward 1 even if P_win is finite — Brownian-bridge captures this; Kelly doesn't. Need framework note in strategy/00_philosophy explaining: use Kelly for ENTRY sizing decisions; use Brownian-bridge for HOLD/TRIM signals on existing late-stage positions. Bounded ~10 line doc addition. Compounds: prevents misinterpretation of Kelly "oversized" signals on long-held positions.
