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

- **2026-05-08** — Cluster cap formal skeptic+champion review (user-authorized). Question: is 30%-of-bankroll right when Iran-themed markets dominate high-APY supply? Bounded analytical exercise, no $ at risk in the analysis itself.
- **2026-05-08** — Non-PM venue DD: Drift / Kalshi / Hyperliquid (user-authorized). Multi-hour structural research; surface findings before any wallet creation / capital deployment.
- **2026-05-08** — `discover_markets.py` hardcodes hurdle `HURDLE_APY = 0.0415` (line 25); current Aave is 3.2-3.4%. Fix to read live Aave rate or pass via CLI flag. Bounded ~10 LOC.
- **2026-05-08** — `discover_markets.py` 7-day floor on hurdle filter suppresses sub-week catalyst trades (line ~220). Reconsider — DEC-0015 (May 15 NO @ 6.5d horizon) was the kind of trade hidden by this floor. Maybe lower to 3 days or make it a flag.
- **2026-05-08** — Bridge $20-30 from Aave Arbitrum → Polygon (Across) → wrap to pUSD to restore the Polymarket reserve buffer (currently $0.39 actionable post-DEC-0015). Not urgent if no immediate next trade; defer until next entry candidate.
- **2026-05-08** — `news_watcher.py` dedup-by-title-hash within 24h window. Currently dedups by GUID, so same WaPo-syndicated story across feeds fires N alerts (saw 9× of "Trump shelved Project Freedom"). ~30 LOC. Low priority — Tier-2 only, no false-positive emergency response.

## Calendar

- **2026-05-09** (~tomorrow): Russia Victory Day. Catalyst for DEC-0014 re-eval window.
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
