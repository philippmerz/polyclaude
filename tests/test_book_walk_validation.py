"""Pure valuation regressions: malformed depth is unknown, not a price."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import book_walk  # noqa: E402


def _net_walk(bids, size):
    return book_walk.realizable(bids, size, {"takerBaseFee": 0})


@pytest.fixture(params=[book_walk.walk_bids, _net_walk])
def walk(request):
    return request.param


@pytest.mark.parametrize("bad", [-1, "NaN", "Infinity", "-Infinity", None, True, "bad"])
def test_requested_size_must_be_finite_nonnegative(walk, bad):
    with pytest.raises(ValueError, match="requested size"):
        walk([{"price": ".5", "size": "1"}], bad)


@pytest.mark.parametrize("field,bad", [
    ("price", "1.5"), ("price", "-0.1"), ("price", "NaN"),
    ("price", "Infinity"), ("price", None), ("price", True),
    ("size", "-10"), ("size", "NaN"), ("size", "Infinity"),
    ("size", None), ("size", False), ("size", "bad"),
])
def test_bad_levels_never_produce_valuation(walk, field, bad):
    level = {"price": ".5", "size": "2", field: bad}
    with pytest.raises(ValueError, match="bid"):
        walk([level], 1)


@pytest.mark.parametrize("bids", [None, {}, "", [None], [{}], [{"price": ".5"}]])
def test_invalid_shape_is_not_an_empty_book(walk, bids):
    with pytest.raises(ValueError, match="bid"):
        walk(bids, 1)


def test_unconsumed_malformed_level_still_invalidates_book(walk):
    with pytest.raises(ValueError, match="bid size"):
        walk([
            {"price": ".9", "size": "10"},
            {"price": ".1", "size": "-1"},
        ], 1)


def test_valid_zero_levels_and_binary_boundaries():
    bids = [
        {"price": "0", "size": "2"},
        {"price": "1", "size": "1"},
        {"price": ".5", "size": "0"},
    ]
    before = deepcopy(bids)
    assert book_walk.walk_bids(bids, 4) == pytest.approx((1, .25, 1))
    assert _net_walk(bids, 4) == pytest.approx({
        "gross": 1, "fee": 0, "net": 1, "avg_fill": .25, "unfilled": 1,
    })
    assert bids == before


def test_empty_book_and_zero_request_remain_valid():
    assert book_walk.walk_bids([], 3) == (0, 0, 3)
    assert book_walk.walk_bids([], 0) == (0, 0, 0)
    assert _net_walk([], 3)["unfilled"] == 3
    assert _net_walk([], 0) == {
        "gross": 0, "fee": 0, "net": 0, "avg_fill": 0, "unfilled": 0,
    }


def test_numeric_strings_and_nonlinear_per_level_fees_are_preserved():
    bids = [{"price": ".2", "size": "2"}, {"price": ".6", "size": "2"}]
    market = {"feeSchedule": {"rate": .25, "exponent": 2, "takerOnly": True}}
    result = book_walk.realizable(bids, "3", market)
    assert result["gross"] == pytest.approx(1.4)
    assert result["fee"] == pytest.approx(2 * .25 * (.6 * .4) ** 2 + .25 * (.2 * .8) ** 2)
    assert result["net"] == pytest.approx(result["gross"] - result["fee"])
    assert result["unfilled"] == 0
