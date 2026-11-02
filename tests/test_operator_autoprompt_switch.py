"""Operator auto-prompt kill switch (notes/operator_autoprompt.json)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _fixture(tmp_path: Path, enabled: bool | None) -> tuple[Path, dict[str, str]]:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "notes").mkdir()
    for name in ("inject_prompt.sh", "daily_checkin.sh"):
        shutil.copy2(REPO / "scripts" / name, tmp_path / "scripts" / name)
    if enabled is not None:
        (tmp_path / "notes" / "operator_autoprompt.json").write_text(
            json.dumps({"enabled": enabled}, indent=2))
    marker = tmp_path / "runner_called"
    runner = tmp_path / "runner.sh"
    runner.write_text(f"#!/usr/bin/env bash\ncat >/dev/null\ntouch {marker}\nexit 0\n")
    runner.chmod(0o755)
    env = dict(os.environ, POLYCLAUDE_AGENT_RUNNER=str(runner),
               POLYCLAUDE_USAGE_PROBE="/nonexistent")
    return marker, env


def test_disabled_flag_drops_inject_without_touching_inject_log(tmp_path):
    marker, env = _fixture(tmp_path, enabled=False)
    out = subprocess.run(["bash", str(tmp_path / "scripts" / "inject_prompt.sh"), "Cron tick T."],
                         env=env, capture_output=True, text=True)
    assert out.returncode == 0
    assert not marker.exists()
    assert not (tmp_path / "notes" / "inject_log.md").exists()
    rows = (tmp_path / "logs" / "inject_suppressed.jsonl").read_text().splitlines()
    assert json.loads(rows[-1])["status"] == "SUPPRESSED"


def test_absent_or_enabled_flag_still_queues(tmp_path):
    for enabled in (None, True):
        sub = tmp_path / str(enabled)
        sub.mkdir()
        marker, env = _fixture(sub, enabled=enabled)
        out = subprocess.run(["bash", str(sub / "scripts" / "inject_prompt.sh"), "hello"],
                             env=env, capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
        assert marker.exists()


def test_daily_checkin_disabled_does_not_queue(tmp_path):
    marker, env = _fixture(tmp_path, enabled=False)
    out = subprocess.run(["bash", str(tmp_path / "scripts" / "daily_checkin.sh"), "news_watcher T1"],
                         env=env, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert not marker.exists()
    skips = (tmp_path / "logs" / "cron" / "peer_skips.log").read_text()
    assert "operator auto-prompt disabled" in skips
    assert "queued to operator" not in skips
