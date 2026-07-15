#!/usr/bin/env python3
"""Live CLOB book walk on every mid/quote-flagged implication pair.

Trade frame (subset A=>B violated): BUY effective-NO(narrow) + BUY effective-YES(broad).
Min payout $1/share pair. Executable iff walked cost incl. taker fees < 1 at >= $10/leg depth.
Tokens in pairs.jsonl are already polarity-mirrored (tok_no_n is the physical token to buy).

Writes book_results.jsonl with per-pair walked economics.
"""
import json, sys, time
import httpx

BOOK = "https://clob.polymarket.com/book"
TARGET_NOTIONAL = 10.0  # $ per leg minimum
EPS = 1e-9


def get_book(client, tok, cache):
    if tok in cache:
        return cache[tok]
    for attempt in range(3):
        try:
            r = client.get(BOOK, params={"token_id": tok})
            if r.status_code == 200:
                b = r.json()
                asks = sorted(((float(x["price"]), float(x["size"])) for x in b.get("asks", [])), key=lambda t: t[0])
                bids = sorted(((float(x["price"]), float(x["size"])) for x in b.get("bids", [])), key=lambda t: -t[0])
                cache[tok] = {"asks": asks, "bids": bids}
                return cache[tok]
            if r.status_code == 429:
                time.sleep(2.0 * (attempt + 1))
                continue
            break
        except Exception:
            time.sleep(1.0)
    cache[tok] = None
    return None


def walk_shares(asks, shares):
    """Cost to buy `shares` walking asks. Returns (avg_px, filled_shares)."""
    need, cost = shares, 0.0
    for p, sz in asks:
        take = min(need, sz)
        cost += take * p
        need -= take
        if need <= EPS:
            break
    filled = shares - need
    return (cost / filled if filled > 0 else None), filled


def max_box(asks_a, asks_b, fee_a, fee_b):
    """Max shares N and profit for the 2-leg $1-payout box, walking both books.
    Greedy: merge both ask ladders; box is fillable while px_a+px_b+fees(level) < 1."""
    ia = ib = 0
    fa = list(asks_a)
    fb = list(asks_b)
    shares = 0.0
    cost = 0.0
    while ia < len(fa) and ib < len(fb):
        pa, sa = fa[ia]
        pb, sb = fb[ib]
        fee = fee_a / 10000 * min(pa, 1 - pa) + fee_b / 10000 * min(pb, 1 - pb)
        unit = pa + pb + fee
        if unit >= 1 - 1e-6:
            break
        take = min(sa, sb)
        shares += take
        cost += take * unit
        fa[ia] = (pa, sa - take)
        fb[ib] = (pb, sb - take)
        if fa[ia][1] <= EPS:
            ia += 1
        if fb[ib][1] <= EPS:
            ib += 1
    profit = shares * 1.0 - cost
    return shares, cost, profit


def main():
    pairs = [json.loads(l) for l in open("/tmp/implication_study/pairs.jsonl")]
    flagged = [r for r in pairs if (r.get("viol_mid_pp", -99) > 0.5) or (r.get("viol_quote_pp", -99) > 0.0)]
    # dedupe identical (narrow,broad) token combos
    seen = set()
    todo = []
    for r in flagged:
        k = (r["tok_no_n"], r["tok_yes_b"])
        if None in k or k in seen:
            continue
        seen.add(k)
        todo.append(r)
    print(f"# {len(flagged)} flagged, {len(todo)} unique pairs to walk", file=sys.stderr)

    cache = {}
    out = open("/tmp/implication_study/book_results.jsonl", "w")
    n_exec = 0
    with httpx.Client(timeout=15) as client:
        for i, r in enumerate(todo):
            ob_n = get_book(client, r["tok_no_n"], cache)   # effective NO on narrow
            ob_b = get_book(client, r["tok_yes_b"], cache)  # effective YES on broad
            res = dict(cls=r["cls"], sub=r["sub"], n_q=r["n_q"], b_q=r["b_q"],
                       n_id=r["n_id"], b_id=r["b_id"], cross_event=r["cross_event"],
                       viol_mid_pp=r.get("viol_mid_pp"), viol_quote_pp=r.get("viol_quote_pp"),
                       fee_n=r["fee_n"], fee_b=r["fee_b"],
                       vol24_n=r["vol24_n"], vol24_b=r["vol24_b"],
                       tok_no_n=r["tok_no_n"], tok_yes_b=r["tok_yes_b"],
                       n_flip=r.get("n_flip"), b_flip=r.get("b_flip"))
            if not ob_n or not ob_b:
                res["status"] = "no_book"
                out.write(json.dumps(res) + "\n")
                continue
            a_n, a_b = ob_n["asks"], ob_b["asks"]
            res["top_no_n"] = a_n[0] if a_n else None
            res["top_yes_b"] = a_b[0] if a_b else None
            res["bid_no_n"] = ob_n["bids"][0] if ob_n["bids"] else None
            res["bid_yes_b"] = ob_b["bids"][0] if ob_b["bids"] else None
            if not a_n or not a_b:
                res["status"] = "empty_ask_side"
                out.write(json.dumps(res) + "\n")
                continue
            # gross top-of-book box cost (no fee)
            gross_unit = a_n[0][0] + a_b[0][0]
            res["top_box_cost"] = round(gross_unit, 4)
            shares, cost, profit = max_box(a_n, a_b, r["fee_n"] or 0, r["fee_b"] or 0)
            res["box_shares"] = round(shares, 2)
            res["box_cost"] = round(cost, 4)
            res["box_profit"] = round(profit, 4)
            # depth requirement: >= $10 per leg -> leg notional at fill
            if shares > 0:
                # approximate leg notionals
                pxa, fa = walk_shares(a_n, shares)
                pxb, fb_ = walk_shares(a_b, shares)
                res["leg_notional_n"] = round((pxa or 0) * shares, 2)
                res["leg_notional_b"] = round((pxb or 0) * shares, 2)
            leg_min = min(res.get("leg_notional_n", 0), res.get("leg_notional_b", 0))
            if shares > 0 and profit > 0.01 and leg_min >= 10:
                res["status"] = "EXECUTABLE"       # >= $10 absorbed on BOTH legs at locked profit
            elif shares > 0 and profit > 0.001:
                res["status"] = "profitable_dust"  # locked profit exists but below $10/leg depth
            else:
                res["status"] = "dead_on_book"
            if res["status"] == "EXECUTABLE":
                n_exec += 1
            out.write(json.dumps(res) + "\n")
            out.flush()
            if (i + 1) % 25 == 0:
                print(f"# {i+1}/{len(todo)} walked, {n_exec} executable", file=sys.stderr)
            time.sleep(0.12)
    out.close()
    print(f"# DONE: {len(todo)} pairs walked, {n_exec} EXECUTABLE -> book_results.jsonl", file=sys.stderr)


if __name__ == "__main__":
    main()
