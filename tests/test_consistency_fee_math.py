"""Money-math pins for the Polymarket consistency basket scanner."""

from __future__ import annotations

import math
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import polymarket_consistency_scan as consistency  # noqa: E402


def test_market_fee_uses_per_market_quadratic_curve() -> None:
    assert consistency._market_fee_buy({"takerBaseFee": None}, 0.50) == 0.0
    assert math.isclose(
        consistency._market_fee_buy({"takerBaseFee": 1000}, 0.50),
        0.0175,
        rel_tol=0,
        abs_tol=1e-12,
    )
    assert math.isclose(
        consistency._market_fee_buy({"takerBaseFee": 500}, 0.50),
        0.0125,
        rel_tol=0,
        abs_tol=1e-12,
    )


def test_basket_fee_is_additive_dollars_per_share_not_price_multiplied() -> None:
    legs = [
        ({"takerBaseFee": 1000}, 0.40),
        ({"takerBaseFee": 500}, 0.60),
        ({"takerBaseFee": None}, 0.25),
    ]
    expected = 0.07 * 0.40 * 0.60 + 0.05 * 0.60 * 0.40

    assert math.isclose(
        consistency._basket_fee_per_unit(legs),
        expected,
        rel_tol=0,
        abs_tol=1e-12,
    )
