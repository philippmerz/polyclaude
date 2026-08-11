#!/usr/bin/env python3
"""Cross-EVENT logical-bound scanner (umbrella vs subset families).

Neither existing scanner covers this relation. polymarket_consistency_scan
works WITHIN one event (mutually-exclusive members must sum to ~1);
event_monotonicity_scan works WITHIN one event (date or threshold ladder).
But Polymarket also lists an UMBRELLA event alongside SUBSET events, and that
pair carries a hard logical bound:

    "any model scores >= k"  must be at least as likely as
    "any Anthropic Claude model scores >= k"

because the subset's winning states are a strict subset of the umbrella's.
So P(umbrella YES) >= P(subset YES) at every shared bar k. A violation is a
riskless structure:

    BUY umbrella-YES + BUY subset-NO,  cost a + b
      subset YES (=> umbrella YES):  1 + 0 = 1
      umbrella YES, subset NO:       1 + 1 = 2
      umbrella NO  (=> subset NO):   0 + 1 = 1
    payout is >= 1 in every state, so a + b < 1 is free money.

WHY THIS IS AD-HOC AND NOT DAEMON-WIRED (2026-08-10): the first family it was
written for (HLE, 7 events) showed an 8.5pp mid-violation that was ENTIRELY an
artifact of a 19pp-wide book — the umbrella leg quoted bid 0.41 / ask 0.60, so
its "mid" of 0.505 was never a tradeable price. At real asks the structure cost
1.03 before fees. Wiring a mid-based version into the 15-min daemon would have
fired phantoms on every wide-book leg, which is a cost I have already paid
twice (Montana duplicate members, WH per-day full-lid). So this walks live
books itself and prints the executable number, and it stays a CLI you point at
a family you already care about.

Fees are the other half of the story: the taker fee is 10% * min(p, 1-p), so a
pair of mid-priced legs pays ~9pp in fees and needs a >9pp gross violation
before it is worth crossing at all. The maker column shows what the same
structure is worth if both legs are rested instead (fee-free, fill not
guaranteed — and a half-filled arb is an outright directional position, which
for a subset leg like Claude is also a self-referential one).

CLI:
  cross_event_bound_scan.py --umbrella <event-slug> --subset <slug> [--subset ...]
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

from event_monotonicity_scan import parse_threshold

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"


def _rungs(slug: str) -> dict[float, dict]:
    ev = httpx.get(f"{GAMMA}/events", params={"slug": slug}, timeout=30).json()
    if not ev:
        print(f"# no event for slug {slug}", file=sys.stderr)
        return {}
    out: dict[float, dict] = {}
    for m in ev[0].get("markets", []):
        if m.get("closed"):
            continue
        t = parse_threshold(m.get("question") or "")
        prices = json.loads(m.get("outcomePrices") or "[]")
        if not t or not prices:
            continue
        out[t[0]] = {
            "yes_mid": float(prices[0]),
            "vol24": float(m.get("volume24hr") or 0),
            "tokens": json.loads(m.get("clobTokenIds") or "[]"),
            "outcomes": json.loads(m.get("outcomes") or "[]"),
            "slug": m.get("slug"),
        }
    return out


def _ask(row: dict, side: str) -> tuple[float | None, float]:
    """Best ask for one side, plus depth in shares."""
    try:
        tok = row["tokens"][row["outcomes"].index(side)]
        book = httpx.get(f"{CLOB}/book", params={"token_id": tok}, timeout=25).json()
        asks = sorted(book.get("asks", []), key=lambda x: float(x["price"]))
        if not asks:
            return None, 0.0
        return float(asks[0]["price"]), float(asks[0]["size"])
    except Exception:
        return None, 0.0


def _bid(row: dict, side: str) -> float | None:
    try:
        tok = row["tokens"][row["outcomes"].index(side)]
        book = httpx.get(f"{CLOB}/book", params={"token_id": tok}, timeout=25).json()
        bids = sorted(book.get("bids", []), key=lambda x: -float(x["price"]))
        return float(bids[0]["price"]) if bids else None
    except Exception:
        return None


def _market(slug: str) -> dict | None:
    r = httpx.get(f"{GAMMA}/markets", params={"slug": slug}, timeout=30).json()
    if not r:
        return None
    m = r[0]
    return {"yes_mid": float(json.loads(m["outcomePrices"])[0]),
            "tokens": json.loads(m.get("clobTokenIds") or "[]"),
            "outcomes": json.loads(m.get("outcomes") or "[]"),
            "question": m.get("question"), "vol24": float(m.get("volume24hr") or 0)}


def implication_pair(a_slug: str, b_slug: str, fee_rate: float) -> int:
    """A implies B  =>  P(A) <= P(B). Violation is riskless: BUY A-NO + BUY B-YES.

    Same payout table as the umbrella/subset case (A is the subset of states).
    Added 2026-08-11 because the standing GPT-6/Astra watch was being eyeballed
    on MIDPOINTS — "3pp, under the 8pp bar" is not a real number when one leg
    can be quoted inside a wide book. This makes the standing check a command.
    """
    A, B = _market(a_slug), _market(b_slug)
    if not A or not B:
        print("# could not load one or both markets", file=sys.stderr)
        return 2
    print(f"A: {A['question'][:78]}\n   YES mid {A['yes_mid']:.3f} (v24 ${A['vol24']:.0f})")
    print(f"B: {B['question'][:78]}\n   YES mid {B['yes_mid']:.3f} (v24 ${B['vol24']:.0f})")
    gap = (A["yes_mid"] - B["yes_mid"]) * 100
    print(f"\nbound: P(A) <= P(B).  mid gap = {gap:+.2f}pp "
          f"({'VIOLATION' if gap > 0 else 'consistent'})")
    a_ask, a_dep = _ask(A, "No")
    b_ask, b_dep = _ask(B, "Yes")
    if a_ask is None or b_ask is None:
        print("-> NO BOOK on one leg — mid-only, not executable")
        return 0
    fees = fee_rate * (min(a_ask, 1 - a_ask) + min(b_ask, 1 - b_ask))
    net = (1.0 - (a_ask + b_ask) - fees) * 100
    ab, bb = _bid(A, "No"), _bid(B, "Yes")
    maker_cost = (ab or 0) + 0.01 + (bb or 0) + 0.01
    print(f"A-NO ask {a_ask:.3f} x{a_dep:g}   B-YES ask {b_ask:.3f} x{b_dep:g}")
    print(f"TAKER: cost {a_ask + b_ask:.4f} + fees {fees:.4f} -> net {net:+.2f}pp"
          f"   ({'REAL ARB' if net > 0 else 'dead — spread/fees eat it'})")
    print(f"MAKER: both rested at bid+tick ~{maker_cost:.4f} -> net {(1 - maker_cost) * 100:+.2f}pp"
          f"   (fill NOT guaranteed; a half-fill is an outright directional position)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--implies", nargs=2, metavar=("A_SLUG", "B_SLUG"),
                    help="market slugs where A implies B (so P(A) must be <= P(B))")
    ap.add_argument("--umbrella", help="event slug of the 'any X' family")
    ap.add_argument("--subset", action="append",
                    help="event slug of a subset family (repeatable)")
    ap.add_argument("--min-violation-pp", type=float, default=1.0)
    ap.add_argument("--fee-bps", type=float, default=1000.0,
                    help="taker base fee in bps applied to min(p,1-p)")
    args = ap.parse_args()

    if args.implies:
        return implication_pair(args.implies[0], args.implies[1], args.fee_bps / 10000.0)
    if not (args.umbrella and args.subset):
        ap.error("need either --implies A B, or --umbrella with at least one --subset")

    umb = _rungs(args.umbrella)
    if not umb:
        return 2
    fee_rate = args.fee_bps / 10000.0
    n_mid = n_real = 0

    for sub_slug in args.subset:
        sub = _rungs(sub_slug)
        label = sub_slug.split("-on-humanitys")[0][:34]
        for bar in sorted(set(umb) & set(sub)):
            u, s = umb[bar], sub[bar]
            gap = (s["yes_mid"] - u["yes_mid"]) * 100
            if gap < args.min_violation_pp:
                continue
            n_mid += 1
            print(f"\n[MID VIOLATION {gap:+.1f}pp] bar>={bar:g}  {label}")
            print(f"   umbrella YES mid {u['yes_mid']:.3f} (v24 ${u['vol24']:.0f})  <  "
                  f"subset YES mid {s['yes_mid']:.3f} (v24 ${s['vol24']:.0f})")
            ua, ud = _ask(u, "Yes")
            sa, sd = _ask(s, "No")
            ub, sb = _bid(u, "Yes"), _bid(s, "No")
            if ua is None or sa is None:
                print("   -> NO BOOK on one leg — mid-only artifact, not executable")
                continue
            fees = fee_rate * (min(ua, 1 - ua) + min(sa, 1 - sa))
            taker_net = (1.0 - (ua + sa) - fees) * 100
            maker_cost = (ub or 0) + 0.01 + (sb or 0) + 0.01
            maker_net = (1.0 - maker_cost) * 100
            print(f"   umbrella-YES ask {ua:.3f} x{ud:g}   subset-NO ask {sa:.3f} x{sd:g}")
            print(f"   TAKER: cost {ua + sa:.4f} + fees {fees:.4f} -> net {taker_net:+.2f}pp"
                  f"   ({'REAL ARB' if taker_net > 0 else 'dead — spread/fees eat it'})")
            print(f"   MAKER: resting both at bid+tick costs ~{maker_cost:.4f} -> net {maker_net:+.2f}pp"
                  f"   (fill NOT guaranteed; a half-fill is an outright directional position)")
            if taker_net > 0:
                n_real += 1

    print(f"\n# {n_mid} mid violation(s); {n_real} executable after live-CLOB walk + fees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
