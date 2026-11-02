#!/usr/bin/env python3
"""Resolution-source watcher: poll the named primary source behind held or
rested markets, diff it, and raise identity-attributed alerts.

Origin: research/2026-11-01-strategy-sweep.md BUILD item, re-verified in
research/2026-11-02-sweep-verification/README.md. The sweep's stated rationale
("the HLE lesson proved repricing lags minutes-to-hours") is NOT supported by
the journal; this daemon is built for a narrower, verified reason:

  * notes/resting_watch_config.json rests a hidden-info SELL (Kimi HLE >=55 at
    0.90) whose own justification puts post-jump fair at ~0.95 "after an
    official >=55 submission lands on agi.safe.ai". Nothing polled that source
    automatically, so the rest could be lifted below post-jump fair.
  * resting_watch auto-pulls only on a CRITICAL impact attributed to the rest's
    conditionId in notes/news_alerts.jsonl. This daemon can write exactly that
    row when a configured threshold rule trips on the resolving source.
  * Wayback captures of dashboard.safe.ai/api/models have been HTTP 403 since
    2026-08-28, so a live change history only exists if we record it. Every
    detected change is appended to logs/source_watch_history.jsonl with the
    linked tokens' public CLOB midpoints, which is the dataset the sweep's lag
    claim would need.

ALERT-ONLY. Never places, cancels or sizes orders. Safety defaults:
  master=false   -> the loop does nothing.
  mode="paper"   -> changes/alerts go only to logs/source_watch_paper.jsonl;
                    no news_alerts.jsonl rows, no Telegram.
  mode="live"    -> also appends news_alerts.jsonl rows and (optionally)
                    Telegram messages. Still no trading.
First successful fetch of a source only establishes a baseline. A fetch or
parse failure never replaces the baseline (fail closed, as in
source_freeze_check.py).

Source kinds:
  hle_chart_api  dashboard.safe.ai/api/models, parsed with
                 source_freeze_check.hle_chart_results (the one instrument).
  http_text      any page; tags stripped, optional extract_regex narrows the
                 compared region; change = normalized-text hash differs.

CLI: source_watch.py start | stop | status | once | check
  check  fetch + diff against stored baseline, print, write nothing.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))
from source_freeze_check import hle_chart_results  # noqa: E402

PY = str(REPO / ".venv" / "bin" / "python3")
CONFIG_PATH = REPO / "notes" / "source_watch_config.json"
ALERTS_PATH = REPO / "notes" / "news_alerts.jsonl"
STATE_PATH = REPO / "logs" / ".source_watch_state.json"
HISTORY_PATH = REPO / "logs" / "source_watch_history.jsonl"
MIDS_PATH = REPO / "logs" / "source_watch_mids.jsonl"
PAPER_PATH = REPO / "logs" / "source_watch_paper.jsonl"
PID_PATH = REPO / "logs" / "source_watch.pid"
LOG_PATH = REPO / "logs" / "source_watch.log"
MIDPOINT_URL = "https://clob.polymarket.com/midpoint"

RSS_CAP_MB = 150
POLL_SECONDS_DEFAULT = 600
POLL_SECONDS_MIN = 120
ESCALATE_CONSECUTIVE_ERRORS = 6
LEVELS = ("MINOR", "MATERIAL", "CRITICAL")
DEFAULT_HEADERS = {
    # The chart API returns 403 to library default user-agents; these match
    # source_freeze_check.py (verified 200 on 2026-11-02).
    "User-Agent": "Mozilla/5.0 (polyclaude source monitor)",
    "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
    "Origin": "https://agi.safe.ai",
    "Referer": "https://agi.safe.ai/",
}


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _stamp(t: dt.datetime | None = None) -> str:
    return (t or _now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"[{_stamp()}] {msg}\n")
    except OSError:
        pass


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save_json_atomic(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _rss_mb() -> float:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return float(line.split()[1]) / 1024.0
    except OSError:
        pass
    return 0.0


# --------------------------------------------------------------------- config

def validate_config(cfg: dict) -> list[str]:
    problems = []
    if not isinstance(cfg, dict):
        return ["config is not an object"]
    if cfg.get("mode", "paper") not in ("paper", "live"):
        problems.append("mode must be paper|live")
    sources = cfg.get("sources")
    if not isinstance(sources, list):
        return problems + ["sources must be a list"]
    seen = set()
    for src in sources:
        sid = str(src.get("id") or "")
        if not sid or sid in seen:
            problems.append(f"source id missing or duplicate: {sid!r}")
        seen.add(sid)
        if src.get("kind") not in ("hle_chart_api", "http_text"):
            problems.append(f"{sid}: kind must be hle_chart_api|http_text")
        if not str(src.get("url") or "").startswith("https://"):
            problems.append(f"{sid}: url must be https")
        for rule in src.get("rules") or []:
            if rule.get("level") not in LEVELS:
                problems.append(f"{sid}: rule level must be one of {LEVELS}")
            try:
                re.compile(str(rule.get("name_regex", "")))
            except re.error:
                problems.append(f"{sid}: bad name_regex")
            if "score_gte" in rule and not isinstance(rule["score_gte"], (int, float)):
                problems.append(f"{sid}: score_gte must be numeric")
            if src.get("kind") != "hle_chart_api" and ("name_regex" in rule or "score_gte" in rule):
                problems.append(f"{sid}: name/score rules need kind=hle_chart_api")
        for pos in src.get("positions") or []:
            if not str(pos.get("condition_id") or "").startswith("0x"):
                problems.append(f"{sid}: position condition_id must be 0x-hex")
    return problems


def load_config() -> dict:
    cfg = _load_json(CONFIG_PATH, None)
    if cfg is None:
        raise RuntimeError(f"config missing or malformed: {CONFIG_PATH}")
    problems = validate_config(cfg)
    if problems:
        raise RuntimeError("invalid config: " + "; ".join(problems))
    return cfg


# ------------------------------------------------------------------ fetching

def _normalize_text(html: str, extract_regex: str | None) -> str:
    if extract_regex:
        m = re.search(extract_regex, html, re.S | re.I)
        if not m:
            raise ValueError("extract_regex matched nothing (layout changed?)")
        html = m.group(1) if m.groups() else m.group(0)
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def fetch_inventory(client: httpx.Client, src: dict) -> dict:
    """Return {'kind', 'hash', 'rows'|'text_len'}; raise on any doubt."""
    headers = {**DEFAULT_HEADERS, **(src.get("headers") or {})}
    r = client.get(src["url"], headers=headers)
    r.raise_for_status()
    if src["kind"] == "hle_chart_api":
        rows = hle_chart_results(r.json())
        canon = json.dumps(sorted([k, *v] for k, v in rows.items()))
        return {"kind": "hle_chart_api", "rows": {k: list(v) for k, v in rows.items()},
                "hash": hashlib.sha256(canon.encode()).hexdigest()}
    text = _normalize_text(r.text, src.get("extract_regex"))
    if len(text) < int(src.get("min_chars", 200)):
        raise ValueError(f"normalized text only {len(text)} chars; refusing to baseline")
    return {"kind": "http_text", "text_len": len(text),
            "hash": hashlib.sha256(text.encode()).hexdigest()}


# ------------------------------------------------------------------- diffing

def diff_rows(old: dict, new: dict) -> dict:
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(k for k in set(old) & set(new) if list(old[k]) != list(new[k]))
    return {"added": added, "removed": removed, "changed": changed}


def _score(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None  # "-" placeholder = row without an HLE score yet


def classify(src: dict, old: dict, new: dict) -> tuple[str | None, list[str], dict]:
    """Level of a change (None = no change), human reasons, structured diff.

    hle_chart_api: each rule names a model-name regex. A touched row matching
    it raises the rule level; with score_gte the rule only fires when the
    row's new score is >= the bar AND the old score (if any) was below it.
    Untouched-by-rules changes are MINOR. http_text: any change is
    src['change_level'] (default MATERIAL).
    """
    if old["hash"] == new["hash"]:
        return None, [], {}
    if src["kind"] == "http_text":
        lvl = src.get("change_level", "MATERIAL")
        return lvl, [f"page text changed ({old.get('text_len')} -> {new.get('text_len')} chars)"], {}
    o, n = old["rows"], new["rows"]
    d = diff_rows(o, n)
    touched = d["added"] + d["changed"] + d["removed"]
    level_idx, reasons = 0, []
    for name in touched:
        before = o.get(name)
        after = n.get(name)
        desc = f"{name}: {before[0] if before else 'absent'} -> {after[0] if after else 'removed'}"
        hit_idx = 0
        for rule in src.get("rules") or []:
            if not re.search(rule.get("name_regex", ""), name, re.I):
                continue
            if "score_gte" in rule:
                ns = _score(after[0]) if after else None
                os_ = _score(before[0]) if before else None
                if ns is None or ns < rule["score_gte"] or (os_ is not None and os_ >= rule["score_gte"]):
                    continue
            hit_idx = max(hit_idx, LEVELS.index(rule["level"]))
        level_idx = max(level_idx, hit_idx)
        reasons.append(f"[{LEVELS[hit_idx]}] {desc}")
    return LEVELS[level_idx], reasons, d


# ------------------------------------------------------------------- outputs

def midpoints(client: httpx.Client, src: dict) -> dict:
    out = {}
    for pos in src.get("positions") or []:
        tok = pos.get("token_id")
        if not tok:
            continue
        try:
            r = client.get(MIDPOINT_URL, params={"token_id": tok}, timeout=15)
            out[pos.get("slug") or tok[:12]] = float(r.json().get("mid"))
        except Exception:
            out[pos.get("slug") or tok[:12]] = None
    return out


def build_alert(src: dict, level: str, reasons: list[str], when: dt.datetime) -> dict:
    title = f"[source_watch] {src['id']} changed ({level}): " + "; ".join(reasons)[:300]
    keys = " ".join(src.get("alert_keys") or [src["id"]])
    impacts = [{"position": str(p["condition_id"]).lower(), "level": level,
                "reason": f"resolution source {src['url']} changed: " + "; ".join(reasons)[:400]}
               for p in src.get("positions") or []]
    aid = hashlib.sha1(f"source_watch|{src['id']}|{title}|{_stamp(when)}".encode()).hexdigest()
    return {
        "alert_id": aid, "ts": _stamp(when), "tier": 1,
        "feed": f"source_watch:{src['id']}", "matched": keys, "title": title,
        "link": src.get("display_url") or src["url"],
        "agent_reason": ("Deterministic resolution-source diff (no LLM). Verify on the "
                         "primary source before acting."),
        "impacts": impacts,
        "relevance": "portfolio_material_critical" if level != "MINOR" else "minor",
        "review_required": level != "MINOR",
    }


def telegram(text: str) -> None:
    try:
        subprocess.run([PY, str(SCRIPTS / "telegram.py"), "msg", "--stdin"], cwd=str(REPO),
                       input=text, text=True, capture_output=True, timeout=60)
    except Exception as exc:  # alerting must never kill the daemon
        _log(f"telegram failed: {exc}")


# --------------------------------------------------------------------- cycle


def dense_active(state: dict, now: dt.datetime | None = None) -> bool:
    """True while any source is inside its dense post-change mid-snapshot
    window (C1 measurement: baseline mids every poll, dense mids every
    ~dense_poll_seconds for dense_minutes after each detected change)."""
    now = now or _now()
    stamp = _stamp(now)
    for st in (state.get("sources") or {}).values():
        until = st.get("dense_until")
        if until and str(until) > stamp:
            return True
    return False

def run_cycle(cfg: dict, state: dict, client: httpx.Client, *, write: bool = True,
              now: dt.datetime | None = None) -> list[str]:
    """One pass over every enabled source. Mutates `state`. Returns actions."""
    now = now or _now()
    mode = cfg.get("mode", "paper")
    out: list[str] = []
    srcstate = state.setdefault("sources", {})
    for src in cfg["sources"]:
        if not src.get("enabled", True):
            continue
        sid = src["id"]
        st = srcstate.setdefault(sid, {})
        try:
            new = fetch_inventory(client, src)
        except Exception as exc:
            st["consecutive_errors"] = int(st.get("consecutive_errors", 0)) + 1
            st["last_error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            out.append(f"{sid}: fetch/parse FAILED ({st['consecutive_errors']}x): {st['last_error']}")
            if (write and mode == "live" and cfg.get("telegram", False)
                    and st["consecutive_errors"] == ESCALATE_CONSECUTIVE_ERRORS):
                telegram(f"[source_watch] {sid} unreadable {st['consecutive_errors']}x: "
                         f"{st['last_error']} (baseline kept; source changes are NOT being seen)")
            continue
        st["consecutive_errors"] = 0
        st["last_ok"] = _stamp(now)
        dense = bool(st.get("dense_until") and str(st["dense_until"]) > _stamp(now))
        if cfg.get("mid_log", True):
            _append_jsonl(MIDS_PATH, {"ts": _stamp(now), "source": sid,
                                      "kind": "dense" if dense else "baseline",
                                      "midpoints": midpoints(client, src)})
        base = st.get("baseline")
        if base is None:
            st["baseline"] = new
            out.append(f"{sid}: baseline established ({new['hash'][:12]})")
            continue
        level, reasons, d = classify(src, base, new)
        if level is None:
            out.append(f"{sid}: unchanged")
            continue
        out.append(f"{sid}: CHANGE {level}: " + "; ".join(reasons))
        st["dense_until"] = _stamp(now + dt.timedelta(
            minutes=float(cfg.get("dense_minutes", 45))))
        if not write:
            continue
        mids = midpoints(client, src)
        hist = {"ts": _stamp(now), "source": sid, "level": level, "reasons": reasons,
                "diff": d, "old_hash": base["hash"], "new_hash": new["hash"],
                "midpoints": mids, "mode": mode}
        _append_jsonl(HISTORY_PATH, hist)
        if cfg.get("mid_log", True):
            _append_jsonl(MIDS_PATH, {"ts": _stamp(now), "source": sid,
                                      "kind": "change", "midpoints": mids})
        alert = build_alert(src, level, reasons, now)
        min_level = cfg.get("min_alert_level", "MATERIAL")
        if LEVELS.index(level) >= LEVELS.index(min_level):
            if mode == "live":
                _append_jsonl(ALERTS_PATH, alert)
                if cfg.get("telegram", False):
                    telegram(alert["title"] + f"\nmids: {mids}")
                out.append(f"{sid}: alert written ({alert['alert_id'][:10]})")
            else:
                _append_jsonl(PAPER_PATH, {**alert, "paper": True, "midpoints": mids})
                out.append(f"{sid}: PAPER alert logged ({alert['alert_id'][:10]})")
        st["baseline"] = new
        st["last_change"] = _stamp(now)
    return out


def poll_loop() -> int:
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(os.getpid()), encoding="utf-8")
    _log(f"up pid={os.getpid()}")
    with httpx.Client(timeout=45, follow_redirects=True) as client:
        while True:
            poll = POLL_SECONDS_DEFAULT
            try:
                cfg = load_config()
                poll = max(POLL_SECONDS_MIN, int(cfg.get("poll_seconds", POLL_SECONDS_DEFAULT)))
                if not cfg.get("master", False):
                    _log("master=false; idle")
                else:
                    state = _load_json(STATE_PATH, {"sources": {}})
                    for action in run_cycle(cfg, state, client):
                        _log(action)
                    _save_json_atomic(STATE_PATH, state)
                    # Recompute AFTER the cycle: a change detected this pass
                    # must dense-poll from the very next sleep (checking
                    # before the cycle would wait a full 600s baseline poll,
                    # missing most of the post-change window).
                    if dense_active(state):
                        # Dense floor 60s: the regular POLL_SECONDS_MIN guards
                        # the baseline cadence; the dense window is bounded
                        # (~dense_minutes), so the extra ~30 polls per change
                        # day stay well inside venue rate limits.
                        poll = max(60, int(cfg.get("dense_poll_seconds", 90)))
            except Exception as exc:
                _log(f"cycle error: {exc}")
            if _rss_mb() > RSS_CAP_MB:
                _log(f"rss cap {_rss_mb():.0f}MB exceeded; exiting for keepalive restart")
                return 0
            time.sleep(poll)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    if mode == "status":
        alive = PID_PATH.exists() and Path(f"/proc/{PID_PATH.read_text().strip()}").exists()
        state = _load_json(STATE_PATH, {"sources": {}})
        cfg = _load_json(CONFIG_PATH, {})
        print(f"source_watch {'UP' if alive else 'DOWN'} master={cfg.get('master')} "
              f"mode={cfg.get('mode', 'paper')}")
        for sid, st in state.get("sources", {}).items():
            print(f"  {sid}: last_ok={st.get('last_ok')} last_change={st.get('last_change')} "
                  f"errors={st.get('consecutive_errors', 0)}")
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
    if mode in ("once", "check"):
        cfg = load_config()
        state = _load_json(STATE_PATH, {"sources": {}})
        if mode == "once" and not cfg.get("master", False):
            print("master=false; nothing done (use `check` for a read-only diff)")
            return 0
        with httpx.Client(timeout=45, follow_redirects=True) as client:
            for action in run_cycle(cfg, state, client, write=(mode == "once")):
                print(action)
        if mode == "once":
            _save_json_atomic(STATE_PATH, state)
        return 0
    if mode != "start":
        print("unknown mode; use start|stop|status|once|check", file=sys.stderr)
        return 2
    return poll_loop()


if __name__ == "__main__":
    sys.exit(main())
