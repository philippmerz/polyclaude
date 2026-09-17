from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import opportunity_watch as watch


def _quiet_side_effects(monkeypatch) -> None:
    monkeypatch.setattr(watch, "_append_alert", lambda _record: None)
    monkeypatch.setattr(watch, "_telegram", lambda _text: None)
    monkeypatch.setattr(watch, "_log", lambda _text: None)


def test_actionable_payload_fires_once_after_success(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    fired: list[str] = []
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda _state, key: fired.append(key) or True,
    )
    state: dict = {}

    assert watch._alert(state, "monotonicity-arb", "same quote", True) is True
    assert watch._alert(state, "monotonicity-arb", "same quote", True) is False

    assert fired == ["monotonicity-arb"]
    assert state["reviewed_alert_texts"]["monotonicity-arb"] == "same quote"


def test_cooldown_blocked_first_review_stays_armed(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    results = iter([False, True])
    fired: list[str] = []

    def fire(_state: dict, key: str) -> bool:
        fired.append(key)
        return next(results)

    monkeypatch.setattr(watch, "_fire_tick", fire)
    state: dict = {}

    assert watch._alert(state, "monotonicity-arb", "new quote", True) is False
    assert watch._alert(state, "monotonicity-arb", "new quote", True) is True
    assert watch._alert(state, "monotonicity-arb", "new quote", True) is False

    assert fired == ["monotonicity-arb", "monotonicity-arb"]


def test_legacy_state_records_already_reviewed_payload(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda *_args: (_ for _ in ()).throw(AssertionError("duplicate tick")),
    )
    state = {
        "alerts": {"monotonicity-arb": 9_000},
        "alert_texts": {"monotonicity-arb": "same quote"},
        "last_cron": 9_001,
    }

    assert watch._alert(state, "monotonicity-arb", "same quote", True) is False
    assert state["reviewed_alert_texts"]["monotonicity-arb"] == "same quote"


def test_legacy_alert_blocked_by_older_tick_still_retries(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    fired: list[str] = []
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda _state, key: fired.append(key) or False,
    )
    state = {
        "alerts": {"monotonicity-arb": 9_000},
        "alert_texts": {"monotonicity-arb": "same quote"},
        "last_cron": 8_999,
    }

    assert watch._alert(state, "monotonicity-arb", "same quote", True) is False
    assert fired == ["monotonicity-arb"]
    assert "monotonicity-arb" not in state["reviewed_alert_texts"]
