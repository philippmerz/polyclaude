#!/usr/bin/env python3
"""Ostium state-diff alerter — surfaces closures/opens between cron ticks.

Lesson source: 2026-05-12 operator asked "did you liquidate the gold position?"
revealing the XAU/USD LONG had auto-closed at Take-Profit but I hadn't
proactively flagged the state change. Cron tick reads ostium_client.py status
but doesn't diff against prior state.

This script:
1. Fetches current Ostium open trades via ostium_client.py status
2. Compares trade IDs against cached state at notes/.ostium_state_cache.json
3. Surfaces:
   - CLOSED: trade IDs present in prior cache but missing now (TP-hit, SL-hit, or manual close)
   - OPENED: new trade IDs not in prior cache
4. Saves current state for next run

Wired into daily_checkin.sh step 1 (state marking) alongside uma_status_check.

Usage:
    python scripts/ostium_state_diff.py
    python scripts/ostium_state_diff.py --json
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = REPO_ROOT / "notes" / ".ostium_state_cache.json"


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text())
    except Exception:
        return {}


def save_cache(c: dict) -> None:
    CACHE_PATH.write_text(json.dumps(c, indent=2))


def fetch_ostium_open_trades() -> list[dict]:
    """Run ostium_client.py status, parse the open-trades JSON lines.

    Each trade in the output is on its own line as `  {<json>}` after `open trades: N`.
    """
    try:
        r = subprocess.run(
            [".venv/bin/python", "scripts/ostium_client.py", "status"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        return []
    if r.returncode != 0:
        return []

    trades = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        # Trade lines may be truncated at 300 chars per ostium_client.py format
        # so JSON may be invalid. Try strict, fall back to extract trade_id+isBuy.
        try:
            trades.append(json.loads(line))
        except Exception:
            # Extract minimum fields via regex
            tid = re.search(r'"tradeID":\s*"([^"]+)"', line)
            collateral = re.search(r'"collateral":\s*"([^"]+)"', line)
            open_price = re.search(r'"openPrice":\s*"([^"]+)"', line)
            is_buy = re.search(r'"isBuy":\s*(true|false)', line)
            tp = re.search(r'"takeProfitPrice":\s*"([^"]+)"', line)
            sl = re.search(r'"stopLossPrice":\s*"([^"]+)"', line)
            if tid:
                trades.append({
                    "tradeID": tid.group(1),
                    "collateral": collateral.group(1) if collateral else None,
                    "openPrice": open_price.group(1) if open_price else None,
                    "isBuy": is_buy.group(1) == "true" if is_buy else None,
                    "takeProfitPrice": tp.group(1) if tp else None,
                    "stopLossPrice": sl.group(1) if sl else None,
                })
    return trades


def fetch_close_records_since(prior_checked_at: str | None) -> list[dict]:
    """Authoritative close rows from the Ostium subgraph (orderAction, price,
    profit%, amountSentToTrader) executed since the prior tick.

    Lesson source DEC-0026 (2026-06-10 restatement): a close booked from this
    script's count-diff plus an ASSUMED direction was a StopLoss recorded as a
    TakeProfit — sign error −$1.95 vs +$1.96 sat in the books 3+ weeks. No perp
    P&L gets written without these rows."""
    try:
        import asyncio
        from ostium_python_sdk import NetworkConfig, SubgraphClient
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import _paths as _secrets
        addr = json.loads(_secrets.path("POLYCLAUDE_WALLET_CRYPTO").read_text())["address"]
        sg = SubgraphClient(url=NetworkConfig.mainnet().graph_url)
        hist = asyncio.run(sg.get_recent_history(addr, last_n_orders=10))
    except Exception as e:
        return [{"error": f"subgraph unavailable ({e}) — DO NOT book P&L until the "
                          f"order row (orderAction/profitPercent/amountSentToTrader) is fetched"}]

    cutoff = 0
    if prior_checked_at:
        try:
            cutoff = int(datetime.datetime.fromisoformat(
                prior_checked_at.replace("Z", "+00:00")).timestamp())
        except Exception:
            cutoff = 0
    rows = []
    for h in hist:
        if h.get("orderAction") in ("Open",):
            continue
        ts = int(h.get("executedAt") or 0)
        if ts <= cutoff:
            continue
        pair = h.get("pair") or {}
        rows.append({
            "pair": f"{pair.get('from','?')}/{pair.get('to','?')}",
            "orderAction": h.get("orderAction"),
            "executedAt": datetime.datetime.utcfromtimestamp(ts).isoformat() + "Z",
            "executionPrice": int(h.get("executionPrice") or h.get("price") or 0) / 1e18,
            "profitPercent": int(h.get("profitPercent") or 0) / 1e6,
            "amountSentToTrader": int(h.get("amountSentToTrader") or 0) / 1e6,
        })
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    cache = load_cache()
    prior_trades = {t["tradeID"]: t for t in cache.get("trades", []) if t.get("tradeID")}

    current_trades = fetch_ostium_open_trades()
    current_ids = {t["tradeID"]: t for t in current_trades if t.get("tradeID")}

    # Diff
    closed_ids = set(prior_trades.keys()) - set(current_ids.keys())
    opened_ids = set(current_ids.keys()) - set(prior_trades.keys())

    alerts = []
    close_records = fetch_close_records_since(cache.get("checked_at")) if closed_ids else []
    for tid in closed_ids:
        t = prior_trades[tid]
        alerts.append({
            "type": "OSTIUM_CLOSED",
            "tradeID": tid,
            "msg": f"trade {tid} no longer open — authoritative order rows below; "
                   f"book P&L from amountSentToTrader, never from an assumed direction",
            "prior": t,
            "close_records": close_records,
        })
    for tid in opened_ids:
        t = current_ids[tid]
        alerts.append({
            "type": "OSTIUM_OPENED",
            "tradeID": tid,
            "msg": f"new trade {tid} opened",
            "current": t,
        })

    # Save current state
    save_cache({
        "trades": current_trades,
        "checked_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
    })

    if args.json:
        print(json.dumps({"alerts": alerts, "current_count": len(current_trades),
                          "prior_count": len(prior_trades)}, indent=2, default=str))
        return 0

    print(f"# ostium_state_diff: {len(current_trades)} open trades (prior: {len(prior_trades)})")
    if not alerts:
        print("  (no change)")
        return 0
    for a in alerts:
        print(f"\n  [{a['type']}] {a['tradeID']}")
        print(f"    {a['msg']}")
        if "prior" in a:
            t = a["prior"]
            side = "LONG" if t.get("isBuy") else "SHORT"
            print(f"    was: {side} entry={t.get('openPrice')} collat={t.get('collateral')} tp={t.get('takeProfitPrice')} sl={t.get('stopLossPrice')}")
        for r in a.get("close_records", []):
            if "error" in r:
                print(f"    !! {r['error']}")
            else:
                print(f"    subgraph: {r['pair']} {r['orderAction']} @ {r['executionPrice']:.2f} "
                      f"on {r['executedAt']}  profit {r['profitPercent']:+.2f}%  "
                      f"sent ${r['amountSentToTrader']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
