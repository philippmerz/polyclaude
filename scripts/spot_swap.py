"""General spot swap via Uniswap V3 exactInputSingle. Adapted from the proven
emergency_swap_usdc_to_eth.py path (same router/quoter/ABIs/gas pattern), but:
any token pair, explicit --amount, decimals queried on-chain, 1% default
slippage cap (not the emergency 5%), best-output fee-tier selection, an
independent execution floor, and a --yes confirm.

Built 2026-06-10 for the operator-directed ARB entry (conditional on the
Jun 16 DAO revenue-share vote). Usage:

    # quote only
    python scripts/spot_swap.py --chain arbitrum --sleeve crypto \
        --token-in USDC --token-out ARB --amount 15 --dry-run
    # execute
    python scripts/spot_swap.py --chain arbitrum --sleeve crypto \
        --token-in USDC --token-out ARB --amount 15 \
        --min-out <independently-derived-token-floor> --yes
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR

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
            "AAVE": "0xba5DdD1f9d7F570dc94a51479a000E3BCE967196",
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
FEE_TIERS = [100, 500, 3000, 10000]


def _select_best_quote(candidates: list[tuple[int, int]]) -> tuple[int, int]:
    """Select the fee tier with maximum executable output, never first-nonzero.

    A nonzero Uniswap quote proves only that a path exists.  It does not prove
    usable liquidity: the Arbitrum AAVE 0.05% pool returned ~0.000003 AAVE for
    $7 while the 0.30% pool returned ~0.0574.  First-nonzero routing would have
    converted essentially the whole input into price impact.
    """
    clean: list[tuple[int, int]] = []
    for tier, amount_out in candidates:
        if isinstance(tier, bool) or isinstance(amount_out, bool):
            raise RuntimeError("malformed quote candidate")
        try:
            tier = int(tier)
            amount_out = int(amount_out)
        except (TypeError, ValueError):
            raise RuntimeError("malformed quote candidate")
        if tier <= 0 or amount_out <= 0:
            raise RuntimeError("nonpositive quote candidate")
        clean.append((tier, amount_out))
    if not clean:
        raise RuntimeError("no positive quote candidates")
    return max(clean, key=lambda row: row[1])


def _execution_floor(quote_out: int, slippage_pct: object,
                     independent_min_out: int | None) -> int:
    """Combine quote-relative slippage with a user-supplied independent floor."""
    if isinstance(quote_out, bool) or isinstance(slippage_pct, bool):
        raise RuntimeError("invalid execution-floor inputs")
    try:
        quote_out = int(quote_out)
        slippage = Decimal(str(slippage_pct))
    except (InvalidOperation, TypeError, ValueError):
        raise RuntimeError("invalid execution-floor inputs")
    if (quote_out <= 0 or not slippage.is_finite()
            or not Decimal(0) <= slippage < Decimal(100)):
        raise RuntimeError("invalid execution-floor inputs")
    quote_floor = int((Decimal(quote_out) * (Decimal(100) - slippage)
                       / Decimal(100)).to_integral_value(rounding=ROUND_FLOOR))
    if independent_min_out is None:
        return quote_floor
    if isinstance(independent_min_out, bool):
        raise RuntimeError("invalid independent minimum output")
    try:
        independent_min_out = int(independent_min_out)
    except (TypeError, ValueError):
        raise RuntimeError("invalid independent minimum output")
    if independent_min_out <= 0:
        raise RuntimeError("invalid independent minimum output")
    if independent_min_out > quote_out:
        raise RuntimeError("independent minimum output exceeds the live quote")
    return max(quote_floor, independent_min_out)


def _human_to_units(value: object, decimals: int, *, round_up: bool) -> int:
    """Convert a human token amount exactly; minimums round toward safety."""
    if isinstance(value, bool) or isinstance(decimals, bool):
        raise RuntimeError("invalid token amount")
    try:
        amount = Decimal(str(value))
        decimals = int(decimals)
    except (InvalidOperation, TypeError, ValueError):
        raise RuntimeError("invalid token amount")
    if not amount.is_finite() or amount <= 0 or not 0 <= decimals <= 255:
        raise RuntimeError("invalid token amount")
    rounding = ROUND_CEILING if round_up else ROUND_FLOOR
    units = int((amount * (Decimal(10) ** decimals)).to_integral_value(
        rounding=rounding))
    if units <= 0:
        raise RuntimeError("token amount is below one base unit")
    return units


def _quote_fee_tiers(quoter, in_addr: str, out_addr: str, amount_units: int,
                     tiers: list[int], attempts: int = 2
                     ) -> tuple[list[tuple[int, int]], dict[int, int], list[int]]:
    """Quote each tier with a bounded retry and retain QuoterV2 gas evidence."""
    candidates: list[tuple[int, int]] = []
    gas_estimates: dict[int, int] = {}
    failures: list[int] = []
    for tier in tiers:
        quote = None
        for _ in range(attempts):
            try:
                result = quoter.functions.quoteExactInputSingle(
                    (in_addr, out_addr, amount_units, tier, 0)).call()
                if int(result[0]) > 0:
                    quote = result
                    break
            except Exception:
                continue
        if quote is None:
            failures.append(tier)
            continue
        candidates.append((tier, int(quote[0])))
        try:
            gas = int(quote[3])
        except (IndexError, TypeError, ValueError):
            gas = 0
        if gas >= 0:
            gas_estimates[tier] = gas
    return candidates, gas_estimates, failures


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
    p.add_argument("--amount", default=None,
                   help="amount of token-in (human units); omit with --all")
    p.add_argument("--all", action="store_true", help="swap full token-in balance")
    p.add_argument("--fee", type=int, default=None,
                   help="explicit pool fee tier; default: quote 100/500/3000/10000 and "
                        "use the tier returning the most token-out")
    p.add_argument("--slippage-pct", default="1.0")
    p.add_argument("--min-out", default=None,
                   help="independently derived minimum token-out in human units. Required "
                        "for execution; combined with the quote-relative slippage floor. "
                        "Do not copy an unverified router quote into this field.")
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
    if args.all and args.amount is not None:
        print("ERROR: choose either --amount or --all", file=sys.stderr)
        return 2
    if args.all:
        amount_units = bal_units
    elif args.amount is not None:
        try:
            amount_units = _human_to_units(args.amount, in_dec, round_up=False)
        except RuntimeError as exc:
            print(f"ERROR: --amount {exc}", file=sys.stderr)
            return 2
    else:
        print("ERROR: provide --amount or --all", file=sys.stderr)
        return 2
    if amount_units <= 0 or amount_units > bal_units:
        print(f"ERROR: amount {amount_units / 10**in_dec:.6f} {in_sym} vs balance "
              f"{bal_units / 10**in_dec:.6f}", file=sys.stderr)
        return 2

    quoter = w.eth.contract(address=Web3.to_checksum_address(cfg["quoter"]), abi=QUOTER_ABI)
    tiers = [args.fee] if args.fee else FEE_TIERS
    quote_candidates, gas_estimates, failed_tiers = _quote_fee_tiers(
        quoter, in_addr, out_addr, amount_units, tiers)
    if failed_tiers:
        print("NOTICE: fee tiers unquoted after two attempts: "
              + ", ".join(str(tier) for tier in failed_tiers), file=sys.stderr)
    if not quote_candidates:
        print(f"ERROR: no quotable pool for {in_sym}->{out_sym} in tiers {tiers}", file=sys.stderr)
        return 2
    try:
        fee_used, quote_out = _select_best_quote(quote_candidates)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    human_in = amount_units / 10**in_dec
    human_out = quote_out / 10**out_dec
    if args.fee is None:
        print("fee-tier quotes (maximum gross output wins; gas estimates shown):")
        for tier, candidate_out in sorted(quote_candidates):
            candidate_human = candidate_out / 10**out_dec
            candidate_px = (human_in / candidate_human
                            if candidate_human else float("inf"))
            chosen = "  <- SELECTED" if tier == fee_used else ""
            gas_note = (f", quoter gas {gas_estimates[tier]:,}"
                        if gas_estimates.get(tier) else "")
            print(f"  {tier/1e4:.2f}%: {candidate_human:.8f} {out_sym} "
                  f"(px {candidate_px:.6f} {in_sym}/{out_sym}{gas_note}){chosen}")
        outputs = [candidate_out for _, candidate_out in quote_candidates]
        if len(outputs) > 1 and min(outputs) * 2 < max(outputs):
            print("WARNING: fee-tier outputs diverge by >2x; at least one pool is "
                  "dust, exhausted, or badly priced.", file=sys.stderr)
    px = human_in / human_out if human_out else float("inf")
    print(f"quote ({args.chain}, fee {fee_used/1e4:.2f}%): "
          f"{human_in:.6f} {in_sym} -> {human_out:.6f} {out_sym}  (px {px:.6f} {in_sym}/{out_sym})")

    independent_min_units = None
    if args.min_out is not None:
        try:
            independent_min_units = _human_to_units(
                args.min_out, out_dec, round_up=True)
        except RuntimeError as exc:
            print(f"ERROR: --min-out {exc}", file=sys.stderr)
            return 2
    if not args.dry_run and independent_min_units is None:
        print("ERROR: execution requires --min-out from an independent fair/reference "
              "price; a router quote alone cannot detect a poisoned pool", file=sys.stderr)
        return 2
    try:
        amount_out_min = _execution_floor(
            quote_out, args.slippage_pct, independent_min_units)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.dry_run:
        print(f"DRY RUN — would swap with amountOutMinimum {amount_out_min / 10**out_dec:.6f} {out_sym}")
        return 0
    print(f"execution protection: independent floor "
          f"{independent_min_units / 10**out_dec:.8f} {out_sym}; current effective "
          f"amountOutMinimum {amount_out_min / 10**out_dec:.8f} {out_sym}")
    if not args.yes:
        if input(f"swap {human_in:.6f} {in_sym} -> ~{human_out:.6f} {out_sym}, "
                 f"never below {amount_out_min / 10**out_dec:.8f} {out_sym}? "
                 "[y/N] ").strip().lower() != "y":
            print("aborted")
            return 1
    confirmed_min_units = amount_out_min

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

    # The operator prompt and a token approval can make the preview quote
    # minutes old. Re-run every tier immediately before signing; the independent
    # floor and the exact operator-confirmed effective floor remain fixed while
    # the quote-relative floor and selected tier move to current state.
    fresh_candidates, fresh_gas, fresh_failures = _quote_fee_tiers(
        quoter, in_addr, out_addr, amount_units, tiers)
    if fresh_failures:
        print("NOTICE: signing-time fee tiers unquoted after two attempts: "
              + ", ".join(str(tier) for tier in fresh_failures), file=sys.stderr)
    if not fresh_candidates:
        print("ERROR: no pool quoted at signing time; no swap sent", file=sys.stderr)
        return 2
    try:
        fresh_fee, fresh_quote = _select_best_quote(fresh_candidates)
        fresh_min = _execution_floor(
            fresh_quote, args.slippage_pct,
            max(independent_min_units, confirmed_min_units))
    except RuntimeError as exc:
        print(f"ERROR: signing-time route failed protection: {exc}", file=sys.stderr)
        return 2
    old_fee, old_quote = fee_used, quote_out
    fee_used, quote_out, amount_out_min = fresh_fee, fresh_quote, fresh_min
    human_out = quote_out / 10**out_dec
    px = human_in / human_out if human_out else float("inf")
    gas_note = (f", quoter gas {fresh_gas[fee_used]:,}"
                if fresh_gas.get(fee_used) else "")
    movement = (f" (preview fee {old_fee}, output "
                f"{old_quote / 10**out_dec:.8f})"
                if old_fee != fee_used or old_quote != quote_out else "")
    print(f"signing-time quote: fee {fee_used}, {human_out:.8f} {out_sym}, "
          f"px {px:.6f} {in_sym}/{out_sym}{gas_note}; minimum "
          f"{amount_out_min / 10**out_dec:.8f}{movement}")

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
