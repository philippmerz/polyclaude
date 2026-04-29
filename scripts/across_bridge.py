"""Bridge USDC across chains via Across V3 SpokePool.

Usage:
    python scripts/across_bridge.py \\
        --sleeve crypto \\
        --from-chain arbitrum --to-chain base \\
        --amount-usdc 30

Reads the wallet from POLYCLAUDE_WALLET (polymarket sleeve) or
POLYCLAUDE_WALLET_CRYPTO (crypto sleeve). Fetches a live quote from
app.across.to/api/suggested-fees, ensures USDC allowance, then calls
depositV3 on the source-chain SpokePool. Print-and-confirm style; no
hidden fallbacks.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import httpx
from eth_account import Account
from web3 import Web3

import _paths as _secrets

# ---- chain config ----------------------------------------------------------

CHAIN = {
    "arbitrum": {
        "id": 42161,
        "rpcs": [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum.drpc.org",
            "https://arbitrum-one-rpc.publicnode.com",
        ],
        "spoke": "0xe35e9842fceaCA96570B734083f4a58e8F7C5f2A",
        "tokens": {"USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"},
    },
    "base": {
        "id": 8453,
        "rpcs": [
            "https://mainnet.base.org",
            "https://base.drpc.org",
        ],
        "spoke": "0x09aea4b2242abC8bb4BB78D537A67a245A7bEC64",
        "tokens": {"USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"},
    },
    "polygon": {
        "id": 137,
        "rpcs": [
            "https://polygon.drpc.org",
            "https://polygon-bor-rpc.publicnode.com",
        ],
        "spoke": "0x9295ee1d8C5b022Be115A2AD3c30C72E34e7F096",
        "tokens": {
            "USDC": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
            "USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        },
    },
    "optimism": {
        "id": 10,
        "rpcs": [
            "https://mainnet.optimism.io",
            "https://optimism.drpc.org",
        ],
        "spoke": "0x6f26Bf09B1C792e3228e5467807a900A503c0281",
        "tokens": {"USDC": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85"},
    },
}

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function",
    },
]

# Across V3 depositV3 ABI fragment
SPOKE_DEPOSIT_V3_ABI = [
    {
        "inputs": [
            {"name": "depositor", "type": "address"},
            {"name": "recipient", "type": "address"},
            {"name": "inputToken", "type": "address"},
            {"name": "outputToken", "type": "address"},
            {"name": "inputAmount", "type": "uint256"},
            {"name": "outputAmount", "type": "uint256"},
            {"name": "destinationChainId", "type": "uint256"},
            {"name": "exclusiveRelayer", "type": "address"},
            {"name": "quoteTimestamp", "type": "uint32"},
            {"name": "fillDeadline", "type": "uint32"},
            {"name": "exclusivityDeadline", "type": "uint32"},
            {"name": "message", "type": "bytes"},
        ],
        "name": "depositV3",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
]

MAX_UINT = (1 << 256) - 1


def pick_rpc(rpcs: list[str], expected_chain_id: int) -> Web3:
    for rpc in rpcs:
        try:
            w = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
            if w.eth.chain_id == expected_chain_id:
                return w
        except Exception:
            continue
    raise RuntimeError(f"no working rpc for chain {expected_chain_id}")


def load_wallet(env: str) -> tuple[str, str]:
    d = json.loads(_secrets.path(env).read_text())
    addr = Web3.to_checksum_address(d["address"])
    pk = d["private_key"]
    if not pk.startswith("0x"):
        pk = "0x" + pk
    derived = Account.from_key(pk).address
    if derived.lower() != addr.lower():
        raise RuntimeError("wallet pk/address mismatch")
    return addr, pk


def fetch_quote(input_token: str, output_token: str, origin_chain_id: int,
                dest_chain_id: int, amount: int) -> dict:
    r = httpx.get(
        "https://app.across.to/api/suggested-fees",
        params={
            "inputToken": input_token,
            "outputToken": output_token,
            "originChainId": origin_chain_id,
            "destinationChainId": dest_chain_id,
            "amount": amount,
        },
        timeout=15,
    )
    r.raise_for_status()
    q = r.json()
    if q.get("isAmountTooLow"):
        raise RuntimeError(f"amount too low; minDeposit={q['limits']['minDeposit']}")
    return q


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sleeve", choices=["polymarket", "crypto"], required=True)
    p.add_argument("--from-chain", choices=list(CHAIN.keys()), required=True)
    p.add_argument("--to-chain", choices=list(CHAIN.keys()), required=True)
    p.add_argument("--token", default="USDC")
    p.add_argument("--amount-usdc", type=float, required=True,
                   help="amount in USDC (will be multiplied by 1e6)")
    p.add_argument("--yes", action="store_true",
                   help="skip the manual confirmation prompt")
    args = p.parse_args()

    src, dst = CHAIN[args.from_chain], CHAIN[args.to_chain]
    src_token = Web3.to_checksum_address(src["tokens"][args.token])
    dst_token = Web3.to_checksum_address(dst["tokens"][args.token])
    spoke_addr = Web3.to_checksum_address(src["spoke"])
    amount = int(args.amount_usdc * 1_000_000)

    env = "POLYCLAUDE_WALLET" if args.sleeve == "polymarket" else "POLYCLAUDE_WALLET_CRYPTO"
    addr, pk = load_wallet(env)
    w = pick_rpc(src["rpcs"], src["id"])
    print(f"sleeve: {args.sleeve}  addr: {addr}")
    print(f"  bridge: {args.amount_usdc} {args.token}  {args.from_chain} -> {args.to_chain}")
    print(f"  source spoke: {spoke_addr}")
    print(f"  ETH balance: {w.eth.get_balance(addr) / 1e18:.6f}")

    usdc = w.eth.contract(address=src_token, abi=ERC20_ABI)
    bal = usdc.functions.balanceOf(addr).call()
    if bal < amount:
        print(f"insufficient {args.token} balance: have {bal/1e6}, need {amount/1e6}")
        return 2
    print(f"  {args.token} balance: {bal/1e6}")

    print("\nfetching quote...")
    q = fetch_quote(src_token, dst_token, src["id"], dst["id"], amount)
    out = int(q["outputAmount"])
    fee = amount - out
    eta = q.get("estimatedFillTimeSec")
    print(f"  quote: {amount/1e6} -> {out/1e6} {args.token}  (fee {fee/1e6:.6f}, eta {eta}s)")
    print(f"  spokePoolAddress (api): {q['spokePoolAddress']}")
    if Web3.to_checksum_address(q["spokePoolAddress"]) != spoke_addr:
        print(f"  WARN: api spoke != hardcoded spoke; using api value")
        spoke_addr = Web3.to_checksum_address(q["spokePoolAddress"])

    if not args.yes:
        ans = input("\nproceed? [y/N] ")
        if ans.strip().lower() != "y":
            print("aborted.")
            return 1

    # Step 1: ensure allowance
    allow = usdc.functions.allowance(addr, spoke_addr).call()
    if allow < amount:
        print(f"\napproving {args.token} -> spoke (current allowance {allow})...")
        nonce = w.eth.get_transaction_count(addr)
        gas_price = w.eth.gas_price
        approve_tx = usdc.functions.approve(spoke_addr, MAX_UINT).build_transaction({
            "from": addr,
            "nonce": nonce,
            "chainId": src["id"],
            "gas": 100_000,
            "maxFeePerGas": gas_price * 2,
            "maxPriorityFeePerGas": 0,
        })
        signed = Account.sign_transaction(approve_tx, pk)
        h = w.eth.send_raw_transaction(signed.raw_transaction)
        print(f"  approve tx: 0x{h.hex()}")
        r = w.eth.wait_for_transaction_receipt(h, timeout=120)
        print(f"  approve status: {r.status}, gas used: {r.gasUsed}")
        if r.status != 1:
            return 3
    else:
        print(f"\nallowance ok ({allow})")

    # Step 2: depositV3
    print(f"\nsubmitting depositV3...")
    spoke = w.eth.contract(address=spoke_addr, abi=SPOKE_DEPOSIT_V3_ABI)
    nonce = w.eth.get_transaction_count(addr)
    gas_price = w.eth.gas_price
    deposit_tx = spoke.functions.depositV3(
        addr,
        addr,
        src_token,
        dst_token,
        amount,
        out,
        dst["id"],
        Web3.to_checksum_address(q["exclusiveRelayer"]),
        int(q["timestamp"]),
        int(q["fillDeadline"]),
        int(q["exclusivityDeadline"]),
        b"",
    ).build_transaction({
        "from": addr,
        "nonce": nonce,
        "chainId": src["id"],
        "gas": 300_000,
        "maxFeePerGas": gas_price * 2,
        "maxPriorityFeePerGas": 0,
    })
    signed = Account.sign_transaction(deposit_tx, pk)
    h = w.eth.send_raw_transaction(signed.raw_transaction)
    print(f"  deposit tx: 0x{h.hex()}")
    r = w.eth.wait_for_transaction_receipt(h, timeout=120)
    print(f"  deposit status: {r.status}, gas used: {r.gasUsed}")
    if r.status != 1:
        return 4

    print(f"\ndone. tx confirmed in block {r.blockNumber}")
    print(f"check arrival on {args.to_chain} via crypto_status.py in ~{eta}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
