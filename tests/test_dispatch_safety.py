import fcntl
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _dispatch_fixture(tmp_path: Path):
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    home = tmp_path / "home"
    notes = repo / "notes"
    runner = home / ".local" / "bin" / "polyclaude-agent"
    scripts.mkdir(parents=True)
    notes.mkdir()
    runner.parent.mkdir(parents=True)

    for name in ("inject_prompt.sh", "daily_checkin.sh"):
        target = scripts / name
        shutil.copy2(SCRIPTS / name, target)
        target.chmod(target.stat().st_mode | stat.S_IXUSR)

    runner.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  queue)
    cat >/dev/null
    exit "${FAKE_QUEUE_RC:?}"
    ;;
  run)
    cat > "${FAKE_RUN_PROMPT:?}"
    printf 'fallback-run\\n' >> "${FAKE_RUN_MARKER:?}"
    ;;
  *)
    exit 99
    ;;
esac
""",
        encoding="utf-8",
    )
    runner.chmod(0o700)

    marker = tmp_path / "fallback-runs"
    receipt = repo / "logs" / "cron" / "dispatch.json"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "POLYCLAUDE_AGENT_RUNNER": str(runner),
            "FAKE_RUN_MARKER": str(marker),
            "FAKE_RUN_PROMPT": str(tmp_path / "fallback-prompt"),
            "POLYCLAUDE_DISPATCH_RECEIPT": str(receipt),
        }
    )
    env.pop("POLYCLAUDE_FORCE_HEADLESS", None)
    return repo, runner, marker, env


def _receipt(repo: Path):
    path = repo / "logs" / "cron" / "dispatch.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload) == {"status", "why", "tick_id", "returncode"}
    assert len(payload["tick_id"]) == 16
    assert path.stat().st_mode & 0o777 == 0o600
    return payload


def test_inject_preserves_ambiguous_delivery_code(tmp_path):
    repo, _runner, marker, env = _dispatch_fixture(tmp_path)
    env["FAKE_QUEUE_RC"] = "75"

    result = subprocess.run(
        [str(repo / "scripts" / "inject_prompt.sh"), "scheduled tick"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 75
    assert not marker.exists()


@pytest.mark.parametrize("queue_rc", [70, 75, 76])
def test_daily_checkin_fails_closed_after_dispatch_starts(tmp_path, queue_rc):
    repo, _runner, marker, env = _dispatch_fixture(tmp_path)
    env["FAKE_QUEUE_RC"] = str(queue_rc)

    result = subprocess.run(
        [str(repo / "scripts" / "daily_checkin.sh")],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == queue_rc
    assert not marker.exists()
    dispatch_log = (repo / "logs" / "cron" / "peer_skips.log").read_text()
    assert f"queue failed rc={queue_rc}; no headless fallback" in dispatch_log
    receipt = _receipt(repo)
    assert (receipt["status"], receipt["why"], receipt["returncode"]) == (
        "failed", "operator_queue_failed", queue_rc
    )


def test_daily_checkin_queue_acceptance_receipt(tmp_path):
    repo, _runner, marker, env = _dispatch_fixture(tmp_path)
    env["FAKE_QUEUE_RC"] = "0"

    result = subprocess.run(
        [str(repo / "scripts" / "daily_checkin.sh")], cwd=repo, env=env,
        capture_output=True, text=True, timeout=10, check=False,
    )

    assert result.returncode == 0
    assert not marker.exists()
    receipt = _receipt(repo)
    assert (receipt["status"], receipt["why"], receipt["returncode"]) == (
        "queued", "operator_queue_accepted", 0
    )


def test_daily_checkin_falls_back_only_when_no_operator_is_proven(tmp_path):
    repo, _runner, marker, env = _dispatch_fixture(tmp_path)
    env["FAKE_QUEUE_RC"] = "69"

    result = subprocess.run(
        [str(repo / "scripts" / "daily_checkin.sh"), "NEWS REVIEW REQUEST: retained-alert-id"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0
    assert marker.read_text(encoding="utf-8").splitlines() == ["fallback-run"]
    assert "NEWS REVIEW REQUEST: retained-alert-id" in Path(env["FAKE_RUN_PROMPT"]).read_text()
    receipt = _receipt(repo)
    assert (receipt["status"], receipt["why"], receipt["returncode"]) == (
        "fallback_starting", "operator_absent", 69
    )
    assert receipt["status"] != "queued"


def test_daily_checkin_lock_held_receipt_is_deferred(tmp_path):
    repo, _runner, marker, env = _dispatch_fixture(tmp_path)
    env["FAKE_QUEUE_RC"] = "0"
    lock_path = repo / ".checkin.lock"
    with lock_path.open("w") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = subprocess.run(
            [str(repo / "scripts" / "daily_checkin.sh")], cwd=repo, env=env,
            capture_output=True, text=True, timeout=10, check=False,
        )
    assert result.returncode == 0
    assert not marker.exists()
    receipt = _receipt(repo)
    assert (receipt["status"], receipt["why"], receipt["returncode"]) == (
        "deferred", "checkin_lock_held", 0
    )


def test_daily_checkin_force_headless_receipt_marks_start_not_completion(tmp_path):
    repo, _runner, marker, env = _dispatch_fixture(tmp_path)
    env["POLYCLAUDE_FORCE_HEADLESS"] = "1"

    result = subprocess.run(
        [str(repo / "scripts" / "daily_checkin.sh")], cwd=repo, env=env,
        capture_output=True, text=True, timeout=10, check=False,
    )

    assert result.returncode == 0
    assert marker.read_text(encoding="utf-8").splitlines() == ["fallback-run"]
    receipt = _receipt(repo)
    assert (receipt["status"], receipt["why"], receipt["returncode"]) == (
        "fallback_starting", "operator_forced_headless", 0
    )
