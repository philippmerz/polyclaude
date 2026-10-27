#!/usr/bin/env bash
# Read model usage headroom without injecting a conversational /usage turn.
# The kimi backend exposes no provider quota API, so this wraps the local
# OpenCode telemetry probe (scripts/model_usage.py).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
PYTHON="${POLYCLAUDE_PYTHON:-${POLYCLAUDE_DIR}/.venv/bin/python}"

# Scheduled check-ins call inject_prompt.sh, which calls this probe, and
# inherit cron's minimal PATH. OpenCode lives under the service account's
# ~/.local/bin, so make the normal system/local user locations explicit before
# Python resolves the executable. Keep caller-supplied PATH entries after the prefix.
export PATH="/usr/local/bin:${HOME}/.local/bin:${PATH:-/usr/bin:/bin}"

if [[ ! -x "${PYTHON}" ]]; then
    echo "ERROR: project Python is unavailable: ${PYTHON}" >&2
    exit 3
fi

exec "${PYTHON}" "${SCRIPT_DIR}/model_usage.py" "$@"
