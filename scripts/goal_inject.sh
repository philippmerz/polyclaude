#!/usr/bin/env bash
# Queue one finite /goal line into the live operator session, or clear it.
# Usage: scripts/goal_inject.sh set "objective"
#        scripts/goal_inject.sh clear
# The queued text is exactly one slash command. Clear it when the work is done.
# Scheduled checks stay on the 3-hour cron. A goal is not a waiting loop.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cmd="${1:?usage: goal_inject.sh set \"objective\" | clear}"
case "$cmd" in
  clear)
    if [[ $# -ne 1 ]]; then
      echo "usage: goal_inject.sh clear" >&2
      exit 64
    fi
    line="/goal clear"
    ;;
  set)
    if [[ $# -ne 2 ]]; then
      echo "usage: goal_inject.sh set \"objective\"" >&2
      exit 64
    fi
    objective="$2"
    if [[ -z "${objective}" || "${objective}" == *$'\n'* || "${objective}" == *$'\r'* ]]; then
      echo "objective must be one non-empty line" >&2
      exit 64
    fi
    line="/goal ${objective}"
    ;;
  *)
    echo "usage: goal_inject.sh set \"objective\" | clear" >&2
    exit 64
    ;;
esac
exec "$SCRIPT_DIR/inject_prompt.sh" "$line"
