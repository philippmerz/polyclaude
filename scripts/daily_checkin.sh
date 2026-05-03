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

1. Mark portfolio + wallet state for both sleeves (scripts/positions.py, scripts/wallet_status.py, scripts/crypto_status.py, scripts/ostium_client.py status).
2. NEWS-ALERT CONSUMPTION: read tail of `notes/news_alerts.jsonl` for any entries timestamped after the last journal entry. Each line is a structured news event with per-position impact scoring (MINOR/MATERIAL/CRITICAL). For every MATERIAL/CRITICAL impact, evaluate whether the agent's read is correct and whether to act (size up, scale down, close). For CRITICAL impacts especially, verify with primary sources before acting. Note the alert + your decision in the journal.
3. Scan for catalysts on active positions (beyond what's in news_alerts); decide hold/adjust/add/close.
4. DECISION TRACKER: for any non-trivial action you take this tick (open/close/resize a position, change a strategy class, add/refactor scaffolding), add a record via `scripts/decisions.py add ...` with thesis, confidence, prediction, size, resolution_at. For any decisions whose resolution date has passed (`scripts/decisions.py pending`), fill in outcome + calibration_delta + lesson via `decisions.py update <id>`. Calibration data is the actual product — your reasoning quality across 50+ entries is what evaluates whether the LLM architecture works at scale.
5. PROSPECT new markets: run scripts/discover_markets.py for markets that became active since the last scan (the journal records timestamps; default to 12h on first run). Score any new candidates against the same edge thresholds the initial portfolio used. If something is clearly mispriced and within sizing rules, add a position (and a decision record).
6. Journal the result. Update README.md with current portfolio state so the GitHub front page stays fresh.
7. EVERY TICK: send a Telegram tick-summary covering the material work this run. Telegram is now ACTION-ONLY — the operator dropped raw news pings, so this summary is their primary visibility. Format (drop sections that have nothing):

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
8. Weekly P&L report if it's been ~7 days since the last one (notes/pnl_weekly.md). The weekly report should now also include `scripts/decisions.py summary` output and call out any pattern of mis-calibration.
9. WEEKLY (Saturday): run `.venv/bin/python scripts/methodology_stress_test.py prospective_resolve` to check open-market snapshot resolutions from the 2026-05-02 airtight test (N=20 markets resolving May 22 – June 30). If any new resolutions, journal the per-variant scoring delta. Once all 20 are resolved, journal a final analysis comparing the prospective ground-truth-blind P&L per variant to the retrospective N=30 ranking — this is the airtight check on whether more reasoning depth genuinely hurts calibration or if that finding was leakage artifact.
10. Commit + push (audit diff for secrets first).

PEER DETECTION: if you detect a peer cron tick running in parallel (other claude -p with the same session id, or a freshly news_watcher-spawned daily_checkin.sh): do NOT block waiting for it. Journal a one-line "deferring to peer tick" note and exit. Stuck-process risk: a 3-day deadlock has happened before.

EMERGENCY-EXIT PROTOCOL: if a Tier-1 news_watcher alert in the recent journal indicates a real exploit / depeg / chain halt affecting our positions, run the 3-layer sanity check (multi-source corroboration, market-reaction consistency, on-chain ground truth — full spec in strategy/02_operations.md). Only after all three layers PASS, invoke the relevant scripts/emergency_exit_*.py with --reason "<short>". On any layer FAIL, Telegram the operator with the discrepancy and HOLD; default to inaction.

POLYMARKET ORDER PLACEMENT BROKEN (as of 2026-05-03): py-clob-client (latest 0.34.6 incl. github HEAD) returns 400 'order_version_mismatch' on order placement. Reads (positions, balances, orderbook) still work. Likely Polymarket pushed an exchange-contract upgrade and the SDK hasn't shipped the fix yet. Implications: (a) DO NOT attempt new Polymarket entries — they'll all fail; just note the candidate and skip. (b) Closing existing positions UNTESTED — same write path. If a position must close and it fails, Telegram operator immediately. (c) Emergency-exit script also goes through the same path; if a Tier-1 fires and the close also fails, escalate to operator immediately. Try `pip install --upgrade py-clob-client` once per cron tick to see if the fix has shipped; if it has, resume normal trading.

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
    --model opus \
    --effort max \
    --permission-mode acceptEdits \
    --allowed-tools "Bash,Read,Write,Edit,Grep,Glob,WebSearch,WebFetch,TaskCreate,TaskUpdate,TaskList" \
    2>&1
  echo
  echo "=== exit $? at $(date -u) ==="
} >> "${LOG_FILE}" 2>&1

# Keep last 30 days of logs only
find "${LOG_DIR}" -name "checkin_*.log" -mtime +30 -delete 2>/dev/null || true
