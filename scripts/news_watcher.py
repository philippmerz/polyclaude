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
ALERTS_LOG_PATH = _REPO_ROOT / "notes" / "news_alerts.jsonl"
TELEGRAM_TOKEN_PATH = _secrets.path("POLYCLAUDE_TELEGRAM_TOKEN")
TELEGRAM_STATE_PATH = _secrets.path("POLYCLAUDE_TELEGRAM_STATE")
CRON_SCRIPT = _SCRIPT_DIR / "daily_checkin.sh"


def _append_news_alert(record: dict) -> None:
    """Append one structured alert line to notes/news_alerts.jsonl.

    Consumed by the cron tick: each tick reads recent records and decides
    whether to act on MATERIAL/CRITICAL impacts. Bounded growth: kept
    reasonable by manual rotation; check-in script drops processed entries.
    """
    try:
        ALERTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with ALERTS_LOG_PATH.open("a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[watcher] alerts-log append failed: {_secrets.scrub(str(e))}", flush=True)


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"seen_ids": [], "last_alerts": {}, "last_cron_trigger": 0,
                "seen_titles": {}}
    s = json.loads(STATE_PATH.read_text())
    # Migration: old state files may not have seen_titles
    s.setdefault("seen_titles", {})
    return s


def save_state(s: dict) -> None:
    s["seen_ids"] = s.get("seen_ids", [])[-5000:]  # bounded
    # Prune seen_titles older than 24h to keep state file bounded.
    # Title-dedup is intra-day; older syndicated copies of the same story
    # are rare enough that re-firing once a day is acceptable.
    now = time.time()
    cutoff = now - 86400  # 24h
    s["seen_titles"] = {t: ts for t, ts in s.get("seen_titles", {}).items()
                        if ts >= cutoff}
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(s, indent=2))
    os.chmod(STATE_PATH, 0o600)


def _normalize_title(title: str) -> str:
    """Normalize a feed-entry title for cross-feed dedup.

    Lowercase, collapse whitespace, strip leading/trailing non-word chars.
    Keeps numerics (date-tagged headlines stay distinct) and punctuation
    inside (don't accidentally collide unrelated headlines that happen to
    overlap on stripped form).

    Example: "Trump shelved 'Project Freedom' after Saudis refused use of
    bases and airspace" — same across all 9 syndicated feeds, normalizes
    identically, dedups.
    """
    if not title:
        return ""
    return " ".join(title.lower().split()).strip()


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


# --- smart filter for Tier-2 alerts ---------------------------------------

# In-process cache of formatted positions; refreshed every 5 min so the
# agent always sees roughly-current book without hammering data-api.
_POSITIONS_CACHE: dict = {"text": None, "ts": 0.0}
_POSITIONS_CACHE_TTL_SECONDS = 300


def _positions_summary_blocking() -> str:
    """Fetch + format current positions for inclusion in agent prompts.

    Cached for 5 min in-process. On any failure, returns a short string
    so the agent still has something to reason about.
    """
    now = time.time()
    if _POSITIONS_CACHE["text"] and now - _POSITIONS_CACHE["ts"] < _POSITIONS_CACHE_TTL_SECONDS:
        return _POSITIONS_CACHE["text"]

    lines: list[str] = ["Polymarket sleeve:"]
    try:
        addr = json.loads(_secrets.path("POLYCLAUDE_WALLET").read_text())["address"]
        r = httpx.get(
            "https://data-api.polymarket.com/positions",
            params={"user": addr.lower(), "limit": "50"},
            timeout=10,
        )
        for p in (r.json() or []):
            cur = float(p.get("curPrice") or 0)
            cost = float(p.get("initialValue") or 0)
            lines.append(f"- {p['outcome']} {cur:.3f} (${cost:.2f}) — {p['title'][:70]}")
    except Exception as e:
        lines.append(f"  (positions read failed: {_secrets.scrub(str(e))[:120]})")

    # Crypto sleeve — keep simple; agent gets enough context from the headline.
    lines.append("\nCrypto sleeve: small Ostium positions (currently long XAU/USD 5x ~$5 collateral).")

    text = "\n".join(lines)
    _POSITIONS_CACHE["text"] = text
    _POSITIONS_CACHE["ts"] = now
    return text


def _agent_filter_tier2(feed_name: str, kw: str, title: str, summary: str) -> tuple[bool, str, list[dict]]:
    """Ask claude -p whether a Tier-2 match should reach Telegram + per-position impact.

    Returns (should_send, one_line_reason, per_position_impacts).
    Each impact is {"position": str, "level": NONE|MINOR|MATERIAL|CRITICAL, "reason": str}.
    On agent error/timeout/unparseable output, returns (True, "agent unavailable: ...", [])
    — fail-OPEN so the operator sees raw alerts rather than silent drops.
    """
    pos = _positions_summary_blocking()
    body = (summary or "")[:600].replace("\n", " ").strip()
    prompt = (
        "You filter news for polyclaude (autonomous trading project) AND assess "
        "per-position impact. Open positions:\n\n"
        f"{pos}\n\n"
        f"News article (matched keyword \"{kw}\", source {feed_name}):\n"
        f"Title: {title}\n"
        f"Summary: {body}\n\n"
        "FIRST LINE: SEND or SUPPRESS verdict.\n"
        "  - SEND = the article moves a probability the operator cares about (state change, named officials taking action, hard numbers, named-entity events).\n"
        "  - SUPPRESS = recycled noise (rephrasing of existing facts, opinion pieces, generic topic mentions).\n\n"
        "FOLLOWING LINES (only if SEND, only for IMPACTED positions): one line per "
        "materially-affected position, in this exact format:\n"
        "  IMPACT: <short-position-key>: <MINOR|MATERIAL|CRITICAL>: <one-line directional reason>\n"
        "  - MINOR = thesis still holds; tiny mark-to-market drift expected.\n"
        "  - MATERIAL = thesis pressure or confirmation; consider rebalance/scale on next tick.\n"
        "  - CRITICAL = thesis-invalidating or thesis-resolving; urgent re-evaluation.\n"
        "Use a short kebab-case position-key DERIVED from each position's title "
        "in the list above (e.g., 'Iran-peace deal by May 31' → 'iran-peace'; "
        "'Atletico Madrid top-4 La Liga' → 'atletico-top4'). Skip positions where "
        "the news has no causal channel — don't fabricate connections. If a "
        "position is no longer in the list above, do NOT score it.\n\n"
        "Respond:\n"
        "LINE 1: SEND: <why> OR SUPPRESS: <why>\n"
        "LINE 2+: IMPACT lines (only if SEND and positions are actually impacted)"
    )

    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "haiku", prompt],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/tmp",  # avoid loading polyclaude project context (CLAUDE.md, tools)
        )
        out = (r.stdout or "").strip()
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        first_line = lines[0] if lines else ""
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
        return (True, f"agent unavailable: {_secrets.scrub(str(e))[:120]}", [])

    impacts: list[dict] = []
    for line in lines[1:]:
        # IMPACT: <key>: <LEVEL>: <reason>
        if not line.upper().startswith("IMPACT:"):
            continue
        try:
            _, rest = line.split(":", 1)
            parts = [p.strip() for p in rest.split(":", 2)]
            if len(parts) < 3:
                continue
            key, level, reason = parts[0], parts[1].upper(), parts[2]
            if level not in ("MINOR", "MATERIAL", "CRITICAL", "NONE"):
                continue
            if level == "NONE":
                continue
            impacts.append({"position": key, "level": level, "reason": reason[:240]})
        except Exception:
            continue

    upper = first_line.upper()
    if upper.startswith("SEND"):
        reason = first_line[4:].lstrip(": ").strip() or "(no reason)"
        return (True, reason, impacts)
    if upper.startswith("SUPPRESS"):
        reason = first_line[8:].lstrip(": ").strip() or "(no reason)"
        return (False, reason, [])
    # Couldn't parse — fail open
    return (True, f"agent unparseable: {first_line[:120]}", impacts)


def entry_id(entry) -> str:
    """Stable id for an RSS entry — prefer guid/link, fall back to title hash."""
    base = entry.get("id") or entry.get("guid") or entry.get("link") or entry.get("title", "")
    return hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest()


import re as _re

_KW_REGEX_CACHE: dict[str, _re.Pattern] = {}


def _kw_regex(kw: str) -> _re.Pattern:
    """Compile a word-boundary regex for a keyword phrase, cached.

    Avoids substring false-positives like "et disclosure" matching
    "asset disclosure" or "trump dead" matching "trump deadline".
    """
    if kw in _KW_REGEX_CACHE:
        return _KW_REGEX_CACHE[kw]
    # Match the phrase with \b on each end. Allow flexible whitespace
    # between tokens so "trump  dies" (double space) still matches.
    tokens = kw.lower().split()
    pat = r"\b" + r"\s+".join(_re.escape(t) for t in tokens) + r"\b"
    rx = _re.compile(pat, _re.IGNORECASE)
    _KW_REGEX_CACHE[kw] = rx
    return rx


def match_keywords(text: str, keywords: list[str]) -> str | None:
    """Return the first matching keyword phrase, or None.

    Uses word-boundary matching so a keyword like "et disclosure" does
    not fire on substrings like "asset disclosure".
    """
    if not text:
        return None
    for kw in keywords:
        if _kw_regex(kw).search(text):
            return kw
    return None


def poll_once(config: dict, state: dict) -> int:
    """Run one polling cycle. Returns number of new alerts emitted."""
    seen = set(state.get("seen_ids", []))
    seen_titles: dict[str, float] = state.get("seen_titles", {})  # title-hash → first-seen-ts
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
            # Title-hash dedup across feeds: same syndicated story
            # republished with new GUIDs across N feeds was firing N alerts.
            # Normalize title and check the seen_titles dict (24h window).
            # Lesson source: 2026-05-08 saw "Trump shelved Project Freedom"
            # fire 9× in 4h across syndicated feeds.
            tnorm = _normalize_title(title)
            if tnorm and tnorm in seen_titles:
                continue
            if tnorm:
                seen_titles[tnorm] = now
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

            # Tier-2 goes through agent-filter (broad keyword recall + agent
            # precision). Tier-1 always sends — those are auto-cron-firing,
            # we never want to suppress a regime-changing event.
            agent_reason = None
            impacts: list[dict] = []
            if tier == 2:
                send, agent_reason, impacts = _agent_filter_tier2(feed["name"], kw, title, summary)
                if not send:
                    print(f"[watcher] suppressed tier2 kw={kw!r} feed={feed['name']} "
                          f"reason={agent_reason[:120]!r} title={title[:80]!r}", flush=True)
                    continue

            # Telegram pings are ACTION-ONLY (operator is autonomous, raw news
            # adds noise without value). Only Tier-1 catastrophic events ping
            # immediately — those auto-fire a cron tick that does the work.
            # Tier-2 (incl. MATERIAL/CRITICAL impacts) silently persists to
            # news_alerts.jsonl; the next scheduled cron tick reads, decides,
            # and includes the digest in its tick-summary Telegram.
            if tier == 1:
                why_line = f"\nwhy: {agent_reason}\n" if agent_reason else "\n"
                msg = (
                    f"[URGENT] {feed['name']}\n"
                    f"matched: {kw}"
                    f"{why_line}"
                    f"\n{title}\n"
                    f"\n{link}\n"
                    f"\nauto-spawning cron tick for sanity-check + decision."
                )
                telegram_send(msg)
            # Persist to structured alerts log for next cron tick to consume
            if tier == 1 or impacts:
                _append_news_alert({
                    "ts": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                    "tier": tier,
                    "feed": feed["name"],
                    "matched": kw,
                    "title": title,
                    "link": link,
                    "agent_reason": agent_reason,
                    "impacts": impacts,
                })
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
    state["seen_titles"] = seen_titles
    save_state(state)
    return new_alerts


def cmd_start(_args: argparse.Namespace) -> int:
    # Refuse to start if an existing daemon is alive — running 2 daemons in
    # parallel races on state-file reads/writes, causing duplicate alerts.
    # Lesson source: 2026-05-08 ~22:57 UTC saw same Al Jazeera headline fire
    # 2x within 10s; root cause was 2 daemons running since 18:13 because
    # the prior restart-via-bash-heredoc spawned both an orphan and a
    # tracked instance.
    if PID_PATH.exists():
        try:
            existing = int(PID_PATH.read_text().strip())
            os.kill(existing, 0)  # raises if not alive
            print(f"[watcher] refusing to start: pid={existing} is already running. "
                  f"Stop with `news_watcher.py stop` first.", flush=True)
            return 2
        except (ValueError, OSError):
            pass  # PID file stale or process dead; ok to claim
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
