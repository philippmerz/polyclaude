# Box-host environment for polyclaude daemons (sourced by box_supervisor.sh).
# HOME is a private runtime home inside the repo (git-ignored: .home/), so
# ~/.polyclaude/env, ~/secrets and ~/.polyclaude_* state resolve there.
POLYCLAUDE_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export POLYCLAUDE_REPO
export HOME="${POLYCLAUDE_REPO}/.home"
export POLYCLAUDE_AGENT_RUNNER="${POLYCLAUDE_REPO}/scripts/wake_webhook.py"
export POLYCLAUDE_OPERATOR_MODE=webhook
export GIT_SSH_COMMAND="ssh -i ${HOME}/.ssh/id_ed25519 -o IdentitiesOnly=yes"
export PATH="${POLYCLAUDE_REPO}/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
umask 077
