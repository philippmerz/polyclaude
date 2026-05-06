#!/bin/bash
# Helper: send a message from the prompter to the operator's tmux pane.
# Used by the prompter when it decides to apply continuation pressure.
#
# Usage:
#   ./scripts/prompter_send.sh "do X next, the philosophy doc says Y"
#
# Behavior:
#   1. Wait briefly for operator pane to be idle (no Braille spinner)
#   2. Send the text via tmux send-keys -l (literal mode)
#   3. Send Enter
#   4. Append the send to notes/prompter_log.md so the user can see what
#      the prompter dispatched

set -euo pipefail

OPERATOR_PANE="operator:0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
LOG="${POLYCLAUDE_DIR}/notes/prompter_log.md"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 \"<message text>\""
    exit 2
fi
MSG="$*"

if ! tmux has-session -t operator 2>/dev/null; then
    echo "ERROR: operator session not running. Start it with scripts/operator_start.sh" >&2
    exit 3
fi

# Wait up to 60s for the operator pane to be idle. Spinner check works for
# claude code's TUI which sets the pane title to "✶ Manifesting..." or
# similar Braille animations while busy.
for i in {1..60}; do
    title=$(tmux display-message -p -t "${OPERATOR_PANE}" "#{pane_title}" 2>/dev/null || echo "")
    # Idle if title doesn't contain a known busy marker
    if ! grep -qE 'Manifesting|Percolating|Pondering|Synthesizing|Thinking|Processing' <<<"${title}"; then
        break
    fi
    sleep 1
done

# Send literal text + Enter. -l avoids interpreting the message as keys.
tmux send-keys -t "${OPERATOR_PANE}" -l "${MSG}"
sleep 0.2
tmux send-keys -t "${OPERATOR_PANE}" Enter

# Log it
{
    echo ""
    echo "## $(date -u +%Y-%m-%dT%H:%M:%SZ) — prompter→operator"
    echo "${MSG}"
} >> "${LOG}"

echo "sent. logged to ${LOG}"
