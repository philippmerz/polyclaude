"""Durable Telegram-to-operator listener.

Authorized text messages are first written to a private ordered spool and only
then acknowledged in the Telegram update cursor. Delivery uses the operator's
conversation queue, never terminal keystrokes. A busy or temporarily absent
agent therefore cannot block polling, turn text into a shell command, or lose a
later correction.

Config (file pointed to by POLYCLAUDE_TELEGRAM_STATE):
  {
    "chat_id": <int>,
    "tmux_pane": "operator:0.0",  # retained for compatible setup/status data
    "last_update_id": <int>
  }

Usage: telegram_listener.py start | status | stop
"""

from __future__ import annotations

import argparse
import atexit
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any

import httpx

import _paths as _secrets


_secrets.install_scrubbing_excepthook()

TOKEN_PATH = _secrets.path("POLYCLAUDE_TELEGRAM_TOKEN")
STATE_PATH = _secrets.path("POLYCLAUDE_TELEGRAM_STATE")
PID_PATH = _secrets.path("POLYCLAUDE_LISTENER_PID")
LOCK_PATH = PID_PATH.with_name(f"{PID_PATH.name}.lock")
QUEUE_PATH = Path(
    os.environ.get(
        "POLYCLAUDE_TELEGRAM_QUEUE",
        str(STATE_PATH.with_name("telegram_operator_queue.json")),
    )
)
REPO_ROOT = Path(__file__).resolve().parent.parent
RUNNER = Path(
    os.environ.get(
        "POLYCLAUDE_AGENT_RUNNER",
        str(Path.home() / ".local" / "bin" / "polyclaude-agent"),
    )
)
API = "https://api.telegram.org"
LONG_POLL_TIMEOUT = 30
DELIVERY_TIMEOUT = 30
STALE_INSTRUCTION_SECONDS = 10 * 60
MAX_TEXT_BYTES = 60_000
MAX_DELIVERED_IDS = 1024
MAX_QUARANTINED = 256
_PID_LOCK_FD: int | None = None


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    """Write private JSON atomically and fsync both file and directory."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        os.chmod(path, 0o600)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _state() -> dict[str, Any]:
    return _read_json(STATE_PATH, {})


def _save_state(state: dict[str, Any]) -> None:
    _atomic_json(STATE_PATH, state)


def _queue() -> dict[str, Any]:
    value = _read_json(
        QUEUE_PATH,
        {"version": 2, "items": [], "quarantined": [], "delivered_ids": []},
    )
    value["version"] = 2
    value.setdefault("items", [])
    value.setdefault("quarantined", [])
    value.setdefault("delivered_ids", [])
    for field in ("items", "quarantined", "delivered_ids"):
        if not isinstance(value[field], list):
            raise ValueError(f"Telegram operator queue has invalid {field} field")
    return value


def _save_queue(queue: dict[str, Any]) -> None:
    _atomic_json(QUEUE_PATH, queue)


def _token() -> str:
    return TOKEN_PATH.read_text(encoding="utf-8").strip()


def _notify_sender(token: str, chat_id: int, text: str) -> bool:
    """Send one best-effort delivery-status note and verify API acceptance."""
    response = httpx.post(
        f"{API}/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    response.raise_for_status()
    return bool(response.json().get("ok"))


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:12]


def _enqueue(queue: dict[str, Any], update: dict[str, Any], text: str) -> bool:
    """Append an update unless its stable ID is pending, quarantined, or done."""
    update_id = int(update["update_id"])
    if any(int(item.get("update_id", -1)) == update_id for item in queue["items"]):
        return False
    if any(
        int(item.get("update_id", -1)) == update_id
        for item in queue.get("quarantined", [])
    ):
        return False
    if update_id in {int(value) for value in queue.get("delivered_ids", [])}:
        return False
    message = update.get("message") or {}
    queue["items"].append(
        {
            "update_id": update_id,
            "message_id": int(message.get("message_id") or 0),
            "sent_at": int(message.get("date") or 0),
            "received_at": int(time.time()),
            "text": text,
            "attempts": 0,
            "first_failure_at": None,
            "next_attempt_at": 0,
            "warning_sent": False,
        }
    )
    _save_queue(queue)
    return True


def _delivery_envelope(item: dict[str, Any], now: int | None = None) -> str:
    now = int(time.time()) if now is None else now
    sent_at = int(item.get("sent_at") or 0)
    age = max(0, now - sent_at) if sent_at else 0
    sent_iso = (
        dt.datetime.fromtimestamp(sent_at, tz=dt.timezone.utc).isoformat()
        if sent_at
        else "unknown"
    )
    stale = age > STALE_INSTRUCTION_SECONDS
    safety = (
        "STALE: this message is over 10 minutes old. For any consequential "
        "asset action, re-check live state and ask the operator to confirm; do "
        "not execute the stale instruction."
        if stale
        else
        "Before any consequential asset action, re-check current live state and "
        "apply every project safety gate."
    )
    return (
        f"telegram: [update_id={int(item['update_id'])} "
        f"message_id={int(item.get('message_id') or 0)} sent_at={sent_iso} "
        f"age_seconds={age}]\n"
        f"Delivery safety: {safety}\n\n"
        f"{str(item.get('text') or '').strip()}"
    )


def _is_stale(item: dict[str, Any], now: float) -> bool:
    sent_at = int(item.get("sent_at") or 0)
    return sent_at <= 0 or now - sent_at > STALE_INSTRUCTION_SECONDS


def _quarantine_stale(
    queue: dict[str, Any], item: dict[str, Any], token: str, chat_id: int, now: float
) -> None:
    """Fail closed: persist stale input without exposing it to the operator."""
    finished = queue["items"].pop(0)
    record = dict(finished)
    record.update(
        {
            "quarantined_at": int(now),
            "quarantine_reason": "missing-or-stale-telegram-timestamp",
            "warning_sent": False,
            "warning_next_at": 0,
        }
    )
    queue.setdefault("quarantined", []).append(record)
    queue["quarantined"] = queue["quarantined"][-MAX_QUARANTINED:]
    _save_queue(queue)
    print(
        f"quarantined stale update={int(item['update_id'])} "
        f"sha256={_fingerprint(str(item.get('text') or ''))}",
        flush=True,
    )
    _retry_quarantine_warnings(queue, token, chat_id, now)


def _retry_quarantine_warnings(
    queue: dict[str, Any], token: str, chat_id: int, now: float
) -> None:
    changed = False
    for item in queue.get("quarantined", []):
        if item.get("warning_sent"):
            continue
        if float(item.get("warning_next_at") or 0) > now:
            continue
        try:
            warned = _notify_sender(
                token,
                chat_id,
                "⚠ Your Telegram message expired before safe delivery and was "
                "NOT sent to the polyclaude operator. Re-check current state "
                "and send a fresh message if you still want it handled.",
            )
        except Exception:
            warned = False
        if warned:
            item["warning_sent"] = True
        else:
            item["warning_next_at"] = now + 60
        changed = True
    if changed:
        _save_queue(queue)


def _deliver(item: dict[str, Any]) -> None:
    if not RUNNER.is_file() or not os.access(RUNNER, os.X_OK):
        raise RuntimeError("operator runtime is unavailable")
    result = subprocess.run(
        [
            str(RUNNER),
            "queue",
            "--workdir",
            str(REPO_ROOT),
            "--reference-id",
            str(int(item["update_id"])),
            "--expires-at",
            str(int(item["sent_at"]) + STALE_INSTRUCTION_SECONDS),
        ],
        input=_delivery_envelope(item),
        capture_output=True,
        text=True,
        timeout=DELIVERY_TIMEOUT,
        check=False,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "queue rejected message").strip()
        raise RuntimeError(_secrets.scrub(detail)[:240])


def _drain_pending(queue: dict[str, Any], token: str, chat_id: int) -> int:
    """Deliver due items in order; stop on first failure to preserve ordering."""
    delivered = 0
    _retry_quarantine_warnings(queue, token, chat_id, time.time())
    while queue["items"]:
        item = queue["items"][0]
        now = time.time()
        if _is_stale(item, now):
            _quarantine_stale(queue, item, token, chat_id, now)
            continue
        if float(item.get("next_attempt_at") or 0) > now:
            break
        # Persist the handoff boundary before the private runtime stages the
        # opaque reference. Retrying this reference is safe: the private reader
        # claims each stable update ID at most once.
        item["handoff_started_at"] = int(now)
        _save_queue(queue)
        try:
            _deliver(item)
        except (OSError, subprocess.SubprocessError, RuntimeError) as exc:
            attempts = int(item.get("attempts") or 0) + 1
            item["attempts"] = attempts
            first = float(item.get("first_failure_at") or now)
            item["first_failure_at"] = first
            item["next_attempt_at"] = now + min(2 ** min(attempts, 6), 60)
            print(
                f"delivery failed update={item['update_id']} attempt={attempts}: "
                f"{_secrets.scrub(str(exc))}; retained",
                file=sys.stderr,
                flush=True,
            )
            if now - first > 600 and not item.get("warning_sent"):
                try:
                    warned = _notify_sender(
                        token,
                        chat_id,
                        "⚠ Your message is safely queued locally, but the "
                        "polyclaude operator is not accepting it yet. It will be "
                        "retried in order; consequential stale requests require "
                        "reconfirmation.",
                    )
                    if warned:
                        item["warning_sent"] = True
                except Exception:
                    pass
            _save_queue(queue)
            break
        else:
            finished = queue["items"].pop(0)
            delivered_ids = queue.setdefault("delivered_ids", [])
            delivered_ids.append(int(finished["update_id"]))
            queue["delivered_ids"] = delivered_ids[-MAX_DELIVERED_IDS:]
            _save_queue(queue)
            print(
                f"delivered update={finished['update_id']} attempts="
                f"{int(finished.get('attempts') or 0) + 1}",
                flush=True,
            )
            delivered += 1
    return delivered


def _ingest_updates(
    updates: list[dict[str, Any]],
    state: dict[str, Any],
    queue: dict[str, Any],
    chat_id: int,
) -> int:
    """Authorize and durably spool a Telegram result batch."""
    accepted = 0
    for update in updates:
        update_id = int(update["update_id"])
        if update_id <= int(state.get("last_update_id") or 0):
            continue
        message = update.get("message")
        if not isinstance(message, dict):
            state["last_update_id"] = update_id
            _save_state(state)
            continue
        incoming_chat_id = int((message.get("chat") or {}).get("id") or 0)
        if incoming_chat_id != chat_id:
            print(f"drop unauthorized update={update_id}", flush=True)
            state["last_update_id"] = update_id
            _save_state(state)
            continue
        text = str(message.get("text") or message.get("caption") or "").strip()
        if not text:
            state["last_update_id"] = update_id
            _save_state(state)
            continue
        if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
            print(f"drop oversize update={update_id} bytes>{MAX_TEXT_BYTES}", flush=True)
            state["last_update_id"] = update_id
            _save_state(state)
            continue

        if _enqueue(queue, update, text):
            accepted += 1
        state["last_update_id"] = update_id
        _save_state(state)
        print(
            f"spooled update={update_id} bytes={len(text.encode('utf-8'))} "
            f"sha256={_fingerprint(text)} pending={len(queue['items'])}",
            flush=True,
        )
    return accepted


def _pid_is_listener(pid: int) -> bool:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False
    parts = [part.decode(errors="replace") for part in raw.split(b"\0") if part]
    return any(Path(part).name == "telegram_listener.py" for part in parts) and "start" in parts


def _release_pid() -> None:
    global _PID_LOCK_FD
    fd = _PID_LOCK_FD
    if fd is None:
        return
    try:
        try:
            owner = int(PID_PATH.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            owner = 0
        if owner == os.getpid():
            PID_PATH.unlink(missing_ok=True)
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
            _PID_LOCK_FD = None


def _claim_pid() -> bool:
    global _PID_LOCK_FD
    PID_PATH.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(PID_PATH.parent, 0o700)
    fd = os.open(
        LOCK_PATH,
        os.O_RDWR | os.O_CREAT | os.O_CLOEXEC,
        0o600,
    )
    os.chmod(LOCK_PATH, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        print("listener already running (singleton lock held)", file=sys.stderr)
        return False
    _PID_LOCK_FD = fd

    if PID_PATH.exists():
        try:
            existing = int(PID_PATH.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            existing = 0
        if existing and _pid_is_listener(existing):
            print(f"listener already running pid={existing}", file=sys.stderr)
            _release_pid()
            return False
    # Retain the legacy plain PID-file contract used by daemon monitoring.
    tmp = PID_PATH.with_name(f".{PID_PATH.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"{os.getpid()}\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, PID_PATH)
        os.chmod(PID_PATH, 0o600)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
    atexit.register(_release_pid)
    return True


def _exit_on_signal(_signum: int, _frame: Any) -> None:
    raise SystemExit(0)


def cmd_start(_args: argparse.Namespace) -> int:
    if not _claim_pid():
        return 2
    signal.signal(signal.SIGTERM, _exit_on_signal)
    signal.signal(signal.SIGINT, _exit_on_signal)
    state = _state()
    queue = _queue()
    chat_id = int(state.get("chat_id") or 0)
    if not chat_id:
        print(f"ERROR: chat_id must be set in {STATE_PATH}", file=sys.stderr)
        _release_pid()
        return 2
    print(
        f"listener up: cursor={int(state.get('last_update_id') or 0)} "
        f"pending={len(queue['items'])} transport=operator-queue",
        flush=True,
    )
    token = _token()
    poll_backoff = 1.0

    while True:
        _drain_pending(queue, token, chat_id)
        try:
            response = httpx.get(
                f"{API}/bot{token}/getUpdates",
                params={
                    "timeout": LONG_POLL_TIMEOUT,
                    "offset": int(state.get("last_update_id") or 0) + 1,
                    "allowed_updates": '["message"]',
                },
                timeout=LONG_POLL_TIMEOUT + 10,
            )
            response.raise_for_status()
            data = response.json()
            if not data.get("ok"):
                raise RuntimeError("Telegram API returned ok=false")
            poll_backoff = 1.0
        except Exception as exc:
            print(
                f"poll error: {_secrets.scrub(str(exc))}; sleeping {poll_backoff:.1f}s",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(poll_backoff)
            poll_backoff = min(poll_backoff * 2, 60)
            continue

        _ingest_updates(data.get("result") or [], state, queue, chat_id)

        _drain_pending(queue, token, chat_id)


def cmd_status(_args: argparse.Namespace) -> int:
    if not PID_PATH.exists():
        print("listener not running (no PID file)")
        return 1
    try:
        pid = int(PID_PATH.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        print("listener not running (invalid PID file)")
        return 1
    if not _pid_is_listener(pid):
        print(f"PID {pid} is not the listener (stale PID file)")
        return 1
    state = _state()
    queue = _queue()
    print(
        f"listener pid={pid}, cursor={int(state.get('last_update_id') or 0)}, "
        f"pending={len(queue['items'])}"
    )
    return 0


def cmd_stop(_args: argparse.Namespace) -> int:
    if not PID_PATH.exists():
        print("not running")
        return 0
    try:
        pid = int(PID_PATH.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        print("invalid PID file; removing it")
        PID_PATH.unlink(missing_ok=True)
        return 0
    if not _pid_is_listener(pid):
        print(f"refusing to signal PID {pid}: identity does not match listener")
        PID_PATH.unlink(missing_ok=True)
        return 1
    os.kill(pid, signal.SIGTERM)
    print(f"sent SIGTERM to listener PID {pid}")
    PID_PATH.unlink(missing_ok=True)
    return 0


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("start").set_defaults(func=cmd_start)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("stop").set_defaults(func=cmd_stop)
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
