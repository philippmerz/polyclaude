"""Read-only wallet status: MATIC + USDC.e + USDC native balances on Polygon.

Reads the wallet file pointed to by POLYCLAUDE_WALLET (resolved via _secrets).
Only reads the address — does NOT require or surface the private key.
Safe to run any time.
"""

import json
import sys
from pathlib import Path
from web3 import Web3
import _paths as _secrets

WALLET_PATH = _secrets.path("POLYCLAUDE_WALLET")
# Default RPC https://polygon-rpc.com began returning "tenant disabled" 2026-04-25.
# Fall through a list of public endpoints; first that answers wins.
POLYGON_RPCS = [
    "https://polygon.drpc.org",
    "https://polygon-bor-rpc.publicnode.com",
    "https://rpc.ankr.com/polygon",
    "https://polygon.api.onfinality.io/public",
]

# USDC.e (bridged, the legacy USDC Polymarket uses): 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
# USDC native (Circle): 0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359
# pUSD (Polymarket CLOB collateral) + Aave aTokens included so idle capital is
# never invisible to cron ticks (2026-06-10: $53.55 Aave + $1.8 pUSD sat
# unreported for days because this script only showed raw USDC).
TOKENS = {
    "USDC.e":     "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDC":       "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    "pUSD":       "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB",
    "aave USDC.e": "0x625E7708f30cA75bfd92586e17077590C60eb4cD",
    "aave USDC":  "0xA4D94019934D8333Ef880ABFFbF2FDd611C762BD",
}
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}],
     "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals",
     "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol",
     "outputs": [{"name": "", "type": "string"}], "type": "function"},
]


def main() -> int:
    wallet = json.loads(WALLET_PATH.read_text())
    address = Web3.to_checksum_address(wallet["address"])
    print(f"address: {address}")

    w3 = None
    for rpc in POLYGON_RPCS:
        candidate = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
        try:
            if candidate.eth.chain_id == 137:
                w3 = candidate
                print(f"rpc: {rpc}")
                break
        except Exception:
            continue
    if w3 is None:
        print("ERROR: no working polygon RPC", file=sys.stderr)
        return 1

    matic_wei = w3.eth.get_balance(address)
    matic = matic_wei / 1e18
    print(f"MATIC: {matic:.6f}")

    pusd_bal = None
    for label, token_addr in TOKENS.items():
        c = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
        try:
            decimals = c.functions.decimals().call()
            bal = c.functions.balanceOf(address).call()
            print(f"{label}: {bal / 10**decimals:.6f}")
            if label == "pUSD":
                pusd_bal = bal / 10**decimals
        except Exception as e:
            print(f"{label}: ERROR {e}")

    # DEPLOYABLE vs HELD (2026-08-13). A resting BUY's collateral is committed at
    # the exchange but is NOT deducted from the on-chain pUSD balance — verified
    # with a live $5.06 bid against an unchanged 9.381882 reading. The bankroll
    # TOTAL is unaffected (that cash is still mine until it becomes shares, so
    # nothing is double-counted), but "what can I deploy right now" is not the
    # balance, and reading it as such invites committing capital twice. I had
    # been netting this by hand every time; a number I recompute manually on
    # every sizing decision is a number the tool should print.
    try:
        import json as _json
        import subprocess as _sp
        out = _sp.run([sys.executable, str(Path(__file__).parent / "clob_v2.py"), "orders"],
                      capture_output=True, text=True, timeout=60).stdout
        # Shape is {"status_code":..., "body":{"data":[...]}} — I wrote this parse
        # from memory as data["data"]["data"] and it silently yielded [] against a
        # live $5.06 bid, printing a confident wrong "deployable". That is the same
        # empty-list-looks-like-success bug I banked a lesson about ONE DAY earlier
        # in run_pair_arb. Caught only because I checked the output against a known
        # truth. Lesson reinforced: read the shape, never recall it.
        data = _json.loads(out[out.index("{"):])
        rows = (data.get("body", {}) or {}).get("data", []) or []
        committed = sum((float(o["price"]) * (float(o["original_size"]) - float(o.get("size_matched", 0) or 0)))
                        for o in rows if o.get("side") == "BUY")
        if pusd_bal is not None:
            print(f"pUSD committed to resting BUYs: {committed:.6f}")
            print(f"pUSD DEPLOYABLE (net of bids):  {pusd_bal - committed:.6f}")
    except Exception as e:
        print(f"deployable calc unavailable ({str(e)[:60]}) — net resting BUYs by hand")

    return 0


if __name__ == "__main__":
    sys.exit(main())
