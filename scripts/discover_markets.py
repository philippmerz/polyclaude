"""Pull active markets from Polymarket gamma API, filter for tradability and quality,
and emit a JSON snapshot to data/snapshots/<UTC ts>.json plus a markdown shortlist.

Read-only. Safe to run frequently.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

import httpx

GAMMA = "https://gamma-api.polymarket.com"
DATA = Path("<PROJECT>/data")
SNAP_DIR = DATA / "snapshots"


def fetch_active(limit_per_page: int = 500, max_pages: int = 8) -> list[dict[str, Any]]:
    """Fetch active+open markets sorted by 24h volume desc, paginated."""
    out: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    with httpx.Client(timeout=20.0) as c:
        for page in range(max_pages):
            r = c.get(
                f"{GAMMA}/markets",
                params={
                    "closed": "false",
                    "archived": "false",
                    "active": "true",
                    "limit": str(limit_per_page),
                    "offset": str(page * limit_per_page),
                    "order": "volume24hr",
                    "ascending": "false",
                },
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            for m in batch:
                mid = str(m.get("id"))
                if mid not in seen_ids:
                    seen_ids.add(mid)
                    out.append(m)
            if len(batch) < limit_per_page:
                break
    return out


def parse_outcome_prices(m: dict[str, Any]) -> tuple[float, float] | None:
    """Return (yes_price, no_price) for binary markets, else None."""
    raw = m.get("outcomePrices")
    outs = m.get("outcomes")
    if not raw or not outs:
        return None
    try:
        prices = json.loads(raw) if isinstance(raw, str) else raw
        outs_l = json.loads(outs) if isinstance(outs, str) else outs
    except Exception:
        return None
    if len(prices) != 2 or set(map(str, outs_l)) != {"Yes", "No"}:
        return None
    p_yes = float(prices[outs_l.index("Yes")])
    p_no = float(prices[outs_l.index("No")])
    return p_yes, p_no


def is_tradable(m: dict[str, Any]) -> bool:
    return bool(
        m.get("acceptingOrders")
        and m.get("enableOrderBook")
        and not m.get("closed")
        and not m.get("archived")
    )


def is_quality(m: dict[str, Any], min_liq: float, min_vol24: float, max_spread: float) -> bool:
    if not is_tradable(m):
        return False
    if float(m.get("liquidityNum") or 0) < min_liq:
        return False
    if float(m.get("volume24hr") or 0) < min_vol24:
        return False
    spread = m.get("spread")
    if spread is not None and float(spread) > max_spread:
        return False
    end = m.get("endDate") or m.get("endDateIso")
    if not end:
        return False
    return True


def days_to_resolution(m: dict[str, Any], now: dt.datetime) -> float | None:
    end = m.get("endDate") or m.get("endDateIso")
    if not end:
        return None
    try:
        if "T" in end:
            t = dt.datetime.fromisoformat(end.replace("Z", "+00:00"))
        else:
            t = dt.datetime.fromisoformat(end + "T00:00:00+00:00")
        return (t - now).total_seconds() / 86400
    except Exception:
        return None


def category_of(m: dict[str, Any]) -> str:
    """Heuristic category from question/event/tag fields."""
    q = (m.get("question") or "").lower()
    desc = (m.get("description") or "").lower()
    text = q + " " + desc
    if m.get("sportsMarketType") or any(
        k in text for k in [" vs. ", " vs ", "premier league", "serie a", "nba", "nfl", "nhl", "mlb", "uefa", "fifa"]
    ):
        return "sports"
    if any(k in text for k in ["bitcoin", "ethereum", "btc", "eth", "solana", "$1", "memecoin", "crypto"]):
        return "crypto"
    if any(k in text for k in ["fed", "interest rate", "cpi", "inflation", "recession", "gdp", "unemployment", "fomc", "rate cut", "treasury"]):
        return "macro"
    if any(k in text for k in [
        "election", "primary", "president", "senator", "congress", "house seat",
        "uk", "germany", "france", "russia", "putin", "ukraine", "israel", "gaza", "iran", "nato", "china",
        "taiwan", "war", "ceasefire", "treaty", "sanction", "tariff",
    ]):
        return "geopolitics"
    if any(k in text for k in ["openai", "anthropic", "google", "chatgpt", "gpt-", "ai ", "agi", "model release", "stargate", "tesla", "nvidia", "apple", "microsoft", "tiktok"]):
        return "tech"
    if any(k in text for k in ["movie", "box office", "oscar", "billboard", "song", "spotify", "album"]):
        return "entertainment"
    return "other"


def shortlist(
    markets: list[dict[str, Any]],
    *,
    min_liq: float,
    min_vol24: float,
    max_spread: float,
    horizon_days: float,
    top_n: int,
) -> list[dict[str, Any]]:
    now = dt.datetime.now(dt.timezone.utc)
    rows: list[dict[str, Any]] = []
    for m in markets:
        if not is_quality(m, min_liq, min_vol24, max_spread):
            continue
        ttr = days_to_resolution(m, now)
        if ttr is None or ttr <= 0 or ttr > horizon_days:
            continue
        prices = parse_outcome_prices(m)
        if prices is None:
            yes = None
        else:
            yes = prices[0]
        rows.append({
            "id": m.get("id"),
            "slug": m.get("slug"),
            "question": m.get("question"),
            "category": category_of(m),
            "yes_price": yes,
            "spread": float(m.get("spread") or 0),
            "best_bid": float(m.get("bestBid") or 0),
            "best_ask": float(m.get("bestAsk") or 0),
            "liquidity": float(m.get("liquidityNum") or 0),
            "vol24h": float(m.get("volume24hr") or 0),
            "vol_total": float(m.get("volumeNum") or m.get("volume") or 0) if not isinstance(m.get("volume"), str) else float(m.get("volume") or 0),
            "days_to_resolve": round(ttr, 2),
            "neg_risk": bool(m.get("negRisk")),
            "fees_enabled": bool(m.get("feesEnabled")),
            "fee_rate": (m.get("feeSchedule") or {}).get("rate"),
            "min_size_usd": float(m.get("orderMinSize") or 0),
            "tick": float(m.get("orderPriceMinTickSize") or 0.01),
            "clob_token_ids": m.get("clobTokenIds"),
            "end_date": m.get("endDate"),
            "url": f"https://polymarket.com/market/{m.get('slug')}",
        })
    rows.sort(key=lambda r: (-r["vol24h"], -r["liquidity"]))
    return rows[:top_n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-liquidity", type=float, default=20_000)
    ap.add_argument("--min-vol24", type=float, default=2_000)
    ap.add_argument("--max-spread", type=float, default=0.05)
    ap.add_argument("--horizon-days", type=float, default=370)
    ap.add_argument("--top", type=int, default=80)
    ap.add_argument("--max-pages", type=int, default=10)
    ap.add_argument("--no-snapshot", action="store_true")
    args = ap.parse_args()

    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    markets = fetch_active(max_pages=args.max_pages)
    print(f"fetched {len(markets)} active markets")

    short = shortlist(
        markets,
        min_liq=args.min_liquidity,
        min_vol24=args.min_vol24,
        max_spread=args.max_spread,
        horizon_days=args.horizon_days,
        top_n=args.top,
    )

    if not args.no_snapshot:
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snap_path = SNAP_DIR / f"shortlist_{ts}.json"
        snap_path.write_text(json.dumps(short, indent=2))
        latest = SNAP_DIR / "shortlist_latest.json"
        try:
            if latest.exists() or latest.is_symlink():
                latest.unlink()
        except FileNotFoundError:
            pass
        os.symlink(snap_path.name, latest)
        print(f"wrote {snap_path}")

    # Also print a compact table
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for r in short:
        by_cat.setdefault(r["category"], []).append(r)
    for cat in sorted(by_cat, key=lambda k: -sum(r["vol24h"] for r in by_cat[k])):
        rows = by_cat[cat][:8]
        print(f"\n=== {cat} ({sum(r['vol24h'] for r in by_cat[cat]):.0f} vol24h, {len(by_cat[cat])} mkts) ===")
        for r in rows:
            yp = f"{r['yes_price']:.3f}" if r["yes_price"] is not None else "  -  "
            print(f"  yes={yp}  spd={r['spread']:.3f}  liq={r['liquidity']:>9.0f}  v24={r['vol24h']:>9.0f}  d={r['days_to_resolve']:>6.1f}  {r['question'][:90]}")


if __name__ == "__main__":
    main()
