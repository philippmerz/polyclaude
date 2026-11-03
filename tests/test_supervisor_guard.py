import os
from pathlib import Path
from unittest.mock import Mock

import pytest
import _supervisor_guard as guard


@pytest.fixture
def setup_guard(tmp_path, monkeypatch):
    monkeypatch.setenv('POLYCLAUDE_SUPERVISOR_GUARD', '1')
    (tmp_path / 'logs').mkdir()
    popen = Mock()
    monkeypatch.setattr(guard.subprocess, 'Popen', popen)
    return tmp_path, popen


def test_dead_spawns_detached_and_rate_limits(setup_guard):
    repo, popen = setup_guard
    assert guard.ensure_supervisor(repo)
    kwargs = popen.call_args.kwargs
    assert kwargs['start_new_session'] is True
    assert kwargs['close_fds'] is True
    assert kwargs['stdin'] == guard.subprocess.DEVNULL
    assert kwargs['cwd'] == repo
    assert popen.call_args.args[0] == ['bash', 'scripts/box_ctl.sh', 'ensure']
    assert not guard.ensure_supervisor(repo)
    stamp = repo / 'logs/.supervisor_guard.stamp'
    os.utime(stamp, (1, 1))
    assert guard.ensure_supervisor(repo)


@pytest.mark.parametrize('age,heartbeat,alive', [(0, None, True), (121, None, False),
                                               (0, 179, True), (0, 181, False)])
def test_liveness(setup_guard, monkeypatch, age, heartbeat, alive):
    repo, popen = setup_guard
    pidfile = repo / 'logs/.box_supervisor.pid'
    pidfile.write_text('12345')
    now = guard.time.time()
    os.utime(pidfile, (now-age, now-age))
    original = Path.read_bytes
    monkeypatch.setattr(Path, 'read_bytes', lambda p: b'bash\0box_supervisor.sh\0'
                        if str(p) == '/proc/12345/cmdline' else original(p))
    if heartbeat is not None:
        hb = repo / 'logs/.box_supervisor.heartbeat'
        hb.touch()
        os.utime(hb, (now-heartbeat, now-heartbeat))
    assert guard.supervisor_alive(repo) is alive
    assert guard.ensure_supervisor(repo) is (not alive)
    assert popen.called is (not alive)


def test_disabled(setup_guard, monkeypatch):
    repo, popen = setup_guard
    monkeypatch.setenv('POLYCLAUDE_SUPERVISOR_GUARD', '0')
    assert not guard.ensure_supervisor(repo)
    popen.assert_not_called()


def test_never_raises(setup_guard):
    repo, popen = setup_guard
    popen.side_effect = OSError('spawn failed')
    assert not guard.ensure_supervisor(repo)
    assert 'spawn failed' in (repo / 'logs/box_supervisor.log').read_text()
    assert not guard.ensure_supervisor(repo / 'logs/box_supervisor.log/impossible')


def test_wrong_process_is_dead(setup_guard, monkeypatch):
    repo, _ = setup_guard
    (repo / 'logs/.box_supervisor.pid').write_text('12345')
    monkeypatch.setattr(Path, 'read_bytes', lambda p: b'python\0unrelated.py')
    assert not guard.supervisor_alive(repo)


def test_intentional_stop_suppresses_recovery(setup_guard):
    repo, popen = setup_guard
    (repo / 'logs/.box_supervisor.stopped').touch()
    assert not guard.ensure_supervisor(repo)
    popen.assert_not_called()
