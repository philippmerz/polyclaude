#!/usr/bin/env python3
"""Polymarket event-monotonicity arbitrage scanner.

TWO ladder shapes are checked (2026-08-10: the threshold pass was added after
finding the scanner could only ever see the date one):

  DATE ladder — "Will X happen by Y?" across by-May-15 / by-May-31 / by-Jun-30.
  THRESHOLD ladder — one deadline, a rising bar: HLE >=50/55/60/65/70,
    "FDV above $50M/$500M/$1B", vote share, temperature. For thresholds
    k1 < k2, P(X >= k2) <= P(X >= k1) — as monotone as the date case, and the
    arb construction is identical with "harder bar" in the role of "earlier
    date". These are common on Polymarket, and the scanner had the machinery
    to check them while explicitly skipping them as "categorical".

For event A occurring at time t (or before) on monotonic dates t1 < t2:

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
import re
import sys

import httpx

import pm_fees  # per-market Gamma feeSchedule; see pm_fees.py for source-of-truth rules


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


POLYMARKET_CLOB = "https://clob.polymarket.com"


# A magnitude suffix MUST be captured and applied, never merely skipped.
# 2026-08-10, first live run of the threshold pass: an earlier version only
# refused to CONSUME "million"/"billion", which for the leading-comparator
# patterns ("above $1B") still returned the bare number. So "$1B" parsed as
# 1.0 and "$50M" as 50.0, inverting a perfectly-priced FDV ladder and
# manufacturing SIX "REAL ARB" fires that survived the live-CLOB walk — the
# books were real, the ORDERING was fabricated. Third instance of the same
# class (Montana duplicate members, WH per-day full-lid): a parse that groups
# non-comparable things as comparable. The CLOB walk cannot rescue a bad
# parse, so the parse carries the safety burden alone.
_SCALES = {"k": 1e3, "thousand": 1e3,
           "m": 1e6, "mm": 1e6, "mln": 1e6, "million": 1e6,
           "b": 1e9, "bn": 1e9, "billion": 1e9,
           "t": 1e12, "trillion": 1e12}
_SCALE_RE = r"(?P<scale>mln|mm|million|billion|trillion|thousand|bn|[kmbt])"
# Try the magnitude suffix first, then fall back to a plain unit (%/°F/bps/
# seats). Alternation order is what makes "$1B" scale and "95F" not.
_NUM = rf"\$?(?P<val>[0-9][0-9,]*(?:\.[0-9]+)?)(?:\s*{_SCALE_RE}\b|\s*(?:%|°?[a-z]{{1,10}}))?"
_UP_WORDS = r"(?:or higher|or more|or greater|or above|or over)"
_DN_WORDS = r"(?:or lower|or less|or fewer|or below|or under)"
_UP_LEAD = r"(?:at least|above|over|greater than|more than|exceeds?)"
_DN_LEAD = r"(?:at most|below|under|less than|fewer than)"


def parse_threshold(question: str) -> tuple[float, int] | None:
    """Extract (value, direction) from a THRESHOLD-ladder question.

    direction +1 = "value or higher" (a HARDER bar as value rises, so YES must
    be non-increasing in value); -1 = "value or lower" (YES non-decreasing).

    The number MUST be anchored to an explicit comparator. That is the whole
    safety property: it rejects exact-value buckets ("will X win 3 seats"),
    which are a PARTITION and carry no monotone constraint, and it stops the
    scan from grabbing an unrelated number like the year in "...on HLE in 2026
    be 50% or higher?" — where an any-number parse would read 2026 as the bar.
    Same failure family as the Montana dedup and the WH per-day exclusion: a
    grouping heuristic treating a non-fungible structure as fungible.
    """
    q = " ".join((question or "").lower().split())
    if not q:
        return None
    for pat, direction in ((rf"{_NUM}\s*{_UP_WORDS}", +1),
                           (rf"{_NUM}\s*{_DN_WORDS}", -1),
                           (rf"{_UP_LEAD}\s*{_NUM}", +1),
                           (rf"{_DN_LEAD}\s*{_NUM}", -1)):
        m = re.search(pat, q)
        if m:
            try:
                val = float(m.group("val").replace(",", ""))
            except Exception:
                return None
            scale = (m.groupdict().get("scale") or "").strip()
            if scale:
                val *= _SCALES[scale]
            return val, direction
    return None


def _best_ask(token_id: str) -> float | None:
    """Lowest executable ask for a CLOB token (what you'd PAY to buy). Returns
    None if the book is empty/unreachable."""
    try:
        r = httpx.get(f"{POLYMARKET_CLOB}/book", params={"token_id": str(token_id)}, timeout=10)
        r.raise_for_status()
        asks = [float(a["price"]) for a in (r.json().get("asks") or []) if a.get("price")]
        return min(asks) if asks else None
    except Exception:
        return None


def _fee_market_from_row(row: dict) -> dict | None:
    """Return the best fee payload carried by a scanner row.

    New rows retain Gamma's complete fee inputs so ``pm_fees`` can honor
    ``feeSchedule.rate``, ``exponent``, and ``takerOnly``.  The legacy fallback
    keeps hand-built rows and old cached scanner fixtures working: an explicit
    ``taker_fee_bps=None`` is a known zero-fee market, while a row with no fee
    information at all is unknown and therefore receives pm_fees' conservative
    fallback.
    """
    if "fee_market" in row:
        fee_market = row.get("fee_market")
        return fee_market if isinstance(fee_market, dict) else None
    if "fee_schedule" in row:
        return {
            "feeSchedule": row.get("fee_schedule"),
            "takerBaseFee": row.get("taker_fee_bps"),
        }
    if "taker_fee_bps" in row:
        return {"takerBaseFee": row.get("taker_fee_bps")}
    return None


def _executable_monotonic_arb(row_early: dict, row_late: dict) -> dict | None:
    """LIVE-CLOB validation (2026-07-23): the monotonicity flag uses gamma
    MIDPOINTS, which sit between stub bids and real asks — the 2026-07-23
    outage surfaced a 3-hour 'actionable' false alarm (Elon-tweet-Hyperliquid:
    flagged +11.25pp on mids, but the earlier YES was 0.024 bid / 0.377 ask =
    no real price). The riskless capture of an (earlier_YES > later_YES)
    violation is BUY later_YES + BUY earlier_NO (min payoff 1.0 in every
    world). It's a real arb only if the EXECUTABLE cost of that pair, incl.
    taker fees, is < 1.0. This walks both books and returns the true edge or
    None if unexecutable."""
    try:
        late_tokens = json.loads(row_late.get("clob_tokens") or "[]")
        early_tokens = json.loads(row_early.get("clob_tokens") or "[]")
    except Exception:
        return None
    if len(late_tokens) != 2 or len(early_tokens) != 2:
        return None
    late_yes_ask = _best_ask(late_tokens[0])     # buy later YES
    early_no_ask = _best_ask(early_tokens[1])    # buy earlier NO
    if late_yes_ask is None or early_no_ask is None:
        return None
    # Both orders cross the book, so each pays its market's taker curve.  Pass
    # the complete Gamma fee payload through the shared source of truth: the
    # legacy inline formula ignored feeSchedule and even used the superseded
    # linear-at-the-tails curve.
    fee = (
        pm_fees.fee_per_share(_fee_market_from_row(row_late), late_yes_ask)
        + pm_fees.fee_per_share(_fee_market_from_row(row_early), early_no_ask)
    )
    cost = late_yes_ask + early_no_ask + fee
    return {"late_yes_ask": late_yes_ask, "early_no_ask": early_no_ask,
            "fee": round(fee, 4), "exec_cost": round(cost, 4),
            "exec_edge_pp": round((1.0 - cost) * 100, 2)}


_UNSET = object()   # "caller supplied nothing" — distinct from takerBaseFee=None,
                    # which is a real value meaning THIS MARKET CHARGES NO FEE.
                    # Collapsing the two charged zero-fee legs a 10% phantom fee
                    # and suppressed genuine arbs (caught by tests/test_money_math.py
                    # minutes after the suite first existed, in code written the
                    # same hour as the lesson warning against this exact mixup).


def fee_aware_breakeven(yes_t1: float, yes_t2: float,
                        bps_t1=_UNSET, bps_t2=_UNSET) -> float:
    """Fee-aware breakeven spread needed to profit on the arb.

    We BUY yes_t2 (paying yes_t2 + fee) and SELL yes_t1 (receiving yes_t1 - fee).
    ``bps_t1`` and ``bps_t2`` retain their historical public meaning: a scalar
    is treated as legacy ``takerBaseFee`` and explicit None means fee-free.
    Callers may now pass a complete Gamma market dict instead, which lets
    ``pm_fees`` consume the authoritative feeSchedule rate and exponent.

    2026-08-14: this used a hard-coded 0.072 while the live modal rate is 0.10
    (84/100 active markets; the other 16 charge nothing). Understating the fee
    by 28% in an ARB breakeven is the worst possible place for that error — it
    lowers the bar a violation must clear, which manufactures arbs that lose
    money on execution. The two legs can also carry DIFFERENT rates, which a
    single constant cannot express at all. market_rows already carried
    taker_fee_bps; it simply was not being read.
    """
    def _market(value):
        if value is _UNSET:
            return None  # unknown/unfetched: conservative pm_fees fallback
        if isinstance(value, dict):
            return value
        return {"takerBaseFee": value}

    sell_fee = pm_fees.fee_per_share(_market(bps_t1), yes_t1)
    buy_fee = pm_fees.fee_per_share(_market(bps_t2), yes_t2)
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
                "clob_tokens": m.get("clobTokenIds"),
                "taker_fee_bps": m.get("takerBaseFee"),
                # Keep the complete structured source of truth.  The legacy
                # scalar remains above for old consumers and cached fixtures.
                "fee_market": {
                    "takerBaseFee": m.get("takerBaseFee"),
                    "feeSchedule": m.get("feeSchedule"),
                },
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
                # PER-DAY exclusion (2026-08-08): "by <TIME>" is a time-of-day
                # bar on INDEPENDENT days, not a cumulative date series — e.g.
                # "full lid by 6:30 PM" for Aug-10 vs Aug-11 are separate daily
                # events with no monotonicity constraint (Monday's probability
                # may legitimately exceed Tuesday's). The scan's first daemon
                # fire was exactly this false positive (+41.5pp "violation").
                # Same root as Montana-dedup: a grouping heuristic treating a
                # non-fungible structure as fungible.
                import re as _re
                if _re.search(r"by \d{1,2}(:\d{2})?\s*(am|pm)", title_low):
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
                breakeven = fee_aware_breakeven(vt1, vt2,
                                               market_rows[i]["fee_market"],
                                               market_rows[j]["fee_market"])
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
                    # row refs for the live-CLOB validation pass (i=earlier, j=later)
                    "_row_early": market_rows[i],
                    "_row_late": market_rows[j],
                })

        # THRESHOLD-LADDER pass (2026-08-10). The date pass above deliberately
        # skips same-date families, and its comment called them "categorical/
        # threshold ... NOT monotonic arbs". That is half wrong, and the wrong
        # half is large: a THRESHOLD ladder is exactly as monotone as a date
        # ladder. For thresholds k1 < k2, P(X >= k2) <= P(X >= k1), and the arb
        # construction is identical with "harder bar" playing the role of
        # "earlier date". Polymarket runs these constantly — score ladders
        # (HLE 50/55/60/65/70), BTC price ladders, vote-share, temperature —
        # so the scanner was structurally blind to a whole population it had
        # the machinery to check. Found while pricing the HLE family, whose own
        # ladder showed a (sub-spread) inversion at the 65/70 rungs.
        same_day = len({r["end_dt"].date() for r in market_rows}) == 1
        parsed = [(r, parse_threshold(r["question"])) for r in market_rows]
        rungs = [(r, t[0], t[1]) for r, t in parsed if t]
        dirs = {d for _, _, d in rungs}
        # Require: one consistent comparator direction, every leg parsed (a
        # partially-parsed event is a mixed structure, not a ladder), distinct
        # values, and a shared deadline so this never double-reports the date
        # pass's pairs.
        if (same_day and len(rungs) >= 2 and len(rungs) == len(market_rows)
                and len(dirs) == 1 and len({v for _, v, _ in rungs}) == len(rungs)):
            direction = dirs.pop()
            # Order by DIFFICULTY: hardest bar first. For a ">=" ladder the
            # hardest is the largest value; for "<=" it is the smallest.
            rungs.sort(key=lambda x: x[1], reverse=(direction > 0))
            for i in range(len(rungs)):
                for j in range(i + 1, len(rungs)):
                    hard_row, hard_v, _ = rungs[i]
                    easy_row, easy_v, _ = rungs[j]
                    if (hard_row["vol24hr"] < args.min_leg_vol24 or
                            easy_row["vol24hr"] < args.min_leg_vol24):
                        continue
                    # The HARDER bar must not price above the EASIER one.
                    vt1, vt2 = hard_row["yes"], easy_row["yes"]
                    violation_pp = (vt1 - vt2) * 100
                    if violation_pp < args.min_violation_pp:
                        continue
                    breakeven = fee_aware_breakeven(vt1, vt2,
                                               hard_row["fee_market"],
                                               easy_row["fee_market"])
                    violations.append({
                        "event_title": ev.get("title", "?"),
                        "event_slug": ev.get("slug", "?"),
                        "kind": "threshold",
                        "t1_question": hard_row["question"],
                        "t1_slug": hard_row["slug"],
                        "t1_end": f"bar>={hard_v}" if direction > 0 else f"bar<={hard_v}",
                        "t1_yes": vt1,
                        "t2_question": easy_row["question"],
                        "t2_slug": easy_row["slug"],
                        "t2_end": f"bar>={easy_v}" if direction > 0 else f"bar<={easy_v}",
                        "t2_yes": vt2,
                        "violation_pp": round(violation_pp, 2),
                        "breakeven_pp": round(breakeven * 100, 2),
                        "net_spread_pp": round(((vt1 - vt2) - breakeven) * 100, 2),
                        "t1_vol24hr": round(hard_row["vol24hr"], 0),
                        "t2_vol24hr": round(easy_row["vol24hr"], 0),
                        # same role mapping as the date pass: _row_early is the
                        # leg that SHOULD carry the lower YES.
                        "_row_early": hard_row,
                        "_row_late": easy_row,
                    })

    # Sort by net_spread_pp desc (largest profit first)
    violations.sort(key=lambda v: -v["net_spread_pp"])

    # LIVE-CLOB VALIDATION (2026-07-23): walk real books on each mid-flagged
    # violation — the midpoint spread is NOT executable. Keep the mid-flag as
    # a candidate list but split REAL (executable arb after fees) from ARTIFACT.
    n_mid = len(violations)
    real = []
    for v in violations:
        ex = _executable_monotonic_arb(v["_row_early"], v["_row_late"])
        if ex is not None:
            v["executable"] = ex
            if ex["exec_edge_pp"] > 0:
                real.append(v)
    for v in violations:
        v.pop("_row_early", None); v.pop("_row_late", None)

    if args.json:
        print(json.dumps({"violations": violations, "real_executable": real,
                          "events_inspected": multi_market_events}, indent=2))
        return 0

    print(f"\n# {multi_market_events} multi-market events inspected; {n_mid} midpoint violation(s) >= {args.min_violation_pp}pp; "
          f"{len(real)} REAL after live-CLOB walk\n")
    if not violations:
        print("(no violations)")
        return 0
    print(f"{'event_title':<44} {'t1':<11} {'t2':<11} {'mid_gross':<9} {'EXEC_edge':<9} {'verdict'}")
    print("-" * 110)
    for v in violations[:30]:
        ex = v.get("executable")
        exec_s = f"{ex['exec_edge_pp']:>+6.2f}pp" if ex else "  n/a  "
        verdict = ("REAL ARB" if ex and ex["exec_edge_pp"] > 0
                   else "ARTIFACT (mid-only)" if ex else "no book")
        print(f"{v['event_title'][:44]:<44} {v['t1_end']:<11} {v['t2_end']:<11} "
              f"{v['violation_pp']:>+6.2f}pp {exec_s:<9} {verdict}")
    if not real:
        print("\n# 0 REAL executable arbs — all midpoint flags evaporated on live books (the usual outcome).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
