"""Review qualification, queue acknowledgment and consumption are distinct facts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import news_watcher as watcher  # noqa: E402


def _alert(key="one", *, critical=False):
    return {"alert_id": key, "title": "A source event", "critical": critical,
            "relevance": "portfolio_material_critical"}


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(watcher, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(watcher, "save_state", lambda _state: None)
    return tmp_path


def test_recent_journal_is_not_ack_and_queued_is_not_completed(monkeypatch, isolated):
    journal = isolated / "notes" / "journal.md"
    journal.parent.mkdir()
    journal.write_text("Unrelated work just finished")
    calls = []
    monkeypatch.setattr(watcher, "fire_cron_tick", lambda reason: calls.append(reason) or {
        "status": "queued", "why": "operator_queue_accepted", "tick_id": "tick"})
    state = {}
    watcher._dispatch_pending_reviews(state, [_alert()], 10_000)
    assert len(calls) == 1 and "one" in calls[0]
    assert "predate the latest journal" in calls[0]
    assert state["last_cron_trigger"] == 10_000
    assert state["pending_review_alerts"] == []
    record = json.loads((isolated / "logs" / "news_dispatch.jsonl").read_text())
    assert record["status"] == "queued" and record["alert_ids"] == ["one"]
    assert "completed" not in record and "running" not in record


def test_deferred_alert_survives_and_retries_without_new_headline(monkeypatch, isolated):
    state = {"last_cron_trigger": 10_000}
    calls = []
    monkeypatch.setattr(watcher, "fire_cron_tick", lambda reason: calls.append(reason) or {
        "status": "queued", "why": "operator_queue_accepted"})
    watcher._dispatch_pending_reviews(state, [_alert()], 10_001)
    assert calls == [] and state["pending_review_alerts"] == [_alert()]
    assert state["last_review_dispatch"]["status"] == "deferred"
    assert state["last_cron_trigger"] == 10_000
    watcher._dispatch_pending_reviews(state, [], 15_401)
    assert len(calls) == 1 and state["pending_review_alerts"] == []
    assert state["last_review_dispatch"]["alert_ids"] == ["one"]


@pytest.mark.parametrize("status", ["failed", "deferred"])
def test_driver_failure_or_lock_deferral_never_claims_queued(monkeypatch, isolated, status):
    monkeypatch.setattr(watcher, "fire_cron_tick", lambda _reason: {
        "status": status, "why": "operator_queue_failed" if status == "failed" else "checkin_lock_held"})
    state = {}
    watcher._dispatch_pending_reviews(state, [_alert()], 10_000)
    assert state["pending_review_alerts"] == [_alert()]
    assert state.get("last_cron_trigger", 0) == 0
    assert state["last_review_dispatch"]["status"] == status


def test_critical_lead_bypasses_generic_cooldown(monkeypatch, isolated):
    calls = []
    monkeypatch.setattr(watcher, "fire_cron_tick", lambda reason: calls.append(reason) or {
        "status": "queued", "why": "operator_queue_accepted"})
    state = {"last_cron_trigger": 10_000, "last_cron_request": 10_000}
    watcher._dispatch_pending_reviews(state, [_alert(critical=True)], 10_001)
    assert len(calls) == 1
    assert state["last_cron_trigger"] == 10_001


def test_late_ack_covers_only_original_ids_without_blind_resend(monkeypatch, isolated):
    receipt = isolated / "logs" / "cron" / "news_dispatch_test.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("")
    monkeypatch.setattr(watcher, "fire_cron_tick", lambda _reason: pytest.fail("duplicate request"))
    state = {"pending_review_alerts": [_alert()], "last_review_dispatch": {
        "status": "unconfirmed", "why": "no_dispatch_acknowledgment",
        "receipt_path": "logs/cron/news_dispatch_test.json", "alert_ids": ["one"]}}
    watcher._dispatch_pending_reviews(state, [_alert("two")], 10_000)
    assert len(state["pending_review_alerts"]) == 2
    assert state["last_review_dispatch"]["status"] == "unconfirmed"
    receipt.write_text(json.dumps({"status": "queued", "why": "operator_queue_accepted",
                                  "tick_id": "tick", "returncode": 0}))
    watcher._dispatch_pending_reviews(state, [], 10_001)
    assert state["pending_review_alerts"] == [_alert("two")]
    assert state["last_review_dispatch"]["alert_ids"] == ["one"]


@pytest.mark.parametrize("status", ["queued", "deferred", "failed", "fallback_starting"])
def test_driver_receipt_controls_reported_status(monkeypatch, isolated, status):
    calls = []

    def child(argv, **kwargs):
        calls.append(argv)
        Path(kwargs["env"]["POLYCLAUDE_DISPATCH_RECEIPT"]).write_text(json.dumps({
            "status": status, "why": "proved boundary", "tick_id": "tick", "returncode": 0}))
        return SimpleNamespace(poll=lambda: 0)

    monkeypatch.setattr(watcher.subprocess, "Popen", child)
    result = watcher.fire_cron_tick("NEWS REVIEW REQUEST: one")
    assert result["status"] == status
    assert calls[0][-1] == "NEWS REVIEW REQUEST: one"
    assert "completed" not in result


def test_missing_ack_is_unconfirmed_not_spawned_or_queued(monkeypatch, isolated):
    monkeypatch.setattr(watcher.subprocess, "Popen", lambda *_a, **_kw: SimpleNamespace(poll=lambda: 0))
    result = watcher.fire_cron_tick("NEWS REVIEW REQUEST: one")
    assert result["status"] == "unconfirmed"
    assert result["why"] == "no_dispatch_acknowledgment"
