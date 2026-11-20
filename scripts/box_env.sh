# Box-host environment for polyclaude daemons (sourced by box_supervisor.sh).
# HOME is a private runtime home inside the repo (git-ignored: .home/), so
# ~/.polyclaude/env, ~/secrets and ~/.polyclaude_* state resolve there.
POLYCLAUDE_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export POLYCLAUDE_REPO
export HOME="${POLYCLAUDE_REPO}/.home"
export POLYCLAUDE_OPERATOR_MODE=webhook
export POLYCLAUDE_AGENT_RUNNER="${POLYCLAUDE_REPO}/scripts/wake_webhook.py"
# OpenCode/Kimi paths kept so scripts/kimi_session.sh still works if invoked by hand.
# Supervisor no longer starts, heals, or auto-wakes the kimi tmux session
# (Philipp cancelled the kimi.com subscription on 2026-11-20; Investor is sole operator).
export POLYCLAUDE_OPENCODE_BIN="${HOME}/.local/bin/opencode"
export POLYCLAUDE_OPENCODE_INJECT="/home/box/.local/bin/pc-opencode-inject"
export POLYCLAUDE_OPENCODE_SESSION="kimi"
export GIT_SSH_COMMAND="ssh -i ${HOME}/.ssh/id_ed25519 -o IdentitiesOnly=yes"
export PATH="${HOME}/.local/bin:/home/box/.local/bin:${POLYCLAUDE_REPO}/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
umask 077
export POLYCLAUDE_TELEGRAM_OUTBOUND=0  # outbound Telegram disabled; alerts go to Grok Bot via wake_webhook.py
