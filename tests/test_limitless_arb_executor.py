"""Fully mocked public-read integration tests for the quote inspector."""

from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import limitless_arb_executor as executor


NOW = 1_000.0


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def candidate():
    return {
        "lim_id": "lim-1", "lim_slug": "lim-leaf",
        "lim_yes_token": "lim-yes", "lim_no_token": "lim-no",
        "pm_slug": "pm-market",
    }


def payloads():
    market = {
        "id": "lim-1", "slug": "lim-leaf", "status": "FUNDED",
        "tradeType": "CLOB", "marketType": "single",
        "expirationTimestamp": NOW + 1_000,
        "tokens": {"yes": "lim-yes", "no": "lim-no"},
        "collateralToken": {
            "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "decimals": 6,
        },
    }
    lim_book = {
        "tokenId": "lim-yes",
        "asks": [{"price": "0.20", "size": "10000000"}],
        "bids": [{"price": "0.80", "size": "10000000"}],
    }
    gamma = {
        "slug": "pm-market",
        "conditionId": "condition-1", "active": True, "closed": False,
        "resolved": False, "outcomes": '["No", "Yes"]',
        "clobTokenIds": '["pm-no", "pm-yes"]',
        "feeSchedule": {"rate": 0, "exponent": 2, "takerOnly": True},
    }
    def book(token):
        return {"asset_id": token, "market": "condition-1", "timestamp": NOW,
                "min_order_size": "1", "asks": [{"price": "0.20", "size": "20"}],
                "bids": []}
    return market, lim_book, gamma, {"pm-yes": book("pm-yes"), "pm-no": book("pm-no")}


def mocked_get(monkeypatch, *, mutate=None, calls=None):
    market, lim_book, gamma, books = payloads()
    data = {"market": market, "lim_book": lim_book, "gamma": gamma, "books": books}
    if mutate:
        mutate(data)
    calls = calls if calls is not None else []

    def get(url, params=None, timeout=None):
        calls.append((url, params))
        if url == f"{executor.LIMITLESS_API_BASE}/markets/lim-leaf":
            return Response(data["market"])
        if url == f"{executor.LIMITLESS_API_BASE}/markets/lim-leaf/orderbook":
            return Response(data["lim_book"])
        if url == f"{executor.POLYMARKET_GAMMA}/markets":
            return Response([data["gamma"]])
        if url == executor.POLYMARKET_CLOB:
            return Response(data["books"][params["token_id"]])
        raise AssertionError(f"unexpected public URL {url!r} {params!r}")

    monkeypatch.setattr(executor.httpx, "get", get)
    return calls


def test_quotes_both_complementary_orientations_and_reads_one_yes_book(monkeypatch):
    calls = mocked_get(monkeypatch)
    result = executor._live_arb_quote(candidate(), 1, now=NOW)
    assert set(result["directions"]) == {"lim_yes_pm_no", "lim_no_pm_yes"}
    assert result["execution_ready"] is False
    assert result["screening_only"] is True
    assert result["directions"]["lim_yes_pm_no"]["lim"]["buy_token"] == "YES"
    assert result["directions"]["lim_no_pm_yes"]["lim"]["buy_token"] == "NO"
    orderbook_calls = [call for call in calls if call[0].endswith("/orderbook")]
    assert len(orderbook_calls) == 1
    assert orderbook_calls[0][1] is None


@pytest.mark.parametrize("mutate, text", [
    (lambda d: d["market"].update(id="other"), "id does not match"),
    (lambda d: d["market"].update(marketType="group", markets=[{"id": "child"}]), "children"),
    (lambda d: d["market"].update(subMarkets=[{"id": "child"}]), "children"),
    (lambda d: d["market"].update(status="RESOLVED"), "CREATED/FUNDED"),
    (lambda d: d["gamma"].update(umaResolutionStatuses='["proposed"]'), "UMA resolution status"),
    (lambda d: d["gamma"].update(outcomes='["Yes", "Maybe"]'), "Yes/No mapping"),
    (lambda d: d["books"]["pm-no"].update(timestamp=NOW - 121), "timestamp age"),
])
def test_invalid_identity_group_resolution_or_stale_book_is_unpriced(monkeypatch, mutate, text):
    mocked_get(monkeypatch, mutate=mutate)
    result = executor._live_arb_quote(candidate(), 1, now=NOW)
    assert result["ok"] is False
    assert result["status"] == "unpriced"
    assert text in result["reason"]
    assert result["execution_ready"] is False


def test_pm_outcome_mapping_and_both_cash_caps_are_enforced(monkeypatch):
    calls = mocked_get(monkeypatch)
    one = executor._live_arb_quote(candidate(), 1, now=NOW)
    three = executor._live_arb_quote(candidate(), 3, now=NOW)
    assert one["selected"]["cash_cap_usdc"] == 1
    assert three["selected"]["cash_cap_usdc"] == 3
    assert one["selected"]["pm"]["token_id"] == "pm-no"  # labels, not Gamma order
    assert any(p == {"token_id": "pm-yes"} for _, p in calls if p)
    assert any(p == {"token_id": "pm-no"} for _, p in calls if p)


def test_group_typed_leaf_without_children_is_supported(monkeypatch):
    mocked_get(monkeypatch, mutate=lambda d: d["market"].update(marketType="group", markets=[]))
    result = executor._live_arb_quote(candidate(), 1, now=NOW)
    assert result["status"] == "screening_quote_only"


@pytest.mark.parametrize("fee_update, text", [
    (lambda d: d["gamma"].pop("feeSchedule"), "missing"),
    (lambda d: d["gamma"].update(feeSchedule={"rate": "bad", "exponent": 1}), "invalid"),
])
def test_missing_or_malformed_pm_fee_metadata_is_unpriced(monkeypatch, fee_update, text):
    mocked_get(monkeypatch, mutate=fee_update)
    result = executor._live_arb_quote(candidate(), 1, now=NOW)
    assert result["status"] == "unpriced"
    assert text in result["reason"]


def test_scan_freshness_fails_closed_before_public_reads():
    assert executor._scan_is_fresh({}, now=NOW) == (
        False, "scan snapshot has no verifiable generated_at")
    assert executor._scan_is_fresh({"generated_at": NOW - executor.SCAN_MAX_AGE_SECONDS - 1}, now=NOW)[0] is False
    assert executor._scan_is_fresh({"generated_at": NOW - 1}, now=NOW)[0] is True


def test_cap_failure_is_conditional_rejection_not_plausible_zero(monkeypatch):
    def mutate(data):
        data["lim_book"]["asks"][0]["price"] = "0.90"
        data["lim_book"]["bids"][0]["price"] = "0.10"
        for book in data["books"].values():
            book["asks"][0]["price"] = "0.90"
    mocked_get(monkeypatch, mutate=mutate)
    result = executor._live_arb_quote(candidate(), 1, now=NOW)
    assert result["ok"] is False
    assert "conditional profit/edge" in result["reason"]
    assert result["selected"]["conditional_profit_floor_usdc"] < 0


def test_minimum_failed_direction_does_not_mask_other_eligible_direction(monkeypatch):
    def mutate(data):
        data["books"]["pm-no"]["min_order_size"] = "100"
    mocked_get(monkeypatch, mutate=mutate)
    result = executor._live_arb_quote(candidate(), 1, now=NOW)
    assert result["ok"] is True
    assert result["best_direction"] == "lim_no_pm_yes"


def test_old_candidate_without_slug_fails_before_any_public_read(monkeypatch):
    calls = []
    mocked_get(monkeypatch, calls=calls)
    old = candidate()
    del old["lim_slug"]
    result = executor._live_arb_quote(old, 1, now=NOW)
    assert result["status"] == "unpriced"
    assert "lim_slug" in result["reason"]
    assert calls == []
