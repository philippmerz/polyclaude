"""Regressions for directional UMA price-move reporting."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import uma_status_check as uma  # noqa: E402


def test_yes_price_move_message_preserves_direction() -> None:
    assert "(-7.2pp)" in uma._yes_price_move_message(0.835, 0.763)
    assert "(+7.2pp)" in uma._yes_price_move_message(0.763, 0.835)


def test_status_change_surfaces_resolution_and_dedupes_it() -> None:
    assert uma._status_change_alert_type(None, "resolved", visible=True) == "UMA_RESOLVED"
    assert (
        uma._status_change_alert_type("proposed", "resolved", visible=False)
        == "INVISIBLE_BUT_RESOLVED"
    )
    assert uma._status_change_alert_type("resolved", "resolved", visible=True) is None


def test_status_change_preserves_dispute_visibility_class() -> None:
    assert (
        uma._status_change_alert_type("proposed", "disputed", visible=True)
        == "UMA_STATUS_CHANGE"
    )
    assert (
        uma._status_change_alert_type("proposed", "disputed", visible=False)
        == "INVISIBLE_BUT_DISPUTED"
    )
    assert (
        uma._status_change_alert_type("proposed", "proposed", visible=False)
        == "INVISIBLE_BUT_PROPOSED"
    )
    assert (
        uma._status_change_alert_type("disputed", "disputed", visible=False)
        == "INVISIBLE_BUT_DISPUTED"
    )


def test_market_id_survives_slug_index_delisting_via_cache() -> None:
    cache = {"held-market": {"market_id": "3943918"}}
    assert uma._market_id_with_cache(None, cache, "held-market") == "3943918"
    assert uma._market_id_with_cache("fresh-id", cache, "held-market") == "fresh-id"
    assert uma._market_id_with_cache(None, cache, "unknown") is None


def test_transient_fetch_failure_preserves_direct_id_and_last_good_state() -> None:
    previous = {
        "market_id": "3943918",
        "umaResolutionStatus": "proposed",
        "outcomePrices": (0.7, 0.3),
    }
    retained = uma._cache_entry_after_fetch_failure(previous, "3943918")
    assert retained == previous
    assert retained is not previous

    first_failure = uma._cache_entry_after_fetch_failure(None, "new-id")
    assert first_failure == {"market_id": "new-id"}
