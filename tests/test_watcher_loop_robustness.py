from types import SimpleNamespace

import pytest
import resting_watch as rw
import news_watcher as nw


def fail(*args, **kwargs):
    raise RuntimeError('injected failure')


@pytest.mark.parametrize('errors,expected', [(0, 120), (1, 120), (2, 240), (3, 360), (9, 600), (100000, 600)])
def test_safe_sleep_backoff(monkeypatch, errors, expected):
    sleeps = []
    monkeypatch.setattr(rw, 'load_config', lambda: {'poll_seconds': 120})
    monkeypatch.setattr(rw.time, 'sleep', sleeps.append)
    rw._safe_sleep(errors)
    assert sleeps == [expected]


def test_safe_sleep_config_fallback(monkeypatch):
    sleeps = []
    monkeypatch.setattr(rw, 'load_config', fail)
    monkeypatch.setattr(rw, '_log', lambda msg: None)
    monkeypatch.setattr(rw.time, 'sleep', sleeps.append)
    rw._safe_sleep(1)
    assert sleeps == [rw.LOOP_SECONDS_DEFAULT]


@pytest.mark.parametrize("counter", [0, 50])
def test_except_side_effects_survive_and_backoff_resets(monkeypatch, tmp_path, counter):
    logs, sleeps = [], []
    monkeypatch.setattr(rw, 'PID_PATH', tmp_path / 'pid')
    monkeypatch.setattr(rw, '_log', logs.append)
    monkeypatch.setattr(rw, '_rss_mb', lambda: 0)
    monkeypatch.setattr(rw, 'load_config', lambda: {'poll_seconds': 10})
    monkeypatch.setattr(rw, '_load_json', lambda *a: {'managed': {}, 'consecutive_errors': counter})
    monkeypatch.setattr(rw, 'wake_agent', fail)
    monkeypatch.setattr(rw, 'telegram', fail)
    monkeypatch.setattr(rw, '_save_json_atomic', fail)
    cycles = iter([True, True, False])
    def reconcile(*args):
        if next(cycles):
            fail()
        # no prior error counter on the successful cycle
        args[1]['consecutive_errors'] = 0
        return []
    monkeypatch.setattr(rw, 'reconcile', reconcile)
    def sleep(seconds):
        sleeps.append(seconds)
        if len(sleeps) == 3:
            raise KeyboardInterrupt
    monkeypatch.setattr(rw.time, 'sleep', sleep)
    with pytest.raises(KeyboardInterrupt):
        rw.poll_loop()
    assert sleeps == [10, 20, 10]
    assert any('error wake failed' in line for line in logs)
    if counter == 50:
        assert any('error telegram failed' in line for line in logs)
    else:
        assert any('error state save failed' in line for line in logs)
    assert logs[-1] == 'exiting rc=130'


def test_rss_fetch_timeout(monkeypatch):
    calls = []
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return SimpleNamespace(content=b'<rss/>', raise_for_status=lambda: None)
    monkeypatch.setattr(nw.httpx, 'get', get)
    monkeypatch.setattr(nw.feedparser, 'parse', lambda body: SimpleNamespace(entries=[]))
    monkeypatch.setattr(nw, 'save_state', lambda state: None)
    nw.poll_once({'feeds': [{'url': 'https://example.invalid/rss', 'name': 'test'}]}, {})
    assert calls[0][1]['timeout'] == 20.0
    assert calls[0][1]['follow_redirects'] is True
    assert calls[0][1]['headers']['User-Agent']


def test_loop_signals_log_and_exit(monkeypatch):
    logs = []
    monkeypatch.setattr(rw, '_log', logs.append)
    rw._loop_signal(rw.signal.SIGHUP, None)
    with pytest.raises(SystemExit) as exc:
        rw._loop_signal(rw.signal.SIGTERM, None)
    assert exc.value.code == 0
    assert 'received SIGHUP' in logs[0]
    assert 'received SIGTERM' in logs[1]
