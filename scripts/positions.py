"""Print current open Polymarket positions for the wallet, mark-to-market.

Pulls from data-api.polymarket.com (public, no auth). Read-only.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import httpx

from polyclaude_client import Wallet  # noqa: E402

DATA_API = "https://data-api.polymarket.com"


def main() -> None:
    addr = Wallet.load().address
    with httpx.Client(timeout=15.0) as c:
        r = c.get(f"{DATA_API}/positions", params={"user": addr.lower(), "limit": "100"})
        r.raise_for_status()
        positions = r.json()
    if not positions:
        print("(no open positions)")
        return

    total_init = 0.0
    total_cur = 0.0
    total_max = 0.0
    print(f"{'side':4} {'entry':>6} {'mark':>6} {'shares':>8} {'cost':>7} {'mtm':>7} {'maxpay':>7} {'pnl%':>6}  market")
    for p in sorted(positions, key=lambda x: -x["initialValue"]):
        side = p["outcome"]
        entry = p["avgPrice"]
        mark = p["curPrice"]
        shares = p["size"]
        cost = p["initialValue"]
        cur = p["currentValue"]
        maxpay = shares  # if NO wins, get $1 per share
        pnl_pct = p["percentPnl"]
        total_init += cost
        total_cur += cur
        total_max += maxpay
        print(f"{side:4} {entry:>6.3f} {mark:>6.3f} {shares:>8.2f} {cost:>7.2f} {cur:>7.2f} {maxpay:>7.2f} {pnl_pct:>6.2f}  {p['title'][:60]}")
    print()
    print(f"TOTAL  cost ${total_init:.2f}  mtm ${total_cur:.2f}  max-payout ${total_max:.2f}  unrealised P&L ${total_cur-total_init:+.2f}  ({(total_cur/total_init-1)*100:+.2f}%)")
    print(f"Max upside if all NO win: ${total_max:.2f}  ({(total_max/total_init-1)*100:+.2f}%)")


if __name__ == "__main__":
    main()
