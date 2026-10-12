#!/usr/bin/env python3
"""Append-only local case/evidence memory and bounded review-packet CLI.

This module is a shadow data store. It has no network, model, wallet, venue,
execution, Telegram, or financial-record integration.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import sys
from typing import Any

CRITERIA_FIELDS = ("question", "description", "resolutionSource", "rules")
SCHEMA = """
CREATE TABLE IF NOT EXISTS case_version (
  case_key TEXT NOT NULL, version INTEGER NOT NULL, semantic_sha256 TEXT NOT NULL,
  market_id TEXT NOT NULL, condition_id TEXT NOT NULL, tokens_json TEXT NOT NULL,
  labels_json TEXT NOT NULL, slug TEXT, criteria_json TEXT NOT NULL,
  criteria_sha256 TEXT NOT NULL, end_date TEXT, neg_risk INTEGER,
  snapshot_path TEXT NOT NULL, snapshot_sha256 TEXT NOT NULL, row_sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL, PRIMARY KEY(case_key, version));
CREATE TABLE IF NOT EXISTS case_receipt (
  receipt_id TEXT PRIMARY KEY, case_key TEXT NOT NULL, version INTEGER NOT NULL,
  market_id TEXT NOT NULL, slug TEXT, snapshot_path TEXT NOT NULL,
  snapshot_sha256 TEXT NOT NULL, row_sha256 TEXT NOT NULL, received_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS case_state (
  case_key TEXT PRIMARY KEY, current_version INTEGER NOT NULL,
  last_seen_at TEXT NOT NULL, last_seen_run TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS snapshot_run (
  run_id TEXT PRIMARY KEY, path TEXT NOT NULL, snapshot_sha256 TEXT NOT NULL,
  imported_at TEXT NOT NULL, market_count INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS quote_context (
  quote_id TEXT PRIMARY KEY, case_key TEXT NOT NULL, version INTEGER NOT NULL,
  quote_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS quote_receipt (
  receipt_id TEXT PRIMARY KEY, case_key TEXT NOT NULL, version INTEGER NOT NULL,
  quote_id TEXT NOT NULL, snapshot_sha256 TEXT NOT NULL, received_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS source_version (
  source_key TEXT NOT NULL, version_id TEXT NOT NULL, configuration_json TEXT NOT NULL,
  payload_json TEXT NOT NULL, available INTEGER NOT NULL, source_url TEXT,
  content_sha256 TEXT, PRIMARY KEY(source_key, version_id));
CREATE TABLE IF NOT EXISTS source_receipt (
  receipt_id TEXT PRIMARY KEY, source_key TEXT NOT NULL, version_id TEXT NOT NULL,
  observed_at TEXT NOT NULL, valid_until TEXT NOT NULL, received_at TEXT NOT NULL,
  content_sha256 TEXT);
CREATE TABLE IF NOT EXISTS assessment (
  assessment_id TEXT PRIMARY KEY, case_key TEXT NOT NULL, case_version INTEGER NOT NULL,
  policy_version TEXT NOT NULL, created_at TEXT NOT NULL, valid_until TEXT NOT NULL,
  dependencies_json TEXT NOT NULL, memo TEXT NOT NULL, p_yes_json TEXT,
  quote_id TEXT);
CREATE INDEX IF NOT EXISTS assessment_latest ON assessment(case_key, created_at DESC);
"""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _fit_packet(packet: dict, max_bytes: int) -> dict:
    packet["packet_bytes"] = 0
    for _ in range(4):
        size = len(_json(packet).encode("utf-8"))
        if packet["packet_bytes"] == size:
            break
        packet["packet_bytes"] = size
    size = len(_json(packet).encode("utf-8"))
    if size > max_bytes:
        raise ValueError(f"packet requires {size} UTF-8 bytes; budget is {max_bytes}")
    return packet


def _time(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone")
    return parsed.astimezone(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _finite(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be finite")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _list_value(value: Any, name: str) -> list:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{name} must be a JSON list") from exc
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a JSON list")
    return value


def _connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript(SCHEMA)
    return db


@contextmanager
def _db(db_path: str | Path):
    db = _connect(db_path)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def _write_db(db_path: str | Path):
    """Serialize validation plus mutation so concurrent writers cannot race."""
    db = _connect(db_path)
    try:
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db(db_path: str | Path) -> None:
    with _db(db_path):
        pass


def _case_row(row: Any, snapshot_path: str, snapshot_sha: str) -> dict:
    if not isinstance(row, dict):
        raise ValueError("every snapshot row must be an object")
    market_id = str(row.get("id") or "").strip()
    condition_id = str(row.get("condition_id") or "").strip()
    tokens = [str(x).strip() for x in _list_value(row.get("clob_token_ids"), "clob_token_ids")]
    labels = [str(x).strip() for x in _list_value(row.get("outcome_labels"), "outcome_labels")]
    if not market_id or not condition_id:
        raise ValueError("snapshot row requires market id and condition_id")
    if len(tokens) != 2 or not all(tokens) or len(set(tokens)) != 2:
        raise ValueError(f"market {market_id}: requires two distinct ordered token IDs")
    if len(labels) != 2 or not all(labels) or len(set(labels)) != 2:
        raise ValueError(f"market {market_id}: requires two distinct outcome labels")
    criteria = row.get("criteria")
    if not isinstance(criteria, dict) or not criteria:
        raise ValueError(f"market {market_id}: criteria must be a non-empty object")
    if any(k not in CRITERIA_FIELDS for k in criteria):
        raise ValueError(f"market {market_id}: unsupported criteria fields")
    criteria_json = _json(criteria)
    criteria_sha = _sha(criteria_json)
    if row.get("criteria_sha256") != criteria_sha:
        raise ValueError(f"market {market_id}: criteria_sha256 mismatch")
    neg_risk = row.get("neg_risk")
    if neg_risk is not None and not isinstance(neg_risk, bool):
        raise ValueError(f"market {market_id}: neg_risk must be boolean or null")
    end_date = row.get("end_date")
    if end_date is not None:
        end_date = _time(end_date, f"market {market_id} end_date")
    identity = {"condition_id": condition_id, "tokens": tokens}
    case_key = _sha(_json(identity))
    semantic = {
        **identity, "criteria_sha256": criteria_sha, "labels": labels,
        "end_date": end_date, "neg_risk": neg_risk,
    }
    row_json = _json(row)
    quote_fields = ("yes_price", "no_price", "best_bid", "best_ask", "spread",
                    "liquidity", "vol24h", "days_to_resolve")
    quote = {}
    for field in quote_fields:
        raw = row.get(field)
        quote[field] = None if raw is None else _finite(raw, f"market {market_id} {field}")
    quote["event_id"] = row.get("event_id")
    quote_id = _sha(_json({"case_key": case_key, "quote": quote}))
    return {
        "case_key": case_key, "semantic_sha": _sha(_json(semantic)),
        "semantic": semantic, "market_id": market_id, "condition_id": condition_id,
        "tokens": tokens, "labels": labels, "slug": row.get("slug"),
        "criteria": criteria, "criteria_json": criteria_json,
        "criteria_sha": criteria_sha, "end_date": end_date, "neg_risk": neg_risk,
        "snapshot_path": snapshot_path, "snapshot_sha": snapshot_sha,
        "row_sha": _sha(row_json), "quote": quote, "quote_id": quote_id,
    }


def import_snapshot(db_path: str | Path, snapshot_path: str | Path,
                    imported_at: str) -> dict:
    received = _time(imported_at, "imported_at")
    path = Path(snapshot_path)
    raw = path.read_bytes()
    try:
        rows = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("snapshot is not valid JSON") from exc
    if not isinstance(rows, list):
        raise ValueError("snapshot must be a JSON list")
    snap_sha = _sha(raw)
    prepared = [_case_row(row, str(path), snap_sha) for row in rows]
    by_key: dict[str, dict] = {}
    by_market: dict[str, str] = {}
    for item in prepared:
        key = item["case_key"]
        old = by_key.get(key)
        if old and (old["semantic_sha"] != item["semantic_sha"]
                    or old["row_sha"] != item["row_sha"]):
            raise ValueError("snapshot has conflicting duplicate case identity")
        by_key[key] = item
        prior_key = by_market.get(item["market_id"])
        if prior_key and prior_key != key:
            raise ValueError("snapshot maps one market ID to conflicting instrument identities")
        by_market[item["market_id"]] = key
    prepared = list(by_key.values())
    run_id = _sha(_json({"path": str(path), "sha256": snap_sha, "imported_at": received}))
    with _write_db(db_path) as db:
        latest = db.execute("SELECT imported_at FROM snapshot_run ORDER BY imported_at DESC LIMIT 1").fetchone()
        if latest and received <= latest["imported_at"]:
            raise ValueError("snapshot import timestamp must be newer than the prior receipt")
        db.execute("INSERT INTO snapshot_run VALUES(?,?,?,?,?)",
                   (run_id, str(path), snap_sha, received, len(prepared)))
        changed = 0
        for item in prepared:
            state = db.execute("SELECT current_version FROM case_state WHERE case_key=?",
                               (item["case_key"],)).fetchone()
            version = 1
            if state:
                version = state["current_version"]
                current = db.execute("SELECT semantic_sha256 FROM case_version WHERE case_key=? AND version=?",
                                     (item["case_key"], version)).fetchone()
                if current["semantic_sha256"] != item["semantic_sha"]:
                    version += 1
                    changed += 1
            else:
                changed += 1
            db.execute("""INSERT OR IGNORE INTO case_version VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (item["case_key"], version, item["semantic_sha"], item["market_id"],
                        item["condition_id"], _json(item["tokens"]), _json(item["labels"]),
                        item["slug"], item["criteria_json"], item["criteria_sha"],
                        item["end_date"], None if item["neg_risk"] is None else int(item["neg_risk"]),
                        item["snapshot_path"], item["snapshot_sha"], item["row_sha"], received))
            receipt_id = _sha(_json({"case": item["case_key"], "version": version,
                                     "snapshot": snap_sha, "received_at": received}))
            db.execute("INSERT OR IGNORE INTO case_receipt VALUES(?,?,?,?,?,?,?,?,?)",
                       (receipt_id, item["case_key"], version, item["market_id"], item["slug"],
                        str(path), snap_sha, item["row_sha"], received))
            db.execute("INSERT OR IGNORE INTO quote_context VALUES(?,?,?,?)",
                       (item["quote_id"], item["case_key"], version, _json(item["quote"])))
            quote_receipt_id = _sha(_json({"case": item["case_key"], "quote": item["quote_id"],
                                           "snapshot": snap_sha, "received_at": received}))
            db.execute("INSERT OR IGNORE INTO quote_receipt VALUES(?,?,?,?,?,?)",
                       (quote_receipt_id, item["case_key"], version, item["quote_id"], snap_sha, received))
            db.execute("""INSERT INTO case_state VALUES(?,?,?,?)
                       ON CONFLICT(case_key) DO UPDATE SET current_version=excluded.current_version,
                       last_seen_at=excluded.last_seen_at,last_seen_run=excluded.last_seen_run""",
                       (item["case_key"], version, received, run_id))
        unseen = db.execute("SELECT count(*) FROM case_state WHERE last_seen_run<>?", (run_id,)).fetchone()[0]
    return {"run_id": run_id, "snapshot_sha256": snap_sha, "market_count": len(prepared),
            "new_or_changed_cases": changed, "previous_cases_unobserved": unseen}


def observe_source(db_path: str | Path, evidence: dict, received_at: str) -> dict:
    if not isinstance(evidence, dict):
        raise ValueError("evidence must be an object")
    source_key = str(evidence.get("source_key") or "").strip()
    if not source_key:
        raise ValueError("source_key is required")
    observed = _time(evidence.get("observed_at"), "observed_at")
    valid_until = _time(evidence.get("valid_until"), "valid_until")
    received = _time(received_at, "received_at")
    if observed > received:
        raise ValueError("observed_at must not be later than received_at")
    if dt.datetime.fromisoformat(valid_until[:-1] + "+00:00") <= dt.datetime.fromisoformat(observed[:-1] + "+00:00"):
        raise ValueError("valid_until must be later than observed_at")
    available = evidence.get("available")
    if not isinstance(available, bool):
        raise ValueError("available must be boolean")
    config = evidence.get("configuration", {})
    payload = evidence.get("payload")
    content_sha = evidence.get("content_sha")
    if content_sha is not None and (not isinstance(content_sha, str) or len(content_sha) != 64
                                    or any(c not in "0123456789abcdef" for c in content_sha)):
        raise ValueError("content_sha must be lowercase SHA-256 hex")
    config_json, payload_json = _json(config), _json(payload)
    source_url = evidence.get("source_url")
    version = _sha(_json({"source_key": source_key, "configuration": config,
                          "payload": payload, "available": available,
                          "source_url": source_url}))
    receipt = _sha(_json({"source": source_key, "version": version, "received_at": received,
                          "observed_at": observed, "valid_until": valid_until}))
    with _write_db(db_path) as db:
        latest = _latest_source(db, source_key)
        if latest and received <= latest["received_at"]:
            raise ValueError("source receipt timestamp must be newer than the prior receipt")
        if latest and observed < latest["observed_at"]:
            raise ValueError("observed_at must not move backwards for a source")
        previous_version = latest["version_id"] if latest else None
        db.execute("INSERT OR IGNORE INTO source_version VALUES(?,?,?,?,?,?,?)",
                   (source_key, version, config_json, payload_json, int(available), source_url, content_sha))
        db.execute("INSERT INTO source_receipt VALUES(?,?,?,?,?,?,?)",
                   (receipt, source_key, version, observed, valid_until, received, content_sha))
    return {"source_key": source_key, "version_id": version, "available": available,
            "observed_at": observed, "valid_until": valid_until, "received_at": received,
            "identical_value": previous_version == version}


def _latest_source(db: sqlite3.Connection, source_key: str):
    return db.execute("""SELECT sv.*,sr.observed_at,sr.valid_until,sr.received_at,
        sr.content_sha256 AS receipt_content_sha256
        FROM source_receipt sr JOIN source_version sv USING(source_key,version_id)
        WHERE sr.source_key=? ORDER BY sr.received_at DESC LIMIT 1""", (source_key,)).fetchone()


def import_assessment(db_path: str | Path, value: dict) -> dict:
    if not isinstance(value, dict):
        raise ValueError("assessment must be an object")
    case_key = str(value.get("case_key") or "")
    case_version = value.get("case_version")
    if type(case_version) is not int or case_version < 1:
        raise ValueError("case_version must be a positive integer")
    policy = str(value.get("policy_version") or "")
    memo = value.get("memo")
    if not case_key or not policy or not isinstance(memo, str):
        raise ValueError("case_key, policy_version, and string memo are required")
    created = _time(value.get("created_at"), "created_at")
    expires = _time(value.get("valid_until"), "valid_until")
    if expires <= created:
        raise ValueError("assessment valid_until must be after created_at")
    deps = value.get("dependencies", {})
    if not isinstance(deps, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in deps.items()):
        raise ValueError("dependencies must map source keys to version IDs")
    p_yes = value.get("p_yes")
    if p_yes is not None:
        if not isinstance(p_yes, list) or len(p_yes) != 3:
            raise ValueError("p_yes must be [low, central, high] or null")
        p_yes = [_finite(x, "p_yes bound") for x in p_yes]
        if not (0 <= p_yes[0] <= p_yes[1] <= p_yes[2] <= 1):
            raise ValueError("p_yes must satisfy 0 <= low <= central <= high <= 1")
    quote_id = value.get("quote_context_id")
    with _write_db(db_path) as db:
        case = db.execute("SELECT current_version FROM case_state WHERE case_key=?", (case_key,)).fetchone()
        if not case:
            raise ValueError("cannot assess an unknown case")
        if case["current_version"] != case_version:
            raise ValueError("assessment case_version is not current")
        version_row = db.execute("SELECT created_at FROM case_version WHERE case_key=? AND version=?",
                                 (case_key, case_version)).fetchone()
        if not version_row or version_row["created_at"] > created:
            raise ValueError("case version did not exist by assessment created_at")
        for key, version in deps.items():
            known = db.execute("SELECT 1 FROM source_version WHERE source_key=? AND version_id=?",
                               (key, version)).fetchone()
            if not known:
                raise ValueError(f"unknown source dependency version: {key}")
            qualifying_receipt = db.execute("""SELECT 1 FROM source_receipt
                WHERE source_key=? AND version_id=? AND observed_at<=? AND received_at<=? LIMIT 1""",
                                           (key, version, created, created)).fetchone()
            if not qualifying_receipt:
                raise ValueError(f"dependency {key} was not observed and received by assessment created_at")
        if quote_id and not db.execute("SELECT 1 FROM quote_context WHERE quote_id=? AND case_key=?",
                                       (quote_id, case_key)).fetchone():
            raise ValueError("quote_context_id does not belong to this case")
        if quote_id and not db.execute("""SELECT 1 FROM quote_receipt
            WHERE quote_id=? AND case_key=? AND received_at<=? LIMIT 1""",
                                       (quote_id, case_key, created)).fetchone():
            raise ValueError("quote context was not received by assessment created_at")
        body = {"case_key": case_key, "case_version": case_version, "policy_version": policy,
                "created_at": created, "valid_until": expires, "dependencies": deps,
                "memo": memo, "p_yes": p_yes, "quote_context_id": quote_id}
        assessment_id = _sha(_json(body))
        same_time = db.execute("SELECT assessment_id FROM assessment WHERE case_key=? AND created_at=?",
                               (case_key, created)).fetchall()
        if any(row["assessment_id"] != assessment_id for row in same_time):
            raise ValueError("conflicting assessment at same case/created_at")
        db.execute("INSERT OR IGNORE INTO assessment VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (assessment_id, case_key, case_version, policy, created, expires,
                    _json(deps), memo, None if p_yes is None else _json(p_yes), quote_id))
    return {"assessment_id": assessment_id, "case_key": case_key,
            "case_version": case_version, "policy_version": policy}


def _latest_quote(db: sqlite3.Connection, case_key: str):
    return db.execute("""SELECT qc.quote_id,qc.quote_json,qr.received_at
        FROM quote_receipt qr JOIN quote_context qc USING(quote_id,case_key)
        WHERE qr.case_key=? ORDER BY qr.received_at DESC LIMIT 1""", (case_key,)).fetchone()


def _packet_state(db: sqlite3.Connection, case_key: str, now: str, policy: str):
    state = db.execute("SELECT * FROM case_state WHERE case_key=?", (case_key,)).fetchone()
    if not state:
        return {"status": "unknown", "reasons": ["missing_case"], "case": None,
                "assessment": None, "dependencies": [], "quote": None,
                "arithmetic_refresh_required": True, "quote_freshness_verified": False,
                "live_economic_refresh_required": True,
                "criteria_completeness_verified": False, "execution_ready": False}
    case = db.execute("SELECT * FROM case_version WHERE case_key=? AND version=?",
                      (case_key, state["current_version"])).fetchone()
    receipt = db.execute("SELECT * FROM case_receipt WHERE case_key=? ORDER BY received_at DESC LIMIT 1",
                         (case_key,)).fetchone()
    latest_run = db.execute("SELECT run_id,imported_at FROM snapshot_run ORDER BY imported_at DESC LIMIT 1").fetchone()
    latest = db.execute("SELECT * FROM assessment WHERE case_key=? ORDER BY created_at DESC,assessment_id DESC LIMIT 1",
                        (case_key,)).fetchone()
    quote = _latest_quote(db, case_key)
    reasons = []
    deps_out = []
    if not latest:
        status = "unknown"
        reasons.append("no_assessment")
    else:
        if now < latest["created_at"]:
            reasons.append("assessment_not_yet_created")
        if latest["case_version"] != state["current_version"]:
            reasons.append("case_version_changed")
        if latest["policy_version"] != policy:
            reasons.append("policy_version_changed")
        if now >= latest["valid_until"]:
            reasons.append("assessment_expired")
        for key, version in json.loads(latest["dependencies_json"]).items():
            cur = _latest_source(db, key)
            reason = None
            first_for_pinned = db.execute("""SELECT observed_at,received_at FROM source_receipt
                WHERE source_key=? AND version_id=? ORDER BY received_at ASC LIMIT 1""",
                                          (key, version)).fetchone()
            if first_for_pinned and first_for_pinned["received_at"] > latest["created_at"]:
                reasons.append(f"dependency_received_after_assessment:{key}")
            if cur is None:
                reason = "dependency_missing"
            else:
                found = []
                if cur["version_id"] != version:
                    found.append("dependency_version_changed")
                if not cur["available"]:
                    found.append("dependency_unavailable")
                if now >= cur["valid_until"]:
                    found.append("dependency_expired")
                if now < cur["observed_at"]:
                    found.append("dependency_not_yet_observed")
                if now < cur["received_at"]:
                    found.append("dependency_not_yet_received")
                reason = ",".join(found) or None
            deps_out.append({"source_key": key, "pinned_version": version,
                             "current_version": cur["version_id"] if cur else None,
                             "available": bool(cur["available"]) if cur else False,
                             "configuration": json.loads(cur["configuration_json"]) if cur else None,
                             "payload": json.loads(cur["payload_json"]) if cur else None,
                             "source_url": cur["source_url"] if cur else None,
                             "content_sha256": cur["receipt_content_sha256"] if cur else None,
                             "observed_at": cur["observed_at"] if cur else None,
                             "received_at": cur["received_at"] if cur else None,
                             "valid_until": cur["valid_until"] if cur else None,
                             "status": reason or "current"})
            if reason:
                reasons.extend(f"{part}:{key}" for part in reason.split(","))
        if latest_run and now < latest_run["imported_at"]:
            reasons.append("snapshot_not_yet_received")
        status = "fresh" if not reasons else "stale"
    if not latest_run or state["last_seen_run"] != latest_run["run_id"]:
        reasons.append("case_unobserved_in_latest_snapshot")
        if latest:
            status = "stale"
    if not latest and latest_run and now < latest_run["imported_at"]:
        reasons.append("snapshot_not_yet_received")
    assessment = None if not latest else {
        "assessment_id": latest["assessment_id"], "case_version": latest["case_version"],
        "policy_version": latest["policy_version"], "created_at": latest["created_at"],
        "valid_until": latest["valid_until"], "memo": latest["memo"],
        "p_yes": json.loads(latest["p_yes_json"]) if latest["p_yes_json"] else None,
        "dependencies": deps_out,
    }
    return {"status": status, "reasons": reasons,
            "case": {"case_key": case_key, "case_version": case["version"],
                     "market_id": receipt["market_id"], "slug": receipt["slug"],
                     "condition_id": case["condition_id"], "clob_token_ids": json.loads(case["tokens_json"]),
                     "outcome_labels": json.loads(case["labels_json"]), "end_date": case["end_date"],
                     "neg_risk": None if case["neg_risk"] is None else bool(case["neg_risk"]),
                     "criteria": json.loads(case["criteria_json"]),
                     "criteria_sha256": case["criteria_sha256"],
                     "last_seen_at": state["last_seen_at"],
                     "observed_in_latest_snapshot": bool(latest_run and state["last_seen_run"] == latest_run["run_id"]),
                     "snapshot_path": receipt["snapshot_path"],
                     "snapshot_sha256": receipt["snapshot_sha256"],
                     "row_sha256": receipt["row_sha256"]},
            "assessment": assessment,
            "quote": None if not quote else {"quote_context_id": quote["quote_id"],
                                               "captured_at": quote["received_at"],
                                               "values": json.loads(quote["quote_json"])},
            "arithmetic_refresh_required": (not latest) or bool(quote and latest["quote_id"] != quote["quote_id"]),
            "quote_freshness_verified": False,
            "live_economic_refresh_required": True,
            "criteria_completeness_verified": False,
            "execution_ready": False}


def build_packet(db_path: str | Path, case_key: str, now: str, policy_version: str,
                 max_bytes: int = 32768) -> dict:
    now = _time(now, "now")
    if max_bytes < 256:
        raise ValueError("max_bytes must be at least 256")
    with _db(db_path) as db:
        db.execute("BEGIN")
        packet = _packet_state(db, case_key, now, policy_version)
    packet["schema_version"] = 1
    encoded = _json(packet).encode("utf-8")
    if len(encoded) <= max_bytes:
        return _fit_packet(packet, max_bytes)
    case = packet.get("case")
    if case is None:
        compact = {"schema_version": 1, "case_key": case_key, "status": "unknown",
                   "reasons": packet["reasons"], "execution_ready": False}
    else:
        criteria = case.pop("criteria")
        criteria_text = _json(criteria).encode("utf-8")
        packet["needs_full_record"] = {
            "path": case["snapshot_path"], "snapshot_sha256": case["snapshot_sha256"],
            "market_id": case["market_id"], "row_sha256": case["row_sha256"],
            "criteria_sha256": case["criteria_sha256"],
            "criteria_utf8_bytes": len(criteria_text),
        }
        case["criteria"] = None
        packet["criteria_omitted_for_budget"] = True
        packet["packet_bytes"] = len(_json(packet).encode("utf-8"))
        compact = packet
    return _fit_packet(compact, max_bytes)


def build_bundle(db_path: str | Path, case_keys: list[str], now: str,
                 policy_version: str, max_bytes: int = 65536) -> dict:
    """Losslessly share byte-identical rule fields in a bounded case bundle.

    Shared prose establishes textual equality only. Exact instrument identities,
    questions, criteria fingerprints, dependencies, and assessment states remain
    per-case; the caller still owns every literal-rule interpretation.
    """
    now = _time(now, "now")
    if (not case_keys or len(case_keys) > 256 or len(set(case_keys)) != len(case_keys)
            or not all(isinstance(key, str) for key in case_keys)):
        raise ValueError("bundle requires 1..256 distinct case keys")
    shared, packets = {}, []
    with _db(db_path) as db:
        # One read transaction keeps all dependency/assessment views consistent.
        db.execute("BEGIN")
        for key in case_keys:
            packet = _packet_state(db, key, now, policy_version)
            case = packet.get("case")
            if case:
                criteria = case.pop("criteria")
                common = {k: v for k, v in criteria.items() if k != "question"}
                common_sha = _sha(_json(common))
                shared[common_sha] = common
                case["criteria_parts"] = {
                    "individual": {k: v for k, v in criteria.items() if k == "question"},
                    "shared_fields_sha256": common_sha,
                }
            packets.append(packet)
    bundle = {"schema_version": 1, "case_count": len(packets),
              "shared_rule_fields": shared, "cases": packets,
              "family_semantics_proven": False, "execution_ready": False}
    return _fit_packet(bundle, max_bytes)


def expand_bundle(bundle: dict) -> list[dict]:
    """Reconstruct and validate full literal criteria before using a binding."""
    copied = json.loads(_json(bundle))
    shared = copied["shared_rule_fields"]
    for packet in copied["cases"]:
        case = packet.get("case")
        if case:
            parts = case.pop("criteria_parts")
            ref = parts["shared_fields_sha256"]
            common = shared[ref]
            if _sha(_json(common)) != ref:
                raise ValueError("shared rule field hash mismatch")
            individual = parts["individual"]
            if set(individual) - {"question"} or "question" in common:
                raise ValueError("individual and shared rule fields overlap")
            criteria = {**common, **individual}
            if _sha(_json(criteria)) != case["criteria_sha256"]:
                raise ValueError("reconstructed literal criteria hash mismatch")
            case["criteria"] = criteria
    return copied["cases"]


def status(db_path: str | Path) -> dict:
    with _db(db_path) as db:
        counts = {table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                  for table in ("case_version", "case_receipt", "source_version",
                                "source_receipt", "assessment", "quote_context", "quote_receipt")}
        run = db.execute("SELECT * FROM snapshot_run ORDER BY imported_at DESC LIMIT 1").fetchone()
        current = db.execute("SELECT count(*) FROM case_state").fetchone()[0]
        unseen = current if not run else db.execute(
            "SELECT count(*) FROM case_state WHERE last_seen_run<>?", (run["run_id"],)).fetchone()[0]
    return {"counts": counts, "tracked_cases": current,
            "unobserved_in_latest_snapshot": unseen,
            "latest_snapshot": None if not run else dict(run)}


def _read_object(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "status"):
        p = sub.add_parser(name); p.add_argument("--db", required=True)
    p = sub.add_parser("import-snapshot"); p.add_argument("--db", required=True); p.add_argument("--snapshot", required=True); p.add_argument("--imported-at", required=True)
    p = sub.add_parser("observe"); p.add_argument("--db", required=True); p.add_argument("--json", required=True); p.add_argument("--received-at", required=True)
    p = sub.add_parser("import-assessment"); p.add_argument("--db", required=True); p.add_argument("--json", required=True)
    p = sub.add_parser("packet"); p.add_argument("--db", required=True); p.add_argument("--case", required=True); p.add_argument("--now", required=True); p.add_argument("--policy-version", required=True); p.add_argument("--max-bytes", type=int, default=32768)
    p = sub.add_parser("bundle"); p.add_argument("--db", required=True); p.add_argument("--case", required=True, action="append"); p.add_argument("--now", required=True); p.add_argument("--policy-version", required=True); p.add_argument("--max-bytes", type=int, default=65536)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            init_db(args.db); result = {"initialized": True}
        elif args.command == "status":
            result = status(args.db)
        elif args.command == "import-snapshot":
            result = import_snapshot(args.db, args.snapshot, args.imported_at)
        elif args.command == "observe":
            result = observe_source(args.db, _read_object(args.json), args.received_at)
        elif args.command == "import-assessment":
            result = import_assessment(args.db, _read_object(args.json))
        elif args.command == "bundle":
            result = build_bundle(args.db, args.case, args.now, args.policy_version, args.max_bytes)
        else:
            result = build_packet(args.db, args.case, args.now, args.policy_version, args.max_bytes)
        if args.command in {"packet", "bundle"}:
            print(_json(result))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, sqlite3.Error, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
