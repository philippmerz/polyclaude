#!/bin/bash
# Spawn the polyclaude operator-agent in a long-lived tmux session.
#
# Usage:
#   ./scripts/operator_agent.sh           # start (idempotent — resumes if running)
#   tmux attach -t operator               # attach to observe / interject
#   tmux send-keys -t operator 'text' Enter  # send command without attaching
#
# To stop:
#   tmux kill-session -t operator
#
# The operator reads strategy/03_operator_role.md + notes/operator_primer.md
# at session start, then runs autonomously until told to stop or the user
# detaches and budget runs out.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
SESSION_NAME="operator"
LOG_FILE="${POLYCLAUDE_DIR}/logs/operator/operator_$(date -u +%Y%m%dT%H%M%SZ).log"

mkdir -p "$(dirname "${LOG_FILE}")"

# Idempotent: if session exists, just print attach instructions
if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
    echo "operator session already running."
    echo "  attach:  tmux attach -t ${SESSION_NAME}"
    echo "  kill:    tmux kill-session -t ${SESSION_NAME}"
    exit 0
fi

echo "starting operator session in tmux pane '${SESSION_NAME}'"
echo "  attach:  tmux attach -t ${SESSION_NAME}"

# Initial primer message that bootstraps the operator. Tells claude to read
# the role docs + primer + state, then begin operating.
read -r -d '' INITIAL_PROMPT <<'EOF' || true
You are the polyclaude operator-agent. Begin by reading these in order:

1. strategy/03_operator_role.md — your role definition, authority, parameters
2. notes/operator_primer.md — the in-depth primer with cadence, spawn protocol, anti-premature-conclusion rules
3. strategy/00_philosophy.md — the project's trading philosophy
4. tail -200 notes/journal.md — recent state
5. notes/operator_log.md tail — your own prior decisions
6. git log --oneline -20 — recent activity

Then assess current state and decide whether to spawn a worker NOW or sleep until a trigger arrives. Log every decision to notes/operator_log.md per the format in the primer.

IMPORTANT: you are the meta-layer. Do not write code, place trades, or push commits yourself. Spawn workers via the Agent tool (subagent_type=general-purpose) for all execution work. Your value-add is continuation pressure and strategic continuity, not direct execution.

Begin.
EOF

# Start tmux session and pipe the initial prompt into a fresh claude session
tmux new-session -d -s "${SESSION_NAME}" -c "${POLYCLAUDE_DIR}"
tmux send-keys -t "${SESSION_NAME}" "cd '${POLYCLAUDE_DIR}' && claude --model sonnet --permission-mode acceptEdits 2>&1 | tee -a '${LOG_FILE}'" Enter

# Give the claude binary a moment to initialize before sending the primer
sleep 3
# Send the bootstrap prompt
printf '%s' "${INITIAL_PROMPT}" | while IFS= read -r line; do
    tmux send-keys -t "${SESSION_NAME}" -- "${line}"
    tmux send-keys -t "${SESSION_NAME}" Enter
done
tmux send-keys -t "${SESSION_NAME}" Enter

echo
echo "operator session started. log streaming to:"
echo "  ${LOG_FILE}"
echo
echo "to observe: tmux attach -t ${SESSION_NAME}"
echo "to detach without stopping: Ctrl-B then D"
echo "to stop entirely: tmux kill-session -t ${SESSION_NAME}"
