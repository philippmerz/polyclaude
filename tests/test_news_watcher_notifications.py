"""The RSS watcher retains detections internally and never sends Telegram."""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import news_watcher  # noqa: E402


def _entry(entry_id: str, title: str, summary: str = "A new report.") -> dict:
    return {
        "id": entry_id,
        "title": title,
        "summary": summary,
        "link": f"https://example.invalid/{entry_id}",
    }


def _poll_harness(monkeypatch, tmp_path, feeds, *, now=2_000_000.0):
    """Provide feed, state, clock, alert-log, and cron fakes; no I/O escapes."""
    by_url = {url: entries for url, entries in feeds.items()}
    monkeypatch.setattr(
        news_watcher.feedparser,
        "parse",
        lambda url: SimpleNamespace(entries=by_url[url]),
    )
    monkeypatch.setattr(news_watcher.time, "time", lambda: now)
    alerts = []
    saved_states = []
    cron_ticks = []
    monkeypatch.setattr(news_watcher, "_append_news_alert", lambda r: alerts.append(copy.deepcopy(r)))
    monkeypatch.setattr(news_watcher, "save_state", lambda s: saved_states.append(copy.deepcopy(s)))
    monkeypatch.setattr(news_watcher, "fire_cron_tick", lambda: cron_ticks.append(True))
    monkeypatch.setattr(
        news_watcher.httpx,
        "post",
        lambda *_a, **_kw: pytest.fail("RSS detections must never make HTTP POSTs"),
    )
    monkeypatch.setattr(
        news_watcher.subprocess,
        "run",
        lambda *_a, **_kw: pytest.fail("poll_once must not spawn a Telegram sender"),
    )
    # A stale journal timestamp lets the test observe the existing cron wakeup gate.
    script_dir = tmp_path / "scripts"
    journal = tmp_path / "notes" / "journal.md"
    journal.parent.mkdir(parents=True)
    journal.write_text("old check-in\n")
    os.utime(journal, (now - 7200, now - 7200))
    monkeypatch.setattr(news_watcher, "_SCRIPT_DIR", script_dir)
    return alerts, saved_states, cron_ticks


def _config(feed_names, *, tier1=None, tier2=None, cooldown=1800):
    return {
        "feeds": [{"name": name, "url": url} for name, url in feed_names],
        "tier1_keywords": tier1 or [],
        "tier2_keywords": tier2 or [],
        "alert_cooldown_seconds": cooldown,
        "max_entries_per_feed": 30,
    }


def test_tier1_arbitrary_keywords_persist_once_and_wake_one_checkin(monkeypatch, tmp_path):
    feeds = {
        "https://feed.invalid/a": [
            _entry("one", "Unheld nuclear test reported"),
            _entry("two", "Treaty signed by the parties"),
        ],
        "https://feed.invalid/b": [
            _entry("syndicated", "  unheld nuclear test REPORTED "),
        ],
    }
    alerts, saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    state = {"seen_ids": [], "last_alerts": {}, "last_cron_trigger": 0, "seen_titles": {}}
    config = _config(
        [("A", "https://feed.invalid/a"), ("B", "https://feed.invalid/b")],
        tier1=["nuclear test", "treaty signed"],
    )

    assert news_watcher.poll_once(config, state) == 2

    assert [r["title"] for r in alerts] == [
        "Unheld nuclear test reported",
        "Treaty signed by the parties",
    ]
    assert [r["tier"] for r in alerts] == [1, 1]
    assert [r["matched"] for r in alerts] == ["nuclear test", "treaty signed"]
    assert len(cron) == 1
    assert state["last_alerts"] == {"t1:nuclear test": 2_000_000.0, "t1:treaty signed": 2_000_000.0}
    assert set(state["seen_ids"]) == {
        news_watcher.entry_id(e)
        for entries in feeds.values()
        for e in entries
    }
    assert len(state["seen_titles"]) == 2
    assert set(saved[-1]) >= {"seen_ids", "last_alerts", "last_cron_trigger", "seen_titles"}
    assert not hasattr(news_watcher, "telegram_send")
    assert not hasattr(news_watcher, "TELEGRAM_TOKEN_PATH")
    assert not hasattr(news_watcher, "TELEGRAM_STATE_PATH")

    # Existing ID/title dedup and the per-keyword detection cooldown still hold.
    feeds["https://feed.invalid/a"] = [
        feeds["https://feed.invalid/a"][0],
        _entry("three", "A different nuclear test report"),
    ]
    feeds["https://feed.invalid/b"] = [_entry("four", "Unheld nuclear test reported")]
    assert news_watcher.poll_once(config, state) == 0
    assert len(alerts) == 2
    assert len(cron) == 1
    assert "t1:nuclear test" in state["last_alerts"]


def test_tier2_failed_inventory_filter_is_retained_internally(monkeypatch, tmp_path):
    feeds = {"https://feed.invalid/tier2": [_entry("t2-1", "Taylor Swift announces an album") ]}
    alerts, _saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    now = 2_000_000.0
    monkeypatch.setattr(news_watcher, "_POSITIONS_CACHE", {
        "text": "position lookup unavailable", "ts": now, "polymarket_available": False,
    })
    monkeypatch.setattr(
        news_watcher,
        "run_agent",
        lambda *_a, **_kw: pytest.fail("failed inventory must fail open before an agent call"),
    )
    state = {"seen_ids": [], "last_alerts": {}, "last_cron_trigger": 0, "seen_titles": {}}
    config = _config([("RSS", "https://feed.invalid/tier2")], tier2=["Taylor Swift"])

    assert news_watcher.poll_once(config, state) == 1

    assert len(alerts) == 1
    assert alerts[0]["tier"] == 2
    assert "inventory unavailable" in alerts[0]["agent_reason"]
    assert alerts[0]["impacts"] == []
    assert state["last_alerts"]["t2:Taylor Swift"] == now
    assert cron == []


def test_tier2_critical_impact_is_retained_for_internal_review(monkeypatch, tmp_path):
    feeds = {"https://feed.invalid/critical": [_entry("critical-1", "Taylor Swift announces an album") ]}
    alerts, _saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    critical = {"position": "swift-album", "level": "CRITICAL", "reason": "resolution event"}
    monkeypatch.setattr(
        news_watcher,
        "_agent_filter_tier2",
        lambda *_a, **_kw: (True, "SEND: retain for review", [critical]),
    )
    state = {"seen_ids": [], "last_alerts": {}, "last_cron_trigger": 0, "seen_titles": {}}
    config = _config([("RSS", "https://feed.invalid/critical")], tier2=["Taylor Swift"])

    assert news_watcher.poll_once(config, state) == 1

    assert alerts[0]["impacts"] == [critical]
    assert alerts[0]["agent_reason"] == "SEND: retain for review"
    assert state["last_alerts"]["t2:Taylor Swift"] == 2_000_000.0
    assert cron == []


def test_tier2_suppression_advances_detection_cooldown_without_persisting(monkeypatch, tmp_path):
    feeds = {"https://feed.invalid/suppressed": [_entry("suppressed-1", "Taylor Swift album rumor") ]}
    alerts, _saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    calls = []
    monkeypatch.setattr(
        news_watcher,
        "_agent_filter_tier2",
        lambda *_a, **_kw: (calls.append(True) or (False, "SUPPRESS: recycled rumor", [])),
    )
    state = {"seen_ids": [], "last_alerts": {}, "last_cron_trigger": 0, "seen_titles": {}}
    config = _config([("RSS", "https://feed.invalid/suppressed")], tier2=["Taylor Swift"])

    assert news_watcher.poll_once(config, state) == 0
    assert state["last_alerts"]["t2:Taylor Swift"] == 2_000_000.0
    assert alerts == []
    # A different headline matching the same keyword is held by the detection cooldown.
    feeds["https://feed.invalid/suppressed"] = [_entry("suppressed-2", "Taylor Swift album update")]
    assert news_watcher.poll_once(config, state) == 0
    assert calls == [True]
    assert alerts == [] and cron == []
