#!/bin/bash
# Polyclaude check-in driver.
# Invoked by cron. Queues the tick to the long-lived operator when available;
# otherwise runs a fresh, fully onboarded headless fallback.

set -euo pipefail
umask 077

# Resolve repo root from this script's location (no hardcoded user path).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
LOG_DIR="${POLYCLAUDE_DIR}/logs/cron"
mkdir -p "${LOG_DIR}"

# Cross-tick lockout. Without this, a Tier-1 news_watcher firing during a
# scheduled cron window can spawn a parallel daily_checkin.sh that resumes
# the same session and races on git/journal commits. Acquire an exclusive
# lock or exit immediately (no blocking — peer-detection inside the prompt
# handles the case anyway).
LOCK_FILE="${POLYCLAUDE_DIR}/.checkin.lock"
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
    echo "$(date -u +%Y%m%dT%H%M%SZ) checkin: lock held by another tick, exiting" \
        >> "${LOG_DIR}/peer_skips.log"
    exit 0
fi

TS=$(date -u +%Y%m%dT%H%M%SZ)
# Optional $1 = why this tick fired (opportunity_watch/news_watcher pass a reason;
# plain cron passes nothing). Surfaced in the prompt so a daemon-fired tick is
# distinguishable from a scheduled one (2026-07-28: stale-ARB-trigger fires read
# as generic ticks and got answered "nothing happened").
REASON_SUFFIX=""
if [[ -n "${1:-}" ]]; then REASON_SUFFIX=" [$1]"; fi
LOG_FILE="${LOG_DIR}/checkin_${TS}.log"

# Ensure a working PATH for cron. HOME must be resolved before PATH.
export HOME="${HOME:-$(getent passwd "$(id -un)" | cut -d: -f6)}"
export PATH="${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# A queue acknowledgement is the dispatch boundary. It is safe while the
# operator is busy and cannot turn prompt text into terminal or shell input.
# POLYCLAUDE_FORCE_HEADLESS=1 is reserved for an explicit operator drill/recovery.
CRON_MSG="Cron tick ${TS}. Run your scheduled polyclaude check-in (11-step list in scripts/daily_checkin.sh). Brief if nothing happened.${REASON_SUFFIX}"
if [[ "${POLYCLAUDE_FORCE_HEADLESS:-}" == "1" ]]; then
    echo "$(date -u +%Y%m%dT%H%M%SZ) checkin: FORCE_HEADLESS set — skipping operator queue" \
        >> "${LOG_DIR}/peer_skips.log"
else
    INJECT_RC=0
    "${SCRIPT_DIR}/inject_prompt.sh" "${CRON_MSG}" >/dev/null 2>&1 || INJECT_RC=$?
    case "${INJECT_RC}" in
      0)
        echo "$(date -u +%Y%m%dT%H%M%SZ) cron: queued to operator; exiting" \
            >> "${LOG_DIR}/peer_skips.log"
        exit 0
        ;;
      69)
        # The private runtime owns rc=69 and emits it only before dispatch,
        # after proving there is no live operator process. This is the sole
        # automatic path allowed to start another asset-capable worker.
        echo "$(date -u +%Y%m%dT%H%M%SZ) cron: no live operator — using headless fallback" \
            >> "${LOG_DIR}/peer_skips.log"
        ;;
      *)
        # A timeout can mean the queue accepted the message before the caller
        # lost its acknowledgement. Fail closed so one tick can never run in
        # both the interactive operator and a fresh autonomous process.
        echo "$(date -u +%Y%m%dT%H%M%SZ) cron: queue failed rc=${INJECT_RC}; no headless fallback (exact-one safety)" \
            >> "${LOG_DIR}/peer_skips.log"
        exit "${INJECT_RC}"
        ;;
    esac
fi

# Load polyclaude path config (env vars for secret/state file locations).
# File lives outside the repo at $HOME/.polyclaude/env, mode 0600.
if [[ -f "${HOME}/.polyclaude/env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "${HOME}/.polyclaude/env"; set +a
fi

# The fallback is fresh and therefore receives a complete onboarding primer.
read -r -d '' PROMPT <<'EOF' || true
Cron tick. Do your scheduled polyclaude check-in:

1. Mark portfolio + wallet state for both sleeves (scripts/positions.py, scripts/wallet_status.py, scripts/crypto_status.py, scripts/ostium_client.py status). ALSO run `.venv/bin/python scripts/bankroll.py` — the single authoritative total-bankroll number (PM MTM + Aave aTokens + pUSD + stables + natives across both sleeves, with WARNINGs for anything unvalued). Use its TOTAL as the tick's bankroll mark; never hand-assemble the aggregate. Lesson source: 2026-05-29 (-12%% misreport vs true -4.6%) and 2026-06-10 ($75.68 idle reported as ~$22 for 5 days — status scripts were aToken-blind). ALSO run `.venv/bin/python scripts/uma_status_check.py` — alerts on umaResolutionStatus changes (proposed/disputed) for held markets, large outcomePrice moves (>5pp), and positions that disappeared from data-api but show dispute on gamma. Lesson source: 2026-05-09 R-U miss — when DEC-0018 went into UMA dispute, I framed it as benign monitoring lag for 18+ hours; this check would have caught the dispute on the next cron tick. ALSO run `.venv/bin/python scripts/ostium_state_diff.py` — alerts on Ostium open-trades count changes (OPENED/CLOSED) since prior tick. Lesson source: 2026-05-12 gold (XAU/USD LONG 5x) auto-closed at TP $4769 (+$1.17 realized) but I didn't proactively flag it; operator had to ask. This diff catches TP/SL triggers + manual closes. ALSO run `.venv/bin/python scripts/crux_coverage_check.py --quiet` — prints ONLY held positions with no matching news keyword (silent when all are covered, so it is not flag-fatigue). Lesson source: three coverage gaps found by hand and only because I happened to think of that market — HLE and Greenland had ZERO of 217 keywords (2026-08-11), and the touchscreen-MacBook leg (largest position) had four keywords that were all announcement phrasings, none of which fires on a ship/pre-order headline (2026-08-14) even though the market resolves on PURCHASABLE, not unveiling. NOTE the check proves nothing is UNWATCHED; it does NOT prove the keyword covers the resolution CRUX — that is the criteria-read rotation's job. ALSO run this one-liner to catch a daemon running STALE CODE — `for d in news_watcher heartbeat_watch telegram_listener opportunity_watch; do pid=$(pgrep -f "$d.py start" | head -1); [ -z "$pid" ] && { echo "DOWN $d"; continue; }; s=$(date -d "$(ps -o lstart= -p $pid)" +%s); m=$(stat -c %Y scripts/$d.py); [ "$m" -gt "$s" ] && echo "STALE $d (edited after start — RESTART IT)"; done` — a long-lived daemon does NOT pick up code edits, only config reloads. Lesson source 2026-08-14: the Gamescom listing-watch fix was applied to a daemon that had been running since Aug-11, so it sat INERT while looking healthy; caught only by diffing process start against file mtime. Restart with `.venv/bin/python scripts/<d>.py stop` then — CRITICALLY — an ABSOLUTE-PATH start: `setsid nohup /home/polyclaude/polyclaude/.venv/bin/python3 /home/polyclaude/polyclaude/scripts/<d>.py start >> /home/polyclaude/polyclaude/logs/<d>.log 2>&1 < /dev/null &`. The absolute form is REQUIRED, not cosmetic: daemon_keepalive.sh's alive() matches the exact cmdline `^<python> <ABSOLUTE script path> start$`, so a relative-path start is INVISIBLE to it and the */10 keepalive spawns a DUPLICATE within 10 minutes — two daemons then race on the same state file, which is where seen_listings and alert cooldowns live. That happened 2026-08-14 11:20 from exactly this mistake. Then VERIFY: new pid postdates the edit, and `pgrep -cf '<d>.py start'` shows exactly one — the first restart attempt that day silently did not take at all.
2. NEWS-ALERT CONSUMPTION: read tail of `notes/news_alerts.jsonl` for any entries timestamped after the last journal entry. Each line is a structured news event with per-position impact scoring (MINOR/MATERIAL/CRITICAL). For every MATERIAL/CRITICAL impact, evaluate whether the agent's read is correct and whether to act (size up, scale down, close). For CRITICAL impacts especially, verify with primary sources before acting. Note the alert + your decision in the journal.
3. Scan for catalysts on active positions (beyond what's in news_alerts); decide hold/adjust/add/close. Run `.venv/bin/python scripts/check_marginal_apy.py` — flags any held NO/YES position whose marginal-APY-to-resolution falls below the Aave hurdle (i.e., capital is better deployed elsewhere even at near-zero P(YES) belief). For any flagged CLOSE_CANDIDATE: verify with carry math, close if confirmed, free capital for redeployment. Lesson source: 2026-05-08 DEC-0001 (Jesus 2027 NO) closed at 2.5% marginal APY for +\$0.19 realized; the hold-to-resolution alternative was below stablecoin yield. ALSO run `.venv/bin/python scripts/watchlist_monitor.py --hits-only --auto-revet` — fires ENTRY_TRIGGER_HIT lines for any long-term watchlist candidate whose price has hit its entry trigger; the `--auto-revet` flag spawns longterm_check on each hit (capped at --max-revet=2 per run, 24h TTL cache) so the fresh fundamental verdict surfaces alongside the price hit. Lesson source: 4-of-4 trigger fires CEG/LEU/CCJ/ALB (2026-05-13/16/16/18) all needed manual fresh longterm_check + revised tighter trigger because static price-derived entry_max was stale. Auto-revet codifies the pattern so operator gets the actionable picture in one alert. **Routing per project memory 2026-05-08:** polyclaude bankroll = <1y horizon only. Each trigger has a `route` field (polyclaude / ibkr_surface). On HIT: if route=ibkr_surface (default for all multi-year + all equities), Telegram the operator with thesis + entry price + suggested sizing — operator executes via personal IBKR. If route=polyclaude (only crypto-on-EVM with <1y catalyst clock), re-run longterm_check.py to verify thesis intact, size per Kelly/4 if confirmed, execute via Uniswap V3 swap. Tickers + triggers + routes configured in notes/watchlist_triggers.json.
3b. STATE HYGIENE: run `.venv/bin/python scripts/position_state_audit.py --fix` — reconciles every position-referencing file (conditionId claim-insurance snapshot, armed opportunity triggers, Kelly priors, acked-holds) against the LIVE book. Auto-fixes the snapshot + expired holds; REPORTS judgment items (armed actionable triggers, orphan priors) for you to resolve THIS tick. Lesson source: 2026-07-28 — an ARB price trigger left armed after the position was sold fired every 5 min for hours, telegramming the operator and burning 90-min-cooldown ticks on an add already ruled out.
3c. EXIT ROUTING: run `.venv/bin/python scripts/exit_analysis.py` — for every position it computes HOLD EV (fee-free resolution) vs TAKER-SELL net (walks the REAL bid book, minus fee x min(p,1-p)) vs the MAKER breakeven (= fair, since post-only pays no fee). Act on any SELL-TAKER verdict; for HOLD verdicts consider resting a maker sell AT fair (free option, fills only if someone pays >= fair) — EXCEPT on hidden-info-class positions, where an informed up-spike means fair JUMPED (doctrine in notes/resting_orders.md). Lesson sources: Prime-SDCC taker exit gave up ~\$2 vs holding (2026-07-24); Fed showed a 2.8pp taker-vs-maker breakeven gap (2026-07-28).
4. DECISION TRACKER: for any non-trivial action you take this tick (open/close/resize a position, change a strategy class, add/refactor scaffolding), add a record via `scripts/decisions.py add ...` with thesis, confidence, prediction, size, resolution_at. For any decisions whose resolution date has passed (`scripts/decisions.py pending`), fill in outcome + calibration_delta + lesson via `decisions.py update <id>`. (Calibration is a debugging byproduct, NOT the objective — operator directive 2026-05-14: the only goal is ROI; treating calibration as the product is Goodhart's law. Record deltas, use them only when they reveal a systematic bias to fix.) ALSO run `.venv/bin/python scripts/portfolio_kelly.py --constrained` — surfaces per-position Kelly+ρ deficit ranking with budget-bound scaling. Use the deficit ranking to RANK any sizing decisions this tick — deploy on highest-deficit + most-robust-sensitivity positions first. Update notes/portfolio_kelly_priors.json when P(win) estimates shift materially per news flow / catalyst checks.
5. REDEEM resolved positions: run `.venv/bin/python scripts/clob_v2.py redeem-all`. It pulls data-api positions, finds any with redeemable=true, and routes through NegRiskAdapter (negativeRisk=true) or standard CTF (binary non-negRisk). Existing approvals on both routes were set during the v2 migration. Skip if no redeemables.
6. PROSPECT new markets: run scripts/discover_markets.py for markets that became active since the last scan. ALSO run a THIN-TAIL second pass: `.venv/bin/python scripts/discover_markets.py --min-liquidity 500 --min-vol24 20 --max-pages 20 --via-events --clears-hurdle-only --top 3000 2>&1 | tail -60` — the primary pass's $20k liquidity floor structurally excludes thin markets, which is where mispricings persist LONGEST because sharps can't size (lesson 2026-08-01: the HLE resolution-source-lag trade sat at $775-2k/leg liquidity, invisible to every tick until the OPERATOR surfaced it; scale-invariance directive says capacity is not a filter). Thin-tail hits are candidates for a CRITERIA READ, not auto-entry — fillability is not guaranteed, walk the book (the journal records timestamps; default to 12h on first run). Score any new candidates against the CURRENT entry pipeline (strategy/00_philosophy.md §4, rewritten 2026-06-10 for pure expected-return maximization): resolution-criteria risk is PRICED via the UMA-loose haircut not banned; robust-edge gate = +EV at the pessimistic p-bound `p − edge_haircut`, NOT a flat edge floor; 15%/ticket + 30%/cluster $-caps; NO position-count cap (deleted 2026-06-10 — diversified gated edges compound better; binding limits are the $-caps + $5 venue floor). Route every entry through `scripts/polyclaude_enter.py`, which enforces the umaResolutionStatus reject + robust-edge gate + Kelly+ρ sizing. If something is clearly mispriced and clears those filters, add a position (and a decision record). ALSO run `.venv/bin/python scripts/sports_pm_scan.py --hours 36 --with-consensus --consensus-top-n 3` to surface MID-MARKET (0.30-0.70) sports candidates with Polymarket-vs-bookie pricing deltas. For any sports candidate with delta > 3pp + decent liquidity (vol24h > $50k), evaluate the entry — bookie consensus is the most accurate per-game fair-value proxy. Bond-like fades on sports favorites (mark > 0.93) are already covered by discover_markets via APY-hurdle filter; the sports_pm_scan unlocks the mid-market range. Use scripts/portfolio_kelly.py --constrained for sizing — RANK candidates by deficit-vs-Kelly, deploy on highest-deficit + most-robust-sensitivity first. ALSO run `.venv/bin/python scripts/macro_pm_scan.py --no-consensus --days 60` for visibility into Fed/CPI/macro markets in 60d window — currently NO automated consensus comparison (v1 limitation: CME FedWatch is JS-rendered, haiku hallucinates) but surfaces all liquid macro markets for manual catalyst-check evaluation. ALSO run the two riskless-arb scanners (cheap, no LLM spawn): `.venv/bin/python scripts/event_monotonicity_scan.py` (decomposition arb / edge-source #4 — sibling date-series where an EARLIER cutoff is priced higher than a later one is a guaranteed edge) and `.venv/bin/python scripts/polymarket_consistency_scan.py` (multi-leg sum>1 / sum<1, validated against live CLOB asks not gamma midpoints). Act on any hit with net-positive edge after costs AND adequate book depth. Lesson 2026-06-01: I eyeballed ~1000 markets and missed these scanners until the operator pushed back — they exist precisely so discovery is systematic, not eyeballed. ALSO run `.venv/bin/python scripts/favorite_fade_scan.py --min-edge-pp 3` — a CANDIDATE SURFACER ONLY (the population fade edge FAILED REPLICATION 2026-07-03, N=836: buckets calibrated at mid, negative at executable asks — the printed edge_pp is a stale browse-order hint, NOT harvestable). Use it to spot candidates for the INSTANCE pipeline (strict-criteria + fresh-fact + catalyst gate); never size off the population numbers. Same for discover_markets' gross_apy column: WIN-ASSUMED carry, price P(loss) with an honest prior before anything (twice-burned lesson 2026-07-18).
7. Journal the result. Update README.md with current portfolio state so the GitHub front page stays fresh.
8. MATERIAL-ONLY Telegram (operator directive 2026-07-31: 'no need to send a message if there's nothing to update with' — supersedes the old every-tick heartbeat): send a tick-summary ONLY if this run produced material content (trades/fills, prior or position changes, incidents, genuine findings, watchlist surfaces, weekly P&L). A flat tick sends NOTHING — pipeline-aliveness is heartbeat_watch's job, not the summary's. Format (drop sections that have nothing):

```
polyclaude tick HH:MM UTC
MTM $X.XX (Δ$Y.YY since prior tick), N positions
[if positions.py prints a REALIZABLE line, quote it too: "realizable $Z.ZZ (best bids)".
 MTM is a MIDPOINT and an illiquid book can inflate it — on 2026-08-13 one leg's 0.685 mark
 sat inside a 0.57/0.76 spread on ZERO 24h volume, overstating the headline by $8.64. Never
 send the marked figure alone when the realizable line is present.]

material alerts processed: <count>  (omit line if 0)
  · <position-key> [LEVEL]: <action taken | "hold: <one-line reason>">
  ...
actions this tick: <"none" | bulleted list, e.g. "closed atletico-top4 YES at $0.99 → $5.06">
next catalyst: <one-liner if known, e.g. "Amy Acton primary May 5">
```

Single Telegram message, body ≤ 700 chars, only when material. Material moves taken between ticks still get their own immediate Telegram from the actor (only Tier-1 news_watcher firings auto-ping outside cron).
9. Weekly P&L report if it's been ~7 days since the last one (notes/pnl_weekly.md). The weekly report should now also include `scripts/decisions.py summary` output and call out any pattern of mis-calibration.
10. WEEKLY (Saturday) — methodology: **CONCLUDED 2026-07-11 (20/20 resolved).** The 2026-05-02 prospective, ground-truth-blind reasoning-depth test finished: zero_shot +0.29/$ beat all 4 multi-agent variants (−0.01 to −0.10), REPLICATING the retrospective N=30 ranking out-of-sample → NOT a leakage artifact; depth adds action-not-accuracy on routine takes (mechanism = selectivity). Encoded in doctrine §6 (confirmed as-written). Full analysis: journal 2026-07-11 ~02:00. NO weekly re-run needed (the experiment is complete; `prospective_resolve` now just reports 20/20). OPTIONAL only: to re-validate on fresh markets later, start a NEW batch with `methodology_stress_test.py prospective_setup` — but the finding is twice-validated (retro N=30 + prospective N=20), so a third round is low marginal value; don't auto-run.
10b. WEEKLY-REVIEW SELF-CHECK (2026-08-10, gap proven in production): the Sunday 16:00 long-term review is dispatched by a SEPARATE cron line, so any outage spanning it loses that week entirely — the Aug-9/10 fallback ran two clean ticks but the weekly rotation silently vanished. So: check the newest timestamp in `notes/world_state_log.md`. If it is more than 8 days old, ALSO run the weekly review NOW as part of this tick — pick 2-3 domain slugs from notes/primary_sources.md least-recently run, `python3 scripts/world_state_digest.py --domain <slug1>,<slug2>`, then longterm_check.py on the top 1-2 candidates from any HIGH/MED theme, and update notes/longterm_watchlist.md. If it is fresher than 8 days, skip this step silently.

11. Commit + push (audit diff for secrets first).

PEER DETECTION: you are running only because the durable operator queue was unavailable or an explicit operator drill/recovery forced a headless run. You are the FALLBACK path. The `.checkin.lock` flock already guarantees that no other `daily_checkin.sh` worker is running, including news-triggered ticks. Do not defer merely because the interactive operator process exists; it is not a peer and could be the failed/quota-blocked path that caused this fallback.

EMERGENCY-EXIT PROTOCOL: if a Tier-1 news_watcher alert in the recent journal indicates a real exploit / depeg / chain halt affecting our positions, run the 3-layer sanity check (multi-source corroboration, market-reaction consistency, on-chain ground truth — full spec in strategy/02_operations.md). Only after all three layers PASS, invoke the relevant scripts/emergency_exit_*.py with --reason "<short>". On any layer FAIL, Telegram the operator with the discrepancy and HOLD; default to inaction.

POLYMARKET WRITE PATH (as of 2026-05-05): the v1 SDKs (py-clob-client, TS clob-client) are still broken against v2 — order_version_mismatch. Use `scripts/clob_v2.py` for ALL new entries, closes, and cancels — buy AND sell verified end-to-end (10/10 reliability after salt-size fix). CLI: `clob_v2.py buy/sell/cancel/orders/orderbook`. CTF token IDs are unchanged across v1→v2 (per Polymarket docs), so existing v1 positions can be closed early via clob_v2.py SELL — CTF approvals to v2 exchanges already set. Existing 9 positions can also just resolve naturally on the underlying CTF; choose based on edge. Liquidity for new v2 entries / fills on cancellation lives in pUSD on Polygon (5 pUSD currently). To wrap more USDC.e → pUSD: approve USDC.e to CollateralOnramp 0x93070a847efEf7F70739046A929D47a521F5B8ee, then call onramp.wrap(USDC.e, eoa_address, amount_6dec). Pull USDC from Aave (Arb or Base) → bridge via Across → wrap. Schema + addresses + the 32-bit-salt requirement are documented in research/_polymarket_v2_schema_2026-05-03.md.

REASONING DEPTH RULE: routine prospecting (single trade <$10, standard market, hurdle-filter passed) uses a SINGLE-CALL evaluation, not skeptic+champion. The 2026-05-02 N=30 stress test found zero-shot beats every multi-agent variant on routine takes (+$0.04/$ vs -$0.04 to -$0.22 per dollar). Only escalate to SKEPTIC + CHAMPION pairing for trade > $10 OR new strategy class OR sizable structural change. In those cases spawn the pair in parallel: skeptic argues counter, champion argues pro-and-next. Synthesize across both. Pattern documented in strategy/00_philosophy.md.

Brief if nothing happened.
EOF

# Run from the repository so the fallback loads the private operator contract.
cd "${POLYCLAUDE_DIR}"

{
  echo "=== polyclaude daily check-in ${TS} ==="
  echo "$ pwd"; pwd
  echo "$ headless fallback (fresh session + primer)"
  # Preserve the exit trailer and auth post-flight even on worker failure.
  RC=0
  PRIMER="You are polyclaude's autonomous FALLBACK session: the interactive operator queue was unreachable or explicitly bypassed, so you are running this scheduled tick headless with NO inherited conversation context.

Onboard first, in this order: read README.md, PRIMER.md, strategy/00_philosophy.md, strategy/01_lessons.md, and strategy/02_operations.md; then run .venv/bin/python scripts/polyclaude_status.py for live state.

Then do the check-in below. Be CONSERVATIVE: you lack the conversation context the interactive session has. Prefer reporting and journaling over trading; do NOT open a new position unless it clears every gate in the doctrine AND you have verified the facts yourself this run. Journal what you did. Send a Telegram summary only when the run produced material content; when you do, note that you are the fallback.

--- SCHEDULED CHECK-IN ---
"
  printf '%s' "${PRIMER}${PROMPT}" | \
    "${HOME}/.local/bin/polyclaude-agent" run \
      --profile main --effort max --access autonomous \
      --cwd "${POLYCLAUDE_DIR}" --timeout 7200 \
      2>&1 || RC=$?
  echo
  echo "=== exit ${RC} at $(date -u) ==="
} >> "${LOG_FILE}" 2>&1

# Creds/auth post-flight (2026-07-02 audit, outage-hardening part 2 of 2).
# 4 outages in ~3 weeks were expired-creds: the headless fallback fails fast
# with an auth error in the log, no tick output is produced, and nobody is
# told. The heartbeat dead-man switch catches the *pattern* within ~16h;
# this catches the *cause* on the very first failed tick and pings the
# operator directly (LLM-independent path). Fires at most 2x/day (per tick).
if tail -n 40 "${LOG_FILE}" | grep -qiE "authentication|unauthorized|401|invalid.*(api key|token|credential)|OAuth.*(expired|error)|please.*log ?in|/login"; then
    cd "${POLYCLAUDE_DIR}" && .venv/bin/python scripts/telegram.py msg \
      "[CHECKIN] tick ${TS} FAILED with an auth error — agent credentials likely expired. Ticks will fail until the service account is logged in again." \
      >> "${LOG_FILE}" 2>&1 || true
fi

# Keep last 30 days of logs only
find "${LOG_DIR}" -name "checkin_*.log" -mtime +30 -delete 2>/dev/null || true
