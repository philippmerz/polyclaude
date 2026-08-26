#!/usr/bin/env bash
# Non-interactive runtime/auth health check.
# Provider quota UI is intentionally not scraped from a transient TUI.

set -euo pipefail

RUNNER="${POLYCLAUDE_AGENT_RUNNER:-${HOME}/.local/bin/polyclaude-agent}"

if [[ ! -x "${RUNNER}" ]]; then
    echo "ERROR: private agent runtime is unavailable" >&2
    exit 3
fi

"${RUNNER}" status
echo "Quota details: attach to the operator and use its built-in status command."
