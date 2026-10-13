"""Conservative quote coverage for observed multi-price SELL fee behavior."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import book_walk  # noqa: E402
import exit_analysis  # noqa: E402
import polyclaude_enter  # noqa: E402


MARKET = {
    "feesEnabled": True,
    "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True},
}


def test_confirmed_four_price_sell_uses_conservative_aggregate_fee() -> None:
    # Receipt: 98.05 actual shares, gross 12.694290, wallet fee 0.442030.
    bids = [
        {"price": 0.142, "size": 25.7},
        {"price": 0.141, "size": 46.05},
        {"price": 0.123, "size": 6.21},
        {"price": 0.089, "size": 20.09},
    ]

    quote = book_walk.realizable(bids, 98.05, MARKET)

    assert quote["gross"] == pytest.approx(12.694290, abs=1e-12)
    assert quote["fee"] == pytest.approx(0.44204, abs=1e-12)
    assert quote["fee"] >= 0.442030  # rounds conservatively at 5dp
    assert quote["net"] == pytest.approx(12.25225, abs=1e-12)
    assert quote["avg_fill"] == pytest.approx(12.694290 / 98.05)


def test_partial_depth_fee_uses_executed_average_not_requested_average() -> None:
    bids = [
        {"price": 0.142, "size": 25.7},
        {"price": 0.141, "size": 46.05},
        {"price": 0.123, "size": 6.21},
        {"price": 0.089, "size": 20.09},
    ]

    quote = book_walk.realizable(bids, 150.0, MARKET)

    assert quote["unfilled"] == pytest.approx(51.95)
    assert quote["avg_fill"] == pytest.approx(12.694290 / 150.0)
    assert quote["fee"] == pytest.approx(0.44204, abs=1e-12)


def test_uniform_price_remains_same_as_levelwise_fee() -> None:
    bids = [{"price": 0.2, "size": 4.0}, {"price": 0.2, "size": 6.0}]

    quote = book_walk.realizable(bids, 10.0, MARKET)

    assert quote["fee"] == pytest.approx(10 * 0.04 * 0.2 * 0.8)


def test_fee_estimate_keeps_larger_per_level_curve_for_other_schedules() -> None:
    market = {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.25, "exponent": 2, "takerOnly": True},
    }
    bids = [{"price": 0.01, "size": 1.0}, {"price": 0.09, "size": 1.0}]
    levelwise = sum(q * 0.25 * (p * (1 - p)) ** 2 for p, q in [(0.01, 1), (0.09, 1)])

    quote = book_walk.realizable(bids, 2.0, market)

    assert quote["fee"] >= levelwise


def test_zero_size_has_no_fee_and_invalid_fee_payload_is_rejected() -> None:
    assert book_walk.realizable([], 0.0, MARKET) == {
        "gross": 0.0,
        "fee": 0.0,
        "net": 0.0,
        "avg_fill": 0.0,
        "unfilled": 0.0,
    }
    with pytest.raises(ValueError, match="finite nonnegative"):
        book_walk.conservative_sell_fee(float("nan"), 1, 0, MARKET)
    with pytest.raises(ValueError, match="zero filled"):
        book_walk.conservative_sell_fee(1, 0, 0, MARKET)


def test_fee_quote_ceils_five_decimals_without_float_boundary_overround() -> None:
    assert book_walk._ceil_fee_quote(0.1234500000004) == pytest.approx(0.12345)
    assert book_walk._ceil_fee_quote(0.123450000002) == pytest.approx(0.12346)
    assert book_walk._ceil_fee_quote(0.0) == 0.0


class _Response:
    def __init__(self, payload: dict):
        self.payload = payload

    def json(self) -> dict:
        return self.payload


def test_exit_analysis_prefix_walk_uses_shared_sell_fee_correction(monkeypatch) -> None:
    bids = [
        {"price": "0.142", "size": "25.7"},
        {"price": "0.141", "size": "46.05"},
        {"price": "0.123", "size": "6.21"},
        {"price": "0.089", "size": "20.09"},
    ]
    monkeypatch.setattr(
        exit_analysis.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({"bids": bids, "min_order_size": "1"}),
    )

    options = exit_analysis._walk_bid_options("token", 98.05, MARKET)

    assert options[-1][0] == pytest.approx(12.694290)
    assert options[-1][1] == pytest.approx(98.05)
    assert options[-1][2] == pytest.approx(0.44204, abs=1e-12)


def test_rollback_sell_guard_uses_same_conservative_fee() -> None:
    bids = [
        {"price": 0.142, "size": 25.7},
        {"price": 0.141, "size": 46.05},
        {"price": 0.123, "size": 6.21},
        {"price": 0.089, "size": 20.09},
    ]

    limit, depth, net = polyclaude_enter._marketable_sell_plan(bids, 98.05, MARKET)

    assert limit == pytest.approx(0.089)
    assert depth == pytest.approx(98.05)
    assert net == pytest.approx(12.25225, abs=1e-12)
