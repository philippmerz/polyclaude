#!/bin/bash
# Box replacement for the VM crontab (no cron on the box).
#   - daemon_keepalive.sh every 10 min (revives the 6 watchers; first run at start)
#   - kimi_session.sh ensure/heal: DISABLED 2026-11-20 (kimi.com sub cancelled; do not respawn)
#   - daily_checkin.sh 3-hourly Kimi auto-wake + sleep catch-up: DISABLED 2026-11-20
#   - arb_cron.sh hourly at :30
#   - wake_webhook.py replay every 10 min (pending outbox wakes/alerts to Grok Bot)
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
        # Kimi/OpenCode tmux retired 2026-11-20. To restore: uncomment the next two
        # lines and set POLYCLAUDE_OPERATOR_MODE=opencode in box_env.sh.
        # timeout 60 bash scripts/kimi_session.sh ensure >> logs/kimi_session.log 2>&1 8>&- || echo "$(date -u +%FT%TZ) kimi_session ensure rc=$?"
        # timeout 60 bash scripts/kimi_session.sh heal >> logs/kimi_session.log 2>&1 8>&- || echo "$(date -u +%FT%TZ) kimi_session heal rc=$?"
        timeout 120 .venv/bin/python scripts/wake_webhook.py replay >> logs/wake_replay.log 2>&1 8>&-
        last_keep=$now
    fi
    # 3-hourly Kimi check-in + sleep catch-up retired 2026-11-20. Event wakes
    # still go to the Grok Bot webhook (wake_webhook.py). news_watcher critical
    # reviews use daily_checkin.sh; opportunity_watch uses the existing telegram
    # alert path only, so the same hit is not also queued as a wake.
    if [[ "$min" == "30" && "$hour" != "$last_arb_hour" ]]; then
        last_arb_hour=$hour
        ( bash scripts/arb_cron.sh 8>&- ) &
    fi
    sleep 20 8>&-
done
