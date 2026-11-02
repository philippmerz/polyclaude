#!/bin/bash
# Box daemon control.  box_ctl.sh {start|stop|status|restart}
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/box_env.sh"
cd "${POLYCLAUDE_REPO}" || exit 1
DAEMONS="resting_watch source_watch news_watcher opportunity_watch heartbeat_watch telegram_listener"
sup_pid() { local p; p=$(cat logs/.box_supervisor.pid 2>/dev/null) || return 1; [[ -n "$p" ]] && grep -q box_supervisor "/proc/$p/cmdline" 2>/dev/null && echo "$p"; }
case "${1:-status}" in
  start)
    if sup_pid >/dev/null; then echo "supervisor already running: $(sup_pid)"; else
      setsid nohup bash scripts/box_supervisor.sh >> logs/box_supervisor.log 2>&1 < /dev/null &
      sleep 8; fi
    "$0" status ;;
  stop)
    if p=$(sup_pid); then
      kill "$p" && echo "stopped supervisor $p"
      # bash defers exit until its foreground sleep returns; wait so restart can take the lock
      for _ in $(seq 1 30); do kill -0 "$p" 2>/dev/null || break; sleep 1; done
    fi
    for d in $DAEMONS; do bash scripts/daemonctl.sh stop "$d"; done ;;
  restart) "$0" stop; sleep 2; "$0" start ;;
  status)
    echo "supervisor: $(sup_pid || echo '<not running>')"
    for d in $DAEMONS; do bash scripts/daemonctl.sh status "$d"; done
    .venv/bin/python scripts/wake_webhook.py status ;;
  *) echo "usage: box_ctl.sh {start|stop|status|restart}"; exit 2 ;;
esac
