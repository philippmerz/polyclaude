"""Place the initial 4-position short-horizon sleeve. See research/_short_initial.md."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from polyclaude_client import Polyclaude  # type: ignore

LOG_DIR = Path("<PROJECT>/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# (label, token_id, side, plan_limit, usd_size, slug)
PLAN: list[tuple[str, str, str, float, float, str]] = [
    ("Iran-peace May31 NO", "42918220085288219341491829385501246298233444593663440094436147850542032590016", "BUY", 0.67,  7.0, "us-x-iran-permanent-peace-deal-by-may-31-2026-333"),
    ("Latvia top10 NO",     "84808556359071914967263506000259998857147664764718810872873752456867359642110", "BUY", 0.83,  5.0, "will-latvia-be-in-the-top-10-at-eurovision-2026"),
    ("Atletico top4 YES",   "100952291322678954514417231357111610948515892742954751932425813530604840075554", "BUY", 0.99,  5.0, "will-atletico-madrid-finish-in-the-top-4-of-the-la-liga-202526-standings"),
    ("Amy Acton YES",       "45282920959193141979506939608658828232463179670129495742906083036305009865038",  "BUY", 0.987, 5.0, "will-amy-acton-win-the-2026-ohio-governor-democratic-primary-election"),
]


def main() -> None:
    pc = Polyclaude.load()
    print("--- short-sleeve plan ---")
    for label, _tid, side, price, size, _slug in PLAN:
        print(f"  {label:24s}  {side} limit @ {price:.4f}  size ${size:.2f}")

    receipts: list[dict] = []
    for label, tid, side, plan_price, usd_size, slug in PLAN:
        ob = pc.orderbook(tid)
        if not ob["asks"]:
            print(f"\n[{label}] no asks; SKIP")
            continue
        best_ask = sorted(ob["asks"])[0][0]
        # Pay no more than plan_price + 1c; if best_ask is below plan, take best_ask
        limit = best_ask if best_ask <= plan_price + 0.0001 else plan_price + 0.005
        limit = round(limit, 4)
        print(f"\n[{label}] best ask {best_ask}  plan {plan_price}  -> limit {limit}  size ${usd_size}")
        try:
            resp = pc.place_limit_buy(tid, price=limit, usd_size=usd_size, gtc=True)
            print(f"  resp: {resp}")
            receipts.append({"label": label, "slug": slug, "token_id": tid, "limit": limit, "usd_size": usd_size, "best_ask_at_place": best_ask, "resp": resp})
        except Exception as e:
            print(f"  ERROR: {e}")
            receipts.append({"label": label, "slug": slug, "token_id": tid, "limit": limit, "usd_size": usd_size, "error": str(e)})

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = LOG_DIR / f"orders_short_{ts}.json"
    out.write_text(json.dumps(receipts, indent=2, default=str))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
