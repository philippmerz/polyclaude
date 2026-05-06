#!/bin/bash
# Spawn the polyclaude prompter agent in a long-lived tmux session.
#
# The prompter --resume's the operator's main Claude session so it inherits
# the full conversation history. Idempotent: if the prompter is already
# running, it just prints the attach instructions.
#
# Usage:
#   ./scripts/prompter_start.sh           # start (or report already-running)
#   tmux attach -t prompter               # observe / interject
#   tmux kill-session -t prompter         # stop entirely
#
# To stop without killing tmux: from inside the session, type 'quit' or '/exit'
# or send Ctrl-C twice — the prompter is told via primer to exit cleanly on
# explicit user 'stop'.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
SESSION_NAME="prompter"
LOG_DIR="${POLYCLAUDE_DIR}/logs/prompter"
LOG_FILE="${LOG_DIR}/prompter_$(date -u +%Y%m%dT%H%M%SZ).log"

mkdir -p "${LOG_DIR}"

# Idempotent
if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
    echo "prompter session already running."
    echo "  attach:  tmux attach -t ${SESSION_NAME}"
    echo "  kill:    tmux kill-session -t ${SESSION_NAME}"
    exit 0
fi

echo "starting prompter session (fresh claude, will read prompter_primer.md for context)"
echo "  attach:  tmux attach -t ${SESSION_NAME}"
echo "  log:     ${LOG_FILE}"

# Start tmux session in $POLYCLAUDE_DIR so the prompter's relative paths
# (notes/, strategy/, scripts/) work.
tmux new-session -d -s "${SESSION_NAME}" -c "${POLYCLAUDE_DIR}"
tmux send-keys -t "${SESSION_NAME}" "cd '${POLYCLAUDE_DIR}'" Enter
# Run claude under script(1) so we get a clean log without breaking the TUI
tmux send-keys -t "${SESSION_NAME}" "script -q -c 'claude --model sonnet --permission-mode acceptEdits' '${LOG_FILE}'" Enter

# Wait for claude TUI to be ready before injecting the bootstrap.
# Poll the log: claude prints its banner ("Welcome" / version) when ready.
echo "waiting for claude to initialize..."
for i in {1..30}; do
    sleep 1
    if grep -q -E 'Try .* to' "${LOG_FILE}" 2>/dev/null; then
        echo "claude is ready (after ${i}s)"
        break
    fi
done
sleep 2  # extra buffer for the prompt input to be focused

# Send a short bootstrap. The prompter primer has all the verbose details.
BOOTSTRAP="You are the polyclaude prompter (NOT the operator). Read notes/prompter_primer.md and strategy/03_prompter_role.md in full, then follow the primer. The user is observing this tmux pane."
tmux send-keys -t "${SESSION_NAME}" -- "${BOOTSTRAP}"
tmux send-keys -t "${SESSION_NAME}" Enter

echo
echo "prompter started. Attach when ready:"
echo "  tmux attach -t ${SESSION_NAME}"
echo "  (Ctrl-B then D to detach without stopping)"
