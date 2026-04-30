#!/bin/bash
# Hourly arb scanner + executor wrapper.
# Resolves repo root from BASH_SOURCE so cron's clean env doesn't matter.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POLYCLAUDE_DIR="$(dirname "${SCRIPT_DIR}")"
cd "${POLYCLAUDE_DIR}"

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export HOME="${HOME:-$(getent passwd "$(id -un)" | cut -d: -f6)}"

# Source polyclaude env if present (for any keys the scripts read)
if [[ -f "${HOME}/.polyclaude/env" ]]; then
    set -a; source "${HOME}/.polyclaude/env"; set +a
fi

mkdir -p logs

.venv/bin/python scripts/limitless_arb_scan.py --notify >> logs/arb_scan.log 2>&1
SCAN_RC=$?

if [[ ${SCAN_RC} -eq 0 ]]; then
    .venv/bin/python scripts/limitless_arb_executor.py run >> logs/arb_executor.log 2>&1
fi
