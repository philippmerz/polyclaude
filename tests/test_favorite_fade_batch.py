from __future__ import annotations

import sys
import json
import pytest
import httpx
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import favorite_fade_scan as scanner  # noqa: E402


def complete_fetch(rows):
    return scanner.MarketFetchResult(rows, {
        "complete": True, "pages_attempted": 1, "pages_succeeded": 1,
        "failures": [], "stop_reason": "valid_short_page", "command_failed": False,
    })


def test_validated_book_rejects_missing_or_crossed():
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    assert scanner._validated_book(None, "a", "condition") is None
    assert scanner._validated_book({"asset_id": "a", "market": "condition", "timestamp": now,
                                    "asks": [{"price": ".4", "size": "1"}],
                                    "bids": [{"price": ".5", "size": "1"}]},
                                   "a", "condition") is None


def test_validated_book_returns_sorted_quote_data():
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    book = scanner._validated_book({"asset_id": "a", "market": "condition", "timestamp": now,
                                    "asks": [{"price": ".5", "size": "2"},
                                              {"price": ".4", "size": "1"}],
                                    "bids": [{"price": ".3", "size": "2"}]},
                                   "a", "condition")
    assert book["asks"] == [(0.5, 2.0), (0.4, 1.0)]


def test_validated_book_rejects_wrong_condition_and_nonfinite_size():
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    base = {"asset_id": "a", "market": "other", "timestamp": now,
            "asks": [{"price": ".4", "size": "1"}], "bids": []}
    assert scanner._validated_book(base, "a", "condition") is None
    base["market"] = "condition"
    base["asks"][0]["size"] = "NaN"
    assert scanner._validated_book(base, "a", "condition") is None


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def response(status, payload=None, *, content=None):
    request = httpx.Request("GET", scanner.GAMMA)
    if content is not None:
        return httpx.Response(status, content=content, request=request)
    return httpx.Response(status, json=payload, request=request)


def test_fetch_active_retries_status_and_malformed_schema_then_completes_on_short_page():
    client = FakeClient([
        response(503, []),
        response(200, {"unexpected": "schema"}),
        response(200, [{"id": "one"}]),
    ])
    result = scanner.fetch_active(3, client)
    assert result == [{"id": "one"}]
    assert result.coverage["complete"] is True
    assert result.coverage["stop_reason"] == "valid_short_page"
    assert result.coverage["command_failed"] is False
    assert result.coverage["pages_attempted"] == 3
    assert result.coverage["pages_succeeded"] == 1
    assert [f["reason"] for f in result.coverage["failures"]] == [
        "http_status_error", "invalid_json_or_schema",
    ]


def test_fetch_active_reports_page_cap_and_422_as_incomplete():
    full_page = [{"id": str(i)} for i in range(100)]
    capped = scanner.fetch_active(1, FakeClient([response(200, full_page)]))
    assert len(capped) == 100
    assert capped.coverage["complete"] is False
    assert capped.coverage["stop_reason"] == "max_pages"
    assert capped.coverage["pages_attempted"] == 1
    assert capped.coverage["pages_succeeded"] == 1

    too_far_client = FakeClient([response(422, {"error": "offset limit"})])
    too_far = scanner.fetch_active(3, too_far_client)
    assert too_far == []
    assert too_far.coverage["complete"] is False
    assert too_far.coverage["stop_reason"] == "http_422_offset_or_page_limit"
    assert too_far.coverage["pages_attempted"] == 1
    assert too_far.coverage["pages_succeeded"] == 0


def test_fetch_active_retry_exhaustion_preserves_rows_but_not_complete():
    page = [{"id": str(i)} for i in range(100)]
    client = FakeClient([response(200, page), *[response(503, []) for _ in range(5)]])
    result = scanner.fetch_active(3, client)
    assert len(result) == 100
    assert result.coverage["complete"] is False
    assert result.coverage["stop_reason"] == "retry_budget_exhausted"
    assert result.coverage["command_failed"] is True
    assert result.coverage["pages_attempted"] == 6
    assert result.coverage["pages_succeeded"] == 1
    assert len(result.coverage["failures"]) == 5

    malformed = scanner.fetch_active(
        1, FakeClient([response(200, {"not": "a market list"}) for _ in range(5)]),
    )
    assert malformed == []
    assert malformed.coverage["complete"] is False
    assert malformed.coverage["stop_reason"] == "retry_budget_exhausted"
    assert malformed.coverage["pages_succeeded"] == 0
    assert len(malformed.coverage["failures"]) == 5


def test_main_incomplete_fetch_is_nonzero_but_retains_candidate_json(monkeypatch, capsys):
    end = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    market = {
        "id": "plain-list-market", "slug": "plain", "conditionId": "plain-condition",
        "question": "Plain list candidate?", "outcomes": '["Yes", "No"]',
        "outcomePrices": '[0.95, 0.05]', "endDate": end, "liquidity": 50_000,
        "volume24hr": 1000, "clobTokenIds": '["plain-y", "plain-n"]',
        "umaResolutionStatus": "", "active": True, "closed": False,
        "acceptingOrders": True, "enableOrderBook": True, "archived": False,
    }
    monkeypatch.setattr(sys, "argv", ["favorite_fade_scan.py", "--json"])
    monkeypatch.setattr(scanner, "fetch_books", lambda *_args, **_kwargs: {
        "plain-y": {
            "asset_id": "plain-y", "market": "plain-condition",
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
            "asks": [{"price": ".95", "size": "100"}],
            "bids": [{"price": ".94", "size": "100"}],
        },
    })
    partial = scanner.MarketFetchResult([market], {
        "complete": False, "pages_attempted": 6, "pages_succeeded": 1,
        "failures": [{"offset": 100, "reason": "http_status_error"}],
        "stop_reason": "retry_budget_exhausted",
    })
    for fetched, expected_reason in (
        (partial, "retry_budget_exhausted"), ([market], "legacy_list_without_coverage"),
    ):
        monkeypatch.setattr(scanner, "fetch_active", lambda *_args, **_kwargs: fetched)
        assert scanner.main() == 0
        captured = capsys.readouterr()
        rows = json.loads(captured.out)
        assert [row["market_id"] for row in rows] == ["plain-list-market"]
        coverage_line = next(
            line for line in captured.err.splitlines()
            if line.startswith("SCAN_COVERAGE ")
        )
        coverage = json.loads(coverage_line.removeprefix("SCAN_COVERAGE "))
        assert coverage["market_fetch"]["complete"] is False
        assert coverage["market_fetch"]["stop_reason"] == expected_reason
        assert coverage["rough_survivors_before_book_cap"] == 1
        assert coverage["selected_for_book_walk"] == 1
        assert coverage["valid_favorite_books"] == 1
        assert coverage["candidate_rows_emitted"] == 1
def test_main_ignores_legacy_edge_floor_and_emits_candidate_context(monkeypatch, capsys):
    end = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    market = {
        "outcomes": '["Yes", "No"]', "outcomePrices": '[0.95, 0.05]',
        "endDate": end, "liquidity": 50_000, "volume24hr": 10_000,
        "clobTokenIds": '["yes-token", "no-token"]',
        "conditionId": "condition", "id": "42", "slug": "president-remain",
        "question": "Will the president remain?",
        "umaResolutionStatus": "", "active": True, "closed": False,
        "acceptingOrders": True, "enableOrderBook": True, "archived": False,
    }
    no_favorite_market = {
        **market,
        "id": "43", "slug": "president-out",
        "question": "Will the president leave?",
        "outcomePrices": '[0.05, 0.95]',
        "clobTokenIds": '["yes-token-2", "no-token-2"]',
    }
    requested = []

    monkeypatch.setattr(
        scanner, "fetch_active",
        lambda *_args, **_kwargs: complete_fetch([market, no_favorite_market]),
    )
    monkeypatch.setattr(
        scanner, "fetch_books",
        lambda tokens, **_kwargs: requested.append(list(tokens)) or {
            token: {
                "asset_id": token, "market": "condition",
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "asks": [{"price": ask, "size": "100"}],
                "bids": [{"price": bid, "size": "100"}],
            }
            for token, ask, bid in (
                ("yes-token", ".95", ".94"),
                ("yes-token-2", ".06", ".05"), ("no-token-2", ".95", ".94"),
            )
        },
    )

    outputs = []
    warnings = []
    for legacy_floor in ("0", "999"):
        monkeypatch.setattr(
            sys, "argv", ["favorite_fade_scan.py", "--min-edge-pp", legacy_floor, "--json"],
        )
        assert scanner.main() == 0
        captured = capsys.readouterr()
        outputs.append(json.loads(captured.out))
        warnings.append(captured.err)
    expected_tokens = ["yes-token", "no-token", "yes-token-2", "no-token-2"]
    assert requested == [expected_tokens, expected_tokens]
    assert len(outputs[0]) == len(outputs[1])
    assert {r["market_id"] for r in outputs[0]} == {r["market_id"] for r in outputs[1]}
    for left, right in zip(outputs[0], outputs[1]):
        assert {k: v for k, v in left.items() if k != "days"} == {
            k: v for k, v in right.items() if k != "days"
        }
    assert len(outputs[0]) == 2
    rows = {row["market_id"]: row for row in outputs[0]}
    row = rows["42"]
    assert row["market_id"] == "42"
    assert row["slug"] == "president-remain"
    assert row["condition_id"] == "condition"
    assert row["tokens"] == {"YES": "yes-token", "NO": "no-token"}
    assert row["selected_side"] == "YES"
    assert row["selected_token_id"] == "yes-token"
    assert row["selected_ask"] == 0.95
    assert row["opposite_side"] == {
        "side": "NO", "token_id": "no-token", "gamma_price": 0.05,
        "book_validated": False, "best_ask": None, "best_bid": None,
    }
    assert row["candidate_only"] is True
    assert row["execution_ready"] is False
    assert row["live_rewalk_required"] is True
    assert not {"exp_winrate", "edge_pp", "apy_pct"} & row.keys()
    no_row = rows["43"]
    assert no_row["selected_side"] == "NO"
    assert no_row["selected_token_id"] == "no-token-2"
    assert no_row["opposite_side"]["side"] == "YES"
    assert no_row["opposite_side"]["token_id"] == "yes-token-2"
    assert no_row["opposite_side"]["book_validated"] is True
    assert all("ignored" in warning for warning in warnings)


def test_main_requires_explicit_new_entry_eligibility_and_valid_gamma_fields(monkeypatch, capsys):
    end = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    base = {
        "outcomes": '["Yes", "No"]', "outcomePrices": '[0.95, 0.05]',
        "endDate": end, "liquidity": 50_000, "volume24hr": 10_000,
        "clobTokenIds": '["yes-token", "no-token"]',
        "conditionId": "condition", "slug": "candidate", "question": "Candidate?",
        "umaResolutionStatus": "", "active": True, "closed": False,
        "acceptingOrders": True, "enableOrderBook": True, "archived": False,
    }
    invalid = [
        {**base, "id": "proposed", "umaResolutionStatus": "proposed"},
        {**base, "id": "disputed", "umaResolutionStatus": "disputed"},
        {**base, "id": "resolved", "umaResolutionStatus": "resolved"},
        {**base, "id": "closed", "closed": True},
        {**base, "id": "not-accepting", "acceptingOrders": False},
        {**base, "id": "no-orderbook", "enableOrderBook": None},
        {**base, "id": "unknown-active", "active": None},
        {**base, "id": "unknown-archive", "archived": None},
        {**base, "id": "bad-prices", "outcomePrices": "not-json"},
        {**base, "id": "bad-number", "outcomePrices": '[NaN, 0.05]'},
        {**base, "id": "bad-outcomes", "outcomes": "not-json"},
        {**base, "id": "bad-liquidity", "liquidity": "NaN"},
        {**base, "id": "missing-id", "id": None},
        {**base, "id": "missing-slug", "slug": ""},
        {**base, "id": "missing-condition", "conditionId": ""},
        {**base, "id": "bad-tokens", "clobTokenIds": "[null, 'no']"},
        {**base, "id": "duplicate-tokens", "clobTokenIds": '["same", "same"]'},
    ]
    valid = {**base, "id": "valid"}
    monkeypatch.setattr(
        scanner, "fetch_active",
        lambda *_args, **_kwargs: complete_fetch([*invalid, valid]),
    )
    requested = []

    def fake_books(tokens, **_kwargs):
        requested.append(list(tokens))
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        return {
            "yes-token": {
                "asset_id": "yes-token", "market": "condition", "timestamp": now_ms,
                "asks": [{"price": ".95", "size": "100"}],
                "bids": [{"price": ".94", "size": "100"}],
            },
            "no-token": {
                "asset_id": "no-token", "market": "condition", "timestamp": now_ms,
                "asks": [{"price": ".06", "size": "100"}],
                "bids": [{"price": ".05", "size": "100"}],
            },
        }

    monkeypatch.setattr(scanner, "fetch_books", fake_books)
    monkeypatch.setattr(sys, "argv", ["favorite_fade_scan.py", "--json"])
    assert scanner.main() == 0
    rows = json.loads(capsys.readouterr().out)
    assert requested == [["yes-token", "no-token"]]
    assert [r["market_id"] for r in rows] == ["valid"]


def test_main_orders_by_deadline_then_liquidity(monkeypatch, capsys):
    now = datetime.now(timezone.utc)
    near_end = (now + timedelta(days=3)).isoformat()
    far_end = (now + timedelta(days=6)).isoformat()

    def market(mid, slug, end, liquidity, yes, tokens):
        return {
            "id": mid, "slug": slug, "conditionId": f"condition-{mid}",
            "question": f"Market {mid}?", "outcomes": '["Yes", "No"]',
            "outcomePrices": f"[{yes}, {1-yes}]", "endDate": end,
            "liquidity": liquidity, "volume24hr": 1000,
            "clobTokenIds": json.dumps(tokens), "umaResolutionStatus": "",
            "active": True, "closed": False, "acceptingOrders": True,
            "enableOrderBook": True, "archived": False,
        }

    mkts = [
        market("lowliq-near", "a", near_end, 25_000, 0.95, ["a-y", "a-n"]),
        market("highliq-near", "b", near_end, 50_000, 0.95, ["b-y", "b-n"]),
        market("highliq-far", "c", far_end, 80_000, 0.95, ["c-y", "c-n"]),
    ]
    monkeypatch.setattr(scanner, "fetch_active", lambda *_args, **_kwargs: complete_fetch(mkts))

    def fake_books(tokens, **_kwargs):
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        return {
            token: {
                "asset_id": token,
                "market": next(m["conditionId"] for m in mkts if token in m["clobTokenIds"]),
                "timestamp": now_ms,
                "asks": [{"price": ".95" if token.endswith("y") else ".06", "size": "100"}],
                "bids": [{"price": ".94" if token.endswith("y") else ".05", "size": "100"}],
            }
            for token in tokens
        }

    monkeypatch.setattr(scanner, "fetch_books", fake_books)
    monkeypatch.setattr(sys, "argv", ["favorite_fade_scan.py", "--json"])
    assert scanner.main() == 0
    rows = json.loads(capsys.readouterr().out)
    assert [r["market_id"] for r in rows] == ["highliq-near", "lowliq-near", "highliq-far"]


def _candidate_market():
    end = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    return {
        "id": "candidate", "slug": "candidate", "conditionId": "candidate-condition",
        "question": "Candidate?", "outcomes": '["Yes", "No"]',
        "outcomePrices": '[0.95, 0.05]', "endDate": end, "liquidity": 50_000,
        "volume24hr": 1000, "clobTokenIds": '["candidate-y", "candidate-n"]',
        "umaResolutionStatus": "", "active": True, "closed": False,
        "acceptingOrders": True, "enableOrderBook": True, "archived": False,
    }


def _candidate_books():
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    return {
        "candidate-y": {
            "asset_id": "candidate-y", "market": "candidate-condition",
            "timestamp": now_ms, "asks": [{"price": ".95", "size": "100"}],
            "bids": [{"price": ".94", "size": "100"}],
        },
    }


def test_main_intentional_page_cap_exits_zero_but_reports_incomplete(
    monkeypatch, capsys,
):
    page = [_candidate_market()] + [{"id": str(i)} for i in range(99)]
    client = FakeClient([response(200, page)])
    monkeypatch.setattr(scanner.httpx, "Client", lambda: client)
    monkeypatch.setattr(scanner, "fetch_books", lambda *_args, **_kwargs: _candidate_books())
    monkeypatch.setattr(
        sys, "argv", ["favorite_fade_scan.py", "--max-pages", "1", "--json"],
    )
    assert scanner.main() == 0
    captured = capsys.readouterr()
    assert [r["market_id"] for r in json.loads(captured.out)] == ["candidate"]
    coverage_line = next(
        line for line in captured.err.splitlines() if line.startswith("SCAN_COVERAGE ")
    )
    coverage = json.loads(coverage_line.removeprefix("SCAN_COVERAGE "))
    assert coverage["market_fetch"]["complete"] is False
    assert coverage["market_fetch"]["command_failed"] is False
    assert coverage["market_fetch"]["stop_reason"] == "max_pages"
    assert coverage["candidate_rows_emitted"] == 1


def test_main_retry_exhaustion_exits_nonzero_but_keeps_partial_candidate(
    monkeypatch, capsys,
):
    page = [_candidate_market()] + [{"id": str(i)} for i in range(99)]
    client = FakeClient([response(200, page), *[response(503, []) for _ in range(5)]])
    monkeypatch.setattr(scanner.httpx, "Client", lambda: client)
    monkeypatch.setattr(scanner, "fetch_books", lambda *_args, **_kwargs: _candidate_books())
    monkeypatch.setattr(sys, "argv", ["favorite_fade_scan.py", "--max-pages", "3", "--json"])
    assert scanner.main() == 1
    captured = capsys.readouterr()
    assert [r["market_id"] for r in json.loads(captured.out)] == ["candidate"]
    coverage_line = next(
        line for line in captured.err.splitlines() if line.startswith("SCAN_COVERAGE ")
    )
    coverage = json.loads(coverage_line.removeprefix("SCAN_COVERAGE "))
    assert coverage["market_fetch"]["complete"] is False
    assert coverage["market_fetch"]["command_failed"] is True
    assert coverage["market_fetch"]["stop_reason"] == "retry_budget_exhausted"
    assert coverage["market_fetch"]["pages_succeeded"] == 1
    assert coverage["candidate_rows_emitted"] == 1
