"""Resolve secret/state file paths from env vars.

Public-repo-safe: this module never references actual filesystem locations.
On import, it auto-loads `~/.polyclaude/env` if present, populating env vars
for the importing script. The env file is gitignored and lives outside the
repo. If a required var is missing, callers get a clear error.

Variables read by callers:
    POLYCLAUDE_WALLET, POLYCLAUDE_WALLET_CRYPTO, POLYCLAUDE_CREDS,
    POLYCLAUDE_TELEGRAM_TOKEN, POLYCLAUDE_TELEGRAM_STATE,
    POLYCLAUDE_SESSION, POLYCLAUDE_NEWS_STATE, POLYCLAUDE_NEWS_PID,
    POLYCLAUDE_LISTENER_PID
"""
from __future__ import annotations
import os
from pathlib import Path

_ENV_FILE = Path.home() / ".polyclaude" / "env"


def _autoload_env() -> None:
    if not _ENV_FILE.exists():
        return
    for raw in _ENV_FILE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_autoload_env()


def path(env_var: str) -> Path:
    """Return Path(os.environ[env_var]) or raise with a clear hint."""
    val = os.environ.get(env_var)
    if not val:
        raise RuntimeError(
            f"required env var {env_var!r} not set; populate the polyclaude env file"
        )
    return Path(val)
