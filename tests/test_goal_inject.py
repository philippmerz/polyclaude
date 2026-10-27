"""Finite /goal inject is one slash command and is cleared the same way."""

from __future__ import annotations

import json
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
    for name in ("goal_inject.sh", "inject_prompt.sh"):
        shutil.copy2(REPO / "scripts" / name, scripts / name)
    captured = tmp_path / "captured.txt"
    runner = tmp_path / "fake-runner.sh"
    runner.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" != "queue" ]]; then
  exit 98
fi
cat > "${FAKE_CAPTURE}"
exit 0
"""
    )
    runner.chmod(0o755)
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path),
            "POLYCLAUDE_AGENT_RUNNER": str(runner),
            "FAKE_CAPTURE": str(captured),
        }
    )
    return scripts / "goal_inject.sh", captured, env


def _run(script: Path, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script), *args],
        cwd=script.parent.parent,
        env=env,
        text=True,
        capture_output=True,
        timeout=10,
    )


def test_set_queues_one_goal_line_without_the_bounded_contract(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)
    result = _run(script, ["set", "recheck order 179 remainder"], env)
    assert result.returncode == 0, result.stderr
    assert captured.read_text() == "/goal recheck order 179 remainder"
    entry = json.loads((tmp_path / "notes" / "inject_log.md").read_text().splitlines()[-1])
    assert entry["bounded_contract"] is False
    assert entry["status"] == "QUEUED"


def test_clear_queues_goal_clear(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)
    result = _run(script, ["clear"], env)
    assert result.returncode == 0, result.stderr
    assert captured.read_text() == "/goal clear"


def test_newline_objective_is_rejected(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)
    result = _run(script, ["set", "first\nsecond"], env)
    assert result.returncode == 64
    assert "one non-empty line" in result.stderr
    assert not captured.exists()


def test_objective_is_not_reparsed_as_shell(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)
    marker = tmp_path / "should-not-exist"
    result = _run(script, ["set", f"literal $(touch {marker})"], env)
    assert result.returncode == 0, result.stderr
    assert captured.read_text() == f"/goal literal $(touch {marker})"
    assert not marker.exists()
