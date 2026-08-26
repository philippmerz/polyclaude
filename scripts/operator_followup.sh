#!/bin/bash
# Schedule a self-injected follow-up prompt after a delay.
#
# Used by the operator agent at the end of any turn where
# the current thread isn't fully resolved. The follow-up fires after the
# delay and submits the prompt to the operator queue via inject_prompt.sh.
# When the follow-up fires, the operator decides whether to schedule
# another (continuing the loop) or call cancel_followup.sh (resolving).
#
# Only one followup is queued at a time — re-running this cancels the prior
# one. PID is tracked in notes/.followup_pid (gitignored).
#
# Usage:
#   ./scripts/operator_followup.sh "<prompt>" [delay_minutes]
# Default delay: 20 minutes.

set -euo pipefail

PROMPT="${1:?usage: operator_followup.sh '<prompt>' [delay_min]}"
DELAY="${2:-20}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
PID_FILE="${POLYCLAUDE_DIR}/notes/.followup_pid"

# Cancel any prior pending followup so only one is queued at a time.
# Identity check before kill (2026-07-16 audit): the PID file persists across
# reboots and boot PIDs are low/collision-prone — kill -0 alone could green-
# light killing an unrelated daemon (e.g. telegram_listener at a reused PID).
if [[ -f "$PID_FILE" ]]; then
    old_pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
        if ps -o args= -p "$old_pid" 2>/dev/null | grep -qE 'inject_prompt\.sh|sleep'; then
            kill "$old_pid" 2>/dev/null && echo "cancelled prior followup pid=$old_pid"
        else
            echo "pid $old_pid is NOT a followup process (PID reuse) — not killing"
        fi
    fi
    rm -f "$PID_FILE"
fi

# Schedule new followup via background sleep+inject. Quoted carefully to handle
# arbitrary text in PROMPT (the inject script takes one positional arg).
DELAY_SEC=$((DELAY * 60))
nohup bash -c "sleep $DELAY_SEC && '$SCRIPT_DIR/inject_prompt.sh' \"\$1\"" \
    _ "$PROMPT" >/dev/null 2>&1 &
new_pid=$!
echo "$new_pid" > "$PID_FILE"
echo "scheduled followup pid=$new_pid: \"$PROMPT\" in ${DELAY}min"
