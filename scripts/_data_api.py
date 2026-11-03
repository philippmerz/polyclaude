"""Strict, retrying Data API v2 adapter with v1-shaped public rows."""
from __future__ import annotations

import math
import time
import httpx

BASE_URL = "https://data-api.polymarket.com"
_MAX_PAGES = 50
_ATTEMPTS = 3
sleep = time.sleep


class DataApiError(RuntimeError):
    """Unavailable or malformed Data API data; never an empty portfolio."""


def _f(value):
    try:
        result = float(value) if value is not None and not isinstance(value, bool) else None
        return result if result is not None and math.isfinite(result) else None
    except (ValueError, TypeError, OverflowError):
        return None


def _schema_error(endpoint, body, message):
    detail = (f" code={body.get('code')} trace_id={body.get('trace_id')}"
              if isinstance(body, dict) else "")
    return DataApiError(f"{endpoint} HTTP 200: {message}{detail}")


def _request(endpoint, params, timeout):
    for attempt in range(_ATTEMPTS):
        retry = False
        try:
            response = httpx.get(BASE_URL + endpoint, params=dict(params), timeout=timeout)
        except httpx.TransportError as exc:
            error = DataApiError(f"{endpoint}: transport error: {exc}")
            retry = True
        else:
            status = response.status_code
            decoded = True
            try:
                body = response.json()
            except (ValueError, TypeError) as exc:
                body = None
                decoded = False
                error = DataApiError(f"{endpoint} HTTP {status}: non-JSON body")
            else:
                detail = (f" code={body.get('code')} trace_id={body.get('trace_id')} "
                          f"error={body.get('error')}" if isinstance(body, dict) else "")
                error = DataApiError(f"{endpoint} HTTP {status}:{detail}")
            retry = status == 429 or status >= 500 or (isinstance(body, dict) and body.get('retryable') is True)
            if 200 <= status < 300 and not retry:
                if not decoded:
                    raise error
                if not isinstance(body, dict) or 'data' not in body:
                    raise DataApiError(f"{error}; expected object with data")
                return body
        if not retry or attempt == _ATTEMPTS - 1:
            raise error
        sleep(0.5 * 2 ** attempt)


def _walk(endpoint, params, timeout, max_pages):
    params = dict(params)
    for _ in range(max_pages):
        body = _request(endpoint, params, timeout)
        data = body['data']
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise _schema_error(endpoint, body, "data must be a list of objects")
        yield from data
        pagination = body.get('pagination')
        if not isinstance(pagination, dict):
            raise _schema_error(endpoint, body, "pagination must be an object")
        if 'has_more' in pagination and not isinstance(pagination['has_more'], bool):
            raise _schema_error(endpoint, body, "invalid pagination.has_more")
        cursor = pagination.get('next_cursor')
        if cursor is None or cursor == '':
            if pagination.get('has_more') is True:
                raise DataApiError(f"{endpoint}: has_more without next_cursor")
            return
        if not isinstance(cursor, str):
            raise DataApiError(f"{endpoint}: invalid next_cursor")
        params['cursor'] = cursor
    raise DataApiError(f"{endpoint}: pagination exceeded page cap {max_pages}")


def to_v1(row: dict) -> dict:
    if not isinstance(row, dict):
        raise DataApiError("/v2/positions: row must be an object")
    for field in ('token_id', 'condition_id', 'current_size', 'avg_price', 'current_value', 'current_price'):
        value = row.get(field)
        valid = isinstance(value, str) and bool(value) if field in ('token_id', 'condition_id') else _f(value) is not None
        if not valid:
            raise DataApiError(f"/v2/positions HTTP 200: invalid required field {field} slug={row.get('slug')}")
    size = _f(row['current_size'])
    avg = _f(row['avg_price'])
    cur_val = _f(row['current_value'])
    init_val = size * avg
    cash_pnl = _f(row.get('unrealized_pnl'))
    if cash_pnl is None:
        cash_pnl = cur_val - init_val
    fees = _f(row.get('entry_fees_usdc'))
    total = _f(row.get('total_size'))
    if fees is not None and total is not None and total > 0 and size < total:
        fees *= size / total
    return {
        "entryFeesUsdc": fees,
        "proxyWallet": row.get("proxy_wallet"),
        "asset": row.get("token_id"),
        "conditionId": row.get("condition_id"),
        "size": size,
        "avgPrice": avg,
        "initialValue": init_val,
        "currentValue": cur_val,
        "cashPnl": cash_pnl,
        "percentPnl": _f(row.get("percent_pnl")),
        "totalBought": _f(row.get("total_size")),
        "realizedPnl": _f(row.get("realized_pnl")),
        "percentRealizedPnl": _f(row.get("percent_realized_pnl")),
        "curPrice": _f(row.get("current_price")),
        "redeemable": row.get("redeemable") is True,
        "mergeable": row.get("mergeable") is True,
        "title": row.get("title"),
        "slug": row.get("slug"),
        "icon": row.get("icon"),
        "eventId": row.get("event_id"),
        "eventSlug": row.get("event_slug"),
        "outcome": row.get("outcome"),
        "outcomeIndex": row.get("outcome_index"),
        "oppositeOutcome": row.get("opposite_outcome"),
        "oppositeAsset": row.get("opposite_token_id"),
        "endDate": row.get("end_date"),
        "negativeRisk": row.get("negative_risk") is True,
        "v2Status": row.get("status"),
    }


class PositionsResponse:
    status_code = 200

    def __init__(self, rows):
        self._rows = rows

    def json(self):
        return self._rows

    def raise_for_status(self):
        return self


def get_positions(params: dict | None = None, timeout: float = 15, **_) -> PositionsResponse:
    p = dict(params or {})
    user = str(p.get('user') or '').lower()
    if not user:
        raise DataApiError('/v2/positions: user required')
    floor = _f(p.get('sizeThreshold', p.get('size_threshold', 1.0)))
    if floor is None:
        raise DataApiError('/v2/positions: invalid sizeThreshold')
    seen = {}
    for status in ('OPEN', 'REDEEMABLE'):
        for row in _walk('/v2/positions', {'user': user, 'status': status, 'limit': 1000,
                                         'sizeThreshold': floor}, timeout, _MAX_PAGES):
            mapped = to_v1(row)
            seen.setdefault(mapped['asset'], mapped)
    rows = [r for r in seen.values() if r['size'] >= floor]
    offset = int(p.get('offset', 0))
    limit = p.get('limit')
    return PositionsResponse(rows[offset:] if limit is None else rows[offset:offset + int(limit)])


def fetch_positions(user: str, size_threshold: float = 0.0, timeout: float = 15) -> list[dict]:
    return get_positions({'user': user, 'sizeThreshold': size_threshold}, timeout).json()


def get_value(user: str, timeout: float = 15) -> float:
    body = _request('/v2/value', {'user': user}, timeout)
    data = body['data']
    value = _f(data.get('value')) if isinstance(data, dict) else None
    if value is None:
        raise DataApiError('/v2/value HTTP 200: invalid data.value')
    return value


_TRADE_KEYS = {'proxy_wallet': 'proxyWallet', 'token_id': 'asset', 'condition_id': 'conditionId',
               'event_slug': 'eventSlug', 'outcome_index': 'outcomeIndex', 'transaction_hash': 'transactionHash'}


def get_trades(user=None, market=None, limit=500, max_pages=50, timeout=15, **params) -> list[dict]:
    params = dict(params, limit=limit)
    if user is not None:
        params['user'] = user
    if market is not None:
        params['market'] = market
    if 'offset' in params:
        raise DataApiError('/v2/trades: offset unsupported; use cursor pagination')
    return [{_TRADE_KEYS.get(k, k): v for k, v in row.items()}
            for row in _walk('/v2/trades', params, timeout, max_pages)]
