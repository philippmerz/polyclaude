from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sys

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import discover_markets as scanner
import market_context_batches as batches

NOW = dt.datetime(2026, 10, 12, tzinfo=dt.timezone.utc)


def market(identifier, **updates):
    value = {
        "id": identifier, "question": "Will the event happen?", "slug": identifier,
        "description": "Exact criteria.", "acceptingOrders": True,
        "enableOrderBook": True, "closed": False, "archived": False,
        "liquidityNum": 1000, "volume24hr": 100,
        "spread": .02, "endDate": "2026-10-19T00:00:00Z",
        "outcomes": '["Yes", "No"]', "outcomePrices": '[".9", ".1"]',
        "feesEnabled": False, "orderMinSize": 5,
    }
    return {**value, **updates}


def shortlist(rows, **kwargs):
    return scanner.shortlist(
        rows, min_liq=500, min_vol24=20, max_spread=.05,
        horizon_days=370, hurdle_apy=.03, now=NOW, **kwargs,
    )


def test_hurdle_filter_precedes_top_and_does_not_lose_a_lower_volume_survivor():
    counts = {}
    result = shortlist([
        market("expensive", volume24hr=999, outcomePrices='[".999", ".001"]'),
        market("candidate"),
    ], top_n=1, clears_hurdle_only=True, coverage=counts)
    assert [row["id"] for row in result] == ["candidate"]
    assert counts["filter_rejections"] == {"win_assumed_hurdle": 1}
    assert counts["eligible_before_top"] == counts["selected"] == 1
    assert counts["top_omitted"] == 0
    assert counts["filter_accounting_complete"]


def test_drop_counts_reconcile_to_fetched_universe_and_top_zero_keeps_survivors():
    rows = [market("a"), market("b", volume24hr=90),
            market("lowliq", liquidityNum=1), market("lowvol", volume24hr=1),
            market("wide", spread=.10), market("closed", closed=True),
            market("nan", liquidityNum="NaN"), market("badspread", spread="garbage"),
            market("expired", endDate="2026-10-11T00:00:00Z"),
            market("late", endDate="2028-01-01T00:00:00Z"),
            market("badtime", endDate="invalid")]
    counts = {}
    result = shortlist(rows, top_n=1, coverage=counts)
    assert [row["id"] for row in result] == ["a"]
    assert counts["eligible_before_top"] == 2
    assert counts["top_omitted"] == 1
    assert sum(counts["filter_rejections"].values()) == 9
    assert counts["filter_accounting_complete"] and not counts["selection_complete"]
    assert len(shortlist(rows, top_n=0)) == 2
    with pytest.raises(ValueError):
        shortlist(rows, top_n=-1)


def fake_client(monkeypatch, pages):
    client_type = httpx.Client
    requested = []

    def handle(request):
        offset = int(request.url.params["offset"])
        requested.append(offset)
        content = pages[offset]
        return httpx.Response(content if isinstance(content, int) else 200,
                              json=None if isinstance(content, int) else content)

    monkeypatch.setattr(scanner.httpx, "Client", lambda **kwargs: client_type(
        **kwargs, transport=httpx.MockTransport(handle)))
    return requested


@pytest.mark.parametrize("endpoint", ["markets", "events"])
@pytest.mark.parametrize("termination,complete", [("short_page", True), ("empty_page", True),
                                                ("page_cap", False), ("api_offset_limit", False)])
def test_endpoint_coverage_distinguishes_caps_from_exhaustion(monkeypatch, endpoint,
                                                            termination, complete):
    row = market("1") if endpoint == "markets" else {"id": "e", "markets": [market("1")]}
    pages = {0: [row, row]}
    if termination == "short_page":
        pages[0] = [row]
    elif termination == "empty_page":
        pages[2] = []
    elif termination == "api_offset_limit":
        pages[2] = 422
    fake_client(monkeypatch, pages)
    coverage = {}
    fetch = scanner.fetch_active if endpoint == "markets" else scanner.fetch_active_via_events
    result = fetch(limit_per_page=2, max_pages=1 if termination == "page_cap" else 2,
                   coverage=coverage)
    assert len(result) == 1
    assert coverage["stop_reason"] == termination
    assert coverage["pagination_complete"] is complete
    assert coverage["fetched_market_rows"] == 1


def test_snapshot_preserves_coverage_and_minimum_is_in_shares(tmp_path):
    rows = shortlist([market("1")], top_n=0)
    assert rows[0]["min_order_shares"] == 5
    assert rows[0]["min_size_units"] == "shares"
    stats = {"fetch": {"pagination_complete": False, "stop_reason": "page_cap"}}
    path, metadata = scanner.write_snapshot(rows, scan_kind="review", params={},
                                           snapshot_dir=tmp_path, now=NOW, coverage=stats)
    assert json.loads(metadata.read_text())["coverage"] == stats
    assert json.loads(path.read_text()) == rows


def test_packets_expose_upstream_cap_without_confusing_integrity_with_coverage(tmp_path):
    rows = shortlist([market("1")], top_n=0)
    stats = {"fetch": {"pagination_complete": False, "stop_reason": "page_cap"},
             "filters": {"top_omitted": 42}}
    path, _ = scanner.write_snapshot(rows, scan_kind="review", params={},
                                     snapshot_dir=tmp_path, now=NOW, coverage=stats)
    payload = batches.build_payload(current_path=path, prior_path=None,
                                    scan_kind="review", batch_size=20)
    assert payload["source_integrity_verified"] is True
    assert payload["discovery_coverage"] == stats
    assert any("pagination is incomplete" in warning for warning in payload["warnings"])
    assert any("omitted 42" in warning for warning in payload["warnings"])
    output = batches.render_markdown(payload)
    assert "Minimum order size is in shares" in output
    assert "page_cap" in output


def test_selection_policy_change_invalidates_delta_comparison_without_losing_rows(tmp_path):
    params = {field: 1 for field in batches.BASE_COHORT_PARAMS}
    rows = shortlist([market("1")], top_n=0)
    prior, prior_meta = scanner.write_snapshot(rows, scan_kind="review", params=params,
                                             snapshot_dir=tmp_path, now=NOW)
    meta = json.loads(prior_meta.read_text())
    meta.pop("selection_policy")  # Legacy collector capped before carry filtering.
    prior_meta.write_text(json.dumps(meta))
    current, _ = scanner.write_snapshot(rows + shortlist([market("2")], top_n=0),
                                       scan_kind="review", params=params, snapshot_dir=tmp_path,
                                       now=NOW + dt.timedelta(hours=12))
    payload = batches.build_payload(current_path=current, prior_path=prior,
                                    scan_kind="review", batch_size=20)
    assert payload["source_integrity_verified"] is True
    assert payload["delta_comparison_verified"] is False
    assert payload["counts"]["current_markets"] == 2
    assert any("different selection policies" in warning for warning in payload["warnings"])
