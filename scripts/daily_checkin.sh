#!/bin/bash
# Polyclaude daily check-in.
# Invoked by cron. Each run is a fresh headless Claude session that loads context
# from polyclaude/ + memory, monitors positions, scans news, journals, and trades
# if conviction warrants it.

set -euo pipefail

POLYCLAUDE_DIR="<PROJECT>"
LOG_DIR="${POLYCLAUDE_DIR}/logs/cron"
mkdir -p "${LOG_DIR}"

TS=$(date -u +%Y%m%dT%H%M%SZ)
LOG_FILE="${LOG_DIR}/checkin_${TS}.log"

# Ensure we have a working PATH for cron (cron runs with minimal env)
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export HOME="<HOME>"

# Cron-driver prompt. Goal-only, minimal directive style — the operator wants
# Claude Opus to think for itself, not follow a checklist. Use your judgment.
read -r -d '' PROMPT <<'EOF' || true
You are continuing the polyclaude project — autonomous Polymarket trading on a Linux VM.
Goal: maximize return on the bankroll, constrained by what's legal and inside the budget.

This is a fresh session triggered by cron. The operator may not be watching.
Wallet (private): <SECRETS>/wallet.json — outside the repo, never commit.
Repo: <PROJECT> (public GitHub). Python venv: ./.venv.

Load context from MEMORY.md (and the files it links), polyclaude/strategy/, the tail
of polyclaude/notes/journal.md, polyclaude/research/, polyclaude/questions.md.
Mark state via scripts/positions.py and scripts/wallet_status.py.

Then exercise your judgment: monitor, research, trade, journal, write the weekly
report when it's due, answer questions, surface anything blocking. Do whatever
you'd do as a careful, polymath-grade operator with this much capital and horizon.
Append to the journal — never rewrite history. Audit every commit diff for secrets
before `git push`. If you're running on a quiet day with no real news and no real
moves, a one-line "stable, no action" entry is the right answer.
EOF

cd "${POLYCLAUDE_DIR}"

{
  echo "=== polyclaude daily check-in ${TS} ==="
  echo "$ pwd"
  pwd
  echo "$ claude -p (headless)"
  echo "${PROMPT}" | claude -p \
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
