"""Emergency swap: convert all USDC on a chain to WETH via Uniswap V3.

Used when USDC depegs. Rotating to native ETH preserves dollar value
even if USDC trades below $1.00 — we just hold ETH at whatever the new
USDC price is. Once the depeg resolves (or we accept the new floor), we
can swap back.

Behavior:
  - Read full USDC balance on the chain.
  - Fetch a Uniswap V3 quote at the 0.05% fee tier (most liquid USDC/ETH pool).
  - Slippage cap: 5%. If the quote implies > 5% loss vs. mid-market ETH price
    pulled from Coingecko, abort and Telegram. Past 5% the market is in
    chaotic price discovery and waiting is usually better than swapping.
  - Approve USDC to SwapRouter (once, MAX_UINT). Then call exactInputSingle.
  - Telegram-summarize the result.

Caveats:
  - Polygon's "USDC.e" (legacy bridged) is what Polymarket uses; this script
    handles both USDC.e and native USDC by token-pick.
  - Doesn't handle a depeg of WETH itself (very rare; if it happens, we have
    bigger problems).

Usage:
    python scripts/emergency_swap_usdc_to_eth.py --reason "usdc depeg" --chain arbitrum
    python scripts/emergency_swap_usdc_to_eth.py --reason "test" --chain polygon --token USDC.e --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

import httpx
from eth_account import Account
from web3 import Web3

import _paths as _secrets

_secrets.install_scrubbing_excepthook()

SLIPPAGE_CAP_PCT = 5.0

# Uniswap V3 contracts (same address across most EVM chains except Base)
UNISWAP_ROUTER_V1 = "0xE592427A0AEce92De3Edee1F18E0157C05861564"  # SwapRouter
QUOTER_V2 = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e"

# Per-chain config
CHAIN = {
    "arbitrum": {
        "id": 42161,
        "rpcs": ["https://arb1.arbitrum.io/rpc", "https://arbitrum.drpc.org"],
        "router": UNISWAP_ROUTER_V1,
        "quoter": QUOTER_V2,
        "weth": "0x82af49447D8a07e3bd95BD0d56f35241523fBab1",
        "tokens": {"USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"},
    },
    "base": {
        "id": 8453,
        "rpcs": ["https://mainnet.base.org", "https://base.drpc.org"],
        # Base uses SwapRouter02 at a different address
        "router": "0x2626664c2603336E57B271c5C0b26F421741e481",
        "quoter": QUOTER_V2,
        "weth": "0x4200000000000000000000000000000000000006",
        "tokens": {"USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"},
    },
    "polygon": {
        "id": 137,
        "rpcs": ["https://polygon.drpc.org", "https://polygon-bor-rpc.publicnode.com"],
        "router": UNISWAP_ROUTER_V1,
        "quoter": QUOTER_V2,
        "weth": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
        "tokens": {
            "USDC":   "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
            "USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        },
    },
    "optimism": {
        "id": 10,
        "rpcs": ["https://mainnet.optimism.io", "https://optimism.drpc.org"],
        "router": UNISWAP_ROUTER_V1,
        "quoter": QUOTER_V2,
        "weth": "0x4200000000000000000000000000000000000006",
        "tokens": {"USDC": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85"},
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

# QuoterV2.quoteExactInputSingle (Uniswap V3)
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

# SwapRouter (V1) and SwapRouter02 share this signature for exactInputSingle
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

POOL_FEE = 500   # 0.05% — most liquid USDC/ETH tier on most chains
MAX_UINT = (1 << 256) - 1


_DRY_RUN = False   # set from --dry-run in main(); gates all operator alerts


def _telegram(text: str) -> None:
    """Best-effort Telegram; never raise.

    DRY-RUN GATE (2026-08-12): gated at the FUNCTION, not per call site, so a
    new call site cannot forget it. Origin: five --dry-run drills of the
    Polymarket exit each Telegrammed "submitted: 7/8" — indistinguishable from
    a real liquidation on the operator's screen. Dry-run suppressed the ORDERS
    and did nothing about the ALARM; with a monthly drill scheduled that would
    have become a recurring false emergency.
    """
    if _DRY_RUN:
        print(f"  (dry run — operator NOT telegrammed: {text.splitlines()[0][:70]})")
        return
    try:
        subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            check=False, timeout=15, capture_output=True,
        )
    except Exception:
        pass


def _coingecko_eth_usd() -> float | None:
    """Fetch ETH/USD spot price from Coingecko's public API."""
    try:
        r = httpx.get("https://api.coingecko.com/api/v3/simple/price",
                      params={"ids": "ethereum", "vs_currencies": "usd"},
                      timeout=10)
        r.raise_for_status()
        return float(r.json()["ethereum"]["usd"])
    except Exception:
        return None


def _pick_rpc(rpcs: list[str], chain_id: int) -> Web3:
    for rpc in rpcs:
        try:
            w = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
            if w.eth.chain_id == chain_id:
                return w
        except Exception:
            continue
    raise RuntimeError(f"no working rpc for chain {chain_id}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--reason", required=True)
    p.add_argument("--chain", required=True, choices=list(CHAIN.keys()))
    p.add_argument("--token", default="USDC")
    p.add_argument("--sleeve", choices=["polymarket", "crypto"], default="crypto")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    # Gate operator alerts on dry-run (2026-08-12). Setting the module flag
    # here covers EVERY _telegram call site in the file at once — the gate
    # without this wiring is inert, which is exactly the half-fix that let the
    # same bug survive one round of repair earlier today.
    global _DRY_RUN
    _DRY_RUN = bool(getattr(args, "dry_run", False))

    cfg = CHAIN[args.chain]
    if args.token not in cfg["tokens"]:
        print(f"unknown token {args.token!r} on {args.chain}; available: {list(cfg['tokens'])}")
        return 2
    usdc_addr = Web3.to_checksum_address(cfg["tokens"][args.token])
    weth_addr = Web3.to_checksum_address(cfg["weth"])
    router_addr = Web3.to_checksum_address(cfg["router"])
    quoter_addr = Web3.to_checksum_address(cfg["quoter"])

    env = "POLYCLAUDE_WALLET" if args.sleeve == "polymarket" else "POLYCLAUDE_WALLET_CRYPTO"
    d = json.loads(_secrets.path(env).read_text())
    addr = Web3.to_checksum_address(d["address"])
    pk = d["private_key"]
    if not pk.startswith("0x"):
        pk = "0x" + pk

    w = _pick_rpc(cfg["rpcs"], cfg["id"])
    print(f"emergency_swap_usdc_to_eth  reason={args.reason!r}  dry_run={args.dry_run}")
    print(f"chain: {args.chain}  token: {args.token}  addr: {addr}")

    usdc = w.eth.contract(address=usdc_addr, abi=ERC20_ABI)
    bal_units = usdc.functions.balanceOf(addr).call()
    bal_usdc = bal_units / 1e6
    print(f"{args.token} balance: {bal_usdc:.6f}")
    if bal_units == 0:
        print("nothing to swap")
        _telegram(f"emergency_swap_usdc_to_eth: 0 {args.token} on {args.chain}; nothing to do (reason: {args.reason})")
        return 0

    quoter = w.eth.contract(address=quoter_addr, abi=QUOTER_ABI)
    quote_params = (usdc_addr, weth_addr, bal_units, POOL_FEE, 0)
    try:
        quote = quoter.functions.quoteExactInputSingle(quote_params).call()
        amount_out_quote = quote[0]
    except Exception as e:
        msg = f"quoter call failed: {str(e)[:200]}"
        print(msg)
        _telegram(f"emergency_swap_usdc_to_eth FAILED (reason: {args.reason}): {msg}")
        return 2

    eth_out_quote = amount_out_quote / 1e18
    print(f"quote: {bal_usdc:.4f} {args.token} -> {eth_out_quote:.6f} WETH")

    eth_market = _coingecko_eth_usd()
    if eth_market:
        # implied USD value of the swap output (assumes WETH pegged to ETH)
        out_usd = eth_out_quote * eth_market
        slippage = (bal_usdc - out_usd) / bal_usdc * 100 if bal_usdc > 0 else 100
        print(f"market ETH/USD: ${eth_market:.2f}, output value ~${out_usd:.4f}, slippage {slippage:.2f}%")
        if slippage > SLIPPAGE_CAP_PCT:
            msg = (f"emergency_swap_usdc_to_eth ABORT (reason: {args.reason}): "
                   f"slippage {slippage:.1f}% > cap {SLIPPAGE_CAP_PCT}%. "
                   f"market in chaotic price discovery; holding instead.")
            print(msg)
            _telegram(msg)
            return 2
    else:
        print("WARN: coingecko ETH price unavailable; proceeding without market-cross check")

    # amountOutMinimum = quote * (1 - slippage cap), giving us 5% protection at the pool level
    amount_out_min = int(amount_out_quote * (1 - SLIPPAGE_CAP_PCT / 100))

    if args.dry_run:
        _telegram(f"DRY emergency_swap_usdc_to_eth on {args.chain}: would swap {bal_usdc:.4f} "
                  f"{args.token} -> ~{eth_out_quote:.6f} WETH (reason: {args.reason})")
        return 0

    # Step 1: ensure USDC allowance to router
    allow = usdc.functions.allowance(addr, router_addr).call()
    if allow < bal_units:
        print(f"approving {args.token} -> router (current allowance {allow})...")
        nonce = w.eth.get_transaction_count(addr)
        gas_price = w.eth.gas_price
        approve_tx = usdc.functions.approve(router_addr, MAX_UINT).build_transaction({
            "from": addr,
            "nonce": nonce,
            "chainId": cfg["id"],
            "gas": 100_000,
            "maxFeePerGas": int(gas_price * 2),
            "maxPriorityFeePerGas": 0,
        })
        signed = Account.sign_transaction(approve_tx, pk)
        h = w.eth.send_raw_transaction(signed.raw_transaction)
        print(f"  approve tx: 0x{h.hex()}")
        r = w.eth.wait_for_transaction_receipt(h, timeout=120)
        if r.status != 1:
            msg = f"approve tx failed: 0x{h.hex()}"
            _telegram(f"emergency_swap_usdc_to_eth FAILED (reason: {args.reason}): {msg}")
            return 3

    # Step 2: exactInputSingle
    router = w.eth.contract(address=router_addr, abi=ROUTER_ABI)
    deadline = int(time.time()) + 600
    swap_params = (
        usdc_addr,
        weth_addr,
        POOL_FEE,
        addr,
        deadline,
        bal_units,
        amount_out_min,
        0,
    )
    nonce = w.eth.get_transaction_count(addr)
    gas_price = w.eth.gas_price
    swap_tx = router.functions.exactInputSingle(swap_params).build_transaction({
        "from": addr,
        "nonce": nonce,
        "chainId": cfg["id"],
        "gas": 400_000,
        "maxFeePerGas": int(gas_price * 2),
        "maxPriorityFeePerGas": 0,
    })
    signed = Account.sign_transaction(swap_tx, pk)
    h = w.eth.send_raw_transaction(signed.raw_transaction)
    print(f"swap tx: 0x{h.hex()}")
    r = w.eth.wait_for_transaction_receipt(h, timeout=180)
    if r.status != 1:
        msg = f"swap tx failed: 0x{h.hex()}"
        _telegram(f"emergency_swap_usdc_to_eth FAILED (reason: {args.reason}): {msg}")
        return 4

    msg = (f"emergency_swap_usdc_to_eth OK (reason: {args.reason}). "
           f"swapped {bal_usdc:.4f} {args.token} -> WETH on {args.chain}, "
           f"tx 0x{h.hex()}")
    print(msg)
    _telegram(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
