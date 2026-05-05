"""Polymarket CLOB v2 order signer.

Both first-party SDKs (py-clob-client 0.34.6, TS @polymarket/clob-client 5.8.1)
got out of sync with a Polymarket exchange-contract upgrade circa 2026-04-26
and now return `400 order_version_mismatch` on order placement. Schema details
were extracted from the polymarket.com JS bundle 2026-05-03; see
`research/_polymarket_v2_schema_2026-05-03.md`.

This module signs and posts orders directly via the REST API — no SDK
dependency for the order-construction path. We still re-use py-clob-client's
HMAC header utility because that auth scheme didn't change between v1 and v2.

Usage:
    python scripts/clob_v2.py orderbook <token_id>
    python scripts/clob_v2.py buy <token_id> <price> <usd_size> [--neg-risk] [--post-only]
    python scripts/clob_v2.py sell <token_id> <price> <shares> [--neg-risk] [--post-only]
    python scripts/clob_v2.py orders   # list open orders
    python scripts/clob_v2.py cancel <order_id>
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from eth_account import Account
from eth_account.messages import encode_typed_data

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as _secrets

_secrets.install_scrubbing_excepthook()

# --- constants from the JS bundle ----------------------------------------

CHAIN_ID = 137  # Polygon mainnet
CLOB_HOST = "https://clob.polymarket.com"

# Exchange contract addresses (v2; extracted 2026-05-03)
EXCHANGE_V2 = "0xE111180000d2663C0091e4f400237545B87B996B"
NEG_RISK_EXCHANGE_V2 = "0xe2222d279d744050d28e00520010520000310F59"

DOMAIN_NAME = "Polymarket CTF Exchange"
DOMAIN_VERSION = "2"

# v2 Order EIP-712 type definition
ORDER_TYPES = {
    "EIP712Domain": [
        {"name": "name", "type": "string"},
        {"name": "version", "type": "string"},
        {"name": "chainId", "type": "uint256"},
        {"name": "verifyingContract", "type": "address"},
    ],
    "Order": [
        {"name": "salt", "type": "uint256"},
        {"name": "maker", "type": "address"},
        {"name": "signer", "type": "address"},
        {"name": "tokenId", "type": "uint256"},
        {"name": "makerAmount", "type": "uint256"},
        {"name": "takerAmount", "type": "uint256"},
        {"name": "side", "type": "uint8"},
        {"name": "signatureType", "type": "uint8"},
        {"name": "timestamp", "type": "uint256"},
        {"name": "metadata", "type": "bytes32"},
        {"name": "builder", "type": "bytes32"},
    ],
}

BYTES32_ZERO = "0x" + "00" * 32

# Side encoding (from JS: `side: +("BUY" !== e.side)`)
SIDE_BUY = 0
SIDE_SELL = 1

# Signature type
SIG_TYPE_EOA = 0

# USDC (collateral) is 6 decimals
USDC_DECIMALS = 6


# --- wallet + creds loading ----------------------------------------------

def _load_wallet() -> tuple[str, str]:
    """Returns (address, private_key_hex_with_0x)."""
    d = json.loads(_secrets.path("POLYCLAUDE_WALLET").read_text())
    pk = d["private_key"]
    if not pk.startswith("0x"):
        pk = "0x" + pk
    return d["address"], pk


def _load_creds() -> dict:
    """Returns {api_key, api_secret, api_passphrase}. Derives from chain if missing."""
    p = _secrets.path("POLYCLAUDE_CREDS")
    if p.exists():
        return json.loads(p.read_text())
    # Derive via py-clob-client (still works for L1 auth, which is unchanged)
    from py_clob_client.client import ClobClient
    c = ClobClient(host=CLOB_HOST, chain_id=CHAIN_ID, key=_load_wallet()[1],
                   signature_type=SIG_TYPE_EOA, funder=_load_wallet()[0])
    creds = c.create_or_derive_api_creds()
    out = {"api_key": creds.api_key, "api_secret": creds.api_secret,
           "api_passphrase": creds.api_passphrase}
    p.write_text(json.dumps(out))
    os.chmod(p, 0o600)
    return out


# --- order construction --------------------------------------------------

def _to_token_decimals(amount_float: float) -> int:
    """Convert a float USDC/share amount to 6-decimal integer units."""
    return int(round(amount_float * (10 ** USDC_DECIMALS)))


def build_order(
    *,
    maker: str,
    token_id: str,
    side: str,
    price: float,
    size: float,
    signer_pk: str,
    neg_risk: bool = False,
) -> dict[str, Any]:
    """Construct + sign a v2 order. Returns the signed-order dict ready to POST.

    For BUY: size is USDC notional spent; shares received = size / price.
    For SELL: size is shares to sell; USDC received = size * price.
    """
    side_upper = side.upper()
    if side_upper == "BUY":
        side_int = SIDE_BUY
        usd_amount = size
        share_amount = size / price
    elif side_upper == "SELL":
        side_int = SIDE_SELL
        usd_amount = size * price
        share_amount = size
    else:
        raise ValueError(f"side must be BUY or SELL, got {side}")

    # In v1+v2, makerAmount = what you give, takerAmount = what you get.
    # For BUY: makerAmount = USDC spent, takerAmount = shares received.
    # For SELL: makerAmount = shares given, takerAmount = USDC received.
    if side_int == SIDE_BUY:
        maker_units = _to_token_decimals(usd_amount)
        taker_units = _to_token_decimals(share_amount)
    else:
        maker_units = _to_token_decimals(share_amount)
        taker_units = _to_token_decimals(usd_amount)

    # 32-bit salt: the API's body parser does `Number.parseInt(salt)` (TS SDK
    # convention), which silently loses precision above JS Number.MAX_SAFE_INTEGER
    # (2^53). 64-bit salts above ~2^53 cause "Invalid order payload" because the
    # parsed-back salt no longer matches the EIP-712-signed value, breaking
    # signature verification. Discovered 2026-05-05 when SELL orders failed
    # while structurally-identical BUY orders happened to draw smaller salts.
    salt = secrets.randbits(32)
    timestamp_ms = str(int(time.time() * 1000))

    message = {
        "salt": str(salt),
        "maker": maker,
        "signer": maker,
        "tokenId": str(token_id),
        "makerAmount": str(maker_units),
        "takerAmount": str(taker_units),
        "side": side_int,
        "signatureType": SIG_TYPE_EOA,
        "timestamp": timestamp_ms,
        "metadata": BYTES32_ZERO,
        "builder": BYTES32_ZERO,
    }

    domain = {
        "name": DOMAIN_NAME,
        "version": DOMAIN_VERSION,
        "chainId": CHAIN_ID,
        "verifyingContract": NEG_RISK_EXCHANGE_V2 if neg_risk else EXCHANGE_V2,
    }

    typed_data = {
        "primaryType": "Order",
        "types": ORDER_TYPES,
        "domain": domain,
        "message": message,
    }

    signable = encode_typed_data(full_message=typed_data)
    signed = Account.sign_message(signable, private_key=signer_pk)
    signature_hex = signed.signature.hex()
    if not signature_hex.startswith("0x"):
        signature_hex = "0x" + signature_hex

    return {**message, "signature": signature_hex}


# --- HTTP transport ------------------------------------------------------

def _hmac_headers(method: str, path: str, body: dict | None, creds: dict, address: str) -> dict[str, str]:
    """Build POLY_* HMAC auth headers. Reuses py-clob-client's signer for HMAC."""
    from py_clob_client.signing.hmac import build_hmac_signature
    timestamp = str(int(time.time()))
    body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False) if body is not None else ""
    sig = build_hmac_signature(creds["api_secret"], timestamp, method, path, body_str)
    return {
        "POLY_ADDRESS": address,
        "POLY_SIGNATURE": sig,
        "POLY_TIMESTAMP": timestamp,
        "POLY_API_KEY": creds["api_key"],
        "POLY_PASSPHRASE": creds["api_passphrase"],
        "Content-Type": "application/json",
    }


ZERO_ADDR = "0x0000000000000000000000000000000000000000"


def _signed_order_to_api_body(signed: dict) -> dict:
    """Convert the EIP-712-signed order dict into the JSON shape the /order
    endpoint actually accepts.

    Notes from JS bundle:
    - The v2 buildOrder return value INCLUDES `expiration: "0"` even though
      `expiration` is NOT in the EIP-712 typed message — meaning the JSON body
      sent to the API includes it for backwards compat.
    - Same probably for `taker` (zero address) and `feeRateBps`/`nonce` (zero):
      v1 body fields the server still accepts as defaults.
    - side gets converted from uint8 (signed) → "BUY"/"SELL" (body), per TS SDK.
    - salt is a JSON number, not a string."""
    # Body shape needs BOTH v1 backward-compat fields AND v2 fields:
    # - server rejects strict-11-fields with "Invalid order payload"
    # - server rejects v1-only with "order_version_mismatch"
    # Including both lets the API parse it AND verify the v2 EIP-712 signature.
    # Discovered empirically 2026-05-04 after first request that got past the
    # schema check ("balance not enough" error) included all 16 fields.
    return {
        "salt": int(signed["salt"]),
        "maker": signed["maker"],
        "signer": signed["signer"],
        "taker": ZERO_ADDR,
        "tokenId": signed["tokenId"],
        "makerAmount": signed["makerAmount"],
        "takerAmount": signed["takerAmount"],
        "side": "BUY" if signed["side"] == SIDE_BUY else "SELL",
        "expiration": "0",
        "nonce": "0",
        "feeRateBps": "0",
        "signatureType": signed["signatureType"],
        "timestamp": signed["timestamp"],
        "metadata": signed["metadata"],
        "builder": signed["builder"],
        "signature": signed["signature"],
    }


def post_order(signed_order: dict, *, order_type: str = "GTC", post_only: bool = False,
               defer_exec: bool = False) -> dict:
    """POST a signed v2 order to /order. Returns parsed JSON response."""
    address, _ = _load_wallet()
    creds = _load_creds()
    body = {
        "deferExec": defer_exec,
        "order": _signed_order_to_api_body(signed_order),
        "owner": creds["api_key"],
        "orderType": order_type,
    }
    if post_only:
        body["postOnly"] = True
    headers = _hmac_headers("POST", "/order", body, creds, address)
    body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    r = httpx.post(f"{CLOB_HOST}/order", content=body_str.encode(), headers=headers, timeout=20)
    return {"status_code": r.status_code, "body": _safe_json(r)}


def cancel_order(order_id: str) -> dict:
    address, _ = _load_wallet()
    creds = _load_creds()
    body = {"orderID": order_id}
    headers = _hmac_headers("DELETE", "/order", body, creds, address)
    body_str = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
    # httpx.delete() doesn't accept `content=` kwarg; use explicit request().
    r = httpx.request("DELETE", f"{CLOB_HOST}/order",
                      content=body_str.encode(), headers=headers, timeout=15)
    return {"status_code": r.status_code, "body": _safe_json(r)}


def list_open_orders() -> dict:
    address, _ = _load_wallet()
    creds = _load_creds()
    headers = _hmac_headers("GET", "/data/orders", None, creds, address)
    r = httpx.get(f"{CLOB_HOST}/data/orders", headers=headers, timeout=15)
    return {"status_code": r.status_code, "body": _safe_json(r)}


def get_orderbook(token_id: str) -> dict:
    r = httpx.get(f"{CLOB_HOST}/book", params={"token_id": str(token_id)}, timeout=15)
    return r.json()


def _safe_json(r: httpx.Response) -> Any:
    try:
        return r.json()
    except Exception:
        return r.text[:500]


# --- CLI ----------------------------------------------------------------

def _check_neg_risk(token_id: str) -> bool:
    """Query gamma-api for neg_risk status of the market this token belongs to."""
    try:
        r = httpx.get(f"{CLOB_HOST}/neg-risk", params={"token_id": str(token_id)}, timeout=10)
        if r.status_code == 200:
            return bool(r.json().get("neg_risk"))
    except Exception:
        pass
    return False


def cmd_buy(args):
    address, pk = _load_wallet()
    neg_risk = args.neg_risk if args.neg_risk is not None else _check_neg_risk(args.token_id)
    print(f"signing v2 BUY order: token={args.token_id[:16]}... price={args.price} usd_size={args.usd_size} neg_risk={neg_risk}")
    signed = build_order(maker=address, token_id=args.token_id, side="BUY",
                          price=args.price, size=args.usd_size, signer_pk=pk, neg_risk=neg_risk)
    print(f"posting...")
    result = post_order(signed, order_type=args.order_type, post_only=args.post_only)
    print(json.dumps(result, indent=2))
    return 0 if result["status_code"] < 400 else 2


def cmd_sell(args):
    address, pk = _load_wallet()
    neg_risk = args.neg_risk if args.neg_risk is not None else _check_neg_risk(args.token_id)
    print(f"signing v2 SELL order: token={args.token_id[:16]}... price={args.price} shares={args.shares} neg_risk={neg_risk}")
    signed = build_order(maker=address, token_id=args.token_id, side="SELL",
                          price=args.price, size=args.shares, signer_pk=pk, neg_risk=neg_risk)
    print(f"posting...")
    result = post_order(signed, order_type=args.order_type, post_only=args.post_only)
    print(json.dumps(result, indent=2))
    return 0 if result["status_code"] < 400 else 2


def cmd_cancel(args):
    result = cancel_order(args.order_id)
    print(json.dumps(result, indent=2))
    return 0 if result["status_code"] < 400 else 2


def cmd_orders(_args):
    result = list_open_orders()
    print(json.dumps(result, indent=2))
    return 0 if result["status_code"] < 400 else 2


def cmd_orderbook(args):
    ob = get_orderbook(args.token_id)
    print(json.dumps(ob, indent=2)[:3000])
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("buy")
    p.add_argument("token_id")
    p.add_argument("price", type=float)
    p.add_argument("usd_size", type=float)
    p.add_argument("--neg-risk", type=lambda x: x.lower() in ("true", "1", "yes"), default=None,
                   help="True/False to override neg_risk auto-detection")
    p.add_argument("--order-type", default="GTC", choices=["GTC", "FOK", "FAK", "GTD"])
    p.add_argument("--post-only", action="store_true")
    p.set_defaults(fn=cmd_buy)

    p = sub.add_parser("sell")
    p.add_argument("token_id")
    p.add_argument("price", type=float)
    p.add_argument("shares", type=float)
    p.add_argument("--neg-risk", type=lambda x: x.lower() in ("true", "1", "yes"), default=None)
    p.add_argument("--order-type", default="GTC", choices=["GTC", "FOK", "FAK", "GTD"])
    p.add_argument("--post-only", action="store_true")
    p.set_defaults(fn=cmd_sell)

    p = sub.add_parser("cancel")
    p.add_argument("order_id")
    p.set_defaults(fn=cmd_cancel)

    p = sub.add_parser("orders")
    p.set_defaults(fn=cmd_orders)

    p = sub.add_parser("orderbook")
    p.add_argument("token_id")
    p.set_defaults(fn=cmd_orderbook)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
