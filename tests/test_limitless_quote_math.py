"""Pure regression tests for Limitless/PM quote arithmetic."""

from decimal import Decimal
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.limitless_quote_math import (
    normalize_limitless_book,
    normalize_pm_book,
    quote_pair,
)


def lim_book(asks, bids=None):
    return {"tokenId": "yes-token", "asks": asks, "bids": bids or []}


def pm_book(asks):
    return {"asks": asks}


def market(rate=0, exponent=1):
    return {"feeSchedule": {"rate": rate, "exponent": exponent, "takerOnly": True}}


def test_false_profit_counterexample_uses_net_limitless_floor():
    result = quote_pair(
        lim_book([{"price": "0.50", "size": 20_000_000}]),
        "yes-token", "YES",
        pm_book([{"price": "0.49", "size": 20}]),
        market(), cap_usdc=10,
    )
    assert result["matched_net_shares"] == Decimal("19.4")
    assert result["limitless"]["fee_bound_contracts"] == Decimal("0.6")
    assert result["pm"]["cost_usdc"] == Decimal("9.506")
    assert result["total_cash_usdc"] == Decimal("19.506")
    assert result["conditional_payout_floor_usdc"] == Decimal("19.4")
    assert result["conditional_profit_floor_usdc"] == Decimal("-0.106")


def test_no_inversion_raw_micro_contracts_and_sorting():
    normalized = normalize_limitless_book(
        lim_book(
            asks=[{"price": "0.30", "size": 2_000_000}],
            bids=[{"price": "0.80", "size": 3_000_000},
                  {"price": "0.60", "size": 1_000_000}],
        ),
        "yes-token", "NO",
    )
    assert [(x.price, x.size) for x in normalized] == [
        (Decimal("0.2"), Decimal("3")),
        (Decimal("0.4"), Decimal("1")),
    ]

    # A high YES bid becomes a low NO ask, so the requested side's pricing is
    # asymmetric even though the source book is the YES book.
    assert normalized[0].price < normalized[1].price


def test_pm_fee_exponent_two_is_charged_per_level():
    result = quote_pair(
        lim_book([{"price": "0.30", "size": 2_000_000}]),
        "yes-token", "YES",
        pm_book([{"price": "0.20", "size": 1},
                 {"price": "0.40", "size": 1}]),
        market(rate="0.25", exponent="2"), cap_usdc=10,
        lim_fee_bound=0,
    )
    # Fee/share: .25*(.2*.8)^2=.0064 and .25*(.4*.6)^2=.0144.
    assert result["pm"]["fee_usdc"] == Decimal("0.0208")
    assert result["pm"]["fills"][0]["fee_usdc"] == Decimal("0.0064")
    assert result["pm"]["fills"][1]["fee_usdc"] == Decimal("0.0144")


def test_displayed_depth_and_cash_cap_bind():
    result = quote_pair(
        lim_book([{"price": "0.40", "size": 30_000_000}]),
        "yes-token", "YES",
        pm_book([{"price": "0.50", "size": 30}]),
        market(rate="0.04", exponent=1), cap_usdc=5,
    )
    # Limitless cap gives 12.5 gross * .97 = 12.125 net; PM's all-in
    # 0.51/share capacity is lower, so PM binds and residual depth is reported.
    assert result["matched_net_shares"] > 0
    assert result["budget_limited"]
    assert result["unfilled"]
    assert result["limitless"]["unfilled_net_contracts_lower"] > 0
    assert result["pm"]["unfilled_shares"] > 0

    # Reverse prices so the Limitless leg, rather than PM, is the cash cap.
    reverse = quote_pair(
        lim_book([{"price": "0.80", "size": 30_000_000}]),
        "yes-token", "YES",
        pm_book([{"price": "0.20", "size": 30}]),
        market(rate="0.04", exponent=1), cap_usdc=5,
    )
    assert reverse["budget_limited_legs"] == ("limitless",)

    depth_only = quote_pair(
        lim_book([{"price": "0.40", "size": 2_000_000}]),
        "yes-token", "YES",
        pm_book([{"price": "0.50", "size": "1.94"}]),
        market(rate=0, exponent=1), cap_usdc=100,
    )
    assert depth_only["unfilled"] is False
    assert depth_only["budget_limited"] is False
    assert depth_only["budget_limited_legs"] == ()


def test_limitless_micro_floor_is_applied_once():
    # PM capacity lands between two Limitless micro-contract quantities.
    result = quote_pair(
        lim_book([{"price": "0.40", "size": 10_000_000}]),
        "yes-token", "YES",
        pm_book([{"price": "0.50", "size": "1.0000004"}]),
        market(rate=0), cap_usdc=100,
    )
    assert result["limitless"]["gross_contracts"] == Decimal("1.030928")
    assert result["matched_net_shares"] == Decimal("1.00000016")
    assert result["pm"]["shares"] == result["matched_net_shares"]


def test_unsorted_levels_are_sorted_and_bad_values_raise():
    assert [x.price for x in normalize_pm_book(pm_book([
        {"price": ".7", "size": 1}, {"price": ".2", "size": 1}
    ]))] == [Decimal(".2"), Decimal(".7")]
    with pytest.raises(ValueError):
        normalize_limitless_book({"tokenId": "other", "asks": [], "bids": []}, "yes-token", "YES")
    with pytest.raises(ValueError):
        normalize_limitless_book(lim_book([{"price": 0, "size": 1}]), "yes-token", "YES")
    with pytest.raises(ValueError):
        normalize_pm_book(pm_book([{"price": "nan", "size": 1}]))
    with pytest.raises(ValueError):
        quote_pair(lim_book([{"price": ".5", "size": 1_000_000}]), "yes-token", "YES",
                   pm_book([{"price": ".5", "size": 1}]), market(), 0)
