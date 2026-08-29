"""Polymarket cross-market consistency scanner.

Finds neg-risk event groups (mutually-exclusive multi-outcome events on
Polymarket) where the YES probabilities don't sum to ~1 — a structural
arb signal. Two directions:

  • sum(YES) < 1 → directional missing-mass signal. Buying every listed
    YES is not guaranteed to pay when an omitted/field outcome can win.

  • sum(YES) > 1 → arb by buying ONE NO of every contender. Exactly one
    contender wins, so N-1 NO tokens pay $1 each. Total payout = N-1.
    Total cost = sum(NO) = N - sum(YES). Profit = (N - 1) - (N - sum(YES))
    - fees = sum(YES) - 1 - fees.

Either direction profits when |1 - sum(YES)| > fee-eaten threshold.

CRITICAL: gamma-api outcomePrices midpoints are NOT executable. On thin
markets they sit between a $0.01 stub bid and a real ask, producing a
displayed mid (e.g. 0.46) that has no live counter-side. To get real
fillable edge we MUST fetch CLOB orderbook asks for every member. The
scanner runs in two passes:

  pass 1: a bounded, volume-ranked Gamma keyset slice flags groups whose
          displayed yes_sum violates consistency. Coverage metadata states
          the exact filters/caps and whether the cursor was exhausted.
  pass 2: within explicit group/leg/deadline bounds, cross-check Gamma
          identity against CLOB market info and walk every structural
          buy-all-NO basket. Any unquoted or failed structural group keeps
          analysis explicitly incomplete.

All live observations are sequential and non-atomic. They are provisional
revalidation prompts, never executable/REAL claims or instructions to trade.

Output: logs/polymarket_consistency_<ts>.md + logs/polymarket_consistency_latest.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
from pathlib import Path

import httpx

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
OUT_DIR = _REPO_ROOT / "logs"

POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"
POLYMARKET_CLOB = "https://clob.polymarket.com"
import pm_fees  # per-market takerBaseFee; see pm_fees.py (0.072 was never a live rate)

# How big the consistency violation must be (after-fee, after-slippage net)
# to surface in Telegram. Below this, the violation is logged but not alerted.
TELEGRAM_THRESHOLD_NET = 0.02  # 2% net edge after fees

# How many YES-sum deviation pp to log at all
LOG_THRESHOLD_GROSS = 0.005  # 0.5% gross deviation

# Gamma event pages embed every child market.  A nominally small event page can
# therefore be several MiB; keep pages small and put hard guards around the
# explicit full-diagnostic mode.  The default is an ROI-ranked *slice*, not a
# claim to have enumerated every event on the exchange.
EVENT_PAGE_LIMIT = 20
EVENT_PAGE_RETRIES = 3
DEFAULT_MAX_MARKETS = 5_000
DEFAULT_MAX_PAGES = 500
DEFAULT_MAX_BYTES = 384 * 1024 * 1024
DEFAULT_END_DATE_MAX = "2027-01-05T23:59:59Z"
SPORTS_TAG_ID = "1"  # sports have a dedicated scanner; keep this scope explicit
MAX_BOOK_AGE_SECONDS = 300.0
DEFAULT_MAX_LIVE_GROUPS = 20
DEFAULT_MAX_LIVE_LEGS = 200
DEFAULT_LIVE_BUDGET_SECONDS = 90.0
STREAM_CHUNK_BYTES = 64 * 1024
FEE_QUANTUM = Decimal("0.00001")


@dataclass(frozen=True)
class UniverseSnapshot:
    markets: list[dict]
    coverage: dict


@dataclass(frozen=True)
class _StreamPageResult:
    payload: dict | None
    bytes_read: int
    body_bytes_retained: int
    cap_exceeded: bool
    error: Exception | None = None


def _telegram(text: str) -> None:
    try:
        subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            cwd=_REPO_ROOT, check=False, timeout=15, capture_output=True,
        )
    except Exception:
        pass


def _stream_event_page(params: dict[str, str], max_body_bytes: int) -> _StreamPageResult:
    """Read at most ``max_body_bytes`` of one Gamma page into retained memory.

    One bounded probe chunk may cross the cumulative transfer budget when the
    server omits Content-Length.  That entire chunk is counted in
    ``bytes_read`` but is never appended to the retained body, so telemetry is
    honest and peak retained page memory remains bounded by ``max_body_bytes``.
    """
    if max_body_bytes <= 0:
        return _StreamPageResult(None, 0, 0, True)
    body = bytearray()
    bytes_read = 0
    try:
        with httpx.stream(
            "GET",
            f"{POLYMARKET_GAMMA}/events/keyset",
            params=params,
            headers={"Accept-Encoding": "identity"},
            timeout=30,
        ) as response:
            response.raise_for_status()
            raw_length = getattr(response, "headers", {}).get("content-length")
            if raw_length is not None:
                try:
                    content_length = int(raw_length)
                except (TypeError, ValueError) as exc:
                    return _StreamPageResult(
                        None, 0, 0, False,
                        ValueError("malformed event-page Content-Length"),
                    )
                if content_length < 0:
                    return _StreamPageResult(
                        None, 0, 0, False,
                        ValueError("malformed event-page Content-Length"),
                    )
                if content_length > max_body_bytes:
                    return _StreamPageResult(None, 0, 0, True)

            chunk_size = max(1, min(STREAM_CHUNK_BYTES, max_body_bytes + 1))
            for chunk in response.iter_bytes(chunk_size=chunk_size):
                if not chunk:
                    continue
                bytes_read += len(chunk)
                if len(body) + len(chunk) > max_body_bytes:
                    return _StreamPageResult(
                        None, bytes_read, len(body), True
                    )
                body.extend(chunk)
    except Exception as exc:
        return _StreamPageResult(None, bytes_read, len(body), False, exc)

    try:
        payload = json.loads(body)
    except Exception as exc:
        return _StreamPageResult(None, bytes_read, len(body), False, exc)
    return _StreamPageResult(payload, bytes_read, len(body), False)


def _remaining_timeout(deadline: float | None, maximum: float) -> float:
    if deadline is None:
        return maximum
    remaining = deadline - time.monotonic()
    if remaining <= 0.0:
        raise TimeoutError("live quote deadline exhausted")
    return min(maximum, remaining)


def _check_deadline(deadline: float | None) -> None:
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("live quote deadline exhausted")


def _retry_sleep(seconds: float, deadline: float | None) -> None:
    if deadline is not None:
        remaining = deadline - time.monotonic()
        if remaining <= seconds:
            raise TimeoutError("live quote deadline exhausted")
    time.sleep(seconds)


def _strict_hex_id(value: object, field: str) -> str:
    normalized = str(value or "").strip()
    if len(normalized) != 66 or not normalized.startswith("0x"):
        raise ValueError(f"malformed {field}")
    try:
        int(normalized[2:], 16)
    except ValueError as exc:
        raise ValueError(f"malformed {field}") from exc
    return normalized


def _json_array(value: object, field: str) -> list:
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except Exception as exc:
        raise ValueError(f"malformed {field}") from exc
    if not isinstance(parsed, list):
        raise ValueError(f"malformed {field}")
    return parsed


def _finite_number(value: object, field: str, *, minimum: float = 0.0,
                   maximum: float | None = None) -> float:
    if isinstance(value, bool):
        raise ValueError(f"malformed {field}")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"malformed {field}") from exc
    if not math.isfinite(parsed) or parsed < minimum:
        raise ValueError(f"malformed {field}")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"malformed {field}")
    return parsed


def _strict_open_market(raw: dict) -> bool:
    """Return whether Gamma affirmatively describes a currently tradable leg.

    Missing/non-boolean state is a schema error, not a false value.  The caller
    handles that distinction so a malformed member cannot silently disappear
    from a neg-risk basket.
    """
    fields = ("active", "closed", "archived", "acceptingOrders", "enableOrderBook")
    if any(not isinstance(raw.get(field), bool) for field in fields):
        raise ValueError("malformed market trading status")
    return (
        raw["active"] is True
        and raw["closed"] is False
        and raw["archived"] is False
        and raw["acceptingOrders"] is True
        and raw["enableOrderBook"] is True
    )


def _normalize_neg_risk_market(raw: dict, parent: dict) -> dict:
    """Keep only fields needed downstream and prove binary token identity."""
    market_id = str(raw.get("id") or "").strip()
    condition_id = _strict_hex_id(raw.get("conditionId"), "conditionId")
    question = str(raw.get("question") or "").strip()
    if not market_id or not question:
        raise ValueError("missing market identity")
    if raw.get("negRisk") is not True:
        raise ValueError("market/event neg-risk mismatch")
    parent_group_id = _strict_hex_id(
        parent.get("negRiskMarketID"), "event negRiskMarketID"
    )
    market_group_id = _strict_hex_id(
        raw.get("negRiskMarketID"), "market negRiskMarketID"
    )
    if market_group_id != parent_group_id:
        raise ValueError("market/event neg-risk adapter mismatch")

    outcomes = _json_array(raw.get("outcomes"), "outcomes")
    prices = _json_array(raw.get("outcomePrices"), "outcomePrices")
    tokens = _json_array(raw.get("clobTokenIds"), "clobTokenIds")
    if not (len(outcomes) == len(prices) == len(tokens) == 2):
        raise ValueError("binary outcome/token cardinality mismatch")

    indexed: dict[str, tuple[float, str]] = {}
    for outcome, price_raw, token_raw in zip(outcomes, prices, tokens):
        label = str(outcome).strip().casefold()
        if label not in {"yes", "no"} or label in indexed:
            raise ValueError("outcomes must be unique Yes/No")
        price = _finite_number(price_raw, "outcome price", maximum=1.0)
        token = str(token_raw).strip()
        if not token.isdigit() or int(token) <= 0:
            raise ValueError("malformed CLOB token id")
        indexed[label] = (price, token)
    if set(indexed) != {"yes", "no"}:
        raise ValueError("outcomes must be exactly Yes/No")
    if indexed["yes"][1] == indexed["no"][1]:
        raise ValueError("duplicate CLOB token id")

    liquidity = _finite_number(
        raw.get("liquidityNum") or 0.0, "liquidityNum"
    )
    compact = {
        "id": market_id,
        "conditionId": condition_id,
        "question": question,
        "slug": raw.get("slug"),
        "groupItemTitle": raw.get("groupItemTitle"),
        "active": True,
        "closed": False,
        "archived": False,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "negRisk": True,
        "negRiskMarketID": market_group_id,
        "outcomes": ["Yes", "No"],
        "outcomePrices": [indexed["yes"][0], indexed["no"][0]],
        "clobTokenIds": [indexed["yes"][1], indexed["no"][1]],
        "liquidityNum": liquidity,
        "endDateIso": raw.get("endDateIso"),
        "endDate": raw.get("endDate"),
        "orderMinSize": raw.get("orderMinSize"),
        "feesEnabled": raw.get("feesEnabled"),
        "feeSchedule": raw.get("feeSchedule"),
        "takerBaseFee": raw.get("takerBaseFee"),
        "events": [parent],
    }
    return compact


def fetch_universe(
    max_markets: int | None = DEFAULT_MAX_MARKETS,
    *,
    end_date_min: str,
    end_date_max: str = DEFAULT_END_DATE_MAX,
    exclude_sports: bool = True,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> UniverseSnapshot:
    """Fetch an explicit top-volume ROI slice through official keyset pages.

    ``max_markets`` counts affirmatively open child markets across all fetched
    events.  The event that crosses the cap is completed, so an API basket is
    never split.  ``None`` requests cursor exhaustion, but page/byte guards
    remain mandatory and turn the result into an explicitly incomplete slice
    rather than allowing an unbounded crawl.

    Only compact, validated neg-risk members are retained.  Request/schema
    failures raise; deterministic resource caps return partial coverage marked
    ``coverage_complete=false`` so a caller cannot print a comprehensive zero.
    """
    if max_markets is not None and max_markets <= 0:
        raise ValueError("max_markets must be positive or None")
    if max_pages <= 0 or max_bytes <= 0:
        raise ValueError("page and byte guards must be positive")

    out: list[dict] = []
    seen_ids: set[str] = set()
    seen_event_ids: set[str] = set()
    seen_cursors: set[str] = set()
    cursor: str | None = None
    pages_fetched = 0
    events_fetched = 0
    events_processed = 0
    open_markets_scanned = 0
    invalid_neg_risk_events = 0
    missing_event_neg_risk_treated_false = 0
    invalid_reasons: dict[str, int] = defaultdict(int)
    raw_response_bytes = 0
    accepted_response_bytes = 0
    max_page_bytes = 0
    max_stream_body_bytes = 0
    cursor_exhausted = False
    stop_reason: str | None = None
    last_rank_volume = math.inf

    while True:
        if pages_fetched >= max_pages:
            stop_reason = "page_cap"
            break
        if raw_response_bytes >= max_bytes:
            stop_reason = "byte_cap"
            break
        params = {
            "closed": "false",
            "limit": str(EVENT_PAGE_LIMIT),
            "order": "volume24hr",
            "ascending": "false",
            "end_date_min": end_date_min,
            "end_date_max": end_date_max,
        }
        if exclude_sports:
            params["exclude_tag_id"] = SPORTS_TAG_ID
        if cursor is not None:
            params["after_cursor"] = cursor
        last_error: Exception | None = None
        payload = None
        page_bytes = 0
        for attempt in range(EVENT_PAGE_RETRIES):
            result = _stream_event_page(params, max_bytes - raw_response_bytes)
            raw_response_bytes += result.bytes_read
            max_stream_body_bytes = max(
                max_stream_body_bytes, result.body_bytes_retained
            )
            if result.cap_exceeded:
                stop_reason = "byte_cap"
                last_error = None
                payload = None
                break
            if result.error is None:
                payload = result.payload
                page_bytes = result.body_bytes_retained
                break
            last_error = result.error
            if raw_response_bytes >= max_bytes:
                stop_reason = "byte_cap"
                break
            if attempt + 1 < EVENT_PAGE_RETRIES:
                time.sleep(0.5 * (2 ** attempt))
        if payload is None and stop_reason == "byte_cap":
            break
        if payload is None:
            raise RuntimeError(
                f"active-event universe fetch failed after cursor={cursor!r}; "
                "refusing to scan a partial universe"
            ) from last_error
        pages_fetched += 1
        accepted_response_bytes += page_bytes
        max_page_bytes = max(max_page_bytes, page_bytes)
        if not isinstance(payload, dict):
            raise RuntimeError(
                f"active-event keyset returned {type(payload).__name__}; "
                "refusing to scan a partial universe"
            )
        batch = payload.get("events")
        if not isinstance(batch, list):
            raise RuntimeError(
                "active-event keyset omitted its events list; refusing to "
                "scan a partial universe"
            )
        if not batch:
            if payload.get("next_cursor") not in (None, ""):
                raise RuntimeError(
                    "active-event keyset returned an empty page with a cursor"
                )
            cursor_exhausted = True
            break

        events_fetched += len(batch)
        next_cursor = payload.get("next_cursor")
        if next_cursor not in (None, "") and not isinstance(next_cursor, str):
            raise RuntimeError(
                "active-event keyset returned a malformed next_cursor; "
                "refusing to scan a partial universe"
            )

        reached_cap = False
        cap_event_index = -1
        for event_index, event in enumerate(batch):
            if not isinstance(event, dict):
                raise RuntimeError("active-event keyset returned a malformed event")
            event_state = (event.get("active"), event.get("closed"), event.get("archived"))
            if any(not isinstance(value, bool) for value in event_state):
                raise RuntimeError("active-event keyset returned malformed event status")
            if event_state != (True, False, False):
                continue
            event_id = str(event.get("id") or "").strip()
            if not event_id:
                raise RuntimeError("active-event keyset returned an event without id")
            if event_id in seen_event_ids:
                raise RuntimeError("active-event keyset repeated an event id")
            seen_event_ids.add(event_id)
            events_processed += 1

            volume24hr = _finite_number(
                event.get("volume24hr") or 0.0, "event volume24hr"
            )
            if volume24hr > last_rank_volume + 1e-6:
                raise RuntimeError(
                    "active-event keyset violated requested volume24hr ordering"
                )
            last_rank_volume = volume24hr

            members = event.get("markets")
            if not isinstance(members, list):
                raise RuntimeError(
                    f"active event {event_id} has malformed market membership; "
                    "refusing to scan a partial universe"
                )
            raw_group_id = event.get("negRiskMarketID")
            group_id_present = raw_group_id not in (None, "")
            child_neg_risk = any(
                isinstance(m, dict) and m.get("negRisk") is True
                for m in members
            )
            neg_risk = event.get("negRisk")
            if not isinstance(neg_risk, bool):
                # Gamma omits event.negRisk on ordinary singleton events.  It
                # is safe to route those away only when no child affirmatively
                # identifies as neg-risk and no adapter identity is present.
                if neg_risk is None and not child_neg_risk and not group_id_present:
                    neg_risk = False
                    missing_event_neg_risk_treated_false += 1
                else:
                    raise RuntimeError(
                        "active-event keyset returned malformed negRisk flag"
                    )
            if neg_risk is False and (child_neg_risk or group_id_present):
                raise RuntimeError(
                    "active-event keyset returned inconsistent neg-risk identity"
                )
            try:
                group_id = (
                    _strict_hex_id(raw_group_id, "event negRiskMarketID")
                    if neg_risk else ""
                )
            except ValueError as exc:
                raise RuntimeError(str(exc)) from exc
            parent = {
                "id": event_id,
                "title": event.get("title"),
                "slug": event.get("slug"),
                "active": True,
                "closed": False,
                "negRisk": neg_risk,
                "negRiskMarketID": group_id,
            }
            normalized_event: list[dict] = []
            event_invalid_reason: str | None = (
                "empty neg-risk market membership"
                if neg_risk and not members else None
            )
            event_condition_ids: set[str] = set()
            for raw_market in members:
                if not isinstance(raw_market, dict):
                    event_invalid_reason = "malformed market object"
                    continue
                try:
                    is_open = _strict_open_market(raw_market)
                except ValueError as exc:
                    if neg_risk:
                        event_invalid_reason = str(exc)
                    continue
                if not is_open:
                    continue
                open_markets_scanned += 1
                if not neg_risk:
                    continue
                try:
                    normalized = _normalize_neg_risk_market(raw_market, parent)
                    condition_id = normalized["conditionId"]
                    if condition_id in event_condition_ids:
                        raise ValueError("duplicate condition in event")
                    event_condition_ids.add(condition_id)
                    normalized_event.append(normalized)
                except ValueError as exc:
                    event_invalid_reason = str(exc)

            if neg_risk and event_invalid_reason is not None:
                invalid_neg_risk_events += 1
                invalid_reasons[event_invalid_reason] += 1
            elif neg_risk:
                for market in normalized_event:
                    market_id = market["conditionId"]
                    if market_id in seen_ids:
                        raise RuntimeError(
                            "active-event keyset repeated a market condition"
                        )
                    seen_ids.add(market_id)
                out.extend(normalized_event)

            if max_markets is not None and open_markets_scanned >= max_markets:
                reached_cap = True
                cap_event_index = event_index
                break

        if reached_cap:
            if cap_event_index == len(batch) - 1 and next_cursor in (None, ""):
                cursor_exhausted = True
            else:
                stop_reason = "market_cap"
            break

        if next_cursor in (None, ""):
            cursor_exhausted = True
            break
        if next_cursor == cursor or next_cursor in seen_cursors:
            raise RuntimeError(
                "active-event keyset repeated a cursor; refusing to scan a "
                "partial universe"
            )
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    retained_json_bytes = len(
        json.dumps(out, separators=(",", ":"), default=str).encode("utf-8")
    )
    # JSON decoding and Python container overhead vary by runtime.  Four times
    # both the largest raw page and retained compact JSON is a deliberately
    # conservative planning estimate, not a measured RSS claim.
    projected_peak_memory_bytes = 4 * (max_stream_body_bytes + retained_json_bytes)
    coverage = {
        "endpoint": f"{POLYMARKET_GAMMA}/events/keyset",
        "ranking": "volume24hr descending",
        "filters": {
            "closed": False,
            "end_date_min": end_date_min,
            "end_date_max": end_date_max,
            "exclude_tag_id": [SPORTS_TAG_ID] if exclude_sports else [],
            "liquidity_min": None,
        },
        "market_soft_cap": max_markets,
        "page_hard_cap": max_pages,
        "byte_hard_cap": max_bytes,
        "byte_cap_semantics": (
            "cumulative decoded stream bytes; a single bounded probe chunk is "
            "counted honestly but never retained when it crosses the cap"
        ),
        "pages_fetched": pages_fetched,
        "events_fetched": events_fetched,
        "events_processed": events_processed,
        "open_markets_scanned": open_markets_scanned,
        "neg_risk_markets_retained": len(out),
        "invalid_neg_risk_events": invalid_neg_risk_events,
        "missing_event_neg_risk_treated_false": missing_event_neg_risk_treated_false,
        "invalid_reasons": dict(sorted(invalid_reasons.items())),
        "raw_response_bytes": raw_response_bytes,
        "accepted_response_bytes": accepted_response_bytes,
        "byte_cap_probe_overshoot_bytes": max(0, raw_response_bytes - max_bytes),
        "max_page_bytes": max_page_bytes,
        "max_stream_body_bytes": max_stream_body_bytes,
        "retained_compact_json_bytes": retained_json_bytes,
        "projected_peak_memory_bytes": projected_peak_memory_bytes,
        "projection_method": "4 * (largest retained streamed body + retained compact JSON)",
        "cursor_exhausted": cursor_exhausted,
        "coverage_complete": cursor_exhausted,
        "analysis_complete": cursor_exhausted and invalid_neg_risk_events == 0,
        "stop_reason": stop_reason,
    }
    return UniverseSnapshot(markets=out, coverage=coverage)


def _yes_price(m: dict) -> float | None:
    raw = m.get("outcomePrices") or "[]"
    try:
        prices = json.loads(raw) if isinstance(raw, str) else raw
        if not (isinstance(prices, list) and len(prices) >= 2):
            return None
        return float(prices[0])
    except Exception:
        return None


def _market_fee_buy(market: dict, p: float) -> float:
    """Polymarket fee dollars/share for this market at ``p``.

    The universe already carries each leg's fee schedule, so a flat fallback
    here would erase zero/lower-rate categories. ``fee_per_share`` applies the
    true quadratic curve, ``rate × p × (1-p)``, and the current 0.07 effective
    category cap.
    """
    return pm_fees.fee_per_share(market, p)


def _conservative_fill_fee(market: dict, price: float,
                           shares: float) -> float:
    """Taker fee for one observable fill bucket, ceiled to 5 USDC decimals.

    Public books aggregate makers at a price level, so maker-by-maker rounding
    cannot be reconstructed.  Ceiling each consumed level is the tightest
    conservative calculation supported by the public depth response.
    """
    curve = pm_fees.fee_schedule(market)
    rate = curve.rate if curve.authoritative else pm_fees.effective_rate(curve.rate)
    d_price = Decimal(str(price))
    d_shares = Decimal(str(shares))
    d_rate = Decimal(str(rate))
    d_base = d_price * (Decimal(1) - d_price)
    exponent = Decimal(str(curve.exponent))
    if exponent == exponent.to_integral_value():
        raw = d_shares * d_rate * (d_base ** int(exponent))
    else:
        # No current live descriptor uses a fractional exponent.  Preserve
        # support without pretending binary transcendental math is exact, then
        # ceiling the result to the protocol precision.
        raw = Decimal(str(
            float(d_shares) * float(d_rate)
            * (float(d_base) ** float(exponent))
        ))
    if raw <= 0:
        return 0.0
    return float(raw.quantize(FEE_QUANTUM, rounding=ROUND_CEILING))


def _basket_fee_per_unit(legs: list[tuple[dict, float]]) -> float:
    """Conservative rounded fee for one share of every basket leg."""
    return sum(
        _conservative_fill_fee(market, price, 1.0)
        for market, price in legs
    )


def _parse_levels(value: object, side: str) -> list[tuple[float, float]]:
    if not isinstance(value, list):
        raise ValueError(f"malformed {side} levels")
    levels: list[tuple[float, float]] = []
    for level in value:
        if not isinstance(level, dict):
            raise ValueError(f"malformed {side} level")
        price = _finite_number(level.get("price"), f"{side} price", maximum=1.0)
        size = _finite_number(level.get("size"), f"{side} size")
        if not 0.0 < price < 1.0 or size <= 0.0:
            raise ValueError(f"malformed {side} level")
        levels.append((price, size))
    levels.sort(key=(lambda x: -x[0]) if side == "bid" else (lambda x: x[0]))
    return levels


def _get_json_with_retries(url: str, *, client: httpx.Client | None,
                           deadline: float | None, timeout: float,
                           description: str) -> dict:
    getter = client.get if client is not None else httpx.get
    last_error: Exception | None = None
    for attempt in range(EVENT_PAGE_RETRIES):
        _check_deadline(deadline)
        try:
            response = getter(
                url, timeout=_remaining_timeout(deadline, timeout)
            )
            response.raise_for_status()
            payload = response.json()
            _check_deadline(deadline)
            if not isinstance(payload, dict):
                raise ValueError(f"{description} is not an object")
            return payload
        except TimeoutError:
            raise
        except Exception as exc:
            last_error = exc
            if attempt + 1 < EVENT_PAGE_RETRIES:
                _retry_sleep(0.5 * (2 ** attempt), deadline)
    raise RuntimeError(f"{description} failed") from last_error


def _clob_market_info(market: dict, *, client: httpx.Client | None,
                      deadline: float | None) -> dict:
    """Cross-check Gamma identity/fees against CLOB execution metadata."""
    condition_id = market["conditionId"]
    payload = _get_json_with_retries(
        f"{POLYMARKET_CLOB}/clob-markets/{condition_id}",
        client=client,
        deadline=deadline,
        timeout=20.0,
        description=f"CLOB market info for {condition_id}",
    )
    if str(payload.get("c") or "") != condition_id:
        raise ValueError("CLOB market-info condition identity mismatch")
    if payload.get("ao") is not True:
        raise ValueError("CLOB market-info says orders are not accepted")
    if payload.get("nr") is not True:
        raise ValueError("CLOB market-info neg-risk mismatch")

    raw_tokens = payload.get("t")
    if not isinstance(raw_tokens, list) or len(raw_tokens) != 2:
        raise ValueError("malformed CLOB market-info tokens")
    tokens_by_outcome: dict[str, str] = {}
    for item in raw_tokens:
        if not isinstance(item, dict):
            raise ValueError("malformed CLOB market-info token")
        outcome = str(item.get("o") or "").strip().casefold()
        token = str(item.get("t") or "").strip()
        if outcome not in {"yes", "no"} or outcome in tokens_by_outcome:
            raise ValueError("malformed CLOB market-info outcomes")
        if not token.isdigit() or int(token) <= 0:
            raise ValueError("malformed CLOB market-info token id")
        tokens_by_outcome[outcome] = token
    if [tokens_by_outcome.get("yes"), tokens_by_outcome.get("no")] != market["clobTokenIds"]:
        raise ValueError("Gamma/CLOB token identity mismatch")

    gamma_min = _finite_number(market.get("orderMinSize"), "Gamma orderMinSize")
    clob_min = _finite_number(payload.get("mos"), "CLOB minimum order size")
    if not math.isclose(gamma_min, clob_min, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("Gamma/CLOB minimum-size mismatch")
    tick = _finite_number(
        payload.get("mts"), "CLOB minimum tick size", maximum=1.0
    )
    if tick <= 0.0:
        raise ValueError("malformed CLOB minimum tick size")

    _validate_exact_fee_metadata(market)
    gamma_enabled = market.get("feesEnabled") is True
    descriptor = payload.get("fd")
    if gamma_enabled:
        if not isinstance(descriptor, dict):
            raise ValueError("CLOB fee descriptor missing")
        clob_rate = _finite_number(descriptor.get("r"), "CLOB fee rate")
        clob_exponent = _finite_number(descriptor.get("e"), "CLOB fee exponent")
        clob_taker_only = descriptor.get("to")
        if not isinstance(clob_taker_only, bool):
            raise ValueError("malformed CLOB fee taker-only flag")
        gamma_schedule = market["feeSchedule"]
        if not math.isclose(
            clob_rate, float(gamma_schedule["rate"]), rel_tol=0.0, abs_tol=1e-12
        ) or not math.isclose(
            clob_exponent, float(gamma_schedule["exponent"]),
            rel_tol=0.0, abs_tol=1e-12
        ) or clob_taker_only is not gamma_schedule["takerOnly"]:
            raise ValueError("Gamma/CLOB fee descriptor mismatch")
        fee_schedule = {
            "rate": clob_rate,
            "exponent": clob_exponent,
            "takerOnly": clob_taker_only,
        }
    else:
        if descriptor is not None:
            if not isinstance(descriptor, dict):
                raise ValueError("fee-free CLOB descriptor is malformed")
            if _finite_number(descriptor.get("r"), "CLOB fee rate") != 0.0:
                raise ValueError("Gamma/CLOB fee-enabled mismatch")
        fee_schedule = None

    current = dict(market)
    current["feesEnabled"] = gamma_enabled
    current["feeSchedule"] = fee_schedule
    current["orderMinSize"] = clob_min
    current["clobTickSize"] = tick
    return current


def _orderbook(token_id: str, condition_id: str,
               expected_min_size: float,
               expected_tick_size: float,
               client: httpx.Client | None = None,
               deadline: float | None = None) -> dict:
    """Fetch and strictly validate one current CLOB token book."""
    getter = client.get if client is not None else httpx.get
    r = getter(
        f"{POLYMARKET_CLOB}/book", params={"token_id": token_id},
        timeout=_remaining_timeout(deadline, 10.0),
    )
    r.raise_for_status()
    payload = r.json()
    _check_deadline(deadline)
    if not isinstance(payload, dict):
        raise ValueError("CLOB book is not an object")
    if str(payload.get("asset_id") or "") != token_id:
        raise ValueError("CLOB book asset identity mismatch")
    if str(payload.get("market") or "") != condition_id:
        raise ValueError("CLOB book condition identity mismatch")
    if payload.get("neg_risk") is not True:
        raise ValueError("CLOB book neg-risk mismatch")
    if not isinstance(payload.get("hash"), str) or not payload["hash"].strip():
        raise ValueError("CLOB book hash missing")

    timestamp_ms = _finite_number(payload.get("timestamp"), "book timestamp")
    book_time = timestamp_ms / 1000.0
    age = time.time() - book_time
    if age < -30.0 or age > MAX_BOOK_AGE_SECONDS:
        raise ValueError(f"CLOB book is stale ({age:.1f}s)")

    book_min = _finite_number(payload.get("min_order_size"), "book min_order_size")
    if not math.isclose(book_min, expected_min_size, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("Gamma/CLOB minimum-size mismatch")
    tick = _finite_number(payload.get("tick_size"), "book tick_size", maximum=1.0)
    if tick <= 0.0:
        raise ValueError("malformed book tick_size")
    if not math.isclose(tick, expected_tick_size, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("CLOB market-info/book tick-size mismatch")

    bids = _parse_levels(payload.get("bids"), "bid")
    asks = _parse_levels(payload.get("asks"), "ask")
    if bids and asks and bids[0][0] >= asks[0][0]:
        raise ValueError("crossed CLOB book")
    return {
        "bids": bids,
        "asks": asks,
        "timestamp": timestamp_ms,
        "age_seconds": age,
        "tick_size": tick,
        "min_order_size": book_min,
        "hash": payload["hash"],
    }


def _walk_ask(asks: list[tuple[float, float]], target_shares: float) -> tuple[float, float] | None:
    """Walk asks (sorted ascending) consuming `target_shares`. Return (avg_fill_price, shares_filled)."""
    if not asks:
        return None
    remaining = target_shares
    spent = 0.0
    filled = 0.0
    for price, size in asks:
        take = min(remaining, size)
        spent += take * price
        filled += take
        remaining -= take
        if remaining <= 1e-9:
            break
    if filled <= 0 or remaining > 1e-9:
        return None
    return spent / filled, filled


def _validate_exact_fee_metadata(market: dict) -> None:
    enabled = market.get("feesEnabled")
    schedule = market.get("feeSchedule")
    if enabled is False:
        if schedule is not None:
            if not isinstance(schedule, dict):
                raise ValueError("fee-disabled market has malformed feeSchedule")
            rate = _finite_number(schedule.get("rate"), "fee rate")
            if rate != 0.0:
                raise ValueError("fee-disabled market has nonzero feeSchedule")
        return
    if enabled is not True or not isinstance(schedule, dict):
        raise ValueError("authoritative fee schedule missing")
    _finite_number(schedule.get("rate"), "fee rate")
    _finite_number(schedule.get("exponent"), "fee exponent")
    if not isinstance(schedule.get("takerOnly"), bool):
        raise ValueError("malformed fee takerOnly flag")


def _refresh_live_members(
    members: list[tuple[dict, float]],
    client: httpx.Client | None = None,
    deadline: float | None = None,
) -> tuple[list[tuple[dict, float]], float]:
    """Re-fetch every leg and cross-check Gamma against CLOB execution data."""
    refreshed: list[tuple[dict, float]] = []
    min_sizes: list[float] = []
    for original, _old_price in members:
        _check_deadline(deadline)
        market_id = str(original.get("id") or "")
        raw = _get_json_with_retries(
            f"{POLYMARKET_GAMMA}/markets/{market_id}",
            client=client,
            deadline=deadline,
            timeout=20.0,
            description=f"Gamma refresh for market {market_id}",
        )
        if str(raw.get("id") or "") != market_id:
            raise ValueError("Gamma market id changed during refresh")
        if str(raw.get("conditionId") or "") != original["conditionId"]:
            raise ValueError("Gamma condition identity changed during refresh")
        if not _strict_open_market(raw):
            raise ValueError("shortlisted Gamma market is no longer open")

        parent = original["events"][0]
        current = _normalize_neg_risk_market(raw, parent)
        if current["clobTokenIds"] != original["clobTokenIds"]:
            raise ValueError("Gamma token identity changed during refresh")
        current = _clob_market_info(
            current, client=client, deadline=deadline
        )
        min_size = _finite_number(current.get("orderMinSize"), "orderMinSize")
        if min_size <= 0.0:
            raise ValueError("malformed orderMinSize")
        min_sizes.append(min_size)
        refreshed.append((current, _yes_price(current) or 0.0))
    if not refreshed:
        raise ValueError("empty refreshed group")
    return refreshed, max(min_sizes)


def live_quote_group(members: list[tuple[dict, float]], action: str,
                     target_shares: float | None = None,
                     client: httpx.Client | None = None,
                     deadline: float | None = None) -> dict:
    """For each member, fetch CLOB orderbook for the side we'd buy and walk to target_shares.
    Returns a realistic cost/payout summary or an explicit fail-closed reason."""
    try:
        members, group_min_size = _refresh_live_members(
            members, client=client, deadline=deadline
        )
    except Exception as exc:
        return {"live_skipped": f"metadata refresh failed: {exc}"}
    if target_shares is None:
        target_shares = group_min_size
    try:
        target_shares = _finite_number(target_shares, "target shares")
    except ValueError as exc:
        return {"live_skipped": str(exc)}
    if target_shares + 1e-9 < group_min_size:
        return {"live_skipped": "target is below a member minimum order size"}

    side_quotes = []
    for m, _yp in members:
        try:
            _check_deadline(deadline)
        except TimeoutError as exc:
            return {"live_skipped": str(exc)}
        tokens = m["clobTokenIds"]
        # action == buy_all_no  → buy NO token (index 1)
        # action == buy_all_yes → buy YES token (index 0)
        token = tokens[1] if action.startswith("buy_all_no") else tokens[0]
        min_size = _finite_number(m.get("orderMinSize"), "orderMinSize")
        try:
            ob = _orderbook(
                token, m["conditionId"], min_size,
                _finite_number(m.get("clobTickSize"), "CLOB tick size"),
                client=client, deadline=deadline,
            )
        except Exception as exc:
            return {"live_skipped": f"book validation failed for {m['id']}: {exc}"}
        if not ob["asks"]:
            return {"live_skipped": f"no asks for market {m['id']}"}
        walk = _walk_ask(ob["asks"], target_shares)
        if walk is None:
            return {"live_skipped": f"insufficient ask depth for market {m['id']}"}
        avg_p, filled = walk
        # The V2 fee curve is nonlinear.  Charge each consumed price level,
        # then normalize to one basket unit; fee(avg price) is not exact.
        remaining = target_shares
        fee_dollars = 0.0
        for price, size in ob["asks"]:
            take = min(remaining, size)
            fee_dollars += _conservative_fill_fee(m, price, take)
            remaining -= take
            if remaining <= 1e-9:
                break
        avg_fee_per_share = fee_dollars / target_shares
        side_quotes.append({"member": m.get("groupItemTitle") or m["question"][:40],
                            "avg_ask": avg_p, "filled": filled,
                            "fee_per_share": avg_fee_per_share,
                            "best_ask": ob["asks"][0][0], "best_ask_sz": ob["asks"][0][1],
                            "book_timestamp": ob["timestamp"],
                            "book_age_seconds": ob["age_seconds"],
                            "book_hash": ob["hash"]})
    if not side_quotes:
        return {"live_skipped": "empty group"}
    n = len(side_quotes)
    sum_avg_ask = sum(q["avg_ask"] for q in side_quotes)
    # Per unit: cost = sum(ask), payout if exactly one YES wins:
    #   buy_all_no  → n-1
    #   buy_all_yes → 1
    if action.startswith("buy_all_no"):
        gross_payout = n - 1
    else:
        gross_payout = 1.0
    fees = sum(q["fee_per_share"] for q in side_quotes)
    net_profit_per_unit = gross_payout - sum_avg_ask - fees
    capital_per_unit = sum_avg_ask + fees
    return {
        "live_notional_per_unit": sum_avg_ask,
        "live_capital_per_unit": capital_per_unit,
        "live_gross_payout": gross_payout,
        "live_fees": fees,
        "live_net_per_unit": net_profit_per_unit,
        "live_net_edge_frac": net_profit_per_unit / capital_per_unit if capital_per_unit > 0 else 0,
        "target_shares": target_shares,
        "snapshot_atomic": False,
        "quote_depth_validated": True,
        "actionable": False,
        "requires_revalidation": True,
        "fee_rounding": "ceil each consumed public price level to 0.00001 USDC",
        "live_quotes": side_quotes,
    }


def group_by_event(markets: list[dict]) -> dict[str, list[dict]]:
    # Dedup members by conditionId (2026-08-01): the paginated market fetch can
    # return the SAME market twice (overlapping pages / re-fetch drift — the
    # duplicates carried slightly different liquidity snapshots). A duplicated
    # member double-counts its YES in the sum AND breaks the buy-all-NO payout
    # assumption (duplicates resolve YES together), which manufactured a phantom
    # "28.7% live-validated free arb" on Montana-Senate (2×R + 2×I + 1×D,
    # yes_sum 2.006) and daemon-fired a tick for it.
    groups: dict[str, list[dict]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for m in markets:
        events = m.get("events") or []
        if not events:
            continue
        # Gamma's negRiskMarketID is the exchange-level basket identity.  The
        # display event id is metadata and is not strong enough to prove that
        # two binary conditions share one neg-risk adapter.
        group_id = events[0].get("negRiskMarketID")
        if not group_id:
            continue
        key = (group_id, str(m.get("conditionId") or m.get("id")))
        if key in seen:
            continue
        seen.add(key)
        groups[group_id].append(m)
    return groups


def evaluate_group(group_id: str, members: list[dict]) -> dict | None:
    """Compute the consistency-violation arb potential for a neg-risk event."""
    if len(members) < 2:
        return None
    # Filter to members that are negRisk + have prices
    valid = []
    for m in members:
        if not m.get("negRisk"):
            return None
        yp = _yes_price(m)
        if yp is None:
            continue
        valid.append((m, yp))
    if len(valid) < 2:
        return None

    yes_sum = sum(yp for _, yp in valid)
    n = len(valid)
    deviation = yes_sum - 1.0

    # Compute realistic net edge.
    #
    # Critical asymmetry: the two sides differ in robustness to "missing markets"
    # (cases where Polymarket lists 20 named candidates but the actual event has
    # more, with the residual unmodeled).
    #
    #   • sum(YES) > 1 (overpriced): buying all NOs is a TRUE free arb. Exactly
    #     one outcome wins; if it's a listed candidate, n-1 NOs pay $1 each
    #     (total $n-1); if it's a non-listed write-in, ALL n NOs pay $1 each
    #     (total $n) — even better. Cost is locked at sum(NO) = n - sum(YES).
    #
    #   • sum(YES) < 1 (underpriced): buying all YESes is NOT a free arb. The
    #     "missing mass" 1 - sum(YES) is the market's implied probability that
    #     none of the listed candidates wins. If that's a real probability
    #     (e.g., a Nobel write-in actually wins), ALL n YESes resolve to $0
    #     and you eat the full sum(YES) loss. Only safe if you have a Field
    #     market to capture the residual, OR you're directionally betting
    #     against the implied non-listed-candidate probability.
    #
    # We compute both directions but only mark the first structural/rule-safe.
    if deviation > 0:
        no_prices = [(1 - p) for _, p in valid]
        total_fees = _basket_fee_per_unit([
            (market, no_price)
            for (market, _yes_price_), no_price in zip(valid, no_prices)
        ])
        notional = sum(no_prices)  # = n - yes_sum
        gross_profit = (n - 1) - notional
        net_profit = gross_profit - total_fees
        action = "buy_all_no"
        structural_free_arb = True
    elif deviation < 0:
        total_fees = _basket_fee_per_unit(valid)
        gross_profit = 1.0 - yes_sum
        net_profit = gross_profit - total_fees
        action = "buy_all_yes (DIRECTIONAL — bets against missing-mass)"
        notional = yes_sum
        structural_free_arb = False
    else:
        return None

    # Liquidity: sum of liquidityNum across members (rough; some are 0 for thin markets)
    liquidity = sum(float(m.get("liquidityNum") or 0) for m, _ in valid)

    # Resolution date: earliest endDate among members
    end_dates = [m.get("endDateIso") or m.get("endDate") for m, _ in valid]
    end_dates = [e for e in end_dates if e]
    earliest_end = min(end_dates) if end_dates else None
    days_to_resolution = None
    if earliest_end:
        try:
            d = dt.datetime.fromisoformat(earliest_end.replace("Z", "+00:00"))
            days_to_resolution = (d - dt.datetime.now(dt.timezone.utc)).days
        except Exception:
            pass

    title = (members[0].get("events") or [{}])[0].get("title", "?")
    event_id = (members[0].get("events") or [{}])[0].get("id")
    capital = notional + total_fees
    return {
        "event_id": event_id,
        "neg_risk_market_id": group_id,
        "title": title,
        "members": n,
        "yes_sum": yes_sum,
        "deviation": deviation,
        "action": action,
        "structural_free_arb": structural_free_arb,
        "live_status": "not_quoted",
        "actionable": False,
        "requires_revalidation": structural_free_arb,
        "notional_required": notional,
        "capital_required": capital,
        "gross_profit": gross_profit,
        "fees_estimate": total_fees,
        "net_profit": net_profit,
        "net_edge_frac": net_profit / capital if capital > 0 else 0,
        "liquidity": liquidity,
        "days_to_resolution": days_to_resolution,
        "top_contenders": sorted(
            [{"name": m.get("groupItemTitle") or m["question"][:60],
              "yes": yp,
              "liq": float(m.get("liquidityNum") or 0)}
             for m, yp in valid],
            key=lambda x: -x["yes"],
        )[:6],
    }


def _plan_live_candidates(candidates: list[dict], max_groups: int,
                          max_legs: int) -> tuple[list[dict], list[dict], int]:
    """Bound live work while accounting explicitly for every structural hit."""
    relevant = [c for c in candidates if c["structural_free_arb"]]
    selected: list[dict] = []
    selected_legs = 0
    for candidate in relevant:
        member_count = int(candidate["members"])
        if len(selected) >= max_groups:
            candidate["live_status"] = "unquoted_group_cap"
            candidate["live_unquoted_reason"] = "live group cap"
            continue
        if selected_legs + member_count > max_legs:
            candidate["live_status"] = "unquoted_leg_cap"
            candidate["live_unquoted_reason"] = "live leg cap"
            continue
        candidate["live_status"] = "queued"
        selected.append(candidate)
        selected_legs += member_count
    return relevant, selected, selected_legs


def _finalize_coverage(coverage: dict, relevant: list[dict],
                       requested: list[dict], *,
                       live_legs: int,
                       budget_exhausted: bool) -> None:
    validated = sum(
        1 for c in requested if c.get("quote_depth_validated") is True
    )
    skipped = sum(1 for c in requested if "live_skipped" in c)
    unquoted = sum(1 for c in relevant if c.get("live_status", "").startswith("unquoted"))
    coverage["live_groups_relevant"] = len(relevant)
    coverage["live_groups_eligible"] = len(relevant)  # compatibility alias
    coverage["live_groups_requested"] = len(requested)
    coverage["live_groups_validated"] = validated
    coverage["live_groups_skipped"] = skipped
    coverage["live_groups_unquoted"] = unquoted
    coverage["live_legs_requested"] = live_legs
    coverage["live_shortlist_complete"] = unquoted == 0
    coverage["live_budget_exhausted"] = budget_exhausted

    reasons: list[str] = []
    if not coverage.get("cursor_exhausted"):
        reasons.append(str(coverage.get("stop_reason") or "cursor not exhausted"))
    if coverage.get("invalid_neg_risk_events"):
        reasons.append("invalid neg-risk events")
    if unquoted:
        reasons.append(f"{unquoted} structural groups unquoted")
    if skipped:
        reasons.append(f"{skipped} structural groups quote-failed")
    if budget_exhausted:
        reasons.append("live deadline exhausted")
    coverage["analysis_incomplete_reasons"] = reasons
    coverage["analysis_complete"] = not reasons


def _analysis_label(coverage: dict) -> str:
    if coverage.get("analysis_complete"):
        return "COMPLETE declared scope"
    reasons = coverage.get("analysis_incomplete_reasons") or [
        coverage.get("stop_reason") or "analysis not complete"
    ]
    return f"INCOMPLETE analysis ({'; '.join(map(str, reasons))})"


def _provisional_live_hits(candidates: list[dict]) -> list[dict]:
    hits = [
        c for c in candidates
        if c.get("structural_free_arb")
        and c.get("quote_depth_validated") is True
        and c.get("live_net_edge_frac", -1.0) > 0.0
    ]
    for candidate in hits:
        candidate["actionable"] = bool(
            candidate.get("snapshot_atomic") is True
            and candidate.get("actionable") is True
        )
        candidate["requires_revalidation"] = not candidate["actionable"]
    hits.sort(key=lambda c: -c["live_net_edge_frac"])
    return hits


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--max-markets", type=int, default=DEFAULT_MAX_MARKETS,
        help=(f"top-volume soft cap, completing the boundary event (default "
              f"{DEFAULT_MAX_MARKETS}); 0 explicitly requests cursor exhaustion "
              "subject to hard page/byte guards"),
    )
    p.add_argument("--end-date-max", default=DEFAULT_END_DATE_MAX,
                   help="inclusive ROI-scope end-date filter sent to Gamma")
    p.add_argument("--include-sports", action="store_true",
                   help="include Sports tag 1 (normally covered by the sports scanner)")
    p.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES,
                   help="hard keyset page guard")
    p.add_argument("--max-bytes-mb", type=float,
                   default=DEFAULT_MAX_BYTES / (1024 * 1024),
                   help="cumulative decoded event-stream budget in MiB")
    p.add_argument("--max-live-groups", type=int, default=DEFAULT_MAX_LIVE_GROUPS,
                   help="maximum structural groups to cross-check and live-price")
    p.add_argument("--max-live-legs", type=int, default=DEFAULT_MAX_LIVE_LEGS,
                   help="maximum total basket legs to refresh and live-price")
    p.add_argument("--live-budget-seconds", type=float,
                   default=DEFAULT_LIVE_BUDGET_SECONDS,
                   help="wall-clock budget for the live-quote pass")
    p.add_argument("--notify", action="store_true")
    p.add_argument("--telegram-threshold-net", type=float, default=TELEGRAM_THRESHOLD_NET,
                   help="net-edge threshold (frac) above which to Telegram")
    args = p.parse_args()

    if args.max_markets < 0:
        p.error("--max-markets cannot be negative")
    if (args.max_pages <= 0 or args.max_bytes_mb <= 0
            or args.max_live_groups <= 0 or args.max_live_legs <= 0
            or args.live_budget_seconds <= 0):
        p.error("hard page/byte guards must be positive")
    cap = args.max_markets if args.max_markets > 0 else None
    scan_started = dt.datetime.now(dt.timezone.utc)
    end_date_min = scan_started.isoformat(timespec="seconds").replace("+00:00", "Z")
    scope = (
        f"top-volume soft cap {cap} open markets"
        if cap is not None else "explicit full cursor diagnostic"
    )
    print(f"fetching Polymarket active event universe ({scope})...")
    print(f"  filters: end_date=[{end_date_min}, {args.end_date_max}], "
          f"sports={'included' if args.include_sports else 'excluded'}, "
          "liquidity_min=omitted")
    snapshot = fetch_universe(
        cap,
        end_date_min=end_date_min,
        end_date_max=args.end_date_max,
        exclude_sports=not args.include_sports,
        max_pages=args.max_pages,
        max_bytes=int(args.max_bytes_mb * 1024 * 1024),
    )
    markets = snapshot.markets
    coverage = snapshot.coverage
    fetch_coverage_state = (
        "COMPLETE declared scope"
        if coverage["coverage_complete"]
        else f"INCOMPLETE ({coverage['stop_reason'] or 'cursor not exhausted'})"
    )
    print(f"  retained {len(markets)} validated neg-risk markets; "
          f"scanned {coverage['open_markets_scanned']} open markets in "
          f"{coverage['events_processed']} events / {coverage['pages_fetched']} pages")
    print(f"  fetch coverage: {fetch_coverage_state}; streamed "
          f"{coverage['raw_response_bytes'] / (1024 * 1024):.1f} MiB; "
          f"projected peak memory "
          f"{coverage['projected_peak_memory_bytes'] / (1024 * 1024):.1f} MiB")
    if coverage["invalid_neg_risk_events"]:
        print(f"  WARNING: {coverage['invalid_neg_risk_events']} malformed neg-risk "
              "event(s) were not evaluated")

    print("grouping by event...")
    groups = group_by_event(markets)
    print(f"  {len(groups)} distinct events")

    print("evaluating consistency (pass 1: gamma-api midpoints)...")
    candidates = []
    valid_members_by_group: dict[str, list[tuple[dict, float]]] = {}
    for group_id, members in groups.items():
        # Re-derive valid (m, yp) inside evaluate_group; cache it for live pass.
        valid_pairs = []
        if all(m.get("negRisk") for m in members):
            for m in members:
                yp = _yes_price(m)
                if yp is not None:
                    valid_pairs.append((m, yp))
        result = evaluate_group(group_id, members)
        if result and abs(result["deviation"]) >= LOG_THRESHOLD_GROSS:
            candidates.append(result)
            valid_members_by_group[group_id] = valid_pairs

    # Sort by net edge (largest profit per dollar locked)
    candidates.sort(key=lambda c: -c["net_edge_frac"])
    print(f"  {len(candidates)} groups exceed {LOG_THRESHOLD_GROSS*100:.1f}% gross deviation (gamma midpoint)")

    # Pass 2: every logged sum>1 structural hit is relevant.  The bounded plan
    # prioritizes midpoint edge, but any cap omission keeps final analysis
    # explicitly incomplete rather than manufacturing a scoped zero.
    live_relevant, live_candidates, live_legs = _plan_live_candidates(
        candidates, args.max_live_groups, args.max_live_legs
    )
    print(f"\nlive-quote pass: {len(live_candidates)}/{len(live_relevant)} "
          f"structural groups requested ({live_legs} legs; every unquoted group "
          "keeps analysis incomplete)")
    live_started = time.monotonic()
    live_deadline = live_started + args.live_budget_seconds
    live_budget_exhausted = False
    with httpx.Client(timeout=20.0) as live_client:
        for i, c in enumerate(live_candidates):
            if time.monotonic() >= live_deadline:
                live_budget_exhausted = True
                break
            group_id = c["neg_risk_market_id"]
            members = valid_members_by_group.get(group_id) or []
            if not members:
                c["live_skipped"] = "no valid members"
                c["live_status"] = "quote_failed"
                continue
            live = live_quote_group(
                members, c["action"], client=live_client,
                deadline=live_deadline,
            )
            c.update(live)
            if c.get("quote_depth_validated") is True:
                c["live_status"] = (
                    "provisional_positive"
                    if c.get("live_net_edge_frac", -1.0) > 0.0
                    else "quoted_nonpositive"
                )
            else:
                c["live_status"] = "quote_failed"
            if time.monotonic() >= live_deadline:
                live_budget_exhausted = True
                break
            if (i + 1) % 10 == 0:
                print(f"  ...{i+1}/{len(live_candidates)} done")
    if live_budget_exhausted:
        for c in live_candidates:
            if c.get("live_status") == "queued":
                c["live_skipped"] = "live pass time budget exhausted"
                c["live_status"] = "quote_failed"
    print(f"  {sum(1 for c in live_candidates if 'live_net_edge_frac' in c)} got live quotes")
    _finalize_coverage(
        coverage, live_relevant, live_candidates,
        live_legs=live_legs,
        budget_exhausted=live_budget_exhausted,
    )
    coverage_state = _analysis_label(coverage)

    # Output
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_md = OUT_DIR / f"polymarket_consistency_{ts}.md"
    out_json = OUT_DIR / "polymarket_consistency_latest.json"

    structural = [c for c in candidates if c["structural_free_arb"]]
    directional = [c for c in candidates if not c["structural_free_arb"]]
    provisional_hits = _provisional_live_hits(candidates)

    with out_md.open("w") as f:
        f.write(f"# Polymarket consistency scan — {ts} UTC\n\n")
        f.write(f"Coverage: **{coverage_state}**. This is a volume-ranked ROI "
                "slice unless the keyset cursor was exhausted.\n\n")
        f.write(f"- filters: `{json.dumps(coverage['filters'], sort_keys=True)}`\n")
        f.write(f"- {coverage['pages_fetched']} pages / "
                f"{coverage['raw_response_bytes'] / (1024 * 1024):.1f} MiB streamed; "
                f"projected peak memory "
                f"{coverage['projected_peak_memory_bytes'] / (1024 * 1024):.1f} MiB\n")
        f.write(f"- cursor_exhausted={str(coverage['cursor_exhausted']).lower()}, "
                f"stop_reason={coverage['stop_reason'] or 'none'}, "
                f"invalid_neg_risk_events={coverage['invalid_neg_risk_events']}\n\n")
        if not coverage["analysis_complete"]:
            f.write("> **Coverage is incomplete. A zero below means no hit in the "
                    "scanned slice; it is not a comprehensive exchange-wide zero.**\n\n")
        f.write(f"Universe slice: {coverage['open_markets_scanned']} open markets "
                f"scanned, {len(markets)} validated neg-risk markets retained, "
                f"{len(groups)} neg-risk groups, "
                f"{len(candidates)} midpoint-violations > {LOG_THRESHOLD_GROSS*100:.1f}%.\n\n")
        f.write(f"- **{len(provisional_hits)} PROVISIONAL positive structural baskets "
                "(sequential CLOB depth; revalidation required)**\n")
        f.write(f"- {len(structural)} sum>1 (midpoint), {len(directional)} sum<1 "
                "(midpoint, directional)\n\n")
        f.write("> WARNING: gamma-api `outcomePrices` shows midpoints between stale stub bids "
                "(often $0.01) and real asks. Most midpoint-only \"free arb\" signals evaporate "
                "when orderbook asks are checked. Positive live-depth observations below are "
                "sequential and non-atomic: independently refresh every leg before any decision; "
                "this report is not an execution instruction.\n\n")

        f.write("## PROVISIONAL structural baskets (revalidation required)\n\n")
        f.write("Computed by walking CLOB asks for buy-all-NO of every member at "
                "one common size no smaller than any validated leg minimum. "
                "Reported economics are per basket unit; snapshots are sequential, "
                "not atomic. Profit assumes exactly one YES wins.\n\n")
        if provisional_hits:
            f.write(f"| Live Edge | Mid Edge | YES-sum | Members | Capital | Liquidity | Title |\n")
            f.write(f"|---:|---:|---:|---:|---:|---:|---|\n")
            for c in provisional_hits[:30]:
                f.write(f"| {c['live_net_edge_frac']*100:+.2f}% | {c['net_edge_frac']*100:+.2f}% | "
                        f"{c['yes_sum']:.4f} | "
                        f"{c['members']} | ${c['live_capital_per_unit']:.2f}/unit | "
                        f"${c['liquidity']:,.0f} | "
                        f"{c['title'][:60]} |\n")
        else:
            if coverage["analysis_complete"]:
                f.write("No positive provisional basket in the complete declared scope; "
                        "every logged structural group received a terminal quote result.\n")
            else:
                f.write("No positive provisional candidate in the scanned slice. Analysis is "
                        "incomplete, so this is not a comprehensive zero.\n")

        f.write("\n## Midpoint-only sum>1 candidates (likely stale orderbooks)\n\n")
        f.write("Sorted by midpoint net edge. These are NOT executable; included for diagnostic only.\n\n")
        f.write(f"| Mid Edge | Live Edge | YES-sum | Members | Liquidity | Title |\n")
        f.write(f"|---:|---:|---:|---:|---:|---|\n")
        for c in structural[:30]:
            live_e = c.get("live_net_edge_frac")
            live_str = (
                f"{live_e*100:+.2f}%" if live_e is not None
                else c.get("live_skipped")
                or c.get("live_unquoted_reason", "—")
            )
            f.write(f"| {c['net_edge_frac']*100:+.2f}% | {live_str} | {c['yes_sum']:.4f} | "
                    f"{c['members']} | "
                    f"${c['liquidity']:,.0f} | "
                    f"{c['title'][:60]} |\n")

        f.write("\n## Midpoint-only sum<1 candidates (directional, missing-mass risk)\n\n")
        f.write(f"| Mid Edge | YES-sum | Members | Liquidity | Title |\n")
        f.write(f"|---:|---:|---:|---:|---|\n")
        for c in directional[:15]:
            f.write(f"| {c['net_edge_frac']*100:+.2f}% | {c['yes_sum']:.4f} | "
                    f"{c['members']} | "
                    f"${c['liquidity']:,.0f} | "
                    f"{c['title'][:60]} |\n")

        if provisional_hits:
            f.write("\n## PROVISIONAL basket breakdown\n\n")
            for c in provisional_hits[:8]:
                f.write(f"### {c['title']}\n")
                f.write(f"- members: {c['members']}, YES-sum (mid): {c['yes_sum']:.4f}\n")
                f.write(f"- validated common quote size: {c['target_shares']:.4f} shares/leg; "
                        f"snapshot_atomic={str(c['snapshot_atomic']).lower()}\n")
                f.write(f"- live notional/unit: ${c['live_notional_per_unit']:.4f}, "
                        f"all-in capital/unit: ${c['live_capital_per_unit']:.4f}, "
                        f"gross ${c['live_gross_payout']:.4f}, fees ${c['live_fees']:.4f}, "
                        f"**net ${c['live_net_per_unit']:.4f} ({c['live_net_edge_frac']*100:+.2f}%)**\n")
                f.write("- live quotes (per-member NO ask, walking the validated "
                        "common size):\n")
                for q in c.get("live_quotes", []):
                    f.write(f"  - {q['member'][:55]}: avg_ask={q['avg_ask']:.4f} "
                            f"(best={q['best_ask']:.3f} sz={q['best_ask_sz']:.0f})\n")
                f.write("\n")

    payload = {
        "generated_at": ts,
        "semantics": {
            "live_snapshots_atomic": False,
            "actionable_candidates": 0,
            "positive_live_depth_observations": len(provisional_hits),
            "instruction": "independent revalidation required; do not execute from this file",
        },
        "coverage": coverage,
        "candidates": candidates,
    }
    out_json.write_text(json.dumps(payload, indent=2, default=str))

    print(f"\nwrote {out_md}")
    print(f"wrote {out_json}\n")

    # Stdout summary — sequential observations, never execution claims.
    print("\n=== PROVISIONAL STRUCTURAL BASKETS (REVALIDATION REQUIRED) ===")
    if provisional_hits:
        print(f"{'live edge':>10}  {'mid edge':>9}  {'YES-sum':>8}  {'members':>7}  {'cap/unit':>9}  {'liq':>10}  title")
        for c in provisional_hits[:15]:
            print(f"{c['live_net_edge_frac']*100:>+9.2f}%  "
                  f"{c['net_edge_frac']*100:>+8.2f}%  {c['yes_sum']:>8.4f}  "
                  f"{c['members']:>7}  ${c['live_capital_per_unit']:>7.2f}  "
                  f"${c['liquidity']:>9,.0f}  {c['title'][:60]}")
    else:
        if coverage["analysis_complete"]:
            print("none positive in the complete declared scope — every logged "
                  "structural group received a terminal quote result.")
        else:
            print("none in scanned slice — coverage incomplete; NOT a comprehensive zero.")
    print(f"\n{len(structural)} midpoint sum>1 / {len(directional)} midpoint sum<1 / "
          f"{len(provisional_hits)} provisional positive after sequential depth check")

    # Notifications request a fresh review; they are never execution claims.
    review_hits = [
        c for c in provisional_hits
        if c["live_net_edge_frac"] > args.telegram_threshold_net
    ]
    print(f"{len(review_hits)} PROVISIONAL consistency candidates exceed "
          f"{args.telegram_threshold_net*100:.1f}% modeled net; REVALIDATION REQUIRED")

    if review_hits and args.notify:
        lines = [
            f"CONSISTENCY REVALIDATION REQUEST: {len(review_hits)} sequential, "
            f"non-atomic basket observation(s) above {args.telegram_threshold_net*100:.1f}% "
            f"modeled net ({coverage_state}). Do not execute from this alert."
        ]
        for c in review_hits[:5]:
            lines.append(
                f"\n• provisional modeled net +{c['live_net_edge_frac']*100:.2f}%  buy-all-NO\n"
                f"  YES-sum {c['yes_sum']:.4f} across {c['members']} members  "
                f"cap/unit ${c['live_capital_per_unit']:.2f}  net/unit ${c['live_net_per_unit']:.4f}\n"
                f"  {c['title'][:80]}"
            )
        lines.append(f"\nRefresh membership, resolution criteria, fees, and every leg at one "
                     f"common size before recommending action. Full table: {out_md.name}")
        _telegram("\n".join(lines))

    return 0


if __name__ == "__main__":
    sys.exit(main())
