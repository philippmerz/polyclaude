#!/usr/bin/env python3
"""Watchlist entry-trigger monitor.

Reads notes/watchlist_triggers.json — structured entry-trigger config seeded
from the long-term watchlist. For each trigger, pulls current price and flags
ENTRY_TRIGGER_HIT when current <= entry_max (downside dip entries) or
current >= entry_min (breakouts, when set).

Wired into daily_checkin.sh step 3 alongside check_marginal_apy.py so every
cron tick auto-surfaces actionable watchlist alerts. Without this, the
discovery → vetting → tracking pipeline (world_state_digest -> longterm_check
-> longterm_watchlist) had no automated alerting layer.

Sources:
- Crypto: CoinGecko free public API (no key, ~50 req/min limit, plenty for ~10 names)
- Equities: yfinance (Yahoo public quote feed)

Usage:
    python scripts/watchlist_monitor.py             # check all
    python scripts/watchlist_monitor.py --json      # JSON output (for downstream)
    python scripts/watchlist_monitor.py --hits-only # only print triggered

Lesson source: 2026-05-08 longterm_watchlist.md introduction; 17 candidates
analyzed, all WATCH/FOLLOW-UP. Without programmatic monitoring, entry triggers
get missed. Bounded ~100 LOC closes the alerting loop.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "notes" / "watchlist_triggers.json"


def fetch_crypto_prices(coingecko_ids: list[str]) -> dict[str, float]:
    """Batch-fetch USD prices from CoinGecko. Returns {id: usd_price}."""
    if not coingecko_ids:
        return {}
    try:
        with httpx.Client(timeout=15.0) as c:
            r = c.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": ",".join(coingecko_ids), "vs_currencies": "usd"},
            )
            r.raise_for_status()
            data = r.json() or {}
            return {k: float(v.get("usd", 0)) for k, v in data.items() if v.get("usd")}
    except Exception as e:
        print(f"WARN: CoinGecko fetch failed: {e}", file=sys.stderr)
        return {}


def fetch_equity_price(symbol: str) -> float | None:
    """Pull last close from yfinance. Returns None on failure."""
    try:
        import yfinance as yf
        t = yf.Ticker(symbol)
        h = t.history(period="1d")
        if len(h) > 0:
            return float(h["Close"].iloc[-1])
    except Exception as e:
        print(f"WARN: yfinance fetch failed for {symbol}: {e}", file=sys.stderr)
    return None


def evaluate(trigger: dict, current: float | None) -> dict:
    """Evaluate one trigger. Returns dict with status, current, trigger info."""
    ticker = trigger.get("ticker", "?")
    entry_max = trigger.get("entry_max")
    entry_min = trigger.get("entry_min")
    rationale = trigger.get("rationale", "")

    if current is None:
        return {"ticker": ticker, "status": "NO_DATA", "current": None,
                "entry_max": entry_max, "entry_min": entry_min,
                "rationale": rationale, "type": trigger.get("type")}

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
    p = argparse.ArgumentParser(description="Long-term watchlist entry-trigger monitor.")
    p.add_argument("--config", default=str(CONFIG_PATH),
                   help="Path to watchlist_triggers.json")
    p.add_argument("--json", action="store_true", help="Output as JSON.")
    p.add_argument("--hits-only", action="store_true",
                   help="Only print TRIGGER_HIT entries (silent if none).")
    args = p.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"ERROR: config not found at {cfg_path}", file=sys.stderr)
        return 2

    cfg = json.loads(cfg_path.read_text())
    triggers = cfg.get("triggers", [])
    if not triggers:
        print("INFO: zero triggers configured", file=sys.stderr)
        return 0

    # Batch crypto prices, individual equity prices
    crypto_ids = [t["coingecko_id"] for t in triggers if t.get("type") == "crypto" and t.get("coingecko_id")]
    crypto_prices = fetch_crypto_prices(crypto_ids)

    results = []
    for t in triggers:
        if t.get("type") == "crypto":
            cid = t.get("coingecko_id")
            price = crypto_prices.get(cid)
        elif t.get("type") in ("equity", "tokenized-equity"):
            sym = t.get("yfinance_symbol", t.get("ticker"))
            price = fetch_equity_price(sym)
        else:
            price = None
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
        print(f"# watchlist_monitor: {len(results)} candidates  ({len(hits)} HIT, {len(no_data)} NO_DATA)")
        print()

    for r in results:
        route_tag = "POLYCLAUDE" if r["route"] == "polyclaude" else "IBKR_SURFACE"
        if r["status"] == "TRIGGER_HIT":
            action = "POLYCLAUDE_BUY" if r["route"] == "polyclaude" else "IBKR_SURFACE_TO_OPERATOR"
            print(f"ENTRY_TRIGGER_HIT [{action}]  {r['ticker']:8s} ({r['type']}, {r['horizon']})  current ${r['current']} {r['currency']} {r['direction']}")
            print(f"                  {r['rationale']}")
        elif r["status"] == "NO_DATA" and not args.hits_only:
            print(f"NO_DATA   [{route_tag}]  {r['ticker']:8s} ({r['type']})  — fetch failed")
        elif not args.hits_only:
            tgt = f"<=${r['entry_max']}" if r['entry_max'] else f">=${r['entry_min']}"
            print(f"WATCH     [{route_tag}]  {r['ticker']:8s} ({r['type']}, {r['horizon']})  current ${r['current']} {r['currency']}  trigger {tgt}")

    return 0 if not hits else 0  # always exit 0; cron consumer parses output


if __name__ == "__main__":
    sys.exit(main())
