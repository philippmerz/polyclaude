"""Pure regressions for the read-only model usage probe."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "model_usage.py"
SPEC = importlib.util.spec_from_file_location("model_usage", SCRIPT)
assert SPEC and SPEC.loader
model_usage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model_usage)


def _rows(now_ms: int) -> list[tuple[int, str]]:
    fresh = now_ms - 60 * 60 * 1000  # one hour ago
    old = now_ms - 48 * 60 * 60 * 1000  # outside the 24h window
    return [
        (
            fresh,
            json.dumps(
                {
                    "modelID": "kimi-for-coding",
                    "tokens": {
                        "input": 1500,
                        "output": 300,
                        "reasoning": 160,
                        "cache": {"read": 40000, "write": 0},
                    },
                }
            ),
        ),
        (
            old,
            json.dumps(
                {
                    "modelID": "kimi-for-coding",
                    "tokens": {
                        "input": 2500,
                        "output": 700,
                        "reasoning": 240,
                        "cache": {"read": 100000, "write": 5000},
                    },
                }
            ),
        ),
        (
            fresh,
            json.dumps(
                {
                    "modelID": "kimi-for-coding",
                    "tokens": {"total": 42418, "cache": {"read": 40448}},
                }
            ),
        ),
        (fresh, "not-json"),
        (fresh, json.dumps({"modelID": "kimi-for-coding"})),  # no tokens block
    ]


def test_summarize_splits_24h_and_all_time_totals() -> None:
    now = 1_800_000_000_000
    snapshot = model_usage.summarize(_rows(now), now_ms=now)
    totals = snapshot["models"]["kimi-for-coding"]

    assert totals["tokens"]["input"] == 1500
    assert totals["tokens"]["output"] == 300
    assert totals["tokens"]["cache_read"] == 80448
    assert totals["tokens"]["cache_write"] == 0
    assert totals["total"]["input"] == 4000
    assert totals["total"]["output"] == 1000
    assert totals["total"]["cache_read"] == 180448
    assert totals["total"]["cache_write"] == 5000


def test_format_notes_no_provider_quota_and_brief_omits_totals() -> None:
    now = 1_800_000_000_000
    snapshot = model_usage.summarize(_rows(now), now_ms=now)

    rendered = model_usage.format_snapshot(snapshot)
    assert "local OpenCode telemetry" in rendered
    assert "kimi-for-coding: no provider quota exposed" in rendered
    assert "24h tokens: 1.50k in / 300 out" in rendered

    brief = model_usage.format_snapshot(snapshot, brief=True)
    assert "24h tokens" not in brief
    assert "no provider quota exposed" in brief


def test_empty_usage_fails_closed() -> None:
    snapshot = model_usage.summarize([], now_ms=1_800_000_000_000)
    try:
        model_usage.format_snapshot(snapshot)
    except model_usage.UsageProbeError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected UsageProbeError")


def test_shell_wrapper_adds_local_bins_to_minimal_cron_path(tmp_path: Path) -> None:
    captured = tmp_path / "path.txt"
    fake_python = tmp_path / "fake-python"
    fake_python.write_text(
        "#!/usr/bin/env bash\nprintf '%s' \"${PATH}\" > \"${CAPTURE_PATH}\"\n"
    )
    fake_python.chmod(0o755)

    result = subprocess.run(
        ["bash", str(SCRIPT.parent / "check_usage.sh"), "--brief"],
        cwd=SCRIPT.parents[1],
        env={
            "HOME": str(tmp_path),
            "PATH": "/usr/bin:/bin",
            "POLYCLAUDE_PYTHON": str(fake_python),
            "CAPTURE_PATH": str(captured),
        },
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert captured.read_text().split(":")[:2] == [
        "/usr/local/bin",
        f"{tmp_path}/.local/bin",
    ]


def test_missing_database_fails_closed(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "bash",
            str(SCRIPT.parent / "check_usage.sh"),
            "--brief",
            "--db",
            str(tmp_path / "missing.db"),
        ],
        cwd=SCRIPT.parents[1],
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert result.returncode == 2
    assert "ERROR" in result.stderr
