#!/bin/bash
# Spawn a transient interactive `claude` session in tmux, capture the /usage dialog,
# and print the relevant numbers. The spawned session sends no prompt, so it consumes
# zero tokens itself. Useful from cron driver to gate heavy work near limits.
#
# Output: the literal /usage dialog block (one-time grep is up to the caller).
# Exit 0 always; failure modes print "USAGE_UNAVAILABLE" so callers can degrade.

set -euo pipefail

SESSION="usage_probe_$$"
trap 'tmux kill-session -t "$SESSION" 2>/dev/null || true' EXIT

tmux new-session -d -s "$SESSION" -x 220 -y 60 'claude' 2>/dev/null || {
  echo "USAGE_UNAVAILABLE: tmux new-session failed"
  exit 0
}

# Wait for claude to fully boot (welcome screen + prompt ready)
sleep 7

# Dismiss any startup dialog (workspace trust etc.) by pressing Enter once
tmux send-keys -t "$SESSION" Enter
sleep 1

# Send /usage and submit
tmux send-keys -t "$SESSION" "/usage"
sleep 1
tmux send-keys -t "$SESSION" Enter

# Wait for dialog to render
sleep 6

# Capture the pane history
PANE=$(tmux capture-pane -t "$SESSION" -p -S -300 2>/dev/null || echo "")

if echo "$PANE" | grep -q "Current session"; then
  # Print the Status block (Status / Config / Usage / Stats and below)
  echo "$PANE" | awk '/Status   Config   Usage   Stats/{flag=1} flag' | sed '/^$/N;/^\n$/D'
else
  echo "USAGE_UNAVAILABLE: dialog did not render in time"
fi
