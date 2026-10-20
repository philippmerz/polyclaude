#!/usr/bin/env python3
"""Bounded, receipt-preserving public Gamma/CLOB capture for deep review.

No account, ledger, order, reservation, or prior access. Bodies are gzipped as
received; response status and UTC start/receive times are recorded before JSON
parsing. Geoblock raw bytes are private because the endpoint may return an IP.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from typing import Any

import httpx

import deep_review_ledger as ledger

ROOT = Path(__file__).resolve().parents[1]
GAMMA = "https://gamma-api.polymarket.com/markets/"
FEE = "https://clob.polymarket.com/clob-markets/"
BOOKS = "https://clob.polymarket.com/books"
FULL_MARKET = "https://clob.polymarket.com/markets/"
GEO = "https://polymarket.com/api/geoblock"
SAFE_HEADERS = ("date", "age", "cache-control", "last-modified", "content-type")


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_array(value: Any, label: str) -> list:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{label} is not a JSON array") from exc
    if not isinstance(value, list):
        raise ValueError(f"{label} is not an array")
    return value


def identity_checks(frozen: dict, gamma: dict) -> dict[str, bool]:
    """Check literal rule and outcome-token binding, never just the title."""
    checks = {
        "market_id": str(gamma.get("id", "")) == str(frozen.get("id", "")),
        "condition_id": str(gamma.get("conditionId", "")).lower()
        == str(frozen.get("conditionId", "")).lower(),
    }
    for key in ("question", "description", "slug", "resolutionSource", "endDate"):
        checks[key] = gamma.get(key) == frozen.get(key)
    checks["outcomes"] = _json_array(gamma.get("outcomes"), "Gamma outcomes") == _json_array(
        frozen.get("outcomes"), "frozen outcomes")
    checks["token_ids"] = _json_array(gamma.get("clobTokenIds"), "Gamma token IDs") == _json_array(
        frozen.get("clobTokenIds"), "frozen token IDs")
    return checks


def compact_market_identity(payload: dict, condition_id: str, token_map: dict[str, str]) -> None:
    """Validate compact condition and exact, duplicate-free token mapping."""
    if str(payload.get("c", "")).lower() != condition_id.lower():
        raise ValueError("compact fee condition ID mismatch")
    rows = payload.get("t")
    if not isinstance(rows, list) or len(rows) != len(token_map):
        raise ValueError("compact condition outcome/token map differs from frozen market")
    got = {}
    seen_tokens = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("compact condition outcome/token row is malformed")
        outcome, token = row.get("o"), row.get("t")
        if not isinstance(outcome, str) or not outcome or not isinstance(token, str) or not token:
            raise ValueError("compact condition outcome/token row is malformed")
        if outcome in got or token in seen_tokens:
            raise ValueError("compact condition outcome/token map contains duplicates")
        got[outcome] = token
        seen_tokens.add(token)
    if got != token_map:
        raise ValueError("compact condition outcome/token map differs from frozen market")


def compact_fee_fields(payload: dict, condition_id: str, token_map: dict[str, str]) -> dict:
    """Extract the fee descriptor from `fd`; top-level `r` is rebate metadata."""
    compact_market_identity(payload, condition_id, token_map)
    raw = payload.get("fd")
    if not isinstance(raw, dict):
        raise ValueError("compact response has no fee descriptor fd")
    if isinstance(raw.get("r"), bool) or isinstance(raw.get("e"), bool):
        raise ValueError("compact fee descriptor fd is malformed")
    try:
        rate, exponent, taker_only = float(raw["r"]), float(raw["e"]), raw["to"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("compact fee descriptor fd is malformed") from exc
    if not (math.isfinite(rate) and math.isfinite(exponent)
            and 0 <= rate < 1 and 0 < exponent <= 10 and isinstance(taker_only, bool)):
        raise ValueError("compact fee descriptor fd has invalid values")
    return {"r": rate, "e": exponent, "to": taker_only}


def fee_free_gamma_schedule(gamma: dict) -> bool:
    """Accept absent/null schedule, or an explicitly valid zero-rate schedule."""
    if "feeSchedule" not in gamma or gamma["feeSchedule"] is None:
        return True
    schedule = gamma["feeSchedule"]
    if not isinstance(schedule, dict):
        return False
    try:
        rate, exponent, taker_only = schedule["rate"], schedule["exponent"], schedule["takerOnly"]
        if isinstance(rate, bool) or isinstance(exponent, bool):
            return False
        rate, exponent = float(rate), float(exponent)
    except (KeyError, TypeError, ValueError):
        return False
    return (math.isfinite(rate) and rate == 0 and math.isfinite(exponent)
            and 0 < exponent <= 10 and isinstance(taker_only, bool))


def corroborate_fee_free_market(full: dict, condition_id: str, token_map: dict[str, str]) -> None:
    """Require exact full-market condition/tokens and explicit numeric zero fee."""
    if not isinstance(full, dict) or str(full.get("condition_id", "")).lower() != condition_id.lower():
        raise ValueError("full CLOB fee-free condition ID mismatch")
    rows = full.get("tokens")
    if not isinstance(rows, list) or len(rows) != len(token_map):
        raise ValueError("full CLOB outcome/token map differs from frozen market")
    got = {}
    seen_tokens = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("full CLOB outcome/token row is malformed")
        outcome, token = row.get("outcome"), row.get("token_id")
        if not isinstance(outcome, str) or not outcome or not isinstance(token, str) or not token:
            raise ValueError("full CLOB outcome/token row is malformed")
        if outcome in got or token in seen_tokens:
            raise ValueError("full CLOB outcome/token map contains duplicates")
        got[outcome] = token
        seen_tokens.add(token)
    if got != token_map:
        raise ValueError("full CLOB outcome/token map differs from frozen market")
    fee = full.get("taker_base_fee")
    if isinstance(fee, bool) or not isinstance(fee, (int, float)) or not math.isfinite(fee) or fee != 0:
        raise ValueError("full CLOB taker_base_fee is not explicit numeric zero")


def fee_parity(gamma: dict, descriptor: dict) -> bool | None:
    schedule = gamma.get("feeSchedule")
    if not isinstance(schedule, dict):
        return None
    try:
        return (
            float(schedule["rate"]) == float(descriptor["r"])
            and float(schedule["exponent"]) == float(descriptor["e"])
            and schedule["takerOnly"] is descriptor["to"]
        )
    except (KeyError, TypeError, ValueError):
        return False


def fee_parity_error(parity: bool | None) -> str | None:
    if parity is True:
        return None
    if parity is None:
        return "compact_fee_vs_gamma_schedule_parity_unavailable"
    return "compact_fee_vs_gamma_schedule_mismatch"


def book_availability_status(status_code: int, payload_valid: bool, available: bool) -> str:
    if available:
        return "returned_in_http_200" if status_code == 200 else f"returned_in_http_{status_code}"
    if status_code != 200:
        return f"unavailable_http_{status_code}"
    if not payload_valid:
        return "invalid_http_200_books_payload"
    return "omitted_from_http_200"


def _safe_repo_path(value: str) -> Path:
    p = Path(value)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("output paths must be repo-relative and cannot traverse")
    resolved = (ROOT / p).resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError("path escapes repo")
    return resolved


class Collector:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.public_dir = log_dir / "public"
        self.private_dir = log_dir / "private"
        if log_dir.exists():
            raise FileExistsError(f"refusing existing capture directory: {log_dir}")
        self.public_dir.mkdir(parents=True)
        self.private_dir.mkdir()
        os.chmod(self.private_dir, 0o700)
        self.receipts: list[dict] = []
        self.errors: list[str] = []
        self.client = httpx.Client(timeout=20)

    def request(self, *, name: str, method: str, url: str, json_body: Any = None,
                private: bool = False) -> tuple[int, bytes, dict]:
        started = utcnow()
        response = self.client.request(method, url, json=json_body)
        received = utcnow()
        raw = response.content
        raw_sha = hashlib.sha256(raw).hexdigest()
        compressed = gzip.compress(raw, mtime=0)
        folder = self.private_dir if private else self.public_dir
        body_path = folder / f"{name}.body.json.gz"
        mode = 0o600 if private else 0o644
        fd = os.open(body_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(compressed)
        request_id = f"{name}_{len(self.receipts)+1:02d}"
        receipt = {
            "request_id": request_id, "method": method, "url": url,
            "started_utc": started, "received_utc": received,
            "status_code": response.status_code,
            "headers": {k: response.headers[k] for k in SAFE_HEADERS if k in response.headers},
            "raw_sha256": raw_sha, "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
            "raw_bytes": len(raw), "gzip_path": body_path.relative_to(ROOT).as_posix(),
            "json_request_body": json_body,
        }
        receipt_path = folder / f"{name}.receipt.json"
        receipt_bytes = (json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n").encode()
        fd = os.open(receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(receipt_bytes)
        row = {k: receipt[k] for k in ("request_id", "method", "url", "started_utc", "received_utc",
                                         "status_code", "raw_sha256", "gzip_sha256", "raw_bytes", "gzip_path")}
        row["receipt_path"] = receipt_path.relative_to(ROOT).as_posix()
        row["type"] = "books_batch" if url == BOOKS else ("geoblock" if private else "http")
        self.receipts.append(row)
        return response.status_code, raw, row

    @staticmethod
    def parse(status: int, body: bytes, name: str) -> Any:
        if status != 200:
            raise ValueError(f"{name} HTTP {status}")
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{name} returned invalid JSON") from exc


def capture(indices: list[int], output: Path, log_dir: Path, include_geo: bool = True) -> dict:
    frozen = ledger.universe()
    if not indices or len(set(indices)) != len(indices):
        raise ValueError("indices must be a nonempty unique list")
    collector = Collector(log_dir)
    cases: list[dict] = []
    all_tokens: list[str] = []
    # One exact market and compact descriptor request per frozen case.
    for index in indices:
        if index not in frozen:
            raise ValueError(f"unknown review index {index}")
        rule = frozen[index]
        market_id, condition_id = str(rule["id"]), str(rule["conditionId"])
        gamma_obj, fee_obj = {}, {}
        case_errors = []
        gamma_receipt = {}
        fee_receipt = {}
        try:
            status, raw, gamma_receipt = collector.request(
                name=f"{index:04d}_gamma", method="GET", url=GAMMA + market_id)
            gamma_obj = collector.parse(status, raw, f"Gamma {index}")
            if not isinstance(gamma_obj, dict):
                raise ValueError("Gamma response is not a market object")
        except Exception as exc:
            case_errors.append(f"gamma:{type(exc).__name__}:{exc}")
        try:
            checks = identity_checks(rule, gamma_obj) if gamma_obj else {}
        except Exception as exc:
            checks = {"identity_parse": False}
            case_errors.append(f"gamma_identity:{type(exc).__name__}:{exc}")
        exact = bool(checks) and all(checks.values())
        if not exact:
            case_errors.append("gamma_identity_mismatch_or_unavailable")
        outcomes = _json_array(rule["outcomes"], "frozen outcomes")
        token_ids = _json_array(rule["clobTokenIds"], "frozen token IDs")
        token_map = {str(o): str(t) for o, t in zip(outcomes, token_ids)}
        fee_received = {}
        try:
            status, raw, fee_receipt = collector.request(
                name=f"{index:04d}_fee", method="GET", url=FEE + condition_id)
            fee_payload = collector.parse(status, raw, f"compact fee {index}")
            compact_market_identity(fee_payload, condition_id, token_map)
            fd = fee_payload.get("fd")
            if isinstance(fd, dict):
                fee_obj = compact_fee_fields(fee_payload, condition_id, token_map)
                if gamma_obj.get("feesEnabled") is False and (
                        fee_obj["r"] != 0 or not fee_free_gamma_schedule(gamma_obj)):
                    raise ValueError("fee-disabled Gamma contradicts compact descriptor or schedule")
                parity = fee_parity(gamma_obj, fee_obj) if gamma_obj else None
                fee_received = {"descriptor": fee_obj, "http_status": status,
                                "received_utc": fee_receipt["received_utc"],
                                "receipt_path": fee_receipt["receipt_path"],
                                "raw_sha256": fee_receipt["raw_sha256"],
                                "gzip_sha256": fee_receipt["gzip_sha256"],
                                "structured_gamma_parity": parity}
                parity_error = fee_parity_error(parity)
                if parity_error:
                    case_errors.append(parity_error)
            elif fd is None:
                if not (exact and gamma_obj.get("feesEnabled") is False):
                    raise ValueError("compact response has no fee descriptor fd")
                if not fee_free_gamma_schedule(gamma_obj):
                    raise ValueError("fee-disabled Gamma schedule is malformed or nonzero")
                full_status, full_raw, full_receipt = collector.request(
                    name=f"{index:04d}_full_fee_free", method="GET", url=FULL_MARKET + condition_id)
                full_payload = collector.parse(full_status, full_raw, f"full fee-free market {index}")
                corroborate_fee_free_market(full_payload, condition_id, token_map)
                fee_received = {"descriptor": None, "http_status": status,
                                "received_utc": fee_receipt["received_utc"],
                                "receipt_path": fee_receipt["receipt_path"],
                                "raw_sha256": fee_receipt["raw_sha256"],
                                "gzip_sha256": fee_receipt["gzip_sha256"],
                                "structured_gamma_parity": None,
                                "fee_free_corroborated": True,
                                "basis": "exact_gamma_fees_disabled_and_full_clob_numeric_zero_taker_base_fee",
                                "full_market_receipt_path": full_receipt["receipt_path"],
                                "full_market_raw_sha256": full_receipt["raw_sha256"],
                                "full_market_gzip_sha256": full_receipt["gzip_sha256"],
                                "full_market_received_utc": full_receipt["received_utc"]}
            else:
                raise ValueError("compact fee descriptor fd is malformed")
        except Exception as exc:
            case_errors.append(f"fee:{type(exc).__name__}:{exc}")
            fee_payload = None
            fee_received = {"error": type(exc).__name__,
                            "receipt_path": fee_receipt.get("receipt_path"),
                            "status_code": fee_receipt.get("status_code")}
        if exact:
            all_tokens.extend(token_ids)
        cases.append({
            "review_index": index,
            "frozen_identity": {"market_id": market_id, "condition_id": condition_id,
                                "criteria_sha256": rule["criteria_sha256"],
                                "question": rule["question"]},
            "current_gamma": gamma_obj,
            "gamma_receipt": {"path": gamma_receipt.get("receipt_path"),
                              "status_code": gamma_receipt.get("status_code"),
                              "received_utc": gamma_receipt.get("received_utc"),
                              "raw_sha256": gamma_receipt.get("raw_sha256")},
            "criteria_exact_match": exact,
            "identity_checks": checks,
            "optionalfee_descriptor": fee_received,
            "books": [],
            "access_status": "gamma_identity_exact" if exact and not case_errors else "capture_gap_or_mismatch",
            "capture_errors": case_errors,
        })
    # One captured books POST for the exact tokens whose Gamma identity matched.
    if all_tokens:
        req_body = [{"token_id": token} for token in all_tokens]
        status, raw, batch = collector.request(name="books_batch_01", method="POST",
                                               url=BOOKS, json_body=req_body)
        parsed = None
        books_payload_valid = False
        try:
            parsed = collector.parse(status, raw, "CLOB books batch")
            if not isinstance(parsed, list):
                raise ValueError("books response is not an array")
            # strict token join; reject duplicates and unexpected assets
            wanted = set(all_tokens); mapped = {}
            for row in parsed:
                if not isinstance(row, dict) or str(row.get("asset_id", "")) not in wanted:
                    raise ValueError("books response contains malformed/unrequested asset")
                token = str(row["asset_id"])
                if token in mapped:
                    raise ValueError("books response contains duplicate token")
                mapped[token] = row
            books_payload_valid = True
        except Exception as exc:
            collector.errors.append(f"books:{type(exc).__name__}:{exc}")
            mapped = {}
        receipt = json.loads(_safe_repo_path(batch["receipt_path"]).read_text())
        for case in cases:
            gamma = case["current_gamma"]
            if not case["criteria_exact_match"]:
                continue
            outcomes = _json_array(gamma["outcomes"], "Gamma outcomes")
            tokens = _json_array(gamma["clobTokenIds"], "Gamma tokens")
            for outcome, token in zip(outcomes, tokens):
                book = mapped.get(str(token))
                case["books"].append({"outcome": str(outcome), "token_id": str(token),
                    "available": isinstance(book, dict),
                    "availability_status": book_availability_status(
                        status, books_payload_valid, isinstance(book, dict)),
                    "http_status": status,
                    "book": book,
                    "received_utc": batch["received_utc"], "request_id": batch["request_id"],
                    "request_raw_sha256": batch["raw_sha256"]})
            if (len(case["books"]) != len(outcomes)
                    or any(not row["available"] for row in case["books"])):
                case["capture_errors"].append("outcome_book_rows_incomplete")
                case["access_status"] = "capture_gap_or_mismatch"
    if include_geo:
        try:
            status, raw, geo_rec = collector.request(name="geoblock", method="GET", url=GEO, private=True)
            geo = collector.parse(status, raw, "geoblock")
            # Output only safe fields; never return/print the endpoint IP.
            geo_summary = {"status_code": status, "received_utc": geo_rec["received_utc"],
                           "blocked": geo.get("blocked"), "country": geo.get("country"),
                           "region": geo.get("region"), "raw_sha256": geo_rec["raw_sha256"],
                           "private_receipt_path": geo_rec["receipt_path"]}
        except Exception as exc:
            geo_summary = {"error": f"{type(exc).__name__}:{exc}"}
            collector.errors.append("geoblock:" + type(exc).__name__)
    else:
        geo_summary = None
    capture_obj = {"schema": "polyclaude.deep_review_quote_resume.v1",
                   "created_utc": utcnow(), "scope_indices": indices,
                   "source_rules_path": "research/2026-10-17-primary-market-review-rules.jsonl.gz",
                   "cases": cases, "clob_transport_receipts": collector.receipts,
                   "host_blocked_http": {}, "gamma_host_blocked_http": {},
                   "freshness_threshold_seconds": 180,
                   "freshness_note": "Compute age from matched receipt; no price or freshness gate is implied here.",
                   "geoblock": geo_summary, "capture_errors": collector.errors}
    all_errors = list(collector.errors)
    for case in cases:
        all_errors.extend(f"case_{case['review_index']}:{e}" for e in case["capture_errors"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output_bytes = (json.dumps(capture_obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(output_bytes)
    manifest = {"schema": "deep_review_public_capture_manifest.v1", "output": output.relative_to(ROOT).as_posix(),
                "output_bytes": len(output_bytes), "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
                "indices": indices, "receipts": collector.receipts, "geoblock": geo_summary,
                "errors": all_errors}
    manifest_path = log_dir / "capture_manifest.json"
    mb = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(mb)
    return {"output": output.relative_to(ROOT).as_posix(), "bytes": len(output_bytes),
            "sha256": hashlib.sha256(output_bytes).hexdigest(), "manifest": manifest_path.relative_to(ROOT).as_posix(),
            "manifest_bytes": len(mb), "manifest_sha256": hashlib.sha256(mb).hexdigest(),
            "cases": len(cases), "exact_gamma": sum(c["criteria_exact_match"] for c in cases),
            "fee_descriptors": sum(isinstance(c["optionalfee_descriptor"].get("descriptor"), dict) for c in cases),
            "fee_free_corroborated": sum(c["optionalfee_descriptor"].get("fee_free_corroborated") is True for c in cases),
            "book_rows": sum(len(c["books"]) for c in cases), "errors": all_errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--indices", required=True, help="comma-separated frozen review indices")
    parser.add_argument("--output", required=True, help="new repo-relative quote packet JSON")
    parser.add_argument("--log-dir", required=True, help="new repo-relative raw receipt directory")
    parser.add_argument("--no-geoblock", action="store_true")
    args = parser.parse_args()
    try:
        indices = [int(x) for x in args.indices.split(",")]
        output, log_dir = _safe_repo_path(args.output), _safe_repo_path(args.log_dir)
        result = capture(indices, output, log_dir, include_geo=not args.no_geoblock)
    except Exception as exc:
        print(f"capture failed closed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
