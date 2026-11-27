#!/bin/bash
# Boot/restore self-heal for the polyclaude box daemons.
#
# Why: the box has no cron/systemd (PID1 is tini -> pod-daemon; `crontab` is not
# installed and nothing runs user init scripts), and box restarts/restores have
# repeatedly left the supervisor + 6 watchers dead for 1-3h (26 Nov ~1h gap), and
# restores wipe the git-ignored .venv and clob_node/node_modules.
#
# This script is idempotent and safe to call from anywhere, any number of times:
#   - fast path: supervisor alive with fresh heartbeat -> exit 0 immediately
#   - rebuild .venv / node_modules only if missing or broken
#   - then `box_ctl.sh ensure` (which itself flocks and never duplicates)
# Hooked from: ~/.bashrc + ~/.profile (any interactive/login shell, e.g. the tmux
# operator), ~/.config/autostart (desktop session start), and the first command
# of every operator/review session.  Usage: boot_ensure.sh [--quiet]
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1
mkdir -p logs
LOG=logs/boot_ensure.log
say() { [[ "${1:-}" ]] && echo "$(date -u +%FT%TZ) $*" >> "$LOG"; }

sup_alive() {
    local p; p=$(cat logs/.box_supervisor.pid 2>/dev/null) || return 1
    [[ -n "$p" ]] && grep -q box_supervisor "/proc/$p/cmdline" 2>/dev/null || return 1
    [[ -e logs/.box_supervisor.heartbeat ]] || return 1
    (( $(date +%s) - $(stat -c %Y logs/.box_supervisor.heartbeat) < 180 ))
}
[[ -e logs/.box_supervisor.stopped ]] && exit 0      # intentional stop: respect it
sup_alive && exit 0

exec 6>/tmp/polyclaude_boot_ensure.lock
flock -n 6 || exit 0                                  # another heal already running
sup_alive && exit 0

if ! .venv/bin/python3 -c 'import httpx' >/dev/null 2>&1; then
    say "venv missing/broken; rebuilding"
    { python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt; } >> "$LOG" 2>&1 \
        || say "venv rebuild FAILED rc=$?"
fi
if [[ -f scripts/clob_node/package.json && ! -d scripts/clob_node/node_modules ]]; then
    say "clob_node/node_modules missing; npm ci"
    ( cd scripts/clob_node && { npm ci --silent || npm install --silent; } ) >> "$LOG" 2>&1 \
        || say "npm install FAILED rc=$?"
fi
say "supervisor dead/stale (boot or restore?); running box_ctl ensure (caller=${BOOT_ENSURE_CALLER:-manual} uptime=$(cut -d' ' -f1 /proc/uptime)s)"
bash scripts/box_ctl.sh ensure 6>&- >> "$LOG" 2>&1
rc=$?
sup_alive && say "ensure ok rc=$rc" || say "ensure rc=$rc but supervisor still not healthy"
exit $rc
