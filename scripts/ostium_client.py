"""Thin wrapper around ostium-python-sdk for the polyclaude crypto sleeve.

Loads the crypto-sleeve wallet via _paths, instantiates an OstiumSDK pointed
at Arbitrum mainnet, and exposes async helpers for:
  - listing pairs and current prices (`pairs`, `pair`)
  - reading open positions (`positions`)
  - opening a position with sane defaults (`open_position`)
  - closing a position (`close_position`)

CLI usage:
    python scripts/ostium_client.py status
    python scripts/ostium_client.py pairs --group crypto
    python scripts/ostium_client.py open --pair ETH --side long --collateral 5 --leverage 5
    python scripts/ostium_client.py close --pair-id 1 --trade-index 0

Read-only commands never sign anything. Open/close commands require the
private key and execute on-chain. The script prints a human summary and
journals nothing — narration belongs in the calling cron tick / interactive
session.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from ostium_python_sdk import NetworkConfig, OstiumSDK

import _paths as _secrets

ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"


def _sdk() -> OstiumSDK:
    cfg = NetworkConfig.mainnet()
    d = json.loads(_secrets.path("POLYCLAUDE_WALLET_CRYPTO").read_text())
    pk = d["private_key"]
    if not pk.startswith("0x"):
        pk = "0x" + pk
    return OstiumSDK(cfg, private_key=pk, rpc_url=ARBITRUM_RPC)


async def _pairs(group: str | None = None) -> list[dict]:
    sdk = _sdk()
    pairs = await sdk.get_formatted_pairs_details()
    if group:
        pairs = [p for p in pairs if p.get("group") == group]
    return pairs


async def _pair_by_symbol(symbol: str) -> dict:
    sdk = _sdk()
    pairs = await sdk.get_formatted_pairs_details()
    s = symbol.upper()
    for p in pairs:
        if p["from"].upper() == s or f"{p['from']}/{p['to']}".upper() == s:
            return p
    raise SystemExit(f"pair {symbol!r} not found; try `pairs` to list")


async def _open_positions() -> list[dict]:
    sdk = _sdk()
    return await sdk.get_open_trades()


async def cmd_status(_args: argparse.Namespace) -> int:
    sdk = _sdk()
    addr = sdk.ostium.get_public_address()
    print(f"address: {addr}")
    # get_open_trades returns (trades, address) tuple
    trades, _ = await sdk.get_open_trades()
    print(f"open trades: {len(trades)}")
    for t in trades:
        print(f"  {json.dumps(t, default=str)[:300]}")
    return 0


async def cmd_pairs(args: argparse.Namespace) -> int:
    pairs = await _pairs(args.group)
    open_pairs = [p for p in pairs if p.get("isMarketOpen")]
    print(f"{len(open_pairs)} open pair(s){' in group ' + args.group if args.group else ''}:")
    for p in open_pairs:
        sym = f"{p['from']}/{p['to']}"
        mkr = float(p["makerFeeP"])
        tkr = float(p["takerFeeP"])
        max_lev = p["maxLeverage"]
        px = p["price"]
        print(f"  id={p['id']:3}  {sym:14s}  group={p['group']:11s}  maxLev={max_lev:>3}  fee m/t={mkr:.3f}/{tkr:.3f}%  px=${px:,.4f}")
    return 0


async def cmd_open(args: argparse.Namespace) -> int:
    sdk = _sdk()
    pair = await _pair_by_symbol(args.pair)
    if not pair.get("isMarketOpen"):
        print(f"market for {args.pair} is closed; aborting")
        return 2
    px = pair["price"]

    direction = args.side.lower() == "long"
    trade_params = {
        "collateral": args.collateral,
        "leverage": args.leverage,
        "asset_type": pair["id"],
        "direction": direction,
        "order_type": args.order_type.upper(),
        "is_day_trade": False,
    }
    # Optional TP / SL as % of price
    if args.tp_pct is not None:
        if direction:
            trade_params["tp"] = px * (1 + args.tp_pct / 100)
        else:
            trade_params["tp"] = px * (1 - args.tp_pct / 100)
    if args.sl_pct is not None:
        if direction:
            trade_params["sl"] = px * (1 - args.sl_pct / 100)
        else:
            trade_params["sl"] = px * (1 + args.sl_pct / 100)

    print(f"pair: {pair['from']}/{pair['to']} (id={pair['id']})  current px=${px:,.4f}")
    print(f"params: {json.dumps(trade_params, default=str)}")
    if not args.yes:
        ans = input("proceed? [y/N] ")
        if ans.strip().lower() != "y":
            print("aborted.")
            return 1

    receipt = sdk.ostium.perform_trade(trade_params, at_price=px)
    print(json.dumps(receipt, default=str, indent=2)[:1500])
    return 0


async def cmd_close(args: argparse.Namespace) -> int:
    sdk = _sdk()
    pair = await sdk.get_formatted_pairs_details()
    p = next((x for x in pair if x["id"] == args.pair_id), None)
    if p is None:
        print(f"pair id {args.pair_id} not found")
        return 2
    px = p["price"]
    print(f"closing pair_id={args.pair_id} ({p['from']}/{p['to']}) trade_index={args.trade_index} pct={args.percent}% at px=${px:,.4f}")
    if not args.yes:
        ans = input("proceed? [y/N] ")
        if ans.strip().lower() != "y":
            print("aborted.")
            return 1
    receipt = sdk.ostium.close_trade(
        pair_id=args.pair_id,
        trade_index=args.trade_index,
        market_price=px,
        close_percentage=args.percent,
    )
    print(json.dumps(receipt, default=str, indent=2)[:1500])
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="address + open trades")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("pairs", help="list open pairs")
    s.add_argument("--group", default=None,
                   choices=["crypto", "forex", "commodities", "indices", "stocks"])
    s.set_defaults(fn=cmd_pairs)

    s = sub.add_parser("open", help="open a new position")
    s.add_argument("--pair", required=True, help="symbol like ETH or BTC/USD")
    s.add_argument("--side", choices=["long", "short"], required=True)
    s.add_argument("--collateral", type=float, required=True, help="USDC collateral")
    s.add_argument("--leverage", type=float, required=True)
    s.add_argument("--order-type", default="MARKET",
                   choices=["MARKET", "LIMIT", "STOP"])
    s.add_argument("--tp-pct", type=float, default=None,
                   help="take-profit as percent of current price")
    s.add_argument("--sl-pct", type=float, default=None,
                   help="stop-loss as percent of current price")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_open)

    s = sub.add_parser("close", help="close an existing position")
    s.add_argument("--pair-id", type=int, required=True)
    s.add_argument("--trade-index", type=int, required=True)
    s.add_argument("--percent", type=int, default=100)
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_close)

    args = p.parse_args()
    return asyncio.run(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
