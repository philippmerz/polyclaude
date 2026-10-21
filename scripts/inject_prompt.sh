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
# Preserve the historical Markdown log; future appends are metadata-only JSON
# lines so the heartbeat's mtime check remains useful without storing prompts.

# The old mixed stock/brokerage review was retired 2026-10-06. Reject its
# legacy seed before quota probes, operator delivery, or inject-log writes.
case "${PROMPT}" in
  "Sunday weekly long-term review."*)
    echo "Retired stock/brokerage review: no work queued."
    exit 0
    ;;
esac

# Scheduled in-chat work is one bounded run: the queue delivers the scheduled
# seed prompt and its resource/safety context. Cron and event watchers handle
# waiting for the next run; this dispatcher must not recreate an indefinite
# continuation goal or idle self-follow-up.
QUEUE_PROMPT="${PROMPT}"
BOUNDED_CONTRACT_APPENDED=0
case "${PROMPT}" in
  "Cron tick "*|"Periodic check:"*)
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

FINITE GOAL SCOPE: This contract bounds scheduled work only. It does not revoke separate authorization for a finite goal or change that goal's lifecycle. In the session that owns an active finite goal, return to its work after due checks under its own instructions and native lifecycle rules; completing this tick is not a goal blocker. Case-specific evidence gaps do not block unrelated pending cases.

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
QUEUED_PROMPT_BYTES=$(printf '%s' "${QUEUE_PROMPT}" | wc -c)
QUEUED_PROMPT_BYTES="${QUEUED_PROMPT_BYTES//[[:space:]]/}"
QUEUED_PROMPT_SHA256=$(printf '%s' "${QUEUE_PROMPT}" | sha256sum)
QUEUED_PROMPT_SHA256="${QUEUED_PROMPT_SHA256%% *}"
ATTEMPT_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
if (( BOUNDED_CONTRACT_APPENDED )); then
    BOUNDED_CONTRACT_JSON=true
else
    BOUNDED_CONTRACT_JSON=false
fi

if (( QUEUE_RC != 0 )); then
    printf '{"ts_utc":"%s","status":"FAILED","actual_rc":%d,"queued_prompt_utf8_bytes":%s,"queued_prompt_sha256":"%s","bounded_contract":%s}\n' \
        "${ATTEMPT_UTC}" "${QUEUE_RC}" "${QUEUED_PROMPT_BYTES}" \
        "${QUEUED_PROMPT_SHA256}" "${BOUNDED_CONTRACT_JSON}" >> "${LOG}"
    echo "ERROR: operator queue failed (rc=${QUEUE_RC})" >&2
    exit "${QUEUE_RC}"
fi

printf '{"ts_utc":"%s","status":"QUEUED","actual_rc":0,"queued_prompt_utf8_bytes":%s,"queued_prompt_sha256":"%s","bounded_contract":%s}\n' \
    "${ATTEMPT_UTC}" "${QUEUED_PROMPT_BYTES}" \
    "${QUEUED_PROMPT_SHA256}" "${BOUNDED_CONTRACT_JSON}" >> "${LOG}"

echo "queued. attempt metadata logged"
