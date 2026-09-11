from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import monotonicity_pair as pair
from monotonicity_pair import validate_pair_markets
import polyclaude_enter as entry


def market(threshold: int, *, source: str = "https://example.test/rules",
           end: str = "2026-12-31T23:59:00Z", comparator: str = "or lower",
           subject: str = "yield") -> dict:
    return {
        "id": str(threshold), "slug": f"x-{threshold}",
        "question": f"Will {subject} be {threshold}% {comparator}?",
        "conditionId": f"0x{threshold:064x}", "active": True, "closed": False,
        "umaResolutionStatus": None, "resolutionSource": source,
        "description": "Resolve if the listed value is met. Source: 2026 dataset.",
        "endDate": end, "outcomes": '["Yes", "No"]',
        "clobTokenIds": '["1", "2"]',
        "enableOrderBook": True, "acceptingOrders": True, "negRisk": False,
        "events": [{"id": "event-1"}],
    }


def test_pair_requires_early_subset_and_exact_shared_criteria():
    result = validate_pair_markets(market(435), market(445))
    assert result["source"].endswith("rules")
    with pytest.raises(RuntimeError, match="thresholds"):
        validate_pair_markets(market(445), market(435))
    with pytest.raises(RuntimeError, match="sources"):
        validate_pair_markets(market(435), market(445, source="https://other.test"))
    with pytest.raises(RuntimeError, match="deadlines"):
        validate_pair_markets(market(435), market(445, end="2027-01-01T00:00:00Z"))


def test_pair_rejects_non_binary_or_active_uma():
    bad = market(435)
    bad["outcomes"] = '["Yes", "Maybe"]'
    with pytest.raises(RuntimeError, match="binary"):
        validate_pair_markets(bad, market(445))
    bad = market(435)
    bad["umaResolutionStatus"] = "proposed"
    with pytest.raises(RuntimeError, match="UMA"):
        validate_pair_markets(bad, market(445))


def test_pair_rejects_resolved_status():
    bad = market(435)
    bad["umaResolutionStatus"] = "resolved"
    with pytest.raises(RuntimeError, match="UMA"):
        validate_pair_markets(bad, market(445))


def test_pair_rejects_wrong_event_or_exchange_route():
    bad_event = market(445)
    bad_event["events"] = [{"id": "event-2"}]
    with pytest.raises(RuntimeError, match="event ID"):
        validate_pair_markets(market(435), bad_event)
    bad_route = market(445)
    bad_route["negRisk"] = True
    with pytest.raises(RuntimeError, match="negRisk"):
        validate_pair_markets(market(435), bad_route)


def test_pair_proves_direction_and_same_proposition():
    validate_pair_markets(
        market(445, comparator="or higher"),
        market(435, comparator="or higher"),
    )
    with pytest.raises(RuntimeError, match="thresholds"):
        validate_pair_markets(
            market(435, comparator="or higher"),
            market(445, comparator="or higher"),
        )
    with pytest.raises(RuntimeError, match="thresholds"):
        validate_pair_markets(market(435), market(445, subject="inflation"))


def test_standard_binary_order_uses_neg_risk_false(monkeypatch):
    seen = {}
    response = '{"status_code":200,"body":{"success":false,"status":"unmatched"}}'
    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        return type("R", (), {"stdout": response, "stderr": "", "returncode": 0})()
    monkeypatch.setattr(entry.subprocess, "run", fake_run)
    state, _ = entry._run_clob_order("BUY", "123", .44, 7.04, 16, "rid",
                                     neg_risk=False)
    assert state == "failed"
    assert seen["cmd"][seen["cmd"].index("--neg-risk") + 1] == "false"


def test_build_leg_rejects_unvalidated_book(monkeypatch):
    monkeypatch.setattr(pair.entry, "_clob_market_info", lambda _: {
        "full": {"tokens": [{"token_id": "2", "outcome": "No"}],
                 "neg_risk": False},
        "minimum_tick_size": .01, "minimum_order_size": 1,
    })
    monkeypatch.setattr(pair, "_fetch_validated_clob_book", lambda *_: None)
    with pytest.raises(RuntimeError, match="stale|identity"):
        pair._build_leg(market(435), "NO", 16)


def test_build_leg_sorts_raw_book_and_enforces_both_minimums(monkeypatch):
    curve = SimpleNamespace(authoritative=True)
    monkeypatch.setattr(pair.entry, "_clob_market_info", lambda _: {
        "full": {"tokens": [{"token_id": "2", "outcome": "No"}],
                 "neg_risk": False},
        "minimum_tick_size": .01, "minimum_order_size": 5,
    })
    monkeypatch.setattr(pair.entry, "_clob_fee_market", lambda _: {})
    monkeypatch.setattr(pair.pm_fees, "fee_schedule", lambda _: curve)
    monkeypatch.setattr(pair.pm_fees, "max_taker_buy_cost_through",
                        lambda _market, price: price)
    monkeypatch.setattr(pair, "_fetch_validated_clob_book", lambda *_: {
        "asks": [(0.99, 100), (0.46, 4), (0.44, 20)],
        "bids": [(0.01, 100), (0.42, 50)],
        "min_order_size": 3,
        "timestamp": 1,
    })

    leg = pair._build_leg(market(435), "NO", 16)
    assert leg["ask"] == pytest.approx(.44)
    assert leg["book"]["best_bid"] == pytest.approx(.42)
    assert leg["depth"] == pytest.approx(20)
    with pytest.raises(RuntimeError, match="below CLOB minimum"):
        pair._build_leg(market(435), "NO", 4)


def test_submission_rejects_fee_increase_above_reservation(monkeypatch):
    planned = {
        "token": "token", "condition_id": "0xabc", "neg_risk": False,
        "outcome": "NO", "limit": .44, "fee_at_limit": .01,
        "slug": "candidate",
    }
    monkeypatch.setattr(pair, "_build_leg", lambda *_: {
        **planned,
        "book": {"asks": [{"price": .44, "size": 20}]},
        "fee_market": {}, "depth": 20,
    })
    monkeypatch.setattr(pair.pm_fees, "max_taker_buy_cost_through",
                        lambda _market, price: price + .02)
    with pytest.raises(RuntimeError, match="fee increased"):
        pair._submission_leg(planned, market(435), 16)


def test_rollback_refresh_fetches_current_gamma_and_pins_identity(monkeypatch):
    old = market(435)
    fresh = {**old, "feesEnabled": True}
    seen = []
    monkeypatch.setattr(pair, "lookup_active_market_identifier", lambda _: fresh)
    monkeypatch.setattr(pair, "_leg_state",
                        lambda raw, outcome: seen.append((raw, outcome)) or {"ok": True})
    assert pair._rollback_refresh({
        "market": old, "slug": old["slug"], "outcome": "NO",
    }) == {"ok": True}
    assert seen == [(fresh, "NO")]


def test_execute_path_keeps_one_bundle_and_reconciles_both_legs(monkeypatch):
    early, late = market(435), market(445)
    balances = {"early-no": 0.0, "late-yes": 0.0}
    submitted, reservations, updates, cap_calls = [], [], [], []

    monkeypatch.setattr(pair, "lookup_active_market_identifier",
                        lambda identifier: early if "435" in identifier else late)

    def build_leg(raw, outcome, shares):
        is_early = raw["id"] == "435"
        return {
            "market": raw, "slug": raw["slug"], "question": raw["question"],
            "condition_id": raw["conditionId"],
            "token": "early-no" if is_early else "late-yes", "outcome": outcome,
            "limit": .45, "fee_at_limit": 0.0,
            "depth": 100.0 if is_early else 20.0, "neg_risk": False,
            "book": {
                "asks": [{"price": .45, "size": 100.0}],
                "bids": [{"price": .44, "size": 100.0}],
            },
            "fee_market": {"feesEnabled": False},
        }

    monkeypatch.setattr(pair, "_build_leg", build_leg)
    monkeypatch.setattr(entry, "_chain_reader", lambda *, neg_risk: {"reader": True})
    monkeypatch.setattr(entry, "_fetch_live_positions", lambda: [])
    monkeypatch.setattr(entry, "_fetch_open_buy_commitments", lambda: [])
    monkeypatch.setattr(entry, "_merge_entry_commitments", lambda *a, **k: [])
    def cap_state(*args, **kwargs):
        cap_calls.append((args, kwargs))
        return {
            "cluster_before": 0.0, "cluster_after": 7.2,
            "cluster_cap": 60.0, "ticket_before": 0.0,
            "ticket_after": 7.2, "ticket_cap": 30.0,
            "new_risk": 7.2, "cluster": "treasury",
        }
    monkeypatch.setattr(entry, "_single_entry_cap_state", cap_state)
    monkeypatch.setattr(entry, "_single_entry_cap_error", lambda _: None)
    monkeypatch.setattr(entry, "_wallet_funds_state", lambda *_: {
        "ctf_approved": True, "deployable": 20.0, "allowance": 100.0,
        "committed": 0.0,
    })
    monkeypatch.setattr(entry, "_read_token_balances",
                        lambda _reader, tokens: {token: balances[token] for token in tokens})

    def guards(legs, _shares, _cap):
        for leg in legs:
            leg["rollback_modeled_loss"] = .1
            leg["rollback_loss_per_share"] = .01
        return .2

    monkeypatch.setattr(entry, "_configure_rollback_guards", guards)
    monkeypatch.setattr(entry, "_acquire_entry_lock",
                        lambda: SimpleNamespace(close=lambda: None))

    def add_records(rows):
        reservations.extend(rows)
        return ["rid-early", "rid-late"]

    monkeypatch.setattr(entry, "_add_entry_reservations", add_records)
    monkeypatch.setattr(entry, "_reservation_indexed_bought",
                        lambda record, _positions: 2 if record["asset"] == "early-no" else 3)

    def run_order(_side, token, _price, _size, expected, _rid, **_kwargs):
        submitted.append(token)
        balances[token] += expected
        return "matched", json.dumps({
            "status_code": 200,
            "body": {
                "success": True, "status": "matched",
                "orderID": f"order-{token}",
                "transactionsHashes": [f"tx-{token}"],
                "takingAmount": str(expected),
            },
        })

    monkeypatch.setattr(entry, "_run_clob_order", run_order)
    monkeypatch.setattr(entry, "_wait_token_balance",
                        lambda _reader, token, _expected: balances[token])
    monkeypatch.setattr(entry, "_update_entry_reservation",
                        lambda rid, order_id="", **kwargs:
                        updates.append((rid, order_id, kwargs)))
    monkeypatch.setattr(sys, "argv", [
        "monotonicity_pair.py", "--early", "market-435", "--late", "market-445",
        "--shares", "16", "--max-cost", ".93", "--bankroll", "200",
        "--cluster", "treasury", "--execute",
    ])

    assert pair.main() == 0
    assert submitted == ["early-no", "late-yes"]
    assert len({row["bundleId"] for row in reservations}) == 1
    assert len(cap_calls) == 4  # two legs in preview and again under the lock
    assert [row["baselineBought"] for row in reservations] == [2, 3]
    assert {row["cluster"] for row in reservations} == {"treasury"}
    assert updates == [
        ("rid-early", "order-early-no", {"submission_state": "matched"}),
        ("rid-late", "order-late-yes", {"submission_state": "matched"}),
    ]
    assert balances == {"early-no": 16.0, "late-yes": 16.0}
