"""Best-effort detached supervisor recovery; no trading operations."""
import datetime as dt
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time


def supervisor_alive(repo: Path) -> bool:
    try:
        pidfile = repo / 'logs/.box_supervisor.pid'
        pid = int(pidfile.read_text().strip())
        if pid <= 0 or b'box_supervisor' not in Path(f'/proc/{pid}/cmdline').read_bytes():
            return False
        heartbeat = repo / 'logs/.box_supervisor.heartbeat'
        now = time.time()
        if heartbeat.exists():
            return now - heartbeat.stat().st_mtime < 180
        return now - pidfile.stat().st_mtime < 120
    except Exception:
        return False


def ensure_supervisor(repo: Path, min_interval_s=300) -> bool:
    """Return whether recovery was spawned. Never propagate an exception."""
    if os.environ.get('POLYCLAUDE_SUPERVISOR_GUARD') == '0':
        return False
    log = repo / 'logs/box_supervisor.log'
    try:
        if (repo / 'logs/.box_supervisor.stopped').exists():
            return False
        log.parent.mkdir(parents=True, exist_ok=True)
        with (log.parent / '.supervisor_guard.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if supervisor_alive(repo):
                return False
            stamp = log.parent / '.supervisor_guard.stamp'
            if stamp.exists() and time.time() - stamp.stat().st_mtime < min_interval_s:
                return False
            stamp.touch()
            with log.open('a') as output:
                utc = dt.datetime.now(dt.timezone.utc).isoformat()
                output.write(f'{utc} guard: supervisor dead/stale, respawning (by {Path(sys.argv[0]).name} pid={os.getpid()})\n')
                output.flush()
                subprocess.Popen(['bash', 'scripts/box_ctl.sh', 'ensure'], cwd=repo,
                                 start_new_session=True, stdin=subprocess.DEVNULL,
                                 stdout=output, stderr=output, close_fds=True)
            return True
    except Exception as exc:
        try:
            with log.open('a') as output:
                output.write(f'{dt.datetime.now(dt.timezone.utc).isoformat()} guard error: {exc}\n')
        except Exception:
            pass
        return False
