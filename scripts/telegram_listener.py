"""Telegram→tmux listener.

Long-poll Telegram for messages from the operator and pipe them into the
existing interactive `claude` session living in a known tmux pane. This makes
the bot a thin remote keyboard: the operator texts, the message lands as a
fresh user turn in the same Claude instance with full conversation context.

Config (file pointed to by POLYCLAUDE_TELEGRAM_STATE):
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

import httpx

import _paths as _secrets

_secrets.install_scrubbing_excepthook()

TOKEN_PATH = _secrets.path("POLYCLAUDE_TELEGRAM_TOKEN")
STATE_PATH = _secrets.path("POLYCLAUDE_TELEGRAM_STATE")
PID_PATH = _secrets.path("POLYCLAUDE_LISTENER_PID")
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


def _notify_sender(token: str, chat_id: int, text: str) -> None:
    """One-shot outbound note to the operator (no retry — best effort)."""
    httpx.post(f"{API}/bot{token}/sendMessage",
               json={"chat_id": chat_id, "text": text}, timeout=15)


def _pane_has_live_claude(pane: str) -> bool:
    """A live claude/node must be a DESCENDANT of the pane before we type into
    it. pane_current_command / spinner checks lie: script(1) keeps the pane
    'alive' after the inner claude exits, and text sent to the leftover bash
    prompt EXECUTES AS A SHELL COMMAND (2026-07-16 audit, the exact mechanism
    that ate the operator's OOM directive)."""
    try:
        pane_pid = subprocess.run(
            ["tmux", "display-message", "-p", "-t", pane, "#{pane_pid}"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
        if not pane_pid:
            return False
        tree = subprocess.run(["pstree", "-p", pane_pid],
                              capture_output=True, text=True, timeout=10).stdout
        return ("claude" in tree) or ("node" in tree)
    except Exception:
        return False


def _send_keys(pane: str, text: str) -> None:
    """Inject a message into a tmux pane as if typed there.

    Requires a live claude/node descendant of the pane, then waits for the
    pane to look idle (no Braille spinner in the title), then sends the text
    via -l (literal mode) followed by Enter. Raises
    subprocess.CalledProcessError on tmux failure; raises RuntimeError if the
    pane is dead or never goes idle, so the caller retries the whole update
    on the next poll cycle.
    """
    flat = text.replace("\r\n", " ").replace("\n", " ").strip()
    if not flat:
        return
    if not _pane_has_live_claude(pane):
        raise RuntimeError(f"pane {pane} has no live claude descendant (dead shell); will retry next poll")
    # Wait up to ~5 minutes for the pane to look idle. If the human is typing
    # or Claude is generating, retry every few seconds.
    for _ in range(60):
        if not _pane_is_busy(pane):
            break
        time.sleep(5)
    else:
        raise RuntimeError(f"pane {pane} stayed busy too long; will retry next poll")
    if not _pane_has_live_claude(pane):
        raise RuntimeError(f"pane {pane} claude died during idle-wait; will retry next poll")
    # timeout= (2026-07-30): a wedged tmux client blocked this run() for 27
    # HOURS (do_wait, child never returned) and silently killed all injection
    # — the operator noticed before any alert did. A hung send-keys now fails
    # in 30s and the update retries next poll. NOTE: tmux clients exit 0 on
    # SIGTERM, so a killed/timed-out send may be logged delivered without the
    # text landing — timeout raises BEFORE that misreport can happen.
    subprocess.run(["tmux", "send-keys", "-t", pane, "-l", flat],
                   check=True, timeout=30)
    time.sleep(0.2)
    subprocess.run(["tmux", "send-keys", "-t", pane, "Enter"],
                   check=True, timeout=30)


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

    stuck: dict[int, float] = {}       # update_id -> first failed-delivery ts
    stuck_notified: set[int] = set()   # update_ids whose sender was warned
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
            print(f"poll error: {_secrets.scrub(str(e))}; sleeping {backoff:.1f}s", file=sys.stderr, flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue

        if not data.get("ok"):
            print(f"telegram API not ok: {_secrets.scrub(str(data))}", file=sys.stderr, flush=True)
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
            tagged = f"telegram: {text}"
            try:
                _send_keys(pane, tagged)
                state["last_update_id"] = uid  # only advance on success
                _save_state(state)
                # Success line (2026-07-16): without it, "was update N ever
                # delivered?" is undecidable from this log — the OOM-night
                # forensics needed exactly that.
                print(f"delivered update {uid} to {pane}", flush=True)
                stuck.pop(uid, None)
            except (subprocess.CalledProcessError, RuntimeError) as e:
                # Don't advance the cursor; this update will be re-fetched on
                # the next poll, and we'll retry the inject when the pane is
                # idle. Break so we don't process later updates ahead of this
                # one.
                print(f"send-keys failed for update {uid}: {e}; will retry", file=sys.stderr, flush=True)
                # Sender-side visibility (2026-07-16): the operator's OOM
                # directive retried silently for hours while they assumed it
                # was read. After 10 min of failed delivery, tell them once.
                first = stuck.setdefault(uid, time.time())
                if time.time() - first > 600 and uid not in stuck_notified:
                    stuck_notified.add(uid)
                    try:
                        _notify_sender(token, chat_id,
                                       "⚠ Your message is received but the polyclaude "
                                       "session isn't accepting input (busy or down) — it will "
                                       "be retried until delivered. heartbeat_watch alerts "
                                       "separately if the session is dead.")
                    except Exception:
                        pass
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
