#!/bin/bash
# Safe daemon stop/restart — NEVER use pkill/pgrep with a pattern that also
# appears in the invoking command line.
#
# Why this exists: `pkill -f "[o]pportunity_watch.py start"` killed my own
# agent shell THREE times (exit 144, 2026-06/07 x2, 2026-07-28). The bracket
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
    local argv=()
    for d in /proc/[0-9]*; do
        local pid="${d#/proc/}"
        [[ "${pid}" == "${SELF}" ]] && continue
        [[ -r "${d}/cmdline" ]] || continue
        # A process may exit between glob expansion and this read. Capture the
        # NUL-delimited argv once and suppress that expected /proc race.
        argv=()
        mapfile -d '' -t argv 2>/dev/null < "${d}/cmdline" || continue
        # Match the actual Python script operand, not arbitrary parent-command
        # text. Accept canonical, bare, and relative paths so restart can
        # remove the historical relative-path duplicates before starting one
        # canonical process.
        if ((${#argv[@]} >= 3)) && \
           [[ "${argv[0]}" == *python* ]] && \
           [[ "${argv[2]}" == "start" ]] && \
           [[ "${argv[1]}" == "${SCRIPT}" || "${argv[1]}" == */"${SCRIPT}" ]]; then
            out+=("${pid}")
        fi
    done
    ((${#out[@]} > 0)) && printf '%s\n' "${out[@]}"
}

case "${ACTION}" in
  status)
    mapfile -t pids < <(find_pids)
    if ((${#pids[@]} == 0)); then
        echo "${SCRIPT}: <not running>"
    else
        echo "${SCRIPT}: ${pids[*]}"
    fi
    ;;
  stop|restart)
    mapfile -t pids < <(find_pids)
    for pid in "${pids[@]}"; do
        kill "${pid}" 2>/dev/null && echo "stopped pid ${pid}"
    done
    sleep 2
    mapfile -t left < <(find_pids)
    if ((${#left[@]} > 0)); then
        for pid in "${left[@]}"; do kill -9 "${pid}" 2>/dev/null; done
        sleep 1
        mapfile -t left < <(find_pids)
        if ((${#left[@]} > 0)); then
            echo "ERROR: refusing restart; ${SCRIPT} survived stop: ${left[*]}" >&2
            exit 1
        fi
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
        spawned=$!
        sleep 3
        mapfile -t pids < <(find_pids)
        if ((${#pids[@]} != 1)); then
            echo "ERROR: restart expected exactly one ${SCRIPT}; found ${#pids[@]} (${pids[*]:-none})" >&2
            # Remove only the process this invocation created. If another
            # supervisor won the race, leave its single canonical worker live.
            kill "${spawned}" 2>/dev/null || true
            wait "${spawned}" 2>/dev/null || true
            exit 1
        fi
        echo "restarted: ${pids[0]}"
        exit 0
    fi
    ;;
  *)
    echo "unknown action: ${ACTION}" >&2; exit 2 ;;
esac
