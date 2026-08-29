from __future__ import annotations

import datetime
import json
import math
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import clob_v2  # noqa: E402
import polyclaude_client  # noqa: E402
import polyclaude_enter as entry  # noqa: E402


def _legs() -> list[dict]:
    return [
        {"token": str(index), "condition_id": f"0x{index:064x}", "slug": f"leg-{index}"}
        for index in (1, 2, 3)
    ]


def _positions(size: float = 20.0) -> list[dict]:
    return [
        {
            "asset": leg["token"],
            "conditionId": leg["condition_id"],
            "outcome": "Yes",
            "size": size,
            "initialValue": 3.8,
            "entryFeesUsdc": 0.0,
            "slug": leg["slug"],
        }
        for leg in _legs()
    ]


def _response(*, status: str = "matched", amount: str = "20",
              success: bool = True, txs: list[str] | None = None) -> str:
    return json.dumps({
        "status_code": 200,
        "body": {
            "success": success,
            "status": status,
            "errorMsg": "" if success else "not filled",
            "orderID": "0xorder",
            "transactionsHashes": ["0xtx"] if txs is None else txs,
            "takingAmount": amount,
            "makingAmount": amount,
        },
    })


def test_clob_fill_parser_requires_exact_terminal_evidence():
    assert entry._parse_clob_result(_response(), "BUY", 20)[0]
    assert entry._parse_clob_result(_response(), "SELL", 20)[0]
    assert not entry._parse_clob_result(_response(status="live"), "BUY", 20)[0]
    assert not entry._parse_clob_result(_response(status="delayed"), "BUY", 20)[0]
    assert not entry._parse_clob_result(_response(amount="19.5"), "BUY", 20)[0]
    assert not entry._parse_clob_result(_response(amount="NaN"), "BUY", 20)[0]
    assert not entry._parse_clob_result(_response(), "BUY", math.nan)[0]
    assert not entry._parse_clob_result(_response(txs=[]), "BUY", 20)[0]
    body_error = json.loads(_response())
    body_error["body"]["error"] = "schema-level error"
    assert not entry._parse_clob_result(json.dumps(body_error), "BUY", 20)[0]
    assert entry._classify_clob_result(_response(status="delayed"), "BUY", 20)[0] == "ambiguous"
    assert entry._classify_clob_result("malformed", "BUY", 20)[0] == "ambiguous"


def test_async_trade_ids_are_resolved_to_hash_proof_before_bundle_parse(monkeypatch):
    body = json.loads(_response(txs=[]))["body"]
    body["tradeIDs"] = ["trade-1"]
    monkeypatch.setattr(
        clob_v2, "_get_trades_by_id",
        lambda trade_id, address, creds: [{
            "id": trade_id, "status": "CONFIRMED",
            "transaction_hash": "0xasync-tx",
        }],
    )
    resolved = clob_v2._resolve_transactions_hashes(
        body, "0xwallet", {"api_key": "test"}, timeout=0)
    assert resolved["transactionsHashes"] == ["0xasync-tx"]
    wrapped = json.dumps({"status_code": 200, "body": resolved})
    assert entry._parse_clob_result(wrapped, "BUY", 20)[0]


def test_unresolved_or_failed_async_trade_never_invents_hash_proof(monkeypatch):
    body = json.loads(_response(txs=[]))["body"]
    body["tradeIDs"] = ["trade-1"]
    monkeypatch.setattr(
        clob_v2, "_get_trades_by_id",
        lambda trade_id, address, creds: [{
            "id": trade_id, "status": "FAILED", "transaction_hash": None,
        }],
    )
    unresolved = clob_v2._resolve_transactions_hashes(
        body, "0xwallet", {"api_key": "test"}, timeout=0)
    assert not unresolved.get("transactionsHashes")
    wrapped = json.dumps({"status_code": 200, "body": unresolved})
    assert not entry._parse_clob_result(wrapped, "BUY", 20)[0]


def test_clob_failure_classifier_requires_terminal_exchange_evidence():
    proxy_error = json.dumps({
        "status_code": 503,
        "body": {"errorMsg": "upstream timeout", "status": ""},
    })
    explicit_reject = json.dumps({
        "status_code": 400,
        "body": {"success": False, "errorMsg": "FOK not filled", "status": ""},
    })
    terminal_status = json.dumps({
        "status_code": 200,
        "body": {"errorMsg": "", "status": "unmatched"},
    })
    contradictory_acceptance = json.dumps({
        "status_code": 400,
        "body": {"success": False, "errorMsg": "unknown", "status": "",
                 "orderID": "0xorder", "transactionsHashes": ["0xtx"]},
    })
    racy_false = json.dumps({
        "status_code": 503,
        "body": {"success": False, "errorMsg": "upstream failed", "status": ""},
    })
    async_contradiction = json.dumps({
        "status_code": 400,
        "body": {"success": False, "errorMsg": "unknown", "status": "",
                 "tradeIDs": ["trade-1"]},
    })
    assert entry._classify_clob_result(proxy_error, "BUY", 20)[0] == "ambiguous"
    assert entry._classify_clob_result(explicit_reject, "BUY", 20)[0] == "failed"
    assert entry._classify_clob_result(terminal_status, "BUY", 20)[0] == "failed"
    assert entry._classify_clob_result(
        contradictory_acceptance, "BUY", 20)[0] == "ambiguous"
    assert entry._classify_clob_result(racy_false, "BUY", 20)[0] == "ambiguous"
    assert entry._classify_clob_result(
        async_contradiction, "BUY", 20)[0] == "ambiguous"


def test_fresh_bundle_requires_no_add_flag():
    baselines, cost = entry._validate_existing_bundle(
        _legs(), [], {"1": 0.0, "2": 0.0, "3": 0.0}, False)
    assert baselines == {"1": 0.0, "2": 0.0, "3": 0.0}
    assert cost == 0.0
    with pytest.raises(RuntimeError, match="no existing"):
        entry._validate_existing_bundle(
            _legs(), [], {"1": 0.0, "2": 0.0, "3": 0.0}, True)


def test_existing_bundle_must_be_explicit_equal_and_independently_indexed():
    balances = {"1": 20.0, "2": 20.0, "3": 20.0}
    with pytest.raises(RuntimeError, match="--bundle-add"):
        entry._validate_existing_bundle(_legs(), _positions(), balances, False)
    baselines, cost = entry._validate_existing_bundle(
        _legs(), _positions(), balances, True)
    assert baselines == balances
    assert cost == pytest.approx(11.4)

    with pytest.raises(RuntimeError, match="unequal"):
        entry._validate_existing_bundle(
            _legs(), _positions(), {"1": 20.0, "2": 19.0, "3": 20.0}, True)
    with pytest.raises(RuntimeError, match="not indexed every leg"):
        entry._validate_existing_bundle(_legs(), _positions()[:2], balances, True)


@pytest.mark.parametrize(
    ("field", "value"),
    [("initialValue", math.nan), ("initialValue", -1),
     ("entryFeesUsdc", math.nan), ("entryFeesUsdc", -0.01)],
)
def test_existing_bundle_cost_basis_must_be_finite_nonnegative(field, value):
    positions = _positions()
    positions[0][field] = value
    with pytest.raises(RuntimeError, match=f"{field} is invalid"):
        entry._validate_existing_bundle(
            _legs(), positions, {"1": 20.0, "2": 20.0, "3": 20.0}, True)


def test_existing_bundle_cost_includes_entry_fees():
    positions = _positions()
    positions[0]["entryFeesUsdc"] = 0.25
    _, cost = entry._validate_existing_bundle(
        _legs(), positions, {"1": 20.0, "2": 20.0, "3": 20.0}, True)
    assert cost == pytest.approx(11.65)


def test_cluster_cost_unions_same_event_and_configured_cluster(tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    priors = {
        leg["slug"]: {"cluster": "range"} for leg in _legs()
    }
    priors["unconfigured-bucket"] = {"cluster": "explicit-independent-bucket"}
    priors["other-correlated"] = {"cluster": "range"}
    (notes / "portfolio_kelly_priors.json").write_text(json.dumps(priors))
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    legs = [{**leg, "event_ids": {"event-1"}} for leg in _legs()]
    positions = [
        {"slug": "leg-1", "conditionId": _legs()[0]["condition_id"],
         "eventId": "event-1", "size": 20,
         "initialValue": 3, "entryFeesUsdc": 0.1},
        # Same event counts even under an explicitly independent cluster tag.
        {"slug": "unconfigured-bucket", "conditionId": "0xbucket",
         "eventId": "event-1", "size": 5,
         "initialValue": 2, "entryFeesUsdc": 0.2},
        # Cross-event position counts through the explicit cluster tag.
        {"slug": "other-correlated", "conditionId": "0xother",
         "eventId": "event-2", "size": 4,
         "initialValue": 1, "entryFeesUsdc": 0.3},
    ]
    assert entry._existing_cluster_cost(legs, positions) == pytest.approx(6.6)

    with pytest.raises(RuntimeError, match="lacks condition/slug/event identity"):
        entry._existing_cluster_cost(
            legs, positions + [{"slug": "mystery", "size": 1,
                                "initialValue": 1, "entryFeesUsdc": 0}])


def test_bundle_caps_include_correlated_promises_and_block_leg_promises(
        tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    priors = {leg["slug"]: {"cluster": "range"} for leg in _legs()}
    priors.update({
        "other-correlated": {"cluster": "range"},
        "unrelated": {"cluster": "explicit-independent-unrelated"},
    })
    (notes / "portfolio_kelly_priors.json").write_text(json.dumps(priors))
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    legs = [{**leg, "event_ids": {"event-1"}} for leg in _legs()]
    pending = [
        {"conditionId": "0xother", "slug": "other-correlated",
         "eventIds": ["event-2"], "risk": 4},
        {"conditionId": "0xunrelated", "slug": "unrelated",
         "eventIds": ["event-3"], "risk": 50},
    ]
    assert entry._existing_cluster_cost(legs, [], pending) == pytest.approx(4)
    assert entry._pending_bundle_ticket_cost(legs, pending) == 0

    selected = [{
        "conditionId": legs[0]["condition_id"], "slug": legs[0]["slug"],
        "eventIds": ["event-1"], "risk": 2,
    }]
    assert entry._pending_bundle_ticket_cost(legs, selected) == pytest.approx(2)


def test_single_entry_caps_union_market_event_and_configured_cluster(
        tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "portfolio_kelly_priors.json").write_text(json.dumps({
        "candidate": {"cluster": "shared-factor"},
        "event-sibling": {"cluster": "explicit-independent-sibling"},
        "cross-event": {"cluster": "shared-factor"},
        "unrelated": {"cluster": "explicit-independent-unrelated"},
    }))
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    market = {
        "slug": "candidate", "conditionId": "0xcandidate",
        "question": "Will candidate happen?", "events": [{"id": "event-1"}],
    }
    positions = [
        {"slug": "candidate", "conditionId": "0xcandidate", "eventId": "event-1",
         "title": "Will candidate happen?", "size": 10, "initialValue": 10,
         "entryFeesUsdc": 0},
        # Same event counts toward the cluster without inflating the ticket.
        {"slug": "event-sibling", "conditionId": "0xsibling", "eventId": "event-1",
         "title": "Sibling", "size": 5, "initialValue": 5,
         "entryFeesUsdc": 0},
        # Explicit cross-event cluster membership also counts once.
        {"slug": "cross-event", "conditionId": "0xother", "eventId": "event-2",
         "title": "Other", "size": 7, "initialValue": 7,
         "entryFeesUsdc": 0},
        {"slug": "unrelated", "conditionId": "0xunrelated", "eventId": "event-3",
         "title": "Unrelated", "size": 50, "initialValue": 50,
         "entryFeesUsdc": 0},
    ]

    state = entry._single_entry_cap_state(
        market, positions, bankroll=100, new_risk=6, declared_cluster_frac=0.10)

    assert state["ticket_before"] == pytest.approx(10)
    assert state["ticket_after"] == pytest.approx(16)
    assert state["cluster_before"] == pytest.approx(22)
    assert state["cluster_after"] == pytest.approx(28)
    assert "15% cap" in entry._single_entry_cap_error(state)


def test_single_entry_cluster_cap_counts_full_fill_of_maker_bid(
        tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "portfolio_kelly_priors.json").write_text(json.dumps({
        "candidate": {"cluster": "shared-factor"},
        "other": {"cluster": "shared-factor"},
    }))
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    market = {"slug": "candidate", "conditionId": "0xcandidate",
              "events": [{"id": "event-1"}]}
    positions = [{
        "slug": "other", "conditionId": "0xother", "eventId": "event-2",
        "title": "Other", "size": 25, "initialValue": 25, "entryFeesUsdc": 0,
    }]

    state = entry._single_entry_cap_state(
        market, positions, bankroll=100, new_risk=6, declared_cluster_frac=0)

    assert state["ticket_after"] == pytest.approx(6)
    assert state["cluster_after"] == pytest.approx(31)
    assert "30% cap" in entry._single_entry_cap_error(state)


def test_single_entry_cap_state_fails_closed_on_relevant_bad_cost(
        tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "portfolio_kelly_priors.json").write_text(json.dumps({
        "candidate": {"cluster": "candidate-factor"},
    }))
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    market = {"slug": "candidate", "conditionId": "0xcandidate",
              "events": [{"id": "event-1"}]}
    positions = [{
        "slug": "candidate", "conditionId": "0xcandidate", "eventId": "event-1",
        "size": 5,
        "initialValue": math.nan, "entryFeesUsdc": 0,
    }]
    with pytest.raises(RuntimeError, match="initialValue is invalid"):
        entry._single_entry_cap_state(market, positions, 100, 5)


def test_single_entry_caps_include_open_ticket_event_and_cluster_commitments(
        tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "portfolio_kelly_priors.json").write_text(json.dumps({
        "candidate": {"cluster": "shared-factor"},
        "event-sibling": {"cluster": "explicit-independent-sibling"},
        "cross-event": {"cluster": "shared-factor"},
        "unrelated": {"cluster": "explicit-independent-unrelated"},
    }))
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    market = {
        "slug": "candidate", "conditionId": "0xcandidate",
        "question": "Candidate?", "events": [{"id": "event-1"}],
    }
    pending = [
        {"conditionId": "0xcandidate", "slug": "candidate",
         "question": "Candidate?", "eventIds": ["event-1"], "risk": 4},
        {"conditionId": "0xsibling", "slug": "event-sibling",
         "question": "Sibling?", "eventIds": ["event-1"], "risk": 5},
        {"conditionId": "0xother", "slug": "cross-event",
         "question": "Other?", "eventIds": ["event-2"], "risk": 7},
        {"conditionId": "0xunrelated", "slug": "unrelated",
         "question": "Unrelated?", "eventIds": ["event-3"], "risk": 50},
    ]

    state = entry._single_entry_cap_state(
        market, [], bankroll=100, new_risk=6, pending_buys=pending)

    assert state["ticket_before"] == pytest.approx(4)
    assert state["ticket_after"] == pytest.approx(10)
    assert state["cluster_before"] == pytest.approx(16)
    assert state["cluster_after"] == pytest.approx(22)


def test_single_entry_cap_requires_affirmative_correlation_identity(
        tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "portfolio_kelly_priors.json").write_text("{}")
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    market = {"slug": "candidate", "conditionId": "0xcandidate",
              "events": [{"id": "event-1"}]}
    with pytest.raises(RuntimeError, match="configured correlation cluster"):
        entry._single_entry_cap_state(market, [], 100, 5)

    (notes / "portfolio_kelly_priors.json").write_text(json.dumps({
        "candidate": {"cluster": "explicit-independent-candidate"},
    }))
    malformed = [{
        "slug": "mystery", "conditionId": "0xmystery", "size": 29,
        "initialValue": 29, "entryFeesUsdc": 0,
    }]
    with pytest.raises(RuntimeError, match="lacks condition/slug/event identity"):
        entry._single_entry_cap_state(market, malformed, 100, 6)


def test_wallet_entry_lock_rejects_concurrent_executor(tmp_path, monkeypatch):
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    first = entry._acquire_entry_lock()
    try:
        with pytest.raises(RuntimeError, match="already in progress"):
            entry._acquire_entry_lock()
    finally:
        first.close()
    after_release = entry._acquire_entry_lock()
    after_release.close()


def test_position_fetch_requests_dust_and_paginates(monkeypatch):
    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    first_page = [{"conditionId": f"0x{index:064x}", "row": index}
                  for index in range(500)]
    calls = []

    def fake_get(_url, *, params, timeout):
        calls.append((params, timeout))
        return Response(first_page if params["offset"] == 0 else [first_page[-1]])

    monkeypatch.setattr(
        polyclaude_client.Wallet,
        "load", staticmethod(lambda: SimpleNamespace(address="0xwallet")),
    )
    monkeypatch.setattr(entry.httpx, "get", fake_get)

    rows = entry._fetch_live_positions()

    assert len(rows) == 500  # exact duplicate at the page boundary is removed
    assert [call[0]["offset"] for call in calls] == [0, 500]
    assert all(call[0]["sizeThreshold"] == 0 for call in calls)


def test_entry_reservation_bridges_open_order_and_position_index_lag(
        tmp_path, monkeypatch):
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    record = {
        "conditionId": "0xcandidate", "slug": "candidate",
        "question": "Candidate?", "eventIds": ["event-1"],
        "asset": "token-yes", "shares": 10, "risk": 4.2,
        "baselineBought": 5,
    }
    reservation_id = entry._add_entry_reservation(record)
    entry._update_entry_reservation(
        reservation_id, "0xorder", submission_state="live")

    # Before either endpoint reflects the order, the local full-fill promise is
    # carried into the cap calculation.
    local = entry._entry_reservation_commitments([], [])
    assert len(local) == 1
    assert local[0]["risk"] == pytest.approx(4.2)

    # Authenticated remaining notional never replaces the original promise: a
    # partial fill can precede data-api indexing.
    authenticated = [{
        "orderId": "0xorder", "conditionId": "0xcandidate",
        "asset": "token-yes", "originalShares": 10, "matchedShares": 8,
        "remainingShares": 2, "price": 0.42,
        "slug": "candidate", "question": "Candidate?",
        "eventIds": ["event-1"], "risk": 0.84,
    }]
    merged = entry._merge_entry_commitments([], authenticated)
    assert len(merged) == 1
    assert merged[0]["risk"] == pytest.approx(4.2)

    # Current size can fall after sells; cumulative totalBought is the durable
    # proof that all reserved shares reached the indexed position.
    indexed = [{
        "conditionId": "0xcandidate", "slug": "candidate",
        "eventId": "event-1", "asset": "token-yes", "size": 3,
        "totalBought": 15,
    }]
    assert entry._entry_reservation_commitments(
        indexed, [], prune=True) == []
    assert not entry._entry_reservations_path().exists()


def test_unreserved_or_mismapped_open_buy_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    open_buy = {
        "orderId": "0xmanual", "conditionId": "0xcandidate",
        "asset": "token-yes", "originalShares": 10, "matchedShares": 2,
        "remainingShares": 8, "price": 0.4, "risk": 3.2,
        "slug": "candidate", "question": "Candidate?", "eventIds": ["event-1"],
    }
    with pytest.raises(RuntimeError, match="lacks a local full-fill reservation"):
        entry._merge_entry_commitments([], [open_buy])

    record = {
        "conditionId": "0xcandidate", "slug": "candidate",
        "question": "Candidate?", "eventIds": ["event-1"],
        "asset": "token-yes", "shares": 10, "risk": 4,
        "baselineBought": 0,
    }
    reservation_id = entry._add_entry_reservation(record)
    entry._update_entry_reservation(
        reservation_id, "0xdifferent", submission_state="live")
    with pytest.raises(RuntimeError, match="order ID is unmapped"):
        entry._merge_entry_commitments([], [open_buy])


def test_unknown_open_order_side_fails_closed(monkeypatch):
    monkeypatch.setattr(clob_v2, "list_open_orders", lambda: {
        "status_code": 200,
        "body": {
            "next_cursor": "LTE=",
            "data": [{"id": "0xorder", "side": "", "original_size": "10"}],
        },
    })
    with pytest.raises(RuntimeError, match="unknown side"):
        entry._fetch_open_buy_commitments()


def test_reservation_batch_is_atomic_and_rejects_same_asset(
        tmp_path, monkeypatch):
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    base = {
        "conditionId": "0xcandidate", "slug": "candidate",
        "question": "Candidate?", "eventIds": ["event-1"],
        "asset": "token-yes", "shares": 10, "risk": 4,
        "baselineBought": 0,
    }
    with pytest.raises(RuntimeError, match="already exists"):
        entry._add_entry_reservations([base, dict(base)])
    assert not entry._entry_reservations_path().exists()

    entry._add_entry_reservation(base)
    with pytest.raises(RuntimeError, match="already exists"):
        entry._add_entry_reservation(base)


def test_verified_cancel_retires_only_confirmed_indexed_matches(
        tmp_path, monkeypatch):
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    record = {
        "conditionId": "0xcandidate", "slug": "candidate",
        "question": "Candidate?", "eventIds": ["event-1"],
        "asset": "token-yes", "shares": 10, "risk": 4,
        "baselineBought": 5,
    }
    reservation_id = entry._add_entry_reservation(record)
    entry._update_entry_reservation(
        reservation_id, "0xorder", submission_state="cancelled")
    rows = entry._read_entry_reservations()
    rows[0]["cancelVerifiedAt"] = (
        datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(minutes=10)).isoformat()
    entry._write_entry_reservations(rows)
    monkeypatch.setattr(
        entry, "_fetch_order_match_totals", lambda records: {"0xorder": 2})
    monkeypatch.setattr(
        entry, "_fetch_terminal_cancelled_totals",
        lambda records: {"0xorder": 2})

    # A sell has reduced size to zero, but totalBought proves both fills indexed.
    indexed = [{
        "conditionId": "0xcandidate", "asset": "token-yes",
        "slug": "candidate", "size": 0, "totalBought": 7,
    }]
    assert entry._entry_reservation_commitments(indexed, [], prune=True) == []
    assert not entry._entry_reservations_path().exists()


def test_missing_live_order_without_verified_cancel_stays_reserved(
        tmp_path, monkeypatch):
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    record = {
        "conditionId": "0xcandidate", "slug": "candidate",
        "question": "Candidate?", "eventIds": ["event-1"],
        "asset": "token-yes", "shares": 10, "risk": 4,
        "baselineBought": 0,
    }
    reservation_id = entry._add_entry_reservation(record)
    entry._update_entry_reservation(
        reservation_id, "0xorder", submission_state="live")
    monkeypatch.setattr(
        entry, "_fetch_order_match_totals",
        lambda _records: pytest.fail("absence alone must not query/retire"),
    )
    assert len(entry._entry_reservation_commitments([], [], prune=True)) == 1


def test_cancel_reappearance_persists_fail_closed_block(tmp_path, monkeypatch):
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    record = {
        "conditionId": "0xcandidate", "slug": "candidate",
        "question": "Candidate?", "eventIds": ["event-1"],
        "asset": "token-yes", "shares": 10, "risk": 4,
        "baselineBought": 0, "submissionState": "cancelled",
        "orderId": "0xorder",
        "cancelVerifiedAt": (datetime.datetime.now(datetime.timezone.utc)
                             - datetime.timedelta(minutes=10)).isoformat(),
    }
    entry._add_entry_reservation(record)
    open_buy = {
        "orderId": "0xorder", "conditionId": "0xcandidate",
        "asset": "token-yes", "originalShares": 10, "matchedShares": 0,
        "remainingShares": 10, "price": 0.4, "risk": 4,
        "slug": "candidate", "question": "Candidate?", "eventIds": ["event-1"],
    }
    with pytest.raises(RuntimeError, match="persistent reconciliation block"):
        entry._merge_entry_commitments([], [open_buy], prune=False)
    blocker = json.loads(entry._entry_reconciliation_path().read_text())
    assert blocker[0]["orderId"] == "0xorder"
    # Even if the order disappears again, the stale cancel timestamp cannot
    # retire anything until the reappearance is reconciled explicitly.
    with pytest.raises(RuntimeError, match="manual reconciliation"):
        entry._merge_entry_commitments([], [], prune=True)
    row = entry._read_entry_reservations()[0]
    assert row["submissionState"] == "cancelled"
    assert "cancelVerifiedAt" in row


def test_cancel_verification_marks_only_exact_local_reservation(
        tmp_path, monkeypatch):
    monkeypatch.setattr(clob_v2, "REPO_ROOT", tmp_path)
    ledger = tmp_path / ".entry_reservations.json"
    ledger.write_text(json.dumps([{
        "reservationId": "r1", "orderId": "0xorder",
        "submissionState": "live",
    }]))
    assert clob_v2._mark_reservation_cancel_verified("0xorder") is True
    row = json.loads(ledger.read_text())[0]
    assert row["submissionState"] == "cancelled"
    assert row["cancelVerifiedAt"].endswith("+00:00")
    assert clob_v2._mark_reservation_cancel_verified("0xother") is False


def test_unreserved_cancel_tombstone_blocks_future_entry(
        tmp_path, monkeypatch):
    monkeypatch.setattr(clob_v2, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    clob_v2._record_unreserved_cancel_block({
        "id": "0xlegacy", "market": "0xmarket", "asset_id": "token-yes",
        "side": "BUY", "original_size": "10", "size_matched": "2",
        "price": "0.4",
    })
    with pytest.raises(RuntimeError, match="manual reconciliation"):
        entry._merge_entry_commitments([], [])


def test_direct_clob_buy_atomically_claims_exact_pending_reservation(
        tmp_path, monkeypatch):
    monkeypatch.setattr(clob_v2, "REPO_ROOT", tmp_path)
    with pytest.raises(RuntimeError, match="no exposure reservation"):
        clob_v2._claim_buy_reservation("token-yes", 0.4, 4.0, "r1")
    ledger = tmp_path / ".entry_reservations.json"
    ledger.write_text(json.dumps([{
        "reservationId": "r1",
        "asset": "token-yes", "submissionState": "pending",
        "shares": 10, "risk": 4.2,
    }]))
    assert clob_v2._claim_buy_reservation(
        "token-yes", 0.4, 4.0, "r1")["shares"] == 10
    assert json.loads(ledger.read_text())[0]["submissionState"] == "claimed"
    with pytest.raises(RuntimeError, match="unclaimed pending"):
        clob_v2._claim_buy_reservation("token-yes", 0.4, 4.0, "r1")

    ledger.write_text(json.dumps([{
        "reservationId": "r2",
        "asset": "token-yes", "submissionState": "pending",
        "shares": 10, "risk": 4.2,
    }]))
    with pytest.raises(RuntimeError, match="exceeds"):
        clob_v2._claim_buy_reservation("token-yes", 0.5, 5.0, "r2")

    (tmp_path / ".entry_reconciliation_required.json").write_text("[]")
    with pytest.raises(RuntimeError, match="reconciliation tombstone"):
        clob_v2._claim_buy_reservation("token-yes", 0.4, 4.0, "r2")


def test_claimed_buy_reservation_remains_full_risk_commitment(
        tmp_path, monkeypatch):
    monkeypatch.setattr(clob_v2, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    record = {
        "conditionId": "0xcandidate", "slug": "candidate",
        "question": "Candidate?", "eventIds": ["event-1"],
        "asset": "token-yes", "shares": 10, "risk": 4.2,
        "baselineBought": 0,
    }
    reservation_id = entry._add_entry_reservation(record)
    clob_v2._claim_buy_reservation(
        "token-yes", 0.4, 4.0, reservation_id)
    commitments = entry._entry_reservation_commitments([], [])
    assert len(commitments) == 1
    assert commitments[0]["submissionState"] == "claimed"
    assert commitments[0]["risk"] == pytest.approx(4.2)


def test_low_level_buy_holds_shared_ledger_lock_through_post(
        tmp_path, monkeypatch):
    monkeypatch.setattr(clob_v2, "REPO_ROOT", tmp_path)
    ledger = tmp_path / ".entry_reservations.json"
    ledger.write_text(json.dumps([{
        "reservationId": "r1", "asset": "token-yes",
        "submissionState": "pending", "shares": 10, "risk": 4.2,
    }]))
    monkeypatch.setattr(clob_v2, "_load_wallet", lambda: ("0xwallet", "pk"))
    monkeypatch.setattr(clob_v2, "build_order", lambda **_kwargs: {"signed": True})

    def post_order(*_args, **_kwargs):
        code = (
            "import fcntl,sys\n"
            "f=open(sys.argv[1], 'w')\n"
            "try:\n"
            " fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
            "except BlockingIOError:\n"
            " sys.exit(0)\n"
            "sys.exit(1)\n"
        )
        probe = subprocess.run(
            [sys.executable, "-c", code,
             str(tmp_path / ".entry_reservation.lock")],
            check=False,
        )
        assert probe.returncode == 0
        return {"status_code": 200, "body": {"success": True}}

    monkeypatch.setattr(clob_v2, "post_order", post_order)
    args = SimpleNamespace(
        token_id="token-yes", price=0.4, usd_size=4.0,
        reservation_id="r1", neg_risk=False, order_type="FAK",
        post_only=False,
    )
    assert clob_v2.cmd_buy(args) == 0
    assert json.loads(ledger.read_text())[0]["submissionState"] == "claimed"


@pytest.mark.parametrize("orders", [
    [],
    [{"id": "0xorder", "side": "", "market": "0xmarket"}],
])
def test_cancel_refuses_absent_or_identity_unknown_target(
        orders, tmp_path, monkeypatch):
    monkeypatch.setattr(clob_v2, "REPO_ROOT", tmp_path)
    closed = []
    monkeypatch.setattr(
        clob_v2, "_acquire_entry_lock",
        lambda: SimpleNamespace(close=lambda: closed.append(True)),
    )
    monkeypatch.setattr(clob_v2, "list_open_orders", lambda: {
        "status_code": 200,
        "body": {"data": orders, "next_cursor": "LTE="},
    })
    monkeypatch.setattr(
        clob_v2, "cancel_order",
        lambda _order_id: pytest.fail("identity-unknown cancel must not DELETE"),
    )
    assert clob_v2.cmd_cancel(SimpleNamespace(order_id="0xorder")) == 3
    assert closed == [True]
    blocker = json.loads(
        (tmp_path / ".entry_reconciliation_required.json").read_text())
    assert blocker[0]["orderId"] == "0xorder"


def test_trade_match_totals_require_exact_confirmed_buy_identity(monkeypatch):
    record = {"conditionId": "0xmarket", "asset": "token-yes"}
    monkeypatch.setattr(clob_v2, "list_authenticated_trades", lambda: {
        "status_code": 200,
        "body": {"next_cursor": "LTE=", "data": [{
            "id": "trade-1", "status": "CONFIRMED", "market": "0xmarket",
            "asset_id": "token-yes", "side": "SELL", "size": "8",
            "taker_order_id": "other", "maker_orders": [{
                "order_id": "0xorder", "asset_id": "token-yes",
                "side": "BUY", "matched_amount": "2",
            }],
        }]},
    })
    assert entry._fetch_order_match_totals(
        {"0xorder": record}) == {"0xorder": pytest.approx(2)}

    monkeypatch.setattr(clob_v2, "list_authenticated_trades", lambda: {
        "status_code": 200,
        "body": {"next_cursor": "LTE=", "data": [{
            "id": "trade-1", "status": "MATCHED", "market": "0xmarket",
            "asset_id": "token-yes", "side": "SELL", "maker_orders": [{
                "order_id": "0xorder", "asset_id": "token-yes",
                "side": "BUY", "matched_amount": "2",
            }],
        }]},
    })
    with pytest.raises(RuntimeError, match="identity/state"):
        entry._fetch_order_match_totals({"0xorder": record})


def test_cancel_retirement_requires_affirmative_terminal_order(monkeypatch):
    record = {
        "conditionId": "0xmarket", "asset": "token-yes", "shares": 10,
    }
    monkeypatch.setattr(clob_v2, "get_authenticated_order", lambda _order_id: {
        "status_code": 200,
        "body": {
            "id": "0xorder", "status": "CANCELED", "side": "BUY",
            "market": "0xmarket", "asset_id": "token-yes",
            "original_size": "10", "size_matched": "2", "price": "0.4",
        },
    })
    assert entry._fetch_terminal_cancelled_totals(
        {"0xorder": record}) == {"0xorder": pytest.approx(2)}

    monkeypatch.setattr(clob_v2, "get_authenticated_order", lambda _order_id: {
        "status_code": 200, "body": None,
    })
    with pytest.raises(RuntimeError, match="lacks affirmative terminal status"):
        entry._fetch_terminal_cancelled_totals({"0xorder": record})


def test_market_sell_limit_walks_multiple_bid_levels():
    bids = [
        {"price": "0.99", "size": "100"},
        {"price": "0.996", "size": "5"},
    ]
    assert entry._marketable_sell_limit(bids, 20) == pytest.approx((0.99, 105.0))
    with pytest.raises(RuntimeError, match="only 105.00"):
        entry._marketable_sell_limit(bids, 106)
    with pytest.raises(RuntimeError, match="invalid rollback bid"):
        entry._marketable_sell_limit([{"price": math.nan, "size": 100}], 20)


def test_rollback_guard_caps_fee_aware_loss_per_possible_filled_leg():
    free = {"feesEnabled": False}
    legs = [
        {
            "slug": f"leg-{index}", "book": {"bids": [{"price": 0.49, "size": 20}]},
            "fee_market": free, "limit": 0.50, "fee_at_limit": 0.0,
        }
        for index in range(3)
    ]
    # Three legs can leave at most two prior fills. A $0.50 total cap allocates
    # $0.25 to each; the modeled $0.20 loss per leg is safe.
    assert entry._configure_rollback_guards(legs, 20, 0.50) == pytest.approx(0.25)
    assert all(leg["rollback_loss_per_share"] == pytest.approx(0.0125) for leg in legs)
    with pytest.raises(RuntimeError, match="exceeds per-leg cap"):
        entry._configure_rollback_guards(legs, 20, 0.30)


def test_bundle_nan_bankroll_is_rejected_before_market_lookup(monkeypatch):
    monkeypatch.setattr(
        entry, "fetch_market_by_slug_or_question",
        lambda slug: pytest.fail("numeric validation must precede market lookup"),
    )
    args = SimpleNamespace(
        bundle_slug=["one", "two"], my_p=0.75, bundle_shares=20.0,
        max_bundle_cost=0.57, bankroll=math.nan, kelly_frac=0.5,
        rho=0.0, cluster_frac=0.0, edge_haircut=0.10, side="YES",
        maker=False, usd=None, tail_mult=None, bundle_add=False,
        execute=False,
    )
    assert entry._bundle_entry(args) == 2


def test_clob_match_time_fee_translation_is_fail_closed():
    paid = {"compact": {"fd": {"r": 0.04, "e": 1, "to": True}}, "full": {}}
    assert entry._clob_fee_market(paid) == {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True},
    }
    free = {"compact": {}, "full": {"taker_base_fee": 0}}
    assert entry._clob_fee_market(free) == {"feesEnabled": False, "takerBaseFee": 0}
    compact_null = {"compact": {"tbf": None}, "full": {"taker_base_fee": 0}}
    assert entry._clob_fee_market(compact_null) == {
        "feesEnabled": False, "takerBaseFee": 0,
    }
    with pytest.raises(RuntimeError, match="not an object"):
        entry._clob_fee_market({
            "compact": {"fd": "malformed"}, "full": {"taker_base_fee": 0},
        })
    with pytest.raises(RuntimeError, match="malformed compact"):
        entry._clob_fee_market({
            "compact": {"fd": {"r": 0.04}}, "full": {"taker_base_fee": 0},
        })
    with pytest.raises(RuntimeError, match="invalid compact"):
        entry._clob_fee_market({
            "compact": {"fd": {"r": 0.04, "e": math.nan, "to": True}},
            "full": {"taker_base_fee": 0},
        })
    with pytest.raises(RuntimeError, match="invalid compact"):
        entry._clob_fee_market({
            "compact": {"fd": {"r": False, "e": 1, "to": True}},
            "full": {"taker_base_fee": 0},
        })
    assert entry._clob_fee_market({"compact": {}, "full": {}}) is None


def test_open_buy_commitment_counts_only_unfilled_buy_collateral(monkeypatch):
    monkeypatch.setattr(clob_v2, "list_open_orders", lambda: {
        "status_code": 200,
        "body": {"data": [
            {"asset_id": "other-buy", "side": "BUY", "price": "0.25",
             "original_size": "20", "size_matched": "4"},
            {"asset_id": "other-sell", "side": "SELL", "price": "0.90",
             "original_size": "50", "size_matched": "0"},
        ]},
    })
    assert entry._open_buy_commitment() == pytest.approx(4.0)


def test_existing_order_on_bundle_token_blocks_preflight(monkeypatch):
    monkeypatch.setattr(clob_v2, "list_open_orders", lambda: {
        "status_code": 200,
        "body": {"data": [{
            "asset_id": "2", "side": "SELL", "price": "0.90",
            "original_size": "20", "size_matched": "0",
        }]},
    })
    with pytest.raises(RuntimeError, match="touches bundle token"):
        entry._open_buy_commitment({"1", "2", "3"})


def test_open_order_shape_failure_is_not_treated_as_zero(monkeypatch):
    monkeypatch.setattr(clob_v2, "list_open_orders", lambda: {
        "status_code": 200, "body": {"unexpected": []},
    })
    with pytest.raises(RuntimeError, match="unexpected shape"):
        entry._open_buy_commitment()
