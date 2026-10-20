from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import entry_review_gate as gate
import monotonicity_pair as pair
import polyclaude_enter as entry


def no_account_access(monkeypatch):
    def unexpected(*_args, **_kwargs):
        pytest.fail("account/reservation access before review authorization")
    for name in ("_chain_reader", "_fetch_live_positions", "_fetch_open_buy_commitments",
                 "_add_entry_reservations", "_add_entry_reservation"):
        monkeypatch.setattr(entry, name, unexpected)


SINGLE = ["--slug", "candidate", "--my-p", ".8", "--maker", "--execute", "--bankroll", "200"]
BUNDLE = ["--bundle-slug", "early", "--bundle-slug", "late", "--side", "YES",
          "--my-p", ".8", "--bundle-shares", "5", "--max-bundle-cost", ".8",
          "--bankroll", "200", "--execute"]
PAIR = ["--early", "early", "--late", "late", "--shares", "5", "--max-cost", ".8",
        "--bankroll", "200", "--cluster", "test", "--execute"]


@pytest.mark.parametrize("route,arguments", [(entry, SINGLE), (entry, BUNDLE), (pair, PAIR)])
def test_execute_pause_stops_each_route_before_venue_or_account(monkeypatch, route, arguments):
    def denied(*_args):
        raise gate.EntryReviewGateError("383/600 completed valuations")
    def unexpected(*_args, **_kwargs):
        pytest.fail("venue lookup before review authorization")
    monkeypatch.setattr(gate, "require_new_buy_allowed", denied)
    monkeypatch.setattr(entry, "fetch_market_by_slug_or_question", unexpected)
    monkeypatch.setattr(pair, "lookup_active_market_identifier", unexpected)
    no_account_access(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["entry"] + arguments)
    assert route.main() == 3


def market(index):
    return {"id": str(index), "slug": "early" if index == 1 else "late",
            "question": f"Will yield be {index}% or lower?",
            "conditionId": f"0x{index:064x}", "active": True, "closed": False,
            "enableOrderBook": True, "acceptingOrders": True, "umaResolutionStatus": None,
            "resolutionSource": "https://example.test/rules",
            "description": "Resolve if listed value is met. Source: 2026 dataset.",
            "endDate": "2026-12-31T23:59:00Z", "outcomes": '["Yes", "No"]',
            "clobTokenIds": json.dumps([str(index * 2 - 1), str(index * 2)]),
            "negRisk": True, "negRiskMarketID": "event", "events": [{"id": "event"}]}


def test_bundle_checks_all_selected_tokens_before_any_account_or_reservation(monkeypatch):
    calls = []
    def authorize(token=None):
        calls.append(token)
        if token == "3":
            raise gate.EntryReviewGateError("second leg is not selected")
    monkeypatch.setattr(gate, "require_new_buy_allowed", authorize)
    monkeypatch.setattr(entry, "fetch_market_by_slug_or_question",
                        lambda slug: market(1 if slug == "early" else 2))
    no_account_access(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["entry"] + BUNDLE)
    assert entry.main() == 3
    assert calls == [None, "1", "3"]


def test_pair_checks_both_selected_tokens_before_any_account_or_reservation(monkeypatch):
    calls = []
    def authorize(token=None):
        calls.append(token)
        if token == "3":
            raise gate.EntryReviewGateError("second leg is not selected")
    monkeypatch.setattr(gate, "require_new_buy_allowed", authorize)
    monkeypatch.setattr(pair, "lookup_active_market_identifier",
                        lambda slug: market(1 if slug == "early" else 2))
    monkeypatch.setattr(pair, "_build_leg", lambda m, outcome, shares: {
        "token": json.loads(m["clobTokenIds"])[0 if outcome == "YES" else 1],
        "limit": .2, "fee_at_limit": 0})
    no_account_access(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["pair"] + PAIR)
    assert pair.main() == 1
    assert calls == [None, "2", "3"]
