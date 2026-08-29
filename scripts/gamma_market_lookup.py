#!/usr/bin/env python3
"""Exact, fail-closed Gamma market identity lookup.

Question lookup is deliberately exact. Public search is the fast path; the
official market keyset is the exhaustive fallback. A network/shape/cursor
failure raises instead of turning partial coverage into "not found".
"""

from __future__ import annotations

import re
import time
from typing import Any

import httpx


GAMMA_HOST = "https://gamma-api.polymarket.com"
PAGE_LIMIT = 100
MAX_KEYSET_PAGES = 1000
REQUEST_RETRIES = 3


class GammaLookupError(RuntimeError):
    """Gamma could not produce an affirmative, trustworthy lookup result."""


class GammaMarketNotFound(GammaLookupError):
    """The requested identity was absent after complete coverage."""


class GammaMarketAmbiguous(GammaLookupError):
    """More than one live market matched the requested exact identity."""


def looks_like_slug(value: str) -> bool:
    """Return whether *value* has the lexical shape of a Gamma slug."""
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value.strip()))


def _question_key(value: str) -> str:
    return " ".join(value.split()).casefold()


def _request_json(
    client: httpx.Client,
    path: str,
    params: dict[str, str],
) -> Any:
    """GET one Gamma payload with bounded retries for transient failures."""
    last_error: Exception | None = None
    for attempt in range(REQUEST_RETRIES):
        try:
            response = client.get(f"{GAMMA_HOST}{path}", params=params)
            if response.status_code == 429 or response.status_code >= 500:
                raise RuntimeError(f"transient HTTP {response.status_code}")
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < REQUEST_RETRIES:
                time.sleep(0.25 * (2 ** attempt))
    raise GammaLookupError(
        f"Gamma {path} failed after {REQUEST_RETRIES} attempts"
    ) from last_error


def _active_market(market: Any, *, source: str) -> dict:
    if not isinstance(market, dict):
        raise GammaLookupError(f"{source} returned a non-object market")
    market_id = str(market.get("id") or "").strip()
    question = market.get("question")
    slug = market.get("slug")
    if not market_id or not isinstance(question, str) or not question.strip():
        raise GammaLookupError(f"{source} returned a market without stable identity")
    if not isinstance(slug, str) or not slug.strip():
        raise GammaLookupError(f"{source} returned market {market_id} without a slug")
    if market.get("active") is not True or market.get("closed") is not False:
        raise GammaLookupError(f"{source} returned non-live market {market_id}")
    return market


def _single_exact_market(
    markets: list[dict],
    *,
    question: str | None = None,
    slug: str | None = None,
    source: str,
) -> dict:
    exact: dict[str, dict] = {}
    qkey = _question_key(question) if question is not None else None
    for raw_market in markets:
        market = _active_market(raw_market, source=source)
        if slug is not None and market["slug"] != slug:
            continue
        if qkey is not None and _question_key(market["question"]) != qkey:
            continue
        exact[str(market["id"])] = market
    if not exact:
        identity = f"slug {slug!r}" if slug is not None else f"question {question!r}"
        raise GammaMarketNotFound(f"no live market matched exact {identity} via {source}")
    if len(exact) != 1:
        raise GammaMarketAmbiguous(
            f"{len(exact)} live markets matched exact identity via {source}: "
            + ", ".join(sorted(exact))
        )
    return next(iter(exact.values()))


def _canonical_refetch(
    client: httpx.Client,
    market_id: str,
    *,
    question: str | None = None,
    slug: str | None = None,
) -> dict:
    payload = _request_json(client, "/markets", {"id": market_id})
    if not isinstance(payload, list):
        raise GammaLookupError("Gamma market-id refetch returned a non-list payload")
    matching_id = [
        m for m in payload
        if isinstance(m, dict) and str(m.get("id") or "") == market_id
    ]
    return _single_exact_market(
        matching_id,
        question=question,
        slug=slug,
        source=f"canonical id={market_id} refetch",
    )


def _public_search_exact(client: httpx.Client, question: str) -> dict | None:
    """Return an exact public-search candidate, or None so keyset can run."""
    try:
        payload = _request_json(client, "/public-search", {"q": question})
    except GammaLookupError:
        return None
    if not isinstance(payload, dict):
        return None
    raw_events = payload.get("events")
    if not isinstance(raw_events, list):
        return None

    candidates: list[dict] = []
    top_level = payload.get("markets")
    if isinstance(top_level, list):
        candidates.extend(m for m in top_level if isinstance(m, dict))
    for event in raw_events:
        if not isinstance(event, dict):
            return None
        markets = event.get("markets")
        if not isinstance(markets, list):
            return None
        candidates.extend(m for m in markets if isinstance(m, dict))

    qkey = _question_key(question)
    ids = {
        str(m.get("id") or "").strip()
        for m in candidates
        if str(m.get("id") or "").strip()
        and _question_key(str(m.get("question") or "")) == qkey
    }
    if not ids:
        return None
    if len(ids) != 1:
        raise GammaMarketAmbiguous(
            f"public search returned {len(ids)} exact-question market IDs: "
            + ", ".join(sorted(ids))
        )
    return _canonical_refetch(client, next(iter(ids)), question=question)


def _keyset_question_lookup(client: httpx.Client, question: str) -> dict:
    """Exhaust active/open keyset pages and distinguish miss from partial failure."""
    cursor: str | None = None
    seen_cursors: set[str] = set()
    seen_ids: set[str] = set()
    matches: list[dict] = []
    qkey = _question_key(question)
    markets_seen = 0

    for page_number in range(1, MAX_KEYSET_PAGES + 1):
        params = {
            "active": "true",
            "closed": "false",
            "limit": str(PAGE_LIMIT),
            "order": "volume24hr",
            "ascending": "false",
        }
        if cursor is not None:
            params["after_cursor"] = cursor
        payload = _request_json(client, "/markets/keyset", params)
        if not isinstance(payload, dict) or not isinstance(payload.get("markets"), list):
            raise GammaLookupError("Gamma keyset response omitted its markets list")
        batch = payload["markets"]
        if len(batch) > PAGE_LIMIT:
            raise GammaLookupError("Gamma keyset returned more markets than requested")
        for raw_market in batch:
            market = _active_market(raw_market, source="Gamma market keyset")
            market_id = str(market["id"])
            if market_id in seen_ids:
                raise GammaLookupError(f"Gamma keyset repeated market id {market_id}")
            seen_ids.add(market_id)
            markets_seen += 1
            if _question_key(market["question"]) == qkey:
                matches.append(market)

        raw_next = payload.get("next_cursor")
        if raw_next not in (None, "") and not isinstance(raw_next, str):
            raise GammaLookupError("Gamma keyset returned a malformed next_cursor")
        next_cursor = raw_next if isinstance(raw_next, str) and raw_next else None
        if next_cursor is None:
            if not matches:
                raise GammaMarketNotFound(
                    f"exact question absent after COMPLETE keyset coverage "
                    f"({markets_seen} live markets, {page_number} pages)"
                )
            market = _single_exact_market(
                matches, question=question, source="complete Gamma market keyset"
            )
            return _canonical_refetch(client, str(market["id"]), question=question)
        if not batch:
            raise GammaLookupError("Gamma keyset returned an empty page with a cursor")
        if next_cursor == cursor or next_cursor in seen_cursors:
            raise GammaLookupError("Gamma keyset repeated a cursor; coverage is partial")
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    raise GammaLookupError(
        f"Gamma keyset exceeded {MAX_KEYSET_PAGES} pages; coverage is partial"
    )


def lookup_active_market(
    *,
    slug: str | None = None,
    question: str | None = None,
    client: httpx.Client | None = None,
) -> dict:
    """Resolve exactly one active/open market by slug or exact question."""
    if (slug is None) == (question is None):
        raise ValueError("provide exactly one of slug or question")
    identity = slug if slug is not None else question
    assert identity is not None
    identity = identity.strip()
    if not identity:
        raise ValueError("market identity must not be blank")

    owns_client = client is None
    active_client = client or httpx.Client(timeout=20.0)
    try:
        if slug is not None:
            payload = _request_json(active_client, "/markets", {"slug": identity})
            if not isinstance(payload, list):
                raise GammaLookupError("Gamma slug lookup returned a non-list payload")
            return _single_exact_market(
                payload, slug=identity, source="direct Gamma slug lookup"
            )

        public_match = _public_search_exact(active_client, identity)
        if public_match is not None:
            return public_match
        return _keyset_question_lookup(active_client, identity)
    finally:
        if owns_client:
            active_client.close()


def lookup_active_market_identifier(
    value: str,
    *,
    client: httpx.Client | None = None,
) -> dict:
    """Resolve the CLI convention: lexical slug, otherwise exact question."""
    if looks_like_slug(value):
        return lookup_active_market(slug=value.strip(), client=client)
    return lookup_active_market(question=value.strip(), client=client)
