"""Fail-closed parsing tests for Gamma market fee metadata."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import pm_fees  # noqa: E402


FALLBACK = pm_fees.FEE_RATE_FALLBACK


@pytest.mark.parametrize(
    "market",
    [
        {},
        {"feeSchedule": None},
        {"feesEnabled": True},
        {"feesEnabled": True, "feeSchedule": None},
        {
            "feesEnabled": True,
            "feeSchedule": None,
            "takerBaseFee": None,
        },
        {
            "feesEnabled": True,
            "feeSchedule": None,
            "takerBaseFee": 0,
        },
        {"feesEnabled": None, "takerBaseFee": None},
        {"feesEnabled": "false", "takerBaseFee": None},
        {"feesEnabled": 0, "takerBaseFee": 0},
    ],
)
def test_missing_or_contradictory_fee_metadata_fails_closed(market: dict) -> None:
    assert pm_fees.fee_rate(market) == FALLBACK


@pytest.mark.parametrize(
    "market",
    [
        {"feesEnabled": False},
        {"takerBaseFee": None},
        {"takerBaseFee": "None"},
        {"takerBaseFee": 0},
        {"takerBaseFee": "0"},
    ],
)
def test_only_explicit_fee_free_legacy_or_disabled_payloads_are_zero(
    market: dict,
) -> None:
    assert pm_fees.fee_rate(market) == 0.0


def test_explicit_structured_zero_remains_authoritative_when_fees_enabled() -> None:
    market = {
        "feesEnabled": True,
        "takerBaseFee": 1000,
        "feeSchedule": {"rate": 0, "exponent": 1, "takerOnly": True},
    }

    curve = pm_fees.fee_schedule(market)

    assert curve.rate == 0.0
    assert curve.authoritative is True


@pytest.mark.parametrize("bad_schedule", [[], "", 0, "garbage"])
def test_non_mapping_structured_schedule_is_not_allowed_to_fall_through(
    bad_schedule: object,
) -> None:
    market = {"feeSchedule": bad_schedule, "takerBaseFee": 0}
    assert pm_fees.fee_per_share(market, 0.5) == pm_fees.MALFORMED_FEE_PER_SHARE


def test_enabled_old_payload_may_still_use_an_explicit_positive_legacy_rate() -> None:
    market = {"feesEnabled": True, "takerBaseFee": 500}
    assert pm_fees.fee_rate(market) == 0.05


def test_buy_limit_reserves_maximum_all_in_cost_without_double_counting_fee() -> None:
    market = {
        "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True},
    }
    assert pm_fees.max_taker_buy_cost_through(market, 0.20) == pytest.approx(
        0.20 + 0.04 * 0.20 * 0.80)
    assert pm_fees.max_taker_buy_cost_through(market, 0.80) == pytest.approx(
        0.80 + 0.04 * 0.80 * 0.20)
    nonmonotone = {
        "feeSchedule": {"rate": 2.0, "exponent": 1, "takerOnly": True},
    }
    with pytest.raises(ValueError, match="non-monotone"):
        pm_fees.max_taker_buy_cost_through(nonmonotone, 0.90)
    with pytest.raises(ValueError):
        pm_fees.max_taker_buy_cost_through(market, float("nan"))


@pytest.mark.parametrize(
    "schedule",
    [
        {"rate": 0.03},
        {"rate": 0.03, "exponent": None},
        {"rate": 0.03, "exponent": float("nan")},
        {"rate": 0.03, "exponent": -1},
        {"exponent": 1},
        {"rate": False, "exponent": 1},
        {"rate": 0.03, "exponent": False},
    ],
)
def test_incomplete_structured_curve_uses_maximal_fail_closed_fee(schedule) -> None:
    curve = pm_fees.fee_schedule({"feesEnabled": True, "feeSchedule": schedule})
    assert curve.rate == pm_fees.MALFORMED_FEE_PER_SHARE
    assert curve.authoritative is True
    assert curve.exponent == 0.0
    assert pm_fees.fee_per_share(
        {"feesEnabled": True, "feeSchedule": schedule}, 0.5
    ) == pm_fees.MALFORMED_FEE_PER_SHARE
