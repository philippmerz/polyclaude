"""One authoritative bankroll number across every asset home. Read-only.

Sums: PM positions MTM (data-api) + stables/pUSD/Aave-aTokens on every chain
for BOTH sleeves + native gas tokens (POL, ETH) at live CoinGecko prices.
Warns (never silently omits) when a component can't be valued: dead RPC,
CoinGecko down, open Ostium trades.

Lesson source 2026-05-29 (-12%% misreport) and 2026-06-10 ($22-vs-$75.68 idle
blindness): hand-assembled aggregates from stale memory get the operator-facing
number wrong. This script IS the number; the cron tick + weekly P&L use it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import httpx
from web3 import Web3

import _paths as _secrets

DATA_API = "https://data-api.polymarket.com"
COINGECKO = "https://api.coingecko.com/api/v3/simple/price"

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}],
     "type": "function"},
]

# chain -> (chain_id, rpcs, native_symbol, {label: token_addr}) — $1-stables,
# pUSD, and Aave aTokens. Addresses mirror crypto_status/wallet_status/aave_deposit.
CHAINS = {
    "polygon": (137, [
        "https://polygon.drpc.org",
        "https://polygon-bor-rpc.publicnode.com",
        "https://rpc.ankr.com/polygon",
    ], "POL", {
        "USDC.e":  "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "USDC":    "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
        "USDT":    "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "pUSD":    "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB",
        "aUSDC.e": "0x625E7708f30cA75bfd92586e17077590C60eb4cD",
        "aUSDC":   "0xA4D94019934D8333Ef880ABFFbF2FDd611C762BD",
    }),
    "arbitrum": (42161, [
        "https://arb1.arbitrum.io/rpc",
        "https://arbitrum.drpc.org",
        "https://arbitrum-one-rpc.publicnode.com",
    ], "ETH", {
        "USDC":   "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDC.e": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        "USDT":   "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "aUSDC":  "0x724dc807b04555b71ed48a6896b6F41593b8C637",
    }),
    "base": (8453, [
        "https://mainnet.base.org",
        "https://base.drpc.org",
        "https://base-rpc.publicnode.com",
    ], "ETH", {
        "USDC":  "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
        "aUSDC": "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB",
    }),
    "optimism": (10, [
        "https://mainnet.optimism.io",
        "https://optimism.drpc.org",
        "https://optimism-rpc.publicnode.com",
    ], "ETH", {
        "USDC":   "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
        "USDC.e": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
    }),
}


def wallet_addresses() -> dict[str, str]:
    out = {}
    for sleeve, env in [("pm", "POLYCLAUDE_WALLET"), ("crypto", "POLYCLAUDE_WALLET_CRYPTO")]:
        out[sleeve] = Web3.to_checksum_address(
            json.loads(_secrets.path(env).read_text())["address"])
    return out


def pick_rpc(rpcs: list[str], chain_id: int) -> Web3 | None:
    for rpc in rpcs:
        try:
            w = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
            if w.eth.chain_id == chain_id:
                return w
        except Exception:
            continue
    return None


def native_prices(warnings: list[str]) -> dict[str, float]:
    try:
        r = httpx.get(COINGECKO, params={
            "ids": "ethereum,polygon-ecosystem-token", "vs_currencies": "usd"
        }, timeout=10)
        r.raise_for_status()
        j = r.json()
        return {"ETH": j["ethereum"]["usd"], "POL": j["polygon-ecosystem-token"]["usd"]}
    except Exception as e:
        warnings.append(f"CoinGecko unavailable ({e}); native tokens valued at $0")
        return {"ETH": 0.0, "POL": 0.0}


def pm_positions_mtm(addr: str, warnings: list[str]) -> float:
    try:
        r = httpx.get(f"{DATA_API}/positions",
                      params={"user": addr.lower(), "limit": "100"}, timeout=15)
        r.raise_for_status()
        return sum(p["currentValue"] for p in r.json())
    except Exception as e:
        warnings.append(f"data-api positions failed ({e}); PM MTM counted as $0")
        return 0.0


def ostium_open_trades(warnings: list[str]) -> None:
    try:
        out = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "ostium_client.py"), "status"],
            capture_output=True, text=True, timeout=60).stdout
        n = int(next(l for l in out.splitlines() if "open trades:" in l).split(":")[1])
        if n > 0:
            warnings.append(f"{n} open Ostium trade(s) NOT valued here — add collateral+PnL manually")
    except Exception as e:
        warnings.append(f"Ostium status unavailable ({e}); any open-trade collateral not counted")


def main() -> int:
    ap = argparse.ArgumentParser(description="authoritative total-bankroll aggregate")
    ap.add_argument("--ref", type=float, default=170.0,
                    help="reference bankroll for delta (default 170 = kickoff)")
    args = ap.parse_args()

    warnings: list[str] = []
    addrs = wallet_addresses()
    prices = native_prices(warnings)

    total = 0.0
    pm_mtm = pm_positions_mtm(addrs["pm"], warnings)
    total += pm_mtm
    print(f"{'PM positions MTM':38s} ${pm_mtm:>9.2f}")

    for chain, (chain_id, rpcs, native_sym, tokens) in CHAINS.items():
        w = pick_rpc(rpcs, chain_id)
        if w is None:
            warnings.append(f"{chain}: no working RPC — balances on it NOT counted")
            continue
        for sleeve, addr in addrs.items():
            native = w.eth.get_balance(addr) / 1e18
            native_usd = native * prices[native_sym]
            if native_usd > 0.005:
                total += native_usd
                print(f"{chain} {sleeve} {native_sym} ({native:.4f}):{'':6s} ${native_usd:>9.2f}")
            for label, taddr in tokens.items():
                c = w.eth.contract(address=Web3.to_checksum_address(taddr), abi=ERC20_ABI)
                try:
                    bal = c.functions.balanceOf(addr).call() / 1e6
                except Exception:
                    warnings.append(f"{chain} {sleeve} {label}: balanceOf failed — not counted")
                    continue
                if bal > 0.005:
                    total += bal
                    print(f"{chain} {sleeve} {label}:{'':{max(1, 24 - len(chain) - len(sleeve) - len(label))}s} ${bal:>9.2f}")

    ostium_open_trades(warnings)

    print("-" * 50)
    delta = total - args.ref
    print(f"{'TOTAL BANKROLL':38s} ${total:>9.2f}")
    print(f"{'vs reference $' + f'{args.ref:.0f}':38s} {delta:>+9.2f}  ({delta / args.ref * 100:+.1f}%)")
    for msg in warnings:
        print(f"WARNING: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
