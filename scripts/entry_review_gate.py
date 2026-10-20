"""Fail-closed offline gate for new Polymarket BUY orders.

This gate reads the current finite-review checkpoint/index and a root-owned
selection document. It does not rebuild the ledger, use the network, or write
state. Existing orders, sells, cancels, and redemptions are outside its scope.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_REL = Path("notes/entry_review_gate.json")
CHECKPOINT_REL = Path("notes/deep_review_checkpoint.json")
QUEUE_REL = Path("research/2026-10-17-deep-review/index.csv")
RULES_REL = Path("research/2026-10-17-primary-market-review-rules.jsonl.gz")
SCHEMA = "polyclaude.entry_review_gate.v1"
MINIMUM = 600
VALID_STATUSES = {"valued", "blocked_after_review", "excluded_factual", "pending"}
CONDITION_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")


class EntryReviewGateError(RuntimeError):
    """A new BUY is disallowed or its review authorization is invalid."""


def _require_int(value: Any, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise EntryReviewGateError(f"entry review gate: invalid {label}")
    return value


def _load_valuation_counts(root: Path) -> tuple[int, set[str]]:
    checkpoint_path = root / CHECKPOINT_REL
    queue_path = root / QUEUE_REL
    try:
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EntryReviewGateError("entry review gate: checkpoint unavailable or malformed") from exc
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != "polyclaude.deep_review.v1":
        raise EntryReviewGateError("entry review gate: checkpoint schema mismatch")
    if checkpoint.get("queue") != QUEUE_REL.as_posix():
        raise EntryReviewGateError("entry review gate: checkpoint queue path mismatch")
    declared_universe = _require_int(checkpoint.get("universe"), "checkpoint universe", minimum=1)
    declared = {
        "valued": _require_int(checkpoint.get("completed_valuations"), "completed valuations"),
        "blocked_after_review": _require_int(
            checkpoint.get("blocked_after_in_depth_review"), "blocked count"),
        "excluded_factual": _require_int(checkpoint.get("factual_exclusions"), "factual count"),
        "pending": _require_int(checkpoint.get("pending"), "pending count"),
    }

    try:
        with queue_path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or not {"index", "condition_id", "status"}.issubset(reader.fieldnames):
                raise EntryReviewGateError("entry review gate: queue columns are malformed")
            rows = list(reader)
    except OSError as exc:
        raise EntryReviewGateError("entry review gate: canonical queue unavailable") from exc

    counts = {status: 0 for status in VALID_STATUSES}
    condition_ids: set[str] = set()
    valued_condition_ids: set[str] = set()
    indices: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise EntryReviewGateError("entry review gate: malformed queue row")
        condition = str(row.get("condition_id") or "").strip()
        status = str(row.get("status") or "").strip()
        try:
            index = int(str(row.get("index") or ""))
        except ValueError as exc:
            raise EntryReviewGateError("entry review gate: malformed queue index") from exc
        if index <= 0 or index in indices:
            raise EntryReviewGateError("entry review gate: duplicate or invalid queue index")
        if not CONDITION_RE.fullmatch(condition) or condition.lower() in condition_ids:
            raise EntryReviewGateError("entry review gate: duplicate or invalid condition identity")
        if status not in VALID_STATUSES:
            raise EntryReviewGateError("entry review gate: unknown queue status")
        indices.add(index)
        condition_ids.add(condition.lower())
        counts[status] += 1
        if status == "valued":
            valued_condition_ids.add(condition.lower())

    if (len(rows) != declared_universe or len(indices) != declared_universe
            or indices != set(range(1, declared_universe + 1))):
        raise EntryReviewGateError("entry review gate: queue size disagrees with checkpoint universe")
    if counts != declared:
        raise EntryReviewGateError("entry review gate: queue status counts disagree with checkpoint")
    return counts["valued"], valued_condition_ids


def _load_frozen_universe(root: Path) -> dict[str, Any]:
    """Read exact frozen identities using the ledger's immutable rules file."""
    path = root / RULES_REL
    try:
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise EntryReviewGateError("entry review gate: frozen rules unavailable or malformed") from exc
    result: dict[str, Any] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise EntryReviewGateError("entry review gate: malformed frozen rule")
        condition = str(row.get("conditionId") or "").lower()
        if not CONDITION_RE.fullmatch(condition) or condition in result:
            raise EntryReviewGateError("entry review gate: duplicate or invalid frozen condition")
        result[condition] = row
    return result


def _aware_utc(value: Any, label: str) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise EntryReviewGateError(f"entry review gate: invalid {label}")
    try:
        parsed = dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise EntryReviewGateError(f"entry review gate: invalid {label}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise EntryReviewGateError(f"entry review gate: {label} must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _validate_selection(root: Path, selection: Any, valued_count: int,
                         valued_conditions: set[str]) -> set[str]:
    if not isinstance(selection, dict):
        raise EntryReviewGateError("entry review gate: primary selection is required")
    reviewed = _aware_utc(selection.get("reviewed_utc"), "selection review time")
    if reviewed > dt.datetime.now(dt.timezone.utc):
        raise EntryReviewGateError("entry review gate: selection review time is in the future")
    selected_count = _require_int(selection.get("completed_valuations"), "selection valuation count",
                                  minimum=MINIMUM)
    if selected_count > valued_count:
        raise EntryReviewGateError("entry review gate: selection count exceeds current valued count")

    report = selection.get("report")
    if not isinstance(report, str) or not report.strip():
        raise EntryReviewGateError("entry review gate: selection report path is missing")
    report_path = Path(report)
    if report_path.is_absolute() or ".." in report_path.parts:
        raise EntryReviewGateError("entry review gate: report must be a relative research path")
    report_path = (root / report_path).resolve()
    research_root = (root / "research").resolve()
    try:
        report_path.relative_to(research_root)
        report_bytes = report_path.read_bytes()
    except (ValueError, OSError) as exc:
        raise EntryReviewGateError("entry review gate: selection report is outside research or unavailable") from exc
    try:
        if not report_bytes.decode("utf-8").strip():
            raise EntryReviewGateError("entry review gate: comparative report is empty")
    except UnicodeDecodeError as exc:
        raise EntryReviewGateError("entry review gate: comparative report is not UTF-8 text") from exc
    expected_hash = selection.get("report_sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
        raise EntryReviewGateError("entry review gate: invalid report SHA-256")
    if hashlib.sha256(report_bytes).hexdigest() != expected_hash.lower():
        raise EntryReviewGateError("entry review gate: selection report hash mismatch")

    targets = selection.get("targets")
    if not isinstance(targets, list) or not targets:
        raise EntryReviewGateError("entry review gate: selection must contain at least one target")
    frozen_by_condition: dict[str, Any] | None = None
    selected_tokens: set[str] = set()
    selected_conditions: set[str] = set()
    for target in targets:
        if not isinstance(target, dict):
            raise EntryReviewGateError("entry review gate: malformed selected target")
        condition = str(target.get("condition_id") or "").strip().lower()
        token = target.get("token_id")
        if not CONDITION_RE.fullmatch(condition) or condition not in valued_conditions:
            raise EntryReviewGateError("entry review gate: target is not a currently valued condition")
        if not isinstance(token, str) or not token.isdecimal():
            raise EntryReviewGateError("entry review gate: selected token identity is malformed")
        if condition in selected_conditions or token in selected_tokens:
            raise EntryReviewGateError("entry review gate: duplicate selected target")
        if frozen_by_condition is None:
            frozen_by_condition = _load_frozen_universe(root)
        rule = frozen_by_condition.get(condition)
        if not isinstance(rule, dict):
            raise EntryReviewGateError("entry review gate: target missing from frozen universe")
        raw_tokens = rule.get("clobTokenIds")
        try:
            frozen_tokens = json.loads(raw_tokens) if isinstance(raw_tokens, str) else raw_tokens
        except json.JSONDecodeError as exc:
            raise EntryReviewGateError("entry review gate: frozen token mapping is malformed") from exc
        if not isinstance(frozen_tokens, list) or token not in frozen_tokens:
            raise EntryReviewGateError("entry review gate: selected token does not match frozen condition")
        selected_conditions.add(condition)
        selected_tokens.add(token)
    return selected_tokens


def _require_new_buy_allowed(token_id: str | None, root: Path) -> None:
    root = Path(root)
    try:
        policy = json.loads((root / POLICY_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EntryReviewGateError("entry review gate: policy unavailable or malformed") from exc
    if (not isinstance(policy, dict) or policy.get("schema") != SCHEMA
            or type(policy.get("minimum_completed_valuations")) is not int
            or policy.get("minimum_completed_valuations") != MINIMUM):
        raise EntryReviewGateError("entry review gate: policy schema or fixed milestone mismatch")

    valued_count, valued_conditions = _load_valuation_counts(root)
    if valued_count < MINIMUM:
        raise EntryReviewGateError(
            f"entry review gate: {valued_count}/{MINIMUM} completed valuations; new BUYs blocked")
    selected_tokens = _validate_selection(
        root, policy.get("selection"), valued_count, valued_conditions)
    if token_id is not None and str(token_id) not in selected_tokens:
        raise EntryReviewGateError("entry review gate: token is not a primary-selected winner")


def require_new_buy_allowed(token_id: str | None = None, *, root: Path = ROOT) -> None:
    """Allow a new BUY only after the valuation milestone and selected target.

    With ``token_id=None`` this validates the milestone/selection phase without
    authorizing any particular order. All malformed or unavailable inputs fail
    closed through the same RuntimeError subtype.
    """
    try:
        _require_new_buy_allowed(token_id, root)
    except EntryReviewGateError:
        raise
    except Exception as exc:
        raise EntryReviewGateError("entry review gate: invalid or unavailable input") from exc
