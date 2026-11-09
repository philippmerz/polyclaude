# Box-host environment for polyclaude daemons (sourced by box_supervisor.sh).
# HOME is a private runtime home inside the repo (git-ignored: .home/), so
# ~/.polyclaude/env, ~/secrets and ~/.polyclaude_* state resolve there.
POLYCLAUDE_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export POLYCLAUDE_REPO
export HOME="${POLYCLAUDE_REPO}/.home"
export POLYCLAUDE_AGENT_RUNNER="${HOME}/.local/bin/polyclaude-agent"
export POLYCLAUDE_OPERATOR_MODE=opencode
export POLYCLAUDE_OPENCODE_BIN="${HOME}/.local/bin/opencode"
export POLYCLAUDE_OPENCODE_INJECT="/home/box/.local/bin/pc-opencode-inject"
export POLYCLAUDE_OPENCODE_SESSION="kimi"
export GIT_SSH_COMMAND="ssh -i ${HOME}/.ssh/id_ed25519 -o IdentitiesOnly=yes"
export PATH="${HOME}/.local/bin:/home/box/.local/bin:${POLYCLAUDE_REPO}/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
umask 077
export POLYCLAUDE_TELEGRAM_OUTBOUND=0  # outbound Telegram disabled; operator prompts go to Kimi via polyclaude-agent
