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

- **2026-06-26** — Small-crypto long-tail opportunity research (operator-requested 2026-06-26, msg 470/471). Background research agent screened airdrop-pipeline + deep-value small-caps. Meta-finding: at $162 single-wallet scale, merger-arb/buyback catalysts on liquid tokens beat points-farming (points charge real gas now for uncertain/dilutable/rug-risk future claims). 3 tracked candidates, NONE actionable yet — each gated on one trigger:
  - **Arbitrum DRIP** (watch-only): best EVM yield engine (pays LIQUID ARB on Aave/Morpho/Fluid/Euler/Dolomite/Silo, withdrawable). GATE: Season 2 DORMANT, no announced date; ~63.7M ARB undeployed, mandate to Jul-2027. Watch the Arbitrum forum; deploy the moment S2 epochs open. Zero capital until then.
  - Excluded as noise at our scale: crypto-treasury "below cash" (NASDAQ equities, un-buyable on-chain), 100x-gem lists, Base/restaking points for one small wallet, ACX (trades above its buyout floor), PENDLE/Fluid (cheap multiples but shrinking-fundamentals/dilution flags — watch-list only).

- **2026-05-08** — Non-PM venue DD: Drift / Kalshi / Hyperliquid (user-authorized). Multi-hour structural research; surface findings before any wallet creation / capital deployment.

- **2026-05-08** — Hyperliquid HIP-4 vs Polymarket arb scan. Discovered during venue DD: Hyperliquid launched zero-fee outcome markets targeting Polymarket. Same questions, potentially different prices = arb opportunity. Extend the `scripts/limitless_arb_scan.py` pattern to Hyperliquid (different venue, same logic). Bounded ~60 LOC. Once shipped, the cross-venue scan auto-surfaces opportunities to operator. Defer until HIP-4 has meaningful TVL (currently early days; not yet at scan-worthy depth).

- **2026-05-08** — Wider net for longterm watchlist seeds (next batch). Less-obvious categories where the cycle bottom may not yet be priced: SiC / advanced packaging (Wolfspeed), lithium cycle bottom (Albemarle), defense-tech sub-sectors (Kratos, AeroVironment, Anduril secondaries), space economy (Rocket Lab, AST SpaceMobile), DeFi blue chips at depressed multiples (UNI / AAVE / MKR), BTC mining infra (Cipher Mining, Hut 8). Run `longterm_check.py` on each. Goal: find candidates that DO trigger ENTER NOW — the visible names today don't.
- **2026-05-08** — Bridge $20-30 from Aave Arbitrum → Polygon (Across) → wrap to pUSD to restore the Polymarket reserve buffer (currently $0.39 actionable post-DEC-0015). ~~Not urgent if no immediate next trade.~~ Partially done 2026-05-08 ~14:30 UTC: bridged $19.99 USDC Arb→Polygon, transferred crypto→polymarket sleeve. Remaining hop: native USDC → USDC.e (DEX swap on Polygon) → wrap to pUSD. Deferred swap until a trade lines up — sunk-cost friction is now $0.45, marginal swap cost ~$0.50.

- **2026-05-08** — `news_watcher.py` dedup-by-title-hash within 24h window. Currently dedups by GUID, so same WaPo-syndicated story across feeds fires N alerts (saw 9× of "Trump shelved Project Freedom"). ~30 LOC. Low priority — Tier-2 only, no false-positive emergency response.

- **2026-07-30 [US-Iran ceasefire family — criteria banked, watch]** — us-x-iran-effective-ceasfire-by-* legs (Jul-31 0.225 / Aug-14 0.465 / Aug-31 0.545). Mechanics: YES = no US air/missile strike impacting Iranian SOIL after the leg date + 14 clean days; maritime/proxy/interception/ground all EXCLUDED; conflicting reports → 3-day dispute window. State at write: Trump PAUSED strikes ~Jul-27 to force a deal (pause-resume oscillation); sources conflict on whether Jul-28/29 wave qualified. No edge while my P(YES) spans market. RE-EVAL when state clarifies: (a) deal signs / pause visibly holds → later-leg YES may lag the mechanics; (b) ~~confirmed NEW strike → Aug-14 NO~~ FIRED 2026-07-31 AND PRODUCED A NULL: 'heavy strikes on Iran' Jul-30 repriced the family UP for YES (crescendo-before-pause read) — the market's interpretation of the fact dominated the fact; condition (b) retired, (a) stands. Verify soil-impact from CENTCOM statements + criteria text BEFORE any entry; world-state rule applies (2 kills already).

- **2026-08-01 [HLE family — criteria-mechanics candidates, capital-bound]** — 7 sibling events (overall + Claude/Kimi/Meta/OpenAI/Grok/Gemini "highest HLE score in 2026"), ALL resolving on agi.safe.ai (official board: global top 38.3 Gemini-3-Pro, OpenAI row 25.3 ~1yr stale; real frontier 53.3 per third-party trackers). OpenAI legs TRADED (DEC-0062, $16.19 NO 50+/55+). Remaining family = same resolution-source-lag read per lab + cross-event consistency (overall ≈ max over labs). NEXT TICK: price the family, check relative consistency, size within 30% cluster cap — but capital-bound until Fed/D23 ammo frees (pUSD ~$3.4; Aave $7.85 bridgeable). Thin books move slowly; no rush premium.

- **2026-08-26 [NVDA-largest post-earnings re-check]** — "Will NVIDIA be the largest company by market cap on Aug-31" (YES 0.745 today; my fair 0.80 after haircutting for the earnings binary). Live caps Aug-03: NVDA $4.74T / GOOGL $4.34T / AAPL $4.30T = 9.2% cushion. The whole trade is the Aug-26 earnings print. IF earnings clears with the lead intact, the remaining 5 days is close to a free carry — re-price then; a YES entry above ~0.85 post-print is still worth checking against the 5-day tail. Mechanical resolution (market cap), no self-reference issue. Capital-bound until D23 resolves.

- **2026-08-03 [Platform-migration question — OPERATOR-RAISED, awaiting their call]** — operator hit Claude Code usage limits twice in 3 days and is weighing a move to DeepSeek V4 / GLM-5.2 / Kimi K3. NOT started (they said "I'll think about it"; unrequested deep-dives burn the scarce resource). When they ask, the writeup should cover: (a) what in this repo is Claude-Code-SPECIFIC vs portable — the trading logic is plain Python/httpx and fully portable; the coupling is the agent loop (cron→tmux send-keys→claude -p), the sub-agent spawns (catalyst_check/longterm_check/sports consensus all shell out to `claude -p --model haiku`), and this session's own interactive loop; (b) kimi_advisor.py is ALREADY a working non-Anthropic integration (Moonshot API, 25-web-search rounds, caught my stale Gemini facts Aug-01) — it is the proof-of-concept and the natural seam to widen; (c) honest conflict-of-interest disclosure: I am a Claude model advising on whether to stop using Claude, so the writeup must lead with that and lean toward understating Claude's advantages (see the self-referential-markets rule in 01_lessons.md).

## Calendar

> Resolved past-dated reminders pruned 2026-06-04 (decision outcomes live in decisions.json; git has full history). Future only; ~Nd as of 2026-06-04:

- **~2026-08-04..08**: D23 panel listings expected — run the playbook (buy active-entity YES ≤0.80 after criteria-text check; cheap legs = biggest edge; pull bids at window end). Event Aug 14-16. $19.9 pUSD reserved.
- **2026-08-16**: US-Iran MOU expiry — LIKELY MOOT (Iran suspended commitments ~mid-Jul; ACTIVE Iran-Gulf missile war since: Kuwait/Bahrain/Qatar/Saudi under fire, ground-incursion threats vs Kuwait bases). WORLD-STATE RULE (2026-07-26, from the Kuwait deploy-gate kill): any Gulf/war-adjacent market gate must RE-PULL live conflict state at decision time — the tier-2 Iran demotion means my ambient world-model runs stale. Book is Iran-free; re-promotion of tier-1 keywords only on Iran re-entry.

- **2026-08-18** (~75d): Trump UAP-EO 300-day declassification deadline. Reassessment trigger for DEC-0003.
- **2026-10-31** (~149d): Annual DNI UAP report deadline. Final pre-resolution catalyst for DEC-0003.
- **2026-11-03** (~152d): US midterm elections. Catalyst for DEC-0004 (Trump-out NO) — even if Dems take House, Senate conviction implausible.

## Recently closed (last 7d, for context — older deletes silently)

- 2026-07-26: Marvel-SDCC SELL filled 0.98 (+43.9%); Apple resolved YES; first Brier scoreboard N=4 beating market.
- 2026-07-25: Fed-hike YES entered+added (DEC-0058/0059); prior-staleness guard shipped; execution-repertoire audit.
- 2026-07-24: maker-first execution shipped; ARB closed +11.8%; weekly P&L; VELO no-arb; ledger_calibration.py.

- **2026-07-27 [D23 playbook — announce-template BASE-RATE CORRECTED]** — SDCC went 4-for-4 YES incl. DC (no slate panel) and Lucasfilm (D23-hold thesis): the official-channels backdoor over a multi-day window ≈ guarantees a qualifying announcement from ANY active studio — panel logic picks WHERE reveals land, not WHETHER (my 0.22/0.15 skips were wrong; missed +69% each at 0.59). D23 (Aug 14-16, listings ~early Aug): after verifying the same loose criteria text, BUY YES on any active-entity leg ≤~0.80 — cheap legs are the biggest edge, not the most suspect. Cluster-cap the family; pull unfilled bids at window end (post-catalyst rule). Same for Gamescom (Aug 19-24) / NYCC. Realized template record: Prime +59%, Marvel +43.9%, skipped DC/Lucasfilm counterfactual −$14.
