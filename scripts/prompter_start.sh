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

# Load env (POLYCLAUDE_SESSION points to the saved session id file)
if [[ -f "${HOME}/.polyclaude/env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "${HOME}/.polyclaude/env"; set +a
fi

SESSION_ID=$(cat "${POLYCLAUDE_SESSION:-/dev/null}" 2>/dev/null | tr -d '[:space:]')
if [[ -z "${SESSION_ID}" ]]; then
    echo "ERROR: no Claude session id resolvable from POLYCLAUDE_SESSION"
    echo "Cannot --resume. Aborting."
    exit 2
fi

# Idempotent
if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
    echo "prompter session already running."
    echo "  attach:  tmux attach -t ${SESSION_NAME}"
    echo "  kill:    tmux kill-session -t ${SESSION_NAME}"
    exit 0
fi

echo "starting prompter session (resuming Claude session ${SESSION_ID:0:8}...)"
echo "  attach:  tmux attach -t ${SESSION_NAME}"
echo "  log:     ${LOG_FILE}"

# Initial bootstrap message: tells claude to read the role + primer first
read -r -d '' BOOTSTRAP <<EOF || true
You are now the polyclaude PROMPTER (not the operator). The conversation you've inherited is the operator's history; from here forward you operate in prompter mode. Read these in order before anything else:

1. strategy/03_prompter_role.md
2. notes/prompter_primer.md
3. tail -200 notes/journal.md
4. notes/prompter_log.md
5. scripts/decisions.py summary

Then assess current state and decide whether to immediately spawn the operator (via the Agent tool, subagent_type=general-purpose) or idle until a trigger. The operator has full autonomy — your job is continuation pressure only, no authority gates.

Log your first decision to notes/prompter_log.md before doing anything else.
EOF

# Start tmux session, sleep briefly to let the previous claude (the operator
# being killed) finish closing its session lock, then claude --resume.
tmux new-session -d -s "${SESSION_NAME}" -c "${POLYCLAUDE_DIR}"
tmux send-keys -t "${SESSION_NAME}" "cd '${POLYCLAUDE_DIR}'" Enter
tmux send-keys -t "${SESSION_NAME}" "echo 'waiting 5s for operator session to free up...'" Enter
tmux send-keys -t "${SESSION_NAME}" "sleep 5" Enter
tmux send-keys -t "${SESSION_NAME}" "claude --resume '${SESSION_ID}' --model sonnet --permission-mode acceptEdits 2>&1 | tee -a '${LOG_FILE}'" Enter

# Send the bootstrap message after claude has initialized
sleep 8
printf '%s' "${BOOTSTRAP}" | while IFS= read -r line; do
    tmux send-keys -t "${SESSION_NAME}" -- "${line}"
    tmux send-keys -t "${SESSION_NAME}" Enter
done
tmux send-keys -t "${SESSION_NAME}" Enter

echo
echo "prompter is starting up. Attach when ready:"
echo "  tmux attach -t ${SESSION_NAME}"
echo "  (Ctrl-B then D to detach without stopping)"
