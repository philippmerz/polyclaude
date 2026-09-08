from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import bankroll  # noqa: E402
import positions  # noqa: E402


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


def _position() -> dict:
    return {
        "outcome": "YES",
        "avgPrice": 0.4,
        "curPrice": 0.8,
        "size": 20.0,
        "initialValue": 8.0,
        "currentValue": 16.0,
        "percentPnl": 100.0,
        "redeemable": False,
        "slug": "reporting-label-contract",
        "title": "Reporting label contract",
    }


def _market() -> dict:
    return {
        "clobTokenIds": '["token-yes"]',
        "outcomes": '["YES"]',
        "feesEnabled": False,
    }


def _book() -> dict:
    return {"bids": [{"price": "0.5", "size": "20"}]}


def test_positions_output_qualifies_sequential_depth_estimate(monkeypatch, capsys) -> None:
    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, **kwargs):
            if url.endswith("/positions"):
                return _Response([_position()])
            if "gamma-api.polymarket.com" in url:
                return _Response([_market()])
            if "clob.polymarket.com" in url:
                return _Response(_book())
            raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(
        positions.Wallet,
        "load",
        staticmethod(lambda: SimpleNamespace(address="0x1234")),
    )
    monkeypatch.setattr(positions.httpx, "Client", lambda *args, **kwargs: _Client())

    positions.main()
    output = capsys.readouterr().out

    assert "REALIZABLE (depth-walked, NET of taker fees): $10.00" in output
    assert "indicative depth/fee estimate only" in output
    assert "not a synchronized or freshness-verified liquidation quote" in output


def test_positions_malformed_book_reports_unavailable_without_estimate(
    monkeypatch, capsys
) -> None:
    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, **kwargs):
            if url.endswith("/positions"):
                return _Response([_position()])
            if "gamma-api.polymarket.com" in url:
                return _Response([_market()])
            if "clob.polymarket.com" in url:
                return _Response({"bids": [{"price": "1.5", "size": "20"}]})
            raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(
        positions.Wallet,
        "load",
        staticmethod(lambda: SimpleNamespace(address="0x1234")),
    )
    monkeypatch.setattr(positions.httpx, "Client", lambda *args, **kwargs: _Client())

    positions.main()
    output = capsys.readouterr().out

    assert "(realizable check unavailable:" in output
    assert "REALIZABLE (" not in output
    assert "indicative depth/fee estimate" not in output


def test_bankroll_output_qualifies_realizable_estimate_and_uses_temp_cache(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    class _Eth:
        chain_id = 1

        @staticmethod
        def get_balance(_address):
            return 0

        @staticmethod
        def contract(**kwargs):
            return SimpleNamespace(
                functions=SimpleNamespace(
                    balanceOf=lambda _address: SimpleNamespace(call=lambda: 0)
                )
            )

    class _Web3:
        def __init__(self, chain_id):
            self.eth = _Eth()
            self.eth.chain_id = chain_id

    def fake_get(url, **kwargs):
        if url.endswith("/positions"):
            return _Response([_position()])
        if "gamma-api.polymarket.com" in url:
            return _Response([_market()])
        if "clob.polymarket.com" in url:
            return _Response(_book())
        raise AssertionError(f"unexpected URL: {url}")

    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, **kwargs):
            return fake_get(url, **kwargs)

    temp_scripts = tmp_path / "scripts"
    temp_notes = tmp_path / "notes"
    temp_scripts.mkdir()
    temp_notes.mkdir()

    monkeypatch.setattr(bankroll, "__file__", str(temp_scripts / "bankroll.py"))
    monkeypatch.setattr(bankroll.sys, "argv", ["bankroll.py"])
    monkeypatch.setattr(
        bankroll, "wallet_addresses", lambda: {"pm": "pm", "crypto": "crypto"}
    )
    monkeypatch.setattr(
        bankroll,
        "native_prices",
        lambda _warnings: {"ETH": 0.0, "POL": 0.0, "ARB": 0.0},
    )
    monkeypatch.setattr(bankroll, "pick_rpc", lambda _rpcs, chain_id: _Web3(chain_id))
    monkeypatch.setattr(bankroll, "ostium_open_trades", lambda _warnings: None)
    monkeypatch.setattr(bankroll.httpx, "get", fake_get)
    monkeypatch.setattr(bankroll.httpx, "Client", lambda *args, **kwargs: _Client())
    monkeypatch.setattr(bankroll, "PM_STATE", {})

    bankroll.main()
    output = capsys.readouterr().out

    assert "unrealized (realizable)" in output
    assert "indicative depth/fee estimate only" in output
    assert "not a synchronized or freshness-verified liquidation quote" in output
    assert "WARNING: PM sleeve marked" in output
    assert (temp_notes / ".bankroll_cache.json").exists()
