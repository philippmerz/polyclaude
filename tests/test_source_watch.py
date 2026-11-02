"""source_watch: diff/classify rules, fail-closed baselines, paper vs live
outputs, and the resting_watch auto-pull contract. No network (MockTransport)."""

from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("source_watch", REPO / "scripts" / "source_watch.py")
sw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sw)
_rspec = importlib.util.spec_from_file_location("resting_watch", REPO / "scripts" / "resting_watch.py")
rw = importlib.util.module_from_spec(_rspec)
_rspec.loader.exec_module(rw)

CID = "0x99ac08ed7765e5b35836b9e68bd90a7d6ad89417a8444d90bac61febcb8a8d41"


def _model(name, hle, cal=10.0):
    return {"name": name, "id": name.lower().replace(" ", "-"),
            "scores": {"hle": hle, "hle_calibration_error": None if hle is None else cal}}


BASE = [_model("Gemini 3.1 Pro", 45.9), _model("Kimi K3.1 Pro", 46.44)]


def _cfg(mode="paper"):
    return {"master": True, "mode": mode, "telegram": False, "min_alert_level": "MATERIAL",
            "sources": [{
                "id": "hle", "kind": "hle_chart_api", "url": "https://dashboard.safe.ai/api/models",
                "alert_keys": ["kimi", "hle"],
                "rules": [{"name_regex": "kimi|moonshot", "score_gte": 55.0, "level": "CRITICAL"},
                          {"name_regex": "kimi|moonshot", "level": "MATERIAL"}],
                "positions": [{"slug": "kimi55", "condition_id": CID, "token_id": "123"}]}]}


class Feed:
    def __init__(self, payload, status=200):
        self.payload, self.status = payload, status

    def handler(self, request):
        if "midpoint" in str(request.url):
            return httpx.Response(200, json={"mid": "0.42"})
        if self.status != 200:
            return httpx.Response(self.status, json={"error": "Forbidden"})
        return httpx.Response(200, json=self.payload)


@pytest.fixture
def paths(tmp_path, monkeypatch):
    for name in ("ALERTS_PATH", "HISTORY_PATH", "PAPER_PATH", "STATE_PATH", "LOG_PATH"):
        monkeypatch.setattr(sw, name, tmp_path / name.lower())
    sent = []
    monkeypatch.setattr(sw, "telegram", lambda text: sent.append(text))
    return tmp_path, sent


def _run(cfg, state, feed):
    with httpx.Client(transport=httpx.MockTransport(feed.handler)) as c:
        return sw.run_cycle(cfg, state, c, now=dt.datetime(2026, 11, 2, 12, tzinfo=dt.timezone.utc))


def _lines(p):
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def test_shipped_config_is_valid_and_safe():
    cfg = json.loads((REPO / "notes" / "source_watch_config.json").read_text())
    assert sw.validate_config(cfg) == []
    assert cfg["master"] is False and cfg["mode"] == "paper" and cfg["telegram"] is False


def test_first_fetch_only_baselines(paths):
    tmp, _ = paths
    state = {}
    out = _run(_cfg("live"), state, Feed(BASE))
    assert "baseline established" in out[0]
    assert not (tmp / "alerts_path").exists()


def test_unchanged_source_is_silent(paths):
    state = {}
    _run(_cfg("live"), state, Feed(BASE))
    assert _run(_cfg("live"), state, Feed(copy.deepcopy(BASE))) == ["hle: unchanged"]


def test_kimi_crossing_55_is_critical_and_live_row_triggers_resting_pull(paths, monkeypatch):
    tmp, _ = paths
    state = {}
    _run(_cfg("live"), state, Feed(BASE))
    _run(_cfg("live"), state, Feed([BASE[0], _model("Kimi K3.1 Pro", 56.2)]))
    rows = _lines(tmp / "alerts_path")
    assert len(rows) == 1 and rows[0]["impacts"][0]["level"] == "CRITICAL"
    # Contract with resting_watch.recent_pull_alerts: CRITICAL + identity + key.
    monkeypatch.setattr(rw, "ALERTS_PATH", tmp / "alerts_path")
    since = dt.datetime(2026, 11, 2, tzinfo=dt.timezone.utc)
    assert len(rw.recent_pull_alerts(["kimi", "moonshot", "hle"], CID, since)) == 1
    hist = _lines(tmp / "history_path")
    assert hist[0]["midpoints"] == {"kimi55": 0.42}


def test_new_kimi_row_below_bar_is_material_not_critical(paths):
    tmp, _ = paths
    state = {}
    _run(_cfg("live"), state, Feed(BASE))
    _run(_cfg("live"), state, Feed(BASE + [_model("Kimi K4", 50.0)]))
    rows = _lines(tmp / "alerts_path")
    assert rows[0]["impacts"][0]["level"] == "MATERIAL"


def test_already_above_bar_does_not_refire_critical(paths):
    tmp, _ = paths
    state = {}
    _run(_cfg("live"), state, Feed([_model("Kimi K5", 57.0)]))
    _run(_cfg("live"), state, Feed([_model("Kimi K5", 57.5)]))
    assert _lines(tmp / "alerts_path")[0]["impacts"][0]["level"] == "MATERIAL"


def test_unrelated_change_is_minor_and_not_alerted(paths):
    tmp, _ = paths
    state = {}
    _run(_cfg("live"), state, Feed(BASE))
    out = _run(_cfg("live"), state, Feed([_model("Gemini 3.1 Pro", 47.0), BASE[1]]))
    assert any("CHANGE MINOR" in o for o in out)
    assert not (tmp / "alerts_path").exists()
    assert len(_lines(tmp / "history_path")) == 1  # still recorded for the lag dataset


def test_paper_mode_never_writes_news_alerts_or_telegram(paths):
    tmp, sent = paths
    cfg = _cfg("paper")
    cfg["telegram"] = True
    state = {}
    _run(cfg, state, Feed(BASE))
    _run(cfg, state, Feed([BASE[0], _model("Kimi K3.1 Pro", 60.0)]))
    assert not (tmp / "alerts_path").exists() and sent == []
    assert _lines(tmp / "paper_path")[0]["paper"] is True


def test_fetch_failure_keeps_baseline(paths):
    state = {}
    _run(_cfg("live"), state, Feed(BASE))
    h = state["sources"]["hle"]["baseline"]["hash"]
    out = _run(_cfg("live"), state, Feed(None, status=403))
    assert "FAILED" in out[0]
    assert state["sources"]["hle"]["baseline"]["hash"] == h
    assert state["sources"]["hle"]["consecutive_errors"] == 1


def test_malformed_payload_fails_closed(paths):
    state = {}
    _run(_cfg("live"), state, Feed(BASE))
    out = _run(_cfg("live"), state, Feed([]))
    assert "FAILED" in out[0]


def test_validate_config_rejects_bad_values():
    bad = _cfg()
    bad["mode"] = "trade"
    bad["sources"][0]["rules"][0]["level"] = "HUGE"
    bad["sources"][0]["positions"][0]["condition_id"] = "abc"
    problems = sw.validate_config(bad)
    assert len(problems) == 3


def test_http_text_extract_and_change(paths):
    html1 = "<html><body><div id=r>" + "row " * 80 + "</div><script>x=1</script></body></html>"
    html2 = html1.replace("<script>x=1</script>", "<script>x=2</script>")  # script-only change
    html3 = html1.replace("row row", "row ROW", 1)
    cfg = {"master": True, "mode": "live", "sources": [{
        "id": "page", "kind": "http_text", "url": "https://example.org/",
        "change_level": "MATERIAL", "positions": []}]}
    pages = iter([html1, html2, html3])

    def handler(request):
        return httpx.Response(200, text=next(pages))
    state = {}
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        sw.run_cycle(cfg, state, c)
        assert sw.run_cycle(cfg, state, c) == ["page: unchanged"]
        assert "CHANGE MATERIAL" in sw.run_cycle(cfg, state, c)[0]
