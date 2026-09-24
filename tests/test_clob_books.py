from __future__ import annotations

import json
import httpx
import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from clob_books import fetch_books  # noqa: E402


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_maps_by_asset_id_and_preserves_missing_explicitly():
    tokens = ["a", "b", "c"]

    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/books"
        assert json.loads(request.content) == [{"token_id": token} for token in tokens]
        return httpx.Response(200, json=[
            {"asset_id": "c", "asks": []},
            {"asset_id": "a", "asks": [{"price": "0.2"}]},
        ])

    with _client(handler) as client:
        result = fetch_books(tokens, client=client)
    assert list(result) == tokens
    assert result["a"]["asset_id"] == "a"
    assert result["b"] is None
    assert result["c"]["asset_id"] == "c"


@pytest.mark.parametrize("payload", [
    {"asset_id": "a"},
    ["a"],
    [{"asset_id": ""}],
])
def test_rejects_malformed_response_rows(payload):
    def handler(_request):
        return httpx.Response(200, json=payload)

    with _client(handler) as client:
        with pytest.raises(ValueError):
            fetch_books(["a"], client=client)


def test_rejects_duplicate_asset_ids():
    def handler(_request):
        return httpx.Response(200, json=[{"asset_id": "a"}, {"asset_id": "a"}])

    with _client(handler) as client:
        with pytest.raises(ValueError, match="duplicate"):
            fetch_books(["a"], client=client)


def test_rejects_unexpected_asset_id_instead_of_positional_fallback():
    def handler(_request):
        return httpx.Response(200, json=[{"asset_id": "other"}])

    with _client(handler) as client:
        with pytest.raises(ValueError, match="unexpected"):
            fetch_books(["a"], client=client)


def test_rejects_duplicate_requested_ids():
    with pytest.raises(ValueError, match="token_ids contain duplicates"):
        fetch_books(["a", "a"])


def test_chunks_above_endpoint_limit_and_merges_by_asset_id():
    tokens = [str(i) for i in range(501)]
    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        return httpx.Response(200, json=[
            {"asset_id": row["token_id"], "asks": []}
            for row in reversed(body)
        ])

    with _client(handler) as client:
        result = fetch_books(tokens, client=client)

    assert [len(call) for call in calls] == [500, 1]
    assert list(result) == tokens
    assert all(result[token]["asset_id"] == token for token in tokens)


def test_http_errors_propagate():
    def handler(_request):
        return httpx.Response(503)

    with _client(handler) as client:
        with pytest.raises(httpx.HTTPStatusError):
            fetch_books(["a"], client=client)


def test_deadline_is_checked_before_request():
    with pytest.raises(TimeoutError, match="deadline"):
        fetch_books(["a"], deadline=0.0)
