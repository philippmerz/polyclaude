#!/bin/bash
# Box replacement for the VM crontab (no cron on the box).
#   - daemon_keepalive.sh every 10 min (revives the 6 watchers; first run at start)
#   - arb_cron.sh hourly at :30
#   - wake_webhook.py replay every 10 min (flushes pending wakes once configured)
# Singleton via flock. Start:  setsid nohup scripts/box_supervisor.sh >> logs/box_supervisor.log 2>&1 < /dev/null &
# Stop:   scripts/box_ctl.sh stop
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/box_env.sh"
cd "${POLYCLAUDE_REPO}" || exit 1
mkdir -p logs
exec 8>"${POLYCLAUDE_REPO}/logs/.box_supervisor.lock"
flock -n 8 || { echo "$(date -u +%FT%TZ) supervisor already running"; exit 0; }
echo $$ > "${POLYCLAUDE_REPO}/logs/.box_supervisor.pid"
echo "$(date -u +%FT%TZ) box_supervisor start pid=$$"
trap 'echo "$(date -u +%FT%TZ) box_supervisor got SIGTERM, exiting"; exit 0' TERM
trap 'echo "$(date -u +%FT%TZ) box_supervisor got SIGINT, exiting"; exit 0' INT
trap 'echo "$(date -u +%FT%TZ) box_supervisor got SIGHUP, ignoring"' HUP
trap 'rc=$?; echo "$(date -u +%FT%TZ) box_supervisor exit rc=$rc"' EXIT
last_keep=0; last_arb_hour=""; previous_iteration=0
while :; do
    now=$(date +%s); min=$(date -u +%M); hour=$(date -u +%Y%m%d%H)
    touch logs/.box_supervisor.heartbeat
    if (( previous_iteration > 0 && now - previous_iteration > 120 )); then
        echo "$(date -u +%FT%TZ) resume detected: gap=$((now - previous_iteration))s"
        last_keep=0
    fi
    previous_iteration=$now
    if (( now - last_keep >= 600 )); then
        timeout 300 bash scripts/daemon_keepalive.sh 8>&- || echo "$(date -u +%FT%TZ) keepalive rc=$?"
        timeout 120 .venv/bin/python scripts/wake_webhook.py replay >> logs/wake_replay.log 2>&1 8>&-
        last_keep=$now
    fi
    if [[ "$min" == "30" && "$hour" != "$last_arb_hour" ]]; then
        last_arb_hour=$hour
        ( bash scripts/arb_cron.sh 8>&- ) &
    fi
    sleep 20 8>&-
done
