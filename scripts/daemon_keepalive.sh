#!/bin/bash
# Generic daemon keepalive — revives any dead 24/7 daemon every 10 min.
#
# Exists because of two audited failure modes (2026-07-16):
#   1. The old inline-crontab oppwatch keepalive was DEAD CODE: cron wraps the
#      line in `/bin/sh -c`, so the wrapper's own cmdline contained the pgrep
#      pattern (even [o]-bracketed patterns lose when the nohup restart text in
#      the same -c string carries the plain string) — pgrep always matched and
#      the restart branch never ran. In a dedicated script, the daemon names
#      live in variables/args; this file's own cmdline is just
#      "bash .../daemon_keepalive.sh" and can never self-match.
#   2. heartbeat_watch / telegram_listener / news_watcher were @reboot-only:
#      a mid-life death (OOM kill, crash) stayed down until the next reboot.
#      The watchdog watching everything else had no watcher.
#
# Identity check is /proc/<pid>/cmdline-based (PID files go stale across
# reboots and can point at unrelated processes — audited class).

set -u
REPO="/home/polyclaude/polyclaude"
PY="${REPO}/.venv/bin/python3"
LOG="${REPO}/logs/daemon_keepalive.log"

exec 9>"/tmp/daemon_keepalive.lock"
flock -n 9 || exit 0

alive() {  # alive <script-abs-path> — a live daemon running "<python> <script> start"?
    # Share daemonctl's positional /proc argv matching so relative script paths
    # count without matching parent command text. Status also exits zero when
    # nothing is running, so inspect the PID field rather than its exit code.
    local script="$1" output pids
    output=$("${REPO}/scripts/daemonctl.sh" status "${script##*/}" 2>/dev/null) || return 1
    pids="${output#*: }"
    [[ "$pids" =~ ^[0-9]+([[:space:]]+[0-9]+)*$ ]]
}

revive() {  # revive <needle> <python> <script-abs-path> start
    local needle="$1"; shift
    local script="$2"
    if alive "$script"; then
        return 0
    fi
    echo "$(date -u +%Y%m%dT%H%M%SZ) reviving: $needle" >> "$LOG"
    local logname="${needle%%.py*}.log"
    [[ "$needle" == "heartbeat_watch.py" ]] && logname="heartbeat.log"
    # 9>&- : do NOT let the daemon inherit the flock FD — an inherited lock
    # FD is held for the daemon's lifetime and every later keepalive run
    # would silently exit at flock -n (bit us within minutes of shipping).
    nohup "$@" >> "${REPO}/logs/${logname}" 2>&1 9>&- &
}

revive "opportunity_watch.py"  "$PY" "${REPO}/scripts/opportunity_watch.py" start
revive "heartbeat_watch.py"    "$PY" "${REPO}/scripts/heartbeat_watch.py" start
revive "telegram_listener.py"  "$PY" "${REPO}/scripts/telegram_listener.py" start
revive "news_watcher.py"       "$PY" "${REPO}/scripts/news_watcher.py" start
revive "resting_watch.py"      "$PY" "${REPO}/scripts/resting_watch.py" start
revive "source_watch.py"       "$PY" "${REPO}/scripts/source_watch.py" start
exit 0
