from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import case_memory as cm

T0 = "2026-10-12T00:00:00.000000Z"
T1 = "2026-10-12T01:00:00.000000Z"
T2 = "2026-10-12T02:00:00.000000Z"
T3 = "2026-10-12T03:00:00.000000Z"
T4 = "2026-10-12T04:00:00.000000Z"


def market(*, tokens=None, description="Resolution text.", price=0.4):
    criteria = {"question": "Will Alpha happen by December 31, 2026?",
                "description": description,
                "resolutionSource": "https://example.invalid/rules",
                "rules": "Rules are literal."}
    criteria_sha = hashlib.sha256(cm._json(criteria).encode()).hexdigest()
    return {
        "id": "market-1", "condition_id": "condition-1",
        "clob_token_ids": tokens or ["yes-token", "no-token"],
        "outcome_labels": ["Yes", "No"], "slug": "alpha-dec-2026",
        "criteria": criteria, "criteria_sha256": criteria_sha,
        "end_date": "2026-12-31T23:59:00Z", "neg_risk": False,
        "yes_price": price, "no_price": 1 - price,
        "best_bid": price - .01, "best_ask": price + .01,
        "spread": .02, "liquidity": 5000, "vol24h": 1200,
        "days_to_resolve": 80,
    }


def snapshot(path, rows):
    path.write_text(json.dumps(rows, ensure_ascii=False))
    return path


def import_market(db, tmp_path, row=None, when=T0):
    path = snapshot(tmp_path / "snapshot-first.json", [row or market()])
    return cm.import_snapshot(db, path, when)


def observe(db, *, key="source-a", payload=None, available=True, received=T1,
            observed=T0, valid=T4, configuration=None):
    evidence = {"source_key": key, "observed_at": observed,
                "valid_until": valid, "payload": {"fact": "old"} if payload is None else payload,
                "configuration": configuration or {"parser": "v1"},
                "available": available, "source_url": "https://example.invalid/source"}
    return cm.observe_source(db, evidence, received)


def assessment(case_key, version=1, *, deps=None, created=T1, valid=T3,
               policy="policy-1", p_yes=None, quote_id=None, memo="Reviewed crux"):
    return {"case_key": case_key, "case_version": version,
            "policy_version": policy, "created_at": created, "valid_until": valid,
            "dependencies": deps or {}, "memo": memo, "p_yes": p_yes,
            "quote_context_id": quote_id}


def packet(db, case_key, *, now=T2, policy="policy-1", max_bytes=32768):
    return cm.build_packet(db, case_key, now, policy, max_bytes=max_bytes)


def test_source_change_invalidates_assessment_after_reopen(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    one = observe(db)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, deps={"source-a": one["version_id"]}))
    initial = packet(db, key)
    assert initial["status"] == "fresh"
    assert initial["execution_ready"] is False
    assert initial["assessment"]["memo"] == "Reviewed crux"

    two = observe(db, payload={"fact": "changed"}, received=T2, observed=T1, valid=T4)
    result = packet(db, key, now=T3)
    assert two["version_id"] != one["version_id"]
    assert result["status"] == "stale"
    assert "dependency_version_changed:source-a" in result["reasons"]


def test_failed_source_version_does_not_fall_back_to_old_value(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    one = observe(db)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, deps={"source-a": one["version_id"]}))
    failed = observe(db, payload=None, available=False, received=T2, observed=T1, valid=T4)
    result = packet(db, key, now=T3)
    assert failed["version_id"] != one["version_id"]
    assert "dependency_unavailable:source-a" in result["reasons"]
    assert "dependency_version_changed:source-a" in result["reasons"]
    assert result["assessment"]["dependencies"][0]["available"] is False


def test_identical_new_receipt_refreshes_source_ttl_not_assessment_expiry(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    one = observe(db, valid=T2)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    original = assessment(key, deps={"source-a": one["version_id"]}, valid=T3)
    cm.import_assessment(db, original)
    refreshed = observe(db, valid=T4, received=T2, observed=T1)
    result = packet(db, key, now=T3, policy="policy-1")
    assert refreshed["version_id"] == one["version_id"]
    assert refreshed["identical_value"] is True
    assert result["status"] == "stale"
    assert "assessment_expired" in result["reasons"]
    assert "dependency_expired:source-a" not in result["reasons"]
    assert result["assessment"]["valid_until"] == T3


def test_expired_source_blocks_unexpired_assessment(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    source = observe(db, valid=T2)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, deps={"source-a": source["version_id"]}, valid=T4))
    result = packet(db, key, now=T2)
    assert result["status"] == "stale"
    assert "dependency_expired:source-a" in result["reasons"]


def test_source_receipts_must_be_chronological(tmp_path):
    db = tmp_path / "cases.db"
    observe(db, received=T2)
    with pytest.raises(ValueError, match="newer"):
        observe(db, received=T1)


def test_source_observation_cannot_be_future_or_move_backwards(tmp_path):
    db = tmp_path / "cases.db"
    with pytest.raises(ValueError, match="later than received_at"):
        observe(db, observed=T2, received=T1)
    observe(db, observed=T1, received=T2)
    with pytest.raises(ValueError, match="move backwards"):
        observe(db, observed=T0, received=T3)


def test_mutation_validation_is_serialized_with_begin_immediate(tmp_path):
    db_path = tmp_path / "cases.db"
    cm.init_db(db_path)
    with cm._write_db(db_path):
        contender = sqlite3.connect(db_path, timeout=0)
        try:
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                contender.execute("BEGIN IMMEDIATE")
        finally:
            contender.close()
    contender = sqlite3.connect(db_path, timeout=0)
    try:
        contender.execute("BEGIN IMMEDIATE")
        contender.rollback()
    finally:
        contender.close()


def test_fractional_receipt_order_is_chronological(tmp_path):
    db = tmp_path / "cases.db"
    one = observe(db, received="2026-10-12T01:00:00.000100Z")
    two = observe(db, received="2026-10-12T01:00:00.000200Z")
    assert one["version_id"] == two["version_id"]
    assert two["received_at"] > one["received_at"]


def test_multiple_dependencies_report_unavailable_source(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    a = observe(db, key="source-a")
    b = observe(db, key="source-b")
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, deps={"source-a": a["version_id"],
                                                    "source-b": b["version_id"]}))
    observe(db, key="source-b", available=False, received=T2, observed=T1, valid=T4)
    result = packet(db, key, now=T3)
    assert "dependency_unavailable:source-b" in result["reasons"]
    assert next(d for d in result["assessment"]["dependencies"]
                if d["source_key"] == "source-a")["status"] == "current"


def test_wrong_side_token_order_is_a_different_case(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    original = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    swapped = cm._case_row(market(tokens=["no-token", "yes-token"]), "unused", "0" * 64)["case_key"]
    assert original != swapped
    assert packet(db, swapped)["status"] == "unknown"
    assert "missing_case" in packet(db, swapped)["reasons"]


def test_case_version_changes_only_for_semantic_fields_and_preserves_history(tmp_path):
    db = tmp_path / "cases.db"
    first = market()
    import_market(db, tmp_path, first, T0)
    key = cm._case_row(first, "unused", "0" * 64)["case_key"]
    quote_id = packet(db, key)["quote"]["quote_context_id"]
    cm.import_assessment(db, assessment(key, quote_id=quote_id))

    # Market price/countdown are quote context; literal criteria/deadline/labels/negRisk define the case.
    second = market(price=.5)
    cm.import_snapshot(db, snapshot(tmp_path / "snapshot-2.json", [second]), T1)
    assert packet(db, key, now=T2)["status"] == "fresh"
    assert packet(db, key, now=T2)["arithmetic_refresh_required"] is True

    third = market(price=.5, description="Changed literal resolution text.")
    cm.import_snapshot(db, snapshot(tmp_path / "snapshot-3.json", [third]), T2)
    result = packet(db, key, now=T3)
    assert result["case"]["case_version"] == 2
    assert result["status"] == "stale"
    assert "case_version_changed" in result["reasons"]
    with sqlite3.connect(db) as conn:
        assert conn.execute("select count(*) from case_version").fetchone()[0] == 2
        assert conn.execute("select count(*) from assessment").fetchone()[0] == 1
        assert conn.execute("select count(*) from quote_receipt").fetchone()[0] == 3


def test_policy_and_assessment_expiry_invalidate(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, valid=T2))
    result = packet(db, key, now=T2, policy="policy-2")
    assert result["status"] == "stale"
    assert "assessment_expired" in result["reasons"]
    assert "policy_version_changed" in result["reasons"]


def test_nan_probability_is_rejected(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    with pytest.raises(ValueError, match="finite"):
        cm.import_assessment(db, assessment(key, p_yes=[.2, float("nan"), .7]))


def test_invalid_probability_order_is_rejected(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    with pytest.raises(ValueError, match="0 <= low"):
        cm.import_assessment(db, assessment(key, p_yes=[.6, .5, .7]))


def test_assessment_requires_exact_current_case_version(tmp_path):
    db = tmp_path / "cases.db"
    first = market()
    import_market(db, tmp_path, first)
    key = cm._case_row(first, "unused", "0" * 64)["case_key"]
    changed = market(description="A different resolution clause")
    cm.import_snapshot(db, snapshot(tmp_path / "next.json", [changed]), T1)
    with pytest.raises(ValueError, match="not current"):
        cm.import_assessment(db, assessment(key, version=1, created=T2, valid=T3))


def test_snapshot_hash_mismatch_is_rejected(tmp_path):
    db = tmp_path / "cases.db"
    row = market()
    row["criteria"]["description"] = "mutated without proof update"
    path = snapshot(tmp_path / "bad.json", [row])
    with pytest.raises(ValueError, match="criteria_sha256 mismatch"):
        cm.import_snapshot(db, path, T0)


def test_conflicting_duplicate_instrument_rows_are_rejected(tmp_path):
    db = tmp_path / "cases.db"
    with pytest.raises(ValueError, match="conflicting duplicate"):
        cm.import_snapshot(db, snapshot(tmp_path / "dup.json", [market(), market(price=.9)]), T0)


def test_absent_cases_remain_unobserved_not_closed(tmp_path):
    db = tmp_path / "cases.db"
    first = market()
    import_market(db, tmp_path, first, T0)
    key = cm._case_row(first, "unused", "0" * 64)["case_key"]
    cm.import_snapshot(db, snapshot(tmp_path / "empty.json", []), T1)
    state = cm.status(db)
    result = packet(db, key, now=T2)
    assert state["tracked_cases"] == 1
    assert state["unobserved_in_latest_snapshot"] == 1
    assert result["case"]["last_seen_at"] == T0
    assert result["case"]["observed_in_latest_snapshot"] is False
    assert "case_unobserved_in_latest_snapshot" in result["reasons"]
    assert "closed" not in result["case"]


def test_absent_case_with_assessment_is_stale(tmp_path):
    db = tmp_path / "cases.db"
    row = market()
    import_market(db, tmp_path, row, T0)
    key = cm._case_row(row, "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, created=T1, valid=T4))
    cm.import_snapshot(db, snapshot(tmp_path / "empty.json", []), T2)
    result = packet(db, key, now=T3)
    assert result["status"] == "stale"
    assert "case_unobserved_in_latest_snapshot" in result["reasons"]


def test_packet_flags_future_assessment_creation(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, created=T3, valid=T4))
    result = packet(db, key, now=T2)
    assert result["status"] == "stale"
    assert "assessment_not_yet_created" in result["reasons"]


def test_packet_flags_future_dependency_observation_and_receipt(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    source = observe(db, observed=T0, received=T1, valid=T4)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, deps={"source-a": source["version_id"]},
                                        created=T1, valid=T4))
    # Simulate an old imported record whose evidence receipt was later corrected/recorded.
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE source_receipt SET observed_at=?,received_at=? WHERE source_key=?",
                     (T2, T3, "source-a"))
    result = packet(db, key, now="2026-10-12T01:30:00Z")
    assert result["status"] == "stale"
    assert "dependency_not_yet_observed:source-a" in result["reasons"]
    assert "dependency_not_yet_received:source-a" in result["reasons"]
    assert "dependency_received_after_assessment:source-a" in result["reasons"]


def test_assessment_rejects_retrospective_dependency_and_future_case_version(tmp_path):
    db = tmp_path / "cases.db"
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    import_market(db, tmp_path, when=T2)
    with pytest.raises(ValueError, match="case version did not exist"):
        cm.import_assessment(db, assessment(key, created=T1, valid=T3))

    source = observe(db, observed=T2, received=T3, valid=T4)
    with pytest.raises(ValueError, match="not observed and received"):
        cm.import_assessment(db, assessment(key, deps={"source-a": source["version_id"]},
                                            created=T2, valid=T4))


def test_packet_flags_snapshot_received_after_packet_time(tmp_path):
    db = tmp_path / "cases.db"
    row = market()
    import_market(db, tmp_path, row, T0)
    key = cm._case_row(row, "unused", "0" *  64)["case_key"]
    cm.import_assessment(db, assessment(key, created=T1, valid=T4))
    cm.import_snapshot(db, snapshot(tmp_path / "future.json", [row]), T2)
    result = packet(db, key, now="2026-10-12T01:30:00Z")
    assert result["status"] == "stale"
    assert "snapshot_not_yet_received" in result["reasons"]


def test_packet_marks_live_terms_and_quote_freshness_unverified(tmp_path):
    db = tmp_path / "cases.db"
    row = market()
    row["event_id"] = "event-42"
    import_market(db, tmp_path, row, T0)
    key = cm._case_row(row, "unused", "0" * 64)["case_key"]
    first = packet(db, key, now=T1)
    cm.import_assessment(db, assessment(key, created=T1, valid=T4,
                                        quote_id=first["quote"]["quote_context_id"]))
    changed_event = dict(row, event_id="event-43")
    cm.import_snapshot(db, snapshot(tmp_path / "event-change.json", [changed_event]), T2)
    result = packet(db, key, now=T3)
    assert result["quote"]["values"]["event_id"] == "event-43"
    assert result["case"]["case_version"] == 1
    assert result["arithmetic_refresh_required"] is True
    assert result["quote_freshness_verified"] is False
    assert result["live_economic_refresh_required"] is True
    assert result["criteria_completeness_verified"] is False


def test_unknown_case_has_explicit_nonexecution_packet(tmp_path):
    db = tmp_path / "cases.db"
    cm.init_db(db)
    result = packet(db, "missing", now=T0)
    assert result["status"] == "unknown"
    assert result["execution_ready"] is False
    assert result["reasons"] == ["missing_case"]


def test_oversize_packet_points_to_exact_full_record_without_truncation(tmp_path):
    db = tmp_path / "cases.db"
    row = market(description="X" * 12000)
    import_market(db, tmp_path, row)
    key = cm._case_row(row, "unused", "0" * 64)["case_key"]
    result = packet(db, key, now=T1, max_bytes=2048)
    assert result["criteria_omitted_for_budget"] is True
    assert result["case"]["criteria"] is None
    assert result["needs_full_record"]["path"].endswith("snapshot-first.json")
    assert result["needs_full_record"]["criteria_sha256"] == row["criteria_sha256"]
    assert result["needs_full_record"]["criteria_utf8_bytes"] > 12000
    assert result["packet_bytes"] <= 2048
    assert len(cm._json(result).encode("utf-8")) == result["packet_bytes"]
    assert result["execution_ready"] is False


def test_snapshot_absence_keeps_last_seen_and_history(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path, when=T0)
    cm.import_snapshot(db, snapshot(tmp_path / "second.json", [market(price=.6)]), T1)
    cm.import_snapshot(db, snapshot(tmp_path / "third.json", []), T2)
    state = cm.status(db)
    assert state["counts"]["case_receipt"] == 2
    assert state["tracked_cases"] == 1
    assert state["unobserved_in_latest_snapshot"] == 1


def test_assessments_are_append_only_versions(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, created=T1, valid=T3, memo="First memo"))
    cm.import_assessment(db, assessment(key, created=T2, valid=T4, memo="Revised memo"))
    result = packet(db, key, now=T3)
    assert result["status"] == "fresh"
    assert result["assessment"]["memo"] == "Revised memo"
    with sqlite3.connect(db) as conn:
        assert conn.execute("select count(*) from assessment").fetchone()[0] == 2


def test_assessment_same_timestamp_is_idempotent_only_for_exact_body(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    original = assessment(key, created=T1, valid=T3, memo="First memo")
    first = cm.import_assessment(db, original)
    second = cm.import_assessment(db, original)
    assert first["assessment_id"] == second["assessment_id"]
    with pytest.raises(ValueError, match="conflicting assessment"):
        cm.import_assessment(db, assessment(key, created=T1, valid=T3, memo="Different memo"))
    with sqlite3.connect(db) as conn:
        assert conn.execute("select count(*) from assessment").fetchone()[0] == 1


def test_cli_init_and_status_emit_json(tmp_path, capsys):
    db = tmp_path / "cli.db"
    assert cm.main(["init", "--db", str(db)]) == 0
    assert json.loads(capsys.readouterr().out) == {"initialized": True}
    assert cm.main(["status", "--db", str(db)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["tracked_cases"] == 0
    assert result["counts"]["case_version"] == 0


def test_bundle_losslessly_shares_only_identical_fields_and_reconstructs_each_case(tmp_path):
    db = tmp_path / "cases.db"
    rows = [market(), market(tokens=["yes-2", "no-2"])]
    rows[1]["id"] = "market-2"
    rows[1]["condition_id"] = "condition-2"
    rows[1]["criteria"]["question"] = "Will Beta happen instead?"
    rows[1]["criteria_sha256"] = cm._sha(cm._json(rows[1]["criteria"]))
    cm.import_snapshot(db, snapshot(tmp_path / "bundle.json", rows), T0)
    keys = [cm._case_row(row, "unused", "0" * 64)["case_key"] for row in rows]
    bundle = cm.build_bundle(db, keys, T1, "policy-1")
    assert len(bundle["shared_rule_fields"]) == 1
    assert bundle["family_semantics_proven"] is False
    assert bundle["execution_ready"] is False
    expanded = cm.expand_bundle(bundle)
    assert [row["case"]["criteria"] for row in expanded] == [row["criteria"] for row in rows]
    assert [row["case"]["clob_token_ids"] for row in expanded] == [row["clob_token_ids"] for row in rows]
    assert len(cm._json(bundle).encode("utf-8")) == bundle["packet_bytes"]
    # A changed common field cannot be hidden behind its old integrity pointer.
    next(iter(bundle["shared_rule_fields"].values()))["description"] = "Altered"
    with pytest.raises(ValueError, match="hash mismatch"):
        cm.expand_bundle(bundle)


def test_bundle_budget_never_truncates_required_clauses(tmp_path):
    db = tmp_path / "cases.db"
    row = market(description="X" * 12000)
    import_market(db, tmp_path, row)
    key = cm._case_row(row, "unused", "0" * 64)["case_key"]
    with pytest.raises(ValueError, match="packet requires"):
        cm.build_bundle(db, [key], T1, "policy-1", max_bytes=2048)


def test_packet_exposes_typed_current_fact_and_exact_parser_configuration(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path)
    source = observe(db, payload={"metric": 12}, configuration={"parser": "exact-field-v1"})
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_assessment(db, assessment(key, deps={"source-a": source["version_id"]}))
    dep = packet(db, key)["assessment"]["dependencies"][0]
    assert dep["payload"] == {"metric": 12}
    assert dep["configuration"] == {"parser": "exact-field-v1"}
    assert dep["source_url"] == "https://example.invalid/source"


def test_assessment_cannot_retroactively_pin_a_later_quote_receipt(tmp_path):
    db = tmp_path / "cases.db"
    import_market(db, tmp_path, when=T0)
    key = cm._case_row(market(), "unused", "0" * 64)["case_key"]
    cm.import_snapshot(db, snapshot(tmp_path / "quote-later.json", [market(price=.6)]), T2)
    quote_id = packet(db, key, now=T2)["quote"]["quote_context_id"]
    with pytest.raises(ValueError, match="quote context was not received"):
        cm.import_assessment(db, assessment(key, created=T1, quote_id=quote_id))
