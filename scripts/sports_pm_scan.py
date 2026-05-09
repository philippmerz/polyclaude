#!/usr/bin/env python3
"""Sports-market scanner for Polymarket — surfaces short-tail trade candidates.

discover_markets.py covers the bond-like-fade lens (high APY tail). This script
adds a SPORTS-specific filter:
- Resolves within next 36-72h (matches <1y horizon)
- Liquid book (vol24h > $50k, liq > $10k)
- Categorizes by lens:
  - BOND_LIKE_FADE: dominant side > 0.93, decent APY
  - MID_50_50: 0.40 <= yes <= 0.60 (requires fair-value model to enter)
  - PROP_TAIL: extreme tails on prop bets (over/under, spread)
- Future v2: integrate bookie consensus odds via the-odds-api or similar to
  find Polymarket vs bookie-consensus deltas.

Operator directive 2026-05-09 ~17:10 UTC: aggressive engineering campaign
to recoup R-U drawdown via untapped sports + cross-venue alpha.

Usage:
    python scripts/sports_pm_scan.py
    python scripts/sports_pm_scan.py --hours 72
    python scripts/sports_pm_scan.py --json
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys

import httpx


def fetch_active_sports_markets(min_vol24: float = 30000, min_liq: float = 5000) -> list[dict]:
    out: list[dict] = []
    seen_ids: set[str] = set()
    with httpx.Client(timeout=20) as c:
        for page in range(6):
            try:
                r = c.get("https://gamma-api.polymarket.com/markets", params={
                    "closed": "false", "active": "true", "limit": 500,
                    "offset": page * 500,
                    "order": "volume24hr", "ascending": "false",
                })
                r.raise_for_status()
            except Exception as e:
                print(f"page {page} fetch err: {e}", file=sys.stderr)
                continue
            data = r.json() or []
            if not data:
                break
            for m in data:
                mid = m.get("id")
                if not mid or mid in seen_ids:
                    continue
                seen_ids.add(mid)
                if m.get("umaResolutionStatus") in ("proposed", "disputed"):
                    continue
                if not _is_sports(m):
                    continue
                vol = float(m.get("volume24hr", 0) or 0)
                liq = float(m.get("liquidityNum", 0) or 0)
                if vol < min_vol24 or liq < min_liq:
                    continue
                out.append(m)
    return out


def _is_sports(m: dict) -> bool:
    if m.get("sportsMarketType"):
        return True
    text = ((m.get("question") or "") + " " + (m.get("description") or "") + " " + (m.get("slug") or "")).lower()
    return any(k in text for k in [
        " vs. ", " vs ", "premier league", "serie a", "nba", "nfl", "nhl",
        "mlb", "uefa", "fifa", "ufc", "f1 ", "tennis", "match", "mls",
        "champions league", "atletico", "real madrid", "manchester",
        "lakers", "warriors", "celtics", "thunder", "pistons", "cavaliers",
    ])


def categorize(m: dict) -> tuple[str, float, float, float]:
    """Return (lens, yes_price, no_price, days_to_resolve)."""
    try:
        prices = json.loads(m.get("outcomePrices", "[]")) if isinstance(m.get("outcomePrices"), str) else m.get("outcomePrices", [])
        yes = float(prices[0])
        no = float(prices[1])
    except Exception:
        return "UNKNOWN", 0.0, 0.0, 0.0

    # Prefer endDate (datetime) over endDateIso (date-only); date-only collapses
    # same-day events to 00:00 UTC which is in the past for any afternoon scan.
    end = m.get("endDate") or m.get("endDateIso") or ""
    try:
        end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        days = (end_dt - now_dt).total_seconds() / 86400
    except Exception:
        days = 0.0

    if yes >= 0.93:
        lens = "BOND_LIKE_FADE_YES"
    elif no >= 0.93:
        lens = "BOND_LIKE_FADE_NO"
    elif 0.40 <= yes <= 0.60:
        lens = "MID_50_50"
    elif yes >= 0.85 or no >= 0.85:
        lens = "STRONG_FAVORITE"
    else:
        lens = "OTHER"
    return lens, yes, no, days


def annualized_apy(p: float, days: float, fee_rate: float = 0.072) -> float:
    """APY for hold-to-resolution at price p, days. Capped at 10000x for display."""
    if p >= 0.999 or days < 0.5:
        return 0.0
    fee = fee_rate * min(p, 1 - p)
    cost = p * (1 + fee)
    if cost >= 1.0:
        return 0.0
    gross = (1.0 - cost) / cost
    # Cap APY at 10000x (1,000,000%) to avoid overflow on sub-day windows.
    # For sub-day windows the APY math becomes meaningless anyway; absolute
    # return-per-dollar is the meaningful metric there.
    try:
        apy = (1.0 + gross) ** (365.0 / max(days, 0.5)) - 1.0
    except OverflowError:
        apy = 1e4
    return min(apy, 1e4)


def main() -> int:
    p = argparse.ArgumentParser(description="Sports-market scanner for Polymarket trade candidates.")
    p.add_argument("--hours", type=float, default=48,
                   help="Resolution-window cutoff hours (default 48).")
    p.add_argument("--min-vol24", type=float, default=30000)
    p.add_argument("--min-liq", type=float, default=5000)
    p.add_argument("--hurdle-apy", type=float, default=0.034,
                   help="Hurdle APY for bond-like-fade surfacing (default 3.4%%).")
    p.add_argument("--json", action="store_true")
    p.add_argument("--limit", type=int, default=20)
    args = p.parse_args()

    print(f"# sports_pm_scan window=<={args.hours}h vol24h>=${args.min_vol24:.0f} liq>=${args.min_liq:.0f}", file=sys.stderr)

    markets = fetch_active_sports_markets(args.min_vol24, args.min_liq)
    print(f"# fetched {len(markets)} sports markets passing thresholds", file=sys.stderr)

    rows = []
    for m in markets:
        lens, yes, no, days = categorize(m)
        if days <= 0 or days * 24 > args.hours:
            continue
        # APY for the dominant side
        if yes >= no:
            apy = annualized_apy(yes, days)
            buy_side = "YES"
            mark = yes
        else:
            apy = annualized_apy(no, days)
            buy_side = "NO"
            mark = no
        rows.append({
            "question": m.get("question", "?"),
            "slug": m.get("slug", ""),
            "lens": lens,
            "yes": yes,
            "no": no,
            "buy_side": buy_side,
            "mark": mark,
            "apy_pct": apy * 100 if apy != float("inf") else float("inf"),
            "clears_hurdle": apy >= args.hurdle_apy if apy != float("inf") else True,
            "days_to_resolve": round(days, 2),
            "vol24h": float(m.get("volume24hr", 0) or 0),
            "liq": float(m.get("liquidityNum", 0) or 0),
            "id": m.get("id"),
            "tokens": m.get("clobTokenIds"),
        })

    rows.sort(key=lambda r: r["apy_pct"] if r["apy_pct"] != float("inf") else 9e9, reverse=True)
    rows = rows[: args.limit]

    if args.json:
        print(json.dumps({"results": rows}, indent=2, default=str))
        return 0

    print(f"\n# top {len(rows)} candidates (resolves <={args.hours}h):\n")
    for r in rows:
        # Profit per $1 if dominant side wins
        profit_per_dollar = (1.0 - r['mark']) / r['mark'] if r['mark'] > 0 else 0
        # APY display
        apy_pct = r['apy_pct']
        if apy_pct >= 1e6:
            apy_str = "  >1e6%"
        else:
            apy_str = f"{apy_pct:>9.1f}%"
        hurdle = "✓" if r['clears_hurdle'] else " "
        print(f"  {r['lens']:20s} {r['buy_side']}@${r['mark']:.4f}  +{profit_per_dollar*100:5.2f}%  d={r['days_to_resolve']:.1f}  v24=${r['vol24h']:>7.0f}  {r['question'][:55]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
