"""Emergency exit: sell all open Polymarket positions for the polymarket-sleeve wallet.

Dumb executor. The intelligence (sanity check, deciding *whether* to call this)
lives in the cron tick that invokes it.

Behavior:
  - Cancel any resting open orders first (so they don't conflict with sells).
  - Read all open positions via data-api.polymarket.com.
  - For each position, fetch the orderbook, place a SELL at best_bid for the
    full size. Aggressive — gets filled instantly if there's any depth.
  - Slippage cap: if best_bid implies >10% loss vs. curPrice, ABORT that
    leg and Telegram. Continue with other positions.
  - Skip positions where `redeemable=true` (market already resolved; we should
    redeem, not sell). Flag for separate redemption flow.
  - Log every order id + Telegram a summary at the end.

Usage:
    python scripts/emergency_exit_polymarket.py --reason "polymarket halted"
    python scripts/emergency_exit_polymarket.py --reason "test" --dry-run

Returns 0 on full success, 1 on partial, 2 on any abort condition.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

import httpx

import _paths as _secrets
from polyclaude_client import Polyclaude

_secrets.install_scrubbing_excepthook()

DATA_API = "https://data-api.polymarket.com"
SLIPPAGE_CAP_PCT = 10.0


def _telegram(text: str) -> None:
    try:
        subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            check=False,
            timeout=15,
            capture_output=True,
        )
    except Exception:
        pass


def _positions(addr: str) -> list[dict]:
    with httpx.Client(timeout=20.0) as c:
        r = c.get(f"{DATA_API}/positions",
                  params={"user": addr.lower(), "limit": "200"})
        r.raise_for_status()
        return r.json() or []


def _best_bid(orderbook: dict) -> float | None:
    """Return the highest bid price (buyer-side) from the orderbook, or None.

    Polyclaude.orderbook returns bids as a list of (price, size) tuples,
    sorted ascending by price.
    """
    bids = orderbook.get("bids") or []
    if not bids:
        return None
    valid = [(float(p), float(s)) for p, s in bids if float(s) > 0]
    if not valid:
        return None
    return max(p for p, _ in valid)


def _close_one(pc: Polyclaude, position: dict, dry_run: bool) -> dict:
    asset = position["asset"]
    title = position["title"][:50]
    side = position["outcome"]
    size = float(position["size"])
    cur_price = float(position["curPrice"])
    label = f"{side} {title}"

    if position.get("redeemable"):
        return {"label": label, "status": "REDEEMABLE_SKIPPED",
                "tx": None, "error": "market resolved; needs redeem flow"}

    try:
        ob = pc.orderbook(asset)
    except Exception as e:
        return {"label": label, "status": "ERR", "tx": None,
                "error": f"orderbook fetch: {str(e)[:200]}"}

    bid = _best_bid(ob)
    if bid is None or bid <= 0:
        return {"label": label, "status": "NO_BID", "tx": None,
                "error": "no buyer in orderbook"}

    slippage = (cur_price - bid) / cur_price * 100 if cur_price > 0 else 100
    if slippage > SLIPPAGE_CAP_PCT:
        return {"label": label, "status": "SLIPPAGE_ABORT",
                "tx": None,
                "error": f"best_bid {bid:.4f} vs curPrice {cur_price:.4f} = {slippage:.1f}% > {SLIPPAGE_CAP_PCT}%"}

    print(f"  -> {label}: selling {size:.4f} @ {bid:.4f} "
          f"(curPrice {cur_price:.4f}, slippage {slippage:.1f}%)")

    if dry_run:
        return {"label": label, "status": "DRY", "tx": None, "error": None}

    # v2 WRITE PATH (2026-08-12). This previously called
    # pc.place_limit_sell(), which routes through py_clob_client — the v1 SDK
    # that has been BROKEN against v2 since the 2026-05-05 migration
    # (order_version_mismatch). This file was written 2026-04-29 and the write
    # path has never once executed, so the breakage sat here for over three
    # months: the script would enumerate positions correctly, compute slippage
    # correctly, and then fail every actual sell — in the exact scenario
    # (exploit / depeg / chain halt) where it is the only thing standing
    # between me and the loss. Found by DRILLING a path my own lesson says is
    # indistinguishable from a working one until forced. clob_v2 is the
    # production-verified route (it placed every live order in the book).
    try:
        import clob_v2 as _v2
        _addr, _pk = _v2._load_wallet()
        _neg = _v2._check_neg_risk(asset)
        _signed = _v2.build_order(maker=_addr, token_id=asset, side="SELL",
                                  price=bid, size=size, signer_pk=_pk, neg_risk=_neg)
        # GTC-at-bid, NOT FOK (revised during the 2026-08-12 drill). The original
        # used FOK, and live-firing an unfillable test order showed why that is
        # wrong here: FOK is all-or-nothing at one price, so in the fast-moving
        # book of an actual exploit or depeg — the only situation this file ever
        # runs in — any thinning between the bid I read and the order I post
        # kills the whole sell and exits NOTHING. A GTC limit at the same bid
        # takes whatever depth is there and rests the remainder, and a partial
        # exit in an emergency strictly beats a clean refusal. Price is still
        # protected by SLIPPAGE_CAP_PCT above, and this script cancels resting
        # orders on entry, so a leftover from a prior run is cleared next run.
        result = _v2.post_order(_signed, order_type="GTC", post_only=False)
        if isinstance(result, dict) and result.get("status_code", 200) >= 400:
            return {"label": label, "status": "ERR", "tx": None,
                    "error": f"v2 post_order {result.get('status_code')}: {str(result.get('body'))[:200]}"}
        result = result.get("body", result) if isinstance(result, dict) else result
    except Exception as e:
        return {"label": label, "status": "ERR", "tx": None,
                "error": f"clob_v2 sell: {str(e)[:300]}"}

    order_id = None
    if isinstance(result, dict):
        order_id = result.get("orderID") or result.get("orderId") or result.get("id")
    return {"label": label, "status": "SUBMITTED", "tx": order_id, "error": None,
            "raw": result}


def run(reason: str, dry_run: bool) -> int:
    pc = Polyclaude.load(ensure_creds=True)
    addr = pc.wallet.address
    print(f"emergency_exit_polymarket  reason={reason!r}  dry_run={dry_run}")
    print(f"address: {addr}")

    # Cancel any resting orders first (clears the way for sell submissions).
    # ALSO REWIRED TO v2 (2026-08-12): this was the SECOND half of the same
    # break — the sell path was fixed first and `pc.cancel()` was left behind
    # on the dead v1 client. It is load-bearing, not incidental: resting sells
    # lock the very shares an emergency sell needs, so a silently-failing
    # cancel does not merely leave clutter, it can BLOCK the exit. Found by
    # grepping for the CLASS after fixing the instance.
    try:
        import clob_v2 as _v2c
        # Shape is {"status_code":..., "body":{"data":[...], "count":N}} — my
        # first attempt at this parse guessed and silently produced an empty
        # list against 4 live orders. The DRILL caught it, not review: a
        # cancel loop over [] prints nothing and looks exactly like success.
        listing = _v2c.list_open_orders()
        body = listing.get("body", {}) if isinstance(listing, dict) else {}
        open_orders = body.get("data", []) if isinstance(body, dict) else []
        if open_orders and not dry_run:
            print(f"cancelling {len(open_orders)} resting order(s) via v2...")
            for o in open_orders:
                oid = o.get("id") or o.get("orderID")
                try:
                    res = _v2c.cancel_order(oid)
                    if res.get("status_code", 200) >= 400:
                        print(f"  cancel {str(oid)[:12]} HTTP {res['status_code']}: {str(res.get('body'))[:120]}")
                except Exception as e:
                    print(f"  cancel failed: {str(e)[:200]}")
        elif open_orders:
            print(f"DRY: would cancel {len(open_orders)} resting order(s) via v2")
    except Exception as e:
        print(f"open_orders fetch failed (non-fatal): {str(e)[:200]}")

    positions = _positions(addr)
    if not positions:
        msg = f"emergency_exit_polymarket: no open positions (reason: {reason})"
        print(msg)
        _telegram(msg)
        return 0

    print(f"found {len(positions)} position(s) to close")

    results = []
    for p in positions:
        r = _close_one(pc, p, dry_run)
        results.append(r)
        print(f"     {r['status']}  tx/order={r['tx']}  err={r['error']}")
        time.sleep(0.5)  # be gentle on the gamma-api

    ok = [r for r in results if r["status"] in ("SUBMITTED", "DRY")]
    skip = [r for r in results if r["status"] in ("REDEEMABLE_SKIPPED", "NO_BID", "SLIPPAGE_ABORT")]
    err = [r for r in results if r["status"] == "ERR"]

    summary_lines = [
        f"emergency_exit_polymarket done (reason: {reason}).",
        f"submitted: {len(ok)}/{len(positions)}",
        f"skipped:   {len(skip)} ({', '.join(r['status'] for r in skip)})" if skip else "",
        f"errored:   {len(err)}" if err else "",
    ]
    summary_lines.extend(f"  {r['label']}: {r['status']}" for r in skip + err)
    summary = "\n".join(s for s in summary_lines if s)
    print(summary)
    _telegram(summary)

    if err:
        return 2
    if skip:
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--reason", required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    return run(args.reason, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
