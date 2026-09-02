#!/usr/bin/env bash
# Read Codex quota headroom without injecting a conversational /usage turn.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
PYTHON="${POLYCLAUDE_PYTHON:-${POLYCLAUDE_DIR}/.venv/bin/python}"

if [[ ! -x "${PYTHON}" ]]; then
    echo "ERROR: project Python is unavailable: ${PYTHON}" >&2
    exit 3
fi

exec "${PYTHON}" "${SCRIPT_DIR}/codex_usage.py" "$@"
