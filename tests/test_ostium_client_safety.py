"""Safety regressions for the legacy Ostium execution wrapper."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import ostium_client  # noqa: E402


def test_legacy_open_is_blocked_before_loading_a_signing_sdk(monkeypatch) -> None:
    def forbidden():
        raise AssertionError("signing SDK must not be loaded")

    monkeypatch.setattr(ostium_client, "_sdk", forbidden)
    args = argparse.Namespace()
    assert asyncio.run(ostium_client.cmd_open(args)) == 3


def test_revoke_refuses_while_any_limit_is_active(monkeypatch) -> None:
    class Subgraph:
        async def get_orders(self, _addr):
            return [{"id": "still-active"}]

    class Ostium:
        @staticmethod
        def get_public_address():
            return "0x0000000000000000000000000000000000000001"

    class SDK:
        ostium = Ostium()
        subgraph = Subgraph()

        async def get_open_trades(self):
            return [], self.ostium.get_public_address()

    monkeypatch.setattr(ostium_client, "_sdk", SDK)
    assert asyncio.run(ostium_client.cmd_revoke_allowance(
        argparse.Namespace(yes=True))) == 2


def test_revoke_refuses_while_any_trade_is_open(monkeypatch) -> None:
    class Subgraph:
        async def get_orders(self, _addr):
            return []

    class Ostium:
        @staticmethod
        def get_public_address():
            return "0x0000000000000000000000000000000000000001"

    class SDK:
        ostium = Ostium()
        subgraph = Subgraph()

        async def get_open_trades(self):
            return [{"id": "still-open"}], self.ostium.get_public_address()

    monkeypatch.setattr(ostium_client, "_sdk", SDK)
    assert asyncio.run(ostium_client.cmd_revoke_allowance(
        argparse.Namespace(yes=True))) == 2


def test_close_rejects_invalid_percent_before_loading_sdk(monkeypatch) -> None:
    monkeypatch.setattr(
        ostium_client, "_sdk",
        lambda: (_ for _ in ()).throw(AssertionError("SDK must not load")),
    )
    args = argparse.Namespace(pair_id=1, trade_index=0, percent=101, yes=True)
    assert asyncio.run(ostium_client.cmd_close(args)) == 2


def test_close_requires_exact_open_trade(monkeypatch) -> None:
    class SDK:
        @staticmethod
        async def get_open_trades():
            return [], "0x0000000000000000000000000000000000000001"

    monkeypatch.setattr(ostium_client, "_sdk", SDK)
    args = argparse.Namespace(pair_id=1, trade_index=0, percent=100, yes=True)
    assert asyncio.run(ostium_client.cmd_close(args)) == 2


def test_full_close_checks_receipt_and_final_trade_state(monkeypatch) -> None:
    held = {
        "pair": {"id": "1"}, "index": "0", "tradeID": "trade-1",
        "collateral": "5000000",
    }

    class Receipt:
        status = 1
        transactionHash = None

    class Ostium:
        @staticmethod
        def close_trade(**_kwargs):
            return {"receipt": Receipt(), "order_id": 42}

    class Subgraph:
        @staticmethod
        async def get_order_by_id(_order_id):
            return {
                "isPending": False, "isCancelled": False,
                "orderAction": "Close", "pair": {"id": "1"},
                "tradeID": "trade-1",
                "trader": "0x0000000000000000000000000000000000000001",
            }

    class SDK:
        ostium = Ostium()
        subgraph = Subgraph()

        class W3:
            class Eth:
                @staticmethod
                def get_transaction_count(_addr, _block):
                    return 7
            eth = Eth()
        w3 = W3()

        def __init__(self):
            self.reads = 0

        async def get_open_trades(self):
            self.reads += 1
            rows = [held] if self.reads == 1 else []
            return rows, "0x0000000000000000000000000000000000000001"

        @staticmethod
        async def get_formatted_pairs_details():
            return [{"id": 1, "from": "SPX", "to": "USD", "price": 7000.0}]

    sdk = SDK()
    monkeypatch.setattr(ostium_client, "_sdk", lambda: sdk)
    args = argparse.Namespace(pair_id=1, trade_index=0, percent=100, yes=True)
    assert asyncio.run(ostium_client.cmd_close(args)) == 0


def test_close_rejects_failed_request_receipt(monkeypatch) -> None:
    held = {
        "pair": {"id": "1"}, "index": "0", "tradeID": "trade-1",
        "collateral": "5000000",
    }

    class Receipt:
        status = 0
        transactionHash = None

    class Ostium:
        @staticmethod
        def close_trade(**_kwargs):
            return {"receipt": Receipt(), "order_id": 42}

    class SDK:
        ostium = Ostium()

        class W3:
            class Eth:
                @staticmethod
                def get_transaction_count(_addr, _block):
                    return 7
            eth = Eth()
        w3 = W3()

        @staticmethod
        async def get_open_trades():
            return [held], "0x0000000000000000000000000000000000000001"

        @staticmethod
        async def get_formatted_pairs_details():
            return [{"id": 1, "from": "SPX", "to": "USD", "price": 7000.0}]

    monkeypatch.setattr(ostium_client, "_sdk", SDK)
    args = argparse.Namespace(pair_id=1, trade_index=0, percent=100, yes=True)
    assert asyncio.run(ostium_client.cmd_close(args)) == 3


def test_close_refuses_when_pending_nonce_differs(monkeypatch) -> None:
    held = {"pair": {"id": "1"}, "index": "0", "tradeID": "trade-1"}

    class SDK:
        class W3:
            class Eth:
                @staticmethod
                def get_transaction_count(_addr, block):
                    return 7 if block == "latest" else 8
            eth = Eth()
        w3 = W3()

        @staticmethod
        async def get_open_trades():
            return [held], "0x0000000000000000000000000000000000000001"

        @staticmethod
        async def get_formatted_pairs_details():
            return [{"id": 1, "from": "SPX", "to": "USD", "price": 7000.0}]

    monkeypatch.setattr(ostium_client, "_sdk", SDK)
    args = argparse.Namespace(pair_id=1, trade_index=0, percent=100, yes=True)
    assert asyncio.run(ostium_client.cmd_close(args)) == 2


def test_close_poll_read_failure_is_reconciliation_required(monkeypatch) -> None:
    held = {"pair": {"id": "1"}, "index": "0", "tradeID": "trade-1"}

    class Receipt:
        status = 1
        transactionHash = None

    class Ostium:
        @staticmethod
        def close_trade(**_kwargs):
            return {"receipt": Receipt(), "order_id": 42}

    class Subgraph:
        @staticmethod
        async def get_order_by_id(_order_id):
            raise ConnectionError("subgraph unavailable")

    class SDK:
        ostium = Ostium()
        subgraph = Subgraph()

        class W3:
            class Eth:
                @staticmethod
                def get_transaction_count(_addr, _block):
                    return 7
            eth = Eth()
        w3 = W3()

        @staticmethod
        async def get_open_trades():
            return [held], "0x0000000000000000000000000000000000000001"

        @staticmethod
        async def get_formatted_pairs_details():
            return [{"id": 1, "from": "SPX", "to": "USD", "price": 7000.0}]

    monkeypatch.setattr(ostium_client, "_sdk", SDK)
    args = argparse.Namespace(pair_id=1, trade_index=0, percent=100, yes=True)
    assert asyncio.run(ostium_client.cmd_close(args)) == 4
