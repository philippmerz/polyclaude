#!/usr/bin/env python3
"""Polymarket event-monotonicity arbitrage scanner.

Polymarket has multi-market EVENTS (e.g. "Will X happen by Y?" with child
markets for different dates like by-May-15 / by-May-31 / by-June-30). For
event A occurring at time t (or before) on monotonic dates t1 < t2:

    P(A by t2) >= P(A by t1)

If prices on the YES side violate this (i.e., YES_t1 > YES_t2 + tolerance),
that's a pure decomposition arb:
- Buy YES_t2 (cheap) + Sell YES_t1 (expensive)
- If A happens by t1: YES_t1 wins (we paid 1.0 to the buyer); YES_t2 also wins
  (we receive 1.0 from the seller)
- If A happens between t1 and t2: only YES_t2 wins; we paid YES_t1 - YES_t2 < 0
  → we keep the spread
- If A doesn't happen by t2: neither wins; we keep the spread (sold YES_t1
  for more than we paid for YES_t2)

Profit per share = (price_YES_t1 - price_YES_t2) - fees, guaranteed.

This script:
1. Fetches active Polymarket events via gamma-api /events
2. For each event with 2+ markets, extracts (endDate, YES_price, slug)
3. Sorts markets by endDate
4. Flags monotonicity violations beyond tolerance (default 1pp)
5. Outputs: violation details + spread + fee-aware breakeven

Lesson source: operator suggestion 2026-05-15 — Polymarket UI glitched
showing June-30 < May-15 transiently. False alarm in that instance but
the GENERAL pattern of monotonicity violations is real arb if they occur.

Usage:
    python scripts/event_monotonicity_scan.py
    python scripts/event_monotonicity_scan.py --min-violation-pp 2
    python scripts/event_monotonicity_scan.py --json
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys

import httpx

POLYMARKET_FEE_RATE = 0.072  # edge-aware fee


def fetch_events(min_vol: float = 1000, max_pages: int = 15) -> list[dict]:
    out: list[dict] = []
    seen = set()
    with httpx.Client(timeout=20) as c:
        for page in range(max_pages):
            try:
                r = c.get("https://gamma-api.polymarket.com/events", params={
                    "closed": "false", "active": "true",
                    # gamma caps pages at 100; offset stride must match the cap,
                    # not the requested limit, else pages skip 80% (verified 2026-06-06).
                    "limit": 100, "offset": page * 100,
                    "order": "volume24hr", "ascending": "false",
                })
                r.raise_for_status()
            except Exception as e:
                print(f"events page {page} err: {e}", file=sys.stderr)
                continue
            data = r.json() or []
            if not data:
                break
            for ev in data:
                eid = ev.get("id")
                if not eid or eid in seen:
                    continue
                seen.add(eid)
                if (ev.get("volume24hr", 0) or 0) < min_vol:
                    continue
                if ev.get("closed"):
                    continue
                out.append(ev)
    return out


def parse_outcome_prices(p) -> tuple[float, float] | None:
    try:
        if isinstance(p, str):
            parsed = json.loads(p)
        else:
            parsed = p
        if isinstance(parsed, list) and len(parsed) >= 2:
            return float(parsed[0]), float(parsed[1])
    except Exception:
        pass
    return None


def fee_aware_breakeven(yes_t1: float, yes_t2: float) -> float:
    """Fee-aware breakeven spread needed to profit on the arb.

    We BUY yes_t2 (paying yes_t2 + fee) and SELL yes_t1 (receiving yes_t1 - fee).
    Polymarket edge-aware fee = 0.072 × min(p, 1-p).
    Need: (yes_t1 - sell_fee) - (yes_t2 + buy_fee) > 0
    => yes_t1 - yes_t2 > sell_fee + buy_fee
    """
    sell_fee = POLYMARKET_FEE_RATE * min(yes_t1, 1 - yes_t1)
    buy_fee = POLYMARKET_FEE_RATE * min(yes_t2, 1 - yes_t2)
    return sell_fee + buy_fee


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--min-violation-pp", type=float, default=1.0,
                   help="Minimum violation in pp to flag (default 1pp).")
    p.add_argument("--min-event-vol24", type=float, default=1000,
                   help="Skip events with vol24hr below this (default $1k).")
    p.add_argument("--min-leg-vol24", type=float, default=500,
                   help="Require BOTH legs of a pair to have >= this 24h volume "
                        "(default $500). Filters stale-midpoint stub artifacts on "
                        "illiquid markets that aren't executable arbs.")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    print(f"# event_monotonicity_scan: fetching active events with vol24hr >= ${args.min_event_vol24}", file=sys.stderr)
    events = fetch_events(min_vol=args.min_event_vol24)
    print(f"# {len(events)} events to inspect", file=sys.stderr)

    violations = []
    multi_market_events = 0
    for ev in events:
        markets = ev.get("markets", [])
        if len(markets) < 2:
            continue
        # Extract (end_date, yes_price, slug, market_id, question)
        market_rows = []
        for m in markets:
            if m.get("closed"):
                continue
            if m.get("umaResolutionStatus") in ("proposed", "disputed", "resolved"):
                continue
            prices = parse_outcome_prices(m.get("outcomePrices"))
            if not prices:
                continue
            end_iso = m.get("endDate") or m.get("endDateIso")
            if not end_iso:
                continue
            try:
                end_dt = datetime.datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
            except Exception:
                continue
            market_rows.append({
                "end_dt": end_dt,
                "yes": prices[0],
                "no": prices[1],
                "slug": m.get("slug"),
                "market_id": m.get("id"),
                "question": m.get("question"),
                "vol24hr": float(m.get("volume24hr", 0) or 0),
            })
        if len(market_rows) < 2:
            continue
        multi_market_events += 1
        market_rows.sort(key=lambda r: r["end_dt"])

        # Check monotonicity: for i<j, yes[i] should be <= yes[j]
        # ONLY for date-monotonic events: require DIFFERENT end dates between
        # pairs. Same-date markets are usually categorical/threshold (e.g.
        # "temperature above X°F today" or "BTC above Y on date Z" with
        # different thresholds) — NOT monotonic arbs.
        for i in range(len(market_rows)):
            for j in range(i + 1, len(market_rows)):
                if market_rows[i]["end_dt"] >= market_rows[j]["end_dt"]:
                    continue  # not a proper monotonic pair
                # Heuristic: require event title to contain a "by ___" pattern
                # (the placeholder for date variability). Otherwise might still
                # be categorical even with different dates (e.g. event spanning
                # multiple weekly games has different end dates but isn't monotonic).
                title_low = (ev.get("title") or "").lower()
                if " by " not in title_low and "before " not in title_low:
                    continue
                # Liquidity gate: a leg with ~no recent volume has a STALE gamma
                # midpoint (sits between a stub bid and no real ask), so the
                # "violation" is an artifact, not an executable arb. Require both
                # legs to have real 24h volume. (Lesson 2026-06-02: "Propr launch
                # a token" flagged +37.5pp but the t2 leg had $0 vol24hr — stub.)
                if (market_rows[i]["vol24hr"] < args.min_leg_vol24 or
                        market_rows[j]["vol24hr"] < args.min_leg_vol24):
                    continue
                vt1 = market_rows[i]["yes"]
                vt2 = market_rows[j]["yes"]
                violation_pp = (vt1 - vt2) * 100
                if violation_pp < args.min_violation_pp:
                    continue
                # arb math: spread yes_t1 - yes_t2, vs fee breakeven
                breakeven = fee_aware_breakeven(vt1, vt2)
                spread = (vt1 - vt2) - breakeven
                violations.append({
                    "event_title": ev.get("title", "?"),
                    "event_slug": ev.get("slug", "?"),
                    "t1_question": market_rows[i]["question"],
                    "t1_slug": market_rows[i]["slug"],
                    "t1_end": market_rows[i]["end_dt"].strftime("%Y-%m-%d"),
                    "t1_yes": vt1,
                    "t2_question": market_rows[j]["question"],
                    "t2_slug": market_rows[j]["slug"],
                    "t2_end": market_rows[j]["end_dt"].strftime("%Y-%m-%d"),
                    "t2_yes": vt2,
                    "violation_pp": round(violation_pp, 2),
                    "breakeven_pp": round(breakeven * 100, 2),
                    "net_spread_pp": round(spread * 100, 2),
                    "t1_vol24hr": round(market_rows[i]["vol24hr"], 0),
                    "t2_vol24hr": round(market_rows[j]["vol24hr"], 0),
                })

    # Sort by net_spread_pp desc (largest profit first)
    violations.sort(key=lambda v: -v["net_spread_pp"])

    if args.json:
        print(json.dumps({"violations": violations, "events_inspected": multi_market_events}, indent=2))
        return 0

    print(f"\n# {multi_market_events} multi-market events inspected, {len(violations)} monotonicity violations >= {args.min_violation_pp}pp\n")
    if not violations:
        print("(no violations)")
        return 0
    print(f"{'event_title':<50} {'t1':<12} {'t2':<12} {'YES_t1':<7} {'YES_t2':<7} {'gross':<7} {'BE':<6} {'net':<7}")
    print("-" * 120)
    for v in violations[:30]:
        print(f"{v['event_title'][:50]:<50} {v['t1_end']:<12} {v['t2_end']:<12} {v['t1_yes']:<7.4f} {v['t2_yes']:<7.4f} {v['violation_pp']:>+5.2f}pp {v['breakeven_pp']:>4.2f}pp {v['net_spread_pp']:>+5.2f}pp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
