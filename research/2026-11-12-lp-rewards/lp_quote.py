"""LP-rewards quote helper (2026-11-12 falsification test).

Reuses scripts/clob_v2.py signing/auth (no new key handling, nothing secret is printed).
Adds what clob_v2's CLI lacks for reward farming: post-only GTD orders with an
explicit expiration, and the L2 /order-scoring eligibility check.

    python lp_quote.py post TOKEN BUY|SELL PRICE SHARES --neg-risk 0|1 --expire-utc 2026-11-12T17:00
    python lp_quote.py scoring ORDER_ID [ORDER_ID ...]
    python lp_quote.py order ORDER_ID

BUY legs are NOT entered in .entry_reservations.json: they are short-lived GTD
quotes that expire on their own (no cancel => no tombstone); open BUYs remain
visible to the desk via the authenticated open-order endpoint while live.
"""
from __future__ import annotations
import argparse, datetime, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import httpx
import clob_v2 as C
from entry_review_gate import require_new_buy_allowed


def post(token, side, price, shares, neg_risk, expire_ts):
    if side == "BUY":
        require_new_buy_allowed(str(token))
    address, pk = C._load_wallet()
    creds = C._load_creds()
    size = round(shares * price, 6) if side == "BUY" else shares
    signed = C.build_order(maker=address, token_id=token, side=side, price=price,
                           size=size, signer_pk=pk, neg_risk=neg_risk)
    order = C._signed_order_to_api_body(signed)
    order["expiration"] = str(int(expire_ts))
    body = {"deferExec": False, "order": order, "owner": creds["api_key"],
            "orderType": "GTD", "postOnly": True}
    headers = C._hmac_headers("POST", "/order", body, creds, address)
    r = httpx.post(f"{C.CLOB_HOST}/order", content=json.dumps(body, separators=(",", ":")).encode(),
                   headers=headers, timeout=20)
    return {"status_code": r.status_code, "body": C._safe_json(r)}


def scoring(order_id):
    address, _ = C._load_wallet()
    creds = C._load_creds()
    headers = C._hmac_headers("GET", "/order-scoring", None, creds, address)
    r = httpx.get(f"{C.CLOB_HOST}/order-scoring", params={"order_id": order_id}, headers=headers, timeout=15)
    return {"status_code": r.status_code, "body": C._safe_json(r)}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("post"); p.add_argument("token"); p.add_argument("side", choices=["BUY", "SELL"])
    p.add_argument("price", type=float); p.add_argument("shares", type=float)
    p.add_argument("--neg-risk", type=int, required=True); p.add_argument("--expire-utc", required=True)
    s = sub.add_parser("scoring"); s.add_argument("order_ids", nargs="+")
    o = sub.add_parser("order"); o.add_argument("order_id")
    a = ap.parse_args()
    if a.cmd == "post":
        exp = datetime.datetime.fromisoformat(a.expire_utc).replace(tzinfo=datetime.timezone.utc).timestamp()
        print(json.dumps(post(a.token, a.side, a.price, a.shares, bool(a.neg_risk), exp), indent=1))
    elif a.cmd == "scoring":
        for oid in a.order_ids:
            print(oid, json.dumps(scoring(oid)))
    else:
        print(json.dumps(C.get_authenticated_order(a.order_id), indent=1))


if __name__ == "__main__":
    main()
