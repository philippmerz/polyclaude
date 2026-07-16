#!/usr/bin/env python3
"""Walk live CLOB books for short-dated sweep finalists. Both tokens per market:
best bid/ask, depth within 2pp of best ask, vwap to fill $10, net cost after taker fee.
"""
import json, sys, time
import httpx

BOOK = "https://clob.polymarket.com/book"

# (scored-row-index, side_to_buy)
FINALISTS = [
    (79, "NO"),   # cyclosporiasis >=10000
    (35, "NO"),   # cyclosporiasis >=5000
    (21, "YES"),  # Gemini Pro by Jul 31
    (33, "YES"),  # Gemini Pro by Jul 30 (cross-check)
    (19, "YES"),  # Sulyok out
    (8,  "YES"),  # Prime Video SDCC
    (9,  "YES"),  # Marvel SDCC
    (29, "YES"),  # Apple TV SDCC
    (44, "NO"),   # Studio Ghibli SDCC
    (48, "YES"),  # Moscow air traffic
    (63, "YES"),  # Israel action Greater Beirut by Jul 31
    (99, "NO"),   # Stripe 3rd valuation
    (53, "YES"),  # Pedro Pascal Hall H
]

def fill_price(levels, usd=10.0):
    """levels: asks sorted asc. Return (vwap_for_$usd, depth_usd_within_2pp_of_best)."""
    if not levels:
        return None, 0.0
    best = float(levels[0]["price"])
    depth = sum(float(l["price"]) * float(l["size"]) for l in levels
                if float(l["price"]) <= best + 0.02)
    left = usd; cost = 0.0; shares = 0.0
    for l in levels:
        p, s = float(l["price"]), float(l["size"])
        take_usd = min(left, p * s)
        cost += take_usd; shares += take_usd / p; left -= take_usd
        if left <= 0:
            break
    vwap = cost / shares if shares and left <= 0 else None
    return vwap, depth

def main():
    rows = [json.loads(l) for l in open('/tmp/shortdated_sweep/scored.jsonl')]
    out = []
    with httpx.Client(timeout=20) as c:
        for idx, side in FINALISTS:
            r = rows[idx]
            toks = json.loads(r["clobTokenIds"])
            yes_tok, no_tok = toks[0], toks[1]
            rec = {"idx": idx, "q": r["q"], "slug": r["slug"], "side": side,
                   "fee_bps": r.get("takerBaseFee") or 0, "dte": r["dte"],
                   "vol": round(r["volumeNum"]), "gamma_p": r["p_yes"],
                   "conditionId": r["conditionId"], "clobTokenIds": r["clobTokenIds"]}
            for name, tok in (("yes", yes_tok), ("no", no_tok)):
                for attempt in range(4):
                    try:
                        resp = c.get(BOOK, params={"token_id": tok})
                        if resp.status_code == 429:
                            time.sleep(2 * (attempt + 1)); continue
                        b = resp.json()
                        bids = sorted(b.get("bids", []), key=lambda x: -float(x["price"]))
                        asks = sorted(b.get("asks", []), key=lambda x: float(x["price"]))
                        vwap10, depth2pp = fill_price(asks)
                        rec[name] = {
                            "bid": float(bids[0]["price"]) if bids else None,
                            "ask": float(asks[0]["price"]) if asks else None,
                            "ask_vwap_$10": round(vwap10, 4) if vwap10 else None,
                            "ask_depth2pp_$": round(depth2pp, 0),
                        }
                        break
                    except Exception:
                        time.sleep(1.5 * (attempt + 1))
                else:
                    rec[name] = {"error": "failed"}
                time.sleep(0.35)
            s = rec.get(side.lower()) or {}
            ask = s.get("ask"); fee_bps = rec["fee_bps"]
            if ask is not None:
                fee = fee_bps / 10000.0 * min(ask, 1 - ask)
                rec["exec_cost_net"] = round(ask + fee, 4)
            out.append(rec)
            print(json.dumps({k: rec[k] for k in rec if k not in ("conditionId", "clobTokenIds")}), flush=True)
    with open('/tmp/shortdated_sweep/book_finalists.jsonl', 'w') as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")

if __name__ == "__main__":
    main()
