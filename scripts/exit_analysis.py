#!/usr/bin/env python3
"""Hold vs sell, computed on the LIVE book, for every open position.

Every exit is three options, not two, and the fee makes the route decisive:
  HOLD            -> EV = shares x fair            (resolution is FEE-FREE)
  SELL TAKER now  -> walk the real BID book, minus taker fee (10% x min(p,1-p)
                     per share on fee-bearing markets)
  REST MAKER sell -> post-only, fee-free, so the breakeven price IS `fair`;
                     the order only fills if someone pays >= fair.

Lesson sources: the Prime-SDCC exit (2026-07-24) sold taker into a thin book at
the midpoint's flattering price and gave up ~$2 of EV vs holding; the Fed
position (2026-07-28) showed taker breakeven 0.2778 vs maker breakeven 0.2500 —
a 2.8pp gap that decides the trade. Doctrine (notes/resting_orders.md): when
hold and sell are close, DON'T CHOOSE — rest a maker sell at the strictly-better
price and let the market decide.

Reads fair values from notes/portfolio_kelly_priors.json (side-aware, and it
respects the `verified` staleness convention by WARNING on priors > 14d).

CLI: exit_analysis.py [--slug-filter TEXT]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
PRIORS = REPO / "notes" / "portfolio_kelly_priors.json"
ADDR = "0x9032ad983ee5a22bfd078ecc4fd3d4d69e57267b"


def _fair(slug: str, side: str, priors: dict):
    for k, v in priors.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        if k in slug or slug in k:
            p = v.get("p_no") if side == "No" else v.get("p_yes")
            return (float(p) if p is not None else None), v.get("verified")
    return None, None


def _walk_bids(token: str, shares: float) -> tuple[float, float]:
    """Return (gross_proceeds, shares_filled) walking the real bid side."""
    b = httpx.get("https://clob.polymarket.com/book",
                  params={"token_id": token}, timeout=15).json()
    bids = sorted(b.get("bids", []), key=lambda x: -float(x["price"]))
    rem, gross = shares, 0.0
    for lvl in bids:
        px, sz = float(lvl["price"]), float(lvl["size"])
        take = min(rem, sz)
        gross += take * px
        rem -= take
        if rem <= 0:
            break
    return gross, shares - rem


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug-filter", default=None)
    args = ap.parse_args()

    priors = json.loads(PRIORS.read_text())
    pos = httpx.get("https://data-api.polymarket.com/positions",
                    params={"user": ADDR, "limit": "100"}, timeout=25).json()
    today = dt.date.today()
    rows = []
    for p in pos:
        if float(p.get("size", 0)) < 0.5:
            continue
        slug = p.get("slug", "")
        if args.slug_filter and args.slug_filter not in slug:
            continue
        side, shares = p["outcome"], float(p["size"])
        fair, verified = _fair(slug, side, priors)
        if fair is None:
            print(f"  [NO PRIOR] {slug[:52]} — add one to price the exit", file=sys.stderr)
            continue
        # fee schedule from the market (0 on fee-free markets)
        mk = httpx.get("https://clob.polymarket.com/markets/" + str(p.get("conditionId")),
                       timeout=15).json()
        fee = float(mk.get("taker_base_fee") or 0) / 10000.0
        gross, filled = _walk_bids(p["asset"], shares)
        avg_fill = (gross / filled) if filled else 0.0
        taker_net = gross - fee * min(avg_fill, 1 - avg_fill) * filled
        hold_ev = shares * fair
        taker_be = fair / (1 - fee) if fee < 1 else None   # price at which taker == hold
        stale = ""
        try:
            if verified and (today - dt.date.fromisoformat(str(verified))).days > 14:
                stale = " [PRIOR-STALE]"
        except Exception:
            stale = " [PRIOR-UNDATED]"
        if taker_net > hold_ev:
            verdict = f"SELL TAKER NOW (+${taker_net - hold_ev:.2f} vs hold)"
        else:
            verdict = (f"HOLD (+${hold_ev - taker_net:.2f}); rest maker sell >= "
                       f"{fair:.3f} (taker would need {taker_be:.3f})")
        rows.append((slug, side, shares, fair, avg_fill, hold_ev, taker_net, verdict, stale))

    if not rows:
        print("no priced positions")
        return 0
    print(f"{'position':<44}{'side':>5}{'sh':>7}{'fair':>7}{'bid~':>7}{'hold$':>8}{'sell$':>8}  verdict")
    for slug, side, sh, fair, bid, hold_ev, taker_net, verdict, stale in rows:
        print(f"{slug[:44]:<44}{side:>5}{sh:>7.1f}{fair:>7.3f}{bid:>7.3f}"
              f"{hold_ev:>8.2f}{taker_net:>8.2f}  {verdict}{stale}")
    print("\nresolution is fee-free; maker sells are fee-free; taker sells pay "
          "fee x min(p,1-p)/share — that gap is usually the whole decision.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
