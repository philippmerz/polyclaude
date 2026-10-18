"""Regression tests for safe post-only maker price construction and routing."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import book_walk  # noqa: E402
import polyclaude_enter as entry  # noqa: E402


@pytest.mark.parametrize(
    ("bid", "ask", "tick", "expected"),
    [
        (0.44, 0.50, 0.01, 0.45),
        (0.44, 0.45, 0.01, 0.44),
        (0.441, 0.445, 0.001, 0.44),
        (0.44, None, 0.01, 0.45),
        # A valid cent/tick grid point above this sub-cent best bid exists.
        (0.008, 0.03, 0.001, 0.01),
        # Decimal strings avoid a false floating-point strict inequality.
        ("0.44", "0.50", "0.01", 0.45),
        # The ask is the binary payout boundary; keep a valid price below it.
        (0.99, 1.0, 0.01, 0.99),
        # With no ask, cap the returned binary price below one dollar.
        (0.999, None, 0.001, 0.99),
        # A non-cent tick's common grid is five cents.
        (0.50, 0.60, 0.025, 0.55),
    ],
)
def test_maker_price_is_on_both_grids_and_passive(bid, ask, tick, expected):
    price = book_walk.maker_rest_price(bid, ask, tick)
    assert price == pytest.approx(expected)
    price_d = Decimal(str(price))
    tick_d = Decimal(str(tick))
    assert price_d > 0
    assert price_d < 1
    assert (price_d * 100) == (price_d * 100).to_integral_value()
    assert (price_d / tick_d) == (price_d / tick_d).to_integral_value()
    if ask is not None:
        assert price_d < Decimal(str(ask))


def test_no_positive_price_exists_below_one_cent_boundary():
    # In binary floats, .009 + .001 can compare below .01. Decimal arithmetic
    # sees that the only one-cent quote would equal the ask, so fails closed.
    with pytest.raises(ValueError, match="no positive price"):
        book_walk.maker_rest_price(0.009, 0.01, 0.001)


def test_tick_cent_grid_matrix_stays_strictly_passive():
    ticks = [Decimal("0.01"), Decimal("0.005"), Decimal("0.001"), Decimal("0.025")]
    for tick in ticks:
        for bid_steps in (4, 17, 31, 50):
            bid = tick * bid_steps
            if bid >= Decimal("0.95"):
                continue
            for ask_steps in (1, 2, 5):
                ask = bid + tick * ask_steps
                if ask > Decimal("1"):
                    continue
                common_grid = [
                    Decimal(cents) / 100
                    for cents in range(1, 100)
                    if (Decimal(cents) / 100 / tick)
                    == (Decimal(cents) / 100 / tick).to_integral_value()
                ]
                feasible = [price for price in common_grid if price < ask]
                if not feasible:
                    with pytest.raises(ValueError):
                        book_walk.maker_rest_price(bid, ask, tick)
                    continue
                preferred = [price for price in feasible if price >= bid + tick]
                expected = min(preferred) if preferred else max(feasible)
                rest = Decimal(str(book_walk.maker_rest_price(bid, ask, tick)))
                assert rest == expected
                assert rest > 0 and rest < ask and rest < 1
                assert (rest / tick) == (rest / tick).to_integral_value()


@pytest.mark.parametrize(
    ("bid", "ask", "tick"),
    [
        (float("nan"), 0.50, 0.01),
        (0.40, float("inf"), 0.01),
        (0.40, 0.50, 0),
        (-0.01, 0.50, 0.01),
        (1.0, None, 0.01),
        (0.40, 0.0, 0.01),
        (True, 0.50, 0.01),
        (0.401, 0.50, 0.01),  # malformed best bid, off the market tick
    ],
)
def test_rejects_invalid_book_prices(bid, ask, tick):
    with pytest.raises(ValueError):
        book_walk.maker_rest_price(bid, ask, tick)


def test_invalid_passive_price_aborts_execution_before_reservation_or_signing(
    monkeypatch, capsys
):
    market = {
        "id": "test-market",
        "conditionId": "0xabc",
        "question": "Test maker price",
        "slug": "test-maker-price",
        "umaResolutionStatus": None,
        "endDate": "2027-01-01T00:00:00Z",
        "outcomePrices": '["0.50", "0.50"]',
        "clobTokenIds": '["yes-token", "no-token"]',
        "negRisk": False,
        "orderPriceMinTickSize": 0.001,
        "feesEnabled": False,
    }
    monkeypatch.setattr(entry, "fetch_market_by_slug_or_question", lambda _lookup: market)
    monkeypatch.setattr(entry, "_existing_exposure", lambda *_args: None)
    monkeypatch.setattr(entry, "_sibling_markets", lambda *_args: None)
    monkeypatch.setattr(entry, "_best_ask", lambda _token: 0.01)
    book_response = Mock()
    book_response.json.return_value = {
        "bids": [{"price": "0.009", "size": "5"}],
        "asks": [{"price": "0.01", "size": "5"}],
    }
    monkeypatch.setattr(entry.httpx, "get", lambda *_args, **_kwargs: book_response)

    def unexpected(*_args, **_kwargs):
        pytest.fail("invalid maker price must abort before reservation or signing")

    monkeypatch.setattr(entry, "_add_entry_reservation", unexpected)
    monkeypatch.setattr(entry, "_acquire_entry_lock", unexpected)
    monkeypatch.setattr(entry.subprocess, "run", unexpected)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "polyclaude_enter.py",
            "--slug",
            "test-maker-price",
            "--my-p",
            "0.90",
            "--skip-catalyst-check",
            "--maker",
            "--execute",
            "--usd",
            "5",
            "--bankroll",
            "100",
        ],
    )

    assert entry.main() == 2
    output = capsys.readouterr().out
    assert "no valid passive maker price" in output
