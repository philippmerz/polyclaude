#!/usr/bin/env python3
"""Capped, shadow-only client for Jev System One inference.

This tool has no caller in the trading, watcher, or execution paths.  It sends
an explicitly supplied typed research state and questions to System One, prints
the structured response, and writes only aggregate metering metadata locally.

Examples:
  python scripts/jev_shadow.py ask --state-file /tmp/state.json --questions-file /tmp/questions.json
  python scripts/jev_shadow.py models
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

import _paths as _secrets

_secrets.install_scrubbing_excepthook()

API_BASE = "https://api.typesafe.ai"
MODEL = "jev-1.13.0"
USAGE_LOG = Path.home() / ".polyclaude" / "jev_usage.jsonl"
MAX_STATE_CHARS = 12_000
MAX_QUESTIONS = 8
MAX_QUESTION_CHARS = 1_200
MAX_QUESTION_TOTAL_CHARS = 6_000
MAX_TIMEOUT = 30.0
MAX_REPEATS_PER_DAY = 3
INPUT_TOKEN_COST_PER_MILLION_USD = 0.042
MONTHLY_COST_CAP_USD = 0.50
_QUESTION_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")


class InputError(ValueError):
    """Raised before a network request when a shadow request is unsafe."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def state_hash(state: dict[str, Any]) -> str:
    """Stable identifier for rate limiting without retaining supplied state."""
    return hashlib.sha256(_canonical_json(state).encode("utf-8")).hexdigest()


def load_json_object(file_path: str) -> dict[str, Any]:
    try:
        value = json.loads(Path(file_path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read JSON object: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError("state must be a JSON object")
    return value


def load_questions(file_path: str) -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(Path(file_path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read questions JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError("questions must be a JSON object keyed by question ID")
    return validate_request(value, {})


def _valid_criteria(question_type: str, criteria: Any) -> bool:
    if question_type == "noul":
        return isinstance(criteria, dict) and set(criteria) == {"true", "false"} and all(
            isinstance(value, str) and value.strip() for value in criteria.values()
        )
    if question_type == "choice":
        return isinstance(criteria, dict) and bool(criteria) and all(
            isinstance(key, str) and key and (value is None or isinstance(value, str))
            for key, value in criteria.items()
        )
    if question_type == "score":
        return isinstance(criteria, list) and len(criteria) >= 2 and all(
            isinstance(value, str) and value.strip() for value in criteria
        )
    return False


def validate_request(questions: dict[str, Any], state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Validate the bounded typed input without mutating it."""
    if len(_canonical_json(state)) > MAX_STATE_CHARS:
        raise InputError(f"state exceeds {MAX_STATE_CHARS} characters")
    if not 1 <= len(questions) <= MAX_QUESTIONS:
        raise InputError(f"questions must contain 1 to {MAX_QUESTIONS} items")
    checked: dict[str, dict[str, Any]] = {}
    total = 0
    for question_id, question in questions.items():
        if not isinstance(question_id, str) or not _QUESTION_ID.fullmatch(question_id):
            raise InputError("question IDs must match [A-Za-z][A-Za-z0-9_-]{0,63}")
        if not isinstance(question, dict):
            raise InputError(f"question {question_id!r} must be an object")
        if set(question) != {"type", "instructions", "criteria"}:
            raise InputError(f"question {question_id!r} must contain only type, instructions, criteria")
        if question.get("type") not in {"noul", "choice", "score"}:
            raise InputError(f"question {question_id!r} has unsupported type")
        if not isinstance(question["instructions"], str) or not question["instructions"].strip():
            raise InputError(f"question {question_id!r} needs non-empty string instructions")
        if not _valid_criteria(question["type"], question["criteria"]):
            raise InputError(f"question {question_id!r} has invalid criteria for {question['type']}")
        question_chars = len(question["instructions"]) + len(_canonical_json(question["criteria"]))
        if question_chars > MAX_QUESTION_CHARS:
            raise InputError(f"question {question_id!r} exceeds {MAX_QUESTION_CHARS} characters")
        total += question_chars
        if total > MAX_QUESTION_TOTAL_CHARS:
            raise InputError(f"questions exceed {MAX_QUESTION_TOTAL_CHARS} total characters")
        checked[question_id] = {key: question[key] for key in ("type", "instructions", "criteria")}
    return checked


def _read_usage() -> list[dict[str, Any]]:
    if not USAGE_LOG.exists():
        return []
    records = []
    for line in USAGE_LOG.read_text(errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def check_repeat_limit(digest: str, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=1)
    repeats = 0
    for record in _read_usage():
        if record.get("state_hash") != digest:
            continue
        try:
            created = datetime.fromisoformat(str(record["ts"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            continue
        if created >= cutoff:
            repeats += 1
    if repeats >= MAX_REPEATS_PER_DAY:
        raise InputError(f"repeat cap reached ({MAX_REPEATS_PER_DAY} per state hash / 24h)")


def _month_cost(now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    total = 0.0
    for record in _read_usage():
        try:
            created = datetime.fromisoformat(str(record["ts"]).replace("Z", "+00:00"))
            cost = float(record.get("estimated_cost_usd"))
        except (KeyError, TypeError, ValueError):
            continue
        if created.year == now.year and created.month == now.month:
            total += cost
    return total


def check_monthly_cost_cap(now: datetime | None = None) -> None:
    # Reserve the worst case allowed by our character caps. This makes the
    # calendar cap preventive even though actual billed tokens arrive afterward.
    worst_case = (MAX_STATE_CHARS + MAX_QUESTION_TOTAL_CHARS) * INPUT_TOKEN_COST_PER_MILLION_USD / 1_000_000
    if _month_cost(now) + worst_case > MONTHLY_COST_CAP_USD:
        raise InputError(f"calendar-month Jev cost cap ${MONTHLY_COST_CAP_USD:.2f} reached")


def _usage_fields(payload: Any) -> tuple[int | None, int | None, float | None]:
    if not isinstance(payload, dict):
        return None, None, None
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None, None, None
    def number(*names: str) -> int | None:
        for name in names:
            value = usage.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return int(value)
        return None
    input_tokens = number("input_tokens", "prompt_tokens")
    output_tokens = number("output_tokens", "completion_tokens")
    estimated_cost = (input_tokens * INPUT_TOKEN_COST_PER_MILLION_USD / 1_000_000
                      if input_tokens is not None else None)
    return input_tokens, output_tokens, estimated_cost


def append_usage(record: dict[str, Any]) -> None:
    """Append only non-sensitive metadata; supplied state and response stay out."""
    allowed = ("ts", "provider", "model", "input_tokens", "output_tokens",
               "latency_ms", "estimated_cost_usd", "status", "state_hash")
    safe = {key: record.get(key) for key in allowed}
    USAGE_LOG.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    payload = (_canonical_json(safe) + "\n").encode("utf-8")
    fd = os.open(USAGE_LOG, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, payload)
    finally:
        os.close(fd)


def _headers() -> dict[str, str]:
    token = os.environ.get("POLYCLAUDE_JEV_API_KEY", "").strip()
    if not token:
        raise InputError("POLYCLAUDE_JEV_API_KEY is not configured")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def command_models(timeout: float) -> int:
    response = httpx.get(f"{API_BASE}/v1/models", headers=_headers(), timeout=timeout)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return 0


def build_payload(state: dict[str, Any], questions: dict[str, dict[str, Any]], model: str) -> dict[str, Any]:
    return {"model": model, "state": state, "questions": questions}


def command_ask(state: dict[str, Any], questions: dict[str, dict[str, Any]], model: str,
                timeout: float) -> int:
    digest = state_hash(state)
    check_repeat_limit(digest)
    check_monthly_cost_cap()
    started = time.monotonic()
    status = "error"
    response_payload: Any = None
    try:
        response = httpx.post(
            f"{API_BASE}/v1/systemone",
            headers=_headers(),
            json=build_payload(state, questions, model),
            timeout=timeout,
        )
        status = f"http_{response.status_code}"
        response.raise_for_status()
        response_payload = response.json()
        status = "ok"
        print(json.dumps(response_payload, indent=2, ensure_ascii=False))
        return 0
    finally:
        input_tokens, output_tokens, estimated_cost = _usage_fields(response_payload)
        append_usage({
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "provider": "jev",
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": round((time.monotonic() - started) * 1000),
            "estimated_cost_usd": estimated_cost,
            "status": status,
            "state_hash": digest,
        })


def main() -> int:
    parser = argparse.ArgumentParser(description="Shadow-only Jev System One client")
    parser.add_argument("--timeout", type=float, default=25.0)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("models", help="list provider models (read-only)")
    ask = sub.add_parser("ask", help="ask bounded questions against typed state")
    ask.add_argument("--state-file", required=True, help="JSON object; never persisted by this tool")
    ask.add_argument("--questions-file", required=True,
                     help="JSON object: ID -> {type, instructions, criteria}")
    ask.add_argument("--model", default=MODEL)
    args = parser.parse_args()
    if not 0 < args.timeout <= MAX_TIMEOUT:
        parser.error(f"--timeout must be >0 and <= {MAX_TIMEOUT}")
    try:
        if args.command == "models":
            return command_models(args.timeout)
        state = load_json_object(args.state_file)
        questions = load_questions(args.questions_file)
        questions = validate_request(questions, state)
        return command_ask(state, questions, args.model, args.timeout)
    except (InputError, httpx.HTTPError) as exc:
        print(_secrets.scrub(f"jev_shadow: {exc}"), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
