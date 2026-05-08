#!/bin/bash
# Inject a prompt into the operator tmux pane.
# Callers: cron periodic checks, operator_followup.sh, news_watcher Tier-1, etc.
# This is the unified injection path for any non-user, non-Telegram prompt
# arriving at the operator pane. The bash guard in daily_checkin.sh predates
# this and stays inline there for the heavy cron-tick prompt.
#
# Usage:
#   ./scripts/inject_prompt.sh "<prompt text>"
# Behavior:
#   1. Verify operator tmux session exists (else error + exit 3).
#   2. Wait up to 60s for the pane to be idle (no Braille spinner).
#   3. tmux send-keys -l (literal) the prompt + Enter to submit.
#   4. Append to notes/inject_log.md so the audit trail is unambiguous.

set -euo pipefail

PROMPT="${1:?usage: inject_prompt.sh '<prompt text>'}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
PANE="operator:0.0"
LOG="${POLYCLAUDE_DIR}/notes/inject_log.md"

if ! tmux has-session -t operator 2>/dev/null; then
    echo "ERROR: operator session not running. Start it with scripts/operator_start.sh" >&2
    exit 3
fi

# Wait up to 60s for operator pane idle (no Braille spinner). Same idle-poll
# pattern as the deprecated prompter_send.sh.
for _ in {1..60}; do
    title=$(tmux display-message -p -t "$PANE" '#{pane_title}' 2>/dev/null || echo "")
    if ! grep -qE 'Manifesting|Percolating|Pondering|Synthesizing|Thinking|Processing' <<<"$title"; then
        break
    fi
    sleep 1
done

tmux send-keys -t "$PANE" -l "$PROMPT"
sleep 0.2
tmux send-keys -t "$PANE" Enter

{
    echo ""
    echo "## $(date -u +%Y-%m-%dT%H:%M:%SZ) — inject"
    echo "$PROMPT"
} >> "$LOG"

echo "injected. logged to $LOG"
