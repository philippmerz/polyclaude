"""Polyclaude heartbeat watcher — meta-monitoring for the autonomy stack.

Hourly probe that checks each tracked daemon is healthy and alerts the
operator on Telegram if anything looks stuck. Catches the class of bug
that left a `claude -p` cron tick deadlocked for 3 days.

Checks performed:
  1. news_watcher daemon: PID alive AND state file (POLYCLAUDE_NEWS_STATE)
     mtime < 30 min old (state file updates after every 5-min poll cycle).
  2. telegram_listener daemon: PID alive (no good activity signal during
     quiet operator periods, so PID-only).
  3. Stuck `claude -p` cron forks: any such process running > 60 min is
     anomalous (cron ticks should complete much faster).

Each anomaly type has its own 1-hour Telegram-cooldown so we don't spam.

Subcommands: start | status | stop | once
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

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent

PID_PATH = Path.home() / ".polyclaude_heartbeat.pid"
STATE_PATH = Path.home() / ".polyclaude_heartbeat_state.json"
LOG_PATH = _REPO_ROOT / "logs" / "heartbeat.log"

POLL_INTERVAL_SECONDS = 3600          # 1 hour
NEWS_STATE_STALE_SECONDS = 30 * 60    # 30 min
CRON_FORK_AGE_LIMIT_SECONDS = 60 * 60 # 1 hour for any single cron tick
ALERT_COOLDOWN_SECONDS = 3600         # don't re-alert same anomaly within 1 hour


def _now() -> int:
    return int(time.time())


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"last_alerts": {}}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"last_alerts": {}}


def _save_state(s: dict) -> None:
    STATE_PATH.write_text(json.dumps(s, indent=2))
    os.chmod(STATE_PATH, 0o600)


def _telegram(text: str) -> None:
    try:
        subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            cwd=_REPO_ROOT, check=False, timeout=15, capture_output=True,
        )
    except Exception:
        pass


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _read_pid_file(env_var: str) -> int | None:
    try:
        path = _secrets.path(env_var)
    except RuntimeError:
        return None
    if not path.exists():
        return None
    try:
        return int(path.read_text().strip())
    except (ValueError, OSError):
        return None


def _emit(state: dict, key: str, msg: str) -> bool:
    """Emit an alert with cooldown. Returns True if actually emitted."""
    last = state["last_alerts"].get(key, 0)
    now = _now()
    if now - last < ALERT_COOLDOWN_SECONDS:
        print(f"[heartbeat] suppressed (cooldown): {key} -- {msg}", flush=True)
        return False
    state["last_alerts"][key] = now
    line = f"[heartbeat] {msg}"
    print(line, flush=True)
    _telegram(f"[HEARTBEAT] {msg}")
    return True


def check_news_watcher(state: dict) -> None:
    pid = _read_pid_file("POLYCLAUDE_NEWS_PID")
    if pid is None or not _pid_alive(pid):
        _emit(state, "news_watcher_dead",
              f"news_watcher PID {pid} not alive — daemon down")
        return

    try:
        state_path = _secrets.path("POLYCLAUDE_NEWS_STATE")
    except RuntimeError:
        return
    if not state_path.exists():
        _emit(state, "news_watcher_no_state",
              "news_watcher state file missing despite live PID")
        return
    age = _now() - int(state_path.stat().st_mtime)
    if age > NEWS_STATE_STALE_SECONDS:
        _emit(state, "news_watcher_stale",
              f"news_watcher state file unchanged for {age // 60} min "
              f"(threshold {NEWS_STATE_STALE_SECONDS // 60}); poll loop may be stuck")

    # Output-integrity invariant (2026-06-11 lesson: liveness != output integrity —
    # 30h of alerts were LOGGED but never PERSISTED to news_alerts.jsonl and every
    # PID/state check above passed). If the watcher log shows alert lines but the
    # jsonl hasn't grown in far longer, the persistence layer is broken.
    try:
        from pathlib import Path
        repo = Path(__file__).resolve().parent.parent
        log_p = repo / "logs" / "news_watcher.log"
        jsonl_p = repo / "notes" / "news_alerts.jsonl"
        if log_p.exists() and jsonl_p.exists():
            log_alert_mtime = None
            # cheap: if the log's last 50 lines contain an alert line, use log mtime
            with open(log_p, "rb") as f:
                f.seek(max(0, log_p.stat().st_size - 8192))
                tail = f.read().decode(errors="replace")
            if "[watcher] alert tier" in tail:
                log_alert_mtime = int(log_p.stat().st_mtime)
            if log_alert_mtime:
                jsonl_age_vs_log = log_alert_mtime - int(jsonl_p.stat().st_mtime)
                if jsonl_age_vs_log > 6 * 3600:
                    _emit(state, "news_alerts_persistence_diverged",
                          f"watcher log shows recent alerts but news_alerts.jsonl is "
                          f"{jsonl_age_vs_log // 3600}h older — persistence layer broken "
                          f"(2026-06-11 class); cron ticks are blind to news")
    except Exception:
        pass


def check_telegram_listener(state: dict) -> None:
    pid = _read_pid_file("POLYCLAUDE_LISTENER_PID")
    if pid is None or not _pid_alive(pid):
        _emit(state, "telegram_listener_dead",
              f"telegram_listener PID {pid} not alive — operator inbound channel down")


def check_stuck_cron_forks(state: dict) -> None:
    """Find any `claude -p` process older than the age limit."""
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid,etimes,cmd"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout
    except subprocess.CalledProcessError:
        return

    stuck = []
    for line in out.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        pid_str, etimes_str, cmd = parts
        if "claude -p" not in cmd:
            continue
        try:
            age = int(etimes_str)
        except ValueError:
            continue
        if age > CRON_FORK_AGE_LIMIT_SECONDS:
            stuck.append((int(pid_str), age, cmd))

    for pid, age, cmd in stuck:
        # Don't keep alerting for the same long-stuck PID; key includes pid
        _emit(state, f"stuck_cron_pid_{pid}",
              f"claude -p cron fork PID {pid} has been running "
              f"{age // 60} min (>{CRON_FORK_AGE_LIMIT_SECONDS // 60} min limit) — "
              f"likely deadlocked. Inspect: ps -p {pid} -o pid,etime,stat,cmd")


def poll_once() -> None:
    state = _load_state()
    check_news_watcher(state)
    check_telegram_listener(state)
    check_stuck_cron_forks(state)
    _save_state(state)


def cmd_start(_args: argparse.Namespace) -> int:
    PID_PATH.write_text(str(os.getpid()))
    print(f"[heartbeat] up pid={os.getpid()}", flush=True)
    while True:
        try:
            poll_once()
        except KeyboardInterrupt:
            print("[heartbeat] interrupted", flush=True)
            return 0
        except Exception as e:
            print(f"[heartbeat] poll error: {_secrets.scrub(str(e))}", flush=True)
        time.sleep(POLL_INTERVAL_SECONDS)


def cmd_once(_args: argparse.Namespace) -> int:
    poll_once()
    print("poll done")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    if not PID_PATH.exists():
        print("heartbeat not running"); return 1
    pid = int(PID_PATH.read_text().strip())
    if not _pid_alive(pid):
        print(f"PID {pid} not alive (stale)"); return 1
    print(f"heartbeat pid={pid}")
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
    sub.add_parser("once").set_defaults(func=cmd_once)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("stop").set_defaults(func=cmd_stop)
    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
