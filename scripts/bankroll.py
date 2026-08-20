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

import book_walk

# Filled by the PM valuation pass; consumed by the REALIZED split in main().
PM_STATE: dict[str, float] = {}

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
# NONSTABLE tokens are valued at live CoinGecko prices (decimals != 6 supported).
NONSTABLE = {"ARB": ("arbitrum", 18)}  # symbol -> (coingecko_id, decimals)
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
        "ARB":    "0x912CE59144191C1204E64559FE8253a0e49E6548",
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
        ids = "ethereum,polygon-ecosystem-token," + ",".join(cg for cg, _ in NONSTABLE.values())
        r = httpx.get(COINGECKO, params={"ids": ids, "vs_currencies": "usd"}, timeout=10)
        r.raise_for_status()
        j = r.json()
        out = {"ETH": j["ethereum"]["usd"], "POL": j["polygon-ecosystem-token"]["usd"]}
        for sym, (cg, _dec) in NONSTABLE.items():
            out[sym] = j.get(cg, {}).get("usd", 0.0)
        return out
    except Exception as e:
        warnings.append(f"CoinGecko unavailable ({e}); native/non-stable tokens valued at $0")
        return {"ETH": 0.0, "POL": 0.0, **{sym: 0.0 for sym in NONSTABLE}}


def pm_positions_mtm(addr: str, warnings: list[str]) -> float:
    """PM sleeve marked at data-api `currentValue`, i.e. MIDPOINTS.

    BASIS DELIBERATELY CHOSEN, 2026-08-13 — do not "improve" this without
    reading the reasoning. Three bases were computed that day on the same book:
    mid $174.68 (+18.2%), best-bid $168.69 (+14.1%), and MY-PRIORS $193.11
    (+30.6%). Mid is kept because it is the conventional market-based measure
    and this is a hold-to-resolution book, where bid systematically understates
    (I am not liquidating) — the bid figure is liquidation value, useful as a
    floor, not as the headline.

    The prior-based figure is BANNED as a headline and the reason matters: it
    is the highest of the three precisely BECAUSE it restates my own belief
    that several positions are underpriced. Reporting +30.6% would be marking
    my own book to my own opinion, which converts a bet into a claimed gain.
    It belongs only where it already lives — exit_analysis's hold-vs-sell math,
    where "what I think this is worth" is exactly the right question.

    Mid's known weakness is illiquid books: the same day, one leg printed a
    0.685 midpoint inside a 0.57/0.76 spread on ZERO 24h volume, inflating the
    headline by $8.64. That is handled where it belongs — positions.py prints
    a REALIZABLE line naming any book whose mark exceeds its bid materially —
    rather than by silently switching this number's basis.
    """
    try:
        r = httpx.get(f"{DATA_API}/positions",
                      params={"user": addr.lower(), "limit": "100"}, timeout=15)
        r.raise_for_status()
        rows = r.json()
        mid = sum(p["currentValue"] for p in rows)
        # Cost basis and both unrealized figures, stashed for the REALIZED split
        # below. Operator directive 2026-08-18: "it's only truly return when the
        # cash settles on the wallet" — so marked gains are explicitly NOT return,
        # and the number they will judge on is cumulative REALIZED P&L.
        PM_STATE["cost"] = sum(float(p.get("initialValue") or 0) for p in rows)
        PM_STATE["mid"] = mid
        # Flag (do NOT silently re-base) when midpoints materially overstate the
        # sleeve. This is the number I quote, so the caveat has to live here and
        # not only in positions.py — otherwise the same error just moves one
        # level up. Walks real bids; costs ~30s on a script that already takes
        # minutes.
        try:
            realizable = 0.0
            with httpx.Client(timeout=20.0) as c:
                for p in rows:
                    if float(p.get("size", 0)) <= 0.5:
                        continue
                    m = c.get("https://gamma-api.polymarket.com/markets",
                              params={"slug": p["slug"]}).json()[0]
                    toks = json.loads(m["clobTokenIds"]); outs = json.loads(m["outcomes"])
                    bk = c.get("https://clob.polymarket.com/book",
                               params={"token_id": toks[outs.index(p["outcome"])]}).json()
                    # Depth-walk NET OF FEES via the shared primitive (2026-08-14).
                    # This walked the book but never subtracted the taker fee, so
                    # the "realizable" cross-check was itself overstated — $4.57
                    # across the book, 3.9pp of reported return. Third layer of the
                    # same error: midpoint -> best-bid -> fee-free walk, each fix
                    # leaving the next intact, every one flattering the number.
                    realizable += book_walk.realizable(
                        bk.get("bids", []), float(p["size"]), m)["net"]
            PM_STATE["realizable"] = realizable
            gap = mid - realizable
            if gap > 1.0:
                warnings.append(
                    f"PM sleeve marked at MIDPOINTS overstates NET realizable by ${gap:.2f} "
                    f"(mid ${mid:.2f} vs ${realizable:.2f}) — illiquid book(s); see positions.py "
                    f"for which. Quote the realizable figure alongside any headline return.")
        except Exception as e:
            warnings.append(f"realizable cross-check unavailable ({str(e)[:40]})")
        return mid
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
                # Accumulate separately: native gas is deposited capital, not P&L.
                PM_STATE["gas_usd"] = PM_STATE.get("gas_usd", 0.0) + native_usd
                print(f"{chain} {sleeve} {native_sym} ({native:.4f}):{'':6s} ${native_usd:>9.2f}")
            for label, taddr in tokens.items():
                c = w.eth.contract(address=Web3.to_checksum_address(taddr), abi=ERC20_ABI)
                dec = NONSTABLE[label][1] if label in NONSTABLE else 6
                bal = None
                for _attempt in range(3):  # flaky public RPCs: per-call retry (Base aUSDC failed 2x 2026-06-11)
                    try:
                        bal = c.functions.balanceOf(addr).call() / 10 ** dec
                        break
                    except Exception:
                        import time as _t
                        _t.sleep(1.5)
                if bal is None:
                    warnings.append(f"{chain} {sleeve} {label}: balanceOf failed 3x — not counted")
                    continue
                usd = bal * prices[label] if label in NONSTABLE else bal
                if label in NONSTABLE and bal > 0 and prices.get(label, 0) == 0:
                    warnings.append(f"{chain} {sleeve} {label}: {bal:.4f} held but unpriced — NOT counted")
                if usd > 0.005:
                    total += usd
                    qty = f" ({bal:.2f})" if label in NONSTABLE else ""
                    print(f"{chain} {sleeve} {label}{qty}:{'':{max(1, 24 - len(chain) - len(sleeve) - len(label) - len(qty))}s} ${usd:>9.2f}")

    ostium_open_trades(warnings)

    # Cache the total so sizing tools (polyclaude_enter, portfolio_kelly) can
    # default to the live figure instead of a static constant (doctrine: this
    # script IS the authoritative bankroll number).
    try:
        cache = Path(__file__).resolve().parent.parent / "notes" / ".bankroll_cache.json"
        import datetime as _dt
        cache.write_text(json.dumps({
            "total": round(total, 2),
            "at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        }))
    except Exception as e:
        warnings.append(f"bankroll cache write failed ({e})")

    print("-" * 50)
    delta = total - args.ref
    print(f"{'TOTAL BANKROLL':38s} ${total:>9.2f}")
    print(f"{'vs reference $' + f'{args.ref:.0f}':38s} {delta:>+9.2f}  ({delta / args.ref * 100:+.1f}%)")

    # REALIZED vs UNREALIZED split (2026-08-18, operator directive: "it's only
    # truly return when the cash settles on the wallet"). Identity: every dollar
    # of total gain that is NOT open-position appreciation must already have
    # settled — through a close, a resolution, or a fee/gas cost. So
    #   realized = (bankroll - deposits) - unrealized
    # Both unrealized bases are shown because the honest realized figure depends
    # on which you believe: marked unrealized is the conventional one, realizable
    # unrealized is what the book would actually fetch. The RANGE is the point —
    # quoting a single realized number would hide the same midpoint problem this
    # script already warns about one line above.
    # GAS IS DEPOSITED CAPITAL, NOT TRADING GAIN (2026-08-20). The $170 reference
    # is TRADING capital only — capital_ledger.md records gas (~53.8 POL + ~0.001
    # ETH) as a SEPARATE operator deposit. But this script counts those tokens'
    # live USD value in `total`, so comparing total against 170 books the
    # operator's gas deposit as return, and the realized line inherited it: +$10.77
    # reported vs +$5.33 honest, a 2x overstatement of the exact number the
    # operator said they would judge on. Native gas tokens are therefore excluded
    # from the realized split. They stay in TOTAL BANKROLL (they are real assets)
    # but they are not trading P&L, and their price drift must never move a line
    # labelled "settled cash".
    gas_usd = PM_STATE.get("gas_usd", 0.0)
    cost = PM_STATE.get("cost")
    if cost is not None:
        unreal_mid = PM_STATE.get("mid", 0.0) - cost
        real_mid = (delta - gas_usd) - unreal_mid
        print(f"{'  REALIZED (settled cash)':38s} {real_mid:>+9.2f}  "
              f"({real_mid / args.ref * 100:+.1f}% of ref) <- the metric that counts")
        if gas_usd:
            print(f"{'  (gas tokens excluded)':38s} {gas_usd:>9.2f}  "
                  f"— separately deposited, not trading P&L")
        print(f"{'  unrealized (marked)':38s} {unreal_mid:>+9.2f}  "
              f"— NOT return until closed or resolved")
        rz = PM_STATE.get("realizable")
        if rz is not None:
            unreal_rz = rz - cost
            print(f"{'  unrealized (realizable)':38s} {unreal_rz:>+9.2f}  "
                  f"— what the open book would actually fetch today")
    for msg in warnings:
        print(f"WARNING: {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
