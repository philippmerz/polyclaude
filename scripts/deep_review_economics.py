"""Offline economics for an explicit, saved deep-review quote packet.

This module does not fetch quotes, mutate financial state, or authorize orders.
The caller must name the quote packet so capture provenance stays reviewable.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import deep_review_ledger as ledger
from pm_fees import fee_per_share, fee_schedule

ROOT = Path(__file__).resolve().parents[1]


def _aware_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing {label}")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {label}: {value!r}") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone")
    return dt.astimezone(timezone.utc)


def _scoped_receipt(path_value: Any) -> Path:
    if not isinstance(path_value, str) or not path_value:
        raise ValueError("missing book receipt path")
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("unsafe book receipt path")
    resolved = (ROOT / path).resolve(strict=True)
    try:
        resolved.relative_to(ROOT.resolve(strict=True))
    except ValueError as exc:
        raise ValueError("book receipt escapes repository root") from exc
    if not resolved.is_file():
        raise ValueError("book receipt path is not a file")
    return resolved


def _receipt_index(capture: dict) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for row in capture.get("clob_transport_receipts", []):
        legacy_books = row.get("type") is None and urlparse(str(row.get("url", ""))).path == "/books"
        if row.get("type") != "books_batch" and not legacy_books:
            continue
        request_id = row.get("request_id")
        if request_id is None and legacy_books:
            request_id = "legacy-books-batch"
        # Some capture versions identify the batch only by its receipt path.
        if request_id is None:
            try:
                receipt = json.loads(_scoped_receipt(row.get("receipt_path")).read_text())
                request_id = receipt.get("request_id")
            except (OSError, json.JSONDecodeError, ValueError):
                continue
        if not isinstance(request_id, str) or request_id in rows:
            raise ValueError("missing or duplicate books-batch request id")
        rows[request_id] = row
    return rows


def _verified_book_received_utc(capture: dict, book_row: dict) -> str:
    """Return the matching books response time after validating its receipt."""
    request_id = book_row.get("request_id")
    batches = _receipt_index(capture)
    if not isinstance(request_id, str) or not request_id:
        legacy = [key for key, value in batches.items() if value.get("type") is None]
        if len(legacy) != 1:
            raise ValueError("book row is missing request_id and no unique legacy books receipt exists")
        request_id = legacy[0]
    batch = batches.get(request_id)
    if batch is None:
        raise ValueError(f"no books-batch receipt metadata for {request_id}")
    if batch.get("type") is None:
        parsed_url = urlparse(str(batch.get("url", "")))
        if (parsed_url.scheme, parsed_url.netloc, parsed_url.path) != ("https", "clob.polymarket.com", "/books"):
            raise ValueError("legacy books receipt is not the expected CLOB endpoint")
        if batch.get("status_code") != 200:
            raise ValueError("legacy books receipt is not HTTP 200")
        raw_path = _scoped_receipt(batch.get("raw_path"))
        raw_body = raw_path.read_bytes()
        if hashlib.sha256(raw_body).hexdigest() != batch.get("body_sha256"):
            raise ValueError("legacy books response body hash mismatch")
        try:
            returned_books = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise ValueError("legacy books response body is not valid JSON") from exc
        if not isinstance(returned_books, list):
            raise ValueError("legacy books response body is not a list")
        token = str(book_row.get("token_id", ""))
        matches = [item for item in returned_books if isinstance(item, dict) and str(item.get("asset_id")) == token]
        if book_row.get("available"):
            if len(matches) != 1 or matches[0] != book_row.get("book"):
                raise ValueError("quote book differs from the hashed legacy CLOB response row")
        elif matches or book_row.get("book") is not None:
            raise ValueError("unavailable quote book conflicts with the legacy CLOB response")
        received = batch.get("received_utc")
        receipt_dt = _aware_utc(received, "legacy books receipt received_utc")
        if book_row.get("received_utc") and _aware_utc(book_row["received_utc"], "book row received_utc") != receipt_dt:
            raise ValueError("book row timestamp does not match its legacy receipt")
        return received
    receipt_path = _scoped_receipt(batch.get("receipt_path"))
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read books receipt {receipt_path}") from exc
    if receipt.get("request_id") != request_id:
        raise ValueError("books receipt request_id mismatch")
    if receipt.get("status_code") != 200 or batch.get("status_code") != 200:
        raise ValueError("books receipt is not HTTP 200")
    parsed_url = urlparse(str(receipt.get("url", "")))
    if receipt.get("method") != "POST" or (parsed_url.scheme, parsed_url.netloc, parsed_url.path) != (
        "https", "clob.polymarket.com", "/books"
    ):
        raise ValueError("books receipt is not the expected CLOB POST endpoint")
    body_path = _scoped_receipt(receipt.get("gzip_path"))
    compressed = body_path.read_bytes()
    if hashlib.sha256(compressed).hexdigest() != receipt.get("gzip_sha256"):
        raise ValueError("books receipt body gzip hash mismatch")
    try:
        raw_body = gzip.decompress(compressed)
    except OSError as exc:
        raise ValueError("books receipt body is not valid gzip") from exc
    if hashlib.sha256(raw_body).hexdigest() != receipt.get("raw_sha256"):
        raise ValueError("books receipt raw body hash mismatch")
    try:
        returned_books = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ValueError("books receipt body is not valid JSON") from exc
    if not isinstance(returned_books, list):
        raise ValueError("books receipt body is not a list")
    receipt_received = receipt.get("received_utc")
    row_received = book_row.get("received_utc")
    batch_received = batch.get("received_utc")
    receipt_dt = _aware_utc(receipt_received, "books receipt received_utc")
    if _aware_utc(row_received, "book row received_utc") != receipt_dt:
        raise ValueError("book row timestamp does not match its receipt")
    if _aware_utc(batch_received, "batch received_utc") != receipt_dt:
        raise ValueError("batch timestamp does not match its receipt")
    requested = receipt.get("json_request_body")
    token = str(book_row.get("token_id", ""))
    if not isinstance(requested, list) or not token:
        raise ValueError("book receipt lacks requested token list")
    if token not in {str(item.get("token_id")) for item in requested if isinstance(item, dict)}:
        raise ValueError("book token is absent from matching receipt request")
    matches = [item for item in returned_books if isinstance(item, dict) and str(item.get("asset_id")) == token]
    if book_row.get("available"):
        if len(matches) != 1 or matches[0] != book_row.get("book"):
            raise ValueError("quote book differs from the hashed CLOB response row")
    elif matches or book_row.get("book") is not None:
        raise ValueError("unavailable quote book conflicts with the CLOB response")
    return receipt_received


def _verified_gamma_received_utc(case: dict, frozen: dict) -> str:
    """Bind the captured Gamma object and its economics fields to raw receipt."""
    entry = case.get("gamma_receipt")
    if not isinstance(entry, dict):
        raise ValueError("missing Gamma receipt")
    market_id = str(frozen.get("id", ""))
    if not market_id:
        raise ValueError("frozen market id is missing")

    if isinstance(entry.get("path"), str):
        receipt_path = _scoped_receipt(entry["path"])
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("cannot read Gamma transport receipt") from exc
        if receipt.get("method") != "GET":
            raise ValueError("Gamma receipt is not a GET")
        url = receipt.get("url")
        status = receipt.get("status_code")
        received = receipt.get("received_utc")
        started = receipt.get("started_utc")
        raw_sha = receipt.get("raw_sha256")
        body_path = _scoped_receipt(receipt.get("gzip_path"))
        compressed = body_path.read_bytes()
        if hashlib.sha256(compressed).hexdigest() != receipt.get("gzip_sha256"):
            raise ValueError("Gamma receipt gzip hash mismatch")
        try:
            raw_body = gzip.decompress(compressed)
        except OSError as exc:
            raise ValueError("Gamma receipt body is not valid gzip") from exc
        if hashlib.sha256(raw_body).hexdigest() != raw_sha:
            raise ValueError("Gamma receipt raw body hash mismatch")
        if entry.get("raw_sha256") != raw_sha:
            raise ValueError("case Gamma hash differs from transport receipt")
        if entry.get("status_code") != status:
            raise ValueError("case Gamma status differs from transport receipt")
    else:
        # The 1745 packet embeds its transport metadata per case and keeps the
        # exact uncompressed response body; require every available binding.
        url = entry.get("request_url")
        status = entry.get("status_code")
        received = entry.get("received_utc")
        started = entry.get("started_utc")
        raw_path = _scoped_receipt(entry.get("raw_path"))
        raw_body = raw_path.read_bytes()
        raw_sha = hashlib.sha256(raw_body).hexdigest()
        if raw_sha != entry.get("body_sha256"):
            raise ValueError("legacy Gamma body hash mismatch")

    parsed_url = urlparse(str(url or ""))
    if ((parsed_url.scheme, parsed_url.netloc, parsed_url.path) !=
            ("https", "gamma-api.polymarket.com", f"/markets/{market_id}") or parsed_url.query or parsed_url.fragment):
        raise ValueError("Gamma receipt is not the exact frozen-market endpoint")
    if status != 200:
        raise ValueError("Gamma receipt is not HTTP 200")
    receipt_dt = _aware_utc(received, "Gamma receipt received_utc")
    if entry.get("received_utc") and _aware_utc(entry["received_utc"], "case Gamma received_utc") != receipt_dt:
        raise ValueError("case Gamma timestamp differs from receipt")
    if started:
        started_dt = _aware_utc(started, "Gamma request started_utc")
        if started_dt > receipt_dt:
            raise ValueError("Gamma receipt time precedes request start")
    try:
        raw_gamma = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise ValueError("Gamma receipt body is not valid JSON") from exc
    if not isinstance(raw_gamma, dict):
        raise ValueError("Gamma receipt body is not a market object")
    if raw_gamma.get("id") is None or str(raw_gamma.get("id")) != market_id:
        raise ValueError("Gamma response market id differs from frozen market")
    if str(raw_gamma.get("conditionId", "")).lower() != str(frozen.get("conditionId", "")).lower():
        raise ValueError("Gamma response condition id differs from frozen market")
    if case.get("current_gamma") != raw_gamma:
        raise ValueError("captured Gamma market differs from hashed response body")
    return received


def book_age_seconds(capture: dict, book_row: dict, book_timestamp_ms: Any) -> tuple[str, float]:
    """Compute age against the matching CLOB response receipt, never Gamma."""
    received = _verified_book_received_utc(capture, book_row)
    try:
        timestamp_ms = float(book_timestamp_ms)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid book timestamp") from exc
    if not math.isfinite(timestamp_ms):
        raise ValueError("invalid book timestamp")
    age = _aware_utc(received, "books receipt received_utc").timestamp() - timestamp_ms / 1000.0
    return received, age


def quote(index: int, quote_path: str | Path) -> tuple[dict, dict, Path]:
    """Load and identity-check one case from a caller-selected quote packet."""
    path = Path(quote_path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve(strict=True)
    if not path.is_file():
        raise ValueError("quote_path must name an existing file")
    raw = path.read_bytes()
    capture = json.loads(raw)
    matches = [row for row in capture.get("cases", []) if int(row.get("review_index", -1)) == index]
    if len(matches) != 1:
        raise ValueError(f"expected one case {index} in quote packet, found {len(matches)}")
    case = matches[0]
    frozen = ledger.universe()[index]
    gamma_received_utc = _verified_gamma_received_utc(case, frozen)
    # Keep verified provenance local to this parsed packet; do not rewrite the
    # captured source object or its immutable on-disk representation.
    case = dict(case)
    case["_verified_gamma_received_utc"] = gamma_received_utc
    identity = case.get("frozen_identity") or case.get("frozen", {})
    if not case.get("criteria_exact_match"):
        raise ValueError("Gamma criteria do not exactly match frozen case")
    if str(identity.get("market_id", identity.get("id"))) != str(frozen["id"]):
        raise ValueError("quote packet frozen market id mismatch")
    if str(identity.get("condition_id", identity.get("conditionId", ""))).lower() != str(frozen["conditionId"]).lower():
        raise ValueError("quote packet frozen condition id mismatch")
    if identity.get("criteria_sha256") != frozen.get("criteria_sha256"):
        raise ValueError("quote packet frozen criteria hash mismatch")
    checks = case.get("identity_checks")
    if checks is not None and any(checks.get(k) is not True for k in ("market_id", "condition_id", "question", "description", "outcomes", "token_ids")):
        raise ValueError("quote packet has failed or missing identity checks")
    gamma = case.get("current_gamma") or {}
    for gamma_key, frozen_key in (
        ("id", "id"), ("slug", "slug"), ("conditionId", "conditionId"), ("question", "question"),
        ("description", "description"), ("resolutionSource", "resolutionSource"),
        ("endDate", "endDate"),
    ):
        actual, expected = gamma.get(gamma_key), frozen.get(frozen_key)
        if gamma_key == "conditionId":
            equal = str(actual or "").lower() == str(expected or "").lower()
        else:
            equal = actual == expected
        if not equal:
            raise ValueError(f"Gamma {gamma_key} differs from frozen case")
    outcomes = json.loads(gamma["outcomes"]) if isinstance(gamma.get("outcomes"), str) else gamma.get("outcomes")
    token_ids = json.loads(gamma["clobTokenIds"]) if isinstance(gamma.get("clobTokenIds"), str) else gamma.get("clobTokenIds")
    if not isinstance(outcomes, list) or not isinstance(token_ids, list) or len(outcomes) != len(token_ids):
        raise ValueError("Gamma outcome/token identity is malformed")
    if len(set(map(str, outcomes))) != len(outcomes) or len(set(map(str, token_ids))) != len(token_ids):
        raise ValueError("Gamma outcome/token identity contains duplicates")
    gamma_tokens = {str(outcome): str(token) for outcome, token in zip(outcomes, token_ids)}
    frozen_outcomes = frozen.get("outcomes", ["Yes", "No"])
    if isinstance(frozen_outcomes, str):
        frozen_outcomes = json.loads(frozen_outcomes)
    if set(gamma_tokens) != set(frozen_outcomes):
        raise ValueError("Gamma outcomes differ from frozen outcomes")
    frozen_token_ids = frozen.get("clobTokenIds")
    if isinstance(frozen_token_ids, str):
        frozen_token_ids = json.loads(frozen_token_ids)
    if not isinstance(frozen_token_ids, list) or len(frozen_token_ids) != len(frozen_outcomes):
        raise ValueError("frozen outcome/token identity is malformed")
    frozen_tokens = {str(outcome): str(token) for outcome, token in zip(frozen_outcomes, frozen_token_ids)}
    if gamma_tokens != frozen_tokens:
        raise ValueError("Gamma outcome/token mapping differs from frozen identity")
    seen = set()
    book_rows = case.get("books", [])
    if len(book_rows) != len(frozen_outcomes):
        raise ValueError("quote packet does not contain every frozen outcome row")
    for row in book_rows:
        outcome, token = row.get("outcome"), str(row.get("token_id", ""))
        if outcome not in gamma_tokens or gamma_tokens[outcome] != token or token in seen:
            raise ValueError("book outcome/token does not match exact Gamma identity")
        seen.add(token)
        book = row.get("book")
        if book:
            if str(book.get("market", "")).lower() != str(frozen["conditionId"]).lower():
                raise ValueError("book condition id mismatch")
            if str(book.get("asset_id")) != token:
                raise ValueError("book asset id mismatch")
        _verified_book_received_utc(capture, row)
    if seen != set(gamma_tokens.values()):
        raise ValueError("quote packet does not contain every frozen outcome token")
    return capture, case, path


def economics(
    index: int,
    p_yes: float,
    quote_path: str | Path,
    reserve: float = 0.20,
    days: float = 15,
    quantity: float = 10,
    *,
    reference_outcome: str | None = None,
) -> dict:
    """Compute hypothetical economics; p_yes belongs to reference_outcome.

    Legacy Yes/No markets keep their historical mapping when no reference is
    supplied. Markets with other labels require an explicit exact label.
    """
    if reference_outcome is not None and not isinstance(reference_outcome, str):
        raise ValueError("reference_outcome must be an exact outcome label string")
    try:
        p_yes = float(p_yes)
        reserve = float(reserve)
        days = float(days)
        quantity = float(quantity)
    except (TypeError, ValueError) as exc:
        raise ValueError("probability, reserve, days, and quantity must be numeric") from exc
    if not math.isfinite(p_yes) or not 0 <= p_yes <= 1:
        raise ValueError("p_yes must be finite and in [0, 1]")
    if not math.isfinite(reserve) or not 0 <= reserve <= 1:
        raise ValueError("reserve must be finite and in [0, 1]")
    if not math.isfinite(days) or days < 0:
        raise ValueError("days must be finite and nonnegative")
    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError("quantity must be finite and positive")
    capture, case, path = quote(index, quote_path)
    gamma = case["current_gamma"]
    outcomes = gamma.get("outcomes")
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except json.JSONDecodeError as exc:
            raise ValueError("captured outcomes are malformed") from exc
    if (not isinstance(outcomes, list) or len(outcomes) != 2
            or any(not isinstance(label, str) for label in outcomes)
            or len(set(outcomes)) != 2):
        raise ValueError("economics requires exactly two distinct string outcome labels")
    if reference_outcome is None:
        if set(outcomes) != {"Yes", "No"}:
            raise ValueError("reference_outcome is required unless outcomes are exactly Yes/No")
        probability_reference = "Yes"
    else:
        if reference_outcome not in outcomes:
            raise ValueError("reference_outcome must exactly match one captured outcome label")
        probability_reference = reference_outcome
    other_outcome = next(label for label in outcomes if label != probability_reference)
    hurdle = json.loads((ROOT / "notes/aave_hurdle.json").read_text(encoding="utf-8"))
    gamma_receipt_utc = case.get("_verified_gamma_received_utc")
    if not gamma_receipt_utc:
        raise ValueError("quote packet missing Gamma capture timestamp")
    _aware_utc(gamma_receipt_utc, "Gamma receipt received_utc")
    curve = fee_schedule(gamma)
    result = {
        "both_sides_considered": True,
        "quote_file": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
        "quote_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "quote_capture_utc": capture.get("created_utc") or capture.get("captured_utc"),
        "gamma_received_utc": gamma_receipt_utc,
        "hypothetical_gross_shares": quantity,
        "horizon_days": days,
        "probability_reference_outcome": probability_reference,
        "actual_entry_reserve_pp": reserve * 100,
        "fee_curve": asdict(curve),
        "fee_convention": "Repository USD-equivalent fee per gross share, ceil5dp per-side; hypothetical planning, not an execution certificate.",
        "alternative": {
            **hurdle,
            "constant_rate_sensitivity_not_forecast": True,
            "funding_and_operations_costs_not_assumed_free": True,
        },
        "sides": {},
    }
    probabilities = {probability_reference: p_yes, other_outcome: 1 - p_yes}
    for row in case["books"]:
        probability = probabilities[row["outcome"]]
        book = row.get("book")
        if not row.get("available") or not book:
            result["sides"][row["outcome"]] = {
                "probability": probability,
                "book_available": False,
                "cost": None,
                "explicit_failure": "exact token has no returned book",
            }
            continue
        book_received, age = book_age_seconds(capture, row, book.get("timestamp"))
        costs = {}
        for direction in ("asks", "bids"):
            levels = sorted(book[direction], key=lambda level: float(level["price"]), reverse=direction == "bids")
            left = quantity
            gross = fee = 0.0
            fills = []
            for level in levels:
                filled = min(left, float(level["size"]))
                if filled <= 0:
                    continue
                price = float(level["price"])
                gross += filled * price
                fee += filled * fee_per_share(gamma, price)
                fills.append({"shares": filled, "price": price})
                left -= filled
                if left <= 1e-9:
                    break
            fee = float(Decimal(str(fee)).quantize(Decimal(".00001"), rounding=ROUND_CEILING))
            complete = left <= 1e-9
            costs[direction] = {
                "complete": complete,
                "filled": quantity - left,
                "gross": gross,
                "fee": fee,
                "fills": fills,
                "net": (gross + fee if direction == "asks" else gross - fee) if complete else None,
            }
        cost = costs["asks"]["net"]
        result["sides"][row["outcome"]] = {
            "probability": probability,
            "selected_stress_probability": max(0, probability - reserve),
            "best_bid": max((float(level["price"]) for level in book["bids"]), default=None),
            "best_ask": min((float(level["price"]) for level in book["asks"]), default=None),
            "minimum_shares": book.get("min_order_size"),
            "tick_size": book.get("tick_size"),
            "book_timestamp": book["timestamp"],
            "book_received_utc": book_received,
            "book_age_seconds_at_receipt": age,
            "passed_180s_at_receipt": 0 <= age <= 180,
            "walks": costs,
            "taker_cost_usd": cost,
            "central_expected_profit_usd": quantity * probability - cost if cost is not None else None,
            "selected_stress_profit_usd": quantity * max(0, probability - reserve) - cost if cost is not None else None,
            "break_even_before_carry": cost / quantity if cost is not None else None,
            "break_even_constant_carry": cost * (1 + hurdle["apy"]) ** (days / 365) / quantity if cost is not None else None,
            "current_execution_authorization": False,
        }
    return result
