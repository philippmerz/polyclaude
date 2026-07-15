#!/usr/bin/env python3
"""Walk live CLOB books for finalist candidates. For each market: both tokens,
best bid/ask, and the price to fill $10 notional on the side we want to BUY.
"""
import json, sys, time
import httpx

BOOK = "https://clob.polymarket.com/book"

# (scored-row-index, side_to_buy)  side is 'YES' or 'NO'
FINALISTS = [
    (24, "NO"), (52, "NO"), (1016, "YES"), (131, "NO"), (3, "NO"),
    (314, "NO"), (145, "NO"), (8, "NO"), (115, "NO"), (324, "YES"),
    (79, "NO"), (17, "YES"), (23, "NO"), (236, "YES"),
]

def fill_price(levels, usd=10.0):
    """levels: list of {price,size} asks sorted asc. Return (vwap, depth_usd_at_best2pp)."""
    if not levels:
        return None, 0.0
    best = float(levels[0]["price"])
    # depth within 2pp of best
    depth = sum(float(l["price"]) * float(l["size"]) for l in levels
                if float(l["price"]) <= best + 0.02)
    # vwap to fill $usd
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
    rows = [json.loads(l) for l in open('/tmp/instance_sweep/scored.jsonl')]
    out = []
    with httpx.Client(timeout=20) as c:
        for idx, side in FINALISTS:
            r = rows[idx]
            toks = json.loads(r["clobTokenIds"])
            yes_tok, no_tok = toks[0], toks[1]
            rec = {"idx": idx, "q": r["q"], "slug": r["slug"], "side": side,
                   "fee_bps": r.get("takerBaseFee") or 0, "dte": r["dte"],
                   "vol": r["volumeNum"], "gamma_p": r["p_yes"]}
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
                    except Exception as e:
                        time.sleep(1.5 * (attempt + 1))
                else:
                    rec[name] = {"error": "failed"}
                time.sleep(0.35)
            # executable summary for the side we want
            s = rec.get(side.lower()) or {}
            ask = s.get("ask"); fee_bps = rec["fee_bps"]
            if ask is not None:
                fee = fee_bps / 10000.0 * min(ask, 1 - ask)
                rec["exec_cost_net"] = round(ask + fee, 4)
            out.append(rec)
            print(json.dumps(rec), flush=True)
    with open('/tmp/instance_sweep/book_finalists.jsonl', 'w') as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")

if __name__ == "__main__":
    main()
