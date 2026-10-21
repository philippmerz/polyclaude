from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import discover_markets as dm  # noqa: E402
import market_context_batches as mcb  # noqa: E402
import log_storage  # noqa: E402


def _market(market_id: str | None, *, event_id: str | None = None, **updates):
    criteria = {
        "question": f"Will market {market_id} resolve yes?",
        "description": f"Exact public criteria for market {market_id}.",
    }
    row = {
        "id": market_id,
        "condition_id": f"condition-{market_id}",
        "clob_token_ids": [f"yes-{market_id}", f"no-{market_id}"],
        "slug": f"market-{market_id}",
        "question": f"Will market {market_id} resolve yes?",
        "event_id": event_id,
        "event_title": "Shared display title",
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-02T00:00:00Z",
        "criteria": criteria,
        "criteria_sha256": hashlib.sha256(json.dumps(
            criteria, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode()).hexdigest(),
        "end_date": "2026-12-31T00:00:00Z",
        "yes_price": 0.4,
        "no_price": 0.6,
        "outcome_labels": ["Yes", "No"],
        "outcome_prices": [0.4, 0.6],
        "best_bid": 0.39,
        "best_ask": 0.41,
        "spread": 0.02,
        "liquidity": 1000.0,
        "vol24h": 500.0,
        "clears_hurdle": True,
        "fees_enabled": False,
        "fee_rate": None,
        "min_size_usd": 5.0,
        "tick": 0.01,
        "neg_risk": False,
    }
    row.update(updates)
    return row


def test_shortlist_adds_exact_identity_timestamps_and_exact_criteria_proof():
    base = {
        "id": "7",
        "slug": "test-market",
        "question": "Will CAFÉ win?",
        "description": "Resolve   YES\nwhen the source says so.",
        "resolutionSource": "Official source",
        "conditionId": "0xcondition",
        "clobTokenIds": '["yes-token", "no-token"]',
        "events": [{"id": "event-9", "title": "Exact parent"}],
        "createdAt": "2026-09-01T01:02:03Z",
        "updatedAt": "2026-09-02T04:05:06Z",
        "acceptingOrders": True,
        "enableOrderBook": True,
        "closed": False,
        "archived": False,
        "liquidityNum": 10_000,
        "volume24hr": 2_000,
        "spread": 0.02,
        "endDate": "2026-12-31T00:00:00Z",
        "outcomes": '["Yes", "No"]',
        "outcomePrices": '["0.4", "0.6"]',
        "takerBaseFee": None,
    }
    changed_variant = {
        **base,
        "question": "will cafe\u0301 WIN?",
        "description": "resolve yes when the source says so.",
        "resolutionSource": " OFFICIAL\tSOURCE ",
    }
    assert dm.criteria_sha256(base) != dm.criteria_sha256(changed_variant)
    assert dm.criteria_sha256({**base, "description": "Resolve NO."}) != dm.criteria_sha256(base)

    rows = dm.shortlist(
        [base], min_liq=0, min_vol24=0, max_spread=1,
        horizon_days=1_000, top_n=10, hurdle_apy=0,
    )
    assert len(rows) == 1
    assert rows[0]["event_id"] == "event-9"
    assert rows[0]["event_title"] == "Exact parent"
    assert rows[0]["created_at"] == "2026-09-01T01:02:03Z"
    assert rows[0]["updated_at"] == "2026-09-02T04:05:06Z"
    assert len(rows[0]["criteria_sha256"]) == 64
    assert rows[0]["criteria"] == dm.criteria_payload(base)
    assert rows[0]["condition_id"] == "0xcondition"
    assert rows[0]["clob_token_ids"] == '["yes-token", "no-token"]'
    assert rows[0]["outcome_labels"] == ["Yes", "No"]
    assert rows[0]["outcome_prices"] == [0.4, 0.6]


def test_snapshot_sidecar_is_additive_and_latest_stays_legacy_list_symlink(tmp_path):
    rows = [_market("1", event_id="event-1")]
    now = dt.datetime(2026, 9, 23, 12, 34, 56, tzinfo=dt.timezone.utc)
    snap, meta = dm.write_snapshot(
        rows, scan_kind="thin_tail", params={"min_liquidity": 500},
        snapshot_dir=tmp_path, now=now, compressed=False,
    )
    assert json.loads(snap.read_text()) == rows
    assert (tmp_path / "shortlist_latest.json").is_symlink()
    assert (tmp_path / "shortlist_latest.json").resolve() == snap.resolve()
    metadata = json.loads(meta.read_text())
    assert metadata["scan_kind"] == "thin_tail"
    assert metadata["params"] == {"min_liquidity": 500}
    assert metadata["snapshot_sha256"] == hashlib.sha256(snap.read_bytes()).hexdigest()


def test_scan_kind_selection_ignores_interleaved_other_scan(tmp_path):
    first, _ = dm.write_snapshot(
        [_market("1")], scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    dm.write_snapshot(
        [_market("2")], scan_kind="thin_tail", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 2, tzinfo=dt.timezone.utc),
    )
    latest, _ = dm.write_snapshot(
        [_market("3")], scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 3, tzinfo=dt.timezone.utc),
    )
    current, prior, kind, warnings = mcb.select_snapshots(
        snapshot_dir=tmp_path, scan_kind="primary", current=None, prior=None,
    )
    assert (current, prior, kind, warnings) == (
        latest.resolve(), first.resolve(), "primary", [],
    )


def test_same_instant_scan_kinds_have_distinct_snapshot_identities(tmp_path):
    now = dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc)
    primary, _ = dm.write_snapshot(
        [_market("1")], scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=now,
    )
    thin_tail, _ = dm.write_snapshot(
        [_market("2")], scan_kind="thin_tail", params={}, snapshot_dir=tmp_path,
        now=now,
    )
    assert primary != thin_tail
    assert mcb.load_snapshot(primary)[0]["id"] == "1"
    assert mcb.load_snapshot(thin_tail)[0]["id"] == "2"
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        dm.write_snapshot(
            [_market("3")], scan_kind="primary", params={},
            snapshot_dir=tmp_path, now=now,
        )


def test_batches_rank_changes_group_only_exact_event_ids_and_fail_open(tmp_path):
    prior_rows = [
        _market("same", event_id="event-1"),
        _market("changed", event_id="event-1"),
        _market("unchanged", event_id=None),
    ]
    current_rows = [
        _market("same", event_id="event-1"),
        _market("changed", event_id="event-1", criteria_sha256="f" * 64),
        _market("new", event_id="event-1", yes_price=0.8),
        _market("other-event", event_id="event-2"),
        _market("missing-event", event_id=None),
        _market(None, event_id=None, slug="missing-market-id"),
        _market("unchanged", event_id=None),
    ]
    prior, _ = dm.write_snapshot(
        prior_rows, scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    current, _ = dm.write_snapshot(
        current_rows, scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 2, tzinfo=dt.timezone.utc),
    )

    payload = mcb.build_payload(
        current_path=current, prior_path=prior, scan_kind="primary", batch_size=2,
    )
    payload_again = mcb.build_payload(
        current_path=current, prior_path=prior, scan_kind="primary", batch_size=2,
    )
    assert payload == payload_again
    assert payload["counts"]["review_triggers"] == 6

    groups = [group for batch in payload["batches"] for group in batch["groups"]]
    event_one = next(group for group in groups if group["event_id"] == "event-1")
    assert {item["market"]["id"] for item in event_one["markets"]} == {
        "same", "changed", "new",
    }
    assert len(event_one["markets"]) == 3
    assert event_one["group_scope"] == "observed_snapshot_rows_only"
    assert event_one["complete_gamma_event_membership_verified"] is False
    unchanged_sibling = next(
        item for item in event_one["markets"] if item["market"]["id"] == "same"
    )
    assert unchanged_sibling["status"] == "context_unchanged"
    assert unchanged_sibling["trigger"] is False
    assert unchanged_sibling["rank"] is None
    # An identical display title cannot merge a different or absent ID.
    assert next(group for group in groups if group["event_id"] == "event-2")["group_key"] == "event:event-2"
    singleton_groups = [group for group in groups if group["event_id"] is None]
    assert len(singleton_groups) == 3
    assert all(len(group["markets"]) == 1 for group in singleton_groups)
    assert any("no exact Gamma event ID" in warning for warning in payload["warnings"])
    assert any("no market ID" in warning for warning in payload["warnings"])
    assert payload["batches"][0]["market_count"] == 3  # event group stays atomic
    assert len(payload["batches"][0]["group_content_sha256"]) == 64
    assert payload["batches"][0]["groups"][0]["markets"][0]["status"] == "changed"
    incomplete = next(
        item for group in singleton_groups for item in group["markets"]
        if item["market"]["id"] == "unchanged"
    )
    assert incomplete["status"] == "incomplete"
    assert incomplete["changed_fields"] == ["incomplete_context"]
    assert payload["family_routing_ready"] is False

    serialized = json.dumps(payload)
    assert "Context grouping" in payload["grouping_warning"]
    assert "criteria body that must stay private" not in serialized
    markdown = mcb.render_markdown(payload)
    assert "Context-only warning" in markdown
    assert "does not establish proposition equivalence" in markdown


def test_explicit_legacy_snapshot_without_identity_is_still_usable(tmp_path):
    current = tmp_path / "legacy.json"
    current.write_text(json.dumps([{"id": "old", "question": "Legacy row"}]))
    selected, prior, kind, warnings = mcb.select_snapshots(
        snapshot_dir=tmp_path, scan_kind=None, current=current, prior=None,
    )
    assert selected == current.resolve()
    assert prior is None
    assert kind == "unknown"
    assert any("no metadata sidecar" in warning for warning in warnings)
    payload = mcb.build_payload(
        current_path=selected, prior_path=None, scan_kind=kind,
        batch_size=20, warnings=warnings,
    )
    assert payload["counts"]["selected"] == 1
    assert payload["source_integrity_verified"] is False
    assert payload["batches"][0]["groups"][0]["markets"][0]["semantic_triage_ready"] is False
    assert payload["batches"][0]["groups"][0]["group_basis"] == "singleton_missing_family_identity"


def test_continuous_drift_is_ignored_until_quote_move_reaches_threshold():
    prior = _market("1", event_id="event-1")
    cosmetic = _market(
        "1", event_id="event-1", yes_price=0.4299, no_price=0.5701,
        outcome_prices=[0.4299, 0.5701],
        best_bid=0.4199, best_ask=0.4399, liquidity=9_999, vol24h=9_999,
        updated_at="2026-09-23T05:00:00Z", days_to_resolve=98,
    )
    triggers, _ = mcb.rank_changes([cosmetic], [prior], price_change_pp=3.0)
    assert triggers == []

    material = {**cosmetic, "yes_price": 0.43, "outcome_prices": [0.43, 0.5701]}
    triggers, _ = mcb.rank_changes([material], [prior], price_change_pp=3.0)
    assert len(triggers) == 1
    assert triggers[0]["changed_fields"] == ["yes_price", "outcome_prices"]


def test_new_to_snapshot_ranks_ahead_of_quote_only_change():
    prior = [_market("old", event_id="event-old")]
    current = [
        _market(
            "old", event_id="event-old", yes_price=0.44, no_price=0.56,
            outcome_prices=[0.44, 0.56],
        ),
        _market("new", event_id="event-new"),
    ]
    triggers, _ = mcb.rank_changes(current, prior, price_change_pp=3.0)
    assert [item["market"]["id"] for item in triggers] == ["new", "old"]
    assert triggers[0]["status"] == "new_to_snapshot"
    assert triggers[1]["changed_fields"] == ["no_price", "yes_price", "outcome_prices"]


def test_context_completeness_requires_two_tokens_and_matching_literal_criteria():
    complete = mcb._proof_completeness(_market("1", event_id="event-1"))
    assert complete["binary_clob_token_ids"] is True
    assert complete["criteria_text_hash_matches"] is True
    assert complete["semantic_context_complete"] is True
    assert complete["context_complete"] is True

    named_binary = mcb._proof_completeness(_market(
        "1", event_id="event-1", yes_price=None, no_price=None,
        outcome_labels=["Team A", "Team B"], outcome_prices=[0.45, 0.55],
    ))
    assert named_binary["binary_outcome_prices"] is True
    assert named_binary["semantic_context_complete"] is True
    assert named_binary["context_complete"] is True

    one_token = mcb._proof_completeness(_market(
        "1", event_id="event-1", clob_token_ids=["yes-1"],
    ))
    assert one_token["binary_clob_token_ids"] is False
    assert one_token["semantic_context_complete"] is False
    assert one_token["context_complete"] is False

    mismatched = mcb._proof_completeness(_market(
        "1", event_id="event-1", criteria={"question": "Changed after hashing"},
    ))
    assert mismatched["criteria_text_hash_matches"] is False
    assert mismatched["semantic_context_complete"] is False
    assert mismatched["context_complete"] is False

    no_body = _market("1", event_id="event-1", criteria={
        "question": "Will market 1 resolve yes?",
    })
    no_body["criteria_sha256"] = hashlib.sha256(json.dumps(
        no_body["criteria"], sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    assert mcb._proof_completeness(no_body)["literal_criteria_body"] is False

    enabled_without_schedule = _market(
        "1", event_id="event-1", fees_enabled=True, fee_schedule=None,
    )
    assert mcb._proof_completeness(enabled_without_schedule)["fee_terms"] is False
    assert mcb._proof_completeness(enabled_without_schedule)["semantic_context_complete"] is True
    assert mcb._proof_completeness(enabled_without_schedule)["context_complete"] is False


def test_malformed_or_contradictory_snapshot_fields_fail_open():
    whitespace = _market("1", event_id="event-1", criteria={
        "question": "Will market 1 resolve yes?", "description": "   \n",
    })
    whitespace["criteria_sha256"] = hashlib.sha256(json.dumps(
        whitespace["criteria"], sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()
    assert mcb._proof_completeness(whitespace)["literal_criteria_body"] is False

    bad_deadline = mcb._proof_completeness(_market(
        "1", event_id="event-1", end_date="definitely-not-a-date",
    ))
    assert bad_deadline["resolution_deadline"] is False
    assert bad_deadline["semantic_context_complete"] is False

    bool_prices = mcb._proof_completeness(_market(
        "1", event_id="event-1", outcome_prices=[True, False],
    ))
    assert bool_prices["binary_outcome_prices"] is False

    contradictory_prices = mcb._proof_completeness(_market(
        "1", event_id="event-1", yes_price=0.9,
        outcome_prices=[0.4, 0.6],
    ))
    assert contradictory_prices["literal_yes_no_prices_match"] is False

    bad_quote = mcb._proof_completeness(_market(
        "1", event_id="event-1", best_bid="oops",
    ))
    assert bad_quote["snapshot_quotes_valid"] is False
    assert bad_quote["semantic_context_complete"] is False

    contradictory_fee = mcb._proof_completeness(_market(
        "1", event_id="event-1", fees_enabled=True, fee_rate=0.99,
        fee_schedule={"rate": 0.05, "exponent": 1, "takerOnly": True},
    ))
    assert contradictory_fee["fee_terms"] is False

    contradictory_free_fee = mcb._proof_completeness(_market(
        "1", event_id="event-1", fees_enabled=False, fee_rate=0.99,
        fee_schedule=None,
    ))
    assert contradictory_free_fee["fee_terms"] is False

    valid_fee = mcb._proof_completeness(_market(
        "1", event_id="event-1", fees_enabled=True, fee_rate=0.05,
        fee_schedule={"rate": 0.05, "exponent": 1, "takerOnly": True},
    ))
    assert valid_fee["fee_terms"] is True

    prior = _market("1", event_id="event-1", best_bid=0)
    current = _market("1", event_id="event-1", best_bid="oops")
    triggers, _ = mcb.rank_changes([current], [prior])
    assert len(triggers) == 1
    assert "best_bid" in triggers[0]["changed_fields"]
    assert "incomplete_context" in triggers[0]["changed_fields"]


def test_outer_event_membership_accumulates_and_ambiguous_parent_stays_ungrouped():
    market = {"id": "1", "events": None}
    dm._merge_event_refs(market, None, {"id": "event-a", "title": "A"})
    dm._merge_event_refs(
        market, {"events": None}, {"id": "event-b", "title": "B"},
    )
    assert {event["id"] for event in market["events"]} == {"event-a", "event-b"}
    assert dm.parent_event_identity(market) == (None, None)


def test_cohort_mismatch_invalidates_delta_comparison_but_not_current_proof(tmp_path):
    prior, _ = dm.write_snapshot(
        [_market("1", event_id="event-1")], scan_kind="primary",
        params={"top": 80}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    current, _ = dm.write_snapshot(
        [_market("1", event_id="event-1", yes_price=0.5)], scan_kind="primary",
        params={"top": 100}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 2, tzinfo=dt.timezone.utc),
    )
    payload = mcb.build_payload(
        current_path=current, prior_path=prior, scan_kind="primary", batch_size=20,
    )
    assert payload["source_integrity_verified"] is True
    assert payload["prior_integrity_verified"] is True
    assert payload["delta_comparison_verified"] is False
    assert any("cohort parameters" in warning for warning in payload["warnings"])


def test_explicit_scan_kind_mismatch_is_rejected(tmp_path):
    current, _ = dm.write_snapshot(
        [_market("1")], scan_kind="thin_tail", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    with pytest.raises(ValueError, match="differs from requested"):
        mcb.select_snapshots(
            snapshot_dir=tmp_path, scan_kind="primary", current=current, prior=None,
        )


def test_soft_cap_never_splits_an_exact_event_family(tmp_path):
    prior_rows = [
        _market("1", event_id="event-1"),
        _market("2", event_id="event-1"),
        _market("3", event_id="event-1"),
    ]
    current_rows = [
        _market("1", event_id="event-1", yes_price=0.5),
        _market("2", event_id="event-1"),
        _market("3", event_id="event-1"),
    ]
    prior, _ = dm.write_snapshot(
        prior_rows, scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    current, _ = dm.write_snapshot(
        current_rows, scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 2, tzinfo=dt.timezone.utc),
    )
    payload = mcb.build_payload(
        current_path=current, prior_path=prior, scan_kind="primary",
        batch_size=2, max_markets=1,
    )
    assert payload["counts"]["selected"] == 3
    assert payload["counts"]["selected_triggers"] == 1
    assert payload["counts"]["selected_context"] == 2
    assert payload["counts"]["cap_family_expansion"] == 2
    assert payload["batches"][0]["market_count"] == 3


def test_soft_cap_counts_truncated_trigger_families(tmp_path):
    prior_rows = [
        _market("1", event_id="event-1"), _market("2", event_id="event-1"),
        _market("3", event_id="event-2"), _market("4", event_id="event-2"),
    ]
    current_rows = [
        _market("1", event_id="event-1", yes_price=0.5, outcome_prices=[0.5, 0.5]),
        _market("2", event_id="event-1"),
        _market("3", event_id="event-2", yes_price=0.5, outcome_prices=[0.5, 0.5]),
        _market("4", event_id="event-2"),
    ]
    prior, _ = dm.write_snapshot(
        prior_rows, scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    current, _ = dm.write_snapshot(
        current_rows, scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 2, tzinfo=dt.timezone.utc),
    )
    payload = mcb.build_payload(
        current_path=current, prior_path=prior, scan_kind="primary",
        batch_size=20, max_markets=1,
    )
    assert payload["counts"]["review_triggers"] == 2
    assert payload["counts"]["selected"] == 2
    assert payload["counts"]["selected_triggers"] == 1
    assert payload["counts"]["selected_context"] == 1
    assert payload["counts"]["truncated_triggers"] == 1
    assert payload["counts"]["cap_family_expansion"] == 1


def test_sidecar_hash_mismatch_fails_open_with_warning(tmp_path):
    current, _ = dm.write_snapshot(
        [_market("1", event_id="event-1")], scan_kind="primary", params={},
        snapshot_dir=tmp_path, compressed=False,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    current.write_text(json.dumps([_market("2", event_id="event-2")]))
    payload = mcb.build_payload(
        current_path=current, prior_path=None, scan_kind="primary", batch_size=20,
    )
    assert payload["source_integrity_verified"] is False
    assert payload["batches"][0]["groups"][0]["markets"][0]["semantic_triage_ready"] is False
    assert any("does not match its metadata SHA-256" in warning for warning in payload["warnings"])


def test_missing_sidecar_snapshot_name_fails_integrity(tmp_path):
    current, meta_path = dm.write_snapshot(
        [_market("1", event_id="event-1")], scan_kind="primary", params={},
        snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    metadata = json.loads(meta_path.read_text())
    metadata.pop("snapshot")
    meta_path.write_text(json.dumps(metadata))
    payload = mcb.build_payload(
        current_path=current, prior_path=None, scan_kind="primary", batch_size=20,
    )
    assert payload["source_integrity_verified"] is False
    assert any("metadata names None" in warning for warning in payload["warnings"])


def _saved_batches(tmp_path):
    criteria = {"question": "Will CAFÉ win?", "description": "Exact   rules.\nDistinct cutoff: 23:59 UTC."}
    row = _market("1", event_id="event-1", question=criteria["question"], criteria=criteria)
    row["criteria_sha256"] = dm.criteria_sha256(criteria)
    snapshot, _ = dm.write_snapshot(
        [row, _market("2", event_id="event-2"), _market("3", event_id="event-3")],
        scan_kind="primary", params={}, snapshot_dir=tmp_path,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    payload = mcb.build_payload(
        current_path=snapshot, prior_path=None, scan_kind="primary", batch_size=1,
    )
    saved = tmp_path / "batches.json"
    saved.write_text(mcb.render_json(payload, compact=True), encoding="utf-8")
    return saved, payload, snapshot


def test_compact_json_preserves_exact_criteria_counts_and_existing_pretty_format(tmp_path):
    saved, payload, _ = _saved_batches(tmp_path)
    assert json.loads(saved.read_text()) == payload
    assert mcb.render_json(payload) == json.dumps(payload, indent=2, sort_keys=True) + "\n"
    assert len(saved.read_bytes()) < len(mcb.render_json(payload).encode()) * 0.8
    assert "CAFÉ" in saved.read_text()
    loaded, sha = mcb.load_payload_with_sha(saved)
    assert loaded == payload
    assert sha == hashlib.sha256(saved.read_bytes()).hexdigest()
    market = loaded["batches"][0]["groups"][0]["markets"][0]["market"]
    assert market["criteria"]["description"] == "Exact   rules.\nDistinct cutoff: 23:59 UTC."
    assert market["criteria_sha256"] == dm.criteria_sha256(market["criteria"])


def test_saved_batch_cli_resumes_without_source_reads_and_keeps_global_counts(tmp_path, monkeypatch, capsys):
    saved, payload, snapshot = _saved_batches(tmp_path)
    snapshot.unlink()
    mcb.metadata_path(snapshot).unlink()
    monkeypatch.setattr(mcb, "select_snapshots", lambda **kwargs: pytest.fail("source selection on saved input"))
    assert mcb.main(["--input", str(saved), "--batch-index", "2", "--format", "compact-json"]) == 0
    selected = json.loads(capsys.readouterr().out)
    assert selected["batches"] == [payload["batches"][1]]
    assert selected["counts"] == payload["counts"]
    assert selected["warnings"] == payload["warnings"]
    assert selected["execution_policy"] == payload["execution_policy"]
    assert selected["output_selection"]["omitted_batches"] == 2
    assert selected["output_selection"]["global_counts_preserved"] is True
    assert "Counts and upstream coverage refer to the complete saved payload" in mcb.render_markdown(selected)


def test_saved_batch_reference_stores_shared_metadata_once_and_accepts_gzip(tmp_path, capsys):
    saved, payload, _ = _saved_batches(tmp_path)
    packed = saved.with_suffix(".json.gz")
    packed.write_bytes(gzip.compress(saved.read_bytes(), mtime=0))
    assert mcb.main([
        "--input", str(packed), "--batch-index", "1", "--reference-only", "--format", "compact-json",
    ]) == 0
    selected = json.loads(capsys.readouterr().out)
    assert selected["batch"] == payload["batches"][0]
    assert selected["parent_payload"] == {
        "path": str(packed.resolve()), "sha256": hashlib.sha256(saved.read_bytes()).hexdigest(),
        "hash_scope": "decoded_json_bytes",
    }
    assert "source" not in selected
    assert "execution_policy" not in selected
    assert selected["safety"] == "offline_context_only_no_model_no_execution"


def test_compact_batch_cli_writes_deterministic_gzip_with_full_lossless_payload(tmp_path):
    saved, payload, _ = _saved_batches(tmp_path)
    outputs = [tmp_path / name for name in ("first.json.gz", "second.json.gz")]
    for output in outputs:
        assert mcb.main(["--input", str(saved), "--format", "compact-json", "--output", str(output)]) == 0
        assert json.loads(gzip.decompress(output.read_bytes())) == payload
        assert mcb.load_payload_with_sha(output)[0] == payload
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
    assert outputs[0].stat().st_size < saved.stat().st_size


@pytest.mark.parametrize("mutation,match", [
    ("criteria", "content hash"), ("execution", "execution policy"),
    ("counts", "global counts"), ("index", "contiguous"),
])
def test_saved_batch_reuse_rejects_tampered_contents_and_counts(tmp_path, mutation, match):
    saved, payload, _ = _saved_batches(tmp_path)
    item = payload["batches"][0]["groups"][0]["markets"][0]
    if mutation == "criteria":
        item["market"]["criteria"]["description"] = "Different rules"
    elif mutation == "execution":
        item["execution_ready"] = True
    elif mutation == "counts":
        payload["counts"]["selected"] += 1
    else:
        payload["batches"][1]["batch_index"] = 1
    saved.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match=match):
        mcb.load_payload_with_sha(saved)


@pytest.mark.parametrize("extra_args", [
    ["--batch-index", "0"], ["--batch-index", "4"],
    ["--reference-only"], ["--batch-index", "1", "--reference-only", "--format", "markdown"],
    ["--scan-kind", "primary"],
])
def test_saved_batch_cli_rejects_invalid_or_ambiguous_selection(tmp_path, extra_args):
    saved, _, _ = _saved_batches(tmp_path)
    with pytest.raises(SystemExit) as caught:
        mcb.main(["--input", str(saved), *extra_args])
    assert caught.value.code == 2


def test_compressed_default_and_both_latest_aliases_preserve_decoded_source_hash(tmp_path):
    saved, payload, snapshot = _saved_batches(tmp_path)
    raw = gzip.decompress(snapshot.read_bytes())
    assert snapshot.name.endswith(".json.gz")
    assert mcb.load_snapshot(tmp_path / "shortlist_latest.json") == json.loads(raw)
    assert mcb.load_snapshot(tmp_path / "shortlist_latest.json.gz") == json.loads(raw)
    assert payload["source"]["current"]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert payload["source_integrity_verified"] is True
    selected, prior, kind, _ = mcb.select_snapshots(
        snapshot_dir=tmp_path, scan_kind="primary", current=None, prior=None,
    )
    assert (selected, prior, kind) == (snapshot.resolve(), None, "primary")

    # A changed gzip header leaves decoded rules intact but invalidates stored proof.
    packed = bytearray(snapshot.read_bytes())
    packed[4] ^= 1
    snapshot.write_bytes(packed)
    changed = mcb.build_payload(
        current_path=snapshot, prior_path=None, scan_kind="primary", batch_size=1,
    )
    assert changed["source_integrity_verified"] is False
    assert any("gzip snapshot does not match" in warning for warning in changed["warnings"])
    assert all(
        item["semantic_triage_ready"] is False
        for batch in changed["batches"] for group in batch["groups"] for item in group["markets"]
    )


def test_archived_legacy_snapshot_requires_manifest_and_keeps_original_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(log_storage, "ROOT", tmp_path)
    snapshot_dir = tmp_path / "data" / "snapshots"
    original, _ = dm.write_snapshot(
        [_market("1", event_id="event-1")], scan_kind="primary", params={},
        snapshot_dir=snapshot_dir, compressed=False,
        now=dt.datetime(2026, 9, 23, 1, tzinfo=dt.timezone.utc),
    )
    raw = original.read_bytes()
    packed = gzip.compress(raw, mtime=0)
    archive = original.with_suffix(".json.gz")
    archive.write_bytes(packed)
    original.unlink()
    with pytest.raises(ValueError, match="unable to read JSON bytes"):
        mcb.load_snapshot(original)
    with pytest.raises(ValueError, match="unable to read JSON bytes"):
        mcb.select_snapshots(snapshot_dir=snapshot_dir, scan_kind="primary", current=None, prior=None)

    index = tmp_path / log_storage.INDEX
    index.parent.mkdir(parents=True)
    index.write_text(json.dumps({
        "path": original.relative_to(tmp_path).as_posix(),
        "gzip_path": archive.relative_to(tmp_path).as_posix(),
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
        "gzip_sha256": hashlib.sha256(packed).hexdigest(),
    }) + "\n")
    current, _, _, _ = mcb.select_snapshots(
        snapshot_dir=snapshot_dir, scan_kind="primary", current=None, prior=None,
    )
    assert current == original
    payload = mcb.build_payload(
        current_path=current, prior_path=None, scan_kind="primary", batch_size=20,
    )
    assert payload["source"]["current"]["path"] == str(original)
    assert payload["source_integrity_verified"] is True
    assert mcb.load_snapshot(snapshot_dir / "shortlist_latest.json") == json.loads(raw)
    archive.write_bytes(packed + b"tampered")
    with pytest.raises(ValueError, match="compressed hash mismatch"):
        mcb.load_snapshot(original)
