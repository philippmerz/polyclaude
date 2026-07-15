#!/usr/bin/env python3
"""Continuous opportunity watcher — 24/7 scanning between cron ticks.

Operator authorization 2026-07-15 ("you have the VM 24/7... run some script
constantly. Just cap the memory use"). Rationale: arbs and price-triggers are
EPHEMERAL — a real consistency/monotonicity arb lives minutes-to-hours, and
armed price triggers (ARB retrace-add, regime-fall re-entry) were only checked
at 2x-daily ticks. This daemon closes that latency gap.

Design (memory-safe by construction):
  - The parent is a tiny scheduler loop (~30MB RSS). Heavy scans run as
    SUBPROCESSES of the existing, tested scanner scripts — children die after
    each run, so scan memory never accumulates in the daemon.
  - Inline work is limited to single cheap HTTP calls (price triggers).
  - RSS self-cap: parent reads /proc/self/status each loop and EXITS at
    RSS_CAP_MB (crontab keepalive restarts it; a death also surfaces via
    heartbeat_watch PID check).

Schedules:
  - every 300s: armed price triggers (notes/opportunity_triggers.json)
  - every 900s: polymarket_consistency_scan (parse REAL-arb count)
  - every 900s (staggered +450s): event_monotonicity_scan (parse violations)

Alerting: hits append notes/opportunity_alerts.jsonl. ACTIONABLE hits (real
arb >2% net, or an armed capital trigger crossing) telegram the operator AND
fire daily_checkin.sh (90-min cooldown, same pattern as news_watcher Tier-1).
Info hits just queue for the next tick.

CLI: opportunity_watch.py start | once
"""

from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
PY = str(REPO / ".venv" / "bin" / "python3")
ALERTS_PATH = REPO / "notes" / "opportunity_alerts.jsonl"
TRIGGERS_PATH = REPO / "notes" / "opportunity_triggers.json"
STATE_PATH = REPO / "logs" / ".opportunity_watch_state.json"
PID_PATH = REPO / "logs" / "opportunity_watch.pid"

RSS_CAP_MB = 150
LOOP_SECONDS = 60
PRICE_EVERY = 300
SCAN_EVERY = 900
CRON_FIRE_COOLDOWN = 5400   # 90 min, matches news_watcher
ALERT_COOLDOWN = 3600       # per-key telegram cooldown


def _now() -> int:
    return int(time.time())


def _log(msg: str) -> None:
    print(f"[oppwatch {dt.datetime.utcnow().isoformat(timespec='seconds')}Z] {msg}", flush=True)


def _rss_mb() -> float:
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmRSS"):
                return int(line.split()[1]) / 1024.0
    except Exception:
        pass
    return 0.0


def _load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"last": {}, "alerts": {}, "last_cron": 0}


def _save_state(s: dict) -> None:
    try:
        STATE_PATH.write_text(json.dumps(s))
    except Exception:
        pass


def _append_alert(rec: dict) -> None:
    rec["ts"] = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    try:
        with ALERTS_PATH.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        _log(f"alert append failed: {e}")


def _telegram(text: str) -> None:
    try:
        subprocess.run([PY, str(SCRIPTS / "telegram.py"), "msg", text],
                       capture_output=True, timeout=30, cwd=str(REPO))
    except Exception as e:
        _log(f"telegram failed: {e}")


def _fire_tick(state: dict, why: str) -> None:
    if _now() - state.get("last_cron", 0) < CRON_FIRE_COOLDOWN:
        _log(f"cron-fire suppressed (cooldown): {why}")
        return
    state["last_cron"] = _now()
    _log(f"FIRING tick: {why}")
    try:
        subprocess.Popen(["bash", str(SCRIPTS / "daily_checkin.sh")],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        _log(f"tick fire failed: {e}")


def _alert(state: dict, key: str, text: str, actionable: bool) -> None:
    _append_alert({"key": key, "text": text, "actionable": actionable})
    last = state.get("alerts", {}).get(key, 0)
    if _now() - last < ALERT_COOLDOWN:
        _log(f"telegram suppressed (cooldown): {key}")
    else:
        state.setdefault("alerts", {})[key] = _now()
        _telegram(f"[OPPWATCH] {text}")
    if actionable:
        _fire_tick(state, key)


# ---------- checks ----------

def check_price_triggers(state: dict) -> None:
    """Armed triggers from notes/opportunity_triggers.json.

    Format: [{"key": "arb-retrace-add", "kind": "coingecko"|"clob_no_ask",
              "id": <coingecko id>|<token_id>, "op": "<="|">=",
              "level": 0.08, "note": "...", "actionable": true}]
    """
    try:
        trigs = json.loads(TRIGGERS_PATH.read_text())
    except Exception:
        return
    for t in trigs:
        try:
            if t["kind"] == "coingecko":
                r = httpx.get("https://api.coingecko.com/api/v3/simple/price",
                              params={"ids": t["id"], "vs_currencies": "usd"}, timeout=15).json()
                px = float(r[t["id"]]["usd"])
            elif t["kind"] == "clob_no_ask":
                b = httpx.get("https://clob.polymarket.com/book",
                              params={"token_id": t["id"]}, timeout=15).json()
                asks = sorted(b.get("asks", []), key=lambda x: float(x["price"]))
                if not asks:
                    continue
                px = float(asks[0]["price"])
            else:
                continue
        except Exception:
            continue
        hit = (px <= t["level"]) if t["op"] == "<=" else (px >= t["level"])
        if hit:
            _alert(state, t["key"],
                   f"armed trigger CROSSED: {t['key']} at {px} ({t['op']} {t['level']}). {t.get('note','')}",
                   bool(t.get("actionable")))


def run_consistency(state: dict) -> None:
    try:
        r = subprocess.run([PY, str(SCRIPTS / "polymarket_consistency_scan.py")],
                           capture_output=True, text=True, timeout=300, cwd=str(REPO))
        out = (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        _log(f"consistency run failed: {e}")
        return
    for line in out.splitlines():
        if "REAL free-arb candidates exceed" in line:
            n = line.strip().split()[0]
            if n.isdigit() and int(n) > 0:
                _alert(state, "consistency-arb",
                       f"consistency scan: {n} REAL free-arb candidate(s) >2% net — window is ephemeral, act now. See logs/polymarket_consistency_latest.json",
                       actionable=True)
            return
    _log("consistency: no REAL-arb line parsed")


def run_monotonicity(state: dict) -> None:
    try:
        r = subprocess.run([PY, str(SCRIPTS / "event_monotonicity_scan.py")],
                           capture_output=True, text=True, timeout=300, cwd=str(REPO))
        out = (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        _log(f"monotonicity run failed: {e}")
        return
    if "0 monotonicity violations" in out or "(no violations)" in out:
        return
    for line in out.splitlines():
        if "monotonicity violations" in line and not line.strip().startswith("# 0"):
            _alert(state, "monotonicity-arb",
                   f"monotonicity scan: {line.strip()[:160]} — decomposition arb window, act now.",
                   actionable=True)
            return


# ---------- main ----------

def poll_loop() -> int:
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(os.getpid()))
    state = _load_state()
    _log(f"up pid={os.getpid()} rss={_rss_mb():.0f}MB cap={RSS_CAP_MB}MB")
    offset = 0
    while True:
        now = _now()
        last = state.setdefault("last", {})
        try:
            if now - last.get("price", 0) >= PRICE_EVERY:
                last["price"] = now
                check_price_triggers(state)
            if now - last.get("consistency", 0) >= SCAN_EVERY:
                last["consistency"] = now
                run_consistency(state)
            if now - last.get("monotonicity", 0) >= SCAN_EVERY + 450 - (450 if last.get("monotonicity") else 0):
                last["monotonicity"] = now
                run_monotonicity(state)
        except KeyboardInterrupt:
            return 0
        except Exception as e:
            _log(f"loop error: {e}")
        _save_state(state)
        rss = _rss_mb()
        if rss > RSS_CAP_MB:
            _telegram(f"[OPPWATCH] RSS {rss:.0f}MB > cap {RSS_CAP_MB}MB — exiting for restart (keepalive).")
            _log(f"RSS cap exceeded ({rss:.0f}MB) — exiting")
            return 1
        time.sleep(LOOP_SECONDS)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "start"
    if mode == "once":
        state = _load_state()
        check_price_triggers(state)
        run_consistency(state)
        run_monotonicity(state)
        _save_state(state)
        _log(f"once done rss={_rss_mb():.0f}MB")
        return 0
    return poll_loop()


if __name__ == "__main__":
    sys.exit(main())
