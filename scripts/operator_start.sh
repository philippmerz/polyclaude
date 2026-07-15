#!/bin/bash
# Spawn the polyclaude operator agent in a long-lived tmux session.
#
# The operator is the working agent (does the actual trading work). One
# long-lived single conversation, no forks. Receives prompts from:
#   - the user (tmux attach + type)
#   - Telegram (telegram_listener routes operator messages here)
#   - cron / news_watcher (via scripts/inject_prompt.sh)
#
# Usage:
#   ./scripts/operator_start.sh           # start (idempotent)
#   tmux attach -t operator               # attach to type or observe
#   tmux kill-session -t operator         # stop entirely

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
SESSION_NAME="operator"
LOG_DIR="${POLYCLAUDE_DIR}/logs/operator"
LOG_FILE="${LOG_DIR}/operator_$(date -u +%Y%m%dT%H%M%SZ).log"

mkdir -p "${LOG_DIR}"

if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
    echo "operator session already running."
    echo "  attach:  tmux attach -t ${SESSION_NAME}"
    echo "  kill:    tmux kill-session -t ${SESSION_NAME}"
    exit 0
fi

echo "starting operator session (fresh claude with operator primer)"
echo "  attach:  tmux attach -t ${SESSION_NAME}"
echo "  log:     ${LOG_FILE}"

# Run from $HOME so the operator's project key is `-home-<user>`
# (its own memory namespace).
tmux new-session -d -s "${SESSION_NAME}" -c "${HOME}"
tmux send-keys -t "${SESSION_NAME}" "cd '${HOME}'" Enter
tmux send-keys -t "${SESSION_NAME}" "script -q -c 'claude --effort max --dangerously-skip-permissions' '${LOG_FILE}'" Enter

# No bootstrap message — the operator is meant to be a fresh claude that the
# user (or this script) will /resume into the polyclaude operator session
# via the slash command (pick it from the /resume list). The /resume slash
# command sidesteps the "deferred-tool-marker" check that the CLI flag
# enforces. After /resume, the operator already knows its role from history.
sleep 5
echo
echo "operator pane ready. To load the polyclaude operator conversation:"
echo "  1. tmux attach -t ${SESSION_NAME}"
echo "  2. Type /resume and pick the operator session from the list."
echo "  3. Detach with Ctrl-B then D (do NOT exit; keep the session running)."
