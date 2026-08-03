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


def _telegram(text: str) -> bool:
    """Returns True only on confirmed send (2026-07-16 audit: failures were
    swallowed AND the cooldown was burned, so the watchdog's one job — the
    ping — could silently not happen for 6h exactly when the network was bad)."""
    try:
        r = subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            cwd=_REPO_ROOT, check=False, timeout=30, capture_output=True,
        )
        return r.returncode == 0
    except Exception:
        return False


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


def _pgrep(pattern: str) -> list[int]:
    """PIDs matching an -f pattern. PID files go stale across reboots/restarts
    (2026-07-16: listener PID file said 416, live daemon was 398 → false
    'channel down' alert); a pgrep fallback beats alerting on a stale file."""
    try:
        out = subprocess.run(["pgrep", "-f", pattern],
                             capture_output=True, text=True, timeout=10).stdout
        return [int(x) for x in out.split()]
    except Exception:
        return []


# Persistent-condition alerts (daemon down, scanning down): the condition
# doesn't change hour to hour, so a 1h cooldown just spams the operator
# (2026-07-16: 11 identical oppwatch-dead alerts overnight). One ping + one
# reminder every 6h is enough — the alert's job is done after the first send.
DAEMON_DOWN_COOLDOWN = 6 * 3600


def _emit(state: dict, key: str, msg: str, cooldown: int = ALERT_COOLDOWN_SECONDS) -> bool:
    """Emit an alert with cooldown. Returns True if actually emitted.

    The cooldown timestamp is recorded ONLY on a confirmed send — a failed
    send leaves the key hot so the next hourly poll retries instead of
    silently waiting out a 6h cooldown on an alert nobody received."""
    last = state["last_alerts"].get(key, 0)
    now = _now()
    if now - last < cooldown:
        print(f"[heartbeat] suppressed (cooldown): {key} -- {msg}", flush=True)
        return False
    line = f"[heartbeat] {msg}"
    print(line, flush=True)
    if _telegram(f"[HEARTBEAT] {msg}"):
        state["last_alerts"][key] = now
        return True
    print(f"[heartbeat] telegram send FAILED for {key} — cooldown not burned, will retry next poll", flush=True)
    return False


def check_news_watcher(state: dict) -> None:
    pid = _read_pid_file("POLYCLAUDE_NEWS_PID")
    if pid is None or not _pid_alive(pid):
        live = _pgrep("[n]ews_watcher.py start")
        if live:
            print(f"[heartbeat] news_watcher PID file stale ({pid}) but daemon "
                  f"alive at {live[0]} — no alert", flush=True)
        else:
            _emit(state, "news_watcher_dead",
                  f"news_watcher PID {pid} not alive — daemon down",
                  cooldown=DAEMON_DOWN_COOLDOWN)
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
            # STATEFUL divergence probe (2026-07-04 fix). The old heuristic —
            # "alert line within the last 8KB of the log + fresh log mtime" —
            # false-fired when a stale alert line sat near EOF because only
            # chatty 'suppressed' lines followed it (log mtime updates every
            # cycle regardless). Instead: compare deltas — a NEW alert line
            # logged while news_alerts.jsonl did not grow is a true
            # persistence failure (2026-06-11 class); anything else is not.
            # Incremental count (2026-07-16 audit: full-file read of a
            # never-rotated log, hourly, in a 1.9GB-RAM box — bound it).
            # Count alert lines only in bytes appended since the last poll
            # and accumulate; reset if the file shrank (rotation/truncate).
            probe_prev = state.get("news_persist_probe") or {}
            if probe_prev and "log_off" not in probe_prev:
                # state written by the pre-2026-07-16 full-count format —
                # counts aren't comparable; re-baseline without alerting
                probe_prev = {}
            log_size = log_p.stat().st_size
            prev_off = probe_prev.get("log_off", 0)
            prev_cum = probe_prev.get("alerts", 0)
            if log_size < prev_off:
                prev_off, prev_cum = 0, 0
            with open(log_p, "rb") as fh:
                fh.seek(prev_off)
                new_alerts = fh.read().count(b"[watcher] alert tier")
            alert_count = prev_cum + new_alerts
            jsonl_size = jsonl_p.stat().st_size
            prev = probe_prev
            if (prev and alert_count > prev.get("alerts", alert_count)
                    and jsonl_size <= prev.get("jsonl", 0)):
                _emit(state, "news_alerts_persistence_diverged",
                      f"{alert_count - prev['alerts']} new watcher alert(s) logged but "
                      f"news_alerts.jsonl did not grow — persistence layer broken "
                      f"(2026-06-11 class); cron ticks are blind to news")
            state["news_persist_probe"] = {"alerts": alert_count, "jsonl": jsonl_size,
                                            "log_off": log_size}
    except Exception:
        pass


def check_telegram_listener(state: dict) -> None:
    pid = _read_pid_file("POLYCLAUDE_LISTENER_PID")
    if pid is None or not _pid_alive(pid):
        live = _pgrep("[t]elegram_listener.py start")
        if live:
            print(f"[heartbeat] telegram_listener PID file stale ({pid}) but daemon "
                  f"alive at {live[0]} — no alert", flush=True)
            pid = live[0]
        else:
            _emit(state, "telegram_listener_dead",
                  f"telegram_listener PID {pid} not alive — operator inbound channel down",
                  cooldown=DAEMON_DOWN_COOLDOWN)
            return

    # Wedged-delivery check (2026-07-30): liveness != progress. A tmux
    # send-keys child of the listener wedged for 27 HOURS (listener blocked in
    # do_wait, PID happily alive) and every operator message queued undelivered
    # until the operator noticed. Normal send-keys children complete in
    # milliseconds; any child older than 10 minutes means the delivery path is
    # stuck. (The listener now passes timeout=30 to send-keys, so this is the
    # backstop for OTHER unbounded block points, and for the alert the operator
    # never got.)
    try:
        out = subprocess.run(["ps", "--ppid", str(pid), "-o", "pid=,etimes=,comm="],
                             capture_output=True, text=True, timeout=10).stdout
        for line in out.strip().splitlines():
            parts = line.split(None, 2)
            if len(parts) >= 2 and int(parts[1]) > 600:
                _emit(state, "telegram_listener_wedged",
                      f"telegram_listener child {parts[0]} ({parts[2] if len(parts) > 2 else '?'}) "
                      f"alive {int(parts[1]) // 60} min — delivery path stuck, operator "
                      f"messages queuing undelivered. Kill the child pid to unwedge.",
                      cooldown=DAEMON_DOWN_COOLDOWN)
                break
    except Exception:
        pass


def check_stuck_cron_forks(state: dict) -> None:
    """Find any `claude -p` process older than the age limit."""
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid,etimes,cmd"],
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout
    except Exception:
        # TimeoutExpired here used to propagate and abort the WHOLE poll cycle
        # (observed under memory pressure 2026-07-16) — skip just this check.
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


SESSION_STALE_SECONDS = 16 * 3600      # journal older than this = session not processing
INJECT_FRESH_SECONDS = 2 * 3600        # ...while injects newer than this = prompts still flowing
SESSION_DEAD_COOLDOWN = 12 * 3600      # re-alert at most 2x/day for a persistent outage


def check_session_liveness(state: dict) -> None:
    """Dead-man switch on tick OUTPUT, not daemon PIDs.

    2026-07-02 audit fix (skeptic+champion consensus #1 operational gap):
    4 outages in ~3 weeks (~7.5 of 21 days dark) where the interactive
    session died (expired creds) while every daemon stayed green — injects
    kept firing into the void and this watchdog saw nothing, because it
    watched PIDs and stuck forks, not whether ticks PRODUCE anything.
    Signature of that failure class: notes/journal.md goes stale while
    notes/inject_log.md stays fresh. Alert the operator directly via
    Telegram (LLM-independent path) so an outage is a ping within hours,
    not a silence discovered days later.
    """
    repo = Path(__file__).resolve().parent.parent
    journal = repo / "notes" / "journal.md"
    inject_log = repo / "notes" / "inject_log.md"
    try:
        journal_age = _now() - int(journal.stat().st_mtime)
        inject_age = _now() - int(inject_log.stat().st_mtime)
    except OSError:
        return
    if journal_age > SESSION_STALE_SECONDS and inject_age < INJECT_FRESH_SECONDS:
        _emit(state, "session_dead",
              f"SESSION LIKELY DEAD: journal.md stale {journal_age // 3600}h while injects "
              f"still flowing ({inject_age // 60}min ago) — ticks firing into the void "
              f"(MODEL QUOTA exhausted? expired creds?). Operator: check quota first "
              f"(cheapest fix — switch model), then re-login/restart.",
              cooldown=SESSION_DEAD_COOLDOWN)


def check_opportunity_watch(state: dict) -> None:
    """PID-alive check for the 24/7 opportunity daemon (added 2026-07-15).

    Its RSS self-cap makes it exit deliberately at >150MB; the */10 crontab
    keepalive restarts it, so only alert if it stays dead >25 min (i.e. the
    keepalive itself is failing)."""
    pid_p = Path(__file__).resolve().parent.parent / "logs" / "opportunity_watch.pid"
    try:
        pid = int(pid_p.read_text().strip())
    except Exception:
        return  # never started on this host — not an anomaly
    if _pid_alive(pid):
        state.pop("oppwatch_dead_since", None)
        return
    live = _pgrep("[o]pportunity_watch.py start")
    if live:
        print(f"[heartbeat] opportunity_watch PID file stale ({pid}) but daemon "
              f"alive at {live[0]} — no alert", flush=True)
        state.pop("oppwatch_dead_since", None)
        return
    dead_since = state.setdefault("oppwatch_dead_since", _now())
    if _now() - dead_since > 25 * 60:
        _emit(state, "opportunity_watch_dead",
              f"opportunity_watch PID {pid} dead >25min and the */10 keepalive "
              f"hasn't revived it — 24/7 scanning is DOWN. Check logs/opportunity_watch.log",
              cooldown=DAEMON_DOWN_COOLDOWN)


MEM_AVAILABLE_FLOOR_KB = 250 * 1024   # alert when the whole box has <250MB headroom
MEM_ALERT_COOLDOWN = 2 * 3600


def check_memory_pressure(state: dict) -> None:
    """OOM early-warning (2026-07-16, after the 3rd OOM crash took the VM +
    network down). The box has ~1.9GB RAM; each claude agent subprocess runs
    200-400MB RSS, so two concurrent agents + the main session exhausts it.
    The behavioral fix is sequential-agents-only; this check is the tripwire
    for whatever slips through — alert BEFORE the kernel starts killing."""
    try:
        meminfo = {}
        for line in open("/proc/meminfo"):
            k, v = line.split(":", 1)
            meminfo[k] = int(v.strip().split()[0])  # kB
        avail = meminfo.get("MemAvailable", 1 << 30)
    except Exception:
        return
    if avail < MEM_AVAILABLE_FLOOR_KB:
        # Attribute RSS by owner (2026-07-19): the first real firing showed the
        # top consumers were the OPERATOR's own concurrent claude sessions, not
        # polyclaude subprocesses — so "kill your agents" was the wrong advice.
        # Split the picture so the alert says WHO is using memory and points at
        # an accurate remediation.
        me = ""
        try:
            import getpass
            myuser = getpass.getuser()  # "polyclaude"
            out = subprocess.run(
                ["ps", "-eo", "rss,user,comm", "--sort=-rss"],
                capture_output=True, text=True, timeout=15).stdout.splitlines()[1:]
            my_mb, other_mb, top = 0, 0, []
            for l in out:
                parts = l.split(None, 2)
                if len(parts) < 3:
                    continue
                rss = int(parts[0]) // 1024
                # ps truncates long usernames ("polyclaude" -> "polycla+"),
                # so prefix-match against the truncation marker.
                uname = parts[1].rstrip("+")
                is_mine = myuser.startswith(uname)
                if "claude" in parts[2] or "python" in parts[2]:
                    if is_mine:
                        my_mb += rss
                    else:
                        other_mb += rss
                if len(top) < 3:
                    top.append(f"{parts[2]}({parts[1][:8]}) {rss}MB")
            me = (f"; polyclaude claude/py RSS {my_mb}MB vs other-user {other_mb}MB"
                  f"; top: {', '.join(top)}")
        except Exception:
            pass
        _emit(state, "memory_pressure",
              f"MEMORY PRESSURE: only {avail // 1024}MB available (floor "
              f"{MEM_AVAILABLE_FLOOR_KB // 1024}MB) — OOM risk (3 VM crashes already)."
              f"{me}. If polyclaude RSS dominates: serialize/kill agent subprocesses. "
              f"If other-user dominates: shared-host contention — reduce concurrent sessions.",
              cooldown=MEM_ALERT_COOLDOWN)


TICK_EXEC_GRACE_SECONDS = 45 * 60
TICK_EXEC_COOLDOWN = 3 * 3600


def check_tick_execution(state: dict) -> None:
    """End-to-end tick sentinel (2026-07-16). The 02:00 tick was DISPATCHED
    (send-keys typed into pane operator:0.0, logged in peer_skips.log) but the
    pane's inner claude was gone, so the keystrokes fell into a dead shell and
    the tick silently never ran. Pane-liveness heuristics can't fully close
    that hole; this check closes it at the OUTPUT end: a dispatch record with
    no journal write within the grace window means the tick was eaten."""
    repo = Path(__file__).resolve().parent.parent
    skips = repo / "logs" / "cron" / "peer_skips.log"
    journal = repo / "notes" / "journal.md"
    try:
        last_dispatch = None
        # bounded read: only the last 16KB matter for the newest dispatch line
        with open(skips, "rb") as fh:
            fh.seek(max(0, skips.stat().st_size - 16384))
            tail = fh.read().decode(errors="replace")
        for line in tail.splitlines()[::-1]:
            if "dispatched to operator pane" in line:
                ts = line.split()[0]  # 20260716T020001Z
                last_dispatch = int(time.mktime(time.strptime(ts, "%Y%m%dT%H%M%SZ")))
                break
        if last_dispatch is None:
            return
        journal_m = int(journal.stat().st_mtime)
    except Exception:
        return
    now = _now()
    if (now - last_dispatch > TICK_EXEC_GRACE_SECONDS
            and journal_m < last_dispatch
            and now - last_dispatch < 24 * 3600):
        _emit(state, "tick_dispatched_not_executed",
              f"TICK EATEN: cron tick dispatched to the pane "
              f"{(now - last_dispatch) // 60}min ago but journal.md hasn't been "
              f"touched since — the send-keys likely landed in a dead/absent claude. "
              f"Operator: check MODEL QUOTA first (a quota-exhausted pane looks "
              f"identical to a dead one — 2026-08-02, 16h), then restart the session.",
              cooldown=TICK_EXEC_COOLDOWN)
        # RECOVERY (2026-08-02): alerting alone left 16h of ticks unrun. Spawn
        # the headless fallback for THIS eaten tick — it runs a different model
        # than the interactive pane, so it completes when the pane's quota
        # bucket is exhausted. Guarded three ways: once per dispatch timestamp,
        # daily_checkin's own flock prevents concurrent runs, and the auth
        # post-flight telegrams the operator if the fallback also fails.
        # DISABLED BY DEFAULT 2026-08-03 (operator): the recovery spawns an
        # ADDITIONAL headless claude run — and the dominant cause of eaten
        # ticks is MODEL QUOTA EXHAUSTION, so recovering burns more of the
        # exact resource that ran out. Net-negative in the common case.
        # Opt back in with POLYCLAUDE_TICK_RECOVERY=1 only if the outage cause
        # is known NOT to be quota (e.g. a hung pane on a healthy account).
        if (os.environ.get("POLYCLAUDE_TICK_RECOVERY") == "1"
                and state.get("last_tick_recovery_for") != last_dispatch):
            state["last_tick_recovery_for"] = last_dispatch
            try:
                env = dict(os.environ, POLYCLAUDE_FORCE_HEADLESS="1")
                subprocess.Popen(
                    ["/bin/bash", str(repo / "scripts" / "daily_checkin.sh"),
                     "RECOVERY: prior tick was EATEN (pane unresponsive — quota or "
                     "hang). You are the headless fallback; run the standard check-in."],
                    cwd=str(repo), env=env,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                print("[heartbeat] tick-eaten RECOVERY: spawned headless daily_checkin", flush=True)
            except Exception as e:
                print(f"[heartbeat] recovery spawn failed: {e}", flush=True)


def check_operator_session(state: dict) -> None:
    """Alert when the operator tmux session itself is absent (2026-07-16
    audit: after the reboot, every daemon auto-recovered except the session —
    a human closed that gap 21 minutes later by luck. The session can't be
    auto-started (interactive login), so the fix is a prompt ping)."""
    try:
        r = subprocess.run(["tmux", "has-session", "-t", "operator"],
                           capture_output=True, timeout=10)
        if r.returncode != 0:
            _emit(state, "operator_session_missing",
                  "operator tmux session is ABSENT (reboot?) — ticks/injects/"
                  "messages have no destination and only headless fallbacks run. "
                  "Operator: start the session.",
                  cooldown=DAEMON_DOWN_COOLDOWN)
    except Exception:
        pass


def poll_once() -> None:
    state = _load_state()
    check_news_watcher(state)
    check_telegram_listener(state)
    check_stuck_cron_forks(state)
    check_session_liveness(state)
    check_opportunity_watch(state)
    check_memory_pressure(state)
    check_tick_execution(state)
    check_operator_session(state)
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
