"""Polyclaude news watcher.

Long-running daemon: polls a configurable list of RSS feeds every N seconds,
matches entry titles + summaries against tiered keyword lists, and:

- Tier 1 (broad recall, including research topics) → classify against current
  exposure; persist research leads without claiming an investment alert.
- Tier 2 → filter and persist qualifying internal detections.
- Material/critical current-exposure impacts and explicit uncertainty/safety
  cases qualify for review. Track queue acknowledgment separately from review.

The watcher is detection-only: RSS matches never send Telegram messages.

Config: `news_watcher_config.json` colocated with this script (in repo, editable).
State (seen entry ids, last alerts): file pointed to by POLYCLAUDE_NEWS_STATE.

Subcommands: start | status | stop | once  (the last polls one cycle and exits,
useful for testing).
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import json
import math
import os
import re as _re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import feedparser
import httpx
from bs4 import BeautifulSoup

import _paths as _secrets
from agent_runtime import run_agent

_secrets.install_scrubbing_excepthook()

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent

CONFIG_PATH = _SCRIPT_DIR / "news_watcher_config.json"
STATE_PATH = _secrets.path("POLYCLAUDE_NEWS_STATE")
PID_PATH = _secrets.path("POLYCLAUDE_NEWS_PID")
LOG_PATH = _REPO_ROOT / "logs" / "news_watcher.log"
ALERTS_LOG_PATH = _REPO_ROOT / "notes" / "news_alerts.jsonl"
CRON_SCRIPT = _SCRIPT_DIR / "daily_checkin.sh"
TITLE_DEDUP_SECONDS = 72 * 60 * 60


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
    # Keep exact normalized titles for three days. Some RSS publishers refresh
    # the GUID on an unchanged article once per day; the former 24h boundary
    # let one CoinTelegraph story fire on three consecutive checks. Three days
    # outlasts normal feed residence without suppressing a genuinely reused
    # headline indefinitely.
    now = time.time()
    cutoff = now - TITLE_DEDUP_SECONDS
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


def fire_cron_tick(reason: str = "") -> dict:
    """Request a review and report only the dispatch boundary actually proved.

    A child PID proves a driver exists, not that a prompt was queued or read.
    The driver writes its own acknowledgment after checking the lock/queue.
    Keep an unconfirmed receipt for the next normal polling cycle to inspect;
    never kill a possibly active fallback just because acknowledgment is slow.
    """
    receipt_path = None
    try:
        directory = _REPO_ROOT / "logs" / "cron"
        directory.mkdir(parents=True, exist_ok=True)
        fd, filename = tempfile.mkstemp(prefix="news_dispatch_", suffix=".json", dir=directory)
        os.close(fd)
        receipt_path = Path(filename)
        env = os.environ.copy()
        env["POLYCLAUDE_DISPATCH_RECEIPT"] = str(receipt_path)
        child = subprocess.Popen(
            ["/bin/bash", str(CRON_SCRIPT), reason],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            receipt = _dispatch_receipt(receipt_path)
            if receipt is not None:
                return receipt
            if child.poll() is not None:
                break
            time.sleep(0.1)
        return {"status": "unconfirmed", "why": "no_dispatch_acknowledgment",
                "receipt_path": str(receipt_path.relative_to(_REPO_ROOT))}
    except Exception as e:
        result = {"status": "failed", "why": "driver_request_failed",
                  "detail": _secrets.scrub(str(e))[:160]}
        if receipt_path is not None:
            result["receipt_path"] = str(receipt_path.relative_to(_REPO_ROOT))
        return result


def _dispatch_receipt(path: Path) -> dict | None:
    """Read only this request's local dispatch acknowledgment, never an inbox."""
    try:
        record = json.loads(path.read_text())
        if not isinstance(record, dict) or record.get("status") not in {
                "queued", "deferred", "failed", "fallback_starting"}:
            return None
        return {**{k: record.get(k) for k in ("status", "why", "tick_id", "returncode")},
                "receipt_path": str(path.relative_to(_REPO_ROOT))}
    except (OSError, ValueError):
        return None


def _dispatch_pending_reviews(state: dict, review_alerts: list[dict], now: float) -> None:
    """Retain qualified alert IDs until the queue acknowledges their dispatch.

    Journal recency is not proof that these alerts were read. An unconfirmed
    request is checked for a late receipt, not blindly repeated. Critical and
    infrastructure-safety leads bypass the ordinary 90-minute request cooldown.
    """
    pending = {r["alert_id"]: r for r in state.get("pending_review_alerts", [])
               if isinstance(r, dict) and isinstance(r.get("alert_id"), str)}
    pending.update({r["alert_id"]: r for r in review_alerts})
    state["pending_review_alerts"] = list(pending.values())
    if not pending:
        return
    previous = state.get("last_review_dispatch", {})
    dispatched_ids = list(pending)
    newly_critical = any(r.get("critical") and key not in previous.get("alert_ids", [])
                         for key, r in pending.items())
    if previous.get("status") == "unconfirmed" and not newly_critical:
        dispatched_ids = previous.get("alert_ids", [])
        path = (_REPO_ROOT / previous.get("receipt_path", "")).resolve()
        directory = (_REPO_ROOT / "logs" / "cron").resolve()
        result = (_dispatch_receipt(path) if path.parent == directory
                  and path.name.startswith("news_dispatch_") else None)
        if result is None:
            result = {**previous, "status": "unconfirmed"}
        elif result["status"] in {"queued", "fallback_starting"}:
            for alert_id in dispatched_ids:
                pending.pop(alert_id, None)
            state["last_cron_trigger"] = now
    else:
        last = max(state.get("last_cron_trigger", 0), state.get("last_cron_request", 0))
        critical = any(r.get("critical") for r in pending.values())
        if not critical and now - last < 5400:
            result = {"status": "deferred", "why": "review_request_cooldown"}
        else:
            save_state(state)  # Pending IDs survive a driver/daemon interruption.
            reason = (
                "NEWS REVIEW REQUEST: inspect notes/news_alerts.jsonl for alert IDs "
                + ",".join(dispatched_ids[:50])
                + (f" (plus {len(dispatched_ids)-50} IDs in logs/news_dispatch.jsonl)."
                   if len(dispatched_ids) > 50 else ".")
                + " Read related alerts even if they predate the latest journal entry. "
                "Relevance is provisional; verify sources, current exposure and any action. "
                "A queued review is not a completed review."
            )
            state["last_cron_request"] = now
            result = fire_cron_tick(reason)
            if result.get("status") in {"queued", "fallback_starting"}:
                state["last_cron_trigger"] = now
                pending.clear()
    record = {**result, "alert_ids": dispatched_ids}
    if record != previous:
        try:
            path = _REPO_ROOT / "logs" / "news_dispatch.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a") as stream:
                stream.write(json.dumps({"ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                                         **record}) + "\n")
        except OSError as exc:
            print(f"[watcher] dispatch-log append failed: {_secrets.scrub(str(exc))[:120]}", flush=True)
        print(f"[watcher] review dispatch {record.get('status')}: {record.get('why')}; "
              f"{len(dispatched_ids)} alert(s); completion not asserted", flush=True)
    state["last_review_dispatch"] = record
    state["pending_review_alerts"] = list(pending.values())


# --- current exposure and scoped relevance filter -------------------------

# In-process cache of formatted positions; refreshed every 5 min so the
# agent always sees roughly-current book without hammering data-api.
_POSITIONS_CACHE: dict = {
    "text": None, "ts": 0.0, "polymarket_available": False,
    "exposures": [], "ostium_available": False, "ostium_open_trades": 0,
}
_POSITIONS_CACHE_TTL_SECONDS = 300
_CONDITION_ID_RE = _re.compile(r"^0x[0-9a-fA-F]{64}$")


def _positions_summary_blocking() -> str:
    """Fetch + format current positions for inclusion in agent prompts.

    Cached for 5 min in-process. Polymarket inventory failures mark the
    cache unavailable so Tier-2 alerts bypass suppression.
    """
    now = time.time()
    if _POSITIONS_CACHE["text"] and now - _POSITIONS_CACHE["ts"] < _POSITIONS_CACHE_TTL_SECONDS:
        return _POSITIONS_CACHE["text"]

    lines: list[str] = ["Polymarket sleeve (held positions):"]
    available = True
    exposures: list[dict] = []
    _POSITIONS_CACHE["exposures"] = exposures
    try:
        addr = json.loads(_secrets.path("POLYCLAUDE_WALLET").read_text())["address"]
        r = httpx.get(
            "https://data-api.polymarket.com/positions",
            params={"user": addr.lower(), "limit": "50", "sizeThreshold": "0"},
            timeout=10,
        )
        r.raise_for_status()
        positions = r.json()
        if not isinstance(positions, list) or len(positions) >= 50:
            raise RuntimeError("positions response unavailable or potentially incomplete")
        for p in positions:
            if p.get("redeemable") is True:
                continue
            cur = float(p.get("curPrice") or 0)
            cost = float(p.get("initialValue") or 0)
            size = float(p.get("size") or 0)
            cid = str(p.get("conditionId") or "")
            if not math.isfinite(size) or size < 0:
                raise RuntimeError("held position has invalid quantity")
            if size > 0:
                if not _CONDITION_ID_RE.fullmatch(cid):
                    available = False
                    lines.append("  (held position omitted: missing valid condition ID)")
                    continue
                exposures.append({"condition_id": cid.lower(), "kind": "held",
                                  "title": str(p.get("title") or "")[:120]})
                lines.append(f"- {p.get('outcome', 'position')} {cur:.3f} (${cost:.2f}) "
                             f"— {str(p.get('title') or '')[:70]}; condition={cid}")
    except Exception as e:
        available = False
        lines.append(f"  (positions read failed: {_secrets.scrub(str(e))[:120]})")

    try:
        lines.append("\n" + _pending_buy_summary_blocking())
    except Exception as e:
        available = False
        lines.append(f"  (pending BUY inventory unavailable: {_secrets.scrub(str(e))[:120]})")

    # Crypto/Ostium must be live too. A hard-coded May-era XAU long survived
    # here after the trade closed and caused an Aug-27 alert to fabricate a
    # portfolio impact. Unknown state is explicitly non-actionable: absence of
    # a successful read is not permission to resurrect a remembered position.
    _POSITIONS_CACHE["exposures"] = exposures
    _POSITIONS_CACHE["ostium_available"] = False
    _POSITIONS_CACHE["ostium_open_trades"] = 0
    lines.append("\n" + _ostium_positions_summary_blocking())

    text = "\n".join(lines)
    _POSITIONS_CACHE["text"] = text
    _POSITIONS_CACHE["ts"] = now
    _POSITIONS_CACHE["polymarket_available"] = available
    return text


def _pending_buy_summary_blocking() -> str:
    """Use the vetted authenticated reader; never reconcile or mutate orders.

    The caller's five-minute cache covers both successful and failed reads.
    Remaining BUY risk is additional to held shares, not a second held position.
    """
    from polyclaude_enter import _fetch_open_buy_commitments

    lines = ["Polymarket pending BUY orders (additional unfilled exposure; "
             "news may require cancellation before a fill):"]
    seen: dict[str, dict] = {}
    for row in _fetch_open_buy_commitments():
        side = str(row.get("side") or "BUY").upper()
        if side == "SELL":
            continue
        if side != "BUY":
            raise RuntimeError("pending order has unknown side")
        order_id = str(row.get("orderId") or "")
        if not order_id or not row.get("asset") or not row.get("conditionId"):
            raise RuntimeError("pending BUY omitted order/token/market identity")
        if order_id in seen:
            if seen[order_id] != row:
                raise RuntimeError("pending BUY has inconsistent duplicate order identity")
            continue
        seen[order_id] = row
        remaining = float(row["remainingShares"])
        price = float(row["price"])
        risk = float(row["risk"])
        if (not all(math.isfinite(v) for v in (remaining, price, risk))
                or remaining <= 0 or not 0 < price < 1
                or abs(risk - remaining * price) > 1e-8):
            raise RuntimeError("pending BUY remaining quantity/commitment is invalid")
        cid = str(row["conditionId"])
        if not _CONDITION_ID_RE.fullmatch(cid):
            raise RuntimeError("pending BUY has invalid condition ID")
        _POSITIONS_CACHE.setdefault("exposures", []).append({
            "condition_id": cid.lower(), "kind": "pending_buy",
            "title": str(row.get("question") or "")[:120],
        })
        question = str(row.get("question") or "")
        slug = str(row.get("slug") or "")
        if not question or not slug:
            raise RuntimeError("pending BUY lacks title/slug")
        lines.append(
            f"- BUY remaining={remaining!r} shares @ {price!r}; "
            f"capped commitment=${risk!r} — {question}; slug={slug}; "
            f"order={order_id}; asset={row['asset']}; condition={row['conditionId']}"
        )
    if not seen:
        lines.append("- No pending BUY orders.")
    return "\n".join(lines)


def _ostium_positions_summary_blocking() -> str:
    """Return live Ostium positions, or a fail-closed instruction on read error."""
    try:
        result = subprocess.run(
            [sys.executable, str(_SCRIPT_DIR / "ostium_client.py"), "status"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            raise RuntimeError(f"status exit {result.returncode}")
        output = result.stdout or ""
        count_line = next(
            line.strip() for line in output.splitlines()
            if line.strip().lower().startswith("open trades:")
        )
        count = int(count_line.split(":", 1)[1].strip())
        if count < 0:
            raise RuntimeError("negative open-trade count")
        _POSITIONS_CACHE["ostium_available"] = True
        _POSITIONS_CACHE["ostium_open_trades"] = count
        if count == 0:
            return "Crypto/Ostium sleeve: no open trades."
        trade_lines = [
            line.strip()[:500]
            for line in output.splitlines()
            if line.startswith("  ") and line.strip()
        ]
        if len(trade_lines) < count:
            raise RuntimeError("status omitted one or more open-trade details")
        return "Crypto/Ostium sleeve (live):\n" + "\n".join(
            f"- {line}" for line in trade_lines[:count]
        )
    except Exception as exc:
        _POSITIONS_CACHE["ostium_available"] = False
        _POSITIONS_CACHE["ostium_open_trades"] = 0
        detail = _secrets.scrub(str(exc))[:120]
        return (
            "Crypto/Ostium sleeve: live status unavailable "
            f"({detail}); do not infer or score any crypto position."
        )


def _fetch_article_body(url: str, max_chars: int = 4000) -> str | None:
    """Fetch and extract main article text. Returns None on failure (fail-OPEN: caller
    proceeds with summary-only when body unavailable).

    Lesson 2026-05-09: 2 false directional miscalls in 24h came from summary-only
    framing (Pentagon UFO read bullish was negative; Trump Project-Freedom read
    imminent was Iran-rejecting). Body has counter-signal headlines drop.
    """
    if not url:
        return None
    try:
        r = httpx.get(url, timeout=15.0, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0 (polyclaude news_watcher)"})
        if r.status_code != 200 or not r.text:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "aside", "form"]):
            tag.decompose()
        article = soup.find("article") or soup.find("main") or soup.body
        if not article:
            return None
        paragraphs = [p.get_text(" ", strip=True) for p in article.find_all("p")]
        text = " ".join(p for p in paragraphs if len(p) > 40)
        text = text[:max_chars]
        return text or None
    except Exception:
        return None


def _agent_filter_tier2(feed_name: str, kw: str, title: str, summary: str, url: str = "") -> tuple[bool, str, list[dict]]:
    """Classify news for internal retention and exact-ID exposure impact.

    Returns (should_retain_internally, one_line_reason, per_position_impacts).
    Each impact is {"position": str, "level": NONE|MINOR|MATERIAL|CRITICAL, "reason": str}.
    On agent error/timeout/unparseable output, returns (True, "agent unavailable: ...", [])
    — fail-open so the next check-in can review the raw alert rather than silently
    dropping it. The worker's literal SEND verdict means retain for internal review.
    """
    pos = _positions_summary_blocking()
    if not _POSITIONS_CACHE.get("polymarket_available", False):
        print(f"[watcher] WARN positions block unavailable for agent filter", flush=True)
        return (True, "Polymarket held/pending inventory unavailable; alert passed through", [])
    body = (summary or "")[:600].replace("\n", " ").strip()
    prompt = (
        "You filter news for polyclaude (autonomous trading project) AND assess "
        "per-position impact. Held positions and pending BUY exposure:\n\n"
        f"{pos}\n\n"
        f"News article (matched keyword \"{kw}\", source {feed_name}):\n"
        f"Title: {title}\n"
        f"Summary: {body}\n\n"
        "FIRST LINE: SEND or SUPPRESS verdict.\n"
        "  - SEND = retain this article for internal check-in review because it may matter to a decision (state change, named officials taking action, hard numbers, named-entity events).\n"
        "  - SUPPRESS = recycled noise (rephrasing of existing facts, opinion pieces, generic topic mentions).\n\n"
        "FOLLOWING LINES (only if SEND, only for IMPACTED positions): one line per "
        "materially-affected position, in this exact format:\n"
        "  IMPACT: <exact 0x condition ID>: <MINOR|MATERIAL|CRITICAL>: <one-line causal reason>\n"
        "  - MINOR = thesis still holds; tiny mark-to-market drift expected.\n"
        "  - MATERIAL = thesis pressure or confirmation; consider rebalance/scale on next tick.\n"
        "  - CRITICAL = thesis-invalidating or thesis-resolving; urgent re-evaluation.\n"
        "Use only the exact condition ID printed for a live held position or pending BUY. "
        "Never invent a key from a title. For a live Ostium trade only, use the key "
        "ostium if the inventory explicitly reports open trades. Skip any position "
        "without a direct causal channel.\n\n"
        "Pending BUY orders can fill until canceled. Treat news affecting their "
        "market as relevant even with no held shares; assess whether it calls "
        "for cancellation or re-evaluation. Do not add their unfilled quantity "
        "to held shares a second time.\n\n"
        "Respond:\n"
        "LINE 1: SEND: <why> OR SUPPRESS: <why>\n"
        "LINE 2+: IMPACT lines (only if SEND and positions are actually impacted)"
    )

    try:
        r = run_agent(prompt, profile="fast", effort="low", timeout=60)
        if r.returncode != 0:
            return (True, f"agent unavailable: exit {r.returncode}", [])
        out = (r.stdout or "").strip()
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        first_line = lines[0] if lines else ""
    except Exception as e:
        return (True, f"agent unavailable: {_secrets.scrub(str(e))[:120]}", [])

    impacts: list[dict] = []
    unsupported = False
    allowed = {x["condition_id"] for x in _POSITIONS_CACHE.get("exposures", [])}
    if (_POSITIONS_CACHE.get("ostium_available") and
            _POSITIONS_CACHE.get("ostium_open_trades", 0) > 0):
        allowed.add("ostium")
    for line in lines[1:]:
        # IMPACT: <key>: <LEVEL>: <reason>
        if not line.upper().startswith("IMPACT:"):
            continue
        try:
            _, rest = line.split(":", 1)
            parts = [p.strip() for p in rest.split(":", 2)]
            if len(parts) < 3:
                unsupported = True
                continue
            key, level, reason = parts[0].lower(), parts[1].upper(), parts[2]
            if level not in ("MINOR", "MATERIAL", "CRITICAL", "NONE"):
                unsupported = True
                continue
            if level == "NONE":
                continue
            if key.lower() not in allowed:
                unsupported = True
                continue
            impacts.append({"position": key, "level": level, "reason": reason[:240]})
        except Exception:
            continue

    upper = first_line.upper()
    retain_decision = None
    send_reason = ""
    if upper.startswith("SEND"):
        retain_decision = True
        send_reason = first_line[4:].lstrip(": ").strip() or "(no reason)"
    elif upper.startswith("SUPPRESS"):
        retain_decision = False
        send_reason = first_line[8:].lstrip(": ").strip() or "(no reason)"
    else:
        retain_decision = True
        send_reason = f"agent unparseable: {first_line[:120]}"

    if retain_decision and url and any(i["level"] == "CRITICAL" for i in impacts):
        body = _fetch_article_body(url)
        body_len = len(body) if body else 0
        if body and body_len > 200:
            before_levels = [i["level"] for i in impacts]
            impacts = _revalidate_critical_impacts(impacts, title, body, pos)
            after_levels = [i["level"] for i in impacts]
            print(f"[watcher] tier2-CRITICAL re-val body={body_len}ch before={before_levels} after={after_levels} url={url[:80]}",
                  flush=True)
        else:
            # body fetch failed or too thin (paywall, video page, JS-rendered) — preserve CRITICAL (fail-OPEN)
            print(f"[watcher] tier2-CRITICAL re-val SKIPPED body_len={body_len} (kept CRITICAL) url={url[:80]}",
                  flush=True)

    if impacts and not retain_decision:
        unsupported = True
    if unsupported:
        retain_decision = True
        send_reason = f"{send_reason}; UNKNOWN relevance: unsupported impact key discarded"
    return (retain_decision, send_reason, impacts)


def _revalidate_critical_impacts(impacts: list[dict], title: str,
                                  body: str, positions_text: str) -> list[dict]:
    """Second-pass validation of CRITICAL tags using full article body.

    Returns impacts list with CRITICAL levels possibly downgraded. MINOR/MATERIAL
    impacts pass through unchanged (first pass is sufficient for non-urgent).
    On agent error: returns original impacts unchanged (fail-OPEN).
    """
    critical = [i for i in impacts if i["level"] == "CRITICAL"]
    if not critical:
        return impacts
    claims = "\n".join(
        f"- {i['position']}: CRITICAL — {i['reason']}" for i in critical
    )
    prompt = (
        "You re-validate per-position CRITICAL tags against the full article body "
        "(first pass used only the RSS summary, which has caused directional miscalls). "
        f"Open positions:\n\n{positions_text}\n\n"
        f"Article title: {title}\n\n"
        f"Article body (excerpt):\n{body[:3500]}\n\n"
        f"First-pass CRITICAL claims to validate:\n{claims}\n\n"
        "For each claim, output one line:\n"
        "  VERDICT: <position-key>: <CONFIRM|MATERIAL|MINOR|NONE>: <one-line reason>\n"
        "  - CONFIRM = body confirms CRITICAL (thesis-invalidating/resolving). Keep CRITICAL.\n"
        "  - MATERIAL = body shows real pressure but not thesis-invalidating. Downgrade.\n"
        "  - MINOR = body shows headline overstated; minor drift only. Downgrade.\n"
        "  - NONE = body contradicts the claim entirely (counter-signal). Remove.\n"
        "Examples of counter-signals: official rejects the framing; story is about "
        "the OPPOSITE side acting; the named action was paused/canceled inside body; "
        "the article is opinion/speculation citing unnamed sources only.\n"
        "Use the EXACT position-key from the claims above."
    )
    try:
        r = run_agent(prompt, profile="fast", effort="low", timeout=60)
        if r.returncode != 0:
            return impacts
        out = (r.stdout or "").strip()
    except Exception:
        return impacts

    verdicts: dict[str, tuple[str, str]] = {}
    for line in out.splitlines():
        line = line.strip()
        if not line.upper().startswith("VERDICT:"):
            continue
        try:
            _, rest = line.split(":", 1)
            parts = [p.strip() for p in rest.split(":", 2)]
            if len(parts) < 3:
                continue
            key, level, reason = parts[0], parts[1].upper(), parts[2]
            if level in ("CONFIRM", "MATERIAL", "MINOR", "NONE"):
                verdicts[key] = (level, reason[:240])
        except Exception:
            continue

    revised: list[dict] = []
    for i in impacts:
        if i["level"] != "CRITICAL":
            revised.append(i)
            continue
        v = verdicts.get(i["position"])
        if not v:
            revised.append(i)  # no verdict — keep original (fail-open)
            continue
        level, reason = v
        if level == "NONE":
            continue  # drop
        if level == "CONFIRM":
            i = dict(i)
            i["reason"] = f"{i['reason']} | body-confirmed: {reason}"
            revised.append(i)
        else:
            revised.append({
                "position": i["position"],
                "level": level,
                "reason": f"body-downgrade from CRITICAL: {reason}",
            })
    return revised


def entry_id(entry) -> str:
    """Stable id for an RSS entry — prefer guid/link, fall back to title hash."""
    base = entry.get("id") or entry.get("guid") or entry.get("link") or entry.get("title", "")
    return hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest()


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


def _entry_published_timestamp(entry) -> float | None:
    """Return an RSS entry's publication/update time, or None if unavailable.

    Feedparser's parsed time fields are UTC tuples. A malformed publication
    date falls through to a valid update date rather than hiding the entry.
    """
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value is None:
            continue
        try:
            if isinstance(value, dt.datetime):
                parsed = value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)
                return parsed.timestamp()
            parts = tuple(value)
            if len(parts) < 6:
                continue
            return float(calendar.timegm(parts))
        except (TypeError, ValueError, OverflowError, OSError):
            continue
    return None


def _newest_entries_first(entries: list, limit: int | None = None) -> list:
    """Order dated RSS entries newest-first before applying the feed cap.

    Equal timestamps retain source order. Entries without a usable published
    or updated date follow all dated entries and retain their source order.
    This lets relevance-ordered feeds expose recent tail items to the cap.
    """
    dated: list[tuple[float, int, object]] = []
    undated: list[tuple[int, object]] = []
    for index, entry in enumerate(entries):
        timestamp = _entry_published_timestamp(entry)
        if timestamp is None:
            undated.append((index, entry))
        else:
            dated.append((timestamp, index, entry))
    dated.sort(key=lambda item: (-item[0], item[1]))
    ordered = [entry for _, _, entry in dated]
    ordered.extend(entry for _, entry in undated)
    return ordered if limit is None else ordered[:limit]


def poll_once(config: dict, state: dict) -> int:
    """Run one detection cycle. Return the number of internally retained alerts."""
    seen = set(state.get("seen_ids", []))
    seen_titles: dict[str, float] = state.get("seen_titles", {})  # title-hash → first-seen-ts
    last_alerts = state.get("last_alerts", {})
    cooldown = config.get("alert_cooldown_seconds", 1800)
    max_entries = config.get("max_entries_per_feed", 30)
    tier1 = config.get("tier1_keywords", [])
    tier2 = config.get("tier2_keywords", [])
    now = time.time()

    new_alerts = 0
    review_alerts: list[dict] = []

    for feed in config["feeds"]:
        try:
            d = feedparser.parse(feed["url"])
        except Exception as e:
            print(f"[watcher] feed error {feed['name']}: {e}", flush=True)
            continue
        for entry in _newest_entries_first(d.entries or [])[:max_entries]:
            eid = entry_id(entry)
            if eid in seen:
                continue
            seen.add(eid)
            title = entry.get("title", "")
            # Title-hash dedup across feeds: same syndicated story
            # republished with new GUIDs across N feeds was firing N alerts.
            # Normalize title and check the seen_titles dict (72h window).
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

            # Per-keyword detection cooldown to avoid repeating a hot story.
            cooldown_key = f"t{tier}:{kw}"
            last = last_alerts.get(cooldown_key, 0)
            routine_cooldown = now - last < cooldown
            # Cooldown records detection, independent of any outbound channel.
            last_alerts[cooldown_key] = now
            # Both tiers use the same fast exposure classifier. Tier 1 remains
            # in the research log regardless of its SEND/SUPPRESS verdict.
            agent_reason = None
            impacts: list[dict] = []
            retain, agent_reason, impacts = _agent_filter_tier2(
                feed["name"], kw, title, summary, link
            )
            if tier == 2 and not retain:
                print(f"[watcher] suppressed tier2 kw={kw!r} feed={feed['name']} "
                      f"reason={agent_reason[:120]!r} title={title[:80]!r}", flush=True)
                continue

            unknown = ("unavailable" in (agent_reason or "").lower()
                       or "unparseable" in (agent_reason or "").lower()
                       or "unknown relevance" in (agent_reason or "").lower()
                       or not _POSITIONS_CACHE.get("polymarket_available", False)
                       or not _POSITIONS_CACHE.get("ostium_available", False))
            safety_terms = (
                "hack", "exploit", "drained", "rug", "depeg", "depegged",
                "loses peg", "breaks peg", "insolvent", "bankrupt", "sequencer",
                "chain halt", "withdrawal halted", "exchange frozen", "shutdown",
                "polymarket halted", "polymarket banned", "polymarket frozen",
            )
            safety_headline = tier == 1 and any(
                term in kw.lower() for term in safety_terms
            )
            material = any(i.get("level") in ("MATERIAL", "CRITICAL") for i in impacts)
            minor = any(i.get("level") == "MINOR" for i in impacts)
            if material:
                relevance = "portfolio_material_critical"
            elif safety_headline:
                relevance = "safety_unknown"
            elif unknown:
                relevance = "unknown"
            elif minor:
                relevance = "minor"
            else:
                relevance = "research_only"
            review_required = relevance in (
                "portfolio_material_critical", "safety_unknown", "unknown"
            )
            # A routine article must not hide a new critical development about
            # the same entity. Apply the headline cooldown after classification.
            if routine_cooldown and not review_required:
                continue

            # Persist retained detections for the next check-in to review. A
            # Tier-2 SEND verdict means internal retention, not a message.
            # Unknown impacts stay attached as empty rather than dropping the
            # alert; the check-in decides what matters.
            alert_record = {
                "alert_id": eid,
                "ts": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "tier": tier,
                "feed": feed["name"],
                "matched": kw,
                "title": title,
                "link": link,
                "agent_reason": agent_reason,
                "impacts": impacts,
                "relevance": relevance,
                "review_required": review_required,
            }
            _append_news_alert(alert_record)
            print(f"[watcher] alert tier{tier} kw={kw!r} feed={feed['name']} title={title[:80]!r}", flush=True)
            new_alerts += 1
            if review_required:
                review_alerts.append({
                    "alert_id": eid, "title": title[:120],
                    "relevance": relevance,
                    "critical": (any(i.get("level") == "CRITICAL" for i in impacts)
                                 or relevance == "safety_unknown"),
                })

    # Existing polls retry qualified pending IDs even without a new headline.
    _dispatch_pending_reviews(state, review_alerts, now)

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
            # Identity check (2026-07-16 audit): PID reuse after a reboot can
            # point the persistent PID file at an unrelated live process,
            # which would block the @reboot start — news watching's single
            # scheduled restart opportunity — indefinitely.
            cmdline = open(f"/proc/{existing}/cmdline", "rb").read()
            if b"news_watcher" not in cmdline:
                print(f"[watcher] PID file pid={existing} is NOT a news_watcher "
                      f"(PID reuse) — claiming.", flush=True)
                raise OSError("pid reuse")
            print(f"[watcher] refusing to start: pid={existing} is already running. "
                  f"Stop with `news_watcher.py stop` first.", flush=True)
            return 2
        except (ValueError, OSError):
            pass  # PID file stale or process dead; ok to claim
    PID_PATH.write_text(str(os.getpid()))
    # Redirect stdout/stderr to LOG_PATH so daemon output persists even when
    # invoked from ephemeral shells (background tasks, tmux session-exit, etc.).
    # Lesson source: 2026-05-21 14:00 UTC cron tick — body-fetch CRITICAL re-val
    # was correctly firing (BBC Iran-Hormuz article downgraded CRITICAL→MATERIAL)
    # but the log lines were going to a stale temporary agent-task output file
    # from the bash background task that invoked `news_watcher.py start` two
    # days earlier. Future audits couldn't find re-val outcomes in
    # logs/news_watcher.log because the daemon's stdout had never been pointed
    # at LOG_PATH.
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _log_fp = open(LOG_PATH, "a", buffering=1)  # line-buffered append
    os.dup2(_log_fp.fileno(), sys.stdout.fileno())
    os.dup2(_log_fp.fileno(), sys.stderr.fileno())
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
