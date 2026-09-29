"""Validated USD crypto quotes with a bounded separate-source fallback.

CoinGecko is the primary aggregate used by the repository. DefiLlama's coins
API is the fallback because it accepts the same CoinGecko asset identifiers and
returns explicit quote timestamps and confidence. Callers receive a complete
batch or an exception: a missing/stale member must never silently become zero.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
import time
from typing import Iterable

import httpx


COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
DEFILLAMA_URL = "https://coins.llama.fi/prices/current/"
MAX_AGE_SECONDS = 15 * 60
MAX_FUTURE_SKEW_SECONDS = 60
MIN_DEFILLAMA_CONFIDENCE = 0.90
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class PriceFetchError(RuntimeError):
    """No complete, validated price batch was available."""


@dataclass(frozen=True)
class PriceBatch:
    prices: dict[str, float]
    sources: dict[str, str]
    timestamps: dict[str, int]
    warnings: tuple[str, ...] = ()

    @property
    def source_label(self) -> str:
        return "+".join(sorted(set(self.sources.values())))


def _requested_ids(ids: Iterable[str]) -> list[str]:
    raw = list(ids)
    invalid = [asset_id for asset_id in raw
               if not isinstance(asset_id, str) or not _ID_RE.fullmatch(asset_id)]
    if invalid:
        raise PriceFetchError(f"invalid CoinGecko asset id(s): {invalid!r}")
    return list(dict.fromkeys(raw))


def _price(value: object, asset_id: str, source: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{source} {asset_id}: boolean price")
    price = float(value)
    if not math.isfinite(price) or price <= 0:
        raise ValueError(f"{source} {asset_id}: invalid price {value!r}")
    return price


def _timestamp(value: object, asset_id: str, source: str, now: int) -> int:
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(float(value)) or not float(value).is_integer()):
        raise ValueError(f"{source} {asset_id}: invalid timestamp {value!r}")
    timestamp = int(value)
    age = now - timestamp
    if age > MAX_AGE_SECONDS:
        raise ValueError(f"{source} {asset_id}: stale quote ({age}s old)")
    if age < -MAX_FUTURE_SKEW_SECONDS:
        raise ValueError(f"{source} {asset_id}: future quote ({-age}s ahead)")
    return timestamp


def _brief(error: Exception) -> str:
    return " ".join(str(error).split())[:180]


def _coingecko(ids: list[str], timeout: float, now: int) -> tuple[dict[str, float], dict[str, int]]:
    response = httpx.get(
        COINGECKO_URL,
        params={
            "ids": ",".join(ids),
            "vs_currencies": "usd",
            "include_last_updated_at": "true",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("CoinGecko payload is not an object")

    prices: dict[str, float] = {}
    timestamps: dict[str, int] = {}
    for asset_id in ids:
        row = payload.get(asset_id)
        if not isinstance(row, dict):
            raise ValueError(f"CoinGecko missing {asset_id}")
        prices[asset_id] = _price(row.get("usd"), asset_id, "CoinGecko")
        timestamps[asset_id] = _timestamp(
            row.get("last_updated_at"), asset_id, "CoinGecko", now)
    return prices, timestamps


def _defillama(ids: list[str], timeout: float, now: int) -> tuple[dict[str, float], dict[str, int]]:
    keys = [f"coingecko:{asset_id}" for asset_id in ids]
    response = httpx.get(DEFILLAMA_URL + ",".join(keys), timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("coins") if isinstance(payload, dict) else None
    if not isinstance(rows, dict):
        raise ValueError("DefiLlama payload has no coins object")

    prices: dict[str, float] = {}
    timestamps: dict[str, int] = {}
    for asset_id, key in zip(ids, keys):
        row = rows.get(key)
        if not isinstance(row, dict):
            raise ValueError(f"DefiLlama missing {key}")
        confidence = row.get("confidence")
        if isinstance(confidence, bool):
            raise ValueError(f"DefiLlama {asset_id}: boolean confidence")
        confidence = float(confidence)
        if (not math.isfinite(confidence)
                or not MIN_DEFILLAMA_CONFIDENCE <= confidence <= 1.0):
            raise ValueError(
                f"DefiLlama {asset_id}: confidence {confidence!r} outside "
                f"[{MIN_DEFILLAMA_CONFIDENCE:.2f}, 1.00]")
        prices[asset_id] = _price(row.get("price"), asset_id, "DefiLlama")
        timestamps[asset_id] = _timestamp(
            row.get("timestamp"), asset_id, "DefiLlama", now)
    return prices, timestamps


def fetch_usd_prices(
    ids: Iterable[str], *, timeout: float = 15.0, now: int | None = None,
) -> PriceBatch:
    """Return a complete fresh batch, preferring CoinGecko over DefiLlama.

    Asset identifiers are CoinGecko IDs. Both sources must supply every member
    of a requested batch, and all quotes must be finite, positive and recent.
    """
    requested = _requested_ids(ids)
    if not requested:
        return PriceBatch({}, {}, {})
    checked_at = int(time.time()) if now is None else int(now)

    try:
        prices, timestamps = _coingecko(requested, timeout, checked_at)
        return PriceBatch(
            prices,
            {asset_id: "CoinGecko" for asset_id in requested},
            timestamps,
        )
    except Exception as primary_error:
        primary = _brief(primary_error)

    try:
        prices, timestamps = _defillama(requested, timeout, checked_at)
        oldest = min(timestamps.values())
        return PriceBatch(
            prices,
            {asset_id: "DefiLlama" for asset_id in requested},
            timestamps,
            (f"CoinGecko unavailable ({primary}); using fresh DefiLlama "
             f"fallback (oldest quote timestamp {oldest})",),
        )
    except Exception as fallback_error:
        raise PriceFetchError(
            f"CoinGecko failed ({primary}); DefiLlama failed "
            f"({_brief(fallback_error)})") from fallback_error
