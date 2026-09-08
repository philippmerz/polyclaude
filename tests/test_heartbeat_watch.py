"""Offline regressions for heartbeat disk-space monitoring."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import heartbeat_watch as heartbeat  # noqa: E402


@pytest.fixture(autouse=True)
def block_production_side_effects(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        heartbeat,
        "_telegram",
        lambda *_args, **_kwargs: pytest.fail("real Telegram is forbidden in tests"),
    )
    for name in ("_load_state", "_save_state"):
        monkeypatch.setattr(
            heartbeat, name,
            lambda *_args, **_kwargs: pytest.fail("production state access is forbidden in tests"),
        )


def _capture_emit(monkeypatch: pytest.MonkeyPatch) -> list[tuple]:
    emitted: list[tuple] = []

    def capture(state, key, msg, cooldown=heartbeat.ALERT_COOLDOWN_SECONDS):
        emitted.append((key, msg, cooldown))
        return True

    monkeypatch.setattr(heartbeat, "_emit", capture)
    return emitted


def _usage(free: int) -> SimpleNamespace:
    return SimpleNamespace(total=2 * 1024**3, used=2 * 1024**3 - free, free=free)


def test_disk_warning_uses_warning_key_and_read_only_probe(monkeypatch: pytest.MonkeyPatch):
    emitted = _capture_emit(monkeypatch)
    monkeypatch.setattr(
        heartbeat.shutil, "disk_usage",
        lambda path: _usage(heartbeat.DISK_WARNING_BYTES - 1),
    )

    state = {"last_alerts": {}}
    heartbeat.check_disk_space(state)

    assert emitted[0][0] == "disk_space_warning"
    assert "DISK SPACE WARNING" in emitted[0][1]
    assert emitted[0][2] == heartbeat.DISK_ALERT_COOLDOWN


def test_disk_critical_escalation_has_distinct_key(monkeypatch: pytest.MonkeyPatch):
    telegram_messages: list[str] = []
    monkeypatch.setattr(
        heartbeat, "_telegram",
        lambda message: telegram_messages.append(message) or True,
    )
    monkeypatch.setattr(heartbeat, "_now", lambda: 10_000)
    monkeypatch.setattr(
        heartbeat.shutil, "disk_usage",
        lambda path: _usage(heartbeat.DISK_CRITICAL_BYTES - 1),
    )

    state = {"last_alerts": {"disk_space_warning": 10_000}}
    heartbeat.check_disk_space(state)

    assert len(telegram_messages) == 1
    assert "DISK SPACE CRITICAL" in telegram_messages[0]
    assert state["last_alerts"]["disk_space_critical"] == 10_000
    assert state["last_alerts"]["disk_space_warning"] == 10_000


def test_disk_cooldown_suppresses_warning_but_allows_critical_escalation(
    monkeypatch: pytest.MonkeyPatch,
):
    telegram_messages: list[str] = []
    monkeypatch.setattr(
        heartbeat, "_telegram",
        lambda message: telegram_messages.append(message) or True,
    )
    monkeypatch.setattr(heartbeat, "_now", lambda: 10_000)
    free = heartbeat.DISK_WARNING_BYTES - 1
    monkeypatch.setattr(heartbeat.shutil, "disk_usage", lambda path: _usage(free))

    state = {"last_alerts": {}}
    heartbeat.check_disk_space(state)
    heartbeat.check_disk_space(state)
    free = heartbeat.DISK_CRITICAL_BYTES - 1
    heartbeat.check_disk_space(state)

    assert len(telegram_messages) == 2
    assert state["last_alerts"] == {
        "disk_space_warning": 10_000,
        "disk_space_critical": 10_000,
    }


def test_failed_disk_alert_send_does_not_burn_cooldown(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(heartbeat, "_telegram", lambda _message: False)
    monkeypatch.setattr(heartbeat, "_now", lambda: 10_000)
    monkeypatch.setattr(
        heartbeat.shutil, "disk_usage",
        lambda path: _usage(heartbeat.DISK_CRITICAL_BYTES - 1),
    )
    state = {"last_alerts": {}}

    heartbeat.check_disk_space(state)

    assert "disk_space_critical" not in state["last_alerts"]


def test_disk_healthy_is_silent(monkeypatch: pytest.MonkeyPatch):
    emitted = _capture_emit(monkeypatch)
    monkeypatch.setattr(
        heartbeat.shutil, "disk_usage",
        lambda path: _usage(heartbeat.DISK_WARNING_BYTES),
    )

    heartbeat.check_disk_space({"last_alerts": {}})

    assert emitted == []


def test_disk_probe_failure_is_unknown_bounded_error(monkeypatch: pytest.MonkeyPatch):
    emitted = _capture_emit(monkeypatch)

    def fail(_path):
        raise OSError("x" * 1000)

    monkeypatch.setattr(heartbeat.shutil, "disk_usage", fail)
    heartbeat.check_disk_space({"last_alerts": {}})

    assert emitted[0][0] == "disk_space_probe_error"
    assert "DISK SPACE UNKNOWN" in emitted[0][1]
    assert len(emitted[0][1]) < 260


def test_poll_once_wires_disk_probe_without_production_state(
    monkeypatch: pytest.MonkeyPatch,
):
    state = {"last_alerts": {}}
    saved: list[dict] = []
    calls: list[str] = []
    checks = [
        "check_news_watcher",
        "check_telegram_listener",
        "check_stuck_cron_forks",
        "check_session_liveness",
        "check_opportunity_watch",
        "check_memory_pressure",
        "check_disk_space",
        "check_tick_execution",
        "check_operator_session",
    ]
    monkeypatch.setattr(heartbeat, "_load_state", lambda: state)
    monkeypatch.setattr(heartbeat, "_save_state", saved.append)
    for name in checks:
        monkeypatch.setattr(
            heartbeat, name, lambda _state, name=name: calls.append(name)
        )

    heartbeat.poll_once()

    assert calls == checks
    assert saved == [state]
