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
    python scripts/clob_v2.py buy <token_id> <price> <usd_size> --reservation-id <id> [--neg-risk] [--post-only]
    python scripts/clob_v2.py sell <token_id> <price> <shares> [--neg-risk] [--post-only]
    python scripts/clob_v2.py orders   # list open orders
    python scripts/clob_v2.py cancel <order_id>
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import functools
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
REPO_ROOT = Path(__file__).resolve().parent.parent

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

# Matched v2 POSTs can now return tradeIDs before settlement transaction
# hashes. Mirror the official SDK's best-effort authenticated trade polling so
# downstream execution can retain transaction-hash proof.
RESOLVE_TRADES_TIMEOUT_SECONDS = 15.0
RESOLVE_TRADES_POLL_INTERVAL_SECONDS = 0.25
FAILED_TRADE_STATUS = "FAILED"


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
    """POST a signed v2 order and resolve async trade IDs when possible."""
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
    response_body = _safe_json(r)
    if r.status_code < 400 and not defer_exec:
        response_body = _resolve_transactions_hashes(response_body, address, creds)
    return {"status_code": r.status_code, "body": response_body}


def _get_trades_by_id(trade_id: str, address: str, creds: dict) -> list[dict]:
    """Fetch the first authenticated trade page for one execution ID."""
    path = "/data/trades"
    headers = _hmac_headers("GET", path, None, creds, address)
    r = httpx.get(
        f"{CLOB_HOST}{path}",
        params={"id": trade_id, "next_cursor": "MA=="},
        headers=headers,
        timeout=5,
    )
    r.raise_for_status()
    body = r.json()
    rows = body.get("data") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError("trade lookup returned an unexpected shape")
    return [trade for trade in rows if isinstance(trade, dict)]


def _resolve_transactions_hashes(response: Any, address: str, creds: dict,
                                  timeout: float = RESOLVE_TRADES_TIMEOUT_SECONDS) -> Any:
    """Best-effort conversion of async ``tradeIDs`` into settlement hashes.

    Poll failures never turn a successfully posted order into a rejection. On
    timeout the original response retains its trade IDs, which forces strict
    downstream callers into manual reconciliation instead of guessing.
    """
    if not isinstance(response, dict) or response.get("transactionsHashes"):
        return response
    raw_ids = response.get("tradeIDs")
    if not isinstance(raw_ids, list):
        return response
    normalized_ids = [str(trade_id).strip() for trade_id in raw_ids
                      if isinstance(trade_id, (str, int)) and str(trade_id).strip()]
    trade_ids = list(dict.fromkeys(normalized_ids))
    if not trade_ids:
        return response

    resolved: dict[str, dict] = {}
    try:
        timeout_value = float(timeout)
    except (TypeError, ValueError):
        timeout_value = 0.0
    if not timeout_value >= 0.0 or timeout_value == float("inf"):
        timeout_value = 0.0
    deadline = time.monotonic() + timeout_value
    while True:
        for trade_id in trade_ids:
            if trade_id in resolved:
                continue
            try:
                trades = _get_trades_by_id(trade_id, address, creds)
            except Exception:
                trades = []
            for trade in trades:
                if str(trade.get("id") or "") != trade_id:
                    continue
                status = str(trade.get("status") or "").upper()
                if status == FAILED_TRADE_STATUS or trade.get("transaction_hash"):
                    resolved[trade_id] = trade
                    break
        if (all(trade_id in resolved for trade_id in trade_ids)
                or time.monotonic() >= deadline):
            break
        time.sleep(RESOLVE_TRADES_POLL_INTERVAL_SECONDS)

    hashes = [
        str(resolved[trade_id]["transaction_hash"])
        for trade_id in trade_ids
        if trade_id in resolved
        and str(resolved[trade_id].get("status") or "").upper() != FAILED_TRADE_STATUS
        and resolved[trade_id].get("transaction_hash")
    ]
    return ({**response, "transactionsHashes": hashes} if hashes else response)


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


def get_authenticated_order(order_id: str) -> dict:
    address, _ = _load_wallet()
    creds = _load_creds()
    path = f"/data/order/{order_id}"
    headers = _hmac_headers("GET", path, None, creds, address)
    r = httpx.get(f"{CLOB_HOST}{path}", headers=headers, timeout=15)
    return {"status_code": r.status_code, "body": _safe_json(r)}


def _acquire_entry_lock():
    handle = (REPO_ROOT / ".entry.lock").open("w")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise RuntimeError("another wallet entry/cancel is already in progress") from exc
    return handle


_RESERVATION_LOCK_DEPTH = 0
_RESERVATION_LOCK_HANDLE = None


class _ReservationLockLease:
    def __init__(self):
        self.closed = False

    def close(self):
        global _RESERVATION_LOCK_DEPTH, _RESERVATION_LOCK_HANDLE
        if self.closed:
            return
        self.closed = True
        _RESERVATION_LOCK_DEPTH -= 1
        if _RESERVATION_LOCK_DEPTH == 0:
            handle = _RESERVATION_LOCK_HANDLE
            _RESERVATION_LOCK_HANDLE = None
            if handle is not None:
                handle.close()


def _acquire_reservation_lock():
    """Process-reentrant lock for every reservation/tombstone transition."""
    global _RESERVATION_LOCK_DEPTH, _RESERVATION_LOCK_HANDLE
    if _RESERVATION_LOCK_DEPTH == 0:
        handle = (REPO_ROOT / ".entry_reservation.lock").open("w")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        _RESERVATION_LOCK_HANDLE = handle
    _RESERVATION_LOCK_DEPTH += 1
    return _ReservationLockLease()


def _reservation_locked(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        lease = _acquire_reservation_lock()
        try:
            return func(*args, **kwargs)
        finally:
            lease.close()
    return wrapped


@_reservation_locked
def _mark_reservation_cancel_verified(order_id: str) -> bool:
    """Attach affirmative cancel evidence to this CLI's local reservation."""
    path = REPO_ROOT / ".entry_reservations.json"
    if not path.exists():
        return False
    try:
        rows = json.loads(path.read_text())
    except Exception as exc:
        raise RuntimeError(f"entry reservation ledger is unreadable: {exc}")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise RuntimeError("entry reservation ledger is malformed")
    matches = [row for row in rows if str(row.get("orderId") or "") == order_id]
    if len(matches) > 1:
        raise RuntimeError("multiple reservations map to the canceled order")
    if not matches:
        return False
    matches[0]["submissionState"] = "cancelled"
    matches[0]["cancelVerifiedAt"] = datetime.datetime.now(
        datetime.timezone.utc).isoformat()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)
    return True


def _has_entry_reservation(order_id: str) -> bool:
    path = REPO_ROOT / ".entry_reservations.json"
    if not path.exists():
        return False
    try:
        rows = json.loads(path.read_text())
    except Exception as exc:
        raise RuntimeError(f"entry reservation ledger is unreadable: {exc}")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise RuntimeError("entry reservation ledger is malformed")
    matches = [row for row in rows if str(row.get("orderId") or "") == order_id]
    if len(matches) > 1:
        raise RuntimeError("multiple reservations map to one order")
    return bool(matches)


@_reservation_locked
def _record_unreserved_cancel_block(order: dict, *, reason: str =
                                    "legacy/unreserved BUY canceled; reconcile "
                                    "fills and indexing manually") -> None:
    """Persist any cancel identity/fill window that cannot be proved safe."""
    if not isinstance(order, dict):
        raise RuntimeError("unreserved canceled order metadata is malformed")
    order_id = str(order.get("id") or "")
    if not order_id:
        raise RuntimeError("unreserved canceled order omitted its ID")
    path = REPO_ROOT / ".entry_reconciliation_required.json"
    if path.exists():
        try:
            rows = json.loads(path.read_text())
        except Exception as exc:
            raise RuntimeError(f"entry reconciliation ledger is unreadable: {exc}")
    else:
        rows = []
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise RuntimeError("entry reconciliation ledger is malformed")
    if not any(str(row.get("orderId") or "") == order_id for row in rows):
        rows.append({
            "orderId": order_id,
            "conditionId": str(order.get("market") or "").lower(),
            "asset": str(order.get("asset_id") or ""),
            "side": str(order.get("side") or "").upper(),
            "originalShares": order.get("original_size"),
            "matchedSharesAtCancel": order.get("size_matched"),
            "price": order.get("price"),
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "reason": reason,
        })
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def _claim_buy_reservation(token_id: str, price: float, usd_size: float,
                           reservation_id: str | None) -> dict:
    """Atomically consume one pending reservation before a BUY is signed.

    The claimed row remains a full-risk commitment if submission crashes or
    times out.  Only the orchestrator may later attach order evidence or remove
    it after a definitive no-fill response.
    """
    claim_lock = _acquire_reservation_lock()
    try:
        reconciliation = REPO_ROOT / ".entry_reconciliation_required.json"
        if reconciliation.exists():
            raise RuntimeError(
                "BUY blocked by unresolved entry reconciliation tombstone")
        path = REPO_ROOT / ".entry_reservations.json"
        if not path.exists():
            raise RuntimeError(
                "BUY has no exposure reservation; enter through polyclaude_enter.py")
        try:
            rows = json.loads(path.read_text())
        except Exception as exc:
            raise RuntimeError(f"entry reservation ledger is unreadable: {exc}")
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            raise RuntimeError("entry reservation ledger is malformed")
        matches = [
            row for row in rows
            if str(row.get("asset") or "") == str(token_id)
            and str(row.get("reservationId") or "") == str(reservation_id or "")
            and str(row.get("submissionState") or "pending") == "pending"
            and not str(row.get("orderId") or "")
        ]
        if len(matches) != 1:
            raise RuntimeError(
                "BUY requires exactly one unclaimed pending reservation for this token")
        record = matches[0]
        try:
            reserved_shares = float(record["shares"])
            reserved_risk = float(record["risk"])
            expected_shares = float(usd_size) / float(price)
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            raise RuntimeError("BUY reservation risk/size is malformed")
        if (not all(value > 0 and value < float("inf") for value in (
                reserved_shares, reserved_risk, expected_shares))
                or abs(reserved_shares - expected_shares) > 1e-4
                or reserved_risk + 1e-4 < float(usd_size)):
            raise RuntimeError("BUY size/risk exceeds its exposure reservation")
        record["submissionState"] = "claimed"
        record["claimedAt"] = datetime.datetime.now(
            datetime.timezone.utc).isoformat()
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
        tmp.replace(path)
        return dict(record)
    finally:
        claim_lock.close()


def list_open_orders() -> dict:
    address, _ = _load_wallet()
    creds = _load_creds()
    path = "/data/orders"
    cursor = "MA=="
    rows: list[dict] = []
    pages = 0
    while cursor != "LTE=":
        headers = _hmac_headers("GET", path, None, creds, address)
        r = httpx.get(
            f"{CLOB_HOST}{path}", params={"next_cursor": cursor},
            headers=headers, timeout=15,
        )
        body = _safe_json(r)
        if r.status_code >= 400 or not isinstance(body, dict):
            return {"status_code": r.status_code, "body": body}
        page = body.get("data")
        next_cursor = body.get("next_cursor")
        if not isinstance(page, list) or not isinstance(next_cursor, str):
            return {"status_code": 502, "body": {
                "error": "open-order pagination returned an unexpected shape"}}
        rows.extend(page)
        cursor = next_cursor
        pages += 1
        if pages >= 100 and cursor != "LTE=":
            return {"status_code": 502, "body": {
                "error": "open-order pagination exceeded safety bound"}}
    return {"status_code": 200,
            "body": {"data": rows, "next_cursor": "LTE="}}


def list_authenticated_trades() -> dict:
    """Return the wallet's complete authenticated trade history page set.

    Reservation reconciliation uses order IDs embedded in taker/maker trade
    rows to distinguish a canceled remainder from a fill that has not reached
    data-api yet.  As with open orders, an incomplete cursor is never accepted
    as proof that an execution did not happen.
    """
    address, _ = _load_wallet()
    creds = _load_creds()
    path = "/data/trades"
    cursor = "MA=="
    rows: list[dict] = []
    pages = 0
    while cursor != "LTE=":
        headers = _hmac_headers("GET", path, None, creds, address)
        r = httpx.get(
            f"{CLOB_HOST}{path}", params={"next_cursor": cursor},
            headers=headers, timeout=15,
        )
        body = _safe_json(r)
        if r.status_code >= 400 or not isinstance(body, dict):
            return {"status_code": r.status_code, "body": body}
        page = body.get("data")
        next_cursor = body.get("next_cursor")
        if not isinstance(page, list) or not isinstance(next_cursor, str):
            return {"status_code": 502, "body": {
                "error": "trade pagination returned an unexpected shape"}}
        rows.extend(page)
        cursor = next_cursor
        pages += 1
        if pages >= 100 and cursor != "LTE=":
            return {"status_code": 502, "body": {
                "error": "trade pagination exceeded safety bound"}}
    return {"status_code": 200,
            "body": {"data": rows, "next_cursor": "LTE="}}


def get_orderbook(token_id: str) -> dict:
    r = httpx.get(f"{CLOB_HOST}/book", params={"token_id": str(token_id)}, timeout=15)
    return r.json()


# --- redemption (post-resolution) ---------------------------------------

CTF_ADDR = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
NEG_RISK_ADAPTER = "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"
USDC_E_ADDR = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
# v2 CLOB collateral (CollateralOnramp-wrapped pUSD). NOTE 2026-07-26: CTF
# redemption with the WRONG collateral for a position's parent collection
# silently no-ops (status=1, pays 0) — but whether v2 positions redeem
# against pUSD or USDC.e is UNVERIFIED (both Marvel attempts no-opped on a
# ZERO balance — the shares had sold at 0.98 minutes earlier, so neither
# call tested the collateral). Test at the next real redemption; if pUSD
# fails, flip redeem_one/redeem_all back to USDC_E_ADDR.
PUSD_ADDR = "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"
POLYGON_RPC = "https://polygon.drpc.org"

_NEG_RISK_REDEEM_ABI = [{
    "inputs": [
        {"name": "_conditionId", "type": "bytes32"},
        {"name": "_amounts", "type": "uint256[]"},
    ],
    "name": "redeemPositions", "outputs": [],
    "stateMutability": "nonpayable", "type": "function",
}]
_CTF_REDEEM_ABI = [{
    "inputs": [
        {"name": "collateralToken", "type": "address"},
        {"name": "parentCollectionId", "type": "bytes32"},
        {"name": "conditionId", "type": "bytes32"},
        {"name": "indexSets", "type": "uint256[]"},
    ],
    "name": "redeemPositions", "outputs": [],
    "stateMutability": "nonpayable", "type": "function",
}]
_CTF_BAL_ABI = [{
    "inputs": [{"name": "a", "type": "address"}, {"name": "id", "type": "uint256"}],
    "name": "balanceOf", "outputs": [{"type": "uint256"}],
    "stateMutability": "view", "type": "function",
}]


def _data_api_positions(address: str) -> list[dict]:
    r = httpx.get("https://data-api.polymarket.com/positions",
                  params={"user": address.lower(), "limit": 50}, timeout=15)
    return r.json() or []


def _redeem_token_balance(ctf: Any, address: str, token_id: str | None) -> int:
    """Return the held outcome-token balance, failing closed without an id.

    A successful ``eth_call`` of ``redeemPositions`` does not prove that the
    caller holds any outcome tokens: the CTF accepts a zero-balance redemption
    as a no-op. Requiring the archived outcome-token id prevents that known
    failure mode; final resolution to the held outcome must still be verified
    separately before broadcast.
    """
    if not token_id:
        raise SystemExit(
            "redeem-one: need --token-id (snapshot field `asset`) so a "
            "nonzero held-token balance can be verified before broadcast"
        )
    try:
        token = int(token_id)
    except (TypeError, ValueError) as exc:
        raise SystemExit("redeem-one: --token-id must be an integer") from exc
    if token <= 0:
        raise SystemExit("redeem-one: --token-id must be positive")
    return int(ctf.functions.balanceOf(address, token).call())


def redeem_all(dry_run: bool = False) -> dict:
    """Iterate user's positions; redeem any with redeemable=true. Routes negRisk
    markets through NegRiskAdapter and binary non-negRisk through standard CTF.
    Returns a summary of attempts. dry_run lists redeemables and exits before
    any tx — safe to hand to read-only delegated ticks."""
    from web3 import Web3
    from eth_account import Account
    address, pk = _load_wallet()
    w = Web3(Web3.HTTPProvider(POLYGON_RPC))
    addr_cs = Web3.to_checksum_address(address)
    ctf = w.eth.contract(address=Web3.to_checksum_address(CTF_ADDR), abi=_CTF_BAL_ABI)
    adapter = w.eth.contract(address=Web3.to_checksum_address(NEG_RISK_ADAPTER),
                              abi=_NEG_RISK_REDEEM_ABI)
    ctf_redeem = w.eth.contract(address=Web3.to_checksum_address(CTF_ADDR),
                                 abi=_CTF_REDEEM_ABI)

    positions = _data_api_positions(address)
    redeemables = [p for p in positions if p.get("redeemable")]
    print(f"found {len(redeemables)}/{len(positions)} redeemable positions")
    if dry_run:
        return {"dry_run": True,
                "redeemable": [{"title": (p.get("title") or "")[:60],
                                "conditionId": p["conditionId"],
                                "size": p.get("size"),
                                "negativeRisk": bool(p.get("negativeRisk"))}
                               for p in redeemables]}

    summary = []
    for p in redeemables:
        title = (p.get("title") or "")[:60]
        cond_id_hex = p["conditionId"]
        is_neg = bool(p.get("negativeRisk"))
        outcome_idx = int(p.get("outcomeIndex", 0))  # 0 = YES, 1 = NO
        yes_tok = int(p["asset"])
        no_tok = int(p["oppositeAsset"])

        # Pull on-chain CTF balance (data-api sometimes lags, on-chain is source of truth)
        bal_yes = ctf.functions.balanceOf(addr_cs, yes_tok).call()
        bal_no = ctf.functions.balanceOf(addr_cs, no_tok).call()
        if bal_yes == 0 and bal_no == 0:
            print(f"  SKIP (zero balance) {title}")
            continue
        cond_id = bytes.fromhex(cond_id_hex.replace("0x", ""))

        nonce = w.eth.get_transaction_count(addr_cs)
        gp = w.eth.gas_price
        common_tx = {
            "from": addr_cs, "nonce": nonce, "chainId": 137,
            "gas": 250_000,
            "maxFeePerGas": max(int(gp * 3), int(gp + 1_000_000_000)),
            "maxPriorityFeePerGas": 30_000_000_000,
        }
        if is_neg:
            tx = adapter.functions.redeemPositions(cond_id, [bal_yes, bal_no]).build_transaction(common_tx)
        else:
            # Standard CTF: indexSets = [1] (YES) | [2] (NO) — pass both, contract no-ops the loser
            tx = ctf_redeem.functions.redeemPositions(
                Web3.to_checksum_address(USDC_E_ADDR),
                b"\x00" * 32,
                cond_id,
                [1, 2],
            ).build_transaction(common_tx)

        h = w.eth.send_raw_transaction(Account.sign_transaction(tx, pk).raw_transaction)
        r = w.eth.wait_for_transaction_receipt(h, timeout=120)
        ok = r.status == 1
        print(f"  {'OK' if ok else 'FAIL'} {title}  tx 0x{r.transactionHash.hex()}  yes={bal_yes/1e6} no={bal_no/1e6}")
        summary.append({
            "title": title, "conditionId": cond_id_hex, "negRisk": is_neg,
            "tx": "0x" + r.transactionHash.hex(), "ok": ok,
            "yes_redeemed": bal_yes / 1e6, "no_redeemed": bal_no / 1e6,
        })
    return {"redemptions": summary}


def redeem_one(cond_id_hex: str, neg_risk: bool = False, dry_run: bool = False,
               token_id: str | None = None, outcome: str | None = None) -> dict:
    """Redeem a single resolved market by conditionId — the fallback for
    DE-INDEXED markets (N=2: Mojtaba 2026-07, Marvel-SDCC 2026-07-26) where
    data-api drops the position row so redeem-all's redeemable-flag scan is
    blind. Verify the market is actually resolved (gamma umaResolutionStatus)
    first — redeeming an unresolved condition reverts.

    Both paths require the archived held token id as a preflight: a successful
    redemption simulation can still be a zero-balance no-op. The standard CTF
    pays whatever the caller holds across both index sets, but the token id is
    checked before broadcast to prevent a zero-balance no-op. NEGRISK PATH ADDED
    2026-08-13: the adapter needs exact balances, which is why this used to refuse outright — but that
    refusal left my LARGEST position with no claim-insurance fallback at all.
    SpaceX ($29.42, 16% of bankroll) was the book's only negRisk market when
    this fallback was added, so a de-index at its Dec-31 resolution would have
    hit exactly the case this function exists for and raised SystemExit. The
    balances come from the conditionId snapshot's `asset` + `outcome` fields
    read ON-CHAIN via balanceOf, never from data-api — which is the whole point, since data-api is
    the thing that has disappeared in the scenario being handled.
    """
    from web3 import Web3
    from eth_account import Account
    address, pk = _load_wallet()
    w = Web3(Web3.HTTPProvider(POLYGON_RPC))
    addr_cs = Web3.to_checksum_address(address)
    ctf_redeem = w.eth.contract(address=Web3.to_checksum_address(CTF_ADDR),
                                 abi=_CTF_REDEEM_ABI)
    ctf_bal = w.eth.contract(address=Web3.to_checksum_address(CTF_ADDR),
                             abi=_CTF_BAL_ABI)
    bal = _redeem_token_balance(ctf_bal, addr_cs, token_id)
    if bal == 0:
        print("  SKIP redeem: held outcome-token balance is zero")
        return {"ok": False, "tx": None, "skipped": "zero outcome-token balance",
                "balance": 0}
    cond_id = bytes.fromhex(cond_id_hex.replace("0x", ""))
    nonce = w.eth.get_transaction_count(addr_cs)
    gp = w.eth.gas_price
    common_tx = {
        "from": addr_cs, "nonce": nonce, "chainId": 137, "gas": 250_000,
        "maxFeePerGas": max(int(gp * 3), int(gp + 1_000_000_000)),
        "maxPriorityFeePerGas": 30_000_000_000,
    }
    if neg_risk:
        if not token_id or outcome not in ("Yes", "No"):
            raise SystemExit("redeem-one negRisk: need --token-id and --outcome Yes|No "
                             "(both are in notes/position_condition_ids.json)")
        # Adapter takes [yes_amount, no_amount]; I hold exactly one side, so the
        # other is zero. Reading the held side on-chain keeps this independent of
        # data-api, which is precisely what has vanished in a de-index.
        amounts = [bal, 0] if outcome == "Yes" else [0, bal]
        print(f"  negRisk redeem: on-chain balance {bal} on the {outcome} leg -> amounts {amounts}")
        adapter = w.eth.contract(address=Web3.to_checksum_address(NEG_RISK_ADAPTER),
                                 abi=_NEG_RISK_REDEEM_ABI)
        tx = adapter.functions.redeemPositions(cond_id, amounts).build_transaction(common_tx)
    else:
        tx = ctf_redeem.functions.redeemPositions(
            Web3.to_checksum_address(PUSD_ADDR), b"\x00" * 32, cond_id, [1, 2],
        ).build_transaction(common_tx)
    # SIMULATE-FIRST (2026-08-12). This function had no dry path, and on that
    # date I called it as a "probe" of the redemption wiring: it sent a real
    # transaction, which reverted (correctly — the condition was unresolved)
    # and cost 0.00808 MATIC. Trivial in money; the shape is the lesson. A
    # function whose ONLY mode is send will eventually be called by someone who
    # believes they are testing. eth_call executes against current state and
    # reverts WITHOUT broadcasting, so the wiring verifies for free and a real
    # redemption can be rehearsed before it is sent.
    if dry_run:
        try:
            w.eth.call({"from": tx["from"], "to": tx["to"], "data": tx["data"]})
            return {"ok": True, "tx": None, "simulated": "would SUCCEED"}
        except Exception as e:
            return {"ok": False, "tx": None, "simulated": f"would REVERT: {str(e)[:180]}"}
    h = w.eth.send_raw_transaction(Account.sign_transaction(tx, pk).raw_transaction)
    r = w.eth.wait_for_transaction_receipt(h, timeout=120)
    print(f"  {'OK' if r.status == 1 else 'FAIL'} redeem {cond_id_hex[:18]}...  tx 0x{r.transactionHash.hex()}")
    return {"ok": r.status == 1, "tx": "0x" + r.transactionHash.hex()}


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
    reservation_lock = _acquire_reservation_lock()
    try:
        try:
            _claim_buy_reservation(
                args.token_id, args.price, args.usd_size, args.reservation_id)
        except Exception as exc:
            print(f"BUY blocked: {exc}", file=sys.stderr)
            return 3
        address, pk = _load_wallet()
        neg_risk = (args.neg_risk if args.neg_risk is not None
                    else _check_neg_risk(args.token_id))
        print(f"signing v2 BUY order: token={args.token_id[:16]}... "
              f"price={args.price} usd_size={args.usd_size} neg_risk={neg_risk}")
        signed = build_order(
            maker=address, token_id=args.token_id, side="BUY",
            price=args.price, size=args.usd_size, signer_pk=pk,
            neg_risk=neg_risk,
        )
        print("posting...")
        result = post_order(
            signed, order_type=args.order_type, post_only=args.post_only)
        print(json.dumps(result, indent=2))
        return 0 if result["status_code"] < 400 else 2
    finally:
        reservation_lock.close()


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
    try:
        entry_lock = _acquire_entry_lock()
    except Exception as exc:
        print(f"cancel blocked: {exc}", file=sys.stderr)
        return 3
    try:
        reservation_lock = _acquire_reservation_lock()
    except Exception as exc:
        entry_lock.close()
        print(f"cancel blocked: reservation ledger lock unavailable: {exc}",
              file=sys.stderr)
        return 3
    try:
        before = list_open_orders()
        before_body = before.get("body") if isinstance(before, dict) else None
        try:
            before_status = int(before.get("status_code", 999))
        except (AttributeError, TypeError, ValueError):
            before_status = 999
        if (before_status >= 400
                or not isinstance(before_body, dict)
                or before_body.get("next_cursor") != "LTE="
                or not isinstance(before_body.get("data"), list)):
            print("cancel blocked: pre-cancel open-order inventory is incomplete",
                  file=sys.stderr)
            return 3
        before_matches = [
            order for order in before_body["data"]
            if isinstance(order, dict) and str(order.get("id") or "") == args.order_id
        ]
        if len(before_matches) > 1:
            print("cancel blocked: duplicate pre-cancel order identity", file=sys.stderr)
            return 3
        if not before_matches:
            _record_unreserved_cancel_block(
                {"id": args.order_id, "side": "UNKNOWN"},
                reason="cancel target absent from exhaustive pre-cancel inventory; "
                       "it may have filled during indexing lag",
            )
            print("cancel blocked: target is absent from the exhaustive pre-cancel "
                  "inventory; persistent reconciliation block recorded",
                  file=sys.stderr)
            return 3
        target_side = str(before_matches[0].get("side") or "").upper()
        if target_side not in {"BUY", "SELL"}:
            _record_unreserved_cancel_block(
                before_matches[0],
                reason="cancel target has unknown side; reconcile whether BUY "
                       "exposure filled before allowing new entries",
            )
            print("cancel blocked: target side identity is unavailable; persistent "
                  "reconciliation block recorded", file=sys.stderr)
            return 3
        if (target_side == "BUY"
                and not _has_entry_reservation(args.order_id)):
            # Persist the blocker before DELETE: a crash after cancellation must
            # not create an unreserved fill/indexing window.
            _record_unreserved_cancel_block(before_matches[0])

        result = cancel_order(args.order_id)
        print(json.dumps(result, indent=2))
        if result["status_code"] >= 400:
            return 2
        # Cancel-race guard (2026-07-28): a cancel response saying "canceled" is
        # NOT proof of removal. Verify the fully paginated live book, then mark
        # the local BUY reservation so a later grace+trade+totalBought reconcile
        # can retire only the genuinely canceled remainder.
        time.sleep(2)
        try:
            live = list_open_orders()
            body = live.get("body") if isinstance(live, dict) else None
            try:
                live_status = int(live.get("status_code", 999))
            except (AttributeError, TypeError, ValueError):
                live_status = 999
            if (live_status >= 400
                    or not isinstance(body, dict)
                    or body.get("next_cursor") != "LTE="
                    or not isinstance(body.get("data"), list)):
                raise RuntimeError("open-order verification was incomplete")
            ids = [order.get("id") for order in body["data"]
                   if isinstance(order, dict)]
            if args.order_id in ids:
                print(f"CANCEL-VERIFY FAILED: {args.order_id[:18]}... STILL IN BOOK — "
                      f"re-cancel or expect fills", file=sys.stderr)
                return 3
            marked = _mark_reservation_cancel_verified(args.order_id)
            suffix = "; BUY reservation marked for delayed reconcile" if marked else ""
            print(f"cancel VERIFIED: order gone from book{suffix}", file=sys.stderr)
        except Exception as exc:
            print(f"cancel-verify inconclusive ({exc}) — check `orders` manually",
                  file=sys.stderr)
            return 3
        return 0
    finally:
        reservation_lock.close()
        entry_lock.close()


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
    p.add_argument("--reservation-id", required=True,
                   help="pending exposure-ledger reservation created by polyclaude_enter")
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

    p = sub.add_parser("redeem-all", help="redeem every redeemable position via the right adapter")
    p.add_argument("--dry-run", action="store_true",
                   help="list redeemables and exit before any tx (read-only safe)")
    p.set_defaults(fn=lambda a: (print(json.dumps(redeem_all(dry_run=a.dry_run), indent=2)), 0)[1])

    p = sub.add_parser("redeem-one", help="redeem a single resolved market by conditionId "
                                          "(fallback for de-indexed markets redeem-all can't see)")
    p.add_argument("condition_id", help="0x-prefixed conditionId (verify resolved on gamma first)")
    p.add_argument("--neg-risk", action="store_true",
                   help="negRisk market — also pass --token-id and --outcome (all three fields "
                        "are in notes/position_condition_ids.json for every live position)")
    p.add_argument("--token-id", required=True,
                   help="the held outcome's token id (snapshot field `asset`); used to "
                        "prevent a zero-balance no-op before any broadcast")
    p.add_argument("--outcome", choices=["Yes", "No"], help="which side is held (snapshot field `outcome`)")
    p.add_argument("--dry-run", action="store_true",
                   help="simulate via eth_call — reverts without broadcasting, so the whole path "
                        "can be rehearsed before resolution day")
    p.set_defaults(fn=lambda a: (print(json.dumps(
        redeem_one(a.condition_id, neg_risk=a.neg_risk, dry_run=a.dry_run,
                   token_id=a.token_id, outcome=a.outcome), indent=2)), 0)[1])

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
