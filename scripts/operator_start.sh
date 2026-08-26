#!/usr/bin/env bash
# Spawn the long-lived PolyClaude operator in one tmux session.
#
# Usage:
#   pc-attach --start
#   pc-attach
#
# The host-private runtime owns provider/model details and writes the active
# conversation identifier used by scheduled and Telegram follow-ups.

set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
SESSION_NAME="operator"
RUNNER="${POLYCLAUDE_AGENT_RUNNER:-${HOME}/.local/bin/polyclaude-agent}"
LOG_DIR="${POLYCLAUDE_DIR}/logs/operator"
LOG_FILE="${LOG_DIR}/operator_$(date -u +%Y%m%dT%H%M%SZ).log"
INITIAL_PROMPT="Initialization check only. Do not use tools, change files, access assets, or send messages. Reply exactly OPERATOR_READY."

export PATH="${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
mkdir -p "${LOG_DIR}"
chmod 700 "${POLYCLAUDE_DIR}/logs" "${LOG_DIR}"

if tmux has-session -t "=${SESSION_NAME}" 2>/dev/null; then
    echo "operator session already running."
    echo "  attach: tmux attach -t ${SESSION_NAME}"
    exit 0
fi

if [[ ! -x "${RUNNER}" ]]; then
    echo "ERROR: operator runtime is missing or not executable" >&2
    exit 69
fi

if ! timeout 15 "${RUNNER}" status >/dev/null; then
    echo "ERROR: operator runtime authentication/health check failed" >&2
    exit 78
fi

printf -v CHILD_CMD '%q interactive --workdir %q --initial-prompt %q' \
    "${RUNNER}" "${POLYCLAUDE_DIR}" "${INITIAL_PROMPT}"
printf -v TMUX_CMD '%q -q -f -e -c %q %q' /usr/bin/script "${CHILD_CMD}" "${LOG_FILE}"

echo "starting operator session"
echo "  attach: pc-attach"
echo "  log:    ${LOG_FILE}"

tmux new-session -d -s "${SESSION_NAME}" -c "${POLYCLAUDE_DIR}" "${TMUX_CMD}"

if ! thread_id="$("${RUNNER}" wait-ready --workdir "${POLYCLAUDE_DIR}" --timeout 30)"; then
    echo "ERROR: operator launched but did not expose a queueable conversation" >&2
    tmux kill-session -t "=${SESSION_NAME}" 2>/dev/null || true
    exit 70
fi

chmod 600 "${LOG_FILE}" 2>/dev/null || true
echo "operator ready (thread ${thread_id})."
echo "Attach with pc-attach. Detach with Ctrl-B then D; do not exit the agent."
