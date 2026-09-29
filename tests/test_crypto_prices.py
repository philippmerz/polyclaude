"""Offline regressions for validated primary/fallback crypto quotes."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import _crypto_prices as prices  # noqa: E402
import bankroll  # noqa: E402


NOW = 1_000_000
IDS = ["ethereum", "polygon-ecosystem-token"]


def _response(status: int, payload: object, url: str) -> httpx.Response:
    return httpx.Response(
        status,
        json=payload,
        request=httpx.Request("GET", url),
    )


def _llama_rows(**overrides: object) -> dict:
    rows = {
        "coingecko:ethereum": {
            "price": 2700.0,
            "timestamp": NOW - 12,
            "confidence": 0.99,
        },
        "coingecko:polygon-ecosystem-token": {
            "price": 0.12,
            "timestamp": NOW - 20,
            "confidence": 0.99,
        },
    }
    for key, value in overrides.items():
        rows["coingecko:ethereum"][key] = value
    return {"coins": rows}


def test_prefers_complete_fresh_coingecko_batch(monkeypatch) -> None:
    calls: list[tuple[str, dict]] = []

    def get(url: str, **kwargs):
        calls.append((url, kwargs))
        return _response(200, {
            "ethereum": {"usd": 2701, "last_updated_at": NOW - 5},
            "polygon-ecosystem-token": {
                "usd": 0.121,
                "last_updated_at": NOW - 6,
            },
        }, url)

    monkeypatch.setattr(prices.httpx, "get", get)
    batch = prices.fetch_usd_prices(IDS, now=NOW)

    assert batch.prices == {"ethereum": 2701.0, "polygon-ecosystem-token": 0.121}
    assert batch.source_label == "CoinGecko"
    assert batch.warnings == ()
    assert len(calls) == 1
    assert calls[0][1]["params"]["include_last_updated_at"] == "true"


def test_403_uses_complete_fresh_defillama_batch(monkeypatch) -> None:
    calls: list[str] = []

    def get(url: str, **_kwargs):
        calls.append(url)
        if "coingecko.com" in url:
            return _response(403, {"error": "blocked"}, url)
        return _response(200, _llama_rows(), url)

    monkeypatch.setattr(prices.httpx, "get", get)
    batch = prices.fetch_usd_prices(IDS, now=NOW)

    assert batch.prices["ethereum"] == 2700.0
    assert batch.prices["polygon-ecosystem-token"] == 0.12
    assert batch.source_label == "DefiLlama"
    assert "CoinGecko unavailable" in batch.warnings[0]
    assert "oldest quote timestamp 999980" in batch.warnings[0]
    assert len(calls) == 2
    assert calls[1].endswith(
        "coingecko:ethereum,coingecko:polygon-ecosystem-token")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("price", "nan", "invalid price"),
        ("timestamp", NOW - prices.MAX_AGE_SECONDS - 1, "stale quote"),
        ("timestamp", NOW + prices.MAX_FUTURE_SKEW_SECONDS + 1, "future quote"),
        ("confidence", 0.89, "outside"),
        ("confidence", 1.01, "outside"),
        ("timestamp", NOW - 1.5, "invalid timestamp"),
        ("timestamp", str(NOW - 1), "invalid timestamp"),
    ],
)
def test_rejects_invalid_fallback_quote(
    monkeypatch, field: str, value: object, message: str,
) -> None:
    def get(url: str, **_kwargs):
        if "coingecko.com" in url:
            return _response(403, {"error": "blocked"}, url)
        return _response(200, _llama_rows(**{field: value}), url)

    monkeypatch.setattr(prices.httpx, "get", get)
    with pytest.raises(prices.PriceFetchError, match=message):
        prices.fetch_usd_prices(IDS, now=NOW)


def test_missing_fallback_member_rejects_entire_batch(monkeypatch) -> None:
    payload = _llama_rows()
    del payload["coins"]["coingecko:polygon-ecosystem-token"]

    def get(url: str, **_kwargs):
        if "coingecko.com" in url:
            return _response(200, {
                "ethereum": {"usd": 2701, "last_updated_at": NOW - 5},
            }, url)
        return _response(200, payload, url)

    monkeypatch.setattr(prices.httpx, "get", get)
    with pytest.raises(prices.PriceFetchError, match="missing coingecko:polygon"):
        prices.fetch_usd_prices(IDS, now=NOW)


def test_both_source_failures_are_visible(monkeypatch) -> None:
    def get(url: str, **_kwargs):
        return _response(503, {"error": "down"}, url)

    monkeypatch.setattr(prices.httpx, "get", get)
    with pytest.raises(prices.PriceFetchError) as exc:
        prices.fetch_usd_prices(["ethereum"], now=NOW)
    assert "CoinGecko failed" in str(exc.value)
    assert "DefiLlama failed" in str(exc.value)


def test_invalid_asset_id_fails_before_network(monkeypatch) -> None:
    monkeypatch.setattr(
        prices.httpx,
        "get",
        lambda *_args, **_kwargs: pytest.fail("network call is forbidden"),
    )
    with pytest.raises(prices.PriceFetchError, match="invalid CoinGecko asset"):
        prices.fetch_usd_prices(["ethereum/bad"], now=NOW)


def test_bankroll_maps_validated_fallback_batch_and_surfaces_source(monkeypatch) -> None:
    warning = "CoinGecko unavailable (403); using fresh DefiLlama fallback"
    batch = prices.PriceBatch(
        {
            "ethereum": 2700.0,
            "polygon-ecosystem-token": 0.12,
            "arbitrum": 0.21,
        },
        {
            "ethereum": "DefiLlama",
            "polygon-ecosystem-token": "DefiLlama",
            "arbitrum": "DefiLlama",
        },
        {
            "ethereum": NOW - 1,
            "polygon-ecosystem-token": NOW - 1,
            "arbitrum": NOW - 1,
        },
        (warning,),
    )
    monkeypatch.setattr(bankroll, "fetch_usd_prices", lambda *_args, **_kwargs: batch)
    warnings: list[str] = []

    assert bankroll.native_prices(warnings) == {
        "ETH": 2700.0,
        "POL": 0.12,
        "ARB": 0.21,
    }
    assert warnings == [f"crypto prices: {warning}"]
