"""Operator auto-prompt policy (notes/operator_autoprompt.json, scripts/autoprompt_policy.py).

2026-11-02 policy: scheduled ticks off (even when daily_checkin.sh is run by
hand), event wakes from news_watcher / opportunity_watch on, operator
self-follow-ups and /goal set off, /goal clear always allowed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
POLICY = {"scheduled_ticks": False, "event_wakes": True, "self_followups": False, "goal_set": False}
NEWS = "NEWS REVIEW REQUEST: inspect notes/news_alerts.jsonl for alert IDs a1."
OPP = "REVALIDATION REQUEST FROM OPPORTUNITY WATCH: x crossed — inspect notes/opportunity_alerts.jsonl"


def _fixture(tmp_path: Path, policy: dict | None | str):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "notes").mkdir()
    for name in ("inject_prompt.sh", "daily_checkin.sh", "autoprompt_policy.py"):
        shutil.copy2(REPO / "scripts" / name, tmp_path / "scripts" / name)
    flag = tmp_path / "notes" / "operator_autoprompt.json"
    if isinstance(policy, str):
        flag.write_text(policy)
    elif policy is not None:
        flag.write_text(json.dumps(policy))
    calls = tmp_path / "runner_calls"
    runner = tmp_path / "runner.sh"
    runner.write_text(f"#!/usr/bin/env bash\ncat >> {calls}\necho >> {calls}\nexit 0\n")
    runner.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k != "POLYCLAUDE_PROMPT_SOURCE"}
    env.update(POLYCLAUDE_AGENT_RUNNER=str(runner), POLYCLAUDE_USAGE_PROBE="/nonexistent")
    return calls, env


def _run(tmp_path, script, arg=None, env=None, extra=None):
    cmd = ["bash", str(tmp_path / "scripts" / script)] + ([arg] if arg is not None else [])
    e = dict(env, **(extra or {}))
    return subprocess.run(cmd, env=e, capture_output=True, text=True)


def _skips(tmp_path):
    return (tmp_path / "logs" / "cron" / "peer_skips.log").read_text()


@pytest.mark.parametrize("arg", [None, "grok-verify", "manual run"])
def test_scheduled_tick_suppressed_even_when_run_by_hand(tmp_path, arg):
    calls, env = _fixture(tmp_path, POLICY)
    out = _run(tmp_path, "daily_checkin.sh", arg, env)
    assert out.returncode == 0, out.stderr
    assert not calls.exists()
    assert "scheduled_tick suppressed" in _skips(tmp_path)
    assert "queued to operator" not in _skips(tmp_path)
    assert not (tmp_path / "notes" / "inject_log.md").exists()


@pytest.mark.parametrize("reason", [NEWS, OPP])
def test_event_wake_queues(tmp_path, reason):
    calls, env = _fixture(tmp_path, POLICY)
    out = _run(tmp_path, "daily_checkin.sh", reason, env)
    assert out.returncode == 0, out.stderr
    assert reason in calls.read_text()
    assert "queued to operator" in _skips(tmp_path)


def test_event_wakes_can_be_turned_off(tmp_path):
    calls, env = _fixture(tmp_path, dict(POLICY, event_wakes=False))
    _run(tmp_path, "daily_checkin.sh", NEWS, env)
    assert not calls.exists()
    assert "event_wake suppressed" in _skips(tmp_path)


def test_direct_cron_shaped_inject_suppressed_without_inject_log(tmp_path):
    calls, env = _fixture(tmp_path, POLICY)
    out = _run(tmp_path, "inject_prompt.sh", "Cron tick T. Run your check-in.", env)
    assert out.returncode == 0
    assert not calls.exists()
    assert not (tmp_path / "notes" / "inject_log.md").exists()
    row = json.loads((tmp_path / "logs" / "inject_suppressed.jsonl").read_text().splitlines()[-1])
    assert row["status"] == "SUPPRESSED" and row["source"] == "scheduled_tick"


def test_self_followup_and_goal_set_suppressed_goal_clear_passes(tmp_path):
    calls, env = _fixture(tmp_path, POLICY)
    _run(tmp_path, "inject_prompt.sh", "check the fill", env, {"POLYCLAUDE_PROMPT_SOURCE": "self_followup"})
    _run(tmp_path, "inject_prompt.sh", "/goal finish the audit", env)
    assert not calls.exists()
    _run(tmp_path, "inject_prompt.sh", "/goal clear", env)
    assert calls.read_text().strip() == "/goal clear"


def test_other_prompts_pass(tmp_path):
    calls, env = _fixture(tmp_path, POLICY)
    out = _run(tmp_path, "inject_prompt.sh", "hello", env)
    assert out.returncode == 0, out.stderr
    assert "hello" in calls.read_text()


@pytest.mark.parametrize("policy", [None, {}, dict(POLICY, scheduled_ticks=True)])
def test_absent_or_enabled_policy_queues_ticks(tmp_path, policy):
    calls, env = _fixture(tmp_path, policy)
    out = _run(tmp_path, "daily_checkin.sh", None, env)
    assert out.returncode == 0, out.stderr
    assert "Cron tick" in calls.read_text()


def test_legacy_enabled_false_blocks_everything_gated(tmp_path):
    calls, env = _fixture(tmp_path, {"enabled": False})
    _run(tmp_path, "daily_checkin.sh", NEWS, env)
    _run(tmp_path, "daily_checkin.sh", None, env)
    assert not calls.exists()


def test_corrupt_policy_fails_safe(tmp_path):
    calls, env = _fixture(tmp_path, "{not json")
    _run(tmp_path, "daily_checkin.sh", None, env)
    assert not calls.exists()
    _run(tmp_path, "daily_checkin.sh", NEWS, env)
    assert NEWS in calls.read_text()


def test_repo_policy_file_is_ticks_off_events_on():
    data = json.loads((REPO / "notes" / "operator_autoprompt.json").read_text())
    assert data["scheduled_ticks"] is False and data["event_wakes"] is True
    assert "enabled" not in data


def test_missing_gate_with_policy_present_fails_safe(tmp_path):
    calls, env = _fixture(tmp_path, POLICY)
    (tmp_path / "scripts" / "autoprompt_policy.py").unlink()
    _run(tmp_path, "daily_checkin.sh", None, env)
    assert not calls.exists()
    _run(tmp_path, "daily_checkin.sh", OPP, env)
    assert OPP in calls.read_text()


def test_operator_followup_marks_its_source():
    text = (REPO / "scripts" / "operator_followup.sh").read_text()
    assert "POLYCLAUDE_PROMPT_SOURCE=self_followup" in text
