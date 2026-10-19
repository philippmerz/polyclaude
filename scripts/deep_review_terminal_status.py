#!/usr/bin/env python3
"""Capture exact Gamma status for an explicit bounded set of frozen cases.

This read-only helper identifies markets that may already be terminal. It
never excludes a case, contacts the CLOB/account APIs, or writes financial
state. Every Gamma response is retained as gzip with timing and hash receipts.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

import httpx

import deep_review_ledger as ledger

ROOT = Path(__file__).resolve().parents[1]
GAMMA = "https://gamma-api.polymarket.com/markets/"
MAX_INDICES = 30


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _array(value: Any) -> list | None:
    """Parse only JSON-encoded arrays; preserve element types and order."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, list) else None


def identity_checks(frozen: dict, gamma: Any) -> dict[str, bool]:
    if not isinstance(gamma, dict):
        return {key: False for key in (
            "market_id", "condition_id", "question", "slug", "description",
            "resolution_source", "end_date", "outcomes", "assets")}
    checks = {
        "market_id": gamma.get("id") == frozen.get("id"),
        "condition_id": gamma.get("conditionId") == frozen.get("conditionId"),
    }
    for field, frozen_field in (
        ("question", "question"), ("slug", "slug"),
        ("description", "description"), ("resolution_source", "resolutionSource"),
        ("end_date", "endDate"),
    ):
        checks[field] = gamma.get(frozen_field) == frozen.get(frozen_field)
    current_outcomes = _array(gamma.get("outcomes"))
    frozen_outcomes = _array(frozen.get("outcomes"))
    current_assets = _array(gamma.get("clobTokenIds"))
    frozen_assets = _array(frozen.get("clobTokenIds"))
    checks["outcomes"] = current_outcomes is not None and current_outcomes == frozen_outcomes
    checks["assets"] = current_assets is not None and current_assets == frozen_assets
    return checks


def _binary_pair(value: Any) -> bool:
    parsed = _array(value)
    if parsed is None or len(parsed) != 2:
        return False
    numbers: list[Decimal] = []
    for item in parsed:
        if isinstance(item, bool) or not isinstance(item, (int, float, str)):
            return False
        try:
            number = Decimal(str(item))
        except (InvalidOperation, ValueError):
            return False
        if not number.is_finite() or number not in (Decimal(0), Decimal(1)):
            return False
        numbers.append(number)
    return sorted(numbers) == [Decimal(0), Decimal(1)]


def classify(frozen: dict, gamma: Any) -> dict:
    checks = identity_checks(frozen, gamma)
    identity_exact = all(checks.values())
    state = {
        "closed_true": isinstance(gamma, dict) and gamma.get("closed") is True,
        "accepting_orders_false": isinstance(gamma, dict) and gamma.get("acceptingOrders") is False,
        "uma_resolved": isinstance(gamma, dict) and gamma.get("umaResolutionStatus") == "resolved",
        "binary_terminal_prices": isinstance(gamma, dict) and _binary_pair(gamma.get("outcomePrices")),
    }
    status_fields_present = isinstance(gamma, dict) and all(
        field in gamma for field in ("closed", "acceptingOrders", "umaResolutionStatus", "outcomePrices"))
    terminal = identity_exact and all(state.values())
    if terminal:
        label = "terminal_candidate"
    elif not identity_exact or not status_fields_present:
        label = "unknown_primary_review"
    else:
        label = "nonterminal_primary_review"
    return {
        "classification": label,
        "terminal_candidate": terminal,
        "identity_exact": identity_exact,
        "identity_checks": checks,
        "state_checks": state,
    }


def _repo_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("output paths must be repository-relative and cannot traverse")
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError("output path escapes repository")
    return resolved


def _write_new(path: Path, content: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)


def _hash_json(value: Any) -> str:
    packed = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(packed).hexdigest()


def capture(indices: list[int], output_dir: Path, log_dir: Path) -> dict:
    frozen = ledger.universe()
    if not indices or len(indices) > MAX_INDICES or len(set(indices)) != len(indices):
        raise ValueError(f"indices must be 1..{MAX_INDICES} unique values")
    unknown = [index for index in indices if index not in frozen]
    if unknown:
        raise ValueError(f"unknown review index(es): {unknown}")
    if output_dir == log_dir or output_dir in log_dir.parents or log_dir in output_dir.parents:
        raise ValueError("unit and raw-capture directories must be separate")
    if output_dir.exists() or log_dir.exists():
        raise FileExistsError("refusing to overwrite an output or capture directory")
    output_dir.mkdir(parents=True)
    log_dir.mkdir(parents=True)
    client = httpx.Client(timeout=20, follow_redirects=False)
    batch_cases = []
    try:
        for index in indices:
            rule = frozen[index]
            market_id = str(rule["id"])
            url = GAMMA + market_id
            started = utcnow()
            status_code = None
            raw = b""
            error = None
            headers: dict[str, str] = {}
            try:
                response = client.get(url)
                received = utcnow()
                status_code = response.status_code
                raw = response.content
                headers = {key: response.headers[key] for key in
                           ("date", "age", "cache-control", "last-modified", "content-type")
                           if key in response.headers}
            except Exception as exc:
                received = utcnow()
                error = f"{type(exc).__name__}: {exc}"
            compressed = gzip.compress(raw, mtime=0)
            body_name = f"{index:04d}_gamma.body.json.gz"
            receipt_name = f"{index:04d}_gamma.receipt.json"
            body_path = log_dir / body_name
            receipt_path = log_dir / receipt_name
            _write_new(body_path, compressed)
            receipt = {
                "review_index": index, "method": "GET", "url": url,
                "started_utc": started, "received_utc": received,
                "status_code": status_code, "headers": headers,
                "raw_bytes": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
                "gzip_path": body_path.relative_to(ROOT).as_posix(),
                "error": error,
            }
            _write_new(receipt_path, (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode())
            gamma = None
            parse_error = None
            if status_code == 200:
                try:
                    gamma = json.loads(raw)
                    if not isinstance(gamma, dict):
                        raise ValueError("Gamma response is not an object")
                except (json.JSONDecodeError, ValueError) as exc:
                    parse_error = f"{type(exc).__name__}: {exc}"
            else:
                parse_error = error or f"HTTP {status_code}"
            result = classify(rule, gamma)
            if parse_error:
                result["classification"] = "unknown_primary_review"
                result["terminal_candidate"] = False
            unit = {
                "review_index": index, "frozen_id": str(rule.get("id", "")),
                "frozen_condition_id": str(rule.get("conditionId", "")),
                "frozen_criteria_sha256": rule.get("criteria_sha256"),
                "frozen_identity_sha256": _hash_json({key: rule.get(key) for key in (
                    "id", "conditionId", "question", "slug", "description",
                    "resolutionSource", "endDate", "outcomes", "clobTokenIds")}),
                "receipt_path": receipt_path.relative_to(ROOT).as_posix(),
                "gamma_gzip_path": body_path.relative_to(ROOT).as_posix(),
                "http_status": status_code, "started_utc": started, "received_utc": received,
                "raw_sha256": receipt["raw_sha256"], "gzip_sha256": receipt["gzip_sha256"],
                "error": parse_error, **result,
                # Never copy outcomePrices or other market-derived price values into summaries.
            }
            unit_path = output_dir / f"case_{index:04d}.json"
            _write_new(unit_path, (json.dumps(unit, sort_keys=True, indent=2) + "\n").encode())
            batch_cases.append({
                "review_index": index, "unit_path": unit_path.relative_to(ROOT).as_posix(),
                "classification": unit["classification"],
                "terminal_candidate": unit["terminal_candidate"],
                "identity_exact": unit["identity_exact"], "http_status": status_code,
            })
    finally:
        client.close()
    batch = {
        "schema": "deep_review_terminal_status_batch.v1",
        "created_utc": utcnow(), "case_count": len(batch_cases), "cases": batch_cases,
    }
    batch_path = output_dir / "index.json"
    _write_new(batch_path, (json.dumps(batch, sort_keys=True, indent=2) + "\n").encode())
    return batch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--indices", required=True, help="explicit comma-separated frozen review indices")
    parser.add_argument("--output-dir", required=True, help="new repo-relative case-unit directory")
    parser.add_argument("--log-dir", required=True, help="new repo-relative gzip receipt directory")
    args = parser.parse_args(argv)
    try:
        raw_indices = [part.strip() for part in args.indices.split(",")]
        if any(not part.isdecimal() for part in raw_indices):
            raise ValueError("indices must be comma-separated positive integers")
        indices = [int(part) for part in raw_indices]
        output = _repo_path(args.output_dir)
        logs = _repo_path(args.log_dir)
        result = capture(indices, output, logs)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(f"terminal status capture failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
