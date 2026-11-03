#!/bin/bash
# Box daemon control.  box_ctl.sh {start|ensure|stop|status|restart}
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/box_env.sh"
cd "${POLYCLAUDE_REPO}" || exit 1
mkdir -p logs
# Serialize recovery without letting the supervisor or daemons inherit this lock.
if [[ "${1:-status}" == "ensure" || "${1:-status}" == "start" ]]; then
    exec 7>logs/.box_ctl.lock
    flock 7
fi
DAEMONS="resting_watch source_watch news_watcher opportunity_watch heartbeat_watch telegram_listener"
sup_pid() { local p; p=$(cat logs/.box_supervisor.pid 2>/dev/null) || return 1; [[ -n "$p" ]] && grep -q box_supervisor "/proc/$p/cmdline" 2>/dev/null && echo "$p"; }
heartbeat_age() {
    if [[ -e logs/.box_supervisor.heartbeat ]]; then
        echo "$(( $(date +%s) - $(stat -c %Y logs/.box_supervisor.heartbeat) ))"
    else
        echo missing
    fi
}
start_supervisor() {
    setsid nohup bash scripts/box_supervisor.sh >> logs/box_supervisor.log 2>&1 < /dev/null 7>&- &
    sleep 8
}
case "${1:-status}" in
  ensure)
    [[ -e logs/.box_supervisor.stopped ]] && exit 0
    if p=$(sup_pid); then
        age=$(heartbeat_age)
        if [[ "$age" == missing || "$age" -lt 180 ]]; then
            timeout 300 bash scripts/daemon_keepalive.sh 7>&- >/dev/null 2>&1
            exit $?
        fi
        # Right after a VM resume every clock looks stale; give the live loop one
        # beat (it touches the heartbeat every 20s) before declaring it hung.
        sleep 30
        age=$(heartbeat_age)
        if [[ "$age" == missing || "$age" -lt 180 ]]; then
            timeout 300 bash scripts/daemon_keepalive.sh 7>&- >/dev/null 2>&1
            exit $?
        fi
        echo "$(date -u +%FT%TZ) stale supervisor pid=$p heartbeat_age=$age; stopping" >> logs/box_supervisor.log
        kill "$p" 2>/dev/null || true
        for _ in $(seq 1 30); do
            kill -0 "$p" 2>/dev/null || break
            sleep 1
        done
        # Do not start a replacement while a stale supervisor still holds the singleton.
        if kill -0 "$p" 2>/dev/null; then
            echo "$(date -u +%FT%TZ) stale supervisor pid=$p still exiting; retry later" >> logs/box_supervisor.log
            exit 1
        fi
    fi
    start_supervisor
    ;;
  start)
    rm -f logs/.box_supervisor.stopped
    if sup_pid >/dev/null; then echo "supervisor already running: $(sup_pid)"; else
      start_supervisor; fi
    "$0" status 7>&- ;;
  stop)
    # Suppress daemon guards throughout an intentional shutdown and until start.
    touch logs/.box_supervisor.stopped
    if p=$(sup_pid); then
      kill "$p" && echo "stopped supervisor $p"
      # bash defers exit until its foreground sleep returns; wait so restart can take the lock
      for _ in $(seq 1 30); do kill -0 "$p" 2>/dev/null || break; sleep 1; done
    fi
    for d in $DAEMONS; do bash scripts/daemonctl.sh stop "$d"; done ;;
  restart) "$0" stop; sleep 2; "$0" start ;;
  status)
    echo "supervisor: $(sup_pid || echo '<not running>') heartbeat_age=$(heartbeat_age)s"
    for d in $DAEMONS; do bash scripts/daemonctl.sh status "$d"; done
    .venv/bin/python scripts/wake_webhook.py status ;;
  *) echo "usage: box_ctl.sh {start|ensure|stop|status|restart}"; exit 2 ;;
esac
