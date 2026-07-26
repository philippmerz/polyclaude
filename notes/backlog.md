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

## Calendar

> Resolved past-dated reminders pruned 2026-06-04 (decision outcomes live in decisions.json; git has full history). Future only; ~Nd as of 2026-06-04:

- **2026-08-16** (~53d): US-Iran MOU 60-day ceasefire window expires — Iran cluster reassessment trigger (regime-fall + Pahlavi NO legs).

- **2026-07-27** (~53d): EU sanctions on Iran review — Iran cluster reassessment.
- **2026-08-18** (~75d): Trump UAP-EO 300-day declassification deadline. Reassessment trigger for DEC-0003.
- **2026-10-31** (~149d): Annual DNI UAP report deadline. Final pre-resolution catalyst for DEC-0003.
- **2026-11-03** (~152d): US midterm elections. Catalyst for DEC-0004 (Trump-out NO) — even if Dems take House, Senate conviction implausible.

## Recently closed (last 7d, for context — older deletes silently)

- 2026-07-26: Marvel-SDCC SELL filled 0.98 (+43.9%); Apple resolved YES; first Brier scoreboard N=4 beating market.
- 2026-07-25: Fed-hike YES entered+added (DEC-0058/0059); prior-staleness guard shipped; execution-repertoire audit.
- 2026-07-24: maker-first execution shipped; ARB closed +11.8%; weekly P&L; VELO no-arb; ledger_calibration.py.
