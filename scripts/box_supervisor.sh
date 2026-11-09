#!/bin/bash
# Box replacement for the VM crontab (no cron on the box).
#   - daemon_keepalive.sh every 10 min (revives the 6 watchers; first run at start)
#   - kimi_session.sh ensure every 10 min (OpenCode K3.1 Pro TUI in tmux 'kimi')
#   - daily_checkin.sh at 00,03,06,09,12,15,18,21 UTC (Kimi auto-wake; independent of Grok Bot)
#   - arb_cron.sh hourly at :30
#   - wake_webhook.py replay every 10 min (unused leftover; harmless if empty)
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
last_keep=0; last_arb_hour=""; last_checkin_hour=""; previous_iteration=0
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
        timeout 60 bash scripts/kimi_session.sh ensure >> logs/kimi_session.log 2>&1 8>&- || echo "$(date -u +%FT%TZ) kimi_session ensure rc=$?"
        timeout 120 .venv/bin/python scripts/wake_webhook.py replay >> logs/wake_replay.log 2>&1 8>&-
        last_keep=$now
    fi
    # Kimi auto-wake: one check-in per 3-hour UTC block (00,03,...,21). Keyed on the
    # block rather than the exact hour so a block missed while the box slept still
    # gets one catch-up check-in on resume.
    utc_hour=$(date -u +%H)
    block="$(date -u +%Y%m%d)$(printf '%02d' $(( (10#$utc_hour / 3) * 3 )))"
    if [[ "$block" != "$last_checkin_hour" ]]; then
        stamp_file=logs/.kimi_checkin_hour
        prev=$(cat "$stamp_file" 2>/dev/null || true)
        last_checkin_hour=$block
        if [[ "$prev" != "$block" ]]; then
            echo "$block" > "$stamp_file"
            mkdir -p logs/cron
            echo "$(date -u +%FT%TZ) scheduling Kimi check-in for block=$block" >> logs/box_supervisor.log
            ( bash scripts/daily_checkin.sh 8>&- >> "logs/cron/checkin_$(date -u +%Y%m%dT%H%M%SZ).log" 2>&1 ) &
        fi
    fi
    if [[ "$min" == "30" && "$hour" != "$last_arb_hour" ]]; then
        last_arb_hour=$hour
        ( bash scripts/arb_cron.sh 8>&- ) &
    fi
    sleep 20 8>&-
done
