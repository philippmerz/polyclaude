"""Provider-neutral subprocess adapter for scoped model workers.

The provider implementation and model mapping live in a host-private runner.
Callers choose a workload profile and reasoning effort, then consume stdout in
the same way they consume any other subprocess result.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess


DEFAULT_RUNNER = Path.home() / ".local" / "bin" / "polyclaude-agent"
VALID_PROFILES = {"main", "research", "fast"}
VALID_EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}


def run_agent(
    prompt: str,
    *,
    profile: str,
    effort: str,
    timeout: int,
    cwd: str = "/tmp",
    autonomous: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run one isolated model worker and return its completed process.

    The outer timeout is slightly longer than the runner's own deadline so the
    runner can report a clean timeout before this process has to terminate it.
    """
    if profile not in VALID_PROFILES:
        raise ValueError(f"invalid model profile: {profile}")
    if effort not in VALID_EFFORTS:
        raise ValueError(f"invalid reasoning effort: {effort}")
    if autonomous and profile != "main":
        raise ValueError("autonomous access is restricted to the main profile")
    if not prompt.strip():
        raise ValueError("prompt must not be empty")

    runner = os.environ.get("POLYCLAUDE_AGENT_RUNNER", str(DEFAULT_RUNNER))
    command = [
        runner,
        "run",
        "--profile", profile,
        "--effort", effort,
        "--timeout", str(timeout),
        "--cwd", cwd,
    ]
    if autonomous:
        command.extend(["--access", "autonomous"])

    return subprocess.run(
        command,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout + 20,
        check=False,
        cwd="/tmp",
    )
