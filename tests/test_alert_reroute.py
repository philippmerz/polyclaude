"""Outbound Telegram is disabled: every send becomes a wake_webhook alert."""
import importlib
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import wake_webhook as ww  # noqa: E402


@pytest.fixture
def box(tmp_path, monkeypatch):
    for k in list(__import__("os").environ):
        if k.startswith("POLYCLAUDE_WAKE") or k == "POLYCLAUDE_TELEGRAM_OUTBOUND":
            monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(ww, "REPO", tmp_path)
    for name in ("POLYCLAUDE_TELEGRAM_TOKEN", "POLYCLAUDE_TELEGRAM_STATE"):
        monkeypatch.setenv(name, str(tmp_path / "nonexistent" / name))

    def _no_network(*_a, **_kw):
        raise AssertionError("Telegram network call attempted")

    import httpx
    monkeypatch.setattr(httpx, "Client", _no_network)
    monkeypatch.setattr(httpx, "post", _no_network)
    monkeypatch.setattr(httpx, "get", _no_network)
    return tmp_path


def _alerts(repo):
    p = repo / "logs" / "wake_outbox.jsonl"
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
    return sorted((r for r in ww.state_of(rows).values() if r.get("kind") == "alert"),
                  key=lambda r: r["ts"])


def _at(monkeypatch, hhmm):
    monkeypatch.setenv("POLYCLAUDE_WAKE_NOW", f"2026-11-02T{hhmm}:00+00:00")


def test_telegram_msg_routes_to_wake_never_network(box, monkeypatch, capsys):
    telegram = importlib.import_module("telegram")
    monkeypatch.setenv("POLYCLAUDE_WAKE_SOURCE", "heartbeat_watch")
    monkeypatch.setattr(sys, "argv", ["telegram.py", "msg",
                        "news_watcher state file unchanged for 62 min (threshold 30); poll loop may be stuck"])
    assert telegram.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["routed"] == "wake_webhook" and out["status"] == "pending"
    (a,) = _alerts(box)
    assert a["source"] == "heartbeat_watch" and a["severity"] == "warning"
    monkeypatch.setattr(sys, "argv", ["telegram.py", "file", str(box), "-c", "report"])
    assert telegram.main() == 0
    assert len(_alerts(box)) == 2


def test_listener_sender_note_routes_to_wake(box):
    listener = importlib.import_module("telegram_listener")
    assert listener._notify_sender("tok", 1, "⚠ Your message is safely queued locally") is True
    (a,) = _alerts(box)
    assert a["source"] == "telegram_listener" and a["severity"] == "warning"


def test_health_kind_capped_once_per_hour(box, monkeypatch):
    for hhmm, mins in (("20:00", 62), ("20:30", 92), ("21:01", 123)):
        _at(monkeypatch, hhmm)
        ww.record_alert(f"news_watcher state file unchanged for {mins} min (threshold 30)",
                        source="heartbeat_watch")
    assert [a["status"] for a in _alerts(box)] == ["pending", "duplicate", "pending"]


def test_non_health_alert_dedupe_30min_and_severity(box, monkeypatch):
    msg = "[OPPWATCH] trigger hit gpt6-trim-at-fair slug=gpt-6-release at 0.41"
    for hhmm in ("10:00", "10:20", "10:31"):
        _at(monkeypatch, hhmm)
        ww.record_alert(msg, source="opportunity_watch")
    rows = _alerts(box)
    assert [a["status"] for a in rows] == ["pending", "duplicate", "pending"]
    assert rows[0]["severity"] == "info" and rows[0]["market_slug"] == "gpt-6-release"
    _at(monkeypatch, "11:30")
    ww.record_alert("[resting_watch] ESCALATION: 3 consecutive cycle errors", source="resting_watch")
    assert _alerts(box)[-1]["severity"] == "critical"


def test_daily_cap_critical_bypass_and_wakes_unaffected(box, monkeypatch):
    for i in range(14):
        _at(monkeypatch, f"12:{i:02d}")
        ww.record_alert(f"source change {chr(97 + i)} detected", source="source_watch")
    _at(monkeypatch, "12:30")
    ww.record_alert("EMERGENCY exit triggered", source="emergency_exit_polymarket")
    st = [a["status"] for a in _alerts(box)]
    assert st.count("pending") == 13 and st.count("rate_limited_daily") == 2
    assert _alerts(box)[-1]["status"] == "pending"
    # alerts must not consume the wake budget
    cfg = ww.load_config(box)
    row = {"kind": "wake", "source": "news_watcher", "dedupe_key": "x", "market_slug": None}
    rows = [json.loads(l) for l in (box / "logs" / "wake_outbox.jsonl").read_text().splitlines()]
    assert ww.admit(row, rows, cfg, ww._now()) == "pending"


def test_alert_payload_carries_kind_and_severity():
    row = {"id": "a", "source": "heartbeat_watch", "severity": "warning", "market_slug": None,
           "headline": "x", "ts": "t", "kind": "alert"}
    assert ww._payload(row) == {**row}
