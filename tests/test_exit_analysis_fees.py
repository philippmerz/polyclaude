"""Focused regressions for execution-time exit fee routing and math."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import exit_analysis as exits  # noqa: E402
import pm_fees  # noqa: E402


CID = "0xabc"


class _Response:
    def __init__(self, payload: object, *, error: Exception | None = None):
        self.payload = payload
        self.error = error

    def raise_for_status(self) -> None:
        if self.error is not None:
            raise self.error

    def json(self) -> object:
        return self.payload


def test_compact_v2_descriptor_overrides_stale_full_1000(monkeypatch) -> None:
    calls: list[str] = []

    def get(url: str, **_kwargs) -> _Response:
        calls.append(url)
        assert "/clob-markets/" in url
        return _Response({
            "c": CID,
            "fd": {"r": 0.04, "e": 1, "to": True},
            "tbf": 1000,
        })

    monkeypatch.setattr(exits.httpx, "get", get)

    market = exits._execution_fee_market(CID)

    assert market == {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True},
    }
    assert pm_fees.fee_per_share(market, 0.5) == pytest.approx(0.04 * 0.25)
    assert len(calls) == 1  # a valid fd never consults the stale full field


def test_compact_absence_accepts_only_explicit_full_zero(monkeypatch) -> None:
    def get(url: str, **_kwargs) -> _Response:
        if "/clob-markets/" in url:
            return _Response({"c": CID, "fd": None})
        return _Response({"condition_id": CID, "taker_base_fee": "0"})

    monkeypatch.setattr(exits.httpx, "get", get)

    market = exits._execution_fee_market(CID)

    assert market == {"takerBaseFee": 0}
    assert pm_fees.fee_per_share(market, 0.5) == 0.0


@pytest.mark.parametrize(
    "compact,full",
    [
        ({"c": CID, "fd": None}, {"condition_id": CID, "taker_base_fee": 1000}),
        ({"c": CID, "fd": "malformed"}, {"condition_id": CID, "taker_base_fee": 0}),
        ({"c": "0xwrong", "fd": {"r": 0, "e": 1}}, {"condition_id": CID, "taker_base_fee": 0}),
    ],
)
def test_ambiguous_metadata_fails_closed(monkeypatch, compact: dict, full: dict) -> None:
    def get(url: str, **_kwargs) -> _Response:
        return _Response(compact if "/clob-markets/" in url else full)

    monkeypatch.setattr(exits.httpx, "get", get)

    market = exits._execution_fee_market(CID)

    assert market is None
    assert pm_fees.fee_per_share(market, 0.5) == pytest.approx(0.07 * 0.25)


def test_unreachable_compact_metadata_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(
        exits.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({}, error=RuntimeError("offline")),
    )

    assert exits._execution_fee_market(CID) is None


def test_book_walk_charges_each_level_with_structured_exponent(monkeypatch) -> None:
    book = {
        "bids": [
            {"price": "0.40", "size": "3"},
            {"price": "0.60", "size": "2"},
        ]
    }
    monkeypatch.setattr(exits.httpx, "get", lambda *_args, **_kwargs: _Response(book))
    market = {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.25, "exponent": 2, "takerOnly": False},
    }

    gross, filled, fee = exits._walk_bids("token", 4.0, market)

    expected_fee = 2 * 0.25 * (0.60 * 0.40) ** 2 + 2 * 0.25 * (0.40 * 0.60) ** 2
    assert gross == pytest.approx(2.0)
    assert filled == pytest.approx(4.0)
    assert fee == pytest.approx(expected_fee)


@pytest.mark.parametrize(
    "level",
    [
        {"price": "1.01", "size": "2"},
        {"price": "0.50", "size": "-1"},
        {"price": "nan", "size": "2"},
    ],
)
def test_book_walk_rejects_malformed_binary_levels(monkeypatch, level: dict) -> None:
    monkeypatch.setattr(
        exits.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({"bids": [level]}),
    )

    with pytest.raises(ValueError, match="malformed binary bid level"):
        exits._walk_bids("token", 1.0, {"takerBaseFee": 0})


def test_breakeven_solves_general_v2_exponent() -> None:
    market = {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.25, "exponent": 2, "takerOnly": True},
    }

    price = exits._taker_breakeven(0.40, market)

    assert price is not None
    assert price - pm_fees.fee_per_share(market, price) == pytest.approx(0.40)
    assert price > 0.40


def test_breakeven_refuses_nonmonotone_extreme_curve() -> None:
    market = {
        "feesEnabled": True,
        "feeSchedule": {"rate": 10.0, "exponent": 2, "takerOnly": True},
    }

    assert exits._taker_breakeven(0.05, market) is None
