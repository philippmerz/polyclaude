#!/usr/bin/env python3
"""Favorite-longshot calibration backtest for Polymarket.

Question this answers: if you mechanically buy the FAVORITE side (the >50% side)
of resolved binary markets, do favorites win MORE often than their price implies
(favorite-longshot bias -> buy-favorite is +EV), LESS often (favorites overpriced
-> fade them), or exactly as priced (calibrated -> no mechanical edge)?

Method:
  1. Pull resolved binary Yes/No markets from gamma (closed=true), liquid only.
  2. For each, read the decisive outcome from outcomePrices (["1","0"]=YES won).
  3. Pull the YES-token CLOB price-history; take the price at (closedTime - lookback)
     as the "entry price" you'd have paid.
  4. favorite_price = max(yes, 1-yes); favorite_won = (favorite side == winning side).
  5. Bucket by favorite_price; per bucket report N, empirical win-rate, mean implied
     price, edge (empirical - implied) +/- binomial SE, and EV per $1 staked.

Caveats (a backtest is not a forward edge): recent-resolution sample (selection),
single lookback snapshot (run several --lookback-days to check sensitivity), no
fee/slippage modelling, no resolution-ambiguity (R-U) filter. Directional only.

CLI:
  longshot_calibration_backtest.py [--limit 400] [--lookback-days 7]
                                   [--min-volume 20000] [--fidelity 720]
"""
from __future__ import annotations

import argparse
import ast
import math
import sys
import time

import httpx

GAMMA = "https://gamma-api.polymarket.com/markets"
CLOB_PH = "https://clob.polymarket.com/prices-history"

BUCKETS = [(0.50, 0.60), (0.60, 0.70), (0.70, 0.80), (0.80, 0.85),
           (0.85, 0.90), (0.90, 0.95), (0.95, 0.98), (0.98, 0.995)]


def _parse(x):
    return ast.literal_eval(x) if isinstance(x, str) else x


def categorize(q: str) -> str:
    """Heuristic category from the question (gamma's category field is empty on
    resolved markets). Used to find WHERE the favorite-longshot edge concentrates."""
    s = (q or "").lower()
    if any(k in s for k in [" vs ", " vs.", "world cup", "french open", "champion",
                            "premier league", "super bowl", "stanley cup", "nba finals",
                            "win the 2026 men", "win the 2026 women", " beat ", "grand prix",
                            "f1 ", "drivers' champion", "iem ", "major 2026", "playoff"]):
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


def fetch_resolved(limit: int, min_volume: float, client: httpx.Client) -> list:
    """Paginate gamma closed=true for liquid binary Yes/No markets."""
    out, offset, retries = [], 0, 0
    while len(out) < limit and offset < limit * 4:
        try:
            r = client.get(GAMMA, params={
                "closed": "true", "limit": 100, "offset": offset,
                "order": "closedTime", "ascending": "false",
                "volume_num_min": min_volume,
            }, timeout=25).json()
        except Exception:
            r = None
        if not isinstance(r, list):  # transient error / dict response -> retry same offset
            retries += 1
            if retries > 5:
                break
            time.sleep(1.5)
            continue
        if not r:
            break
        retries = 0
        for m in r:
            if not isinstance(m, dict):
                continue
            oc = _parse(m.get("outcomes"))
            op = _parse(m.get("outcomePrices"))
            if oc != ["Yes", "No"] or not op:
                continue
            if m.get("umaResolutionStatus") != "resolved":
                continue
            # decisive resolution only (["1","0"] or ["0","1"])
            try:
                p0 = float(op[0])
            except Exception:
                continue
            if p0 not in (0.0, 1.0):
                continue
            toks = _parse(m.get("clobTokenIds"))
            ct = m.get("closedTime")
            if not toks or not ct:
                continue
            out.append({"q": m.get("question", ""), "yes_won": p0 == 1.0,
                        "yes_tok": toks[0], "closedTime": ct,
                        "cat": categorize(m.get("question", ""))})
        offset += 100
    return out[:limit]


def _closed_ts(ct: str) -> int | None:
    # gamma closedTime like "2026-06-02 10:09:16+00"
    for fmt in ("%Y-%m-%d %H:%M:%S%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return int(time.mktime(time.strptime(ct.split("+")[0], "%Y-%m-%d %H:%M:%S")))
        except Exception:
            continue
    return None


def entry_price(yes_tok: str, closed_ts: int, lookback_days: float,
                fidelity: int, client: httpx.Client,
                require_full: bool = False) -> float | None:
    ph = None
    for _ in range(3):  # retry transient prices-history failures so we don't silently drop markets
        try:
            resp = client.get(CLOB_PH, params={"market": yes_tok, "interval": "max",
                                               "fidelity": fidelity}, timeout=25).json()
            if isinstance(resp, dict):
                ph = resp
                break
        except Exception:
            pass
        time.sleep(0.8)
    if ph is None:
        return None
    h = ph.get("history", [])
    if not h:
        return None
    target = closed_ts - int(lookback_days * 86400)
    # nearest point at or before target; fall back to earliest if market younger
    best = None
    for pt in h:
        if pt["t"] <= target:
            best = pt
        else:
            break
    if best is None:
        if require_full:
            return None  # market younger than lookback; no genuine entry price (skip, don't fall back)
        best = h[0]  # market younger than lookback -> earliest available
    p = float(best["p"])
    if p <= 0.0 or p >= 1.0:
        return None
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--lookback-days", type=float, default=7.0)
    ap.add_argument("--min-volume", type=float, default=20000)
    ap.add_argument("--fidelity", type=int, default=720)
    ap.add_argument("--require-full-lookback", action="store_true",
                    help="skip markets younger than lookback instead of falling back to open price "
                         "(controls for the 'opens near 0.5, drifts to winner' artifact)")
    ap.add_argument("--by-category", action="store_true",
                    help="also break down the favorite edge by market category for fav>=0.90 "
                         "(finds WHERE the favorite-longshot bias concentrates)")
    ap.add_argument("--ask-adjust", type=float, default=0.0,
                    help="EXECUTABLE-PRICE sensitivity (2026-07-03 haircut-design review): add this "
                         "many price units to the favorite entry price to model the mid-to-ask gap "
                         "(prices-history is trade/mid-ish, not a lifted ask — the midpoints-"
                         "unreliable house lesson). E.g. 0.01. A bucket whose edge survives "
                         "--ask-adjust 0.01-0.015 is executable, not just observable.")
    args = ap.parse_args()

    with httpx.Client() as client:
        mkts = fetch_resolved(args.limit, args.min_volume, client)
        print(f"# {len(mkts)} resolved binary markets (vol>={args.min_volume:.0f}), "
              f"lookback={args.lookback_days}d", file=sys.stderr)
        rows = []
        for i, m in enumerate(mkts):
            cts = _closed_ts(m["closedTime"])
            if cts is None:
                continue
            ep = entry_price(m["yes_tok"], cts, args.lookback_days, args.fidelity, client,
                             require_full=args.require_full_lookback)
            if ep is None:
                continue
            fav = max(ep, 1 - ep)
            fav_is_yes = ep >= 0.5
            fav_won = (fav_is_yes == m["yes_won"])
            if args.ask_adjust:
                fav = min(fav + args.ask_adjust, 0.999)  # model paying the ask, not the mid
            rows.append((fav, fav_won, m.get("cat", "")))
            if (i + 1) % 50 == 0:
                print(f"#  processed {i+1}/{len(mkts)}", file=sys.stderr)

    print(f"\n# usable (entry price + outcome): {len(rows)} markets\n")
    print(f"{'bucket':>12} {'N':>5} {'emp_win%':>9} {'implied%':>9} "
          f"{'edge_pp':>8} {'SE_pp':>6} {'EV/$1':>7}")
    print("-" * 64)
    tot_n = tot_correct = 0
    for lo, hi in BUCKETS:
        b = [(f, w) for f, w, c in rows if lo <= f < hi]
        n = len(b)
        if n == 0:
            continue
        wins = sum(1 for _, w in b if w)
        emp = wins / n
        impl = sum(f for f, _ in b) / n
        edge = (emp - impl) * 100
        se = math.sqrt(emp * (1 - emp) / n) * 100 if n else 0
        # EV of buying favorite at mean implied price, $1 payout: win_rate*1 - price
        ev = emp - impl
        tot_n += n
        tot_correct += wins
        print(f"{lo:.2f}-{hi:.2f}  {n:>5} {emp*100:>8.1f}% {impl*100:>8.1f}% "
              f"{edge:>+7.1f} {se:>5.1f} {ev:>+7.3f}")
    print("-" * 64)
    if tot_n:
        print(f"  overall favorites: {tot_correct}/{tot_n} = {tot_correct/tot_n*100:.1f}% won")

    if args.by_category:
        from collections import defaultdict
        cats = defaultdict(list)
        for f, w, c in rows:
            if f >= 0.90:  # the validated edge zone
                cats[c or "(none)"].append((f, w))
        print(f"\n# favorite edge by category (fav>=0.90 only):")
        print(f"{'category':>14} {'N':>5} {'emp_win%':>9} {'implied%':>9} {'edge_pp':>8} {'SE_pp':>6}")
        print("-" * 56)
        for cat, b in sorted(cats.items(), key=lambda kv: -len(kv[1])):
            n = len(b)
            if n < 10:
                continue
            wins = sum(1 for _, w in b if w)
            emp = wins / n
            impl = sum(f for f, _ in b) / n
            se = math.sqrt(emp * (1 - emp) / n) * 100
            print(f"{cat[:14]:>14} {n:>5} {emp*100:>8.1f}% {impl*100:>8.1f}% "
                  f"{(emp-impl)*100:>+7.1f} {se:>5.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
