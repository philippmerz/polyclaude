"""Print current open Polymarket positions for the wallet, mark-to-market.

Pulls from data-api.polymarket.com (public, no auth). Read-only.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import httpx

from polyclaude_client import Wallet  # noqa: E402

DATA_API = "https://data-api.polymarket.com"


def main() -> None:
    addr = Wallet.load().address
    with httpx.Client(timeout=15.0) as c:
        r = c.get(f"{DATA_API}/positions", params={"user": addr.lower(), "limit": "100"})
        r.raise_for_status()
        positions = r.json()
    if not positions:
        print("(no open positions)")
        return

    total_init = 0.0
    total_cur = 0.0
    total_max = 0.0
    print(f"{'side':4} {'entry':>6} {'mark':>6} {'shares':>8} {'cost':>7} {'mtm':>7} {'maxpay':>7} {'pnl%':>6}  market")
    for p in sorted(positions, key=lambda x: -x["initialValue"]):
        side = p["outcome"]
        entry = p["avgPrice"]
        mark = p["curPrice"]
        shares = p["size"]
        cost = p["initialValue"]
        cur = p["currentValue"]
        maxpay = shares  # if NO wins, get $1 per share
        pnl_pct = p["percentPnl"]
        total_init += cost
        total_cur += cur
        total_max += maxpay
        print(f"{side:4} {entry:>6.3f} {mark:>6.3f} {shares:>8.2f} {cost:>7.2f} {cur:>7.2f} {maxpay:>7.2f} {pnl_pct:>6.2f}  {p['title'][:60]}")
    print()
    print(f"TOTAL  cost ${total_init:.2f}  mtm ${total_cur:.2f}  max-payout ${total_max:.2f}  unrealised P&L ${total_cur-total_init:+.2f}  ({(total_cur/total_init-1)*100:+.2f}%)")
    print(f"Max upside if all NO win: ${total_max:.2f}  ({(total_max/total_init-1)*100:+.2f}%)")

    # REALIZABLE vs MARKED (2026-08-13). `curPrice` is a MIDPOINT, and on an
    # illiquid book the midpoint is not a price anyone will pay. That day the
    # MacBook leg printed mark 0.685 — the middle of a 0.57/0.76 spread with
    # ZERO 24h volume and zero bid depth above 0.60 — inflating that leg by
    # $7.59 and the headline by $8.64 (+19.5% marked vs +13.7% realizable). I
    # was one step from reporting the marked figure to the operator, for the
    # second time in two days that a midpoint flattered a number. exit_analysis
    # already walks real bids, but THIS is the headline, so it needs to say so
    # itself. Only prints when the gap is material, so it stays quiet on a
    # tight book rather than becoming wallpaper.
    try:
        import json as _json
        realizable = 0.0
        worst = []
        with httpx.Client(timeout=20.0) as c:
            for p in positions:
                if float(p.get("size", 0)) <= 0.5:
                    continue
                m = c.get("https://gamma-api.polymarket.com/markets",
                          params={"slug": p["slug"]}).json()[0]
                toks = _json.loads(m["clobTokenIds"]); outs = _json.loads(m["outcomes"])
                bk = c.get("https://clob.polymarket.com/book",
                           params={"token_id": toks[outs.index(p["outcome"])]}).json()
                bids = sorted(bk.get("bids", []), key=lambda x: -float(x["price"]))
                # WALK the book for the ACTUAL size rather than best_bid x size
                # (2026-08-13 evening). Best-bid pricing assumes infinite depth
                # at the touch, which is exactly wrong on the books where this
                # check matters: MacBook that evening showed a 1pp spread — so
                # the MARK was trustworthy — but only 5 shares bid at 0.63
                # before a gap to 0.57, against 66 held. Best-bid claimed $41.58;
                # walking the book gives ~$37.62. Same error class as using a
                # midpoint: a single price point standing in for an executable path.
                size_left = float(p["size"])
                proceeds = 0.0
                for lvl in bids:
                    if size_left <= 0:
                        break
                    take = min(size_left, float(lvl["size"]))
                    proceeds += take * float(lvl["price"])
                    size_left -= take
                realizable += proceeds          # unfilled remainder counts as $0
                avg_fill = proceeds / float(p["size"]) if float(p["size"]) else 0.0
                gap = float(p["curPrice"]) - avg_fill
                if gap > 0.03:
                    # report AVG FILL, not best bid — the displayed number must be
                    # the one the gap was computed from, or the line contradicts
                    # itself (a 1pp spread showing a 6.5pp gap reads as a bug).
                    worst.append((gap, p["slug"][:44], float(p["curPrice"]), avg_fill))
        gap_total = total_cur - realizable
        if gap_total > 1.0:
            print(f"REALIZABLE (depth-walked): ${realizable:.2f}  "
                  f"({(realizable/total_init-1)*100:+.2f}%)  "
                  f"— midpoints overstate by ${gap_total:.2f}")
            for g, slug, mk, bd in sorted(worst, reverse=True):
                print(f"   thin book: {slug} mark {mk:.3f} vs avg-fill {bd:.3f} "
                      f"({g*100:.1f}pp to exit the full position)")
    except Exception as e:
        print(f"(realizable check unavailable: {str(e)[:60]})")


if __name__ == "__main__":
    main()
