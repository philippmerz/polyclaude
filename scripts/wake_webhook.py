#!/usr/bin/env python3
"""Box operator runtime: event wakes go to an HTTP webhook (Grok Bot).

Drop-in replacement for the retired host-private ``polyclaude-agent`` runner
(Kimi/opencode tmux pane). Point ``POLYCLAUDE_AGENT_RUNNER`` at this file.

Subcommands (same CLI shape callers already use):
  queue --workdir DIR [--reference-id N] [--expires-at TS]   prompt on stdin
      Build a compact JSON wake {id, source, severity, market_slug, headline, ts},
      apply policy + dedupe + rate limits, then POST it to POLYCLAUDE_WAKE_URL.
      Until URL and KEY are set, the wake is recorded as ``pending`` in
      logs/wake_outbox.jsonl and replayed later. Exit 0 = durably recorded.
  replay        POST every pending outbox wake (oldest first) if configured.
  alert --source NAME [--severity S]   text on stdin
      Operator alert (what used to be an outbound Telegram message). Same outbox,
      dedupe and rate limits as wakes, plus a severity (critical|warning|info).
      scripts/telegram.py routes every send here; outbound Telegram is disabled.
  status        Print config presence (never values) and outbox counts.
  run ...       No model backend on the box: exit 75 (callers fail open).
  operator-live Exit 1 (there is no interactive operator process).

Config (environment wins over <repo>/.env.wake, which is chmod 600 and git-ignored):
  POLYCLAUDE_WAKE_URL, POLYCLAUDE_WAKE_KEY
  POLYCLAUDE_WAKE_AUTH_HEADER   default "Authorization"
  POLYCLAUDE_WAKE_AUTH_SCHEME   default "Bearer" (empty = send the raw key)
  POLYCLAUDE_WAKE_MARKET_COOLDOWN_S default 1800, POLYCLAUDE_WAKE_DAILY_CAP default 12,
  POLYCLAUDE_WAKE_REPLAY_MAX_AGE_S default 86400 (older pending wakes expire).
Optional per-call hints: POLYCLAUDE_WAKE_SOURCE, POLYCLAUDE_WAKE_SEVERITY,
POLYCLAUDE_WAKE_MARKET.

Policy kept from notes/operator_autoprompt.json: event wakes (urgent news,
opportunity triggers, resting_watch critical order alerts) and Telegram
messages wake; scheduled ticks, self-followups and goal_set never do.
Telegram messages are user-initiated and exempt from the market cooldown and
daily cap (each update_id is still delivered at most once).

Alerts (kind="alert") are rate-limited separately from wakes so alert noise can
never starve a real wake: identical alert kind (text with digits normalised) at
most once per 30 min, health/heartbeat kinds at most once per hour
(POLYCLAUDE_WAKE_HEALTH_COOLDOWN_S), one alert per market per 30 min, and
POLYCLAUDE_ALERT_DAILY_CAP (default 12) non-critical alerts per UTC day.
Critical alerts are still deduped but bypass the market cooldown and daily cap.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NEVER_WAKE = {"scheduled_tick", "self_followup", "goal_set"}
HEALTH_SOURCES = {"heartbeat_watch", "daemon_keepalive", "box_supervisor"}
_HEALTH_RE = re.compile(r"\b(rss|cycle error|stale|stuck|dead|absent|disk|memory|keepalive|"
                        r"pid file|session|tick eaten|unreachable|timed? ?out)\b", re.I)
_CRITICAL_RE = re.compile(r"critical|emergency|escalation|fill suspected|pulled|liquidat", re.I)
_WARNING_RE = re.compile(r"warn|stale|stuck|dead|absent|fail|error|exceed|⚠|alert|eaten", re.I)


def _repo(workdir: str | None = None) -> Path:
    return Path(workdir).resolve() if workdir else REPO


def load_config(repo: Path) -> dict:
    file_vals: dict[str, str] = {}
    path = repo / ".env.wake"
    try:
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            file_vals[k.strip()] = v.strip().strip("'\"")
    except OSError:
        pass

    def get(name: str, default: str = "") -> str:
        val = os.environ.get(name)
        if val is None:
            val = file_vals.get(name, default)
        return val

    return {
        "url": get("POLYCLAUDE_WAKE_URL"),
        "key": get("POLYCLAUDE_WAKE_KEY"),
        "header": get("POLYCLAUDE_WAKE_AUTH_HEADER", "Authorization") or "Authorization",
        "scheme": get("POLYCLAUDE_WAKE_AUTH_SCHEME", "Bearer"),
        "cooldown": int(get("POLYCLAUDE_WAKE_MARKET_COOLDOWN_S", "1800") or 1800),
        "daily_cap": int(get("POLYCLAUDE_WAKE_DAILY_CAP", "12") or 12),
        "alert_daily_cap": int(get("POLYCLAUDE_ALERT_DAILY_CAP", "12") or 12),
        "health_cooldown": int(get("POLYCLAUDE_WAKE_HEALTH_COOLDOWN_S", "3600") or 3600),
        "max_age": int(get("POLYCLAUDE_WAKE_REPLAY_MAX_AGE_S", "86400") or 86400),
        "timeout": float(get("POLYCLAUDE_WAKE_TIMEOUT_S", "10") or 10),
    }


def auth_headers(cfg: dict) -> dict[str, str]:
    scheme = (cfg.get("scheme") or "").strip()
    value = f"{scheme} {cfg['key']}" if scheme else cfg["key"]
    return {cfg["header"]: value}


# ---------------------------------------------------------------- classify
_SLUG_RES = [
    re.compile(r"\bslug[=:]\s*([a-z0-9][a-z0-9-]{2,})", re.I),
    re.compile(r"polymarket\.com/(?:event|market)/([a-z0-9][a-z0-9-]{2,})", re.I),
]
_CID_RE = re.compile(r"\b0x[0-9a-fA-F]{64}\b")


def classify(text: str, *, reference_id: str | None = None,
             env: dict | None = None) -> dict:
    env = os.environ if env is None else env
    t = text or ""
    source = env.get("POLYCLAUDE_WAKE_SOURCE") or ""
    prompt_source = env.get("POLYCLAUDE_PROMPT_SOURCE") or ""
    if not source:
        if reference_id is not None or t.startswith("telegram: [update_id="):
            source = "telegram"
        elif "NEWS REVIEW REQUEST:" in t:
            source = "news_watcher"
        elif "REVALIDATION REQUEST FROM OPPORTUNITY WATCH:" in t:
            source = "opportunity_watch"
        elif t.startswith("[resting_watch]"):
            source = "resting_watch"
        elif t.startswith("/goal"):
            source = "goal_set"
        elif prompt_source:
            source = prompt_source
        elif t.startswith("Cron tick ") or t.startswith("Periodic check:"):
            source = "scheduled_tick"
        else:
            source = "other"

    headline = t
    if source == "telegram":
        parts = t.split("\n\n", 1)
        headline = parts[1] if len(parts) > 1 else t
    else:
        m = re.search(r"\[((?:NEWS REVIEW REQUEST|REVALIDATION REQUEST FROM OPPORTUNITY WATCH):.*)\]\s*$",
                      t, re.S)
        if m:
            headline = m.group(1)
        headline = re.sub(r"^\[resting_watch\]\s*", "", headline)
    headline = " ".join(headline.split())[:280]

    market = env.get("POLYCLAUDE_WAKE_MARKET") or ""
    if not market:
        for rx in _SLUG_RES:
            m = rx.search(t)
            if m:
                market = m.group(1).lower()
                break
    if not market:
        m = _CID_RE.search(t)
        if m:
            market = m.group(0).lower()
    if not market and source == "resting_watch":
        m = re.search(r"(?:PULLED|FILL suspected:)\s*([^\s:—]+)", t)
        if m:
            market = m.group(1).strip().lower()

    severity = env.get("POLYCLAUDE_WAKE_SEVERITY") or ""
    if not severity:
        up = t.upper()
        if "CRITICAL" in up or "EMERGENCY" in up or "FILL SUSPECTED" in up or "PULLED" in up:
            severity = "critical"
        elif source in ("news_watcher", "opportunity_watch", "resting_watch", "telegram"):
            severity = "high"
        else:
            severity = "info"
    return {"source": source, "severity": severity,
            "market_slug": market or None, "headline": headline}


# ---------------------------------------------------------------- outbox
class Outbox:
    def __init__(self, repo: Path):
        self.path = repo / "logs" / "wake_outbox.jsonl"
        self.lock_path = repo / "logs" / ".wake_outbox.lock"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        self._fh = open(self.lock_path, "a")
        fcntl.flock(self._fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._fh, fcntl.LOCK_UN)
        self._fh.close()

    def rows(self) -> list[dict]:
        out = []
        try:
            with self.path.open() as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            out.append(json.loads(line))
                        except ValueError:
                            pass
        except OSError:
            pass
        return out

    def append(self, row: dict) -> None:
        new = not self.path.exists()
        with self.path.open("a") as fh:
            fh.write(json.dumps(row, separators=(",", ":"), ensure_ascii=False) + "\n")
        if new:
            os.chmod(self.path, 0o600)


def _parse_ts(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def _now() -> dt.datetime:
    override = os.environ.get("POLYCLAUDE_WAKE_NOW")  # tests only
    if override:
        return _parse_ts(override)
    return dt.datetime.now(dt.timezone.utc)


def state_of(rows: list[dict]) -> dict[str, dict]:
    """Latest status per wake id (append-only event log)."""
    latest: dict[str, dict] = {}
    for r in rows:
        wid = r.get("id")
        if not wid:
            continue
        if r.get("event") == "wake":
            latest[wid] = dict(r)
        elif wid in latest:
            latest[wid]["status"] = r.get("status", latest[wid].get("status"))
    return latest


def post(cfg: dict, payload: dict) -> tuple[bool, str]:
    data = json.dumps(payload, separators=(",", ":")).encode()
    headers = {"Content-Type": "application/json", "User-Agent": "polyclaude-wake/1"}
    headers.update(auth_headers(cfg))
    req = urllib.request.Request(cfg["url"], data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=cfg["timeout"]) as resp:
            code = resp.status
        return (200 <= code < 300, f"http {code}")
    except urllib.error.HTTPError as e:
        return (False, f"http {e.code}")
    except Exception as e:  # network errors: keep pending
        return (False, type(e).__name__)


def _payload(row: dict) -> dict:
    out = {k: row[k] for k in ("id", "source", "severity", "market_slug", "headline", "ts")}
    out["kind"] = row.get("kind", "wake")
    return out


def replay(repo: Path, cfg: dict, ob: Outbox) -> dict:
    counts = {"sent": 0, "failed": 0, "expired": 0}
    if not (cfg["url"] and cfg["key"]):
        return counts
    now = _now()
    for wid, row in state_of(ob.rows()).items():
        if row.get("status") != "pending":
            continue
        if (now - _parse_ts(row["ts"])).total_seconds() > cfg["max_age"]:
            ob.append({"event": "status", "id": wid, "status": "expired", "at": now.isoformat()})
            counts["expired"] += 1
            continue
        ok, detail = post(cfg, _payload(row))
        ob.append({"event": "status", "id": wid, "status": "sent" if ok else "pending",
                   "attempt": detail, "at": now.isoformat()})
        counts["sent" if ok else "failed"] += 1
        if not ok:
            break  # preserve order; retry later
    return counts


def admit(row: dict, rows: list[dict], cfg: dict, now: dt.datetime) -> str:
    """Return 'pending' to deliver, or a terminal reason for log-only."""
    if row["source"] in NEVER_WAKE:
        return "suppressed_policy"
    if row.get("kind") == "alert":
        return admit_alert(row, rows, cfg, now)
    latest = {k: v for k, v in state_of(rows).items() if v.get("kind", "wake") == "wake"}
    for prev in latest.values():
        if prev.get("dedupe_key") == row["dedupe_key"] and prev.get("status") in ("pending", "sent"):
            if row["source"] == "telegram" or \
                    (now - _parse_ts(prev["ts"])).total_seconds() < cfg["cooldown"]:
                return "duplicate"
    if row["source"] == "telegram":
        return "pending"
    if row.get("market_slug"):
        for prev in latest.values():
            if prev.get("market_slug") == row["market_slug"] and prev.get("source") != "telegram" \
                    and prev.get("status") in ("pending", "sent") \
                    and (now - _parse_ts(prev["ts"])).total_seconds() < cfg["cooldown"]:
                return "rate_limited_market"
    day = now.date().isoformat()
    used = sum(1 for p in latest.values()
               if p.get("source") != "telegram" and p.get("status") in ("pending", "sent", "expired")
               and p["ts"][:10] == day)
    if used >= cfg["daily_cap"]:
        return "rate_limited_daily"
    return "pending"


def _is_health(row: dict) -> bool:
    return row["source"] in HEALTH_SOURCES or bool(_HEALTH_RE.search(row.get("headline") or ""))


def admit_alert(row: dict, rows: list[dict], cfg: dict, now: dt.datetime) -> str:
    latest = [v for v in state_of(rows).values() if v.get("kind") == "alert"
              and v.get("status") in ("pending", "sent", "expired")]
    age = lambda p: (now - _parse_ts(p["ts"])).total_seconds()  # noqa: E731
    window = cfg["health_cooldown"] if _is_health(row) else cfg["cooldown"]
    if any(p.get("dedupe_key") == row["dedupe_key"] and age(p) < window for p in latest):
        return "duplicate"
    if row["severity"] == "critical":
        return "pending"
    if row.get("market_slug") and any(
            p.get("market_slug") == row["market_slug"] and age(p) < cfg["cooldown"] for p in latest):
        return "rate_limited_market"
    day = now.date().isoformat()
    used = sum(1 for p in latest if p.get("severity") != "critical" and p["ts"][:10] == day)
    if used >= cfg["alert_daily_cap"]:
        return "rate_limited_daily"
    return "pending"


def alert_kind(text: str) -> str:
    t = re.sub(r"0x[0-9a-fA-F]+", "0x#", text.lower())
    t = re.sub(r"\d+(?:[.,]\d+)*", "#", t)
    return " ".join(t.split())[:100]


def classify_alert(text: str, source: str, severity: str | None = None,
                   env: dict | None = None) -> dict:
    env = os.environ if env is None else env
    info = classify(text, env={k: v for k, v in env.items()
                               if k in ("POLYCLAUDE_WAKE_MARKET",)})
    sev = (severity or env.get("POLYCLAUDE_WAKE_SEVERITY") or "").lower()
    if sev not in ("critical", "warning", "info"):
        if _CRITICAL_RE.search(text):
            sev = "critical"
        elif source in HEALTH_SOURCES or _WARNING_RE.search(text) or _HEALTH_RE.search(text):
            sev = "warning"
        else:
            sev = "info"
    headline = re.sub(r"^\[[A-Za-z_ ]+\]\s*", "", " ".join((text or "").split()))[:280]
    return {"source": source or "other", "severity": sev,
            "market_slug": info["market_slug"], "headline": headline}


def record_alert(text: str, *, source: str, severity: str | None = None,
                 repo: Path | None = None) -> tuple[str, str]:
    """Durably record one operator alert; POST it now if the webhook is configured."""
    repo = repo or REPO
    cfg = load_config(repo)
    info = classify_alert(text, source, severity)
    now = _now()
    dkey = hashlib.sha256(f"alert|{info['source']}|{alert_kind(text)}".encode()).hexdigest()[:16]
    wid = hashlib.sha256(f"{dkey}|{now.isoformat()}".encode()).hexdigest()[:12]
    row = {"event": "wake", "kind": "alert", "id": wid,
           "ts": now.isoformat().replace("+00:00", "Z"), **info, "dedupe_key": dkey,
           "prompt_sha256": hashlib.sha256(text.encode()).hexdigest()}
    with Outbox(repo) as ob:
        row["status"] = admit(row, ob.rows(), cfg, now)
        ob.append(row)
        if row["status"] == "pending" and cfg["url"] and cfg["key"]:
            replay(repo, cfg, ob)
        final = state_of(ob.rows()).get(wid, row).get("status")
    return wid, final


def cmd_alert(args) -> int:
    text = sys.stdin.read()
    if not text.strip():
        print("ERROR: empty alert", file=sys.stderr)
        return 2
    wid, final = record_alert(text, source=args.source, severity=args.severity,
                              repo=_repo(args.workdir))
    print(f"alert {wid}: {final}")
    return 0


def cmd_queue(args) -> int:
    repo = _repo(args.workdir)
    cfg = load_config(repo)
    text = sys.stdin.read()
    if not text.strip():
        print("ERROR: empty prompt", file=sys.stderr)
        return 2
    info = classify(text, reference_id=args.reference_id)
    now = _now()
    if info["source"] == "telegram" and args.reference_id is not None:
        dkey = f"telegram:{args.reference_id}"
    else:
        dkey = hashlib.sha256(f"{info['source']}|{info['market_slug']}|{info['headline']}"
                              .encode()).hexdigest()[:16]
    wid = hashlib.sha256(f"{dkey}|{now.isoformat()}".encode()).hexdigest()[:12]
    row = {"event": "wake", "kind": "wake", "id": wid, "ts": now.isoformat().replace("+00:00", "Z"),
           **info, "dedupe_key": dkey, "prompt_sha256": hashlib.sha256(text.encode()).hexdigest()}
    with Outbox(repo) as ob:
        row["status"] = admit(row, ob.rows(), cfg, now)
        ob.append(row)
        if row["status"] == "pending" and cfg["url"] and cfg["key"]:
            replay(repo, cfg, ob)
        final = state_of(ob.rows()).get(wid, row).get("status")
    print(f"wake {wid}: {final}")
    return 0


def cmd_replay(args) -> int:
    repo = _repo(getattr(args, "workdir", None))
    cfg = load_config(repo)
    with Outbox(repo) as ob:
        c = replay(repo, cfg, ob)
    print(json.dumps({"configured": bool(cfg["url"] and cfg["key"]), **c}))
    return 0


def cmd_status(args) -> int:
    repo = _repo(getattr(args, "workdir", None))
    cfg = load_config(repo)
    ob = Outbox(repo)
    counts: dict[str, int] = {}
    for r in state_of(ob.rows()).values():
        counts[r.get("status", "?")] = counts.get(r.get("status", "?"), 0) + 1
    print(json.dumps({"url_set": bool(cfg["url"]), "key_set": bool(cfg["key"]),
                      "auth_header": cfg["header"], "auth_scheme": cfg["scheme"],
                      "outbox": counts}))
    return 0


def main(argv=None) -> int:
    raw = list(argv if argv is not None else sys.argv[1:])
    if raw and raw[0] == "run":
        sys.stdin.read() if not sys.stdin.isatty() else None
        print("no model backend on this host (operator runtime is the wake webhook)", file=sys.stderr)
        return 75
    if raw and raw[0] == "operator-live":
        return 1
    if raw and raw[0] not in ("queue", "replay", "status", "alert"):
        print(f"unsupported subcommand: {raw[0]}", file=sys.stderr)
        return 69
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    q = sub.add_parser("queue")
    q.add_argument("--workdir")
    q.add_argument("--reference-id")
    q.add_argument("--expires-at")
    a = sub.add_parser("alert")
    a.add_argument("--workdir")
    a.add_argument("--source", default="other")
    a.add_argument("--severity", choices=["critical", "warning", "info"])
    for name in ("replay", "status"):
        s = sub.add_parser(name)
        s.add_argument("--workdir")
    args, _rest = p.parse_known_args(argv)
    if args.cmd == "queue":
        return cmd_queue(args)
    if args.cmd == "alert":
        return cmd_alert(args)
    if args.cmd == "replay":
        return cmd_replay(args)
    if args.cmd == "status":
        return cmd_status(args)
    p.print_usage(sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
