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
Cron tick. Do your scheduled polyclaude check-in: mark portfolio + wallet state, scan
for catalysts on active positions, decide hold/adjust/add/close, journal the result,
write a weekly report if it's been ~7 days since the last one, commit + push (audit
secrets in the diff first), and ping the operator on Telegram if anything material
moved. Brief if nothing happened.
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
