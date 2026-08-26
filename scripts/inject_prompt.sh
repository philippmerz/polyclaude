#!/usr/bin/env bash
# Queue a prompt for the long-lived operator agent.
#
# Usage:
#   ./scripts/inject_prompt.sh "<prompt text>"
#
# The host-private runtime resolves the active conversation and uses its
# durable follow-up queue. No terminal keystrokes are sent: input can never
# become a shell command or alter the operator's current in-progress turn.

set -euo pipefail

PROMPT="${1:?usage: inject_prompt.sh '<prompt text>'}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
RUNNER="${POLYCLAUDE_AGENT_RUNNER:-${HOME}/.local/bin/polyclaude-agent}"
LOG="${POLYCLAUDE_DIR}/notes/inject_log.md"

if [[ ! -x "${RUNNER}" ]]; then
    echo "ERROR: operator runtime is unavailable" >&2
    exit 127
fi

# For recurring continuation/meta-reflection checks only, preserve the
# skip-if-idle behavior. Detection is best-effort and fail-open.
case "${PROMPT}" in
  "Continuation check:"*|"Meta-reflection cycle:"*)
    last_reply="$("${RUNNER}" last-reply --workdir "${POLYCLAUDE_DIR}" 2>/dev/null || true)"
    if printf '%s' "${last_reply}" | grep -qiE '^idle'; then
        {
            echo ""
            echo "## $(date -u +%Y-%m-%dT%H:%M:%SZ) — inject SKIPPED (operator idle; auto-cancel)"
            echo "${PROMPT}"
        } >> "${LOG}"
        echo "skipped (operator idle): continuation/meta check not queued"
        exit 0
    fi
    ;;
esac

QUEUE_RC=0
printf '%s' "${PROMPT}" | "${RUNNER}" queue --workdir "${POLYCLAUDE_DIR}" || QUEUE_RC=$?
if (( QUEUE_RC != 0 )); then
    {
        echo ""
        echo "## $(date -u +%Y-%m-%dT%H:%M:%SZ) — inject FAILED (operator queue rc=${QUEUE_RC})"
        echo "${PROMPT}"
    } >> "${LOG}"
    echo "ERROR: operator queue failed (rc=${QUEUE_RC})" >&2
    exit "${QUEUE_RC}"
fi

{
    echo ""
    echo "## $(date -u +%Y-%m-%dT%H:%M:%SZ) — inject QUEUED"
    echo "${PROMPT}"
} >> "${LOG}"

echo "queued. logged to ${LOG}"
