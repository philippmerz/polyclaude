#!/usr/bin/env python3
"""Premium resting-order watcher — one-sided maker rests on held positions.

Operator-authorized 2026-11-01. Automates the doctrine in
notes/resting_orders.md and strategy/03_opportunity_method.md: premium-to-fair
maker SELLS are free options (a no-fill costs nothing; a fill converts marks
to cash above fair, fee-free). This daemon keeps a small, justified set of
resting sells aligned with current priors and pulls them on the conditions the
doctrine names:

  - hidden-info class: rest strictly ABOVE fair, at a price that also clears
    the post-jump fair estimate (an informed up-spike means fair jumped; a
    fill must leave us happy). Enforced: min_price > fair + premium_pp.
  - ordinary class: rest at or above fair.
  - scheduled catalysts / unassessed material news: cancel-first (suspend;
    re-underwrite is an agent decision, never an automatic repost).
  - quote lifetime: every rest carries a named max age, after which it is
    cancelled for re-underwriting (the October 19 quote-lifetime rule).
  - group/set-only legs and dust positions are never rested.

Buy-side rests (discounted bids below the pessimistic bound, via the gated
polyclaude_enter.py maker path) are config-ready but intentionally disabled in
v1: each creates a gated reservation and merits its own underwriting pass.

Actions run through the vetted clob_v2.py CLI (post-only sells; guarded
cancels). The daemon is a tiny scheduler; every action is a short-lived
subprocess. RSS self-caps like opportunity_watch.

CLI: resting_watch.py start | stop | status | once | plan
"""

from __future__ import annotations

import datetime as dt
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
PY = str(REPO / ".venv" / "bin" / "python3")
CLOB = str(SCRIPTS / "clob_v2.py")
CONFIG_PATH = REPO / "notes" / "resting_watch_config.json"
PRIORS_PATH = REPO / "notes" / "portfolio_kelly_priors.json"
ALERTS_PATH = REPO / "notes" / "news_alerts.jsonl"
STATE_PATH = REPO / "logs" / ".resting_watch_state.json"
PID_PATH = REPO / "logs" / "resting_watch.pid"
LOG_PATH = REPO / "logs" / "resting_watch.log"

RSS_CAP_MB = 150
LOOP_SECONDS_DEFAULT = 120
DEFAULT_PREMIUM_PP = 0.05
MATERIAL_LEVELS = {"MATERIAL", "CRITICAL"}


def _log(msg: str) -> None:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"[{stamp}] {msg}\n")
    except OSError:
        pass


def _rss_mb() -> float:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return float(line.split()[1]) / 1024.0
    except OSError:
        pass
    return 0.0


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save_json_atomic(path: Path, value) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_config() -> dict:
    cfg = _load_json(CONFIG_PATH, {})
    if not isinstance(cfg, dict) or not isinstance(cfg.get("rests"), list):
        raise RuntimeError(f"config missing or malformed: {CONFIG_PATH}")
    return cfg


def load_fairs() -> dict[str, float]:
    """slug -> central p_yes from the Kelly priors file."""
    priors = _load_json(PRIORS_PATH, {})
    out = {}
    for slug, row in priors.items():
        if isinstance(row, dict):
            try:
                out[slug] = float(row.get("p_yes"))
            except (TypeError, ValueError):
                continue
    return out


def validate_rest(rest: dict, fair: float | None) -> list[str]:
    """Return policy violations for one rest config (empty = clean)."""
    problems = []
    if rest.get("side") != "SELL":
        problems.append("v1 supports side=SELL only")
    shares = rest.get("shares")
    if not isinstance(shares, (int, float)) or shares <= 0:
        problems.append("shares must be positive")
    price = rest.get("min_price")
    if not isinstance(price, (int, float)) or not (0 < price < 1):
        problems.append("min_price must be in (0,1)")
    cls = rest.get("class")
    if cls not in ("hidden", "ordinary"):
        problems.append("class must be hidden|ordinary")
    if not str(rest.get("justification") or "").strip():
        problems.append("quote-lifetime rule: justification required")
    if fair is None:
        problems.append("no fair (p_yes) in priors file")
    else:
        if cls == "hidden":
            floor = min(1.0, fair + float(rest.get("premium_pp", DEFAULT_PREMIUM_PP)))
            if price is not None and price <= floor:
                problems.append(
                    f"hidden-info rest {price} not strictly above fair+premium ({floor:.3f})")
        elif cls == "ordinary" and price is not None and price < fair:
            problems.append(f"ordinary rest {price} below fair {fair}")
    return problems


def open_orders() -> list[dict]:
    r = subprocess.run(
        [PY, CLOB, "orders"], cwd=str(REPO), capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"orders read failed rc={r.returncode}: {r.stderr[:200]}")
    if not (r.stdout or "").strip():
        raise RuntimeError("orders read returned empty output (lock contention or CLI fault)")
    try:
        payload = json.loads(r.stdout)
    except ValueError as exc:
        raise RuntimeError(f"orders read non-JSON output: {(r.stdout or '')[:160]!r}") from exc
    body = payload.get("body") or {}
    rows = body.get("data")
    if not isinstance(rows, list):
        raise RuntimeError("orders read returned unexpected shape")
    return [o for o in rows if isinstance(o, dict)]


def place_sell(rest: dict) -> str:
    r = subprocess.run(
        [PY, CLOB, "sell", str(rest["asset"]),
         f"{float(rest['min_price']):.3f}".rstrip("0").rstrip("."),
         str(rest["shares"]), "--post-only"],
        cwd=str(REPO), capture_output=True, text=True, timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise RuntimeError(f"sell post failed rc={r.returncode}: {out[:240]}")
    # cmd_sell prints progress lines before the JSON document; parse the last
    # JSON object in the output.
    raw = r.stdout or ""
    start = raw.rfind("{")
    payload = None
    while start != -1:
        try:
            payload = json.loads(raw[start:])
            break
        except ValueError:
            start = raw.rfind("{", 0, start)
    if payload is None:
        raise RuntimeError(f"sell post returned no JSON: {out[:200]}")
    body = payload.get("body") or {}
    if payload.get("status_code", 999) >= 400 or not body.get("success"):
        raise RuntimeError(f"sell post rejected: {out[:240]}")
    order_id = str(body.get("orderID") or "")
    if not order_id:
        raise RuntimeError("sell post returned no orderID")
    return order_id


def cancel_order(order_id: str) -> None:
    r = subprocess.run(
        [PY, CLOB, "cancel", order_id],
        cwd=str(REPO), capture_output=True, text=True, timeout=120)
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise RuntimeError(f"cancel failed rc={r.returncode}: {out[:240]}")


def telegram(text: str) -> None:
    try:
        subprocess.run(
            [PY, str(SCRIPTS / "telegram.py"), "msg", "--stdin"],
            cwd=str(REPO), input=text, text=True, capture_output=True, timeout=60)
    except Exception as exc:  # alerting must never kill the daemon
        _log(f"telegram failed: {exc}")


AGENT_RUNNER = "/home/polyclaude/.local/bin/polyclaude-agent"
AGENT_WAKE_MIN_SECONDS = 1800
HUMAN_ESCALATE_CONSECUTIVE_ERRORS = 5


def wake_agent(text: str, state: dict, *, force: bool = False) -> bool:
    """Queue a bounded message to the operator session (durable spool ->
    injector). Throttled to one wake per AGENT_WAKE_MIN_SECONDS unless
    force. Returns True when a wake was queued."""
    now = dt.datetime.now(dt.timezone.utc)
    last = dt.datetime.fromisoformat(
        str(state.get("last_agent_wake", "1970-01-01T00:00:00+00:00")))
    if not force and (now - last).total_seconds() < AGENT_WAKE_MIN_SECONDS:
        return False
    try:
        r = subprocess.run(
            [AGENT_RUNNER, "queue", "--workdir", str(REPO)],
            input=text, text=True, capture_output=True, timeout=60)
        if r.returncode != 0:
            _log(f"agent wake queue failed rc={r.returncode}: {(r.stderr or '')[:160]}")
            return False
        state["last_agent_wake"] = now.isoformat()
        return True
    except Exception as exc:
        _log(f"agent wake failed: {exc}")
        return False


def recent_material_alerts(keys: list[str], since: dt.datetime) -> list[dict]:
    """news_alerts rows after `since` whose text matches keys and carry a
    MATERIAL/CRITICAL impact level (classifier-populated)."""
    if not keys:
        return []
    rows = []
    try:
        with ALERTS_PATH.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    except (OSError, ValueError):
        return []
    hits = []
    for row in rows:
        try:
            ts = dt.datetime.fromisoformat(str(row.get("ts", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts < since:
            continue
        hay = (str(row.get("matched", "")) + " " + str(row.get("title", ""))).lower()
        if not any(k.lower() in hay for k in keys):
            continue
        impacts = row.get("impacts") or []
        levels = {str(i.get("level", "")).upper() for i in impacts if isinstance(i, dict)}
        if levels & MATERIAL_LEVELS:
            hits.append(row)
    return hits


CYCLE_LOCK = REPO / "logs" / ".resting_watch_cycle.lock"


def reconcile(cfg: dict, state: dict, dry_run: bool = False) -> list[str]:
    """One reconciliation pass, serialized against concurrent runners."""
    import fcntl
    lock_fd = os.open(CYCLE_LOCK, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock_fd)
        return ["cycle skipped: another reconcile holds the lock"]
    try:
        return _reconcile_locked(cfg, state, dry_run)
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


def _reconcile_locked(cfg: dict, state: dict, dry_run: bool = False) -> list[str]:
    """One reconciliation pass. Returns a human-readable action summary."""
    actions: list[str] = []
    fairs = load_fairs()
    now = dt.datetime.now(dt.timezone.utc)
    master = bool(cfg.get("master", False))
    max_age_h = float(cfg.get("max_lifetime_hours", 72))
    book = open_orders()
    book_by_id = {str(o.get("id")): o for o in book}

    if not master:
        for key, managed in list(state.get("managed", {}).items()):
            if managed.get("order_id") in book_by_id:
                if not dry_run:
                    cancel_order(managed["order_id"])
                actions.append(f"KILL master=off: cancelled {key}")
            state.get("managed", {}).pop(key, None)
        if actions and not dry_run:
            _save_json_atomic(STATE_PATH, state)
        return actions

    for rest in cfg["rests"]:
        slug = str(rest.get("slug") or "")
        key = f"{slug}:{rest.get('side')}:{rest.get('min_price')}"
        managed = state.setdefault("managed", {}).get(key)
        if not rest.get("enabled", False):
            if managed and managed.get("order_id") in book_by_id:
                if not dry_run:
                    cancel_order(managed["order_id"])
                actions.append(f"disabled rest cancelled: {key}")
                state["managed"].pop(key, None)
            continue

        fair = fairs.get(slug)
        problems = validate_rest(rest, fair)
        if problems:
            if managed and managed.get("order_id") in book_by_id:
                if not dry_run:
                    cancel_order(managed["order_id"])
                actions.append(f"INVALID config, cancelled: {key} ({problems[0]})")
                state["managed"].pop(key, None)
            else:
                actions.append(f"INVALID config, not placed: {key} ({problems[0]})")
            continue

        # Existing managed order?
        if managed and managed.get("order_id") in book_by_id:
            placed_at = dt.datetime.fromisoformat(
                str(managed.get("placed_at", "")).replace("Z", "+00:00"))
            age_h = (now - placed_at).total_seconds() / 3600.0
            pull_reason = None
            if age_h > max_age_h:
                pull_reason = f"lifetime {age_h:.1f}h > {max_age_h}h; re-underwrite required"
            else:
                hits = recent_material_alerts(
                    list(rest.get("alert_keys") or []), placed_at)
                if hits:
                    pull_reason = (f"cancel-first: {len(hits)} MATERIAL/CRITICAL alert(s) "
                                   f"since placement (latest {hits[-1].get('ts')})")
            if pull_reason:
                if not dry_run:
                    cancel_order(managed["order_id"])
                    state["managed"][key] = {**managed, "suspended": pull_reason,
                                             "suspended_at": now.isoformat()}
                    _save_json_atomic(STATE_PATH, state)
                    wake_agent(f"[resting_watch] PULLED {key}: {pull_reason}. "
                               "Review the trigger; clear the suspension in "
                               "logs/.resting_watch_state.json to re-place.", state)
                actions.append(f"pulled {key}: {pull_reason}")
            continue

        # Managed order gone from the book: filled (or dead). Do not repost.
        if managed and managed.get("order_id") not in book_by_id \
                and not managed.get("suspended"):
            actions.append(f"FILLED/dead: {key} order {managed['order_id'][:12]} gone "
                           "from book; re-underwrite before any repost")
            state["managed"][key] = {**managed, "suspended": "order left the book",
                                     "suspended_at": now.isoformat()}
            if not dry_run:
                _save_json_atomic(STATE_PATH, state)
                wake_agent(f"[resting_watch] FILL suspected: {key} — verify the fill, "
                           "journal it, and re-underwrite before any repost.", state,
                           force=True)
                telegram(f"[resting_watch] fill suspected: {key}")
            continue

        # Suspended rests wait for manual re-underwrite (agent decision).
        if managed and managed.get("suspended"):
            continue

        # No order, no state: place it.
        actions.append(f"PLACE {key} shares={rest['shares']} (justification on file)")
        if not dry_run:
            order_id = place_sell(rest)
            state["managed"][key] = {
                "order_id": order_id, "placed_at": now.isoformat(),
                "shares": rest["shares"], "price": rest["min_price"],
                "justification": rest["justification"],
            }
            _save_json_atomic(STATE_PATH, state)
            _log(f"placed {key} order={order_id} justification={rest['justification']}")
    return actions


def poll_loop() -> int:
    PID_PATH.write_text(str(os.getpid()), encoding="utf-8")
    _log(f"up pid={os.getpid()}")
    while True:
        try:
            cfg = load_config()
            state = _load_json(STATE_PATH, {"managed": {}})
            for action in reconcile(cfg, state):
                _log(action)
        except Exception as exc:
            _log(f"cycle error: {exc}")
            state = _load_json(STATE_PATH, {"managed": {}})
            state["consecutive_errors"] = int(state.get("consecutive_errors", 0)) + 1
            woke = wake_agent(
                f"[resting_watch] cycle error ({state['consecutive_errors']}x): "
                f"{str(exc)[:200]}. Check logs/resting_watch.log; set master=false "
                "in notes/resting_watch_config.json to halt all rests.", state)
            if state["consecutive_errors"] >= HUMAN_ESCALATE_CONSECUTIVE_ERRORS:
                telegram(f"[resting_watch] ESCALATION: {state['consecutive_errors']} "
                         f"consecutive cycle errors; last: {str(exc)[:140]}")
                state["consecutive_errors"] = 0  # re-arm after notifying
            if woke or state["consecutive_errors"] == 1:
                _save_json_atomic(STATE_PATH, state)
        else:
            if int(state.get("consecutive_errors", 0)) > 0:
                state["consecutive_errors"] = 0
                _save_json_atomic(STATE_PATH, state)
        if _rss_mb() > RSS_CAP_MB:
            _log(f"rss cap {_rss_mb():.0f}MB exceeded; exiting for keepalive restart")
            return 0
        time.sleep(int(load_config().get("poll_seconds", LOOP_SECONDS_DEFAULT)))


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    if mode == "status":
        alive = PID_PATH.exists() and Path(f"/proc/{PID_PATH.read_text().strip()}").exists()
        state = _load_json(STATE_PATH, {"managed": {}})
        print(f"resting_watch {'UP' if alive else 'DOWN'} managed={len(state.get('managed', {}))}")
        return 0
    if mode == "plan":
        cfg = load_config()
        state = {"managed": _load_json(STATE_PATH, {"managed": {}}).get("managed", {})}
        for action in reconcile(cfg, {"managed": dict(state)}, dry_run=True):
            print(action)
        return 0
    if mode == "stop":
        if PID_PATH.exists():
            pid = int(PID_PATH.read_text().strip())
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"sent SIGTERM to {pid}")
            except Exception as exc:
                print(f"could not signal {pid}: {exc}")
            PID_PATH.unlink(missing_ok=True)
        return 0
    if mode == "once":
        cfg = load_config()
        state = _load_json(STATE_PATH, {"managed": {}})
        for action in reconcile(cfg, state):
            print(action)
        return 0
    if mode != "start":
        print("unknown mode; use start|stop|status|once|plan", file=sys.stderr)
        return 2
    return poll_loop()


if __name__ == "__main__":
    sys.exit(main())
