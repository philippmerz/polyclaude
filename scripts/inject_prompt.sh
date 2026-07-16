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

# --- skip-if-idle guard (2026-06-04, per operator request) ------------------
# For recurring continuation/meta-reflection checks ONLY: if the operator's last
# reply was a bare "Idle", skip this injection. The continuation loop thus
# auto-pauses when idle and re-engages on the next real trigger (cron periodic
# check, daily_checkin cron, news Tier-1, operator message, or any non-idle
# reply). Cuts idle-churn + the long-session continuation-artifact surface.
# FAIL-OPEN: any error detecting the last reply -> inject normally (never go dark).
case "$PROMPT" in
  "Continuation check:"*|"Meta-reflection cycle:"*)
    last_reply="$("${POLYCLAUDE_DIR}/.venv/bin/python" - <<'PYEOF' 2>/dev/null || true
import json, glob, os
try:
    d = os.path.expanduser("~/.claude/projects/-home-polyclaude")
    files = sorted(glob.glob(d + "/*.jsonl"), key=os.path.getmtime, reverse=True)
    txt = ""
    if files:
        for line in reversed(open(files[0], errors="replace").readlines()):
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("type") == "assistant":
                for b in o.get("message", {}).get("content", []):
                    if isinstance(b, dict) and b.get("type") == "text" and b.get("text", "").strip():
                        txt = b["text"].strip()
                        break
                if txt:
                    break
    print(txt)
except Exception:
    print("")
PYEOF
)"
    if printf '%s' "$last_reply" | grep -qiE '^idle'; then
        {
            echo ""
            echo "## $(date -u +%Y-%m-%dT%H:%M:%SZ) — inject SKIPPED (operator idle; auto-cancel)"
            echo "$PROMPT"
        } >> "$LOG"
        echo "skipped (operator idle): continuation/meta check not injected"
        exit 0
    fi
    ;;
esac
# ---------------------------------------------------------------------------

# Dead-pane guard (2026-07-16 audit): the session existing is NOT proof the
# inner claude is alive — script(1) keeps the pane up after claude exits, and
# a prompt typed into the leftover bash EXECUTES as a shell command while
# inject_log.md records a successful inject. Require a live claude/node
# descendant of the pane; otherwise log the failure truthfully and exit 4.
PANE_PID=$(tmux display-message -p -t "$PANE" '#{pane_pid}' 2>/dev/null || echo "")
if [[ -z "$PANE_PID" ]] || ! pstree -p "$PANE_PID" 2>/dev/null | grep -qE 'claude|node'; then
    {
        echo ""
        echo "## $(date -u +%Y-%m-%dT%H:%M:%SZ) — inject FAILED (dead pane, no live claude)"
        echo "$PROMPT"
    } >> "$LOG"
    echo "ERROR: pane $PANE has no live claude descendant (pane_pid=$PANE_PID) — inject aborted" >&2
    exit 4
fi

# Wait up to 60s for operator pane idle (no Braille spinner).
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
