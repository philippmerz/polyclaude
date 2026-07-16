#!/bin/bash
# Cancel any pending self-injected follow-up.
# Called by the operator at the end of a turn where the current thread is
# fully resolved. Stops the auto-followup loop.
#
# Usage:
#   ./scripts/cancel_followup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
PID_FILE="${POLYCLAUDE_DIR}/notes/.followup_pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "no pending followup"
    exit 0
fi

pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    # Identity check before kill (2026-07-16 audit): PID reuse after reboot
    # can point this file at an unrelated daemon.
    if ps -o args= -p "$pid" 2>/dev/null | grep -qE 'inject_prompt\.sh|sleep'; then
        kill "$pid" 2>/dev/null && echo "cancelled followup pid=$pid"
    else
        echo "pid $pid is NOT a followup process (PID reuse) — not killing"
    fi
else
    echo "stale pid file (process $pid no longer running)"
fi
rm -f "$PID_FILE"
