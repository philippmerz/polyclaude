"""Regressions for scheduled-prompt continuation contracts."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    scripts = tmp_path / "scripts"
    notes = tmp_path / "notes"
    scripts.mkdir()
    notes.mkdir()
    for name in ("inject_prompt.sh", "operator_followup.sh"):
        shutil.copy2(REPO / "scripts" / name, scripts / name)

    captured = tmp_path / "captured.txt"
    runner = tmp_path / "fake-runner.sh"
    runner.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
command_name="${1:-}"
if [[ "${command_name}" == "last-reply" ]]; then
  echo "Idle"
  exit 99
fi
if [[ "${command_name}" != "queue" ]]; then
  exit 98
fi
payload=$(cat)
printf '%s\\n' "${payload}" >> "${FAKE_CAPTURE}"
exit "${FAKE_QUEUE_RC:-0}"
"""
    )
    runner.chmod(0o755)
    usage_probe = tmp_path / "fake-usage.sh"
    usage_probe.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' 'Codex quota headroom:' '  codex: 32% used / 68% headroom (1w, resets later)'
"""
    )
    usage_probe.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path),
            "POLYCLAUDE_AGENT_RUNNER": str(runner),
            "POLYCLAUDE_USAGE_PROBE": str(usage_probe),
            "FAKE_CAPTURE": str(captured),
        }
    )
    return scripts / "inject_prompt.sh", captured, env


def _run(script: Path, prompt: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), prompt],
        cwd=script.parent.parent,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
    )


def test_scheduled_prompts_append_manual_cancel_only_goal_contract(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)

    result = _run(script, "Cron tick 20260828T140001Z. Run check-in.", env)

    assert result.returncode == 0, result.stderr
    payload = captured.read_text()
    assert "CONTINUATION CONTRACT" in payload
    assert "automatic continuation turns" in payload
    assert "until the user manually cancels it" in payload
    assert "RESOURCE SNAPSHOT" in payload
    assert "codex: 32% used / 68% headroom" in payload
    assert "RESOURCE CONTRACT" in payload
    assert "check_usage.sh --brief" in payload
    assert "do not inject /usage" in payload
    inject_log = (tmp_path / "notes" / "inject_log.md").read_text()
    assert "durable ROI-goal continuation contract appended" in inject_log
    assert "direct Codex quota-headroom contract appended" in inject_log


def test_daily_checkin_includes_direct_quota_preflight() -> None:
    prompt_source = (REPO / "scripts" / "daily_checkin.sh").read_text()

    assert "RESOURCE PRE-FLIGHT" in prompt_source
    assert "./scripts/check_usage.sh --brief" in prompt_source
    assert "do not inject `/usage`" in prompt_source
    assert "Never skip required safety checks" in prompt_source


def test_failed_usage_probe_never_blocks_scheduled_risk_prompt(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)
    failed_probe = tmp_path / "failed-usage.sh"
    failed_probe.write_text("#!/usr/bin/env bash\nexit 2\n")
    failed_probe.chmod(0o755)
    env["POLYCLAUDE_USAGE_PROBE"] = str(failed_probe)

    result = _run(script, "Cron tick quota unavailable", env)

    assert result.returncode == 0, result.stderr
    payload = captured.read_text()
    assert "quota unavailable" in payload
    assert "unavailable (probe failed" in payload


def test_periodic_prompt_also_restores_goal_but_ordinary_prompt_does_not(
    tmp_path: Path,
) -> None:
    script, captured, env = _fixture(tmp_path)

    periodic = _run(
        script,
        "Periodic check: anything else to take care of?",
        env,
    )
    ordinary = _run(script, "operator asked a normal question", env)

    assert periodic.returncode == ordinary.returncode == 0
    payload = captured.read_text()
    assert payload.count("CONTINUATION CONTRACT") == 1


def test_continuation_is_never_auto_skipped_for_idle_last_reply(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)

    result = _run(script, "Continuation check: keep going", env)

    assert result.returncode == 0, result.stderr
    assert captured.read_text().strip() == "Continuation check: keep going"
    assert "SKIPPED" not in (tmp_path / "notes" / "inject_log.md").read_text()


def test_queue_failure_is_preserved_and_logged(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)
    env["FAKE_QUEUE_RC"] = "76"

    result = _run(script, "Cron tick failed queue", env)

    assert result.returncode == 76
    assert "queue failed" in result.stderr
    assert "inject FAILED" in (tmp_path / "notes" / "inject_log.md").read_text()
    assert "CONTINUATION CONTRACT" in captured.read_text()


def test_operator_followup_help_never_schedules_literal_help(tmp_path: Path) -> None:
    scripts = tmp_path / "scripts"
    notes = tmp_path / "notes"
    scripts.mkdir()
    notes.mkdir()
    script = scripts / "operator_followup.sh"
    shutil.copy2(REPO / "scripts" / "operator_followup.sh", script)

    result = subprocess.run(
        ["bash", str(script), "--help"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert not (notes / ".followup_pid").exists()
