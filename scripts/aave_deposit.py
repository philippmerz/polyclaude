"""Deposit/withdraw USDC into Aave V3 on a specified L2 chain.

Used to park idle USDC at the supply rate (~3-5% APY in 2026) instead of
0% in the wallet. Read-only `rate` subcommand prints the current supply
APY and current position. Deposits/withdrawals are signed by the
crypto-sleeve wallet (or polymarket-sleeve via --sleeve polymarket).

Usage:
    python scripts/aave_deposit.py rate --chain base
    python scripts/aave_deposit.py supply --chain base --amount-usdc 25 --yes
    python scripts/aave_deposit.py withdraw --chain base --amount-usdc 10 --yes
    python scripts/aave_deposit.py withdraw --chain base --all --yes
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from eth_account import Account
from web3 import Web3

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


# Aave V3 Pool addresses (verified via aave.com docs / chain explorer 2026-04-30)
CHAIN = {
    "base": {
        "id": 8453,
        "rpcs": ["https://mainnet.base.org", "https://base.drpc.org"],
        "pool": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
        "tokens": {"USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"},
        # aTokens = receipts you hold while supplied
        "a_tokens": {"USDC": "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB"},
    },
    "arbitrum": {
        "id": 42161,
        "rpcs": ["https://arb1.arbitrum.io/rpc", "https://arbitrum.drpc.org"],
        "pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "tokens": {"USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"},
        "a_tokens": {"USDC": "0x724dc807b04555b71ed48a6896b6F41593b8C637"},
    },
    "polygon": {
        "id": 137,
        "rpcs": ["https://polygon.drpc.org", "https://polygon-bor-rpc.publicnode.com"],
        "pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "tokens": {
            "USDC":   "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
            "USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        },
        "a_tokens": {
            "USDC":   "0xA4D94019934D8333Ef880ABFFbF2FDd611C762BD",
            "USDC.e": "0x625E7708f30cA75bfd92586e17077590C60eb4cD",
        },
    },
}

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"},
                                  {"name": "_spender", "type": "address"}],
     "name": "allowance", "outputs": [{"name": "remaining", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"},
                                    {"name": "_value", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "success", "type": "bool"}], "type": "function"},
]

# Aave V3 Pool ABI fragments
POOL_ABI = [
    {"inputs": [{"name": "asset", "type": "address"},
                {"name": "amount", "type": "uint256"},
                {"name": "onBehalfOf", "type": "address"},
                {"name": "referralCode", "type": "uint16"}],
     "name": "supply", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "asset", "type": "address"},
                {"name": "amount", "type": "uint256"},
                {"name": "to", "type": "address"}],
     "name": "withdraw", "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "asset", "type": "address"}],
     "name": "getReserveData",
     "outputs": [{"components": [
         {"name": "data", "type": "uint256"},
     ], "name": "configuration", "type": "tuple"},
                 {"name": "liquidityIndex", "type": "uint128"},
                 {"name": "currentLiquidityRate", "type": "uint128"},
                 {"name": "variableBorrowIndex", "type": "uint128"},
                 {"name": "currentVariableBorrowRate", "type": "uint128"},
                 {"name": "currentStableBorrowRate", "type": "uint128"},
                 {"name": "lastUpdateTimestamp", "type": "uint40"},
                 {"name": "id", "type": "uint16"},
                 {"name": "aTokenAddress", "type": "address"},
                 {"name": "stableDebtTokenAddress", "type": "address"},
                 {"name": "variableDebtTokenAddress", "type": "address"},
                 {"name": "interestRateStrategyAddress", "type": "address"},
                 {"name": "accruedToTreasury", "type": "uint128"},
                 {"name": "unbacked", "type": "uint128"},
                 {"name": "isolationModeTotalDebt", "type": "uint128"}],
     "stateMutability": "view", "type": "function"},
]

MAX_UINT = (1 << 256) - 1
RAY = 10**27  # Aave's fixed-point precision for rates


def _wallet(sleeve: str) -> tuple[str, str]:
    env = "POLYCLAUDE_WALLET" if sleeve == "polymarket" else "POLYCLAUDE_WALLET_CRYPTO"
    d = json.loads(_secrets.path(env).read_text())
    addr = Web3.to_checksum_address(d["address"])
    pk = d["private_key"]
    if not pk.startswith("0x"):
        pk = "0x" + pk
    return addr, pk


def _w3(chain: str) -> Web3:
    cfg = CHAIN[chain]
    for rpc in cfg["rpcs"]:
        try:
            w = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
            if w.eth.chain_id == cfg["id"]:
                return w
        except Exception:
            continue
    raise RuntimeError(f"no working rpc for {chain}")


def cmd_rate(args: argparse.Namespace) -> int:
    cfg = CHAIN[args.chain]
    w = _w3(args.chain)
    pool = w.eth.contract(address=Web3.to_checksum_address(cfg["pool"]), abi=POOL_ABI)
    asset = Web3.to_checksum_address(cfg["tokens"][args.token])
    a_token_addr = Web3.to_checksum_address(cfg["a_tokens"][args.token])
    addr, _ = _wallet(args.sleeve)

    rd = pool.functions.getReserveData(asset).call()
    # currentLiquidityRate is at index 2, in RAY (1e27) units, annualised
    liquidity_rate_ray = rd[2]
    apy = liquidity_rate_ray / RAY * 100  # convert RAY-fraction to %
    a_token = w.eth.contract(address=a_token_addr, abi=ERC20_ABI)
    bal_a = a_token.functions.balanceOf(addr).call() / 1e6
    plain = w.eth.contract(address=asset, abi=ERC20_ABI)
    bal_plain = plain.functions.balanceOf(addr).call() / 1e6

    print(f"{args.chain}/{args.token} (sleeve {args.sleeve}, {addr})")
    print(f"  current supply APY:  {apy:.3f}%")
    print(f"  walleted (idle):     {bal_plain:.4f} {args.token}")
    print(f"  supplied (a{args.token}): {bal_a:.4f}  ({bal_a / max(bal_plain + bal_a, 1e-9) * 100:.1f}% of total)")
    return 0


def cmd_supply(args: argparse.Namespace) -> int:
    cfg = CHAIN[args.chain]
    asset = Web3.to_checksum_address(cfg["tokens"][args.token])
    pool_addr = Web3.to_checksum_address(cfg["pool"])
    addr, pk = _wallet(args.sleeve)
    w = _w3(args.chain)

    amount_units = int(args.amount_usdc * 1_000_000)
    plain = w.eth.contract(address=asset, abi=ERC20_ABI)
    bal = plain.functions.balanceOf(addr).call()
    if bal < amount_units:
        print(f"insufficient {args.token}: have {bal/1e6}, need {args.amount_usdc}")
        return 2

    if not args.yes:
        ans = input(f"supply {args.amount_usdc} {args.token} on {args.chain} from {args.sleeve} sleeve? [y/N] ")
        if ans.strip().lower() != "y":
            return 1

    allow = plain.functions.allowance(addr, pool_addr).call()
    if allow < amount_units:
        print(f"approving {args.token} -> Aave Pool...")
        nonce = w.eth.get_transaction_count(addr)
        gas_price = w.eth.gas_price
        approve_tx = plain.functions.approve(pool_addr, MAX_UINT).build_transaction({
            "from": addr, "nonce": nonce, "chainId": cfg["id"],
            "gas": 100_000,
            "maxFeePerGas": max(int(gas_price * 3), int(gas_price + 1_000_000)),
            "maxPriorityFeePerGas": 1_000_000,
        })
        h = w.eth.send_raw_transaction(
            Account.sign_transaction(approve_tx, pk).raw_transaction)
        print(f"  approve tx: 0x{h.hex()}")
        r = w.eth.wait_for_transaction_receipt(h, timeout=120)
        if r.status != 1:
            print(f"  approve failed")
            return 3

    print(f"supplying {args.amount_usdc} {args.token}...")
    pool = w.eth.contract(address=pool_addr, abi=POOL_ABI)
    nonce = w.eth.get_transaction_count(addr)
    gas_price = w.eth.gas_price
    supply_tx = pool.functions.supply(asset, amount_units, addr, 0).build_transaction({
        "from": addr, "nonce": nonce, "chainId": cfg["id"],
        "gas": 400_000,
        "maxFeePerGas": int(gas_price * 2),
        "maxPriorityFeePerGas": 0,
    })
    h = w.eth.send_raw_transaction(
        Account.sign_transaction(supply_tx, pk).raw_transaction)
    print(f"  supply tx: 0x{h.hex()}")
    r = w.eth.wait_for_transaction_receipt(h, timeout=120)
    if r.status != 1:
        print(f"  supply failed")
        return 4
    print(f"done. now earning supply APY in a{args.token}.")
    return 0


def cmd_withdraw(args: argparse.Namespace) -> int:
    cfg = CHAIN[args.chain]
    asset = Web3.to_checksum_address(cfg["tokens"][args.token])
    pool_addr = Web3.to_checksum_address(cfg["pool"])
    a_token_addr = Web3.to_checksum_address(cfg["a_tokens"][args.token])
    addr, pk = _wallet(args.sleeve)
    w = _w3(args.chain)

    if args.all:
        amount_units = MAX_UINT  # Aave special-cases MAX_UINT to "withdraw all"
        a_token = w.eth.contract(address=a_token_addr, abi=ERC20_ABI)
        bal_a = a_token.functions.balanceOf(addr).call() / 1e6
        amount_label = f"{bal_a:.4f} (full balance)"
    else:
        amount_units = int(args.amount_usdc * 1_000_000)
        amount_label = f"{args.amount_usdc}"

    if not args.yes:
        ans = input(f"withdraw {amount_label} {args.token} on {args.chain} from {args.sleeve} sleeve? [y/N] ")
        if ans.strip().lower() != "y":
            return 1

    pool = w.eth.contract(address=pool_addr, abi=POOL_ABI)
    nonce = w.eth.get_transaction_count(addr)
    gas_price = w.eth.gas_price
    tx = pool.functions.withdraw(asset, amount_units, addr).build_transaction({
        "from": addr, "nonce": nonce, "chainId": cfg["id"],
        "gas": 400_000,
        "maxFeePerGas": int(gas_price * 2),
        "maxPriorityFeePerGas": 0,
    })
    h = w.eth.send_raw_transaction(Account.sign_transaction(tx, pk).raw_transaction)
    print(f"  withdraw tx: 0x{h.hex()}")
    r = w.eth.wait_for_transaction_receipt(h, timeout=120)
    if r.status != 1:
        print("  withdraw failed")
        return 4
    print("done.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    common = lambda s: (
        s.add_argument("--chain", required=True, choices=list(CHAIN.keys())),
        s.add_argument("--token", default="USDC"),
        s.add_argument("--sleeve", choices=["polymarket", "crypto"], default="crypto"),
    )
    s = sub.add_parser("rate")
    common(s)
    s.set_defaults(fn=cmd_rate)
    s = sub.add_parser("supply")
    common(s)
    s.add_argument("--amount-usdc", type=float, required=True)
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_supply)
    s = sub.add_parser("withdraw")
    common(s)
    s.add_argument("--amount-usdc", type=float, default=0)
    s.add_argument("--all", action="store_true")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_withdraw)
    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
