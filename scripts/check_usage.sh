#!/usr/bin/env bash
# Read Codex quota headroom without injecting a conversational /usage turn.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
PYTHON="${POLYCLAUDE_PYTHON:-${POLYCLAUDE_DIR}/.venv/bin/python}"

# The light 06/10/18/22 UTC crons invoke inject_prompt.sh directly and inherit
# cron's minimal PATH. Codex is installed in /usr/local/bin on this host, so
# make the normal system/local user locations explicit before Python resolves
# the executable. Keep any caller-supplied PATH entries after the safe prefix.
export PATH="/usr/local/bin:${HOME}/.local/bin:${PATH:-/usr/bin:/bin}"

if [[ ! -x "${PYTHON}" ]]; then
    echo "ERROR: project Python is unavailable: ${PYTHON}" >&2
    exit 3
fi

exec "${PYTHON}" "${SCRIPT_DIR}/codex_usage.py" "$@"
