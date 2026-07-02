"""Ostium funding-rate scanner.

Pulls every active Ostium pair, computes the OI imbalance and the recent
funding-rate magnitude, and surfaces pairs where one side is paying the
other meaningful carry.

The Ostium funding mechanism is Hill-model: funding rate scales with
(longOI - shortOI) / max(longOI, shortOI). The heavier side pays the
lighter side, so:
  · longOI >> shortOI → longs pay shorts → you collect funding by going SHORT
  · shortOI >> longOI → shorts pay longs → you collect funding by going LONG

CAVEAT: the funding-rate magnitude signal is unverified on Ostium — many
pairs report `lastFundingRate=0` and `maxFundingFeePerBlock=0` even when
OI imbalance is large, suggesting funding is bursty or pair-dependent.
The accFunding fields ARE non-zero, so SOMETHING accrues cumulatively;
calibration should come from empirically measuring P&L drift on existing
positions vs price-only movement.

This is informational ONLY — it surfaces candidates. Actual trades require:
- correlated-pair hedge for delta-neutrality (long pair X, short pair Y)
  OR explicit directional thesis if running net-long/short
- size within Ostium budget (currently ~$35 free of $50 cap)
- skeptic + champion check before any new strategy class

Output: logs/ostium_funding_<ts>.md + logs/ostium_funding_latest.json.
No auto-execution.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ostium_client import _sdk

import _paths as _secrets

_secrets.install_scrubbing_excepthook()

_REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = _REPO_ROOT / "logs"

# Min OI per side (in nominal USD via lastTradePrice * OI_in_tokens / 1e18)
# below which the funding signal is too noisy / orderbook too thin.
MIN_OI_USD = 50_000


def _to_float(x, scale: float = 1e18) -> float:
    try:
        return float(x) / scale
    except Exception:
        return 0.0


def evaluate_pair(p: dict) -> dict | None:
    """Return funding-trade evaluation for one pair, or None if too thin."""
    long_oi_tokens = _to_float(p.get("longOI", 0))
    short_oi_tokens = _to_float(p.get("shortOI", 0))
    last_price = _to_float(p.get("lastTradePrice", 0), scale=1e18)
    # Convert OI to USD nominal
    long_oi_usd = long_oi_tokens * last_price
    short_oi_usd = short_oi_tokens * last_price
    total_oi_usd = long_oi_usd + short_oi_usd
    if total_oi_usd < 2 * MIN_OI_USD:
        return None
    if long_oi_usd < MIN_OI_USD or short_oi_usd < MIN_OI_USD:
        # Below the noise floor on the lighter side — funding signal unreliable
        return None

    imbalance = (long_oi_usd - short_oi_usd) / max(long_oi_usd, short_oi_usd)
    # Heavier side pays. Recommended direction = lighter side.
    if imbalance > 0:
        recommended = "SHORT"  # longs heavier → short collects funding
    else:
        recommended = "LONG"   # shorts heavier → long collects funding

    last_funding = _to_float(p.get("lastFundingRate", 0))
    acc_long = _to_float(p.get("accFundingLong", 0))
    acc_short = _to_float(p.get("accFundingShort", 0))
    # accFunding values are cumulative since pair inception; the SIGN of
    # (accLong - accShort) tells you who's been paying historically.
    # Positive accFundingLong = longs paid into the pool (= longs lost carry).
    historical_funding_to_shorts = acc_long - acc_short

    return {
        "pair_id": p.get("id"),
        "symbol": f"{p.get('from')}/{p.get('to')}",
        "group": (p.get("group") or {}).get("name") if isinstance(p.get("group"), dict) else p.get("group"),
        "last_price": last_price,
        "long_oi_usd": round(long_oi_usd, 0),
        "short_oi_usd": round(short_oi_usd, 0),
        "total_oi_usd": round(total_oi_usd, 0),
        "imbalance": round(imbalance, 4),
        "recommended_direction": recommended,
        "last_funding_rate": round(last_funding, 6),
        "acc_funding_long": round(acc_long, 6),
        "acc_funding_short": round(acc_short, 6),
        "historical_paid_to_shorts": round(historical_funding_to_shorts, 6),
        "max_oi_cap_usd": _to_float(p.get("maxOI", 0)) * last_price,
    }


async def fetch_all_pairs() -> list[dict]:
    sdk = _sdk()
    out: list[dict] = []
    # Try ids 0..60 (currently 29 active, but spaced)
    for pid in range(60):
        try:
            p = await sdk.subgraph.get_pair_details(pid)
            if p:
                out.append(p)
        except Exception:
            continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-imbalance", type=float, default=0.10,
                    help="surface pairs with |imbalance| above this (default 0.10 = 10%)")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    print("fetching Ostium pair data...")
    pairs = asyncio.run(fetch_all_pairs())
    print(f"  pulled {len(pairs)} pairs")

    print("evaluating funding imbalance...")
    rows = []
    for p in pairs:
        r = evaluate_pair(p)
        if r is None:
            continue
        rows.append(r)
    print(f"  {len(rows)} pairs above {MIN_OI_USD/1000:.0f}k USD min-OI floor")

    # Sort by absolute imbalance descending
    rows.sort(key=lambda r: -abs(r["imbalance"]))

    above_threshold = [r for r in rows if abs(r["imbalance"]) >= args.min_imbalance]
    print(f"  {len(above_threshold)} pairs above |imbalance|≥{args.min_imbalance*100:.0f}%")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_md = OUT_DIR / f"ostium_funding_{ts}.md"
    out_json = OUT_DIR / "ostium_funding_latest.json"

    with out_md.open("w") as f:
        f.write(f"# Ostium funding-rate scan — {ts} UTC\n\n")
        f.write(f"{len(pairs)} pairs pulled, {len(rows)} above OI floor (≥${MIN_OI_USD/1000:.0f}k each side), "
                f"{len(above_threshold)} above {args.min_imbalance*100:.0f}% imbalance.\n\n")
        f.write("Heavier side pays funding to lighter side. `recommended` = direction that COLLECTS carry. "
                "Pure-directional risk; pair-trade against a correlated pair for delta-neutral.\n\n")
        f.write("| Pair | Group | Imb | Rec | Long OI ($) | Short OI ($) | Last Px | Hist Long→Short |\n")
        f.write("|---|---|---:|---|---:|---:|---:|---:|\n")
        for r in rows[:args.top]:
            f.write(f"| {r['symbol']} | {r['group']} | {r['imbalance']*100:+.1f}% | {r['recommended_direction']} | "
                    f"${r['long_oi_usd']:,.0f} | ${r['short_oi_usd']:,.0f} | "
                    f"${r['last_price']:,.4f} | {r['historical_paid_to_shorts']:+.4f} |\n")

    out_json.write_text(json.dumps({"generated_at": ts, "pairs": rows}, indent=2, default=str))

    print(f"\nwrote {out_md}")
    print(f"wrote {out_json}")

    print(f"\n{'pair':<14} {'group':<12} {'imb':>7}  {'rec':>5}  {'long $':>12}  {'short $':>12}  hist L→S")
    for r in rows[:args.top]:
        print(f"{r['symbol']:<14} {(r['group'] or '?'):<12} {r['imbalance']*100:>+6.1f}%  "
              f"{r['recommended_direction']:>5}  "
              f"${r['long_oi_usd']:>11,.0f}  ${r['short_oi_usd']:>11,.0f}  {r['historical_paid_to_shorts']:+.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
