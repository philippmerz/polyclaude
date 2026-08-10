#!/bin/bash
# Safe daemon stop/restart — NEVER use pkill/pgrep with a pattern that also
# appears in the invoking command line.
#
# Why this exists: `pkill -f "[o]pportunity_watch.py start"` killed my own
# claude shell THREE times (exit 144, 2026-06/07 x2, 2026-07-28). The bracket
# trick only works if the pattern appears ONCE in the command line — any later
# plain reference (a nohup restart, a pgrep verify, an echo) re-creates the
# self-match. This script matches on /proc/<pid>/cmdline of OTHER pids only,
# and can never match the caller because the caller's cmdline is "bash
# daemonctl.sh <name>", not the daemon's.
#
# Usage:
#   daemonctl.sh stop    <script.py>     # kill the daemon, verify gone
#   daemonctl.sh restart <script.py>     # stop, then start detached
#   daemonctl.sh status  <script.py>     # list matching pids
set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${REPO}/.venv/bin/python3"
ACTION="${1:-status}"
SCRIPT="${2:-}"
[[ -z "${SCRIPT}" ]] && { echo "usage: daemonctl.sh {stop|restart|status} <script.py>" >&2; exit 2; }
# Name normalisation (2026-08-10): calling this with a bare name ("restart
# opportunity_watch") matched NO pids — so the running daemon was never
# stopped — and then nohup'd a nonexistent path that died instantly. The
# failure was survivable only because the old process kept running; with the
# arguments in the other order it would have left NO daemon at all.
[[ "${SCRIPT}" != *.py ]] && SCRIPT="${SCRIPT}.py"
[[ -f "${REPO}/scripts/${SCRIPT}" ]] || { echo "no such daemon script: scripts/${SCRIPT}" >&2; exit 2; }

SELF=$$
find_pids() {
    local out=()
    for d in /proc/[0-9]*; do
        local pid="${d#/proc/}"
        [[ "${pid}" == "${SELF}" ]] && continue
        # cmdline is NUL-separated; match the script path as its own argument
        if tr '\0' '\n' < "${d}/cmdline" 2>/dev/null | grep -qx ".*/${SCRIPT}\|${SCRIPT}"; then
            # exclude anything that isn't a python invocation of the script
            if tr '\0' '\n' < "${d}/cmdline" 2>/dev/null | head -1 | grep -q 'python'; then
                out+=("${pid}")
            fi
        fi
    done
    printf '%s\n' "${out[@]:-}"
}

case "${ACTION}" in
  status)
    pids=$(find_pids | tr '\n' ' ')
    echo "${SCRIPT}: ${pids:-<not running>}"
    ;;
  stop|restart)
    for pid in $(find_pids); do
        [[ -z "${pid}" ]] && continue
        kill "${pid}" 2>/dev/null && echo "stopped pid ${pid}"
    done
    sleep 2
    left=$(find_pids | tr -d '[:space:]')
    if [[ -n "${left}" ]]; then
        for pid in $(find_pids); do [[ -n "${pid}" ]] && kill -9 "${pid}" 2>/dev/null; done
        sleep 1
    fi
    if [[ "${ACTION}" == "restart" ]]; then
        cd "${REPO}" || exit 1
        # ABSOLUTE script path required: daemon_keepalive.sh's alive() regex
        # matches the exact cmdline form "<python3> <abs-path> start" — a
        # relative-path daemon is invisible to it and gets DUPLICATED on the
        # next 10-min keepalive pass (observed 2026-07-29: 7.5h of two
        # opportunity_watch instances after a relative-path restart).
        # Log name must match daemon_keepalive.sh's convention (incl. the
        # heartbeat_watch special case) or the daemon's output ALTERNATES
        # between two files depending on which mechanism last started it
        # (observed 2026-07-30: heartbeat alerts split across heartbeat.log
        # and heartbeat_watch.log).
        LOGNAME="${SCRIPT%.py}.log"
        [[ "${SCRIPT}" == "heartbeat_watch.py" ]] && LOGNAME="heartbeat.log"
        nohup "${PY}" "${REPO}/scripts/${SCRIPT}" start >> "logs/${LOGNAME}" 2>&1 &
        sleep 3
        pids=$(find_pids | tr '\n' ' ')
        echo "restarted: ${pids:-<FAILED TO START>}"
        [[ -z "${pids// /}" ]] && exit 1
    fi
    ;;
  *)
    echo "unknown action: ${ACTION}" >&2; exit 2 ;;
esac
