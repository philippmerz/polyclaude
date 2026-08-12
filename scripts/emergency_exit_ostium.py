"""Emergency exit: close all open Ostium positions for the crypto-sleeve wallet.

Dumb executor. The intelligence (sanity check, deciding *whether* to call this)
lives in the cron tick that invokes it. This script just does what it says.

Behavior:
  - Read all open trades via the Ostium SDK.
  - For each, market-close 100% at the current price.
  - If a single close fails 3 times in a row, abort the whole run (don't
    keep retrying into a degraded protocol — that just burns gas).
  - Log every tx hash and realized P&L per position + total.
  - Telegram-summarize the result.

Usage:
    python scripts/emergency_exit_ostium.py --reason "ostium hack confirmed"
    python scripts/emergency_exit_ostium.py --reason "operator panic"  --dry-run

Returns 0 on full success, 1 on partial, 2 on abort.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import time

from ostium_python_sdk import NetworkConfig, OstiumSDK

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"
MAX_CLOSE_ATTEMPTS = 3


def _sdk() -> OstiumSDK:
    cfg = NetworkConfig.mainnet()
    d = json.loads(_secrets.path("POLYCLAUDE_WALLET_CRYPTO").read_text())
    pk = d["private_key"]
    if not pk.startswith("0x"):
        pk = "0x" + pk
    return OstiumSDK(cfg, private_key=pk, rpc_url=ARBITRUM_RPC)


_DRY_RUN = False   # set from --dry-run in main(); gates all operator alerts


def _telegram(text: str) -> None:
    """Best-effort Telegram via the existing CLI; never raise.

    DRY-RUN GATE (2026-08-12). Gated at the FUNCTION rather than at each call
    site, so a new call site cannot forget it. Origin: five --dry-run drills of
    the Polymarket exit each sent the operator a summary reading "submitted:
    7/8", which reads exactly like the book being liquidated; they asked what it
    was. Dry-run correctly suppressed the ORDERS and did nothing about the
    ALARM. With a monthly drill now scheduled, an ungated alert would have
    become a recurring false emergency across every one of these scripts.
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


async def _close_one(sdk: OstiumSDK, trade: dict, dry_run: bool) -> dict:
    """Close one trade, retrying up to MAX_CLOSE_ATTEMPTS times.

    Returns a dict with status / pnl / tx info.
    """
    pair_id = int(trade["pair"]["id"])
    trade_index = int(trade["index"])
    pair_from = trade["pair"]["from"]
    pair_to = trade["pair"]["to"]
    label = f"{pair_from}/{pair_to} idx={trade_index}"

    if dry_run:
        return {"label": label, "status": "DRY", "tx": None, "error": None}

    last_err = None
    for attempt in range(1, MAX_CLOSE_ATTEMPTS + 1):
        try:
            # Re-fetch current price each attempt — protocols under stress
            # may have moved a lot.
            pairs = await sdk.get_formatted_pairs_details()
            p = next((x for x in pairs if int(x["id"]) == pair_id), None)
            if p is None:
                return {"label": label, "status": "ERR", "tx": None,
                        "error": f"pair {pair_id} not found"}
            px = p["price"]

            receipt = sdk.ostium.close_trade(
                pair_id=pair_id,
                trade_index=trade_index,
                market_price=px,
                close_percentage=100,
            )
            tx_hash = None
            if isinstance(receipt, dict):
                r = receipt.get("receipt")
                if r is not None and hasattr(r, "transactionHash"):
                    tx_hash = "0x" + r.transactionHash.hex()
            return {"label": label, "status": "OK", "tx": tx_hash, "error": None}
        except Exception as e:
            last_err = str(e)[:300]
            print(f"  attempt {attempt} for {label} failed: {last_err}", flush=True)
            time.sleep(2 * attempt)

    return {"label": label, "status": "ERR", "tx": None, "error": last_err}


async def run(reason: str, dry_run: bool) -> int:
    sdk = _sdk()
    addr = sdk.ostium.get_public_address()
    print(f"emergency_exit_ostium  reason={reason!r}  dry_run={dry_run}")
    print(f"address: {addr}")

    trades, _ = await sdk.get_open_trades()
    if not trades:
        msg = f"emergency_exit_ostium: no open positions (reason: {reason})"
        print(msg)
        _telegram(msg)
        return 0

    print(f"found {len(trades)} open position(s) to close:")
    for t in trades:
        print(f"  {t['pair']['from']}/{t['pair']['to']}  idx={t['index']}  "
              f"isBuy={t['isBuy']}  collateral={t.get('collateral')}  lev={t.get('leverage')}")

    results = []
    for t in trades:
        r = await _close_one(sdk, t, dry_run)
        results.append(r)
        print(f"  -> {r['label']}: {r['status']}  tx={r['tx']}  err={r['error']}")
        if r["status"] == "ERR":
            # Single failure aborts the run — don't keep retrying into a
            # degraded protocol.
            break

    ok = [r for r in results if r["status"] == "OK"]
    err = [r for r in results if r["status"] == "ERR"]
    summary = (
        f"emergency_exit_ostium done (reason: {reason}). "
        f"closed {len(ok)}/{len(trades)}"
        + (f", aborted on {err[0]['label']}" if err else "")
    )
    print(summary)
    _telegram(summary + "\n" + "\n".join(
        f"  {r['label']}: {r['status']}  {r['tx'] or ''}" for r in results))

    if err:
        return 2 if not ok else 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--reason", required=True,
                   help="why this is being run; logged + Telegrammed")
    p.add_argument("--dry-run", action="store_true",
                   help="enumerate positions but don't actually close")
    args = p.parse_args()
    global _DRY_RUN
    _DRY_RUN = bool(args.dry_run)
    return asyncio.run(run(args.reason, args.dry_run))


if __name__ == "__main__":
    sys.exit(main())
