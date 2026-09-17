import importlib.util
import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("jev_shadow", SCRIPTS / "jev_shadow.py")
jev = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(jev)


def test_request_bounds_and_question_shape():
    state = {"market": "x"}
    questions = {"q1": {"type": "noul", "instructions": "What changed?", "criteria": {"true": "Changed.", "false": "Unchanged."}}}
    assert jev.validate_request(questions, state)["q1"]["type"] == "noul"
    with pytest.raises(jev.InputError, match="type, instructions, criteria"):
        jev.validate_request({"q1": {"question": ""}}, state)
    with pytest.raises(jev.InputError, match="1 to"):
        jev.validate_request({}, state)


def test_exact_wire_shape_and_raw_env_auth(monkeypatch):
    monkeypatch.setenv("POLYCLAUDE_JEV_API_KEY", "test-value-not-a-real-secret")
    state = {"public_fact": "example"}
    questions = {"route": {"type": "noul", "instructions": "Classify.", "criteria": {"true": "Yes.", "false": "No."}}}
    assert jev.build_payload(state, questions, jev.MODEL) == {
        "model": "jev-1.13.0", "state": state, "questions": questions,
    }
    assert jev._headers()["Authorization"].startswith("Bearer ")


def test_state_hash_is_stable_and_does_not_expose_state():
    digest = jev.state_hash({"b": 2, "a": 1})
    assert digest == jev.state_hash({"a": 1, "b": 2})
    assert digest != jev.state_hash({"a": 2, "b": 2})
    assert len(digest) == 64


def test_append_usage_redacts_non_metering_data(tmp_path, monkeypatch):
    usage_path = tmp_path / "jev_usage.jsonl"
    monkeypatch.setattr(jev, "USAGE_LOG", usage_path)
    jev.append_usage({
        "ts": "2026-09-17T00:00:00Z", "provider": "jev", "model": "jev-1.13.0",
        "input_tokens": 10, "output_tokens": 5, "latency_ms": 12,
        "estimated_cost_usd": 0.01, "status": "ok", "state_hash": "a" * 64,
        "state": {"private": "must-not-log"}, "response": "must-not-log",
    })
    stored = json.loads(usage_path.read_text())
    assert stored["state_hash"] == "a" * 64
    assert "state" not in stored and "response" not in stored
    assert stat.S_IMODE(usage_path.stat().st_mode) == 0o600


def test_repeat_cap_counts_only_recent_matching_hash(tmp_path, monkeypatch):
    usage_path = tmp_path / "jev_usage.jsonl"
    monkeypatch.setattr(jev, "USAGE_LOG", usage_path)
    now = datetime(2026, 9, 17, tzinfo=timezone.utc)
    rows = [{"ts": "2026-09-16T23:00:00Z", "state_hash": "x"} for _ in range(3)]
    usage_path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(jev.InputError, match="repeat cap"):
        jev.check_repeat_limit("x", now)
    jev.check_repeat_limit("y", now)


def test_monthly_cap_reserves_worst_allowed_request(tmp_path, monkeypatch):
    usage_path = tmp_path / "jev_usage.jsonl"
    monkeypatch.setattr(jev, "USAGE_LOG", usage_path)
    now = datetime(2026, 9, 17, tzinfo=timezone.utc)
    usage_path.write_text(json.dumps({"ts": "2026-09-17T00:00:00Z", "estimated_cost_usd": 0.50}) + "\n")
    with pytest.raises(jev.InputError, match="calendar-month"):
        jev.check_monthly_cost_cap(now)
