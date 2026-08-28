from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import clob_v2  # noqa: E402
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
    priors["other-correlated"] = {"cluster": "range"}
    (notes / "portfolio_kelly_priors.json").write_text(json.dumps(priors))
    monkeypatch.setattr(entry, "REPO_ROOT", tmp_path)
    legs = [{**leg, "event_ids": {"event-1"}} for leg in _legs()]
    positions = [
        {"slug": "leg-1", "eventId": "event-1", "size": 20,
         "initialValue": 3, "entryFeesUsdc": 0.1},
        # Same event must count even though its slug is absent from priors.
        {"slug": "unconfigured-bucket", "eventId": "event-1", "size": 5,
         "initialValue": 2, "entryFeesUsdc": 0.2},
        # Cross-event position counts through the explicit cluster tag.
        {"slug": "other-correlated", "eventId": "event-2", "size": 4,
         "initialValue": 1, "entryFeesUsdc": 0.3},
    ]
    assert entry._existing_cluster_cost(legs, positions) == pytest.approx(6.6)


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
