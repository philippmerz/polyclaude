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
- **2026-05-08** — `discover_markets.py` hardcodes hurdle `HURDLE_APY = 0.0415` (line 25); current Aave is 3.2-3.4%. Fix to read live Aave rate or pass via CLI flag. Bounded ~10 LOC.
- **2026-05-08** — `discover_markets.py` 7-day floor on hurdle filter suppresses sub-week catalyst trades (line ~220). Reconsider — DEC-0015 (May 15 NO @ 6.5d horizon) was the kind of trade hidden by this floor. Maybe lower to 3 days or make it a flag.
- **2026-05-08** — Bridge $20-30 from Aave Arbitrum → Polygon (Across) → wrap to pUSD to restore the Polymarket reserve buffer (currently $0.39 actionable post-DEC-0015). ~~Not urgent if no immediate next trade.~~ Partially done 2026-05-08 ~14:30 UTC: bridged $19.99 USDC Arb→Polygon, transferred crypto→polymarket sleeve. Remaining hop: native USDC → USDC.e (DEX swap on Polygon) → wrap to pUSD. Deferred swap until a trade lines up — sunk-cost friction is now $0.45, marginal swap cost ~$0.50.

- ~~**2026-05-08** — `scripts/across_bridge.py`: when bridging to Polygon, prefer `--token USDC.e`...~~ **DONE 2026-05-08, commit pending.** Added `--token-out` flag (default = same as `--token`); --token-out USDC.e for Polygon destination lands as bridged-USDC-variant directly, bypassing the USDC→USDC.e swap step.

- ~~**2026-05-08** — `scripts/across_bridge.py`: support `--recipient` flag...~~ **DONE 2026-05-08, commit pending.** Added `--recipient` flag (default = depositor address). Allows cross-wallet bridging — e.g. crypto sleeve withdraws Aave, bridges with `--recipient=<polymarket-sleeve-addr>`, lands as deployable Polymarket buffer with no extra ERC20 hop.

- ~~**2026-05-08** — Re-evaluate DEC-0003 (US confirm aliens before 2027 NO @ entry 0.80, current mark 0.815).~~ **DONE 2026-05-08 ~16:00 UTC.** Ran `catalyst_check.py` (see `notes/catalyst_log.md`). Findings: 2 HIGH-impact catalysts in the window — (1) 2026-08-18 Trump-EO 300-day declassification deadline; (2) 2026-10-31 annual DNI UAP report. Central P(YES) = 16% vs market 18.5% YES = NO has small positive edge (~$0.45 EV on $9 cost over 237d, ~7.7% APY). **Decision: HOLD.** Add Aug 18 to calendar as reassessment trigger — if market YES drifts up materially toward the deadline, reconsider close.

- ~~**2026-05-08** — Add to `strategy/00_philosophy.md` edge-source-1 ("longshot fade"): explicit rule that bond-like fades require 5-minute web search for window-specific catalysts BEFORE sizing.~~ **DONE 2026-05-08, commit `6c9d171`** — philosophy updated with mandatory catalyst_check.py pre-trade gate. discover_markets.py also got `--check-catalysts N` flag for auto-prefilter on hurdle-clearance candidates.

- ~~**2026-05-08** — Cron-tick auto-check for marginal-APY-below-hurdle on held positions.~~ **DONE 2026-05-08, commit pending.** `scripts/check_marginal_apy.py` shipped — pulls from data-api, computes `(1-mark)/mark × 365/days`, flags CLOSE_CANDIDATEs vs configurable hurdle (default 3.4% Aave Base). Wired into `scripts/daily_checkin.sh` cron prompt step 3 as a mandatory check. Smoke-tested: all 9 current positions clear; if Jesus 2027 NO (closed earlier) hadn't been closed, it would've been the only flag.

- ~~**2026-05-08** — `scripts/catalyst_check.py` prompt enhancement: for multi-conditional questions ("Will X happen by date" where X = "Y AND Z"), require haiku to show the multiplicative breakdown explicitly.~~ **DONE 2026-05-08, commit `11e89bb`.**

- ~~**2026-05-08** — `scripts/catalyst_check.py` enhancement: auto-fetch the market's resolution description from gamma-api...~~ **DONE 2026-05-08, commit pending.** Implemented `_fetch_resolution_description(question)` — searches gamma-api active markets for exact-match question, returns description or None. Prompt template now includes a "LITERAL RESOLUTION CRITERIA" block when fetch succeeds. Validated end-to-end: re-running US-invade-Iran NO check shifted central P(YES) from 98% (loose framing) → 2.2% (strict criteria with multiplicative breakdown). Same query, 95pp swing. Tool now anchors on oracle language, not media framing. The skip decision on US-invade-Iran was preserved (UMA-interpretation prior unknown), but for future bond-like fades the tool will correctly distinguish strict vs loose interpretations.
- **2026-05-08** — `news_watcher.py` dedup-by-title-hash within 24h window. Currently dedups by GUID, so same WaPo-syndicated story across feeds fires N alerts (saw 9× of "Trump shelved Project Freedom"). ~30 LOC. Low priority — Tier-2 only, no false-positive emergency response.

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
