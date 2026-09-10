"""Thin wrapper around ostium-python-sdk for the polyclaude crypto sleeve.

Loads the crypto-sleeve wallet via _paths, instantiates an OstiumSDK pointed
at Arbitrum mainnet, and exposes async helpers for:
  - listing pairs and current prices (`pairs`, `pair`)
  - reading open positions (`positions`)
  - blocking new entries on eligibility and legacy-writer safety grounds
  - closing one exact full position with oracle-state reconciliation
  - revoking the legacy TradingStorage allowance

CLI usage:
    python scripts/ostium_client.py status
    python scripts/ostium_client.py pairs --group crypto
    python scripts/ostium_client.py revoke-allowance --yes
    python scripts/ostium_client.py close --pair-id 1 --trade-index 0

Read-only commands never sign anything. The blocked `open` command does not
load the signing SDK. `close` and `revoke-allowance` require the private key and
execute on-chain. The script prints a human summary and journals nothing —
narration belongs in the calling cron tick / interactive session.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from ostium_python_sdk import NetworkConfig, OstiumSDK

import _paths as _secrets

_secrets.install_scrubbing_excepthook()

ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"
ARBITRUM_CHAIN_ID = 42161
EXPECTED_USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
EXPECTED_TRADING_STORAGE = "0xcCd5891083A8acD2074690F65d3024E7D13d66E7"
LEGACY_OPEN_BLOCK = (
    "new Ostium entries are disabled: this Finland execution environment fails "
    "the current EU Services eligibility gate. Independently, legacy SDK 3.2.0 "
    "grants a $1m allowance, defaults to 2% slippage, and does not verify the "
    "final oracle fill. Both legal eligibility and a safe current writer must be "
    "established before opening exposure."
)


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
    # Neither query alone is a complete exposure inventory: limits can remain
    # active while the open-trade list is empty.
    trades, _ = await sdk.get_open_trades()
    limits = await sdk.subgraph.get_orders(addr)
    print(f"open trades: {len(trades)}")
    for t in trades:
        print(f"  {json.dumps(t, default=str)[:300]}")
    print(f"active limits: {len(limits)}")
    for order in limits:
        print(f"  {json.dumps(order, default=str)[:300]}")
    _, _, allowance = _allowance_context(sdk)
    print(f"USDC allowance to TradingStorage: {allowance / 1e6:.6f}")
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
    # Eligibility and execution integrity are independent hard gates. Closing
    # remains available for risk reduction.
    print(LEGACY_OPEN_BLOCK)
    return 3


def _allowance_context(sdk: OstiumSDK):
    """Validate exact chain/contracts and return (address, spender, allowance)."""
    w = sdk.w3
    if w.eth.chain_id != ARBITRUM_CHAIN_ID:
        raise RuntimeError(f"wrong chain: expected {ARBITRUM_CHAIN_ID}, got {w.eth.chain_id}")
    cfg = sdk.network_config.contracts
    usdc = w.to_checksum_address(cfg["usdc"])
    spender = w.to_checksum_address(cfg["tradingStorage"])
    if usdc != w.to_checksum_address(EXPECTED_USDC):
        raise RuntimeError(f"unexpected Ostium USDC contract: {usdc}")
    if spender != w.to_checksum_address(EXPECTED_TRADING_STORAGE):
        raise RuntimeError(f"unexpected Ostium TradingStorage contract: {spender}")
    if not w.eth.get_code(usdc) or not w.eth.get_code(spender):
        raise RuntimeError("USDC or TradingStorage has no deployed bytecode")
    addr = w.to_checksum_address(sdk.ostium.get_public_address())
    allowance = sdk.ostium.usdc_contract.functions.allowance(addr, spender).call()
    return addr, spender, allowance


def _trade_matches(trade: dict, pair_id: int, trade_index: int) -> bool:
    """Match the exact on-chain trade identity exposed by the subgraph."""
    try:
        return (int(trade["pair"]["id"]) == pair_id
                and int(trade["index"]) == trade_index)
    except (KeyError, TypeError, ValueError):
        return False


def _receipt_field(receipt, name: str):
    if isinstance(receipt, dict):
        return receipt.get(name)
    return getattr(receipt, name, None)


async def cmd_revoke_allowance(args: argparse.Namespace) -> int:
    """Set Ostium TradingStorage's USDC allowance to zero after exposure checks."""
    sdk = _sdk()
    addr = sdk.ostium.get_public_address()
    trades, _ = await sdk.get_open_trades()
    limits = await sdk.subgraph.get_orders(addr)
    if trades or limits:
        print(
            f"refusing allowance revocation with {len(trades)} open trade(s) and "
            f"{len(limits)} active limit(s); reconcile exposure first")
        return 2

    try:
        addr, spender, allowance = _allowance_context(sdk)
    except Exception as e:
        print(f"allowance validation FAILED, not broadcasting: {str(e)[:180]}")
        return 3
    print(
        f"current USDC allowance: {allowance / 1e6:.6f} "
        f"(wallet=...{addr[-4:]}, spender=...{spender[-4:]})")
    if allowance == 0:
        print("allowance already zero; no transaction needed")
        return 0
    if not args.yes:
        if input("revoke Ostium TradingStorage USDC allowance? [y/N] ").strip().lower() != "y":
            return 1

    approve = sdk.ostium.usdc_contract.functions.approve(spender, 0)
    try:
        simulated = approve.call({"from": addr})
        if simulated is not True:
            raise RuntimeError(f"approve(0) simulation returned {simulated!r}")
        gas_est = approve.estimate_gas({"from": addr})
    except Exception as e:
        print(f"revoke simulation FAILED, not broadcasting: {str(e)[:180]}")
        return 3

    tx = approve.build_transaction({
        "from": addr,
        "nonce": sdk.w3.eth.get_transaction_count(addr, "pending"),
        "chainId": ARBITRUM_CHAIN_ID,
        "gas": int(gas_est * 1.3),
    })
    signed = sdk.w3.eth.account.sign_transaction(tx, private_key=sdk.private_key)
    expected_hash = sdk.w3.keccak(signed.raw_transaction).hex()
    print(f"revocation prepared tx hash: {expected_hash}")
    try:
        tx_hash = sdk.w3.eth.send_raw_transaction(signed.raw_transaction)
    except Exception as e:
        print(
            f"RECONCILIATION REQUIRED: {expected_hash} may have been submitted but "
            f"the RPC response failed ({type(e).__name__}); inspect it and DO NOT RETRY")
        return 4
    if tx_hash.hex().lower() != expected_hash.lower():
        print(
            f"RECONCILIATION REQUIRED: signed hash {expected_hash} and RPC hash "
            f"{tx_hash.hex()} differ; inspect both and DO NOT RETRY")
        return 4
    print(f"revocation submitted tx: {tx_hash.hex()}")
    try:
        receipt = sdk.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    except Exception as e:
        print(
            "RECONCILIATION REQUIRED: transaction was submitted but its receipt "
            f"is unavailable ({type(e).__name__}); inspect {tx_hash.hex()} and DO NOT RETRY")
        return 4
    if receipt.status != 1:
        raise RuntimeError(f"allowance revocation reverted: {tx_hash.hex()}")
    try:
        remaining = sdk.ostium.usdc_contract.functions.allowance(addr, spender).call()
    except Exception as e:
        print(
            "RECONCILIATION REQUIRED: receipt succeeded but post-flight allowance "
            f"is unavailable ({type(e).__name__}); inspect {tx_hash.hex()} and DO NOT RETRY")
        return 4
    if remaining != 0:
        raise RuntimeError(f"post-flight allowance is not zero: {remaining}")
    print(f"revocation tx: {tx_hash.hex()}")
    print("post-flight USDC allowance: 0")
    return 0


async def cmd_close(args: argparse.Namespace) -> int:
    if args.percent != 100:
        print("the guarded legacy client supports full closes only (--percent 100)")
        return 2

    sdk = _sdk()
    trades, addr = await sdk.get_open_trades()
    matches = [
        trade for trade in trades
        if _trade_matches(trade, args.pair_id, args.trade_index)
    ]
    if len(matches) != 1:
        print(
            f"refusing close: expected exactly one open pair_id={args.pair_id} "
            f"trade_index={args.trade_index}, found {len(matches)}")
        return 2
    before = matches[0]

    pair = await sdk.get_formatted_pairs_details()
    p = next((x for x in pair if int(x["id"]) == args.pair_id), None)
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

    # Check immediately at the signing boundary. The installed SDK requests
    # `latest` internally; any pending nonce could otherwise be reused.
    latest_nonce = sdk.w3.eth.get_transaction_count(addr, "latest")
    pending_nonce = sdk.w3.eth.get_transaction_count(addr, "pending")
    if latest_nonce != pending_nonce:
        print(
            f"refusing close with unresolved nonce state: latest={latest_nonce}, "
            f"pending={pending_nonce}")
        return 2
    try:
        result = sdk.ostium.close_trade(
            pair_id=args.pair_id,
            trade_index=args.trade_index,
            market_price=px,
            close_percentage=args.percent,
        )
    except Exception as e:
        print(
            "RECONCILIATION REQUIRED: the legacy close writer raised after the "
            f"broadcast boundary ({type(e).__name__}). Re-read the exact trade "
            "and recent transactions before any retry.")
        return 4

    receipt = result.get("receipt") if isinstance(result, dict) else None
    order_id = result.get("order_id") if isinstance(result, dict) else None
    status = _receipt_field(receipt, "status")
    tx_hash = _receipt_field(receipt, "transactionHash")
    tx_label = tx_hash.hex() if hasattr(tx_hash, "hex") else str(tx_hash or "unknown")
    if status == 0:
        print(f"close request FAILED: receipt status={status!r}, tx={tx_label}")
        return 3
    if status != 1:
        print(
            f"RECONCILIATION REQUIRED: close request receipt has unknown status "
            f"{status!r}, tx={tx_label}; re-read the trade and DO NOT RETRY.")
        return 4
    if order_id is None:
        print(
            f"RECONCILIATION REQUIRED: close request tx {tx_label} succeeded but "
            "has no oracle order id. Re-read the trade and DO NOT RETRY.")
        return 4
    print(f"close request tx: {tx_label}; oracle order id: {order_id}")

    # The first receipt only requests an oracle price. Confirm the exact order
    # and resulting trade state before reporting that the close completed.
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 30
    while loop.time() < deadline:
        try:
            order = await asyncio.wait_for(
                sdk.subgraph.get_order_by_id(order_id), timeout=5)
        except TimeoutError:
            print(
                f"RECONCILIATION REQUIRED: order {order_id} for tx {tx_label} "
                "timed out during read; DO NOT RETRY.")
            return 4
        except Exception as e:
            print(
                f"RECONCILIATION REQUIRED: order {order_id} for tx {tx_label} "
                f"could not be read ({type(e).__name__}); DO NOT RETRY.")
            return 4
        if not order or order.get("isPending", True):
            await asyncio.sleep(min(1, max(0, deadline - loop.time())))
            continue
        if str(order.get("orderAction", "")).lower() != "close":
            print("RECONCILIATION REQUIRED: oracle order is not a close; DO NOT RETRY")
            return 4
        if order.get("isCancelled", False):
            print(f"close order cancelled: {order.get('cancelReason', 'unknown reason')}")
            return 3
        try:
            order_pair = int(order["pair"]["id"])
        except (KeyError, TypeError, ValueError):
            order_pair = -1
        if order_pair != args.pair_id:
            print("RECONCILIATION REQUIRED: close order pair mismatch; DO NOT RETRY")
            return 4
        if order.get("trader") and str(order["trader"]).lower() != str(addr).lower():
            print("RECONCILIATION REQUIRED: close order trader mismatch; DO NOT RETRY")
            return 4
        if (order.get("tradeID") is not None and before.get("tradeID") is not None
                and str(order["tradeID"]) != str(before["tradeID"])):
            print("RECONCILIATION REQUIRED: close order trade mismatch; DO NOT RETRY")
            return 4

        try:
            current, _ = await asyncio.wait_for(
                sdk.get_open_trades(), timeout=5)
        except TimeoutError:
            print(
                f"RECONCILIATION REQUIRED: exact trade state after order {order_id} "
                "timed out during read; DO NOT RETRY.")
            return 4
        except Exception as e:
            print(
                f"RECONCILIATION REQUIRED: exact trade state after order {order_id} "
                f"could not be read ({type(e).__name__}); DO NOT RETRY.")
            return 4
        remaining = [
            trade for trade in current
            if _trade_matches(trade, args.pair_id, args.trade_index)
        ]
        if not remaining:
            print("full close confirmed in exact trade state")
            return 0
        await asyncio.sleep(min(1, max(0, deadline - loop.time())))

    print(
        f"RECONCILIATION REQUIRED: close order {order_id} was not reflected in the "
        "exact trade state within 30 seconds; DO NOT RETRY.")
    return 4


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="address + open trades")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("pairs", help="list open pairs")
    s.add_argument("--group", default=None,
                   choices=["crypto", "forex", "commodities", "indices", "stocks"])
    s.set_defaults(fn=cmd_pairs)

    s = sub.add_parser("open", help="disabled until the legacy write path is replaced")
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

    s = sub.add_parser("revoke-allowance", help="set TradingStorage USDC allowance to zero")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_revoke_allowance)

    s = sub.add_parser("close", help="close an existing position")
    s.add_argument("--pair-id", type=int, required=True)
    s.add_argument("--trade-index", type=int, required=True)
    s.add_argument("--percent", type=int, default=100,
                   help="guarded legacy path supports 100 only")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_close)

    args = p.parse_args()
    return asyncio.run(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
