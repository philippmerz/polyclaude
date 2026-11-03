"""Offline transport and fail-closed bankroll regressions."""
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import _data_api as api
from _v2_data_api import envelope


@pytest.fixture(autouse=True)
def no_backoff(monkeypatch):
    monkeypatch.setattr(api, 'sleep', lambda _: None)


def row(**kw):
    return dict(token_id='token', condition_id='cid', current_size=2, avg_price=.4,
                current_value=1.2, current_price=.6, slug='example', **kw)


def reply(body, status=200):
    return httpx.Response(status, json=body)


def mock_get(monkeypatch, bodies):
    calls = []
    def get(url, *, params, timeout):
        calls.append((url, params.copy(), timeout))
        return bodies.pop(0)
    monkeypatch.setattr(api.httpx, 'get', get)
    return calls


def page(rows, cursor=None):
    return reply({'data': rows, 'pagination': {'next_cursor': cursor}})


def test_positions_cursor_merge_slice_and_mapping(monkeypatch):
    r = row(opposite_token_id='other', negative_risk=True, redeemable=True,
            entry_fees_usdc=.2, total_size=4, realized_pnl=.3)
    calls = mock_get(monkeypatch, [page([r], 'next'), page([dict(r, token_id='second')]), page([r])])
    response = api.get_positions({'user': 'ABC', 'offset': 0, 'limit': 2, 'sizeThreshold': 0}, timeout=9)
    response.raise_for_status()
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 2
    p = result[0]
    assert [p[k] for k in ('size','avgPrice','initialValue','currentValue','curPrice','cashPnl')] == pytest.approx([2,.4,.8,1.2,.6,.4])
    assert p['asset'] == 'token' and p['conditionId'] == 'cid'
    assert p['oppositeAsset'] == 'other' and p['negativeRisk'] and p['redeemable']
    assert p['entryFeesUsdc'] == .1 and p['realizedPnl'] == .3
    assert p['percentPnl'] is None and 'v2Status' in p
    assert calls[1][1]['cursor'] == 'next'
    assert all('offset' not in p and timeout == 9 for _, p, timeout in calls)
    assert calls[-1][1]['status'] == 'REDEEMABLE'


def test_threshold_default_and_explicit_zero(monkeypatch):
    r = dict(row(), current_size=.2)
    mock_get(monkeypatch, [page([r]), page([]), page([r]), page([])])
    assert api.get_positions({'user': 'abc'}).json() == []
    assert len(api.fetch_positions('abc')) == 1


@pytest.mark.parametrize('body,status,match', [([],200,'data'), ({'error':'gone','code':'retired','trace_id':'trace'},410,'410'), ({},200,'data'), ({'data':None},200,'list')])
def test_invalid_response(monkeypatch, body, status, match):
    mock_get(monkeypatch, [reply(body,status)])
    with pytest.raises(api.DataApiError, match=match):
        api.fetch_positions('abc')


@pytest.mark.parametrize('field', ['token_id','condition_id','current_size','avg_price','current_value','current_price'])
def test_required_field(monkeypatch, field):
    r = row(); del r[field]
    mock_get(monkeypatch, [page([r])])
    with pytest.raises(api.DataApiError, match=field + '.*example'):
        api.fetch_positions('abc')


@pytest.mark.parametrize('value', [float('nan'), float('inf'), 'bad', None, True])
def test_nonfinite_required(value):
    with pytest.raises(api.DataApiError, match='current_size'):
        api.to_v1(dict(row(), current_size=value))


def test_transient_retry(monkeypatch):
    calls = mock_get(monkeypatch, [reply({},503), page([]), page([])])
    assert api.fetch_positions('abc') == []
    assert len(calls) == 3


def test_persistent_retry(monkeypatch):
    calls = mock_get(monkeypatch, [reply({'code':'busy','trace_id':'xyz'},503) for _ in range(3)])
    with pytest.raises(api.DataApiError, match='503.*busy.*xyz'):
        api.fetch_positions('abc')
    assert len(calls) == 3


def test_non_json(monkeypatch):
    monkeypatch.setattr(api.httpx, 'get', lambda *a, **k: httpx.Response(200, text='bad'))
    with pytest.raises(api.DataApiError):
        api.get_value('abc')


def test_value(monkeypatch):
    mock_get(monkeypatch, [reply({'data': {'value':40.842}})])
    assert api.get_value('abc', timeout=8) == 40.842


def test_trades(monkeypatch):
    trade = {'proxy_wallet':'a','token_id':'t','condition_id':'c','event_slug':'e',
             'outcome_index':1,'transaction_hash':'hash','side':'BUY','size':2,'price':.4,'timestamp':1,'extra':3}
    calls = mock_get(monkeypatch, [page([trade],'next'),page([trade])])
    trades = api.get_trades(market='cid', limit=10, takerOnly=True, timeout=12)
    assert len(trades) == 2
    assert trades[0] == {'proxyWallet':'a','asset':'t','conditionId':'c','eventSlug':'e','outcomeIndex':1,
                         'transactionHash':'hash','side':'BUY','size':2,'price':.4,'timestamp':1,'extra':3}
    assert calls[1][1]['cursor'] == 'next' and calls[0][1]['takerOnly'] is True
    assert all('offset' not in p for _,p,_ in calls)


def test_page_cap(monkeypatch):
    mock_get(monkeypatch, [page([], 'next')])
    with pytest.raises(api.DataApiError, match='page cap'):
        api.get_trades(max_pages=1)


def test_bankroll_failure_preserves_cache(monkeypatch, tmp_path, capsys):
    import bankroll
    cache = tmp_path / 'cache.json'
    cache.write_text('{"total":188}')
    monkeypatch.setattr(bankroll, 'BANKROLL_CACHE_PATH', cache)
    monkeypatch.setattr(sys, 'argv', ['bankroll.py'])
    monkeypatch.setattr(bankroll, 'wallet_addresses', lambda: {'pm':'abc'})
    monkeypatch.setattr(bankroll, 'native_prices', lambda warnings: {})
    monkeypatch.setattr(bankroll, 'pick_rpc', lambda *a: pytest.fail('RPC must not run'))
    def fail(**kwargs):
        raise api.DataApiError('HTTP 410')
    monkeypatch.setattr(api, 'get_positions', fail)
    assert bankroll.main() == 2
    assert 'ERROR: PM positions unavailable' in capsys.readouterr().err
    assert cache.read_text() == '{"total":188}'
    cache.unlink()
    assert bankroll.main() == 2
    assert not cache.exists()


@pytest.mark.parametrize('status,body', [(429, {}), (200, {'retryable': True})])
def test_other_transient_responses(monkeypatch, status, body):
    calls = mock_get(monkeypatch, [reply(body, status), reply({'data': {'value': 2}})])
    assert api.get_value('abc') == 2
    assert len(calls) == 2


def test_transport_retry_and_backoff(monkeypatch):
    attempts = []
    delays = []
    def get(*args, **kwargs):
        attempts.append(1)
        if len(attempts) < 3:
            raise httpx.ReadTimeout('offline')
        return reply({'data': {'value': 2}})
    monkeypatch.setattr(api.httpx, 'get', get)
    monkeypatch.setattr(api, 'sleep', delays.append)
    assert api.get_value('abc') == 2
    assert delays == [.5, 1]


def test_audit_wraps_adapter_failure(monkeypatch):
    import position_state_audit as audit
    def fail(**kwargs):
        raise api.DataApiError('HTTP 503')
    monkeypatch.setattr(api, 'get_positions', fail)
    monkeypatch.setattr(audit.time, 'sleep', lambda _: None)
    with pytest.raises(audit.LivePositionsUnavailable, match='503'):
        audit._live_positions()
