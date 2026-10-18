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
_REAL_FILTER = news_watcher._agent_filter_tier2


def _entry(entry_id: str, title: str, summary: str = "A new report.") -> dict:
    return {
        "id": entry_id,
        "title": title,
        "summary": summary,
        "link": f"https://example.invalid/{entry_id}",
    }


def _poll_harness(monkeypatch, tmp_path, feeds, *, now=2_000_000.0):
    """Provide feed, state, clock, alert-log, and cron fakes; no I/O escapes."""
    by_url = feeds  # Follow replacements between simulated polling cycles.
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
    monkeypatch.setattr(news_watcher, "fire_cron_tick", lambda reason="": (
        cron_ticks.append(True) or {"status": "queued", "reason": "test", "tick_id": "test"}
    ))
    monkeypatch.setattr(news_watcher, "_agent_filter_tier2",
                        lambda *_a, **_kw: (True, "SEND: no exposure impact", []))
    monkeypatch.setattr(news_watcher, "_POSITIONS_CACHE", {
        "text": "empty but verified", "ts": now, "polymarket_available": True,
        "exposures": [], "ostium_available": True, "ostium_open_trades": 0,
    })
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
    monkeypatch.setattr(news_watcher, "_REPO_ROOT", tmp_path)
    return alerts, saved_states, cron_ticks


def _config(feed_names, *, tier1=None, tier2=None, cooldown=1800):
    return {
        "feeds": [{"name": name, "url": url} for name, url in feed_names],
        "tier1_keywords": tier1 or [],
        "tier2_keywords": tier2 or [],
        "alert_cooldown_seconds": cooldown,
        "max_entries_per_feed": 30,
    }


def test_tier1_research_persists_deduplicates_and_does_not_wake(monkeypatch, tmp_path):
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
    assert [r["relevance"] for r in alerts] == ["research_only", "research_only"]
    assert [r["review_required"] for r in alerts] == [False, False]
    assert len(cron) == 0
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
    assert len(cron) == 0
    assert "t1:nuclear test" in state["last_alerts"]


def test_tier2_failed_inventory_filter_is_retained_internally(monkeypatch, tmp_path):
    feeds = {"https://feed.invalid/tier2": [_entry("t2-1", "Taylor Swift announces an album") ]}
    alerts, _saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    now = 2_000_000.0
    monkeypatch.setattr(news_watcher, "_POSITIONS_CACHE", {
        "text": "position lookup unavailable", "ts": now, "polymarket_available": False,
    })
    monkeypatch.setattr(news_watcher, "_agent_filter_tier2", _REAL_FILTER)
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
    assert alerts[0]["relevance"] == "unknown"
    assert alerts[0]["review_required"] is True
    assert state["last_alerts"]["t2:Taylor Swift"] == now
    assert len(cron) == 1


def test_tier2_critical_impact_is_retained_for_internal_review(monkeypatch, tmp_path):
    feeds = {"https://feed.invalid/critical": [_entry("critical-1", "Taylor Swift announces an album") ]}
    alerts, _saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    cid = "0x" + "1" * 64
    monkeypatch.setitem(news_watcher._POSITIONS_CACHE, "exposures", [
        {"condition_id": cid, "kind": "held", "title": "Taylor Swift"},
    ])
    critical = {"position": cid, "level": "CRITICAL", "reason": "resolution event"}
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
    assert alerts[0]["relevance"] == "portfolio_material_critical"
    assert alerts[0]["review_required"] is True
    assert state["last_alerts"]["t2:Taylor Swift"] == 2_000_000.0
    assert len(cron) == 1


def test_tier1_current_pending_buy_material_impact_qualifies_review(monkeypatch, tmp_path):
    feeds = {"https://feed.invalid/buy": [_entry("buy-impact", "Treaty signed by the parties")]}
    alerts, _saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    cid = "0x" + "2" * 64
    monkeypatch.setitem(news_watcher._POSITIONS_CACHE, "exposures", [
        {"condition_id": cid, "kind": "pending_buy", "title": "Treaty outcome"},
    ])
    impact = {"position": cid, "level": "MATERIAL", "reason": "changes pending market thesis"}
    monkeypatch.setattr(news_watcher, "_agent_filter_tier2", lambda *_a, **_kw: (
        True, "SEND: pending buy is directly affected", [impact]
    ))
    state = {"seen_ids": [], "last_alerts": {}, "last_cron_trigger": 0, "seen_titles": {}}
    config = _config([("RSS", "https://feed.invalid/buy")], tier1=["treaty signed"])
    assert news_watcher.poll_once(config, state) == 1
    assert alerts[0]["relevance"] == "portfolio_material_critical"
    assert alerts[0]["review_required"] is True
    assert cron == [True]


def test_infrastructure_safety_unknown_is_retained_for_review(monkeypatch, tmp_path):
    feeds = {"https://feed.invalid/safety": [_entry("hack", "Ostium exploit reported")]}
    alerts, _saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    monkeypatch.setattr(news_watcher, "_POSITIONS_CACHE", {
        "text": "inventory unavailable", "ts": 2_000_000.0,
        "polymarket_available": False, "exposures": [],
        "ostium_available": False, "ostium_open_trades": 0,
    })
    monkeypatch.setattr(news_watcher, "_agent_filter_tier2", _REAL_FILTER)
    state = {"seen_ids": [], "last_alerts": {}, "last_cron_trigger": 0, "seen_titles": {}}
    config = _config([("RSS", "https://feed.invalid/safety")], tier1=["ostium exploit"])
    assert news_watcher.poll_once(config, state) == 1
    assert alerts[0]["relevance"] == "safety_unknown"
    assert alerts[0]["impacts"] == []
    assert alerts[0]["review_required"] is True
    assert cron == [True]


def test_unsupported_impact_key_cannot_claim_portfolio_relevance(monkeypatch, tmp_path):
    feeds = {"https://feed.invalid/id": [_entry("invented", "Unheld nuclear test reported")]}
    alerts, _saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    monkeypatch.setattr(news_watcher, "_agent_filter_tier2", lambda *_a, **_kw: (
        True, "SEND: UNKNOWN relevance: unsupported impact key discarded", []
    ))
    state = {"seen_ids": [], "last_alerts": {}, "last_cron_trigger": 0, "seen_titles": {}}
    config = _config([("RSS", "https://feed.invalid/id")], tier1=["nuclear test"])
    assert news_watcher.poll_once(config, state) == 1
    assert alerts[0]["relevance"] == "unknown"
    assert alerts[0]["review_required"] is True
    assert not any(i["level"] in ("MATERIAL", "CRITICAL") for i in alerts[0]["impacts"])
    assert cron == [True]


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
    # A new headline is classified before the routine cooldown can suppress it.
    feeds["https://feed.invalid/suppressed"] = [_entry("suppressed-2", "Taylor Swift album update")]
    assert news_watcher.poll_once(config, state) == 0
    assert calls == [True, True]
    assert alerts == [] and cron == []


def test_routine_headline_cannot_mask_later_critical_same_keyword(monkeypatch, tmp_path):
    feeds = {"https://feed.invalid/update": [_entry("routine", "Taylor Swift album rumor")]}
    alerts, _saved, cron = _poll_harness(monkeypatch, tmp_path, feeds)
    cid = "0x" + "2" * 64
    verdicts = iter([
        (False, "SUPPRESS: routine rumor", []),
        (True, "SEND: source confirms event", [
            {"position": cid, "level": "CRITICAL", "reason": "resolving event"}]),
    ])
    monkeypatch.setattr(news_watcher, "_agent_filter_tier2", lambda *_a, **_kw: next(verdicts))
    state = {}
    config = _config([("RSS", "https://feed.invalid/update")], tier2=["Taylor Swift"])
    assert news_watcher.poll_once(config, state) == 0
    feeds["https://feed.invalid/update"] = [_entry("confirmed", "Taylor Swift album released")]
    assert news_watcher.poll_once(config, state) == 1
    assert alerts[0]["review_required"] is True
    assert cron == [True]
