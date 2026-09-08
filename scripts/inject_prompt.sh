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

# Scheduled in-chat work is one bounded run: the queue delivers the scheduled
# seed prompt and its resource/safety context. Cron and event watchers handle
# waiting for the next run; this dispatcher must not recreate an indefinite
# continuation goal or idle self-follow-up.
QUEUE_PROMPT="${PROMPT}"
BOUNDED_CONTRACT_APPENDED=0
case "${PROMPT}" in
  "Cron tick "*|"Periodic check:"*|"Sunday weekly long-term review."*)
    USAGE_PROBE="${POLYCLAUDE_USAGE_PROBE:-${SCRIPT_DIR}/check_usage.sh}"
    USAGE_SNAPSHOT="unavailable (refresh with ./scripts/check_usage.sh --brief)"
    if [[ -x "${USAGE_PROBE}" ]]; then
        if ! USAGE_SNAPSHOT=$("${USAGE_PROBE}" --brief --no-token-usage 2>/dev/null); then
            # Quota telemetry is advisory. A broken probe must never suppress a
            # scheduled portfolio/risk check.
            USAGE_SNAPSHOT="unavailable (probe failed; refresh with ./scripts/check_usage.sh --brief)"
        fi
    fi
    # Keep an unexpected provider response from bloating the scheduled turn.
    USAGE_SNAPSHOT="${USAGE_SNAPSHOT:0:2000}"
    QUEUE_PROMPT="${PROMPT}

BOUNDED RUN CONTRACT: This is one scheduled in-chat run. Execute the due check or trigger once, complete the concrete necessary follow-up or verification within this run, and end when the work is done or there is no actionable work. Do not create or maintain an indefinite durable goal, schedule idle self-follow-ups, or continue merely because this tick is quiet; cron and event watchers handle waiting for the next run. This supersedes earlier scheduled instructions requiring perpetual goal continuation (operator-authorized 2026-09-08). Preserve all required safety checks and finish any bounded safety follow-up needed by this run.

RESOURCE SNAPSHOT (read-only, captured by the dispatcher):
${USAGE_SNAPSHOT}

RESOURCE CONTRACT: Use the main-Codex headroom above to reserve the primary context for portfolio/risk judgment and route bounded routine work to cheaper subagents. Refresh with ./scripts/check_usage.sh --brief before unusually expensive discretionary research. Never skip a required safety check or delay a thesis-break exit merely to conserve quota. The quota probe is direct and read-only; do not inject /usage as a conversational turn."
    BOUNDED_CONTRACT_APPENDED=1
    ;;
esac

if [[ ! -x "${RUNNER}" ]]; then
    echo "ERROR: operator runtime is unavailable" >&2
    exit 127
fi

QUEUE_RC=0
printf '%s' "${QUEUE_PROMPT}" | "${RUNNER}" queue --workdir "${POLYCLAUDE_DIR}" || QUEUE_RC=$?
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
    if (( BOUNDED_CONTRACT_APPENDED )); then
        echo "[bounded scheduled-run contract appended to queued prompt]"
        echo "[direct Codex quota-headroom contract appended to queued prompt]"
    fi
} >> "${LOG}"

echo "queued. logged to ${LOG}"
