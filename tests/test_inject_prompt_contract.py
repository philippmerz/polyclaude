"""Regressions for bounded scheduled-prompt contracts."""

from __future__ import annotations

import hashlib
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
cat > "${FAKE_CAPTURE}"
exit "${FAKE_QUEUE_RC:-0}"
"""
    )
    runner.chmod(0o755)
    usage_probe = tmp_path / "fake-usage.sh"
    usage_probe.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' 'Model usage headroom:' '  kimi-for-coding: no provider quota exposed'
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


def _attempt(log_path: Path) -> dict[str, object]:
    lines = log_path.read_text(encoding="utf8").splitlines()
    assert len(lines) == 1
    return json.loads(lines[0])


def _assert_payload_binding(entry: dict[str, object], payload: bytes) -> None:
    assert entry["queued_prompt_utf8_bytes"] == len(payload)
    assert entry["queued_prompt_sha256"] == hashlib.sha256(payload).hexdigest()


def test_scheduled_prompts_append_bounded_run_contract(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)

    result = _run(script, "Cron tick 20260828T140001Z. Run check-in.", env)

    assert result.returncode == 0, result.stderr
    payload = captured.read_text()
    assert "BOUNDED RUN CONTRACT" in payload
    assert "complete the concrete necessary follow-up or verification" in payload
    assert "cron and event watchers handle waiting" in payload
    assert "Do not create or maintain an indefinite durable goal" in payload
    assert (
        "This supersedes earlier scheduled instructions requiring perpetual goal continuation "
        "(operator-authorized 2026-09-08)."
    ) in payload
    assert "automatic continuation turns" not in payload
    assert "maximum expected ROI" not in payload
    assert "until the user manually cancels it" not in payload
    assert "durable ROI-goal" not in payload
    assert "RESOURCE SNAPSHOT" in payload
    assert "kimi-for-coding: no provider quota exposed" in payload
    assert "RESOURCE CONTRACT" in payload
    assert "check_usage.sh --brief" in payload
    assert "do not inject /usage" in payload
    log_path = tmp_path / "notes" / "inject_log.md"
    entry = _attempt(log_path)
    _assert_payload_binding(entry, captured.read_bytes())
    assert entry["status"] == "QUEUED"
    assert entry["actual_rc"] == 0
    assert entry["bounded_contract"] is True
    assert "Cron tick" not in log_path.read_text(encoding="utf8")
    assert "no provider quota exposed" not in log_path.read_text(encoding="utf8")


def test_daily_checkin_includes_direct_quota_preflight() -> None:
    prompt_source = (REPO / "scripts" / "daily_checkin.sh").read_text()

    assert "BOUNDED RUN CONTRACT" in prompt_source
    assert "Do not create or maintain an indefinite durable goal" in prompt_source
    assert "Cron and event watchers handle waiting" in prompt_source
    assert "CONTINUATION CONTRACT:" not in prompt_source
    assert "create one whose objective is to keep operating polyclaude" not in prompt_source
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
    entry = _attempt(tmp_path / "notes" / "inject_log.md")
    _assert_payload_binding(entry, captured.read_bytes())
    assert entry["bounded_contract"] is True


def test_periodic_prompt_also_gets_bounded_contract_but_ordinary_prompt_does_not(
    tmp_path: Path,
) -> None:
    script, captured, env = _fixture(tmp_path)

    periodic = _run(
        script,
        "Periodic check: anything else to take care of?",
        env,
    )
    assert periodic.returncode == 0
    periodic_payload = captured.read_text()
    assert periodic_payload.count("BOUNDED RUN CONTRACT") == 1
    ordinary = _run(script, "operator asked a normal question", env)
    assert ordinary.returncode == 0
    ordinary_payload = captured.read_text()
    assert "BOUNDED RUN CONTRACT" not in ordinary_payload
    assert "operator asked a normal question" in ordinary_payload
    for payload in (periodic_payload, ordinary_payload):
        assert "automatic continuation turns" not in payload
        assert "maximum expected ROI" not in payload
        assert "until the user manually cancels it" not in payload


def test_retired_sunday_seed_never_probes_queues_or_logs(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)
    probe_marker = tmp_path / "usage-probed"
    env["FAKE_USAGE_CAPTURE"] = str(probe_marker)
    Path(env["POLYCLAUDE_USAGE_PROBE"]).write_text(
        '#!/usr/bin/env bash\nprintf used > "${FAKE_USAGE_CAPTURE}"\n'
    )

    result = _run(
        script,
        "Sunday weekly long-term review. Pick domains, vet stocks, and Telegram.",
        env,
    )

    assert result.returncode == 0, result.stderr
    assert "Retired scheduled seed: no work queued." in result.stdout
    assert not captured.exists()
    assert not probe_marker.exists()
    assert not (tmp_path / "notes" / "inject_log.md").exists()


def test_unscheduled_check_prompt_is_delivered_even_when_last_reply_is_idle(
    tmp_path: Path,
) -> None:
    script, captured, env = _fixture(tmp_path)

    result = _run(script, "Continuation check: keep going", env)

    assert result.returncode == 0, result.stderr
    assert captured.read_text().strip() == "Continuation check: keep going"


def test_attempt_log_is_metadata_only_and_tracks_exact_queued_utf8_payload(
    tmp_path: Path,
) -> None:
    script, captured, env = _fixture(tmp_path)
    log_path = tmp_path / "notes" / "inject_log.md"
    legacy = b"## preserved legacy record\n"
    log_path.write_bytes(legacy)
    old_mtime_ns = 1_700_000_000_000_000_000
    os.utime(log_path, ns=(old_mtime_ns, old_mtime_ns))
    marker = tmp_path / "must-not-execute"
    prompt = (
        "Periodic check: literal $(touch "
        + str(marker)
        + ") and `touch "
        + str(marker)
        + "`;\nsecond line with $HOME and café"
    )

    result = _run(script, prompt, env)

    assert result.returncode == 0, result.stderr
    assert not marker.exists()
    payload = captured.read_bytes()
    assert prompt.encode("utf8") in payload
    log_bytes = log_path.read_bytes()
    assert log_bytes.startswith(legacy)
    record_bytes = log_bytes[len(legacy):]
    assert record_bytes.count(b"\n") == 1
    assert b"touch " not in record_bytes
    assert b"Periodic check" not in record_bytes
    assert b"no provider quota exposed" not in record_bytes
    entry = json.loads(record_bytes)
    _assert_payload_binding(entry, payload)
    assert entry["status"] == "QUEUED"
    assert entry["actual_rc"] == 0
    assert entry["bounded_contract"] is True
    assert log_path.stat().st_mtime_ns > old_mtime_ns


def test_failed_queue_logs_rc_and_exact_payload_metadata_only(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)
    env["FAKE_QUEUE_RC"] = "7"
    prompt = "operator asked to retry after failure\nkeep this body private"

    result = _run(script, prompt, env)

    assert result.returncode == 7
    payload = captured.read_bytes()
    assert payload == prompt.encode("utf8")
    log_path = tmp_path / "notes" / "inject_log.md"
    log_bytes = log_path.read_bytes()
    assert log_bytes.count(b"\n") == 1
    assert prompt.encode("utf8") not in log_bytes
    entry = _attempt(log_path)
    _assert_payload_binding(entry, payload)
    assert entry["status"] == "FAILED"
    assert entry["actual_rc"] == 7
    assert entry["bounded_contract"] is False
    assert "SKIPPED" not in (tmp_path / "notes" / "inject_log.md").read_text()


def test_queue_failure_is_preserved_and_logged(tmp_path: Path) -> None:
    script, captured, env = _fixture(tmp_path)
    env["FAKE_QUEUE_RC"] = "76"

    result = _run(script, "Cron tick failed queue", env)

    assert result.returncode == 76
    assert "queue failed" in result.stderr
    payload = captured.read_bytes()
    assert b"BOUNDED RUN CONTRACT" in payload
    entry = _attempt(tmp_path / "notes" / "inject_log.md")
    _assert_payload_binding(entry, payload)
    assert entry["status"] == "FAILED"
    assert entry["actual_rc"] == 76
    assert entry["bounded_contract"] is True


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
