"""Money-math pins for the Polymarket consistency basket scanner."""

from __future__ import annotations

import math
import json
import sys
import time
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import polymarket_consistency_scan as consistency  # noqa: E402


class _Response:
    def __init__(self, payload):
        self._payload = payload
        self.content = json.dumps(payload).encode()
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload

    def iter_bytes(self, chunk_size=65_536):
        for offset in range(0, len(self.content), chunk_size):
            yield self.content[offset:offset + chunk_size]


def _patch_event_stream(monkeypatch, fake_get) -> None:
    def fake_stream(_method, url, *, params, headers, timeout):
        assert headers == {"Accept-Encoding": "identity"}
        return fake_get(url, params=params, timeout=timeout)

    monkeypatch.setattr(consistency.httpx, "stream", fake_stream)


def _event(event_id: int, market_ids: list[int]) -> dict:
    return {
        "id": str(event_id),
        "title": f"event {event_id}",
        "slug": f"event-{event_id}",
        "active": True,
        "closed": False,
        "archived": False,
        "negRisk": True,
        "negRiskMarketID": "0x" + f"{event_id + 10_000:064x}",
        "volume24hr": 1_000_000 - event_id,
        "markets": [
            {
                "id": str(market_id),
                "conditionId": "0x" + f"{market_id:064x}",
                "question": f"market {market_id}?",
                "active": True,
                "closed": False,
                "archived": False,
                "acceptingOrders": True,
                "enableOrderBook": True,
                "negRisk": True,
                "negRiskMarketID": "0x" + f"{event_id + 10_000:064x}",
                "outcomes": ["Yes", "No"],
                "outcomePrices": [0.6, 0.4],
                "clobTokenIds": [str(2 * market_id + 1), str(2 * market_id + 2)],
                "liquidityNum": 10,
                "orderMinSize": 5,
                "feesEnabled": False,
                "feeSchedule": None,
                "takerBaseFee": None,
            }
            for market_id in market_ids
        ],
    }


FETCH_ARGS = {"end_date_min": "2026-08-29T00:00:00Z"}


def test_fetch_universe_flattens_events_with_parent_identity(monkeypatch) -> None:
    calls = []

    def fake_get(url, *, params, timeout):
        calls.append((url, params, timeout))
        return _Response({"events": [_event(7, [70, 71])], "next_cursor": None})

    _patch_event_stream(monkeypatch, fake_get)
    snapshot = consistency.fetch_universe(**FETCH_ARGS)
    rows = snapshot.markets

    assert [row["id"] for row in rows] == ["70", "71"]
    assert all(row["events"] == [{
        "id": "7",
        "title": "event 7",
        "slug": "event-7",
        "active": True,
        "closed": False,
        "negRisk": True,
        "negRiskMarketID": "0x" + f"{10_007:064x}",
    }] for row in rows)
    assert calls[0][0].endswith("/events/keyset")
    assert calls[0][1]["closed"] == "false"
    assert calls[0][1]["end_date_min"] == FETCH_ARGS["end_date_min"]
    assert calls[0][1]["exclude_tag_id"] == consistency.SPORTS_TAG_ID
    assert "after_cursor" not in calls[0][1]
    assert snapshot.coverage["coverage_complete"] is True
    assert snapshot.coverage["raw_response_bytes"] == len(calls) * len(
        _Response({"events": [_event(7, [70, 71])], "next_cursor": None}).content
    )


def test_fetch_universe_paginates_events(monkeypatch) -> None:
    first = [_event(0, [99]), _event(1, [1])]
    second = [_event(100, [100])]
    cursors = []

    def fake_get(_url, *, params, timeout):
        del timeout
        cursor = params.get("after_cursor")
        cursors.append(cursor)
        if cursor is None:
            return _Response({"events": first, "next_cursor": "page-2"})
        return _Response({"events": second, "next_cursor": None})

    _patch_event_stream(monkeypatch, fake_get)
    rows = consistency.fetch_universe(max_markets=5000, **FETCH_ARGS).markets

    assert cursors == [None, "page-2"]
    assert [row["id"] for row in rows] == ["99", "1", "100"]
    assert len({row["id"] for row in rows}) == 3


def test_fetch_universe_rejects_duplicate_market_identity(monkeypatch) -> None:
    first = [_event(0, [99])]
    second = [_event(100, [99])]

    def fake_get(_url, *, params, timeout):
        del timeout
        if params.get("after_cursor") is None:
            return _Response({"events": first, "next_cursor": "page-2"})
        return _Response({"events": second, "next_cursor": None})

    _patch_event_stream(monkeypatch, fake_get)
    with pytest.raises(RuntimeError, match="repeated a market condition"):
        consistency.fetch_universe(max_markets=5000, **FETCH_ARGS)


def test_fetch_universe_soft_cap_never_splits_an_event(monkeypatch) -> None:
    _patch_event_stream(
        monkeypatch,
        lambda *_args, **_kwargs: _Response({
            "events": [_event(1, [10, 11, 12])],
            "next_cursor": "unused-because-cap-is-reached",
        }),
    )

    snapshot = consistency.fetch_universe(max_markets=2, **FETCH_ARGS)
    rows = snapshot.markets

    assert [row["id"] for row in rows] == ["10", "11", "12"]
    assert snapshot.coverage["coverage_complete"] is False
    assert snapshot.coverage["stop_reason"] == "market_cap"


def test_fetch_universe_fails_closed_on_partial_fetch(monkeypatch) -> None:
    def fail(*_args, **_kwargs):
        raise OSError("network down")

    _patch_event_stream(monkeypatch, fail)
    monkeypatch.setattr(consistency.time, "sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError, match="refusing to scan a partial universe"):
        consistency.fetch_universe(**FETCH_ARGS)


def test_fetch_universe_retries_transient_page(monkeypatch) -> None:
    calls = 0

    def flaky(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("one transient disconnect")
        return _Response({"events": [_event(1, [10])], "next_cursor": None})

    _patch_event_stream(monkeypatch, flaky)
    monkeypatch.setattr(consistency.time, "sleep", lambda _seconds: None)

    assert [row["id"] for row in consistency.fetch_universe(**FETCH_ARGS).markets] == ["10"]
    assert calls == 2


def test_fetch_universe_fails_closed_on_repeated_cursor(monkeypatch) -> None:
    calls = 0

    def repeated_cursor(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return _Response({
            "events": [_event(calls, [calls])],
            "next_cursor": "same-cursor",
        })

    _patch_event_stream(monkeypatch, repeated_cursor)

    with pytest.raises(RuntimeError, match="repeated a cursor"):
        consistency.fetch_universe(**FETCH_ARGS)


def test_fetch_universe_byte_cap_is_explicitly_incomplete(monkeypatch) -> None:
    response = _Response({"events": [_event(1, [10])], "next_cursor": None})
    _patch_event_stream(monkeypatch, lambda *_a, **_k: response)

    snapshot = consistency.fetch_universe(max_bytes=len(response.content) - 1,
                                          **FETCH_ARGS)

    assert snapshot.markets == []
    assert snapshot.coverage["coverage_complete"] is False
    assert snapshot.coverage["stop_reason"] == "byte_cap"


def test_malformed_token_identity_suppresses_event_and_complete_zero(monkeypatch) -> None:
    event = _event(1, [10, 11])
    event["markets"][1]["clobTokenIds"] = ["21", "21"]
    _patch_event_stream(
        monkeypatch,
        lambda *_a, **_k: _Response({"events": [event], "next_cursor": None}),
    )

    snapshot = consistency.fetch_universe(**FETCH_ARGS)

    assert snapshot.markets == []
    assert snapshot.coverage["coverage_complete"] is True
    assert snapshot.coverage["analysis_complete"] is False
    assert snapshot.coverage["invalid_neg_risk_events"] == 1


@pytest.mark.parametrize("bad_members", [None, {}, ""])
def test_neg_risk_event_requires_real_membership(monkeypatch, bad_members) -> None:
    event = _event(1, [10])
    event["markets"] = bad_members
    _patch_event_stream(
        monkeypatch,
        lambda *_a, **_k: _Response({"events": [event], "next_cursor": None}),
    )

    with pytest.raises(RuntimeError, match="malformed market membership"):
        consistency.fetch_universe(**FETCH_ARGS)


def test_empty_neg_risk_membership_prevents_complete_analysis(monkeypatch) -> None:
    event = _event(1, [])
    _patch_event_stream(
        monkeypatch,
        lambda *_a, **_k: _Response({"events": [event], "next_cursor": None}),
    )

    snapshot = consistency.fetch_universe(**FETCH_ARGS)

    assert snapshot.coverage["coverage_complete"] is True
    assert snapshot.coverage["analysis_complete"] is False
    assert snapshot.coverage["invalid_neg_risk_events"] == 1


def test_group_identity_blocks_missing_neg_risk_shortcut(monkeypatch) -> None:
    event = _event(1, [10])
    event.pop("negRisk")
    event["markets"][0]["negRisk"] = None
    _patch_event_stream(
        monkeypatch,
        lambda *_a, **_k: _Response({"events": [event], "next_cursor": None}),
    )

    with pytest.raises(RuntimeError, match="malformed negRisk flag"):
        consistency.fetch_universe(**FETCH_ARGS)


def test_stream_byte_cap_stops_after_one_bounded_probe(monkeypatch) -> None:
    response = _Response({"unused": True})
    response.content = b"x" * 10_000
    _patch_event_stream(monkeypatch, lambda *_a, **_k: response)

    snapshot = consistency.fetch_universe(max_bytes=100, **FETCH_ARGS)

    assert snapshot.coverage["stop_reason"] == "byte_cap"
    assert snapshot.coverage["raw_response_bytes"] == 101
    assert snapshot.coverage["accepted_response_bytes"] == 0
    assert snapshot.coverage["byte_cap_probe_overshoot_bytes"] == 1


def test_grouping_uses_authoritative_neg_risk_market_id() -> None:
    parent = {
        "id": "display-event",
        "title": "event",
        "negRiskMarketID": "0x" + "a" * 64,
    }
    markets = [
        {"conditionId": "0x" + f"{i:064x}", "events": [parent]}
        for i in (1, 2)
    ]

    groups = consistency.group_by_event(markets)

    assert list(groups) == [parent["negRiskMarketID"]]
    assert len(groups[parent["negRiskMarketID"]]) == 2


def test_walk_ask_requires_full_depth() -> None:
    assert consistency._walk_ask([(0.4, 4)], 5) is None


def _live_members() -> tuple[list[tuple[dict, float]], dict[str, dict]]:
    event = _event(7, [70, 71])
    parent = {
        "id": event["id"],
        "title": event["title"],
        "slug": event["slug"],
        "active": True,
        "closed": False,
        "negRisk": True,
        "negRiskMarketID": event["negRiskMarketID"],
    }
    raw_by_id = {}
    members = []
    for raw in event["markets"]:
        raw["feesEnabled"] = True
        raw["feeSchedule"] = {
            "rate": 0.04,
            "exponent": 1,
            "takerOnly": True,
            "rebateRate": 0.25,
        }
        raw_by_id[raw["id"]] = raw
        compact = consistency._normalize_neg_risk_market(raw, parent)
        members.append((compact, consistency._yes_price(compact)))
    return members, raw_by_id


def _clob_info(raw: dict) -> dict:
    schedule = raw.get("feeSchedule")
    payload = {
        "c": raw["conditionId"],
        "t": [
            {"t": raw["clobTokenIds"][0], "o": "Yes"},
            {"t": raw["clobTokenIds"][1], "o": "No"},
        ],
        "mos": raw["orderMinSize"],
        "mts": 0.01,
        "ao": True,
        "nr": True,
    }
    if isinstance(schedule, dict):
        payload["fd"] = {
            "r": schedule["rate"],
            "e": schedule["exponent"],
            "to": schedule["takerOnly"],
        }
    return payload


def _raw_for_condition(raw_by_id: dict[str, dict], condition_id: str) -> dict:
    return next(raw for raw in raw_by_id.values() if raw["conditionId"] == condition_id)


def test_live_quote_refreshes_exact_fees_and_walks_every_level(monkeypatch) -> None:
    members, raw_by_id = _live_members()
    monkeypatch.setattr(consistency.time, "time", lambda: 1_000.0)

    def fake_get(url, *, params=None, timeout):
        del timeout
        if "/markets/" in url:
            return _Response(raw_by_id[url.rsplit("/", 1)[1]])
        if "/clob-markets/" in url:
            return _Response(_clob_info(
                _raw_for_condition(raw_by_id, url.rsplit("/", 1)[1])
            ))
        token = params["token_id"]
        market = next(
            m for m, _ in members if token in m["clobTokenIds"]
        )
        asks = (
            [{"price": "0.30", "size": "2"}, {"price": "0.40", "size": "3"}]
            if market["id"] == "70"
            else [{"price": "0.20", "size": "5"}]
        )
        return _Response({
            "asset_id": token,
            "market": market["conditionId"],
            "timestamp": "1000000",
            "min_order_size": "5",
            "tick_size": "0.01",
            "neg_risk": True,
            "hash": f"hash-{token}",
            "bids": [{"price": "0.10", "size": "50"}],
            "asks": asks,
        })

    monkeypatch.setattr(consistency.httpx, "get", fake_get)
    quote = consistency.live_quote_group(members, "buy_all_no")

    expected_fees = (
        (2 * 0.04 * 0.30 * 0.70 + 3 * 0.04 * 0.40 * 0.60) / 5
        + 0.04 * 0.20 * 0.80
    )
    assert quote["target_shares"] == 5
    assert quote["snapshot_atomic"] is False
    assert math.isclose(quote["live_notional_per_unit"], 0.56, abs_tol=1e-12)
    assert math.isclose(quote["live_fees"], expected_fees, abs_tol=1e-12)
    assert math.isclose(
        quote["live_capital_per_unit"], 0.56 + expected_fees, abs_tol=1e-12
    )
    assert math.isclose(
        quote["live_net_per_unit"], 1 - 0.56 - expected_fees, abs_tol=1e-12
    )


def test_live_quote_rejects_missing_authoritative_fee_schedule(monkeypatch) -> None:
    members, raw_by_id = _live_members()
    raw_by_id["71"]["feeSchedule"] = None

    def fake_get(url, **_kwargs):
        if "/markets/" in url:
            return _Response(raw_by_id[url.rsplit("/", 1)[1]])
        return _Response(_clob_info(
            _raw_for_condition(raw_by_id, url.rsplit("/", 1)[1])
        ))

    monkeypatch.setattr(consistency.httpx, "get", fake_get)
    monkeypatch.setattr(consistency.time, "sleep", lambda _seconds: None)

    quote = consistency.live_quote_group(members, "buy_all_no")

    assert "authoritative fee schedule missing" in quote["live_skipped"]


def test_live_quote_rejects_orderbook_identity_mismatch(monkeypatch) -> None:
    members, raw_by_id = _live_members()
    monkeypatch.setattr(consistency.time, "time", lambda: 1_000.0)

    def fake_get(url, *, params=None, timeout):
        del timeout
        if "/markets/" in url:
            return _Response(raw_by_id[url.rsplit("/", 1)[1]])
        if "/clob-markets/" in url:
            return _Response(_clob_info(
                _raw_for_condition(raw_by_id, url.rsplit("/", 1)[1])
            ))
        return _Response({
            "asset_id": params["token_id"],
            "market": "0x" + "f" * 64,
            "timestamp": "1000000",
            "min_order_size": "5",
            "tick_size": "0.01",
            "neg_risk": True,
            "hash": "hash",
            "bids": [],
            "asks": [{"price": "0.20", "size": "5"}],
        })

    monkeypatch.setattr(consistency.httpx, "get", fake_get)
    quote = consistency.live_quote_group(members, "buy_all_no")

    assert "condition identity mismatch" in quote["live_skipped"]


@pytest.mark.parametrize("neg_risk", [None, False, "true"])
def test_orderbook_requires_affirmative_neg_risk(monkeypatch, neg_risk) -> None:
    monkeypatch.setattr(consistency.time, "time", lambda: 1_000.0)
    monkeypatch.setattr(
        consistency.httpx,
        "get",
        lambda *_a, **_k: _Response({
            "asset_id": "123",
            "market": "0x" + "b" * 64,
            "timestamp": "1000000",
            "hash": "hash",
            "neg_risk": neg_risk,
            "min_order_size": "5",
            "tick_size": "0.01",
            "bids": [],
            "asks": [{"price": "0.20", "size": "5"}],
        }),
    )

    with pytest.raises(ValueError, match="neg-risk mismatch"):
        consistency._orderbook("123", "0x" + "b" * 64, 5, 0.01)


def test_live_quote_rejects_adapter_drift(monkeypatch) -> None:
    members, raw_by_id = _live_members()
    raw_by_id["71"]["negRiskMarketID"] = "0x" + "f" * 64

    def fake_get(url, **_kwargs):
        if "/markets/" in url:
            return _Response(raw_by_id[url.rsplit("/", 1)[1]])
        return _Response(_clob_info(
            _raw_for_condition(raw_by_id, url.rsplit("/", 1)[1])
        ))

    monkeypatch.setattr(consistency.httpx, "get", fake_get)

    quote = consistency.live_quote_group(members, "buy_all_no")

    assert "adapter mismatch" in quote["live_skipped"]


def test_live_quote_rejects_gamma_clob_fee_mismatch(monkeypatch) -> None:
    members, raw_by_id = _live_members()

    def fake_get(url, **_kwargs):
        if "/markets/" in url:
            return _Response(raw_by_id[url.rsplit("/", 1)[1]])
        info = _clob_info(_raw_for_condition(raw_by_id, url.rsplit("/", 1)[1]))
        info["fd"]["r"] = 0.05
        return _Response(info)

    monkeypatch.setattr(consistency.httpx, "get", fake_get)

    quote = consistency.live_quote_group(members, "buy_all_no")

    assert "fee descriptor mismatch" in quote["live_skipped"]


def test_live_deadline_stops_after_overrunning_request(monkeypatch) -> None:
    members, raw_by_id = _live_members()
    clock = {"now": 0.0}
    calls = []

    def fake_get(url, **_kwargs):
        calls.append(url)
        clock["now"] = 2.0
        return _Response(raw_by_id[url.rsplit("/", 1)[1]])

    monkeypatch.setattr(consistency.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(consistency.httpx, "get", fake_get)

    quote = consistency.live_quote_group(
        members, "buy_all_no", deadline=1.0
    )

    assert "deadline exhausted" in quote["live_skipped"]
    assert len(calls) == 1


def test_conservative_fee_rounds_each_fill_bucket_up() -> None:
    market = {
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True},
    }

    assert consistency._conservative_fill_fee(market, 0.33, 1.234567) == 0.01092


def test_low_deviation_structural_group_is_relevant_and_marks_cap_incomplete() -> None:
    candidate = {
        "structural_free_arb": True,
        "members": 2,
        "deviation": 0.03,
        "live_status": "not_quoted",
    }
    relevant, requested, legs = consistency._plan_live_candidates(
        [candidate], max_groups=1, max_legs=1
    )
    coverage = {
        "cursor_exhausted": True,
        "invalid_neg_risk_events": 0,
        "stop_reason": None,
    }
    consistency._finalize_coverage(
        coverage, relevant, requested, live_legs=legs, budget_exhausted=False
    )

    assert relevant == [candidate]
    assert requested == []
    assert coverage["analysis_complete"] is False
    assert coverage["live_groups_unquoted"] == 1
    assert consistency._analysis_label(coverage).startswith("INCOMPLETE analysis")


def test_non_atomic_positive_quote_is_provisional_not_actionable() -> None:
    candidate = {
        "structural_free_arb": True,
        "quote_depth_validated": True,
        "live_net_edge_frac": 0.03,
        "snapshot_atomic": False,
        "actionable": True,
    }

    assert consistency._provisional_live_hits([candidate]) == [candidate]
    assert candidate["actionable"] is False
    assert candidate["requires_revalidation"] is True


def test_market_fee_uses_per_market_quadratic_curve() -> None:
    assert consistency._market_fee_buy({"takerBaseFee": None}, 0.50) == 0.0
    assert math.isclose(
        consistency._market_fee_buy({"takerBaseFee": 1000}, 0.50),
        0.0175,
        rel_tol=0,
        abs_tol=1e-12,
    )
    assert math.isclose(
        consistency._market_fee_buy({"takerBaseFee": 500}, 0.50),
        0.0125,
        rel_tol=0,
        abs_tol=1e-12,
    )


def test_basket_fee_is_additive_dollars_per_share_not_price_multiplied() -> None:
    legs = [
        ({"takerBaseFee": 1000}, 0.40),
        ({"takerBaseFee": 500}, 0.60),
        ({"takerBaseFee": None}, 0.25),
    ]
    expected = 0.07 * 0.40 * 0.60 + 0.05 * 0.60 * 0.40

    assert math.isclose(
        consistency._basket_fee_per_unit(legs),
        expected,
        rel_tol=0,
        abs_tol=1e-12,
    )
