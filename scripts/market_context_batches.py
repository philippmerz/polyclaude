#!/usr/bin/env python3
"""Build deterministic, proof-carrying context batches from market snapshots.

This is an offline read/format tool. It never calls a model, fetches a network
resource, imports an execution client, or submits an order. Event membership is
used only to keep related context together; it is never evidence that two child
markets are equivalent propositions.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SNAPSHOT_DIR = REPO_ROOT / "data" / "snapshots"
SNAPSHOT_RE = re.compile(
    r"^shortlist_(\d{8}T\d{6}(?:\d{6})?Z)(?:_[a-z0-9_]+)?\.json$"
)
CRITERIA_FINGERPRINT = "sha256:canonical-json-exact-v1"
SNAPSHOT_SCHEMA_VERSION = 2
BASE_COHORT_PARAMS = (
    "min_liquidity", "min_vol24", "max_spread", "horizon_days", "top",
    "max_pages", "via_events", "clears_hurdle_only",
)
HURDLE_COHORT_PARAMS = ("hurdle_apy", "hurdle_days_floor")
GROUPING_WARNING = (
    "Context grouping uses exact Gamma event IDs among rows present in this "
    "snapshot. The snapshot may omit event siblings, and shared event membership "
    "does not prove proposition, criteria, outcome, or settlement equivalence."
)

# Continuous timestamp, volume, liquidity and countdown drift are context, not
# triggers. Stable contract changes and material quote moves are triggers.
IDENTITY_FIELDS = {
    "question", "slug", "event_id", "event_title", "end_date",
    "condition_id", "clob_token_ids", "outcome_labels", "neg_risk",
}
EXECUTION_TERM_FIELDS = {
    "fees_enabled", "fee_schedule", "fee_rate", "min_size_usd", "tick",
}
PRICE_FIELDS = {"yes_price", "no_price", "best_bid", "best_ask", "spread"}
PRICE_CHANGE_FIELDS = PRICE_FIELDS | {"outcome_prices"}
COMPACT_FIELDS = (
    "id", "condition_id", "clob_token_ids", "slug", "question", "url",
    "category", "event_id", "event_title",
    "created_at", "updated_at", "criteria", "criteria_sha256", "end_date",
    "yes_price", "no_price", "outcome_labels", "outcome_prices",
    "best_bid", "best_ask", "spread", "liquidity",
    "vol24h", "days_to_resolve", "dominant_side", "apy_dominant",
    "clears_hurdle", "fees_enabled", "fee_schedule", "fee_rate",
    "min_size_usd", "tick", "neg_risk",
)


def metadata_path(snapshot: Path) -> Path:
    return snapshot.with_name(f"{snapshot.stem}.meta.json")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"snapshot file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def load_metadata(snapshot: Path) -> dict[str, Any] | None:
    path = metadata_path(snapshot)
    if not path.exists():
        return None
    value = _read_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"metadata sidecar is not an object: {path}")
    return value


def load_snapshot_with_sha(path: Path) -> tuple[list[dict[str, Any]], str]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except FileNotFoundError as exc:
        raise ValueError(f"snapshot file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"snapshot must be a JSON list of objects: {path}")
    return value, hashlib.sha256(raw).hexdigest()


def load_snapshot(path: Path) -> list[dict[str, Any]]:
    return load_snapshot_with_sha(path)[0]


def snapshot_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _metadata_integrity_warnings(
    snapshot: Path | None, metadata: dict[str, Any] | None, label: str,
    *, actual_sha256: str | None = None, market_count: int | None = None,
) -> list[str]:
    if snapshot is None:
        return []
    if metadata is None:
        return [
            f"{label} snapshot has no metadata sidecar; source integrity is unverified"
        ]
    warnings: list[str] = []
    recorded = str(metadata.get("snapshot_sha256") or "")
    actual = actual_sha256 or snapshot_sha256(snapshot)
    if not re.fullmatch(r"[0-9a-f]{64}", recorded) or recorded != actual:
        warnings.append(
            f"{label} snapshot does not match its metadata SHA-256; "
            "treat every derived packet as incomplete"
        )
    if metadata.get("snapshot") != snapshot.name:
        warnings.append(
            f"{label} metadata names {metadata.get('snapshot')!r}, not {snapshot.name!r}"
        )
    if metadata.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        warnings.append(f"{label} metadata has an unsupported schema version")
    if metadata.get("criteria_fingerprint") != CRITERIA_FINGERPRINT:
        warnings.append(f"{label} metadata has an unsupported criteria fingerprint")
    if market_count is not None and metadata.get("market_count") != market_count:
        warnings.append(f"{label} metadata market_count does not match the snapshot")
    return warnings


def _snapshot_candidates(snapshot_dir: Path, scan_kind: str) -> list[Path]:
    candidates: list[Path] = []
    for path in snapshot_dir.glob("shortlist_*.json"):
        if not SNAPSHOT_RE.match(path.name):
            continue
        metadata = load_metadata(path)
        if metadata and metadata.get("scan_kind") == scan_kind:
            candidates.append(path.resolve())
    return sorted(set(candidates), key=lambda path: path.name)


def select_snapshots(
    *, snapshot_dir: Path, scan_kind: str | None,
    current: Path | None, prior: Path | None,
) -> tuple[Path, Path | None, str, list[str]]:
    """Resolve explicit paths or the latest two sidecars for one scan kind."""
    warnings: list[str] = []
    current_path = current.resolve() if current else None
    prior_path = prior.resolve() if prior else None

    current_meta = load_metadata(current_path) if current_path else None
    effective_kind = scan_kind or (
        str(current_meta.get("scan_kind")) if current_meta and current_meta.get("scan_kind") else None
    )
    if current_path is None:
        if not effective_kind:
            raise ValueError("--scan-kind is required when --current is not supplied")
        candidates = _snapshot_candidates(snapshot_dir, effective_kind)
        if not candidates:
            raise ValueError(f"no snapshots with scan_kind={effective_kind!r} in {snapshot_dir}")
        current_path = candidates[-1]
        if prior_path is None and len(candidates) > 1:
            prior_path = candidates[-2]
    else:
        if not current_path.exists():
            raise ValueError(f"snapshot file not found: {current_path}")
        if current_meta is None:
            warnings.append(f"current snapshot has no metadata sidecar: {current_path}")
        elif scan_kind and current_meta.get("scan_kind") != scan_kind:
            raise ValueError(
                f"explicit current sidecar scan_kind={current_meta.get('scan_kind')!r} "
                f"differs from requested {scan_kind!r}"
            )
        if prior_path is None and effective_kind:
            candidates = [
                path for path in _snapshot_candidates(snapshot_dir, effective_kind)
                if path != current_path and path.name < current_path.name
            ]
            if candidates:
                prior_path = candidates[-1]

    if prior_path is not None and not prior_path.exists():
        raise ValueError(f"snapshot file not found: {prior_path}")
    if prior_path == current_path:
        raise ValueError("current and prior snapshots must differ")
    if prior_path is None:
        warnings.append("no prior snapshot selected; every current market is ranked as new")
    else:
        prior_meta = load_metadata(prior_path)
        if prior_meta is None:
            warnings.append(f"prior snapshot has no metadata sidecar: {prior_path}")
        elif effective_kind and prior_meta.get("scan_kind") != effective_kind:
            raise ValueError(
                f"prior sidecar scan_kind={prior_meta.get('scan_kind')!r} "
                f"differs from current/requested {effective_kind!r}"
            )
    return current_path, prior_path, effective_kind or "unknown", warnings


def _market_id(row: dict[str, Any]) -> str | None:
    value = str(row.get("id") or "").strip()
    return value or None


def _number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def _price_delta(current: dict[str, Any], prior: dict[str, Any] | None) -> float:
    if prior is None:
        return 1.0
    deltas = []
    for field in PRICE_FIELDS:
        if current.get(field) is not None and prior.get(field) is not None:
            deltas.append(abs(_number(current[field]) - _number(prior[field])))
    current_outcomes = _json_list(current.get("outcome_prices"))
    prior_outcomes = _json_list(prior.get("outcome_prices"))
    if current_outcomes is not None and prior_outcomes is not None:
        if len(current_outcomes) == len(prior_outcomes):
            deltas.extend(
                abs(_number(current_value) - _number(prior_value))
                for current_value, prior_value in zip(current_outcomes, prior_outcomes)
            )
    return max(deltas, default=0.0)


def _priority(status: str, changed_fields: list[str]) -> int:
    changed = set(changed_fields)
    if "criteria_sha256" in changed:
        return 0
    if changed & (IDENTITY_FIELDS | EXECUTION_TERM_FIELDS):
        return 1
    if "incomplete_context" in changed:
        return 1
    if status in {"new", "new_to_snapshot"}:
        return 2
    if changed & PRICE_CHANGE_FIELDS:
        return 3
    return 4


def _json_list(value: Any) -> list[Any] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return None
    return value if isinstance(value, list) else None


def _comparison_value(row: dict[str, Any], field: str) -> Any:
    value = row.get(field)
    if field in {"clob_token_ids", "outcome_labels", "outcome_prices"}:
        values = _json_list(value)
        return tuple(str(item) for item in values) if values is not None else value
    return value


def _material_changes(
    current: dict[str, Any], prior: dict[str, Any], price_change: float,
) -> list[str]:
    changed: list[str] = []
    if current.get("criteria_sha256") != prior.get("criteria_sha256"):
        changed.append("criteria_sha256")
    for field in sorted(IDENTITY_FIELDS | EXECUTION_TERM_FIELDS):
        if _comparison_value(current, field) != _comparison_value(prior, field):
            changed.append(field)
    for field in sorted(PRICE_FIELDS):
        current_value, prior_value = current.get(field), prior.get(field)
        if (current_value is None) != (prior_value is None):
            changed.append(field)
        elif current_value is not None:
            current_number = _finite_number_or_none(current_value)
            prior_number = _finite_number_or_none(prior_value)
            if (current_number is None) != (prior_number is None):
                changed.append(field)
            elif current_number is None:
                if current_value != prior_value:
                    changed.append(field)
            else:
                delta = abs(current_number - prior_number)
                if delta > 0 and delta + 1e-12 >= price_change:
                    changed.append(field)
    current_outcomes = _json_list(current.get("outcome_prices"))
    prior_outcomes = _json_list(prior.get("outcome_prices"))
    if (current_outcomes is None) != (prior_outcomes is None):
        changed.append("outcome_prices")
    elif current_outcomes is not None and prior_outcomes is not None:
        if len(current_outcomes) != len(prior_outcomes):
            changed.append("outcome_prices")
        else:
            deltas = [
                abs(_number(current_value) - _number(prior_value))
                for current_value, prior_value in zip(current_outcomes, prior_outcomes)
            ]
            if any(delta > 0 and delta + 1e-12 >= price_change for delta in deltas):
                changed.append("outcome_prices")
    return changed


def _compact_market(row: dict[str, Any]) -> dict[str, Any]:
    compact = {field: row.get(field) for field in COMPACT_FIELDS if field in row}
    tokens = _json_list(compact.get("clob_token_ids"))
    if tokens is not None:
        compact["clob_token_ids"] = [str(token) for token in tokens]
    labels = _json_list(compact.get("outcome_labels"))
    if labels is not None:
        compact["outcome_labels"] = [str(label) for label in labels]
    return compact


def _criteria_hash(criteria: Any) -> str | None:
    if not isinstance(criteria, dict) or not criteria:
        return None
    encoded = json.dumps(
        criteria, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite_number_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _valid_fee_terms(row: dict[str, Any]) -> bool:
    enabled = row.get("fees_enabled")
    schedule = row.get("fee_schedule")
    if enabled is False:
        redundant_rate = row.get("fee_rate")
        redundant_rate_valid = (
            redundant_rate is None
            or _finite_number_or_none(redundant_rate) == 0
        )
        if schedule in (None, {}):
            return redundant_rate_valid
        if not isinstance(schedule, dict):
            return False
        rate = _finite_number_or_none(schedule.get("rate"))
        return rate == 0 and redundant_rate_valid
    if enabled is not True or not isinstance(schedule, dict):
        return False
    rate = _finite_number_or_none(schedule.get("rate"))
    exponent = _finite_number_or_none(schedule.get("exponent"))
    taker_only = schedule.get("takerOnly")
    redundant_rate = _finite_number_or_none(row.get("fee_rate"))
    return (
        rate is not None and rate >= 0
        and exponent is not None and exponent > 0
        and isinstance(taker_only, bool)
        and redundant_rate == rate
    )


def _valid_deadline(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        dt.datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _valid_optional_quote(value: Any) -> bool:
    if value is None:
        return True
    number = _finite_number_or_none(value)
    return number is not None and 0 <= number <= 1


def _proof_completeness(row: dict[str, Any]) -> dict[str, bool]:
    tokens = _json_list(row.get("clob_token_ids"))
    criteria_hash = str(row.get("criteria_sha256") or "")
    criteria = row.get("criteria")
    criteria_text_hash = _criteria_hash(criteria)
    outcome_labels = _json_list(row.get("outcome_labels"))
    outcome_prices = _json_list(row.get("outcome_prices"))
    valid_outcome_prices = (
        outcome_labels is not None and outcome_prices is not None
        and len(outcome_labels) == 2 and len(outcome_prices) == 2
        and len({str(label).strip() for label in outcome_labels}) == 2
        and all(str(label).strip() for label in outcome_labels)
        and all(
            (number := _finite_number_or_none(price)) is not None and 0 <= number <= 1
            for price in outcome_prices
        )
    )
    has_criteria_body = isinstance(criteria, dict) and any(
        (
            bool(criteria.get(field).strip())
            if isinstance(criteria.get(field), str)
            else criteria.get(field) not in (None, "", [], {})
        )
        for field in ("description", "resolutionSource", "rules")
    )
    literal_yes_no_consistent = True
    normalized_labels = (
        [str(label) for label in outcome_labels]
        if outcome_labels is not None else None
    )
    if (
        normalized_labels is not None and outcome_prices is not None
        and len(normalized_labels) == 2 and len(outcome_prices) == 2
        and set(normalized_labels) == {"Yes", "No"}
    ):
        yes_price = _finite_number_or_none(row.get("yes_price"))
        no_price = _finite_number_or_none(row.get("no_price"))
        literal_yes_no_consistent = (
            yes_price == _finite_number_or_none(outcome_prices[normalized_labels.index("Yes")])
            and no_price == _finite_number_or_none(outcome_prices[normalized_labels.index("No")])
        )
    checks = {
        "market_id": _market_id(row) is not None,
        "condition_id": bool(str(row.get("condition_id") or "").strip()),
        "binary_clob_token_ids": (
            tokens is not None
            and len(tokens) == 2
            and len({str(token).strip() for token in tokens}) == 2
            and all(str(token).strip() for token in tokens)
        ),
        "gamma_event_id": bool(str(row.get("event_id") or "").strip()),
        "criteria_sha256": bool(re.fullmatch(r"[0-9a-f]{64}", criteria_hash)),
        "criteria_text_hash_matches": (
            criteria_text_hash is not None and criteria_text_hash == criteria_hash
        ),
        "literal_question_matches": (
            isinstance(criteria, dict)
            and criteria.get("question") == row.get("question")
            and bool(str(row.get("question") or "").strip())
        ),
        "literal_criteria_body": has_criteria_body,
        "resolution_deadline": _valid_deadline(row.get("end_date")),
        "binary_outcome_prices": valid_outcome_prices,
        "literal_yes_no_prices_match": literal_yes_no_consistent,
        "snapshot_quotes_valid": (
            _valid_optional_quote(row.get("best_bid"))
            and _valid_optional_quote(row.get("best_ask"))
            and _valid_optional_quote(row.get("spread"))
        ),
        "fee_terms": _valid_fee_terms(row),
        "order_terms": (
            (_finite_number_or_none(row.get("min_size_usd")) or 0) > 0
            and (_finite_number_or_none(row.get("tick")) or 0) > 0
        ),
        "neg_risk": isinstance(row.get("neg_risk"), bool),
    }
    semantic_fields = (
        "market_id", "condition_id", "binary_clob_token_ids",
        "gamma_event_id", "criteria_sha256", "criteria_text_hash_matches",
        "literal_question_matches", "literal_criteria_body",
        "resolution_deadline", "binary_outcome_prices", "neg_risk",
        "literal_yes_no_prices_match", "snapshot_quotes_valid",
    )
    semantic_complete = all(checks[field] for field in semantic_fields)
    execution_metadata_complete = checks["fee_terms"] and checks["order_terms"]
    return {
        **checks,
        "semantic_context_complete": semantic_complete,
        "execution_metadata_complete": execution_metadata_complete,
        "context_complete": semantic_complete and execution_metadata_complete,
    }


def _prior_proof(prior: dict[str, Any] | None) -> dict[str, Any] | None:
    if prior is None:
        return None
    tokens = _json_list(prior.get("clob_token_ids"))
    return {
        "condition_id": prior.get("condition_id"),
        "clob_token_ids": (
            [str(token) for token in tokens] if tokens is not None
            else prior.get("clob_token_ids")
        ),
        "criteria_sha256": prior.get("criteria_sha256"),
        "updated_at": prior.get("updated_at"),
        "yes_price": prior.get("yes_price"),
        "no_price": prior.get("no_price"),
        "outcome_labels": prior.get("outcome_labels"),
        "outcome_prices": prior.get("outcome_prices"),
        "best_bid": prior.get("best_bid"),
        "best_ask": prior.get("best_ask"),
    }


def _make_item(
    row: dict[str, Any], prior: dict[str, Any] | None, *, row_index: int,
    status: str, changed_fields: list[str], trigger: bool,
    force_singleton: bool,
) -> dict[str, Any]:
    market_id = _market_id(row)
    event_id = str(row.get("event_id") or "").strip() or None
    item = {
        "rank": None,
        "trigger": trigger,
        "status": status,
        "changed_fields": changed_fields,
        "market": _compact_market(row),
        "completeness": _proof_completeness(row),
        "semantic_triage_ready": False,
        "execution_ready": False,
        "live_rewalk_required": True,
        "prior_proof": _prior_proof(prior),
        "_event_id": event_id,
        "_force_singleton": force_singleton,
        "_row_index": row_index,
        "_sort": (
            _priority(status, changed_fields),
            -_price_delta(row, prior),
            -_number(row.get("vol24h")),
            -_number(row.get("liquidity")),
            market_id or "",
            row_index,
        ),
    }
    item["semantic_triage_ready"] = item["completeness"]["semantic_context_complete"]
    return item


def _unique_by_id(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], set[str]]:
    by_id: dict[str, dict[str, Any]] = {}
    duplicates: set[str] = set()
    for row in rows:
        market_id = _market_id(row)
        if market_id is None:
            continue
        if market_id in by_id:
            duplicates.add(market_id)
        else:
            by_id[market_id] = row
    for market_id in duplicates:
        by_id.pop(market_id, None)
    return by_id, duplicates


def rank_changes(
    current_rows: list[dict[str, Any]], prior_rows: list[dict[str, Any]],
    *, price_change_pp: float = 3.0,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Return material new/changed trigger rows in a total deterministic order."""
    warnings: list[str] = []
    prior_by_id, duplicate_prior = _unique_by_id(prior_rows)
    _, duplicate_current = _unique_by_id(current_rows)
    if duplicate_prior:
        warnings.append(
            "duplicate prior market IDs were treated as unmatchable: "
            + ", ".join(sorted(duplicate_prior))
        )

    items: list[dict[str, Any]] = []
    missing_market_rows: list[int] = []
    missing_event_keys: list[str] = []
    price_change = price_change_pp / 100.0
    for row_index, row in enumerate(current_rows):
        market_id = _market_id(row)
        if market_id is None:
            prior = None
            status = "new"
            changed_fields = ["missing_market_id"]
            missing_market_rows.append(row_index)
            force_singleton = True
        elif market_id in duplicate_current:
            prior = None
            status = "new"
            changed_fields = ["duplicate_market_id"]
            force_singleton = True
        else:
            prior = prior_by_id.get(market_id)
            status = "new_to_snapshot" if prior is None else "changed"
            changed_fields = (
                _material_changes(row, prior, price_change)
                if prior is not None else ["new_to_snapshot"]
            )
            force_singleton = False
        if prior is not None and not _proof_completeness(row)["semantic_context_complete"]:
            changed_fields.append("incomplete_context")
            if status == "changed" and len(changed_fields) == 1:
                status = "incomplete"
        if prior is not None and not changed_fields:
            continue

        event_id = str(row.get("event_id") or "").strip() or None
        if event_id is None:
            missing_event_keys.append(market_id or f"row-{row_index}")
        items.append(_make_item(
            row, prior, row_index=row_index, status=status,
            changed_fields=changed_fields, trigger=True,
            force_singleton=force_singleton,
        ))

    if duplicate_current:
        warnings.append(
            "duplicate current market IDs were retained: "
            + ", ".join(sorted(duplicate_current))
        )
    if missing_market_rows:
        sample = ", ".join(map(str, missing_market_rows[:5]))
        suffix = "..." if len(missing_market_rows) > 5 else ""
        warnings.append(
            f"{len(missing_market_rows)} current row(s) have no market ID "
            f"(indices {sample}{suffix}); retained as singletons"
        )
    if missing_event_keys:
        sample = ", ".join(missing_event_keys[:5])
        suffix = "..." if len(missing_event_keys) > 5 else ""
        warnings.append(
            f"{len(missing_event_keys)} changed market(s) have no exact Gamma event ID "
            f"({sample}{suffix}); retained as ungrouped singletons"
        )

    items.sort(key=lambda item: item["_sort"])
    for rank, item in enumerate(items, 1):
        item["rank"] = rank
    return items, list(dict.fromkeys(warnings))


def expand_event_context(
    triggers: list[dict[str, Any]], current_rows: list[dict[str, Any]],
    prior_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Expand a trigger to all current exact-event siblings as context."""
    prior_by_id, _ = _unique_by_id(prior_rows)
    _, duplicate_current = _unique_by_id(current_rows)
    trigger_indices = {item["_row_index"] for item in triggers}
    triggered_events = {
        item["_event_id"] for item in triggers
        if item["_event_id"] is not None and not item["_force_singleton"]
    }
    expanded = list(triggers)
    for row_index, row in enumerate(current_rows):
        if row_index in trigger_indices:
            continue
        event_id = str(row.get("event_id") or "").strip() or None
        if event_id not in triggered_events:
            continue
        market_id = _market_id(row)
        force_singleton = market_id is None or market_id in duplicate_current
        expanded.append(_make_item(
            row, prior_by_id.get(market_id) if market_id and not force_singleton else None,
            row_index=row_index, status="context_unchanged", changed_fields=[],
            trigger=False, force_singleton=force_singleton,
        ))
    return expanded


def group_and_batch(
    items: list[dict[str, Any]], batch_size: int, max_markets: int = 0,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Group only exact event IDs and apply a family-atomic soft output cap."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        event_id = item["_event_id"]
        if event_id is not None and not item["_force_singleton"]:
            key = f"event:{event_id}"
        else:
            market_id = _market_id(item["market"])
            condition_id = str(item["market"].get("condition_id") or "").strip()
            stable_id = market_id or condition_id
            key = (
                f"ungrouped:market:{stable_id}"
                if stable_id and not item["_force_singleton"]
                else f"ungrouped:row:{item['_row_index']}"
            )
        groups.setdefault(key, []).append(item)

    def group_rank(pair: tuple[str, list[dict[str, Any]]]) -> tuple[int, str]:
        ranks = [item["rank"] for item in pair[1] if item["rank"] is not None]
        return (min(ranks) if ranks else sys.maxsize, pair[0])

    ordered_groups = sorted(
        groups.items(), key=group_rank,
    )
    rendered_groups: list[dict[str, Any]] = []
    for key, members in ordered_groups:
        members.sort(key=lambda item: (
            not item["trigger"], item["rank"] if item["rank"] is not None else sys.maxsize,
            _market_id(item["market"]) or "", item["_row_index"],
        ))
        event_id = members[0]["_event_id"]
        titles = {
            str(item["market"].get("event_title") or "").strip()
            for item in members if item["market"].get("event_title")
        }
        rendered = {
            "group_key": key,
            "group_basis": (
                "exact_gamma_event_id" if event_id is not None and not members[0]["_force_singleton"]
                else (
                    "singleton_missing_family_identity"
                    if (_market_id(members[0]["market"]) is not None
                        or members[0]["market"].get("condition_id"))
                    else "singleton_unusable_market_identity"
                )
            ),
            "event_id": event_id,
            "event_title": next(iter(titles)) if len(titles) == 1 else None,
            "group_scope": "observed_snapshot_rows_only",
            "complete_gamma_event_membership_verified": False,
            "context_only": True,
            "oversize_market_batch": len(members) > batch_size,
            "markets": [],
        }
        if len(titles) > 1:
            rendered["warning"] = "same event ID carried conflicting titles in this snapshot"
        for item in members:
            clean = {key: value for key, value in item.items() if not key.startswith("_")}
            rendered["markets"].append(clean)
        rendered_groups.append(rendered)

    selected_groups: list[dict[str, Any]] = []
    selected_count = 0
    for group in rendered_groups:
        if max_markets > 0 and selected_groups and selected_count >= max_markets:
            break
        selected_groups.append(group)
        selected_count += len(group["markets"])

    batches: list[dict[str, Any]] = []
    batch_groups: list[dict[str, Any]] = []
    batch_count = 0
    for group in selected_groups:
        group_count = len(group["markets"])
        if batch_groups and batch_count + group_count > batch_size:
            batches.append({"groups": batch_groups, "market_count": batch_count})
            batch_groups, batch_count = [], 0
        batch_groups.append(group)
        batch_count += group_count
    if batch_groups:
        batches.append({"groups": batch_groups, "market_count": batch_count})
    for index, batch in enumerate(batches, 1):
        batch["batch_index"] = index
        group_content = json.dumps(
            batch["groups"], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        batch["group_content_chars"] = len(group_content.decode("utf-8"))
        batch["group_content_sha256"] = hashlib.sha256(group_content).hexdigest()
        batch["oversize_market_batch"] = batch["market_count"] > batch_size
    selected_items = [item for group in selected_groups for item in group["markets"]]
    selected_triggers = sum(bool(item["trigger"]) for item in selected_items)
    selected_context = len(selected_items) - selected_triggers
    selected_ready = sum(bool(item["semantic_triage_ready"]) for item in selected_items)
    return batches, {
        "selected": len(selected_items),
        "selected_triggers": selected_triggers,
        "selected_context": selected_context,
        "selected_semantic_ready": selected_ready,
        "selected_fail_open": len(selected_items) - selected_ready,
        "cap_family_expansion": max(0, len(selected_items) - max_markets) if max_markets else 0,
    }


def build_payload(
    *, current_path: Path, prior_path: Path | None, scan_kind: str,
    batch_size: int, max_markets: int = 0, price_change_pp: float = 3.0,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    current_rows, current_sha256 = load_snapshot_with_sha(current_path)
    if prior_path:
        prior_rows, prior_sha256 = load_snapshot_with_sha(prior_path)
    else:
        prior_rows, prior_sha256 = [], None
    current_ids = {_market_id(row) for row in current_rows} - {None}
    prior_ids = {_market_id(row) for row in prior_rows} - {None}
    prior_only_ids = sorted(prior_ids - current_ids)
    triggers, rank_warnings = rank_changes(
        current_rows, prior_rows, price_change_pp=price_change_pp,
    )
    items = expand_event_context(triggers, current_rows, prior_rows)
    current_meta = load_metadata(current_path)
    prior_meta = load_metadata(prior_path) if prior_path else None
    all_warnings = list(warnings or []) + rank_warnings
    if prior_only_ids:
        all_warnings.append(
            f"{len(prior_only_ids)} prior market(s) are absent from the current "
            "filtered shortlist; omission is not evidence of closure or resolution"
        )
    current_integrity_warnings = _metadata_integrity_warnings(
        current_path, current_meta, "current", actual_sha256=current_sha256,
        market_count=len(current_rows),
    )
    prior_integrity_warnings = _metadata_integrity_warnings(
        prior_path, prior_meta, "prior", actual_sha256=prior_sha256,
        market_count=len(prior_rows) if prior_path else None,
    )
    if current_meta and current_meta.get("scan_kind") != scan_kind:
        current_integrity_warnings.append(
            f"payload scan_kind={scan_kind!r} does not match current metadata "
            f"{current_meta.get('scan_kind')!r}"
        )
    comparison_warnings: list[str] = []
    if current_meta and prior_meta:
        if current_meta.get("scan_kind") != prior_meta.get("scan_kind"):
            comparison_warnings.append("current and prior snapshots have different scan kinds")
        if current_meta.get("criteria_fingerprint") != prior_meta.get("criteria_fingerprint"):
            comparison_warnings.append(
                "current and prior snapshots use different criteria fingerprint methods"
            )
        current_params = current_meta.get("params")
        prior_params = prior_meta.get("params")
        if not isinstance(current_params, dict) or not isinstance(prior_params, dict):
            comparison_warnings.append("current or prior metadata lacks scanner parameters")
        else:
            required_params = list(BASE_COHORT_PARAMS)
            if (
                current_params.get("clears_hurdle_only") is True
                or prior_params.get("clears_hurdle_only") is True
            ):
                required_params.extend(HURDLE_COHORT_PARAMS)
            missing_params = [
                field for field in required_params
                if field not in current_params or field not in prior_params
            ]
            if missing_params:
                comparison_warnings.append(
                    "current or prior metadata lacks cohort parameters: "
                    + ", ".join(missing_params)
                )
            changed_params = [
                field for field in required_params
                if current_params.get(field) != prior_params.get(field)
            ]
            if changed_params:
                comparison_warnings.append(
                    "current and prior snapshots use different cohort parameters: "
                    + ", ".join(changed_params)
                )
        try:
            current_created = dt.datetime.fromisoformat(
                str(current_meta.get("created_at") or "").replace("Z", "+00:00")
            )
            prior_created = dt.datetime.fromisoformat(
                str(prior_meta.get("created_at") or "").replace("Z", "+00:00")
            )
            if prior_created >= current_created:
                comparison_warnings.append("prior snapshot is not older than current snapshot")
        except (TypeError, ValueError):
            comparison_warnings.append("current or prior metadata has an invalid created_at")
    all_warnings.extend(current_integrity_warnings)
    all_warnings.extend(prior_integrity_warnings)
    all_warnings.extend(comparison_warnings)
    source_integrity_verified = not current_integrity_warnings
    prior_integrity_verified = bool(prior_path) and not prior_integrity_warnings
    delta_comparison_verified = (
        source_integrity_verified and prior_integrity_verified
        and not comparison_warnings
    )
    if not source_integrity_verified:
        for item in items:
            item["semantic_triage_ready"] = False
    batches, selection = group_and_batch(items, batch_size, max_markets)
    return {
        "schema_version": 1,
        "safety": "offline_context_only_no_model_no_execution",
        "execution_policy": (
            "Snapshot quotes are discovery context, not executable evidence. "
            "Re-read literal criteria and rewalk current CLOB books before any action."
        ),
        "source_integrity_verified": source_integrity_verified,
        "prior_integrity_verified": prior_integrity_verified,
        "delta_comparison_verified": delta_comparison_verified,
        "family_routing_ready": False,
        "grouping_warning": GROUPING_WARNING,
        "scan_kind": scan_kind,
        "material_price_change_pp": price_change_pp,
        "ranking_policy": [
            "criteria_change", "identity_or_execution_term_change", "new_to_snapshot",
            f"quote_change_at_least_{price_change_pp:g}pp",
            "largest_price_delta", "vol24h", "liquidity", "market_id",
        ],
        "source": {
            "current": {
                "path": str(current_path),
                "sha256": current_sha256,
                "metadata": current_meta,
            },
            "prior": None if prior_path is None else {
                "path": str(prior_path),
                "sha256": prior_sha256,
                "metadata": prior_meta,
            },
        },
        "counts": {
            "current_markets": len(current_rows),
            "prior_markets": len(prior_rows),
            "prior_only_markets": len(prior_only_ids),
            "review_triggers": len(triggers),
            "expanded_context": len(items) - len(triggers),
            "selected": selection["selected"],
            "selected_triggers": selection["selected_triggers"],
            "selected_context": selection["selected_context"],
            "selected_semantic_ready": selection["selected_semantic_ready"],
            "selected_fail_open": selection["selected_fail_open"],
            "truncated_triggers": len(triggers) - selection["selected_triggers"],
            "cap_family_expansion": selection["cap_family_expansion"],
            "batches": len(batches),
        },
        "warnings": list(dict.fromkeys(all_warnings)),
        "batches": batches,
    }


def _md(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Market context batches",
        "",
        f"> **Context-only warning:** {payload['grouping_warning']}",
        "",
        f"Scan kind: `{_md(payload['scan_kind'])}`  ",
        f"Current proof: `{payload['source']['current']['sha256']}`  ",
        f"Source integrity verified: `{payload['source_integrity_verified']}`  ",
    ]
    prior = payload["source"]["prior"]
    lines.append(f"Prior proof: `{prior['sha256'] if prior else 'none'}`")
    if payload["warnings"]:
        lines.extend(["", "Warnings:"] + [f"- {_md(warning)}" for warning in payload["warnings"]])
    for batch in payload["batches"]:
        lines.extend(["", f"## Batch {batch['batch_index']} ({batch['market_count']} markets)"])
        for group in batch["groups"]:
            title = group.get("event_title") or group["group_key"]
            lines.extend([
                "",
                f"### {_md(title)}",
                f"Group basis: `{group['group_basis']}`; event ID: `{_md(group.get('event_id') or 'missing')}`. "
                "Only observed snapshot rows are included; context grouping does not establish proposition equivalence.",
                "",
                "| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |",
                "|---:|---|---|---|---|---|---|",
            ])
            for item in group["markets"]:
                market = item["market"]
                question = market.get("question") or market.get("slug") or market.get("id") or "missing identity"
                identity = (
                    f"{question} [market={market.get('id') or 'missing'}; "
                    f"condition={market.get('condition_id') or 'missing'}]"
                )
                labels = market.get("outcome_labels") or ["Yes", "No"]
                outcome_prices = market.get("outcome_prices")
                prices = (
                    ", ".join(f"{label}={price}" for label, price in zip(labels, outcome_prices))
                    if isinstance(outcome_prices, list) else
                    f"{market.get('yes_price')}/{market.get('no_price')}"
                )
                lines.append(
                    f"| {_md(item['rank'] if item['rank'] is not None else 'context')} | "
                    f"{_md(item['status'])} | {_md(identity)} | "
                    f"{_md(prices)} | {_md(', '.join(item['changed_fields']))} | "
                    f"{_md(item['completeness']['semantic_context_complete'])} | "
                    f"`{_md(market.get('criteria_sha256') or 'missing')}` |"
                )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--scan-kind", help="Sidecar scan kind (for example primary or thin_tail).")
    parser.add_argument("--current", type=Path, help="Explicit current shortlist JSON path.")
    parser.add_argument("--prior", type=Path, help="Explicit prior shortlist JSON path.")
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--batch-size", type=int, default=20,
                        help="Soft maximum markets per batch; exact event groups stay intact.")
    parser.add_argument("--max-markets", type=int, default=0,
                        help="Soft output cap; exact event families are never split. 0 keeps all.")
    parser.add_argument("--price-change-pp", type=float, default=3.0,
                        help="Minimum absolute quote move that triggers review (default: 3pp).")
    parser.add_argument("--output", type=Path, help="Write output here instead of stdout.")
    args = parser.parse_args(argv)
    if (
        args.batch_size < 1 or args.max_markets < 0
        or not math.isfinite(args.price_change_pp) or args.price_change_pp < 0
    ):
        parser.error("batch size must be positive; caps and price threshold must be nonnegative")
    try:
        current, prior, scan_kind, warnings = select_snapshots(
            snapshot_dir=args.snapshot_dir,
            scan_kind=args.scan_kind,
            current=args.current,
            prior=args.prior,
        )
        payload = build_payload(
            current_path=current, prior_path=prior, scan_kind=scan_kind,
            batch_size=args.batch_size, max_markets=args.max_markets,
            price_change_pp=args.price_change_pp,
            warnings=warnings,
        )
    except ValueError as exc:
        parser.error(str(exc))
    rendered = (
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.format == "json" else render_markdown(payload)
    )
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
