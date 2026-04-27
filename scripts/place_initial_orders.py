"""Place the initial 5-position carry portfolio.

Reads current best ask, places GTC limit BUY orders on the NO token at
min(plan_price, best_ask + 1tick) so we fill near-instantly given depth.
Logs receipts to logs/orders_<ts>.json (gitignored).
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from polyclaude_client import Polyclaude  # type: ignore

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# (label, NO-token-id, plan_limit, usd_size, slug)
PLAN = [
    ("Jesus NO",       "51797157743046504218541616681751597845468055908324407922581755135522797852101", 0.962, 10.0, "will-jesus-christ-return-before-2027"),
    ("Pahlavi NO",     "96214953624495509683027302209340859673097705517450500531670409012928242777230", 0.910, 10.0, "will-reza-pahlavi-lead-iran-in-2026"),
    ("Aliens NO",      "7305630249804085635496399869905769372294302716159034447326228509068694952392",  0.802, 9.0,  "will-the-us-confirm-that-aliens-exist-before-2027-789-924-249"),
    ("Trump-out NO",   "2849827372590072151380088930233312280478318575453624773762283369907909283027",  0.842, 7.0,  "trump-out-as-president-before-2027"),
    ("Iran-regime NO", "106181075047366745139197108801635573283215248045056329679360376976893016488727", 0.802, 7.0,  "will-the-iranian-regime-fall-by-the-end-of-2026"),
]


def main() -> None:
    pc = Polyclaude.load()
    print("--- portfolio plan ---")
    for label, _tid, price, size, _slug in PLAN:
        print(f"  {label:18s}  buy NO  limit @ {price:.3f}  size ${size:.2f}")

    receipts: list[dict] = []
    for label, tid, plan_price, usd_size, slug in PLAN:
        ob = pc.orderbook(tid)
        if not ob["asks"]:
            print(f"[skip] {label}: empty ask side")
            continue
        # asks were returned descending in _client.orderbook; sort ascending
        asks_sorted = sorted(ob["asks"])
        best_ask = asks_sorted[0][0]
        # take the lower of plan_price or best_ask + 1tick (1c)
        # but never pay more than plan_price + 1tick
        limit = min(plan_price, best_ask + 0.01)
        # never place an order strictly below best_ask if best_ask < plan_price (we'd just wait forever
        # and miss); prefer to step up to best_ask if it's tight.
        if best_ask <= plan_price:
            limit = best_ask
        print(f"\n[{label}] best ask {best_ask}  plan {plan_price}  -> limit {limit:.4f}  size ${usd_size}")
        try:
            resp = pc.place_limit_buy(tid, price=round(limit, 4), usd_size=usd_size, gtc=True)
            print(f"  resp: {resp}")
            receipts.append({"label": label, "slug": slug, "token_id": tid, "limit": limit, "usd_size": usd_size, "best_ask_at_place": best_ask, "resp": resp})
        except Exception as e:
            print(f"  ERROR: {e}")
            receipts.append({"label": label, "slug": slug, "token_id": tid, "limit": limit, "usd_size": usd_size, "error": str(e)})

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = LOG_DIR / f"orders_{ts}.json"
    out.write_text(json.dumps(receipts, indent=2, default=str))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
