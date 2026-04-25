"""Telegram→tmux listener.

Long-poll Telegram for messages from the operator and pipe them into the
existing interactive `claude` session living in a known tmux pane. This makes
the bot a thin remote keyboard: the operator texts, the message lands as a
fresh user turn in the same Claude instance with full conversation context.

Config (in <HOME>/.polyclaude_telegram.json):
  {
    "chat_id": <int>,
    "tmux_pane": "session:window.pane",   # e.g. "0:0.0"
    "last_update_id": <int>               # cursor; managed by this script
  }

Usage:
  start            run as a foreground process (cron / systemd / nohup it)
  status           print listener PID + last activity
  stop             kill the listener (reads PID file)

Run with: nohup ./.venv/bin/python scripts/telegram_listener.py start \\
            > logs/telegram_listener.log 2>&1 &
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx

TOKEN_PATH = Path("<SECRETS>/telegram_token.txt")
STATE_PATH = Path("<HOME>/.polyclaude_telegram.json")
PID_PATH = Path("<HOME>/.polyclaude_telegram_listener.pid")
API = "https://api.telegram.org"
LONG_POLL_TIMEOUT = 30  # seconds


def _state() -> dict:
    if not STATE_PATH.exists():
        return {}
    return json.loads(STATE_PATH.read_text())


def _save_state(s: dict) -> None:
    STATE_PATH.write_text(json.dumps(s, indent=2))
    os.chmod(STATE_PATH, 0o600)


def _token() -> str:
    return TOKEN_PATH.read_text().strip()


def _pane_is_busy(pane: str) -> bool:
    """Heuristic: Claude Code's TUI shows a Braille spinner glyph in the pane
    title while generating. If we see one of those characters, assume busy.

    Returns True if we believe the pane should not receive injected input yet.
    """
    try:
        out = subprocess.run(
            ["tmux", "display-message", "-p", "-t", pane, "#{pane_title}"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return False
    # Braille spinner code points used by Claude Code's TUI. If any appear,
    # the pane is animating and not in a stable input state.
    return any(0x2800 <= ord(c) <= 0x28FF for c in out)


def _send_keys(pane: str, text: str) -> None:
    """Inject a message into a tmux pane as if typed there.

    Waits for the pane to look idle (no Braille spinner in the title), then
    sends the text via -l (literal mode) followed by Enter. Raises
    subprocess.CalledProcessError on tmux failure; raises RuntimeError if the
    pane never goes idle within the wait budget so the caller can retry the
    whole update on the next poll cycle.
    """
    flat = text.replace("\r\n", " ").replace("\n", " ").strip()
    if not flat:
        return
    # Wait up to ~5 minutes for the pane to look idle. If the human is typing
    # or Claude is generating, retry every few seconds.
    for _ in range(60):
        if not _pane_is_busy(pane):
            break
        time.sleep(5)
    else:
        raise RuntimeError(f"pane {pane} stayed busy too long; will retry next poll")
    subprocess.run(["tmux", "send-keys", "-t", pane, "-l", flat], check=True)
    time.sleep(0.2)
    subprocess.run(["tmux", "send-keys", "-t", pane, "Enter"], check=True)


def cmd_start(_args: argparse.Namespace) -> int:
    PID_PATH.write_text(str(os.getpid()))
    state = _state()
    chat_id = int(state.get("chat_id") or 0)
    pane = state.get("tmux_pane")
    if not chat_id or not pane:
        print(f"ERROR: chat_id and tmux_pane must be set in {STATE_PATH}", file=sys.stderr)
        return 2
    print(f"listener up: chat_id={chat_id}, pane={pane}, last_update_id={state.get('last_update_id', 0)}", flush=True)
    token = _token()

    backoff = 1.0
    while True:
        try:
            params = {
                "timeout": LONG_POLL_TIMEOUT,
                "offset": int(state.get("last_update_id", 0)) + 1,
                "allowed_updates": '["message"]',
            }
            r = httpx.get(f"{API}/bot{token}/getUpdates", params=params,
                          timeout=LONG_POLL_TIMEOUT + 10)
            r.raise_for_status()
            data = r.json()
            backoff = 1.0
        except Exception as e:
            print(f"poll error: {e}; sleeping {backoff:.1f}s", file=sys.stderr, flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue

        if not data.get("ok"):
            print(f"telegram API not ok: {data}", file=sys.stderr, flush=True)
            time.sleep(5)
            continue

        for update in data["result"]:
            uid = update["update_id"]
            msg = update.get("message")
            if not msg:
                state["last_update_id"] = uid
                continue
            chat = msg.get("chat", {})
            if chat.get("id") != chat_id:
                print(f"drop foreign chat {chat.get('id')}", flush=True)
                state["last_update_id"] = uid
                continue
            text = msg.get("text") or msg.get("caption") or ""
            if not text:
                # Sticker / photo / etc. — skip and advance.
                state["last_update_id"] = uid
                continue
            print(f"recv update {uid}: {text[:120]!r}", flush=True)
            try:
                _send_keys(pane, text)
                state["last_update_id"] = uid  # only advance on success
                _save_state(state)
            except (subprocess.CalledProcessError, RuntimeError) as e:
                # Don't advance the cursor; this update will be re-fetched on
                # the next poll, and we'll retry the inject when the pane is
                # idle. Break so we don't process later updates ahead of this
                # one.
                print(f"send-keys failed for update {uid}: {e}; will retry", file=sys.stderr, flush=True)
                break


def cmd_status(_args: argparse.Namespace) -> int:
    if not PID_PATH.exists():
        print("listener not running (no PID file)"); return 1
    pid = int(PID_PATH.read_text().strip())
    try:
        os.kill(pid, 0)
    except OSError:
        print(f"PID {pid} not alive (stale PID file)"); return 1
    state = _state()
    print(f"listener pid={pid}, last_update_id={state.get('last_update_id', 0)}")
    return 0


def cmd_stop(_args: argparse.Namespace) -> int:
    if not PID_PATH.exists():
        print("not running"); return 0
    pid = int(PID_PATH.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"sent SIGTERM to {pid}")
    except OSError as e:
        print(f"could not signal {pid}: {e}")
    PID_PATH.unlink(missing_ok=True)
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("start").set_defaults(func=cmd_start)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("stop").set_defaults(func=cmd_stop)
    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
