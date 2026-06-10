"""Read-only multi-chain status for the crypto-sleeve wallet.

Reads the address from POLYCLAUDE_WALLET_CRYPTO (resolved via _paths) and
reports native + USDC balances across Arbitrum, Base, Polygon, and Optimism.
Only reads the address — never the private key. Safe to run any time.
"""

import json
import sys

from web3 import Web3

import _paths as _secrets

# (chain_id, label, list-of-rpc-fallbacks, native-token-symbol, [(token-symbol, token-addr), ...])
CHAINS = [
    (
        42161,
        "Arbitrum",
        [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum.drpc.org",
            "https://arbitrum-one-rpc.publicnode.com",
        ],
        "ETH",
        [
            ("USDC",   "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"),  # Circle native
            ("USDC.e", "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"),  # legacy bridged
            ("USDT",   "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"),
            ("aUSDC",  "0x724dc807b04555b71ed48a6896b6F41593b8C637"),  # Aave V3 — idle sleeve must stay visible
            ("ARB",    "0x912CE59144191C1204E64559FE8253a0e49E6548"),  # spot position (operator-directed entry)
        ],
    ),
    (
        8453,
        "Base",
        [
            "https://mainnet.base.org",
            "https://base.drpc.org",
            "https://base-rpc.publicnode.com",
        ],
        "ETH",
        [
            ("USDC",  "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),  # Circle native
            ("USDbC", "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA"),  # legacy bridged
            ("aUSDC", "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB"),  # Aave V3 — idle sleeve must stay visible
        ],
    ),
    (
        137,
        "Polygon",
        [
            "https://polygon.drpc.org",
            "https://polygon-bor-rpc.publicnode.com",
            "https://rpc.ankr.com/polygon",
        ],
        "MATIC",
        [
            ("USDC.e",  "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"),  # Polymarket settles in this
            ("USDC",    "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"),  # Circle native
            ("USDT",    "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"),
            ("pUSD",    "0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB"),  # CLOB collateral
            ("aUSDC.e", "0x625E7708f30cA75bfd92586e17077590C60eb4cD"),  # Aave V3 — idle sleeve must stay visible
        ],
    ),
    (
        10,
        "Optimism",
        [
            "https://mainnet.optimism.io",
            "https://optimism.drpc.org",
            "https://optimism-rpc.publicnode.com",
        ],
        "ETH",
        [
            ("USDC",   "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85"),  # Circle native
            ("USDC.e", "0x7F5c764cBc14f9669B88837ca1490cCa17c31607"),  # legacy bridged
        ],
    ),
]

# ERC20 balances are read with these decimals (default 6 = USDC-style).
TOKEN_DECIMALS = {"ARB": 18}

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]


def pick_rpc(rpcs: list[str], expected_chain_id: int) -> Web3 | None:
    for rpc in rpcs:
        try:
            w = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
            if w.eth.chain_id == expected_chain_id:
                return w
        except Exception:
            continue
    return None


def read_chain(w: Web3, addr: str, native_symbol: str, tokens: list[tuple[str, str]]) -> dict:
    out = {}
    out[native_symbol] = w.eth.get_balance(addr) / 1e18
    for sym, contract_addr in tokens:
        try:
            c = w.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=ERC20_ABI)
            out[sym] = c.functions.balanceOf(addr).call() / 10 ** TOKEN_DECIMALS.get(sym, 6)
        except Exception:
            out[sym] = float("nan")
    return out


def main() -> int:
    sleeve = sys.argv[1] if len(sys.argv) > 1 else "crypto"
    env_var = {
        "crypto": "POLYCLAUDE_WALLET_CRYPTO",
        "polymarket": "POLYCLAUDE_WALLET",
        "pm": "POLYCLAUDE_WALLET",
    }.get(sleeve.lower())
    if not env_var:
        print(f"unknown sleeve {sleeve!r}; pick 'crypto' or 'polymarket'", file=sys.stderr)
        return 2

    addr = json.loads(_secrets.path(env_var).read_text())["address"]
    print(f"sleeve: {sleeve}")
    print(f"address: {addr}\n")

    for chain_id, label, rpcs, native, tokens in CHAINS:
        w = pick_rpc(rpcs, chain_id)
        if w is None:
            print(f"[{label}] no working RPC")
            continue
        bals = read_chain(w, addr, native, tokens)
        any_balance = any(v > 0.0 for v in bals.values())
        if any_balance:
            print(f"[{label}] block {w.eth.block_number}")
            for sym, val in bals.items():
                if val > 0:
                    fmt = f"{val:.6f}" if sym in ("ETH", "MATIC") else f"{val:.4f}"
                    print(f"  {sym:8s} {fmt}")
        else:
            print(f"[{label}] empty (block {w.eth.block_number})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
