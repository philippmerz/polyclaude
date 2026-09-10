#!/usr/bin/env python3
"""Convert between USDC.e and pUSD (Polymarket USD) on Polygon.

Background: Polymarket CLOB v2 collateral is **pUSD**
(0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB, 6 decimals), NOT USDC.e. New
entries / early closes on the v2 exchange require a pUSD balance; raw USDC.e
fails with "balance not enough". pUSD is minted 1:1 from USDC.e by the
CollateralOnramp contract:

    onramp.wrap(collateral=USDC.e, recipient=eoa, amount_6dec)

(verified via read-only eth_call simulation 2026-06-01.) USDC.e -> onramp
allowance is already MAX on the polymarket sleeve; the approve branch below is a
safety net for fresh wallets. The deployed CollateralOfframp converts pUSD back
to USDC.e or, when that asset route is unpaused, native USDC 1:1. That makes
realized Polymarket proceeds available to the same-chain Aave markets or to a
bridge instead of trapping them as venue float.

CLI:
    wrap_pusd.py wrap   --amount-usdc 1.7 [--sleeve polymarket] [--yes]
    wrap_pusd.py wrap   --all            # wrap entire USDC.e balance
    wrap_pusd.py unwrap --amount-pusd 1.7 [--asset USDC.e] [--yes]
    wrap_pusd.py unwrap --all             # unwrap entire pUSD balance
    wrap_pusd.py status [--sleeve polymarket]

Mirrors aave_deposit.py idioms (_paths wallet load, chain-aware Polygon gas
floor, eth_call pre-flight before broadcast).
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation

from eth_account import Account
from web3 import Web3

import _paths as _secrets

_secrets.install_scrubbing_excepthook()

POLYGON_RPCS = [
    "https://polygon.drpc.org",
    "https://polygon-bor-rpc.publicnode.com",
]
CHAIN_ID = 137

USDCE = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
USDC = Web3.to_checksum_address("0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359")
PUSD = Web3.to_checksum_address("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB")
ONRAMP = Web3.to_checksum_address("0x93070a847efEf7F70739046A929D47a521F5B8ee")
OFFRAMP = Web3.to_checksum_address("0x2957922Eb93258b93368531d39fAcCA3B4dC5854")
ASSETS = {"USDC.e": USDCE, "USDC": USDC}


class BroadcastUncertain(RuntimeError):
    """A transaction hash exists but its final state could not be confirmed."""

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "a", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"constant": True, "inputs": [{"name": "o", "type": "address"}, {"name": "s", "type": "address"}],
     "name": "allowance", "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "", "type": "bool"}],
     "stateMutability": "nonpayable", "type": "function"},
    {"anonymous": False,
     "inputs": [{"indexed": True, "name": "caller", "type": "address"},
                {"indexed": True, "name": "asset", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "amount", "type": "uint256"}],
     "name": "Unwrapped", "type": "event"},
]
ONRAMP_ABI = [
    {"inputs": [{"name": "collateral", "type": "address"},
                {"name": "recipient", "type": "address"},
                {"name": "amount", "type": "uint256"}],
     "name": "wrap", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
]
OFFRAMP_ABI = [
    {"inputs": [], "name": "COLLATERAL_TOKEN",
     "outputs": [{"name": "", "type": "address"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "asset", "type": "address"}], "name": "paused",
     "outputs": [{"name": "", "type": "bool"}],
     "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "asset", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "amount", "type": "uint256"}],
     "name": "unwrap", "outputs": [], "stateMutability": "nonpayable",
     "type": "function"},
]


def _wallet(sleeve: str) -> tuple[str, str]:
    env = "POLYCLAUDE_WALLET" if sleeve == "polymarket" else "POLYCLAUDE_WALLET_CRYPTO"
    d = json.loads(_secrets.path(env).read_text())
    addr = Web3.to_checksum_address(d["address"])
    pk = d["private_key"]
    if not pk.startswith("0x"):
        pk = "0x" + pk
    return addr, pk


def _w3() -> Web3:
    for rpc in POLYGON_RPCS:
        try:
            w = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if w.eth.chain_id == CHAIN_ID:
                return w
        except Exception:
            continue
    raise RuntimeError("no working Polygon rpc")


def _gas_fields(w: Web3, gas_limit: int) -> dict:
    """Polygon validators enforce a ~25 gwei min priority fee; floor at 30."""
    base = w.eth.gas_price
    try:
        tip = int(w.eth.max_priority_fee)
    except Exception:
        tip = 0
    tip = max(tip, 30_000_000_000)
    return {"gas": gas_limit, "maxFeePerGas": int(base * 2) + tip, "maxPriorityFeePerGas": tip}


def _send_receipt(w: Web3, pk: str, tx: dict):
    signed = Account.from_key(pk).sign_transaction(tx)
    expected_hash = Web3.keccak(signed.raw_transaction).hex()
    print(f"  prepared tx hash: {expected_hash}")
    try:
        h = w.eth.send_raw_transaction(signed.raw_transaction)
    except Exception as e:
        raise BroadcastUncertain(
            f"{expected_hash} may have been submitted but the RPC response failed "
            f"({type(e).__name__}); inspect that hash and DO NOT RETRY") from None
    txh = h.hex()
    if txh.lower() != expected_hash.lower():
        raise BroadcastUncertain(
            f"the signed hash {expected_hash} and RPC hash {txh} differ; "
            "inspect both and DO NOT RETRY")
    print(f"  submitted tx: {txh}")
    try:
        r = w.eth.wait_for_transaction_receipt(h, timeout=180)
    except Exception as e:
        raise BroadcastUncertain(
            f"{txh} was submitted but its receipt is unavailable "
            f"({type(e).__name__}); inspect that hash and DO NOT RETRY") from None
    if r.status != 1:
        raise RuntimeError(f"tx reverted: {txh}")
    return txh, r


def _send(w: Web3, pk: str, tx: dict) -> str:
    return _send_receipt(w, pk, tx)[0]


def _amount_units(raw: str, all_balance: bool, balance: int) -> int:
    """Convert a six-decimal CLI amount exactly; never round a money request."""
    if all_balance:
        return balance
    try:
        amount = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise ValueError("amount must be a decimal number") from None
    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be finite and greater than zero")
    units = amount * 1_000_000
    if units != units.to_integral_value():
        raise ValueError("amount supports at most 6 decimal places")
    return int(units)


def _validate_offramp(w: Web3, offramp, asset: str) -> None:
    """Fail closed if the live deployment is missing, mismatched, or paused."""
    if not w.eth.get_code(OFFRAMP):
        raise RuntimeError("CollateralOfframp has no deployed bytecode")
    collateral = Web3.to_checksum_address(
        offramp.functions.COLLATERAL_TOKEN().call())
    if collateral != PUSD:
        raise RuntimeError(
            f"CollateralOfframp token mismatch: expected {PUSD}, got {collateral}")
    if offramp.functions.paused(asset).call():
        raise RuntimeError("CollateralOfframp is paused for the selected asset")


def _validate_onramp(w: Web3) -> None:
    """Require bytecode at the pinned onramp before approving or wrapping."""
    if not w.eth.get_code(ONRAMP):
        raise RuntimeError("CollateralOnramp has no deployed bytecode")


def _has_exact_unwrap_event(pusd, receipt, asset: str, to: str,
                            amount_units: int) -> bool:
    """Verify the tx-local state transition instead of racy wallet deltas."""
    events = pusd.events.Unwrapped().process_receipt(receipt)
    return any(
        Web3.to_checksum_address(event["args"]["caller"]) == OFFRAMP
        and Web3.to_checksum_address(event["args"]["asset"]) == asset
        and Web3.to_checksum_address(event["args"]["to"]) == to
        and int(event["args"]["amount"]) == amount_units
        for event in events
    )


def cmd_status(args: argparse.Namespace) -> int:
    addr, _ = _wallet(args.sleeve)
    w = _w3()
    usdce = w.eth.contract(address=USDCE, abi=ERC20_ABI)
    usdc = w.eth.contract(address=USDC, abi=ERC20_ABI)
    pusd = w.eth.contract(address=PUSD, abi=ERC20_ABI)
    offramp = w.eth.contract(address=OFFRAMP, abi=OFFRAMP_ABI)
    print(f"sleeve={args.sleeve} addr=...{addr[-4:]}")
    print(f"  USDC.e:           {usdce.functions.balanceOf(addr).call()/1e6:.6f}")
    print(f"  USDC:             {usdc.functions.balanceOf(addr).call()/1e6:.6f}")
    print(f"  pUSD:             {pusd.functions.balanceOf(addr).call()/1e6:.6f}")
    print(f"  USDC.e->onramp:   {usdce.functions.allowance(addr, ONRAMP).call()/1e6:.4f}")
    print(f"  pUSD->offramp:    {pusd.functions.allowance(addr, OFFRAMP).call()/1e6:.4f}")
    _validate_offramp(w, offramp, USDCE)
    print("  offramp USDC.e:   live / unpaused / correct pUSD")
    print(
        "  offramp USDC:     "
        + ("PAUSED" if offramp.functions.paused(USDC).call() else "live / unpaused"))
    return 0


def cmd_wrap(args: argparse.Namespace) -> int:
    addr, pk = _wallet(args.sleeve)
    w = _w3()
    usdce = w.eth.contract(address=USDCE, abi=ERC20_ABI)
    pusd = w.eth.contract(address=PUSD, abi=ERC20_ABI)
    onramp = w.eth.contract(address=ONRAMP, abi=ONRAMP_ABI)

    bal = usdce.functions.balanceOf(addr).call()
    try:
        amount_units = _amount_units(args.amount_usdc, args.all, bal)
    except ValueError as e:
        print(str(e))
        return 2
    if amount_units <= 0:
        print("nothing to wrap")
        return 2
    if bal < amount_units:
        print(f"insufficient USDC.e: have {bal/1e6:.6f}, need {amount_units/1e6:.6f}")
        return 2

    try:
        _validate_onramp(w)
    except Exception as e:
        print(f"onramp validation FAILED, not broadcasting: {str(e)[:180]}")
        return 3

    pusd_before = pusd.functions.balanceOf(addr).call()
    print(f"wrap {amount_units/1e6:.6f} USDC.e -> pUSD  (sleeve={args.sleeve} addr=...{addr[-4:]})")

    # safety-net approve (allowance is normally already MAX)
    allow = usdce.functions.allowance(addr, ONRAMP).call()
    if allow < amount_units:
        if not args.yes:
            if input("approve USDC.e -> CollateralOnramp? [y/N] ").strip().lower() != "y":
                return 1
        nonce = w.eth.get_transaction_count(addr, "pending")
        atx = usdce.functions.approve(ONRAMP, 2**256 - 1).build_transaction(
            {"from": addr, "nonce": nonce, "chainId": CHAIN_ID, **_gas_fields(w, 120_000)})
        print("  approve tx:", _send(w, pk, atx))

    # pre-flight: read-only simulation; aborts before broadcast if it would revert
    try:
        onramp.functions.wrap(USDCE, addr, amount_units).call({"from": addr})
    except Exception as e:
        print(f"  pre-flight simulation FAILED, not broadcasting: {str(e)[:160]}")
        return 3

    if not args.yes:
        if input(f"broadcast wrap of {amount_units/1e6:.6f} USDC.e? [y/N] ").strip().lower() != "y":
            return 1

    try:
        gas_est = onramp.functions.wrap(USDCE, addr, amount_units).estimate_gas({"from": addr})
        gas_limit = int(gas_est * 1.3)
    except Exception:
        gas_limit = 250_000
    nonce = w.eth.get_transaction_count(addr, "pending")
    tx = onramp.functions.wrap(USDCE, addr, amount_units).build_transaction(
        {"from": addr, "nonce": nonce, "chainId": CHAIN_ID, **_gas_fields(w, gas_limit)})
    txh = _send(w, pk, tx)
    print(f"  wrap tx: {txh}")
    try:
        pusd_after = pusd.functions.balanceOf(addr).call()
        print(
            f"  pUSD: {pusd_before/1e6:.6f} -> {pusd_after/1e6:.6f}  "
            f"(+{(pusd_after-pusd_before)/1e6:.6f})")
    except Exception as e:
        print(
            "  receipt succeeded; post-flight balance display unavailable "
            f"({type(e).__name__}).")
    return 0


def cmd_unwrap(args: argparse.Namespace) -> int:
    """Unwrap pUSD 1:1 through Polymarket's deployed CollateralOfframp."""
    addr, pk = _wallet(args.sleeve)
    w = _w3()
    asset_addr = ASSETS[args.asset]
    asset = w.eth.contract(address=asset_addr, abi=ERC20_ABI)
    pusd = w.eth.contract(address=PUSD, abi=ERC20_ABI)
    offramp = w.eth.contract(address=OFFRAMP, abi=OFFRAMP_ABI)

    bal = pusd.functions.balanceOf(addr).call()
    try:
        amount_units = _amount_units(args.amount_pusd, args.all, bal)
    except ValueError as e:
        print(str(e))
        return 2
    if amount_units <= 0:
        print("nothing to unwrap")
        return 2
    if bal < amount_units:
        print(f"insufficient pUSD: have {bal/1e6:.6f}, need {amount_units/1e6:.6f}")
        return 2

    try:
        _validate_offramp(w, offramp, asset_addr)
    except Exception as e:
        print(f"offramp validation FAILED, not broadcasting: {str(e)[:180]}")
        return 3

    asset_before = asset.functions.balanceOf(addr).call()
    print(
        f"unwrap {amount_units/1e6:.6f} pUSD -> {args.asset}  "
        f"(sleeve={args.sleeve} addr=...{addr[-4:]})")

    # If more allowance is needed, approve exactly this conversion rather than
    # creating a new unlimited approval. An existing adequate allowance is
    # retained and remains visible in `status`.
    allow = pusd.functions.allowance(addr, OFFRAMP).call()
    if allow < amount_units:
        if not args.yes:
            if input("approve this pUSD amount for CollateralOfframp? [y/N] ").strip().lower() != "y":
                return 1
        nonce = w.eth.get_transaction_count(addr, "pending")
        atx = pusd.functions.approve(OFFRAMP, amount_units).build_transaction(
            {"from": addr, "nonce": nonce, "chainId": CHAIN_ID,
             **_gas_fields(w, 120_000)})
        print("  approve tx:", _send(w, pk, atx))

    # The call covers the allowance, wrapper role, vault allowance/liquidity,
    # asset pause and exact deployed behavior before an unwrap is signed.
    try:
        offramp.functions.unwrap(asset_addr, addr, amount_units).call({"from": addr})
    except Exception as e:
        print(f"  pre-flight simulation FAILED, not broadcasting: {str(e)[:160]}")
        return 3

    if not args.yes:
        if input(
                f"broadcast unwrap of {amount_units/1e6:.6f} pUSD to {args.asset}? [y/N] "
        ).strip().lower() != "y":
            return 1

    try:
        gas_est = offramp.functions.unwrap(
            asset_addr, addr, amount_units).estimate_gas({"from": addr})
        gas_limit = int(gas_est * 1.3)
    except Exception:
        gas_limit = 250_000
    nonce = w.eth.get_transaction_count(addr, "pending")
    tx = offramp.functions.unwrap(asset_addr, addr, amount_units).build_transaction(
        {"from": addr, "nonce": nonce, "chainId": CHAIN_ID,
         **_gas_fields(w, gas_limit)})
    txh, receipt = _send_receipt(w, pk, tx)
    print(f"  unwrap tx: {txh}")
    try:
        exact_event = _has_exact_unwrap_event(
            pusd, receipt, asset_addr, addr, amount_units)
    except Exception as e:
        print(
            "  RECONCILIATION REQUIRED: receipt succeeded but event parsing "
            f"failed ({type(e).__name__}). Treat the funds as moved and DO NOT RETRY.")
        return 4
    if not exact_event:
        print(
            "  RECONCILIATION REQUIRED: receipt succeeded but the exact Unwrapped "
            "event was not found. Treat the funds as moved and DO NOT RETRY.")
        return 4
    try:
        pusd_after = pusd.functions.balanceOf(addr).call()
        asset_after = asset.functions.balanceOf(addr).call()
        print(
            f"  pUSD: {bal/1e6:.6f} -> {pusd_after/1e6:.6f}; "
            f"{args.asset}: {asset_before/1e6:.6f} -> {asset_after/1e6:.6f}")
    except Exception as e:
        print(
            "  exact Unwrapped event confirmed; post-flight balance display "
            f"unavailable ({type(e).__name__}).")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Convert USDC.e <-> pUSD on Polygon")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("--sleeve", choices=["polymarket", "crypto"], default="polymarket")
    s.set_defaults(func=cmd_status)
    wr = sub.add_parser("wrap")
    amount = wr.add_mutually_exclusive_group(required=True)
    amount.add_argument("--amount-usdc")
    amount.add_argument("--all", action="store_true")
    wr.add_argument("--sleeve", choices=["polymarket", "crypto"], default="polymarket")
    wr.add_argument("--yes", action="store_true")
    wr.set_defaults(func=cmd_wrap)
    uw = sub.add_parser("unwrap")
    amount = uw.add_mutually_exclusive_group(required=True)
    amount.add_argument("--amount-pusd")
    amount.add_argument("--all", action="store_true")
    uw.add_argument("--asset", choices=sorted(ASSETS), default="USDC.e")
    uw.add_argument("--sleeve", choices=["polymarket", "crypto"], default="polymarket")
    uw.add_argument("--yes", action="store_true")
    uw.set_defaults(func=cmd_unwrap)
    args = p.parse_args()
    try:
        return args.func(args)
    except BroadcastUncertain as e:
        print(f"RECONCILIATION REQUIRED: {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
