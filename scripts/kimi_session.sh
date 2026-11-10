#!/bin/bash
# Start or check the long-lived Kimi (OpenCode K3.1 Pro) operator TUI.
# Usage: kimi_session.sh {ensure|status|stop|fresh|heal}
#   fresh: kill and start a NEW OpenCode session (no -c), for a poisoned session.
#   heal:  restart fresh only if the pane shows the empty-assistant-message error.
set -u
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/box_env.sh"
SESSION="${POLYCLAUDE_OPENCODE_SESSION:-kimi}"
OPENCODE_BIN="${POLYCLAUDE_OPENCODE_BIN:-${HOME}/.local/bin/opencode}"
LOG="${POLYCLAUDE_REPO}/logs/kimi_session.log"
mkdir -p "${POLYCLAUDE_REPO}/logs"

session_live() { tmux has-session -t "=${SESSION}" 2>/dev/null; }
pane_cmd() { tmux list-panes -t "=${SESSION}" -F '#{pane_current_command}' 2>/dev/null | head -n1; }

start_session() {
    if [[ ! -x "${OPENCODE_BIN}" ]]; then
        echo "$(date -u +%FT%TZ) kimi_session: opencode missing at ${OPENCODE_BIN}" >> "${LOG}"
        return 1
    fi
    # Continue the last project session when one exists so a restart keeps context.
    local extra=()
    if [[ "${KIMI_FRESH:-0}" != "1" && -f "${HOME}/.local/share/opencode/opencode.db" ]]; then
        extra+=(-c)
    fi
    tmux new-session -d -s "${SESSION}" -x 160 -y 48 -c "${POLYCLAUDE_REPO}" \
        -e "HOME=${HOME}" \
        -e "PATH=${PATH}" \
        -e "TERM=xterm-256color" \
        -e "POLYCLAUDE_REPO=${POLYCLAUDE_REPO}" \
        "${OPENCODE_BIN}" "${extra[@]}"
    echo "$(date -u +%FT%TZ) kimi_session: started pid-check next" >> "${LOG}"
    sleep 2
    session_live
}

case "${1:-status}" in
  ensure)
    if session_live && [[ "$(pane_cmd)" == "opencode" ]]; then
        echo "kimi session live"
        exit 0
    fi
    if session_live; then
        echo "$(date -u +%FT%TZ) kimi_session: session up but pane=$(pane_cmd); restarting" >> "${LOG}"
        tmux kill-session -t "=${SESSION}" 2>/dev/null || true
        sleep 1
    fi
    if start_session; then
        echo "kimi session started"
        exit 0
    fi
    echo "kimi session failed to start" >&2
    exit 1
    ;;
  fresh)
    tmux kill-session -t "=${SESSION}" 2>/dev/null || true
    sleep 1
    echo "$(date -u +%FT%TZ) kimi_session: fresh restart (no -c)" >> "${LOG}"
    if KIMI_FRESH=1 start_session; then echo "kimi fresh session started"; exit 0; fi
    echo "kimi fresh session failed to start" >&2; exit 1
    ;;
  heal)
    if session_live && tmux capture-pane -pt "=${SESSION}:" -S -200 2>/dev/null \
         | grep -q "role 'assistant' must not be empty\|role assistant must not be empty"; then
        echo "$(date -u +%FT%TZ) kimi_session: poisoned session detected; fresh restart" >> "${LOG}"
        exec "$0" fresh
    fi
    echo "kimi session not poisoned"
    ;;
  status)
    if session_live; then
        echo "kimi: live pane=$(pane_cmd)"
        exit 0
    fi
    echo "kimi: absent"
    exit 1
    ;;
  stop)
    if session_live; then
        tmux kill-session -t "=${SESSION}"
        echo "kimi session stopped"
    else
        echo "kimi session already absent"
    fi
    ;;
  *)
    echo "usage: kimi_session.sh {ensure|status|stop|fresh|heal}" >&2
    exit 2
    ;;
esac
