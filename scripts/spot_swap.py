"""General spot swap via Uniswap V3 exactInputSingle. Adapted from the proven
emergency_swap_usdc_to_eth.py path (same router/quoter/ABIs/gas pattern), but:
any token pair, explicit --amount, decimals queried on-chain, 1% default
slippage cap (not the emergency 5%), and a --yes confirm.

Built 2026-06-10 for the operator-directed ARB entry (conditional on the
Jun 16 DAO revenue-share vote). Usage:

    # quote only
    python scripts/spot_swap.py --chain arbitrum --sleeve crypto \
        --token-in USDC --token-out ARB --amount 15 --dry-run
    # execute
    python scripts/spot_swap.py --chain arbitrum --sleeve crypto \
        --token-in USDC --token-out ARB --amount 15 --yes
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

UNISWAP_ROUTER_V1 = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
QUOTER_V2 = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e"

CHAIN = {
    "arbitrum": {
        "id": 42161,
        "rpcs": ["https://arb1.arbitrum.io/rpc", "https://arbitrum.drpc.org",
                 "https://arbitrum-one-rpc.publicnode.com"],
        "router": UNISWAP_ROUTER_V1,
        "quoter": QUOTER_V2,
        "tokens": {
            "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "USDC.e": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "WETH": "0x82af49447D8a07e3bd95BD0d56f35241523fBab1",
            "ARB":  "0x912CE59144191C1204E64559FE8253a0e49E6548",
        },
    },
    "polygon": {
        "id": 137,
        "rpcs": ["https://polygon.drpc.org", "https://polygon-bor-rpc.publicnode.com"],
        "router": UNISWAP_ROUTER_V1,
        "quoter": QUOTER_V2,
        "tokens": {
            "USDC":   "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
            "USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "WETH":   "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        },
    },
    "base": {
        "id": 8453,
        "rpcs": ["https://mainnet.base.org", "https://base.drpc.org"],
        "router": "0x2626664c2603336E57B271c5C0b26F421741e481",  # SwapRouter02
        "quoter": QUOTER_V2,
        "tokens": {
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "WETH": "0x4200000000000000000000000000000000000006",
        },
    },
}

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals",
     "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol",
     "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"},
                                  {"name": "_spender", "type": "address"}],
     "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_spender", "type": "address"},
                                   {"name": "_value", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]

QUOTER_ABI = [{
    "inputs": [{"components": [
        {"name": "tokenIn", "type": "address"},
        {"name": "tokenOut", "type": "address"},
        {"name": "amountIn", "type": "uint256"},
        {"name": "fee", "type": "uint24"},
        {"name": "sqrtPriceLimitX96", "type": "uint160"},
    ], "name": "params", "type": "tuple"}],
    "name": "quoteExactInputSingle",
    "outputs": [
        {"name": "amountOut", "type": "uint256"},
        {"name": "sqrtPriceX96After", "type": "uint160"},
        {"name": "initializedTicksCrossed", "type": "uint32"},
        {"name": "gasEstimate", "type": "uint256"},
    ],
    "stateMutability": "nonpayable",
    "type": "function",
}]

ROUTER_ABI = [{
    "inputs": [{"components": [
        {"name": "tokenIn", "type": "address"},
        {"name": "tokenOut", "type": "address"},
        {"name": "fee", "type": "uint24"},
        {"name": "recipient", "type": "address"},
        {"name": "deadline", "type": "uint256"},
        {"name": "amountIn", "type": "uint256"},
        {"name": "amountOutMinimum", "type": "uint256"},
        {"name": "sqrtPriceLimitX96", "type": "uint160"},
    ], "name": "params", "type": "tuple"}],
    "name": "exactInputSingle",
    "outputs": [{"name": "amountOut", "type": "uint256"}],
    "stateMutability": "payable",
    "type": "function",
}]

MAX_UINT = (1 << 256) - 1
FEE_TIERS = [500, 3000, 10000]  # tried in order when --fee not given


def _pick_rpc(rpcs: list[str], chain_id: int) -> Web3:
    for rpc in rpcs:
        try:
            w = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
            if w.eth.chain_id == chain_id:
                return w
        except Exception:
            continue
    raise RuntimeError(f"no working rpc for chain {chain_id}")


def _resolve_token(cfg: dict, w: Web3, name_or_addr: str):
    addr = cfg["tokens"].get(name_or_addr.upper()) or cfg["tokens"].get(name_or_addr) or name_or_addr
    addr = Web3.to_checksum_address(addr)
    c = w.eth.contract(address=addr, abi=ERC20_ABI)
    return addr, c, c.functions.symbol().call(), c.functions.decimals().call()


def main() -> int:
    p = argparse.ArgumentParser(description="Uniswap V3 spot swap (exactInputSingle)")
    p.add_argument("--chain", required=True, choices=list(CHAIN.keys()))
    p.add_argument("--sleeve", choices=["polymarket", "crypto"], default="crypto")
    p.add_argument("--token-in", required=True, help="symbol from chain map, or address")
    p.add_argument("--token-out", required=True, help="symbol from chain map, or address")
    p.add_argument("--amount", type=float, default=None,
                   help="amount of token-in (human units); omit with --all")
    p.add_argument("--all", action="store_true", help="swap full token-in balance")
    p.add_argument("--fee", type=int, default=None,
                   help="pool fee tier (500/3000/10000); default: first tier that quotes")
    p.add_argument("--slippage-pct", type=float, default=1.0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--yes", action="store_true", help="skip interactive confirm")
    args = p.parse_args()

    cfg = CHAIN[args.chain]
    env = "POLYCLAUDE_WALLET" if args.sleeve == "polymarket" else "POLYCLAUDE_WALLET_CRYPTO"
    d = json.loads(_secrets.path(env).read_text())
    addr = Web3.to_checksum_address(d["address"])
    pk = d["private_key"] if d["private_key"].startswith("0x") else "0x" + d["private_key"]

    w = _pick_rpc(cfg["rpcs"], cfg["id"])
    in_addr, in_c, in_sym, in_dec = _resolve_token(cfg, w, args.token_in)
    out_addr, _, out_sym, out_dec = _resolve_token(cfg, w, args.token_out)

    bal_units = in_c.functions.balanceOf(addr).call()
    if args.all:
        amount_units = bal_units
    elif args.amount:
        amount_units = int(args.amount * 10**in_dec)
    else:
        print("ERROR: provide --amount or --all", file=sys.stderr)
        return 2
    if amount_units <= 0 or amount_units > bal_units:
        print(f"ERROR: amount {amount_units / 10**in_dec:.6f} {in_sym} vs balance "
              f"{bal_units / 10**in_dec:.6f}", file=sys.stderr)
        return 2

    quoter = w.eth.contract(address=Web3.to_checksum_address(cfg["quoter"]), abi=QUOTER_ABI)
    tiers = [args.fee] if args.fee else FEE_TIERS
    quote_out, fee_used = None, None
    for tier in tiers:
        try:
            q = quoter.functions.quoteExactInputSingle(
                (in_addr, out_addr, amount_units, tier, 0)).call()
            if q[0] > 0:
                quote_out, fee_used = q[0], tier
                break
        except Exception:
            continue
    if quote_out is None:
        print(f"ERROR: no quotable pool for {in_sym}->{out_sym} in tiers {tiers}", file=sys.stderr)
        return 2

    human_in = amount_units / 10**in_dec
    human_out = quote_out / 10**out_dec
    px = human_in / human_out if human_out else float("inf")
    print(f"quote ({args.chain}, fee {fee_used/1e4:.2f}%): "
          f"{human_in:.6f} {in_sym} -> {human_out:.6f} {out_sym}  (px {px:.6f} {in_sym}/{out_sym})")

    amount_out_min = int(quote_out * (1 - args.slippage_pct / 100))
    if args.dry_run:
        print(f"DRY RUN — would swap with amountOutMinimum {amount_out_min / 10**out_dec:.6f} {out_sym}")
        return 0
    if not args.yes:
        if input(f"swap {human_in:.6f} {in_sym} -> ~{human_out:.6f} {out_sym}? [y/N] ").strip().lower() != "y":
            print("aborted")
            return 1

    router_addr = Web3.to_checksum_address(cfg["router"])
    if in_c.functions.allowance(addr, router_addr).call() < amount_units:
        tx = in_c.functions.approve(router_addr, MAX_UINT).build_transaction({
            "from": addr, "nonce": w.eth.get_transaction_count(addr), "chainId": cfg["id"],
            "gas": 100_000, "maxFeePerGas": int(w.eth.gas_price * 2), "maxPriorityFeePerGas": 0,
        })
        h = w.eth.send_raw_transaction(Account.sign_transaction(tx, pk).raw_transaction)
        print(f"approve tx: 0x{h.hex()}")
        if w.eth.wait_for_transaction_receipt(h, timeout=120).status != 1:
            print("ERROR: approve failed", file=sys.stderr)
            return 3

    router = w.eth.contract(address=router_addr, abi=ROUTER_ABI)
    tx = router.functions.exactInputSingle((
        in_addr, out_addr, fee_used, addr, int(time.time()) + 600,
        amount_units, amount_out_min, 0,
    )).build_transaction({
        "from": addr, "nonce": w.eth.get_transaction_count(addr), "chainId": cfg["id"],
        "gas": 400_000, "maxFeePerGas": int(w.eth.gas_price * 2), "maxPriorityFeePerGas": 0,
    })
    h = w.eth.send_raw_transaction(Account.sign_transaction(tx, pk).raw_transaction)
    print(f"swap tx: 0x{h.hex()}")
    if w.eth.wait_for_transaction_receipt(h, timeout=180).status != 1:
        print("ERROR: swap failed", file=sys.stderr)
        return 4
    print(f"OK: swapped {human_in:.6f} {in_sym} -> ~{human_out:.6f} {out_sym} (min {amount_out_min / 10**out_dec:.6f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
