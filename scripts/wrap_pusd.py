#!/usr/bin/env python3
"""Wrap USDC.e -> pUSD (Polymarket USD) on Polygon, so the CLOB v2 collateral
balance can fund new entries.

Background: Polymarket CLOB v2 collateral is **pUSD**
(0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB, 6 decimals), NOT USDC.e. New
entries / early closes on the v2 exchange require a pUSD balance; raw USDC.e
fails with "balance not enough". pUSD is minted 1:1 from USDC.e by the
CollateralOnramp contract:

    onramp.wrap(collateral=USDC.e, recipient=eoa, amount_6dec)

(verified via read-only eth_call simulation 2026-06-01.) USDC.e -> onramp
allowance is already MAX on the polymarket sleeve; the approve branch below is a
safety net for fresh wallets. Use `unwrap`-equivalent is not provided — pUSD is
spent by trading or redeemed via resolution.

CLI:
    wrap_pusd.py wrap   --amount-usdc 1.7 [--sleeve polymarket] [--yes]
    wrap_pusd.py wrap   --all            # wrap entire USDC.e balance
    wrap_pusd.py status [--sleeve polymarket]

Mirrors aave_deposit.py idioms (_paths wallet load, chain-aware Polygon gas
floor, eth_call pre-flight before broadcast).
"""
from __future__ import annotations

import argparse
import json
import sys

from eth_account import Account
from web3 import Web3

import _paths as _secrets

POLYGON_RPCS = [
    "https://polygon.drpc.org",
    "https://polygon-bor-rpc.publicnode.com",
]
CHAIN_ID = 137

USDCE = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
PUSD = Web3.to_checksum_address("0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB")
ONRAMP = Web3.to_checksum_address("0x93070a847efEf7F70739046A929D47a521F5B8ee")

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
]
ONRAMP_ABI = [
    {"inputs": [{"name": "collateral", "type": "address"},
                {"name": "recipient", "type": "address"},
                {"name": "amount", "type": "uint256"}],
     "name": "wrap", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
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


def _send(w: Web3, pk: str, tx: dict) -> str:
    signed = Account.from_key(pk).sign_transaction(tx)
    h = w.eth.send_raw_transaction(signed.raw_transaction)
    r = w.eth.wait_for_transaction_receipt(h, timeout=180)
    if r.status != 1:
        raise RuntimeError(f"tx reverted: {h.hex()}")
    return h.hex()


def cmd_status(args: argparse.Namespace) -> int:
    addr, _ = _wallet(args.sleeve)
    w = _w3()
    usdce = w.eth.contract(address=USDCE, abi=ERC20_ABI)
    pusd = w.eth.contract(address=PUSD, abi=ERC20_ABI)
    print(f"sleeve={args.sleeve} addr=...{addr[-4:]}")
    print(f"  USDC.e:           {usdce.functions.balanceOf(addr).call()/1e6:.6f}")
    print(f"  pUSD:             {pusd.functions.balanceOf(addr).call()/1e6:.6f}")
    print(f"  USDC.e->onramp:   {usdce.functions.allowance(addr, ONRAMP).call()/1e6:.4f}")
    return 0


def cmd_wrap(args: argparse.Namespace) -> int:
    addr, pk = _wallet(args.sleeve)
    w = _w3()
    usdce = w.eth.contract(address=USDCE, abi=ERC20_ABI)
    pusd = w.eth.contract(address=PUSD, abi=ERC20_ABI)
    onramp = w.eth.contract(address=ONRAMP, abi=ONRAMP_ABI)

    bal = usdce.functions.balanceOf(addr).call()
    if args.all:
        amount_units = bal
    else:
        amount_units = int(round(args.amount_usdc * 1_000_000))
    if amount_units <= 0:
        print("nothing to wrap")
        return 2
    if bal < amount_units:
        print(f"insufficient USDC.e: have {bal/1e6:.6f}, need {amount_units/1e6:.6f}")
        return 2

    pusd_before = pusd.functions.balanceOf(addr).call()
    print(f"wrap {amount_units/1e6:.6f} USDC.e -> pUSD  (sleeve={args.sleeve} addr=...{addr[-4:]})")

    # safety-net approve (allowance is normally already MAX)
    allow = usdce.functions.allowance(addr, ONRAMP).call()
    if allow < amount_units:
        if not args.yes:
            if input("approve USDC.e -> CollateralOnramp? [y/N] ").strip().lower() != "y":
                return 1
        nonce = w.eth.get_transaction_count(addr)
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
    nonce = w.eth.get_transaction_count(addr)
    tx = onramp.functions.wrap(USDCE, addr, amount_units).build_transaction(
        {"from": addr, "nonce": nonce, "chainId": CHAIN_ID, **_gas_fields(w, gas_limit)})
    txh = _send(w, pk, tx)
    pusd_after = pusd.functions.balanceOf(addr).call()
    print(f"  wrap tx: {txh}")
    print(f"  pUSD: {pusd_before/1e6:.6f} -> {pusd_after/1e6:.6f}  (+{(pusd_after-pusd_before)/1e6:.6f})")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Wrap USDC.e -> pUSD on Polygon")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status")
    s.add_argument("--sleeve", choices=["polymarket", "crypto"], default="polymarket")
    s.set_defaults(func=cmd_status)
    wr = sub.add_parser("wrap")
    wr.add_argument("--amount-usdc", type=float, default=0)
    wr.add_argument("--all", action="store_true")
    wr.add_argument("--sleeve", choices=["polymarket", "crypto"], default="polymarket")
    wr.add_argument("--yes", action="store_true")
    wr.set_defaults(func=cmd_wrap)
    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
