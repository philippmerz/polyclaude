#!/usr/bin/env python3
"""Favorite-fade scanner — harvest the empirically-validated favorite-longshot edge.

Backtest (scripts/longshot_calibration_backtest.py, N=1513, 7d-pre-resolution, clean)
showed Polymarket favorites in the 0.90-0.98 zone win MORE than priced:
  0.90-0.95: won 97.3% vs 92.5% priced (+4.8pp, 3.2sigma)
  0.95-0.98: won 99.4% vs 96.6% priced (+2.8pp, 4.7sigma)
Mild favorites (<0.90) are calibrated; >0.98 edge is tiny + small-N-lucky. The edge is
strongest NEAR resolution (the 30d cut was weak), so we target a short horizon.

This finds CURRENT liquid binary markets whose favorite side trades (live CLOB ask, NOT
gamma midpoint) in the validated zone with a short horizon, computes the expected edge
from the calibration curve net of the slippage we'd pay (we use the real ask), and ranks.

Compute-bounded: gamma candidate pre-filter, then live-book walks capped at --max-walks.
Execution still routes through polyclaude_enter.py (umaResolutionStatus + robust-edge gate
+ Kelly sizing) — this surfaces a ranked, diversification-tagged buy-list, it does not trade.

Caveats: (1) the calibration win-rate is a POPULATION average — an individual market's
longshot side may be fairly priced (no edge) or a meme mispricing (more edge); diversify.
(2) resolution-ambiguity (the R-U risk) is not fully mechanical — proposed/disputed UMA is
skipped, but run catalyst_check on the top picks before sizing. (3) fat tail: win a few c /
lose ~the stake — size small (fractional Kelly), spread across uncorrelated `cat` groups.

CLI: favorite_fade_scan.py [--min-days 2] [--max-days 14] [--min-liq 20000]
                           [--min-edge-pp 1.0] [--max-walks 40] [--json]
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone

import httpx

GAMMA = "https://gamma-api.polymarket.com/markets"
CLOB_BOOK = "https://clob.polymarket.com/book"

# Empirical favorite-side win-rate by live-ask bucket (from the N=1513 7d backtest).
# Used as the expected resolution probability for a market whose favorite trades there.
CALIB = [
    (0.90, 0.95, 0.973),
    (0.95, 0.98, 0.994),
    (0.98, 0.985, 0.990),  # conservative cap; the raw 100% was small-N luck
]


def _parse(x):
    return ast.literal_eval(x) if isinstance(x, str) else x


def empirical_winrate(p: float) -> float | None:
    for lo, hi, wr in CALIB:
        if lo <= p < hi:
            return wr
    return None


def categorize(q: str) -> str:
    """Category from the question. Per the 2026-06-02 category-segmented backtest
    (fav>=0.90), the favorite-longshot edge is REAL in other/meme (+1.9pp, 4.8sigma),
    politics/geo (+2.3pp) and sports (+1.6pp) but ABSENT in crypto/price (+0.4pp, ns) —
    so crypto/price + macro are excluded by default (efficient markets, spurious edge)."""
    s = (q or "").lower()
    if any(k in s for k in [" vs ", " vs.", "world cup", "french open", "champion",
                            "premier league", "super bowl", "stanley cup", "nba finals",
                            "win the 2026 men", "win the 2026 women", " beat ", "grand prix",
                            "f1 ", "drivers' champion", "iem ", "major 2026", "playoff",
                            "win on 2026"]):
        return "sports"
    if any(k in s for k in ["bitcoin", "ethereum", "btc", "eth ", "solana", " sol ",
                            "hyperliquid", "dogecoin", "xrp", "price of", "launch a token",
                            "all time high", "market cap"]):
        return "crypto/price"
    if any(k in s for k in ["fed ", "interest rate", "ecb", " cpi", "inflation", "recession",
                            "gdp", "jobs report", "rate cut", "rate hike", "basis point"]):
        return "macro"
    if any(k in s for k in ["president", "election", "senate", "house", "governor",
                            "prime minister", "regime", "coup", "nuclear", "invade", " war",
                            "peace deal", "ceasefire", "sanction", "minister", "parliament",
                            "nominee", "mayor", "impeach", "out as ", "airspace", "blockade",
                            "strait", "leader of", "head of state"]):
        return "politics/geo"
    return "other/meme"


def fetch_active(max_pages: int, client: httpx.Client) -> list:
    out, offset, retries = [], 0, 0
    while len(out) < max_pages * 100:
        try:
            r = client.get(GAMMA, params={
                "closed": "false", "active": "true", "limit": 100, "offset": offset,
                "order": "volume24hr", "ascending": "false",
            }, timeout=25).json()
        except Exception:
            r = None
        if not isinstance(r, list):
            retries += 1
            if retries > 4:
                break
            continue
        if not r:
            break
        retries = 0
        out.extend([m for m in r if isinstance(m, dict)])
        offset += 100
        if offset >= max_pages * 100:
            break
    return out


def best_ask(token: str, client: httpx.Client) -> tuple[float | None, float]:
    try:
        b = client.get(CLOB_BOOK, params={"token_id": token}, timeout=15).json()
    except Exception:
        return None, 0.0
    asks = b.get("asks", []) if isinstance(b, dict) else []
    if not asks:
        return None, 0.0
    best = min(asks, key=lambda a: float(a["price"]))
    bp = float(best["price"])
    depth = sum(float(a["size"]) for a in asks if float(a["price"]) <= bp + 0.02)
    return bp, depth


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-days", type=float, default=2.0)
    ap.add_argument("--max-days", type=float, default=14.0)
    ap.add_argument("--min-liq", type=float, default=20000)
    ap.add_argument("--min-edge-pp", type=float, default=1.0)
    ap.add_argument("--max-walks", type=int, default=40)
    ap.add_argument("--max-pages", type=int, default=10)
    ap.add_argument("--exclude-cats", default="crypto/price,macro",
                    help="comma-separated categories to skip as efficient/no-edge "
                         "(default crypto/price,macro per the category-segmented backtest)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    exclude_cats = {c.strip() for c in args.exclude_cats.split(",") if c.strip()}

    now = datetime.now(timezone.utc)
    with httpx.Client() as client:
        mkts = fetch_active(args.max_pages, client)
        print(f"# fetched {len(mkts)} active markets", file=sys.stderr)
        cands = []
        for m in mkts:
            if _parse(m.get("outcomes")) != ["Yes", "No"]:
                continue
            if m.get("umaResolutionStatus") not in (None, "", "resolved"):
                continue  # proposed/disputed -> skip (R-U risk)
            op = _parse(m.get("outcomePrices") or "[]")
            if not op or len(op) != 2:
                continue
            try:
                yes = float(op[0])
            except Exception:
                continue
            fav = max(yes, 1 - yes)
            if not (0.88 <= fav <= 0.99):  # rough zone; live ask refines
                continue
            end = m.get("endDate")
            if not end:
                continue
            try:
                edt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            except Exception:
                continue
            days = (edt - now).total_seconds() / 86400
            if not (args.min_days <= days <= args.max_days):
                continue
            liq = float(m.get("liquidity") or 0)
            if liq < args.min_liq:
                continue
            toks = _parse(m.get("clobTokenIds") or "[]")
            if len(toks) != 2:
                continue
            cat = categorize(m.get("question", ""))
            if cat in exclude_cats:
                continue  # efficient category (no favorite-longshot edge) — skip
            fav_is_yes = yes >= 0.5
            cands.append({
                "q": m.get("question", ""), "fav_is_yes": fav_is_yes,
                "fav_tok": toks[0] if fav_is_yes else toks[1],
                "days": days, "liq": liq, "cat": cat,
                "vol24": float(m.get("volume24hr") or 0),
            })
        cands.sort(key=lambda c: -c["liq"])
        cands = cands[:args.max_walks]
        print(f"# {len(cands)} candidates in rough zone; walking live books", file=sys.stderr)

        rows = []
        for c in cands:
            ask, depth = best_ask(c["fav_tok"], client)
            if ask is None:
                continue
            wr = empirical_winrate(ask)
            if wr is None:
                continue  # live ask outside the validated 0.90-0.98 zone
            edge = wr - ask  # net of the slippage we pay (we cross to the ask)
            if edge * 100 < args.min_edge_pp:
                continue
            apy = edge / ask * 365 / max(c["days"], 0.5)
            rows.append({**c, "ask": round(ask, 4), "depth_usd": round(ask * depth, 0),
                         "exp_winrate": wr, "edge_pp": round(edge * 100, 2),
                         "apy_pct": round(apy * 100, 0)})
    rows.sort(key=lambda r: -r["edge_pp"])

    if args.json:
        print(json.dumps(rows, indent=1))
        return 0
    print(f"\n# {len(rows)} favorite-fade candidates (live ask in validated 0.90-0.98 zone, "
          f"{args.min_days:.0f}-{args.max_days:.0f}d, edge>={args.min_edge_pp}pp)\n")
    if not rows:
        print("  none")
        return 0
    print(f"{'side':>4} {'ask':>6} {'edgepp':>6} {'APY':>6} {'days':>5} {'depth$':>9} {'cat':>8}  question")
    print("-" * 92)
    for r in rows:
        side = "YES" if r["fav_is_yes"] else "NO"
        print(f"{side:>4} {r['ask']:.3f} {r['edge_pp']:>6.1f} {r['apy_pct']:>5.0f}% "
              f"{r['days']:>4.0f}d {r['depth_usd']:>9.0f} {r['cat']:>8}  {r['q'][:50]}")
    print("\n# NOTE: edge = population calibration avg; run catalyst_check on top picks "
          "(R-U risk), diversify across cat groups, size small (fat tail).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
