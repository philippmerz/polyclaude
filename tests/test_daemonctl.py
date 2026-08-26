import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _stop(processes):
    for process in processes:
        if process.poll() is None:
            process.terminate()
    for process in processes:
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def test_status_finds_all_script_path_forms_but_not_parent_text(tmp_path):
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    scripts.mkdir(parents=True)
    daemonctl = scripts / "daemonctl.sh"
    shutil.copy2(SCRIPTS / "daemonctl.sh", daemonctl)
    daemonctl.chmod(daemonctl.stat().st_mode | stat.S_IXUSR)

    script_name = f"daemon_probe_{os.getpid()}_{tmp_path.name}.py"
    probe = scripts / script_name
    probe.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")

    matched = [
        subprocess.Popen([sys.executable, str(probe), "start"]),
        subprocess.Popen(
            [sys.executable, script_name, "start"], cwd=scripts
        ),
        subprocess.Popen(
            [sys.executable, f"scripts/{script_name}", "start"], cwd=repo
        ),
        subprocess.Popen(
            [sys.executable, f"./scripts/{script_name}", "start"], cwd=repo
        ),
    ]
    parent_text = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(30)",
            str(probe),
            "start",
        ]
    )

    try:
        expected = {process.pid for process in matched}
        observed = set()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            result = subprocess.run(
                [str(daemonctl), "status", script_name],
                cwd=repo,
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            observed = {
                int(value) for value in result.stdout.partition(":")[2].split()
                if value.isdigit()
            }
            if observed == expected:
                break
            time.sleep(0.05)

        assert observed == expected
        assert parent_text.pid not in observed

        _stop(matched)
        result = subprocess.run(
            [str(daemonctl), "status", script_name],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        assert result.stdout.strip().endswith("<not running>")
    finally:
        _stop(matched + [parent_text])


def test_restart_replaces_relative_worker_with_one_canonical_worker(tmp_path):
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    logs = repo / "logs"
    python_dir = repo / ".venv" / "bin"
    scripts.mkdir(parents=True)
    logs.mkdir()
    python_dir.mkdir(parents=True)
    (python_dir / "python3").symlink_to(sys.executable)

    daemonctl = scripts / "daemonctl.sh"
    shutil.copy2(SCRIPTS / "daemonctl.sh", daemonctl)
    daemonctl.chmod(daemonctl.stat().st_mode | stat.S_IXUSR)
    script_name = f"restart_probe_{os.getpid()}_{tmp_path.name}.py"
    probe = scripts / script_name
    probe.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")

    legacy = subprocess.Popen(
        [sys.executable, f"./scripts/{script_name}", "start"], cwd=repo
    )
    try:
        result = subprocess.run(
            [str(daemonctl), "restart", script_name],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        legacy.wait(timeout=3)
        assert f"stopped pid {legacy.pid}" in result.stdout

        status = subprocess.run(
            [str(daemonctl), "status", script_name],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        pids = [
            int(value) for value in status.stdout.partition(":")[2].split()
            if value.isdigit()
        ]
        assert len(pids) == 1
        argv = Path(f"/proc/{pids[0]}/cmdline").read_bytes().split(b"\0")
        assert argv[1].decode() == str(probe)
        assert argv[2] == b"start"
    finally:
        subprocess.run(
            [str(daemonctl), "stop", script_name],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        _stop([legacy])
