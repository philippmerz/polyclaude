from pathlib import Path
import subprocess
import sys
from unittest import mock

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import agent_runtime  # noqa: E402


def test_builds_scoped_worker_command_without_shell(monkeypatch):
    monkeypatch.setenv("POLYCLAUDE_AGENT_RUNNER", "/opt/private/runner")
    completed = subprocess.CompletedProcess([], 0, "answer", "")
    with mock.patch.object(agent_runtime.subprocess, "run", return_value=completed) as run:
        result = agent_runtime.run_agent(
            "lookup prompt", profile="research", effort="medium", timeout=45
        )

    assert result is completed
    run.assert_called_once_with(
        [
            "/opt/private/runner",
            "run",
            "--profile", "research",
            "--effort", "medium",
            "--timeout", "45",
            "--cwd", "/tmp",
        ],
        input="lookup prompt",
        capture_output=True,
        text=True,
        timeout=65,
        check=False,
        cwd="/tmp",
    )


@pytest.mark.parametrize(
    ("profile", "effort", "autonomous"),
    [("unknown", "low", False), ("fast", "bogus", False), ("fast", "low", True)],
)
def test_rejects_unsafe_or_unknown_profiles(profile, effort, autonomous):
    with pytest.raises(ValueError):
        agent_runtime.run_agent(
            "prompt",
            profile=profile,
            effort=effort,
            timeout=30,
            autonomous=autonomous,
        )


def test_rejects_empty_prompt():
    with pytest.raises(ValueError):
        agent_runtime.run_agent(
            "  ", profile="fast", effort="low", timeout=30
        )
