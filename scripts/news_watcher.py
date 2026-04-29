"""Polyclaude news watcher.

Long-running daemon: polls a configurable list of RSS feeds every N seconds,
matches entry titles + summaries against tiered keyword lists, and:

- Tier 1 (book-resolving events: Trump dies, regime falls, aliens confirmed,
  peace deal signed, etc.) → Telegram alert with [URGENT] prefix AND auto-fires
  a cron-style check-in so a fresh max-effort session reacts ASAP.
- Tier 2 (notable but not resolution-shifting) → Telegram alert with [NEWS]
  prefix only; the next scheduled cron tick will pick it up.

Config: `news_watcher_config.json` colocated with this script (in repo, editable).
State (seen entry ids, last alerts): file pointed to by POLYCLAUDE_NEWS_STATE.

Subcommands: start | status | stop | once  (the last polls one cycle and exits,
useful for testing).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import feedparser
import httpx

import _paths as _secrets

_secrets.install_scrubbing_excepthook()

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent

CONFIG_PATH = _SCRIPT_DIR / "news_watcher_config.json"
STATE_PATH = _secrets.path("POLYCLAUDE_NEWS_STATE")
PID_PATH = _secrets.path("POLYCLAUDE_NEWS_PID")
LOG_PATH = _REPO_ROOT / "logs" / "news_watcher.log"
TELEGRAM_TOKEN_PATH = _secrets.path("POLYCLAUDE_TELEGRAM_TOKEN")
TELEGRAM_STATE_PATH = _secrets.path("POLYCLAUDE_TELEGRAM_STATE")
CRON_SCRIPT = _SCRIPT_DIR / "daily_checkin.sh"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"seen_ids": [], "last_alerts": {}, "last_cron_trigger": 0}
    return json.loads(STATE_PATH.read_text())


def save_state(s: dict) -> None:
    s["seen_ids"] = s.get("seen_ids", [])[-5000:]  # bounded
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(s, indent=2))
    os.chmod(STATE_PATH, 0o600)


def telegram_send(text: str) -> None:
    """Best-effort Telegram message. Logs failure but doesn't raise."""
    try:
        token = TELEGRAM_TOKEN_PATH.read_text().strip()
        chat_id = json.loads(TELEGRAM_STATE_PATH.read_text())["chat_id"]
        # Cap length to Telegram's 4096; trim with ellipsis
        if len(text) > 4000:
            text = text[:3997] + "..."
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "disable_web_page_preview": False},
            timeout=10,
        )
        if not r.json().get("ok"):
            print(f"[watcher] telegram error: {_secrets.scrub(r.text[:200])}", flush=True)
    except Exception as e:
        print(f"[watcher] telegram exception: {_secrets.scrub(str(e))}", flush=True)


def fire_cron_tick() -> None:
    """Spawn the daily check-in as a detached background process."""
    try:
        subprocess.Popen(
            ["/bin/bash", str(CRON_SCRIPT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print("[watcher] auto-triggered daily_checkin.sh (Tier-1 event)", flush=True)
    except Exception as e:
        print(f"[watcher] failed to spawn cron tick: {e}", flush=True)


def entry_id(entry) -> str:
    """Stable id for an RSS entry — prefer guid/link, fall back to title hash."""
    base = entry.get("id") or entry.get("guid") or entry.get("link") or entry.get("title", "")
    return hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest()


def match_keywords(text: str, keywords: list[str]) -> str | None:
    """Return the first matching keyword (lowercased), or None."""
    lo = text.lower()
    for kw in keywords:
        if kw.lower() in lo:
            return kw
    return None


def poll_once(config: dict, state: dict) -> int:
    """Run one polling cycle. Returns number of new alerts emitted."""
    seen = set(state.get("seen_ids", []))
    last_alerts = state.get("last_alerts", {})
    cooldown = config.get("alert_cooldown_seconds", 1800)
    max_entries = config.get("max_entries_per_feed", 30)
    tier1 = config.get("tier1_keywords", [])
    tier2 = config.get("tier2_keywords", [])
    now = time.time()

    new_alerts = 0
    tier1_fired = False

    for feed in config["feeds"]:
        try:
            d = feedparser.parse(feed["url"])
        except Exception as e:
            print(f"[watcher] feed error {feed['name']}: {e}", flush=True)
            continue
        for entry in (d.entries or [])[:max_entries]:
            eid = entry_id(entry)
            if eid in seen:
                continue
            seen.add(eid)
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")
            blob = f"{title}. {summary}"
            link = entry.get("link", "")

            kw1 = match_keywords(blob, tier1)
            kw2 = None if kw1 else match_keywords(blob, tier2)
            if not kw1 and not kw2:
                continue

            tier = 1 if kw1 else 2
            kw = kw1 or kw2

            # Per-keyword cooldown to avoid spamming on a hot story
            cooldown_key = f"t{tier}:{kw}"
            last = last_alerts.get(cooldown_key, 0)
            if now - last < cooldown:
                continue
            last_alerts[cooldown_key] = now

            prefix = "[URGENT]" if tier == 1 else "[NEWS]"
            msg = (
                f"{prefix} {feed['name']}\n"
                f"matched: {kw}\n"
                f"\n{title}\n"
                f"\n{link}"
            )
            telegram_send(msg)
            print(f"[watcher] alert tier{tier} kw={kw!r} feed={feed['name']} title={title[:80]!r}", flush=True)
            new_alerts += 1
            if tier == 1:
                tier1_fired = True

    if tier1_fired:
        # Rate-limit auto-cron firing so a multi-headline event doesn't spawn
        # several simultaneous check-ins.
        last_trigger = state.get("last_cron_trigger", 0)
        if now - last_trigger >= 1800:  # 30-min minimum between auto-fires
            fire_cron_tick()
            state["last_cron_trigger"] = now

    state["seen_ids"] = list(seen)
    state["last_alerts"] = last_alerts
    save_state(state)
    return new_alerts


def cmd_start(_args: argparse.Namespace) -> int:
    PID_PATH.write_text(str(os.getpid()))
    print(f"[watcher] up pid={os.getpid()}", flush=True)
    backoff = 1.0
    while True:
        try:
            cfg = load_config()
            st = load_state()
            n = poll_once(cfg, st)
            if n:
                print(f"[watcher] {n} new alerts this cycle", flush=True)
            backoff = 1.0
            time.sleep(int(cfg.get("poll_interval_seconds", 300)))
        except KeyboardInterrupt:
            print("[watcher] interrupted", flush=True)
            return 0
        except Exception as e:
            print(f"[watcher] loop exception: {_secrets.scrub(str(e))}; sleeping {backoff:.1f}s", flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, 300)


def cmd_once(_args: argparse.Namespace) -> int:
    cfg = load_config()
    st = load_state()
    n = poll_once(cfg, st)
    print(f"poll done: {n} new alert(s)")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    if not PID_PATH.exists():
        print("watcher not running"); return 1
    pid = int(PID_PATH.read_text().strip())
    try:
        os.kill(pid, 0)
    except OSError:
        print(f"PID {pid} not alive (stale PID file)"); return 1
    s = load_state()
    print(f"watcher pid={pid} seen={len(s.get('seen_ids', []))} last_cron_trigger={s.get('last_cron_trigger', 0)}")
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
