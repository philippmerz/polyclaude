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


def test_monotonicity_cosmetic_changes_do_not_rearm_review(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    fired: list[str] = []
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda _state, key: fired.append(key) or True,
    )
    state: dict = {}
    initial = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    cosmetic_change = (
        "monotonicity: 4 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.50pp +3.35pp REAL ARB"
    )

    assert watch._alert(state, "monotonicity-arb", initial, True) is True
    assert watch._alert(state, "monotonicity-arb", cosmetic_change, True) is False

    assert fired == ["monotonicity-arb"]


def test_exact_text_state_migrates_to_semantic_review(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda *_args: (_ for _ in ()).throw(AssertionError("duplicate tick")),
    )
    initial = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    cosmetic_change = (
        "monotonicity: 4 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.50pp +3.35pp REAL ARB"
    )
    state = {"reviewed_alert_texts": {"monotonicity-arb": initial}}

    assert watch._alert(state, "monotonicity-arb", cosmetic_change, True) is False
    record = state["reviewed_alerts"]["monotonicity-arb"]
    assert record["metric"] == 3.35
    assert record["fingerprint"] == "Clarity Act bar>=58.0 bar>=50.0"


def test_monotonicity_material_improvement_rearms_review(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    fired: list[str] = []
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda _state, key: fired.append(key) or True,
    )
    state: dict = {}
    initial = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    improved = (
        "monotonicity: 6 EXECUTABLE arb(s) after live-CLOB walk, best +3.85pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +6.00pp +3.85pp REAL ARB"
    )

    assert watch._alert(state, "monotonicity-arb", initial, True) is True
    assert watch._alert(state, "monotonicity-arb", improved, True) is True

    assert fired == ["monotonicity-arb", "monotonicity-arb"]
    assert state["reviewed_alerts"]["monotonicity-arb"]["metric"] == 3.85


def test_monotonicity_small_improvement_does_not_rearm_review(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    fired: list[str] = []
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda _state, key: fired.append(key) or True,
    )
    state: dict = {}
    initial = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    small_improvement = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.84pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +6.00pp +3.84pp REAL ARB"
    )

    assert watch._alert(state, "monotonicity-arb", initial, True) is True
    assert watch._alert(state, "monotonicity-arb", small_improvement, True) is False

    assert fired == ["monotonicity-arb"]


def test_monotonicity_different_best_pair_rearms_review(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    fired: list[str] = []
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda _state, key: fired.append(key) or True,
    )
    state: dict = {}
    initial = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    different_pair = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Another ladder bar>=60.0 bar>=55.0 +5.00pp +3.35pp REAL ARB"
    )

    assert watch._alert(state, "monotonicity-arb", initial, True) is True
    assert watch._alert(state, "monotonicity-arb", different_pair, True) is True

    assert fired == ["monotonicity-arb", "monotonicity-arb"]


def test_monotonicity_pair_history_suppresses_return_and_rearms_improvement(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    fired: list[str] = []
    monkeypatch.setattr(
        watch, "_fire_tick", lambda _state, key: fired.append(key) or True,
    )
    state: dict = {}
    pair_a = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    pair_b = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=64.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    pair_b_improved = pair_b.replace("best +3.35pp", "best +3.90pp").replace(
        "+3.35pp REAL", "+3.90pp REAL")

    assert watch._alert(state, "monotonicity-arb", pair_a, True) is True
    assert watch._alert(state, "monotonicity-arb", pair_b, True) is True
    assert watch._alert(state, "monotonicity-arb", pair_a, True) is False
    assert watch._alert(state, "monotonicity-arb", pair_b_improved, True) is True

    assert fired == ["monotonicity-arb"] * 3
    history = state["reviewed_alert_history"]["monotonicity-arb"]
    assert {row["fingerprint"] for row in history} == {
        "Clarity Act bar>=58.0 bar>=50.0",
        "Clarity Act bar>=64.0 bar>=50.0",
    }
    assert next(row for row in history
                if row["fingerprint"].endswith("bar>=64.0 bar>=50.0"))["metric"] == 3.90


def test_monotonicity_cosmetic_change_does_not_repeat_telegram(monkeypatch) -> None:
    monkeypatch.setattr(watch, "_append_alert", lambda _record: None)
    monkeypatch.setattr(watch, "_log", lambda _text: None)
    now = {"value": 10_000}
    monkeypatch.setattr(watch, "_now", lambda: now["value"])
    sent: list[str] = []
    monkeypatch.setattr(
        watch, "_telegram", lambda text: sent.append(text) or True,
    )
    monkeypatch.setattr(watch, "_fire_tick", lambda *_args: True)
    state: dict = {}
    initial = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    cosmetic_change = (
        "monotonicity: 7 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +6.50pp +3.35pp REAL ARB"
    )

    assert watch._alert(state, "monotonicity-arb", initial, True) is True
    now["value"] += watch.ALERT_COOLDOWN * 2
    assert watch._alert(state, "monotonicity-arb", cosmetic_change, True) is False

    assert len(sent) == 1
    history = state["notified_alert_history"]["monotonicity-arb"]
    assert len(history) == 1
    assert history[0]["metric"] == 3.35


def test_monotonicity_blocked_review_retries_without_repeat_telegram(monkeypatch) -> None:
    monkeypatch.setattr(watch, "_append_alert", lambda _record: None)
    monkeypatch.setattr(watch, "_log", lambda _text: None)
    now = {"value": 10_000}
    monkeypatch.setattr(watch, "_now", lambda: now["value"])
    sent: list[str] = []
    monkeypatch.setattr(
        watch, "_telegram", lambda text: sent.append(text) or True,
    )
    fire_results = iter([False, True])
    fired: list[str] = []

    def fire(_state: dict, key: str) -> bool:
        fired.append(key)
        return next(fire_results)

    monkeypatch.setattr(watch, "_fire_tick", fire)
    state: dict = {}
    initial = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    cosmetic_change = (
        "monotonicity: 6 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +6.00pp +3.35pp REAL ARB"
    )

    assert watch._alert(state, "monotonicity-arb", initial, True) is False
    now["value"] += watch.ALERT_COOLDOWN * 2
    assert watch._alert(state, "monotonicity-arb", cosmetic_change, True) is True

    assert len(sent) == 1
    assert fired == ["monotonicity-arb", "monotonicity-arb"]


def test_monotonicity_material_improvement_rearms_telegram(monkeypatch) -> None:
    monkeypatch.setattr(watch, "_append_alert", lambda _record: None)
    monkeypatch.setattr(watch, "_log", lambda _text: None)
    now = {"value": 10_000}
    monkeypatch.setattr(watch, "_now", lambda: now["value"])
    sent: list[str] = []
    monkeypatch.setattr(
        watch, "_telegram", lambda text: sent.append(text) or True,
    )
    monkeypatch.setattr(watch, "_fire_tick", lambda *_args: True)
    state: dict = {}
    initial = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    improved = initial.replace("best +3.35pp", "best +3.85pp").replace(
        "+3.35pp REAL", "+3.85pp REAL"
    )

    assert watch._alert(state, "monotonicity-arb", initial, True) is True
    now["value"] += watch.ALERT_COOLDOWN * 2
    assert watch._alert(state, "monotonicity-arb", improved, True) is True

    assert len(sent) == 2
    history = state["notified_alert_history"]["monotonicity-arb"]
    assert history[0]["metric"] == 3.85


def test_review_during_telegram_cooldown_does_not_mark_pair_notified(monkeypatch) -> None:
    monkeypatch.setattr(watch, "_append_alert", lambda _record: None)
    monkeypatch.setattr(watch, "_log", lambda _text: None)
    now = {"value": 10_000}
    monkeypatch.setattr(watch, "_now", lambda: now["value"])
    sent: list[str] = []
    monkeypatch.setattr(
        watch, "_telegram", lambda text: sent.append(text) or True,
    )
    fired: list[str] = []
    monkeypatch.setattr(
        watch, "_fire_tick", lambda _state, key: fired.append(key) or True,
    )
    state: dict = {}
    pair_a = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )
    pair_b = pair_a.replace("bar>=58.0", "bar>=64.0")

    assert watch._alert(state, "monotonicity-arb", pair_a, True) is True
    now["value"] += 1
    assert watch._alert(state, "monotonicity-arb", pair_b, True) is True
    assert len(sent) == 1

    now["value"] += watch.ALERT_COOLDOWN + 1
    assert watch._alert(state, "monotonicity-arb", pair_b, True) is False
    assert len(sent) == 2
    assert fired == ["monotonicity-arb", "monotonicity-arb"]


def test_failed_telegram_is_retried_even_if_review_succeeds(monkeypatch) -> None:
    monkeypatch.setattr(watch, "_append_alert", lambda _record: None)
    monkeypatch.setattr(watch, "_log", lambda _text: None)
    now = {"value": 10_000}
    monkeypatch.setattr(watch, "_now", lambda: now["value"])
    attempts: list[str] = []
    outcomes = iter([False, True])

    def send(text: str) -> bool:
        attempts.append(text)
        return next(outcomes)

    monkeypatch.setattr(watch, "_telegram", send)
    fired: list[str] = []
    monkeypatch.setattr(
        watch, "_fire_tick", lambda _state, key: fired.append(key) or True,
    )
    state: dict = {}
    alert = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +3.35pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +5.00pp +3.35pp REAL ARB"
    )

    assert watch._alert(state, "monotonicity-arb", alert, True) is True
    now["value"] += watch.ALERT_COOLDOWN + 1
    assert watch._alert(state, "monotonicity-arb", alert, True) is False

    assert len(attempts) == 2
    assert fired == ["monotonicity-arb"]
    assert state["notified_alert_history"]["monotonicity-arb"][0]["metric"] == 3.35


def test_existing_review_history_migrates_to_notification_dedupe(monkeypatch) -> None:
    monkeypatch.setattr(watch, "_append_alert", lambda _record: None)
    monkeypatch.setattr(watch, "_log", lambda _text: None)
    monkeypatch.setattr(watch, "_now", lambda: 20_000)
    monkeypatch.setattr(
        watch,
        "_telegram",
        lambda *_args: (_ for _ in ()).throw(AssertionError("duplicate Telegram")),
    )
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda *_args: (_ for _ in ()).throw(AssertionError("duplicate tick")),
    )
    fingerprint = "Clarity Act bar>=58.0 bar>=50.0"
    prior = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +4.38pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +6.00pp +4.38pp REAL ARB"
    )
    state = {
        "reviewed_alert_history": {
            "monotonicity-arb": [
                {"fingerprint": fingerprint, "metric": 4.38, "text": prior},
            ]
        }
    }
    changed = prior.replace("5 EXECUTABLE", "7 EXECUTABLE").replace(
        "+6.00pp +4.38pp", "+6.50pp +4.38pp"
    )

    assert watch._alert(state, "monotonicity-arb", changed, True) is False
    assert state["notified_alert_history"]["monotonicity-arb"][0]["metric"] == 4.38


def test_review_history_repairs_malformed_fields(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    fired: list[str] = []
    monkeypatch.setattr(
        watch, "_fire_tick", lambda _state, key: fired.append(key) or True,
    )
    state = {
        "alerts": None,
        "alert_texts": None,
        "reviewed_alert_history": None,
        "reviewed_alerts": None,
        "reviewed_alert_texts": None,
    }

    assert watch._alert(state, "monotonicity-arb", "new quote", True) is True
    assert fired == ["monotonicity-arb"]
    assert state["reviewed_alert_history"]["monotonicity-arb"]


def test_review_history_duplicate_keeps_highest_metric(monkeypatch) -> None:
    _quiet_side_effects(monkeypatch)
    monkeypatch.setattr(watch, "_now", lambda: 10_000)
    monkeypatch.setattr(
        watch,
        "_fire_tick",
        lambda *_args: (_ for _ in ()).throw(AssertionError("duplicate tick")),
    )
    fingerprint = "Clarity Act bar>=58.0 bar>=50.0"
    state = {
        "reviewed_alert_history": {
            "monotonicity-arb": [
                {"fingerprint": fingerprint, "metric": 4.38, "text": "higher"},
                {"fingerprint": fingerprint, "metric": 3.35, "text": "later lower"},
            ]
        }
    }
    text = (
        "monotonicity: 5 EXECUTABLE arb(s) after live-CLOB walk, best +4.50pp — "
        "Clarity Act bar>=58.0 bar>=50.0 +6.00pp +4.50pp REAL ARB"
    )

    assert watch._alert(state, "monotonicity-arb", text, True) is False
    history = state["reviewed_alert_history"]["monotonicity-arb"]
    assert len(history) == 1
    assert history[0]["metric"] == 4.38


def test_load_state_rejects_non_object_json(monkeypatch, tmp_path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text("[]")
    monkeypatch.setattr(watch, "STATE_PATH", state_path)

    assert watch._load_state() == {"last": {}, "alerts": {}, "last_cron": 0}


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
