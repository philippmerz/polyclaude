#!/bin/bash
# Polyclaude check-in driver.
# Invoked by cron. Queues the tick to the long-lived operator when available;
# otherwise runs a fresh, fully onboarded headless fallback.
# Canonical 11-step checklist: docs/checkin.md. Read it; do not redispatch a live tick.

set -euo pipefail
umask 077

# Resolve repo root from this script's location (no hardcoded user path).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
LOG_DIR="${POLYCLAUDE_DIR}/logs/cron"
mkdir -p "${LOG_DIR}"

# Cross-tick lockout. Without this, a Tier-1 news_watcher firing during a
# scheduled cron window can spawn a parallel daily_checkin.sh that resumes
# the same session and races on git/journal commits. Acquire an exclusive
# lock or exit immediately (no blocking — peer-detection inside the prompt
# handles the case anyway).
LOCK_FILE="${POLYCLAUDE_DIR}/.checkin.lock"
exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
    echo "$(date -u +%Y%m%dT%H%M%SZ) checkin: lock held by another tick, exiting" \
        >> "${LOG_DIR}/peer_skips.log"
    exit 0
fi

TS=$(date -u +%Y%m%dT%H%M%SZ)
# Optional $1 = why this tick fired (opportunity_watch/news_watcher pass a reason;
# plain cron passes nothing). Surfaced in the prompt so a daemon-fired tick is
# distinguishable from a scheduled one (2026-07-28: stale-ARB-trigger fires read
# as generic ticks and got answered "nothing happened").
REASON_SUFFIX=""
if [[ -n "${1:-}" ]]; then REASON_SUFFIX=" [$1]"; fi
LOG_FILE="${LOG_DIR}/checkin_${TS}.log"

# Ensure a working PATH for cron. HOME must be resolved before PATH.
export HOME="${HOME:-$(getent passwd "$(id -un)" | cut -d: -f6)}"
export PATH="${HOME}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# A queue acknowledgement is the dispatch boundary. It is safe while the
# operator is busy and cannot turn prompt text into terminal or shell input.
# POLYCLAUDE_FORCE_HEADLESS=1 is reserved for an explicit operator drill/recovery.
CRON_MSG="Cron tick ${TS}. Run your scheduled polyclaude check-in (11-step list in docs/checkin.md). Brief if nothing happened.${REASON_SUFFIX}"
if [[ "${POLYCLAUDE_FORCE_HEADLESS:-}" == "1" ]]; then
    echo "$(date -u +%Y%m%dT%H%M%SZ) checkin: FORCE_HEADLESS set — skipping operator queue" \
        >> "${LOG_DIR}/peer_skips.log"
else
    INJECT_RC=0
    "${SCRIPT_DIR}/inject_prompt.sh" "${CRON_MSG}" >/dev/null 2>&1 || INJECT_RC=$?
    case "${INJECT_RC}" in
      0)
        echo "$(date -u +%Y%m%dT%H%M%SZ) cron: queued to operator; exiting" \
            >> "${LOG_DIR}/peer_skips.log"
        exit 0
        ;;
      69)
        # The private runtime owns rc=69 and emits it only before dispatch,
        # after proving there is no live operator process. This is the sole
        # automatic path allowed to start another asset-capable worker.
        echo "$(date -u +%Y%m%dT%H%M%SZ) cron: no live operator — using headless fallback" \
            >> "${LOG_DIR}/peer_skips.log"
        ;;
      *)
        # A timeout can mean the queue accepted the message before the caller
        # lost its acknowledgement. Fail closed so one tick can never run in
        # both the interactive operator and a fresh autonomous process.
        echo "$(date -u +%Y%m%dT%H%M%SZ) cron: queue failed rc=${INJECT_RC}; no headless fallback (exact-one safety)" \
            >> "${LOG_DIR}/peer_skips.log"
        exit "${INJECT_RC}"
        ;;
    esac
fi

# Load polyclaude path config (env vars for secret/state file locations).
# File lives outside the repo at $HOME/.polyclaude/env, mode 0600.
if [[ -f "${HOME}/.polyclaude/env" ]]; then
    # shellcheck disable=SC1091
    set -a; source "${HOME}/.polyclaude/env"; set +a
fi

# The fallback reads the same canonical checklist used by in-chat ticks.
PROMPT=$(<"${POLYCLAUDE_DIR}/docs/checkin.md")

# Run from the repository so the fallback loads the private operator contract.
cd "${POLYCLAUDE_DIR}"

{
  echo "=== polyclaude daily check-in ${TS} ==="
  echo "$ pwd"; pwd
  echo "$ headless fallback (fresh session + primer)"
  # Preserve the exit trailer and auth post-flight even on worker failure.
  RC=0
  PRIMER="You are polyclaude's autonomous FALLBACK session: the interactive operator queue was unreachable or explicitly bypassed, so you are running this scheduled tick headless with NO inherited conversation context.

Onboard first, in this order: read docs/START.md, the compact README.md dashboard and strategy/00_philosophy.md. Then read the complete docs/checkin.md checklist below and carry it out once. Load topic references only when needed; do not preload PRIMER, lesson archives, or the full journal. The checklist itself obtains live state, so do not run a duplicate status pass.

Follow the operator mandate and all existing strategy and execution safeguards. Verify facts independently; missing context or unknown safety inputs must not become permission to act. Journal the full check; Telegram only material content, noting the fallback.

--- SCHEDULED CHECK-IN ---
"
  printf '%s' "${PRIMER}${PROMPT}" | \
    "${HOME}/.local/bin/polyclaude-agent" run \
      --profile main --effort max --access autonomous \
      --cwd "${POLYCLAUDE_DIR}" --timeout 7200 \
      2>&1 || RC=$?
  echo
  echo "=== exit ${RC} at $(date -u) ==="
} >> "${LOG_FILE}" 2>&1

# Creds/auth post-flight (2026-07-02 audit, outage-hardening part 2 of 2).
# 4 outages in ~3 weeks were expired-creds: the headless fallback fails fast
# with an auth error in the log, no tick output is produced, and nobody is
# told. The heartbeat dead-man switch catches the *pattern* within ~16h;
# this catches the *cause* on the very first failed tick and pings the
# operator directly (LLM-independent path). Fires at most 2x/day (per tick).
if tail -n 40 "${LOG_FILE}" | grep -qiE "authentication|unauthorized|401|invalid.*(api key|token|credential)|OAuth.*(expired|error)|please.*log ?in|/login"; then
    cd "${POLYCLAUDE_DIR}" && .venv/bin/python scripts/telegram.py msg \
      "[CHECKIN] tick ${TS} FAILED with an auth error — agent credentials likely expired. Ticks will fail until the service account is logged in again." \
      >> "${LOG_FILE}" 2>&1 || true
fi

# Keep last 30 days of logs only
find "${LOG_DIR}" -name "checkin_*.log" -mtime +30 -delete 2>/dev/null || true
