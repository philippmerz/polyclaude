#!/usr/bin/env python3
"""Walk live CLOB books for SDCC finalists. For each market print both tokens:
best bid/ask, depth-usd within 2pp of best ask, vwap to fill $8, net cost after taker fee.
Input: /tmp/redeploy_sweep/sdcc_walk_in.jsonl
"""
import json, sys, time
import httpx

BOOK = "https://clob.polymarket.com/book"

def fill(levels, usd=8.0):
    if not levels:
        return None, 0.0
    best = float(levels[0]["price"])
    depth = sum(float(l["price"]) * float(l["size"]) for l in levels
                if float(l["price"]) <= best + 0.02)
    left = usd; cost = 0.0; shares = 0.0
    for l in levels:
        p, s = float(l["price"]), float(l["size"])
        take = min(left, p * s)
        cost += take; shares += take / p; left -= take
        if left <= 0:
            break
    vwap = cost / shares if shares and left <= 0 else None
    return vwap, depth

def main():
    rows = [json.loads(l) for l in open('/tmp/redeploy_sweep/sdcc_walk_in.jsonl')]
    out = []
    with httpx.Client(timeout=20) as c:
        for r in rows:
            toks = json.loads(r["clobTokenIds"])
            yes_tok, no_tok = toks[0], toks[1]
            fee_bps = r.get("takerBaseFee") or 0
            rec = {"slug": r["slug"], "q": r["q"], "fee_bps": fee_bps, "dte": r["dte"],
                   "vol": round(r.get("volumeNum") or 0), "gamma_p": None,
                   "conditionId": r["conditionId"], "clobTokenIds": r["clobTokenIds"]}
            try:
                rec["gamma_p"] = float(json.loads(r["outcomePrices"])[0])
            except Exception:
                pass
            for name, tok in (("yes", yes_tok), ("no", no_tok)):
                for att in range(4):
                    try:
                        resp = c.get(BOOK, params={"token_id": tok})
                        if resp.status_code == 429:
                            time.sleep(2 * (att + 1)); continue
                        b = resp.json()
                        bids = sorted(b.get("bids", []), key=lambda x: -float(x["price"]))
                        asks = sorted(b.get("asks", []), key=lambda x: float(x["price"]))
                        vwap8, depth2 = fill(asks)
                        best_ask = float(asks[0]["price"]) if asks else None
                        net = None
                        if best_ask is not None:
                            fee = fee_bps / 10000.0 * min(best_ask, 1 - best_ask)
                            net = round(best_ask + fee, 4)
                        rec[name] = {
                            "bid": float(bids[0]["price"]) if bids else None,
                            "ask": best_ask,
                            "ask_vwap_$8": round(vwap8, 4) if vwap8 else None,
                            "depth2pp_$": round(depth2, 0),
                            "net_after_fee": net,
                        }
                        break
                    except Exception:
                        time.sleep(1.5 * (att + 1))
                else:
                    rec[name] = {"error": "failed"}
                time.sleep(0.35)
            out.append(rec)
            print(json.dumps({k: rec[k] for k in rec if k not in ("conditionId", "clobTokenIds")}), flush=True)
    with open('/tmp/redeploy_sweep/sdcc_books.jsonl', 'w') as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")

if __name__ == "__main__":
    main()
