import os
from pathlib import Path
import shlex
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


def _make_repo(tmp_path, script_name):
    repo = tmp_path / "repo"
    scripts = repo / "scripts"
    logs = repo / "logs"
    python_dir = repo / ".venv" / "bin"
    scripts.mkdir(parents=True)
    logs.mkdir()
    python_dir.mkdir(parents=True)
    (python_dir / "python3").symlink_to(sys.executable)

    probe = scripts / script_name
    probe.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    daemonctl = scripts / "daemonctl.sh"
    shutil.copy2(SCRIPTS / "daemonctl.sh", daemonctl)
    daemonctl.chmod(daemonctl.stat().st_mode | stat.S_IXUSR)

    keepalive_source = (SCRIPTS / "daemon_keepalive.sh").read_text(encoding="utf-8")
    repo_setting = 'REPO="${POLYCLAUDE_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"'
    lock_setting = 'exec 9>"/tmp/daemon_keepalive.lock"'
    assert repo_setting in keepalive_source
    assert lock_setting in keepalive_source
    keepalive_source = keepalive_source.replace(
        repo_setting, f"REPO={shlex.quote(str(repo))}", 1
    ).replace(lock_setting, 'exec 9>"${REPO}/daemon_keepalive.lock"', 1)
    lines = [
        line for line in keepalive_source.splitlines()
        if not line.startswith("revive ") and line != "exit 0"
    ]
    lines.extend([
        f'revive "{script_name}" "$PY" "${{REPO}}/scripts/{script_name}" start',
        "exit 0",
    ])
    keepalive = scripts / "daemon_keepalive.sh"
    keepalive.write_text("\n".join(lines) + "\n", encoding="utf-8")
    keepalive.chmod(keepalive.stat().st_mode | stat.S_IXUSR)
    return repo, daemonctl, keepalive, probe


def _run_keepalive(keepalive, repo):
    subprocess.run(
        [str(keepalive)],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )


def _status_pids(daemonctl, repo, script_name):
    result = subprocess.run(
        [str(daemonctl), "status", script_name],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    return [
        int(value) for value in result.stdout.partition(":")[2].split()
        if value.isdigit()
    ]


def _stop_workers(daemonctl, repo, script_name):
    subprocess.run(
        [str(daemonctl), "stop", script_name],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_relative_worker_prevents_revival(tmp_path):
    script_name = f"keepalive_probe_{os.getpid()}_{tmp_path.name}.py"
    repo, daemonctl, keepalive, _ = _make_repo(tmp_path, script_name)
    worker = subprocess.Popen(
        [sys.executable, f"scripts/{script_name}", "start"], cwd=repo
    )

    try:
        _run_keepalive(keepalive, repo)
        assert worker.poll() is None
        assert _status_pids(daemonctl, repo, script_name) == [worker.pid]
        assert not (repo / "logs" / "daemon_keepalive.log").exists()
    finally:
        _stop_workers(daemonctl, repo, script_name)
        _stop([worker])


def test_parent_text_does_not_block_single_canonical_revival(tmp_path):
    script_name = f"keepalive_probe_{os.getpid()}_{tmp_path.name}.py"
    repo, daemonctl, keepalive, probe = _make_repo(tmp_path, script_name)
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
        _run_keepalive(keepalive, repo)
        pids = []
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            pids = _status_pids(daemonctl, repo, script_name)
            if len(pids) == 1:
                break
            time.sleep(0.05)
        assert len(pids) == 1
        assert parent_text.pid not in pids
        assert parent_text.poll() is None
        argv = Path(f"/proc/{pids[0]}/cmdline").read_bytes().split(b"\0")
        assert argv[1].decode() == str(probe)
        assert argv[2] == b"start"

        _run_keepalive(keepalive, repo)
        assert _status_pids(daemonctl, repo, script_name) == pids
        log = repo / "logs" / "daemon_keepalive.log"
        assert log.read_text(encoding="utf-8").count("reviving:") == 1
    finally:
        _stop_workers(daemonctl, repo, script_name)
        _stop([parent_text])
