"""Resolve secret/state file paths from env vars + scrub secrets from log lines.

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
import re
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


# Telegram bot tokens look like `bot<digits>:<base64-ish>` in URLs. Match and
# replace before any error message hits a log file.
_TELEGRAM_TOKEN_RE = re.compile(r"bot\d+:[A-Za-z0-9_-]{20,}")


def scrub(text: str) -> str:
    """Strip known-credential patterns from arbitrary text before logging."""
    return _TELEGRAM_TOKEN_RE.sub("bot<TOKEN>", text)


def install_scrubbing_excepthook() -> None:
    """Replace sys.excepthook so any unhandled exception's traceback is
    written to stderr with credential patterns stripped first."""
    import sys
    import traceback

    def _hook(exc_type, exc_val, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
        sys.stderr.write(scrub(text))

    sys.excepthook = _hook
