"""Focused tests for source_watch dense mid-logging (no network)."""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "source_watch", REPO / "scripts" / "source_watch.py")
sw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sw)


class _FakeClient:
    pass


def _cfg(**over):
    base = {
        "master": True, "mode": "live", "mid_log": True,
        "poll_seconds": 600, "dense_minutes": 45, "dense_poll_seconds": 90,
        "sources": [{
            "id": "test_src", "kind": "http_text", "enabled": True,
            "url": "https://example.invalid/x",
            "positions": [{"slug": "s", "token_id": "1",
                           "condition_id": "0xabc"}],
        }],
    }
    base.update(over)
    return base


def _state():
    return {"sources": {"test_src": {"baseline": {"hash": "a"}, "last_ok": "x"}}}


def _fake_mids(client, src):
    return {"s": 0.42}


def test_baseline_cycle_appends_baseline_mids_row(tmp_path, monkeypatch):
    monkeypatch.setattr(sw, "MIDS_PATH", tmp_path / "mids.jsonl")
    monkeypatch.setattr(sw, "fetch_inventory", lambda c, s: {"hash": "a"})
    monkeypatch.setattr(sw, "midpoints", _fake_mids)
    cfg, state = _cfg(), _state()
    sw.run_cycle(cfg, state, _FakeClient(), now=dt.datetime(2026, 11, 2, tzinfo=dt.timezone.utc))
    rows = [json.loads(l) for l in (tmp_path / "mids.jsonl").read_text().splitlines()]
    assert rows[-1]["kind"] == "baseline" and rows[-1]["midpoints"] == {"s": 0.42}


def test_change_cycle_sets_dense_window_and_logs_change_row(tmp_path, monkeypatch):
    monkeypatch.setattr(sw, "MIDS_PATH", tmp_path / "mids.jsonl")
    monkeypatch.setattr(sw, "HISTORY_PATH", tmp_path / "hist.jsonl")
    monkeypatch.setattr(sw, "ALERTS_PATH", tmp_path / "alerts.jsonl")
    monkeypatch.setattr(sw, "fetch_inventory", lambda c, s: {"hash": "b", "rows": [{"name": "Kimi K9", "score": 57.0}]})
    monkeypatch.setattr(sw, "midpoints", _fake_mids)
    src = _cfg()["sources"][0]
    src["rules"] = [{"name_regex": "kimi", "score_gte": 55.0, "level": "CRITICAL", "why": "w"}]
    cfg = _cfg(sources=[src])
    state = _state()
    now = dt.datetime(2026, 11, 2, 12, 0, tzinfo=dt.timezone.utc)
    sw.run_cycle(cfg, state, _FakeClient(), now=now)
    st = state["sources"]["test_src"]
    until = dt.datetime.fromisoformat(st["dense_until"])
    assert dt.timedelta(minutes=40) < (until - now) <= dt.timedelta(minutes=50)
    rows = [json.loads(l) for l in (tmp_path / "mids.jsonl").read_text().splitlines()]
    assert any(r["kind"] == "change" for r in rows)
    assert sw.dense_active(state, now + dt.timedelta(minutes=10))
    assert not sw.dense_active(state, now + dt.timedelta(minutes=60))
