from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import spot_swap  # noqa: E402


def test_fee_tier_selection_maximizes_output_not_first_nonzero() -> None:
    # Regression: Arbitrum's AAVE 0.05% dust pool returned a positive but nearly
    # worthless quote, while the 0.30% pool returned normal market value.
    assert spot_swap._select_best_quote([
        (500, 3_090_000_000_000),
        (3000, 57_406_150_000_000_000),
    ]) == (3000, 57_406_150_000_000_000)


@pytest.mark.parametrize(
    "candidates",
    [[], [(500, 0)], [(0, 10)], [(500, float("nan"))], [(True, 10)]],
)
def test_fee_tier_selection_rejects_unusable_candidates(candidates) -> None:
    with pytest.raises(RuntimeError):
        spot_swap._select_best_quote(candidates)


def test_execution_floor_combines_slippage_and_independent_minimum() -> None:
    assert spot_swap._execution_floor(100_000, 1.0, None) == 99_000
    assert spot_swap._execution_floor(100_000, 1.0, 99_500) == 99_500
    assert spot_swap._execution_floor(100_000, 1.0, 90_000) == 99_000


def test_execution_floor_rejects_false_protection() -> None:
    with pytest.raises(RuntimeError, match="exceeds the live quote"):
        spot_swap._execution_floor(100_000, 1.0, 100_001)
    with pytest.raises(RuntimeError, match="invalid execution-floor"):
        spot_swap._execution_floor(100_000, 100.0, None)
    with pytest.raises(RuntimeError, match="invalid independent"):
        spot_swap._execution_floor(100_000, 1.0, 0)


def test_signing_requote_cannot_weaken_confirmed_floor() -> None:
    # Preview 100k at 1% confirms 99k. A signing quote of 98k must abort rather
    # than silently lowering protection to 97.02k.
    confirmed = spot_swap._execution_floor(100_000, 1.0, 90_000)
    assert confirmed == 99_000
    with pytest.raises(RuntimeError, match="exceeds the live quote"):
        spot_swap._execution_floor(98_000, 1.0, max(90_000, confirmed))

    # An improved quote still gets its fresh, tighter slippage-relative floor.
    assert spot_swap._execution_floor(
        102_000, 1.0, max(90_000, confirmed)) == 100_980


def test_minimum_unit_conversion_uses_decimal_ceiling() -> None:
    assert spot_swap._human_to_units(
        "0.0000000000000000011", 18, round_up=True) == 2
    assert spot_swap._human_to_units(
        "0.0000000000000000011", 18, round_up=False) == 1
    # Integer/Decimal slippage arithmetic cannot drift by base units through a
    # binary-float multiply.
    assert spot_swap._execution_floor(10**30 + 1, "0.1", None) == (
        (10**30 + 1) * 999 // 1000)


def test_quote_tiers_retry_failures_and_retain_gas_evidence() -> None:
    calls = {500: 0, 3000: 0, 10000: 0}

    class Call:
        def __init__(self, tier):
            self.tier = tier

        def call(self):
            calls[self.tier] += 1
            if self.tier == 500 and calls[self.tier] == 1:
                raise RuntimeError("transient")
            if self.tier == 10000:
                raise RuntimeError("no pool")
            amount = 100 if self.tier == 500 else 120
            return (amount, 0, 0, 50_000 + self.tier)

    class Functions:
        @staticmethod
        def quoteExactInputSingle(params):
            return Call(params[3])

    class Quoter:
        functions = Functions()

    candidates, gas, failures = spot_swap._quote_fee_tiers(
        Quoter(), "in", "out", 1_000, [500, 3000, 10000])

    assert candidates == [(500, 100), (3000, 120)]
    assert gas == {500: 50_500, 3000: 53_000}
    assert failures == [10000]
    assert calls == {500: 2, 3000: 1, 10000: 2}
