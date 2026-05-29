#!/bin/bash
# Polyclaude check-in driver.
# Invoked by cron. Forks a headless session from the operator's interactive
# Claude (so the tick inherits full conversation context) and asks it to do
# its scheduled check-in. Token-heavier than a fresh primer-only session, but
# avoids the prompt-engineering trap and keeps the cron Claude in lockstep
# with the live thread.

set -euo pipefail

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
LOG_FILE="${LOG_DIR}/checkin_${TS}.log"

# Ensure we have a working PATH for cron (cron runs with minimal env)
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export HOME="${HOME:-$(getent passwd "$(id -un)" | cut -d: -f6)}"

# Bash-level pre-check: if the long-lived operator pane is alive, dispatch the
# cron-tick prompt via `tmux send-keys` and exit. The forked headless claude
# below is a fallback for operator-pane-down scenarios. This rule fixes the
# mutual-defer deadlock observed 2026-05-07 02:00 UTC (commit ff13200): the
# forked tick saw the operator pane in `pgrep claude` and deferred to it,
# while the operator pane simultaneously deferred to the forked tick — no
# work happened.
#
# Detection: tmux session "operator" exists AND its pane's current command
# is one of {script, claude, node} (the operator pane wraps claude with
# script(1) for log capture, so `script` is the typical foreground proc).
# `bash` means claude exited and we should fall through to fallback.
if command -v tmux >/dev/null 2>&1 && tmux has-session -t operator 2>/dev/null; then
    PANE_CMD=$(tmux display-message -p -t operator:0.0 '#{pane_current_command}' 2>/dev/null || echo "")
    case "${PANE_CMD}" in
        claude|node|script)
            # Wait up to 60s for operator pane to be idle (no Braille spinner).
            for _ in {1..60}; do
                title=$(tmux display-message -p -t operator:0.0 '#{pane_title}' 2>/dev/null || echo "")
                if ! grep -qE 'Manifesting|Percolating|Pondering|Synthesizing|Thinking|Processing' <<<"${title}"; then
                    break
                fi
                sleep 1
            done
            CRON_MSG="Cron tick ${TS}. Run your scheduled polyclaude check-in (11-step list in scripts/daily_checkin.sh). Brief if nothing happened."
            tmux send-keys -t operator:0.0 -l "${CRON_MSG}"
            sleep 0.2
            tmux send-keys -t operator:0.0 Enter
            echo "$(date -u +%Y%m%dT%H%M%SZ) cron: dispatched to operator pane (cmd=${PANE_CMD}) via send-keys; exiting" \
                >> "${LOG_DIR}/peer_skips.log"
            exit 0
            ;;
    esac
fi

# Load polyclaude path config (env vars for secret/state file locations).
# File lives outside the repo at $HOME/.polyclaude/env, mode 0600.
if [[ -f "${HOME}/.polyclaude/env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "${HOME}/.polyclaude/env"; set +a
fi

# Session id to fork from. The interactive Claude session id was captured when
# the project began and is updated only when the operator starts a new thread.
SESSION_ID=$(cat "${POLYCLAUDE_SESSION:-/dev/null}" 2>/dev/null | tr -d '[:space:]')

# Cron prompt — short, since this is a forked-resume session and inherits all
# prior context (PRIMER, philosophy, current portfolio, ongoing decisions).
read -r -d '' PROMPT <<'EOF' || true
Cron tick. Do your scheduled polyclaude check-in:

1. Mark portfolio + wallet state for both sleeves (scripts/positions.py, scripts/wallet_status.py, scripts/crypto_status.py, scripts/ostium_client.py status). ALSO run `.venv/bin/python scripts/uma_status_check.py` — alerts on umaResolutionStatus changes (proposed/disputed) for held markets, large outcomePrice moves (>5pp), and positions that disappeared from data-api but show dispute on gamma. Lesson source: 2026-05-09 R-U miss — when DEC-0018 went into UMA dispute, I framed it as benign monitoring lag for 18+ hours; this check would have caught the dispute on the next cron tick. ALSO run `.venv/bin/python scripts/ostium_state_diff.py` — alerts on Ostium open-trades count changes (OPENED/CLOSED) since prior tick. Lesson source: 2026-05-12 gold (XAU/USD LONG 5x) auto-closed at TP $4769 (+$1.17 realized) but I didn't proactively flag it; operator had to ask. This diff catches TP/SL triggers + manual closes.
2. NEWS-ALERT CONSUMPTION: read tail of `notes/news_alerts.jsonl` for any entries timestamped after the last journal entry. Each line is a structured news event with per-position impact scoring (MINOR/MATERIAL/CRITICAL). For every MATERIAL/CRITICAL impact, evaluate whether the agent's read is correct and whether to act (size up, scale down, close). For CRITICAL impacts especially, verify with primary sources before acting. Note the alert + your decision in the journal.
3. Scan for catalysts on active positions (beyond what's in news_alerts); decide hold/adjust/add/close. Run `.venv/bin/python scripts/check_marginal_apy.py` — flags any held NO/YES position whose marginal-APY-to-resolution falls below the Aave hurdle (i.e., capital is better deployed elsewhere even at near-zero P(YES) belief). For any flagged CLOSE_CANDIDATE: verify with carry math, close if confirmed, free capital for redeployment. Lesson source: 2026-05-08 DEC-0001 (Jesus 2027 NO) closed at 2.5% marginal APY for +\$0.19 realized; the hold-to-resolution alternative was below stablecoin yield. ALSO run `.venv/bin/python scripts/watchlist_monitor.py --hits-only --auto-revet` — fires ENTRY_TRIGGER_HIT lines for any long-term watchlist candidate whose price has hit its entry trigger; the `--auto-revet` flag spawns longterm_check on each hit (capped at --max-revet=2 per run, 24h TTL cache) so the fresh fundamental verdict surfaces alongside the price hit. Lesson source: 4-of-4 trigger fires CEG/LEU/CCJ/ALB (2026-05-13/16/16/18) all needed manual fresh longterm_check + revised tighter trigger because static price-derived entry_max was stale. Auto-revet codifies the pattern so operator gets the actionable picture in one alert. **Routing per project memory 2026-05-08:** polyclaude bankroll = <1y horizon only. Each trigger has a `route` field (polyclaude / ibkr_surface). On HIT: if route=ibkr_surface (default for all multi-year + all equities), Telegram the operator with thesis + entry price + suggested sizing — operator executes via personal IBKR. If route=polyclaude (only crypto-on-EVM with <1y catalyst clock), re-run longterm_check.py to verify thesis intact, size per Kelly/4 if confirmed, execute via Uniswap V3 swap. Tickers + triggers + routes configured in notes/watchlist_triggers.json.
4. DECISION TRACKER: for any non-trivial action you take this tick (open/close/resize a position, change a strategy class, add/refactor scaffolding), add a record via `scripts/decisions.py add ...` with thesis, confidence, prediction, size, resolution_at. For any decisions whose resolution date has passed (`scripts/decisions.py pending`), fill in outcome + calibration_delta + lesson via `decisions.py update <id>`. (Calibration is a debugging byproduct, NOT the objective — operator directive 2026-05-14: the only goal is ROI; treating calibration as the product is Goodhart's law. Record deltas, use them only when they reveal a systematic bias to fix.) ALSO run `.venv/bin/python scripts/portfolio_kelly.py --constrained` — surfaces per-position Kelly+ρ deficit ranking with budget-bound scaling. Use the deficit ranking to RANK any sizing decisions this tick — deploy on highest-deficit + most-robust-sensitivity positions first. Update notes/portfolio_kelly_priors.json when P(win) estimates shift materially per news flow / catalyst checks.
5. REDEEM resolved positions: run `.venv/bin/python scripts/clob_v2.py redeem-all`. It pulls data-api positions, finds any with redeemable=true, and routes through NegRiskAdapter (negativeRisk=true) or standard CTF (binary non-negRisk). Existing approvals on both routes were set during the v2 migration. Skip if no redeemables.
6. PROSPECT new markets: run scripts/discover_markets.py for markets that became active since the last scan (the journal records timestamps; default to 12h on first run). Score any new candidates against the CURRENT entry filters (mechanical-resolution only; robust-edge gate = +EV at the pessimistic p-bound `p − edge_haircut`, NOT a flat edge floor — the old 10pp bar was retired 2026-05-29; cluster cap; max-5 positions). Route every entry through `scripts/polyclaude_enter.py`, which enforces the umaResolutionStatus reject + robust-edge gate + Kelly+ρ sizing. If something is clearly mispriced and clears those filters, add a position (and a decision record). ALSO run `.venv/bin/python scripts/sports_pm_scan.py --hours 36 --with-consensus --consensus-top-n 3` to surface MID-MARKET (0.30-0.70) sports candidates with Polymarket-vs-bookie pricing deltas. For any sports candidate with delta > 3pp + decent liquidity (vol24h > $50k), evaluate the entry — bookie consensus is the most accurate per-game fair-value proxy. Bond-like fades on sports favorites (mark > 0.93) are already covered by discover_markets via APY-hurdle filter; the sports_pm_scan unlocks the mid-market range. Use scripts/portfolio_kelly.py --constrained for sizing — RANK candidates by deficit-vs-Kelly, deploy on highest-deficit + most-robust-sensitivity first. ALSO run `.venv/bin/python scripts/macro_pm_scan.py --no-consensus --days 60` for visibility into Fed/CPI/macro markets in 60d window — currently NO automated consensus comparison (v1 limitation: CME FedWatch is JS-rendered, haiku hallucinates) but surfaces all liquid macro markets for manual catalyst-check evaluation.
7. Journal the result. Update README.md with current portfolio state so the GitHub front page stays fresh.
8. EVERY TICK: send a Telegram tick-summary covering the material work this run. Telegram is now ACTION-ONLY — the operator dropped raw news pings, so this summary is their primary visibility. Format (drop sections that have nothing):

```
polyclaude tick HH:MM UTC
MTM $X.XX (Δ$Y.YY since prior tick), N positions

material alerts processed: <count>  (omit line if 0)
  · <position-key> [LEVEL]: <action taken | "hold: <one-line reason>">
  ...
actions this tick: <"none" | bulleted list, e.g. "closed atletico-top4 YES at $0.99 → $5.06">
next catalyst: <one-liner if known, e.g. "Amy Acton primary May 5">
```

Single Telegram message, body ≤ 700 chars. Always send (even on a no-action tick — the inaction reasoning IS the operator's signal that the system is alive and reasoning). Material moves taken between ticks still get their own immediate Telegram from the actor (only Tier-1 news_watcher firings auto-ping outside cron).
9. Weekly P&L report if it's been ~7 days since the last one (notes/pnl_weekly.md). The weekly report should now also include `scripts/decisions.py summary` output and call out any pattern of mis-calibration.
10. WEEKLY (Saturday): run `.venv/bin/python scripts/methodology_stress_test.py prospective_resolve` to check open-market snapshot resolutions from the 2026-05-02 airtight test (N=20 markets resolving May 22 – June 30). If any new resolutions, journal the per-variant scoring delta. Once all 20 are resolved, journal a final analysis comparing the prospective ground-truth-blind P&L per variant to the retrospective N=30 ranking — this is the airtight check on whether more reasoning depth genuinely hurts calibration or if that finding was leakage artifact.
11. Commit + push (audit diff for secrets first).

PEER DETECTION (2026-05-07+): you (a forked headless `claude -p`) are running ONLY because the bash-level pre-check in daily_checkin.sh did not find a live operator pane to dispatch to. You are the FALLBACK path. Long-lived operator/prompter `claude` processes (no `-p` flag) are NOT peers — do not defer to them. The .checkin.lock flock prevents another daily_checkin.sh-spawned tick from running concurrently with you, including news_watcher-triggered ones. Real race target: another `claude -p` (note the -p) with the same session id and a different PID from your own. Detect with `pgrep -af 'claude -p' | grep -v "^$$"`. If found, defer with a one-line journal note. If not — proceed even if `pgrep claude` shows other processes; those are panes, not peers. Mutual-defer deadlock previously observed 2026-05-07 02:00 UTC (commit ff13200) is fixed by the bash guard upstream and this clarification.

EMERGENCY-EXIT PROTOCOL: if a Tier-1 news_watcher alert in the recent journal indicates a real exploit / depeg / chain halt affecting our positions, run the 3-layer sanity check (multi-source corroboration, market-reaction consistency, on-chain ground truth — full spec in strategy/02_operations.md). Only after all three layers PASS, invoke the relevant scripts/emergency_exit_*.py with --reason "<short>". On any layer FAIL, Telegram the operator with the discrepancy and HOLD; default to inaction.

POLYMARKET WRITE PATH (as of 2026-05-05): the v1 SDKs (py-clob-client, TS clob-client) are still broken against v2 — order_version_mismatch. Use `scripts/clob_v2.py` for ALL new entries, closes, and cancels — buy AND sell verified end-to-end (10/10 reliability after salt-size fix). CLI: `clob_v2.py buy/sell/cancel/orders/orderbook`. CTF token IDs are unchanged across v1→v2 (per Polymarket docs), so existing v1 positions can be closed early via clob_v2.py SELL — CTF approvals to v2 exchanges already set. Existing 9 positions can also just resolve naturally on the underlying CTF; choose based on edge. Liquidity for new v2 entries / fills on cancellation lives in pUSD on Polygon (5 pUSD currently). To wrap more USDC.e → pUSD: approve USDC.e to CollateralOnramp 0x93070a847efEf7F70739046A929D47a521F5B8ee, then call onramp.wrap(USDC.e, eoa_address, amount_6dec). Pull USDC from Aave (Arb or Base) → bridge via Across → wrap. Schema + addresses + the 32-bit-salt requirement are documented in research/_polymarket_v2_schema_2026-05-03.md.

REASONING DEPTH RULE: routine prospecting (single trade <$10, standard market, hurdle-filter passed) uses a SINGLE-CALL evaluation, not skeptic+champion. The 2026-05-02 N=30 stress test found zero-shot beats every multi-agent variant on routine takes (+$0.04/$ vs -$0.04 to -$0.22 per dollar). Only escalate to SKEPTIC + CHAMPION pairing for trade > $10 OR new strategy class OR sizable structural change. In those cases spawn the pair in parallel: skeptic argues counter, champion argues pro-and-next. Synthesize across both. Pattern documented in strategy/00_philosophy.md.

Brief if nothing happened.
EOF

# Run from $HOME so claude sees the right project scope for --resume.
cd "${HOME}"

{
  echo "=== polyclaude daily check-in ${TS} ==="
  echo "$ pwd"; pwd
  echo "$ session=${SESSION_ID}"
  echo "$ claude -p --resume \${SESSION_ID} --fork-session (headless)"
  if [ -z "${SESSION_ID}" ]; then
    echo "ERROR: no session id resolvable from POLYCLAUDE_SESSION; cannot fork-resume"
    exit 2
  fi
  echo "${PROMPT}" | claude -p \
    --resume "${SESSION_ID}" \
    --fork-session \
    --model "claude-opus-4-8[1m]" \
    --effort max \
    --permission-mode acceptEdits \
    --allowed-tools "Bash,Read,Write,Edit,Grep,Glob,WebSearch,WebFetch,TaskCreate,TaskUpdate,TaskList" \
    2>&1
  echo
  echo "=== exit $? at $(date -u) ==="
} >> "${LOG_FILE}" 2>&1

# Keep last 30 days of logs only
find "${LOG_DIR}" -name "checkin_*.log" -mtime +30 -delete 2>/dev/null || true
