"""Strict, read-only batching transport for Polymarket CLOB books.

The ``POST /books`` endpoint may omit requested assets which have no returned
book, and its response order is not an API contract.  Callers therefore use
the returned ``asset_id`` as the only join key.  A requested asset absent from
the response is represented explicitly by ``None``; malformed responses fail
closed with an exception.
"""

from __future__ import annotations

import time
from collections.abc import Iterable
from typing import Any

import httpx


BOOKS_URL = "https://clob.polymarket.com/books"
MAX_UNIQUE_BOOKS = 500


def _remaining_timeout(deadline: float | None, timeout: float) -> float:
    """Return a positive request timeout bounded by an absolute monotonic deadline."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if deadline is None:
        return float(timeout)
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("CLOB books deadline exceeded")
    return min(float(timeout), remaining)


def fetch_books(
    token_ids: Iterable[str],
    *,
    client: httpx.Client | None = None,
    deadline: float | None = None,
    timeout: float = 10.0,
    url: str = BOOKS_URL,
) -> dict[str, dict[str, Any] | None]:
    """Fetch a batch of books and map results strictly by ``asset_id``.

    The result contains every requested token in input order.  ``None`` means
    the endpoint returned no row for that requested token.  Response rows must
    be objects with a non-empty string ``asset_id`` that is requested exactly
    once.  No positional fallback is permitted.
    """
    requested = list(token_ids)
    if not requested:
        return {}
    if any(not isinstance(token, str) or not token.strip() for token in requested):
        raise ValueError("token_ids must contain non-empty strings")
    if len(set(requested)) != len(requested):
        raise ValueError("token_ids contain duplicates")
    mapped: dict[str, dict[str, Any] | None] = {token: None for token in requested}
    for start in range(0, len(requested), MAX_UNIQUE_BOOKS):
        chunk = requested[start:start + MAX_UNIQUE_BOOKS]
        chunk_set = set(chunk)
        body = [{"token_id": token} for token in chunk]
        request_timeout = _remaining_timeout(deadline, timeout)
        if client is None:
            response = httpx.post(url, json=body, timeout=request_timeout)
        else:
            response = client.post(url, json=body, timeout=request_timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("CLOB /books response is not a list")

        for row in payload:
            if not isinstance(row, dict):
                raise ValueError("CLOB /books response contains a non-object row")
            asset_id = row.get("asset_id")
            if not isinstance(asset_id, str) or not asset_id.strip():
                raise ValueError("CLOB /books row has malformed asset_id")
            if asset_id not in chunk_set:
                raise ValueError("CLOB /books returned an unexpected asset_id")
            if mapped[asset_id] is not None:
                raise ValueError("CLOB /books returned duplicate asset_id")
            mapped[asset_id] = row
    return mapped


__all__ = ["BOOKS_URL", "MAX_UNIQUE_BOOKS", "fetch_books"]
