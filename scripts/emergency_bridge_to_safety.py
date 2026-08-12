"""Emergency bridge: move USDC off an at-risk chain back to Polygon via Across.

Dumb executor. Used when news_watcher / cron concludes the source chain
(Arbitrum, Base, Optimism, etc.) is degraded — sequencer halt, bridge
exploit, or related. Pulls full USDC balance from the at-risk chain and
sends it home to Polygon (or to a different safe chain via --to-chain).

Behavior:
  - Reads the wallet's full USDC balance on the source chain.
  - Subtracts a small dust margin so the bridge call's $0.01-0.05 fee
    doesn't push us over the available balance.
  - Invokes scripts/across_bridge.py with that amount.
  - Telegram-alerts the operator with reason + tx.

CAVEAT: if the at-risk event IS Across itself (across-protocol exploit),
do not use this script — Across is the bridge it uses. The cron tick's
sanity check should detect this and use a different mechanism (currently
none implemented; operator manual intervention required).

Usage:
    python scripts/emergency_bridge_to_safety.py --reason "arbitrum sequencer halt" --from-chain arbitrum
    python scripts/emergency_bridge_to_safety.py --reason "base degraded" --from-chain base --to-chain polygon
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from web3 import Web3

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


# Mirror of across_bridge.CHAIN — duplicated here to avoid the cross-import
# loading the bridge module's top-level work just to look up addresses.
CHAIN = {
    "arbitrum": (42161, ["https://arb1.arbitrum.io/rpc", "https://arbitrum.drpc.org"],
                 "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"),
    "base":     (8453,  ["https://mainnet.base.org", "https://base.drpc.org"],
                 "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
    "polygon":  (137,   ["https://polygon.drpc.org", "https://polygon-bor-rpc.publicnode.com"],
                 "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"),
    "optimism": (10,    ["https://mainnet.optimism.io", "https://optimism.drpc.org"],
                 "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85"),
}

ERC20_ABI = [{
    "constant": True,
    "inputs": [{"name": "_owner", "type": "address"}],
    "name": "balanceOf",
    "outputs": [{"name": "balance", "type": "uint256"}],
    "type": "function",
}]

# Margin to subtract from full balance, in USDC (covers across fees + dust)
SAFETY_MARGIN_USDC = 0.10


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
            check=False,
            timeout=15,
            capture_output=True,
        )
    except Exception:
        pass


def _usdc_balance(chain: str, addr: str) -> float:
    chain_id, rpcs, usdc_addr = CHAIN[chain]
    for rpc in rpcs:
        try:
            w = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 8}))
            if w.eth.chain_id != chain_id:
                continue
            usdc = w.eth.contract(
                address=Web3.to_checksum_address(usdc_addr), abi=ERC20_ABI)
            return usdc.functions.balanceOf(Web3.to_checksum_address(addr)).call() / 1e6
        except Exception:
            continue
    raise RuntimeError(f"no working rpc for {chain}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--reason", required=True)
    p.add_argument("--from-chain", required=True, choices=list(CHAIN.keys()))
    p.add_argument("--to-chain", default="polygon", choices=list(CHAIN.keys()))
    p.add_argument("--sleeve", choices=["polymarket", "crypto"], default="crypto")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    # Gate operator alerts on dry-run (2026-08-12). Setting the module flag
    # here covers EVERY _telegram call site in the file at once — the gate
    # without this wiring is inert, which is exactly the half-fix that let the
    # same bug survive one round of repair earlier today.
    global _DRY_RUN
    _DRY_RUN = bool(getattr(args, "dry_run", False))

    if args.from_chain == args.to_chain:
        print("from-chain and to-chain are the same; nothing to do")
        return 0

    env = "POLYCLAUDE_WALLET" if args.sleeve == "polymarket" else "POLYCLAUDE_WALLET_CRYPTO"
    addr = json.loads(_secrets.path(env).read_text())["address"]

    bal = _usdc_balance(args.from_chain, addr)
    print(f"emergency_bridge_to_safety  reason={args.reason!r}  dry_run={args.dry_run}")
    print(f"sleeve: {args.sleeve}  addr: {addr}")
    print(f"USDC on {args.from_chain}: {bal:.4f}")

    if bal <= SAFETY_MARGIN_USDC:
        msg = (f"emergency_bridge_to_safety: only {bal:.4f} USDC on "
               f"{args.from_chain}; nothing meaningful to bridge")
        print(msg)
        _telegram(msg)
        return 0

    bridge_amount = max(0.0, bal - SAFETY_MARGIN_USDC)
    print(f"bridging {bridge_amount:.4f} USDC {args.from_chain} -> {args.to_chain}")

    if args.dry_run:
        msg = (f"DRY emergency_bridge_to_safety: would bridge {bridge_amount:.4f} USDC "
               f"{args.from_chain}->{args.to_chain} (reason: {args.reason})")
        print(msg)
        _telegram(msg)
        return 0

    cmd = [
        ".venv/bin/python", "scripts/across_bridge.py",
        "--sleeve", args.sleeve,
        "--from-chain", args.from_chain,
        "--to-chain", args.to_chain,
        "--amount-usdc", f"{bridge_amount:.4f}",
        "--yes",
    ]
    print(f"invoking: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    print(res.stdout)
    if res.stderr:
        print(f"STDERR: {res.stderr}")

    if res.returncode == 0:
        msg = (f"emergency_bridge_to_safety OK (reason: {args.reason}). "
               f"bridged {bridge_amount:.4f} USDC {args.from_chain}->{args.to_chain}")
        _telegram(msg)
        return 0
    else:
        msg = (f"emergency_bridge_to_safety FAILED (reason: {args.reason}, "
               f"chain {args.from_chain}->{args.to_chain}, code {res.returncode}). "
               f"Manual intervention needed.")
        _telegram(msg)
        return 2


if __name__ == "__main__":
    sys.exit(main())
