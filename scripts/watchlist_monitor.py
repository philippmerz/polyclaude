#!/usr/bin/env python3
"""Project-crypto watchlist review monitor.

Reads notes/watchlist_triggers.json — structured entry-trigger config seeded
from the long-term watchlist. For each trigger, pulls current price and flags
ENTRY_TRIGGER_HIT [PROJECT_REVIEW] when current <= entry_max (dip entries) or
current >= entry_min (breakouts, when set). A trigger is an observation for
project review, never an automatic buy instruction.

Only explicitly routed project crypto triggers are evaluated. Other
instruments remain in historical/config records but are skipped here.

Sources: validated CoinGecko primary with fresh DefiLlama fallback.

Usage:
    python scripts/watchlist_monitor.py             # check project crypto
    python scripts/watchlist_monitor.py --json      # JSON output (for downstream)
    python scripts/watchlist_monitor.py --hits-only # only print triggered

Lesson source: 2026-05-08 longterm_watchlist.md introduction; 17 candidates
analyzed, all WATCH/FOLLOW-UP. Without programmatic monitoring, entry triggers
get missed. Bounded ~100 LOC closes the alerting loop.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

from _crypto_prices import PriceFetchError, fetch_usd_prices

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "notes" / "watchlist_triggers.json"
REVET_CACHE = REPO_ROOT / "notes" / ".watchlist_revet_cache.json"
REVET_TTL_HOURS = 24  # don't re-vet the same ticker within this window
LONGTERM_CHECK = REPO_ROOT / "scripts" / "longterm_check.py"


def auto_revet_ticker(ticker: str, asset_type: str) -> dict:
    """Spawn project-horizon longterm_check for an eligible crypto ticker.

    Returns {"verdict": "ENTER|WATCH|PASS|ERROR", "score": "N/4", "summary": str,
             "fresh": bool, "from_cache": bool}.
    Skips spawn if cached result <REVET_TTL_HOURS old.

    Lesson source: 2026-05-13 → 2026-05-18 the watchlist had 4-of-4 trigger
    fires (CEG/LEU/CCJ/ALB) where the static entry_max was stale and a manual
    fresh longterm_check produced a tighter revised trigger. Codifying so each
    fire auto-surfaces the fresh fundamental verdict — operator gets the
    actionable picture without waiting for me to re-vet manually.
    """
    if asset_type != "crypto":
        return {"verdict": "ERROR", "score": "?/4",
                "summary": "auto-revet is limited to project crypto",
                "fresh": False, "from_cache": False}

    cache = {}
    try:
        if REVET_CACHE.exists():
            cache = json.loads(REVET_CACHE.read_text())
    except Exception:
        cache = {}

    now = time.time()
    entry = cache.get(ticker)
    if entry and now - entry.get("ts", 0) < REVET_TTL_HOURS * 3600:
        return {**entry["result"], "from_cache": True}

    try:
        r = subprocess.run(
            [sys.executable, str(LONGTERM_CHECK), ticker, "crypto", "--no-log"],
            capture_output=True, text=True, timeout=180,
        )
        out = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return {"verdict": "ERROR", "score": "?/4", "summary": "longterm_check timeout",
                "fresh": False, "from_cache": False}
    except Exception as e:
        return {"verdict": "ERROR", "score": "?/4", "summary": f"spawn failed: {e}",
                "fresh": False, "from_cache": False}

    # Parse verdict line: "### Verdict: 3/4 — WATCH" or similar
    score = "?/4"
    verdict = "ERROR"
    m = re.search(r"Verdict[:\s]+(\d+(?:\.\d+)?)/4\s*[—\-–]+\s*(ENTER|WATCH|PASS|FOLLOW-UP|FOLLOWUP)",
                  out, re.IGNORECASE)
    if m:
        score = f"{m.group(1)}/4"
        verdict_raw = m.group(2).upper().replace("FOLLOWUP", "WATCH").replace("FOLLOW-UP", "WATCH")
        verdict = verdict_raw if verdict_raw in ("ENTER", "WATCH", "PASS") else "WATCH"

    # Pull entry trigger one-liner if present
    # Pull the entry-trigger BLOCK (not just the first line). longterm_check often
    # formats triggers as a lead-in + multi-line bullet list; the old single-line
    # regex captured only the lead-in ("...Concrete triggers:") and dropped the
    # actual triggers — the actionable part that flips WATCH->ENTER (2026-06-17 fix).
    summary = ""
    em = re.search(r"#{1,4}\s*Entry trigger\s*\n+(.+?)(?=\n#{1,4}\s|\Z)", out, re.DOTALL)
    if em:
        summary = " ".join(em.group(1).split())[:400]
    elif verdict == "ERROR":
        # Surface first 200 chars of stdout/stderr for debugging
        summary = out.strip()[:200].replace("\n", " ")

    result = {"verdict": verdict, "score": score, "summary": summary, "fresh": True}
    cache[ticker] = {"ts": now, "result": result}
    try:
        REVET_CACHE.write_text(json.dumps(cache, indent=2))
    except Exception:
        pass
    return {**result, "from_cache": False}


def fetch_crypto_prices(coingecko_ids: list[str]) -> dict[str, float]:
    """Batch-fetch validated USD prices. Returns {CoinGecko id: usd_price}."""
    if not coingecko_ids:
        return {}
    try:
        batch = fetch_usd_prices(coingecko_ids, timeout=15)
        for warning in batch.warnings:
            print(f"WARN: crypto prices: {warning}", file=sys.stderr)
        return batch.prices
    except PriceFetchError as e:
        print(f"WARN: crypto price fetch failed: {e}", file=sys.stderr)
        return {}


def is_project_crypto_trigger(trigger: object) -> bool:
    """Return whether a config row is safe for this project-crypto monitor."""
    if not isinstance(trigger, dict):
        return False
    if trigger.get("type") != "crypto" or trigger.get("route") != "polyclaude":
        return False
    if not isinstance(trigger.get("ticker"), str) or not trigger["ticker"].strip():
        return False
    if not isinstance(trigger.get("coingecko_id"), str) or not trigger["coingecko_id"].strip():
        return False
    if trigger.get("currency", "USD") != "USD":
        return False
    for key in ("entry_max", "entry_min"):
        value = trigger.get(key)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
            try:
                finite = math.isfinite(value)
            except (OverflowError, TypeError):
                finite = False
            if not finite:
                return False
    return any(trigger.get(key) is not None for key in ("entry_max", "entry_min"))


def evaluate(trigger: dict, current: float | None) -> dict:
    """Evaluate one trigger. Returns dict with status, current, trigger info."""
    ticker = trigger.get("ticker", "?")
    entry_max = trigger.get("entry_max")
    entry_min = trigger.get("entry_min")
    rationale = trigger.get("rationale", "")

    if current is None:
        return {"ticker": ticker, "status": "NO_DATA", "current": None,
                "entry_max": entry_max, "entry_min": entry_min,
                "direction": "", "rationale": rationale,
                "type": trigger.get("type"),
                "currency": trigger.get("currency", "USD"),
                "route": trigger.get("route", "polyclaude"),
                "horizon": trigger.get("horizon", "?")}

    hit = False
    direction = ""
    if entry_max is not None and current <= entry_max:
        hit = True
        direction = f"<= entry_max ${entry_max}"
    if entry_min is not None and current >= entry_min:
        hit = True
        direction = f">= entry_min ${entry_min}" if not direction else direction + f" / >= entry_min ${entry_min}"

    return {
        "ticker": ticker,
        "status": "TRIGGER_HIT" if hit else "WATCH",
        "current": round(current, 4) if current < 10 else round(current, 2),
        "entry_max": entry_max,
        "entry_min": entry_min,
        "direction": direction,
        "rationale": rationale,
        "type": trigger.get("type"),
        "currency": trigger.get("currency", "USD"),
        "route": trigger.get("route", "polyclaude"),
        "horizon": trigger.get("horizon", "?"),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Project-crypto threshold review monitor.")
    p.add_argument("--config", default=str(CONFIG_PATH),
                   help="Path to watchlist_triggers.json")
    p.add_argument("--json", action="store_true", help="Output as JSON.")
    p.add_argument("--hits-only", action="store_true",
                   help="Only print project-review trigger observations (silent if none).")
    p.add_argument("--auto-revet", action="store_true",
                   help="On a project-review trigger, spawn a fresh project-horizon longterm_check. "
                        "Caches per ticker for 24h to avoid duplicate spawns across cron runs. "
                        "Bounded to --max-revet hits per run.")
    p.add_argument("--max-revet", type=int, default=2,
                   help="Cap on auto-revet spawns per run (default 2, each ~90s).")
    args = p.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"ERROR: config not found at {cfg_path}", file=sys.stderr)
        return 2

    cfg = json.loads(cfg_path.read_text())
    if not isinstance(cfg, dict):
        print("ERROR: config must be a JSON object", file=sys.stderr)
        return 2
    triggers = cfg.get("triggers", [])
    if not isinstance(triggers, list):
        print("ERROR: triggers must be a JSON array", file=sys.stderr)
        return 2
    if not triggers:
        print("INFO: zero triggers configured", file=sys.stderr)
        return 0

    # Unsupported and malformed rows are discarded before any price or vetting work.
    eligible = [t for t in triggers if is_project_crypto_trigger(t)]
    crypto_ids = list(dict.fromkeys(t["coingecko_id"] for t in eligible))
    crypto_prices = fetch_crypto_prices(crypto_ids)

    results = []
    for t in eligible:
        cid = t["coingecko_id"]
        price = crypto_prices.get(cid)
        results.append(evaluate(t, price))

    if args.hits_only:
        results = [r for r in results if r["status"] == "TRIGGER_HIT"]

    if args.json:
        print(json.dumps({"results": results, "version": cfg.get("version", 0)}, indent=2))
        return 0

    # Plain-text output
    if not results:
        if not args.hits_only:
            print("watchlist_monitor: no candidates evaluated")
        return 0

    hits = [r for r in results if r["status"] == "TRIGGER_HIT"]
    no_data = [r for r in results if r["status"] == "NO_DATA"]

    if not args.hits_only:
        print(f"# watchlist_monitor: {len(results)} project candidates  ({len(hits)} HIT, {len(no_data)} NO_DATA)")
        print()

    revet_done = 0
    for r in results:
        if r["status"] == "TRIGGER_HIT":
            print(f"ENTRY_TRIGGER_HIT [PROJECT_REVIEW]  {r['ticker']:8s} ({r['type']}, {r['horizon']})  current ${r['current']} {r['currency']} {r['direction']}")
            print(f"                  {r['rationale']}")
            if args.auto_revet and revet_done < args.max_revet:
                rv = auto_revet_ticker(r['ticker'], r['type'])
                tag = "cache" if rv.get("from_cache") else "fresh"
                print(f"                  AUTO_REVET[{tag}]: {rv['verdict']} ({rv['score']})  {rv['summary'][:200]}")
                revet_done += 1
        elif r["status"] == "NO_DATA" and not args.hits_only:
            print(f"NO_DATA   [PROJECT_REVIEW]  {r['ticker']:8s} ({r['type']})  — fetch failed")
        elif not args.hits_only:
            tgt = f"<=${r['entry_max']}" if r['entry_max'] else f">=${r['entry_min']}"
            print(f"WATCH     [PROJECT_REVIEW]  {r['ticker']:8s} ({r['type']}, {r['horizon']})  current ${r['current']} {r['currency']}  trigger {tgt}")

    return 0 if not hits else 0  # always exit 0; cron consumer parses output


if __name__ == "__main__":
    sys.exit(main())
