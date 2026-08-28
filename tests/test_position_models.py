"""Regression tests for hazard-decay signals and operational position scope."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import brownian_bridge_fv as brownian  # noqa: E402
import portfolio_kelly  # noqa: E402


def test_portfolio_kelly_recognizes_generic_and_legacy_set_markers() -> None:
    assert portfolio_kelly.set_only_label({"set_only": "range"}) == "range"
    assert portfolio_kelly.set_only_label({"arb_paired": "arb"}) == "arb"
    assert portfolio_kelly.set_only_label({"p_yes": 0.7}) is None
    assert portfolio_kelly.set_only_label(None) is None


def test_survival_hazard_rolls_toward_one() -> None:
    assert math.isclose(
        brownian.fair_mark_hazard(0.81, 0.5, "survival"),
        0.90,
        rel_tol=0,
        abs_tol=1e-12,
    )


def test_occurrence_hazard_rolls_toward_zero() -> None:
    assert math.isclose(
        brownian.fair_mark_hazard(0.19, 0.5, "occurrence"),
        0.10,
        rel_tol=0,
        abs_tol=1e-12,
    )


def test_mutable_current_prior_without_bb_metadata_is_non_actionable() -> None:
    result = brownian.assess_brownian_signal(
        mark=0.045,
        prior={"p_yes": 0.09},
        t_frac=0.358,
    )

    assert result["status"] == "NON_ACTIONABLE"
    assert result["actionable"] is False
    assert result["verdict"] == "NO_BB_MODEL"
    assert result["fair_bb"] is None
    assert result["delta_pp"] is None
    assert "bb_entry_p" in result["reason"]
    assert "bb_mode" in result["reason"]


@pytest.mark.parametrize("module", [brownian, portfolio_kelly])
def test_operational_filter_excludes_dust(module) -> None:
    rows = [
        {"slug": "resolved-dust", "size": 0.247019},
        {"slug": "boundary-is-not-live", "size": 0.5},
        {"slug": "live", "size": 0.500001},
        {"slug": "also-live", "size": "15"},
        {"slug": "invalid", "size": "not-a-number"},
    ]

    assert [p["slug"] for p in module.filter_operational_positions(rows)] == [
        "live",
        "also-live",
    ]


@pytest.mark.parametrize("module", [brownian, portfolio_kelly])
def test_fetch_positions_requests_threshold_and_defensively_filters(monkeypatch, module) -> None:
    calls = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> list[dict]:
            # Simulate data-api ignoring sizeThreshold and returning dust anyway.
            return [
                {"slug": "resolved-dust", "size": 0.247019},
                {"slug": "live", "size": 2.0},
            ]

    class FakeClient:
        def __init__(self, **_kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def get(self, url, *, params):
            calls.append((url, params))
            return FakeResponse()

    monkeypatch.setattr(module.httpx, "Client", FakeClient)

    assert module.fetch_positions("0xABC") == [{"slug": "live", "size": 2.0}]
    assert calls[0][1]["user"] == "0xabc"
    assert calls[0][1]["sizeThreshold"] == module.MIN_POSITION_SHARES
