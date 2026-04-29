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
2. Scan for catalysts on active positions; decide hold/adjust/add/close.
3. PROSPECT new markets: run scripts/discover_markets.py for markets that became active since the last scan (the journal records timestamps; default to 12h on first run). Score any new candidates against the same edge thresholds the initial portfolio used. If something is clearly mispriced and within sizing rules, add a position.
4. Journal the result. Update README.md with current portfolio state so the GitHub front page stays fresh.
5. Once daily (skip if today's already-done line is in the journal): send a one-line P&L Telegram so the operator has continuous visibility — total MTM, day-over-day change, any open issues. Format: "polyclaude $X.XX MTM (+/-$Y.YY today). N positions. <one-line note>". Material moves still get their own immediate Telegram.
6. Weekly P&L report if it's been ~7 days since the last one (notes/pnl_weekly.md).
7. Commit + push (audit diff for secrets first).

PEER DETECTION: if you detect a peer cron tick running in parallel (other claude -p with the same session id, or a freshly news_watcher-spawned daily_checkin.sh): do NOT block waiting for it. Journal a one-line "deferring to peer tick" note and exit. Stuck-process risk: a 3-day deadlock has happened before.

EMERGENCY-EXIT PROTOCOL: if a Tier-1 news_watcher alert in the recent journal indicates a real exploit / depeg / chain halt affecting our positions, run the 3-layer sanity check (multi-source corroboration, market-reaction consistency, on-chain ground truth — full spec in strategy/02_operations.md). Only after all three layers PASS, invoke the relevant scripts/emergency_exit_*.py with --reason "<short>". On any layer FAIL, Telegram the operator with the discrepancy and HOLD; default to inaction.

SKEPTIC AGENT: before any trade > $10 or any new strategy class, spawn a general-purpose Agent prompted to argue the strongest counter-thesis. If it surfaces a real consideration, reconsider. Pattern documented in strategy/00_philosophy.md.

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
