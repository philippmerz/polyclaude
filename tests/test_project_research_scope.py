"""Project research must reject retired routes before starting a worker."""

from pathlib import Path
import subprocess
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import longterm_check


@pytest.mark.parametrize(
    "arguments",
    [
        ["Stock", "equity"],
        ["Aave (AAVE)", "crypto", "--horizon-years", "3"],
        ["Aave (AAVE)", "crypto", "--horizon-years", "1"],
        ["Aave (AAVE)", "crypto", "--horizon-years", "0"],
        ["Aave (AAVE)", "crypto", "--horizon-years", "nan"],
    ],
)
def test_invalid_scope_never_starts_research_worker(monkeypatch, arguments):
    def unexpected_worker(*args, **kwargs):
        pytest.fail("Invalid research scope reached a model worker")

    monkeypatch.setattr(longterm_check, "run_agent", unexpected_worker)
    monkeypatch.setattr(sys, "argv", ["longterm_check.py", *arguments, "--no-log"])

    with pytest.raises(SystemExit) as error:
        longterm_check.main()

    assert error.value.code == 2


def test_project_crypto_still_reaches_worker_without_writing_log(
    monkeypatch, tmp_path, capsys
):
    calls = []

    def worker(prompt, **kwargs):
        calls.append((prompt, kwargs))
        return subprocess.CompletedProcess([], 0, "### Verdict: 2/4 — WATCH\n", "")

    log_path = tmp_path / "research.md"
    monkeypatch.setattr(longterm_check, "run_agent", worker)
    monkeypatch.setattr(longterm_check, "LOG_PATH", log_path)
    monkeypatch.setattr(
        sys, "argv", ["longterm_check.py", "Aave (AAVE)", "crypto", "--no-log"]
    )

    assert longterm_check.main() == 0
    assert len(calls) == 1
    assert "Asset: Aave (AAVE)" in calls[0][0]
    assert "WATCH" in capsys.readouterr().out
    assert not log_path.exists()
