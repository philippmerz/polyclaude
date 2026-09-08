import json
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import limitless_arb_scan as scan  # noqa: E402


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def _markets(start: int, count: int) -> list[dict]:
    return [
        {
            "id": str(i),
            "slug": f"market-{i}",
            "question": f"Will market {i} happen?",
            "active": True,
            "closed": False,
            "volume24hr": 1_000_000 - i,
            "outcomePrices": "[\"0.5\", \"0.5\"]",
            "outcomes": '["Yes", "No"]',
        }
        for i in range(start, start + count)
    ]


def test_keyset_fetch_stops_at_bound_and_labels_partial(monkeypatch) -> None:
    first = _markets(0, 100)
    second = _markets(100, 50)
    calls = []

    def fake_get(url, *, params, timeout):
        calls.append((url, dict(params), timeout))
        if len(calls) == 1:
            return _Response({"markets": first, "next_cursor": "page-2"})
        return _Response({"markets": second, "next_cursor": "page-3"})

    monkeypatch.setattr(scan.httpx, "get", fake_get)
    result = scan.fetch_polymarket_universe(max_markets=150)

    assert result.markets == first + second
    assert result.complete is False
    assert result.coverage == "bounded_partial"
    assert "BOUNDED PARTIAL" in result.coverage_label
    assert result.pages == 2
    assert calls[0][0].endswith("/markets/keyset")
    assert calls[0][1] == {
        "active": "true",
        "closed": "false",
        "limit": "100",
        "order": "volume24hr",
        "ascending": "false",
    }
    assert calls[1][1]["after_cursor"] == "page-2"
    assert calls[1][1]["limit"] == "50"
    assert all("offset" not in params for _, params, _ in calls)


def test_keyset_fetch_marks_exhausted_slice_complete(monkeypatch) -> None:
    records = _markets(10, 2)
    monkeypatch.setattr(
        scan.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({"markets": records}),
    )

    result = scan.fetch_polymarket_universe(max_markets=3000)

    assert result.markets == records
    assert result.complete is True
    assert result.coverage == "complete"
    assert "COMPLETE" in result.coverage_label


def test_keyset_fetch_retries_transient_failure(monkeypatch) -> None:
    calls = 0

    def flaky(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("transient disconnect")
        return _Response({"markets": _markets(1, 1)})

    monkeypatch.setattr(scan.httpx, "get", flaky)
    monkeypatch.setattr(scan.time, "sleep", lambda _seconds: None)

    result = scan.fetch_polymarket_universe(max_markets=10)

    assert [market["id"] for market in result.markets] == ["1"]
    assert calls == 2


def test_keyset_fetch_fails_closed_after_later_page_failure(monkeypatch) -> None:
    calls = 0

    def first_then_fail(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return _Response({
                "markets": _markets(0, 100),
                "next_cursor": "page-2",
            })
        raise OSError("page two unavailable")

    monkeypatch.setattr(scan.httpx, "get", first_then_fail)
    monkeypatch.setattr(scan.time, "sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError, match="refusing partial coverage"):
        scan.fetch_polymarket_universe(max_markets=150)
    assert calls == 1 + scan.POLYMARKET_PAGE_RETRIES


def test_keyset_fetch_rejects_repeated_cursor(monkeypatch) -> None:
    calls = 0

    def repeated(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return _Response({
            "markets": _markets(calls, 1),
            "next_cursor": "stuck",
        })

    monkeypatch.setattr(scan.httpx, "get", repeated)

    with pytest.raises(RuntimeError, match="repeated a cursor"):
        scan.fetch_polymarket_universe(max_markets=3)


def test_keyset_fetch_rejects_duplicate_market_identity(monkeypatch) -> None:
    pages = iter([
        {"markets": _markets(7, 1), "next_cursor": "page-2"},
        {"markets": _markets(7, 1)},
    ])
    monkeypatch.setattr(
        scan.httpx,
        "get",
        lambda *_args, **_kwargs: _Response(next(pages)),
    )

    with pytest.raises(RuntimeError, match="repeated market id"):
        scan.fetch_polymarket_universe(max_markets=2)


@pytest.mark.parametrize("closed", [None, "false", True])
def test_keyset_fetch_requires_affirmative_open_state(monkeypatch, closed) -> None:
    records = _markets(10, 1)
    records[0]["closed"] = closed
    monkeypatch.setattr(
        scan.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({"markets": records}),
    )

    with pytest.raises(RuntimeError, match="violated active/open filters"):
        scan.fetch_polymarket_universe(max_markets=1)


def test_keyset_fetch_rejects_ranking_violation(monkeypatch) -> None:
    records = _markets(10, 2)
    records[0]["volume24hr"] = 1
    records[1]["volume24hr"] = 2
    monkeypatch.setattr(
        scan.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({"markets": records}),
    )

    with pytest.raises(RuntimeError, match="violated requested volume24hr ordering"):
        scan.fetch_polymarket_universe(max_markets=2)


def test_main_persists_explicit_partial_coverage_label(
    monkeypatch, tmp_path, capsys,
) -> None:
    candidate = {
        "id": "lim-1",
        "slug": "example-subject-2026",
        "title": "Will Example Subject happen in 2026?",
        "prices": [0.5, 0.5],
        "tokens": {"yes": "lim-yes-1", "no": "lim-no-1"},
        "metadata": {},
    }
    partial = scan.PolymarketUniverseFetch(
        markets=[],
        max_markets=scan.POLYMARKET_UNIVERSE_LIMIT,
        pages=30,
        complete=False,
    )
    monkeypatch.setattr(scan, "OUT_DIR", tmp_path)
    monkeypatch.setattr(scan, "fetch_arb_candidates", lambda: [candidate])
    monkeypatch.setattr(scan, "fetch_polymarket_universe", lambda **_kwargs: partial)
    monkeypatch.setattr(sys, "argv", ["limitless_arb_scan.py"])

    assert scan.main() == 0

    stdout = capsys.readouterr().out
    assert "coverage: BOUNDED PARTIAL" in stdout
    report = next(tmp_path.glob("limitless_arb_*.md")).read_text()
    assert "Polymarket universe coverage: **BOUNDED PARTIAL" in report
    payload = json.loads((tmp_path / "limitless_arb_latest.json").read_text())
    assert payload["polymarket_universe"]["coverage"] == "bounded_partial"
    assert payload["polymarket_universe"]["markets_returned"] == 0
    assert payload["polymarket_universe"]["max_markets"] == 3000


def test_main_aborts_without_publishing_on_keyset_failure(
    monkeypatch, tmp_path, capsys,
) -> None:
    candidate = {
        "id": "lim-1",
        "slug": "example-subject-2026",
        "title": "Will Example Subject happen in 2026?",
        "prices": [0.5, 0.5],
        "tokens": {"yes": "lim-yes-1", "no": "lim-no-1"},
        "metadata": {},
    }
    monkeypatch.setattr(scan, "OUT_DIR", tmp_path)
    monkeypatch.setattr(scan, "fetch_arb_candidates", lambda: [candidate])

    def fail(**_kwargs):
        raise RuntimeError("page two unavailable; refusing partial coverage")

    monkeypatch.setattr(scan, "fetch_polymarket_universe", fail)
    monkeypatch.setattr(sys, "argv", ["limitless_arb_scan.py"])

    assert scan.main() == 2

    captured = capsys.readouterr()
    assert "ABORT: Polymarket universe unavailable" in captured.err
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_keyset_fetch_requires_positive_integer_bound(value) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        scan.fetch_polymarket_universe(max_markets=value)


def test_flagged_groups_expand_to_priced_leaf_contracts(monkeypatch) -> None:
    parent = {
        "id": "parent-1",
        "slug": "parent-event",
        "title": "Will Example Subject happen?",
        "description": "Parent event rule.",
        "metadata": {
            "isPolyArbitrage": True,
            "chainlinkDataStream": {"enabled": True},
        },
        "marketType": "group",
        "prices": None,
        "tokens": None,
        "children": [
            {
                "id": "child-1",
                "slug": "example-subject-yes",
                "title": "Example Subject by 2026?",
                "description": "Child-specific deadline rule.",
                "marketType": "group",
                "prices": ["0.62", "0.38"],
                "tokens": {"yes": "token-1-yes", "no": "token-1-no"},
                "metadata": {},
            },
            {
                "id": "child-bad",
                "slug": "example-subject-bad",
                "title": "Bad child",
                "prices": None,
                "tokens": None,
            },
        ],
    }
    monkeypatch.setattr(
        scan.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({
            "data": [parent],
            "totalMarketsCount": 1,
        }),
    )

    result = scan.fetch_arb_candidates()

    assert [market["id"] for market in result] == ["child-1"]
    assert result[0]["slug"] == "example-subject-yes"
    assert result[0]["prices"] == [0.62, 0.38]
    assert result[0]["tokens"] == {"yes": "token-1-yes", "no": "token-1-no"}
    assert "Will Example Subject happen?" in result[0]["_match_title"]
    assert "Example Subject by 2026?" in result[0]["_match_title"]
    assert "Parent event rule." in result[0]["_match_description"]
    assert "Child-specific deadline rule." in result[0]["_match_description"]
    assert result[0]["metadata"] == {"isPolyArbitrage": True}
    assert scan.LAST_ARB_NORMALIZATION_STATS["expanded_children"] == 2
    assert scan.LAST_ARB_NORMALIZATION_STATS["eligible_leaves"] == 1
    assert scan.LAST_ARB_NORMALIZATION_STATS["excluded"] == 1


def _flagged_leaf(leaf_id: str = "leaf-1", slug: str = "leaf-slug",
                  tokens: dict[str, str] | None = None) -> dict:
    return {
        "id": leaf_id,
        "slug": slug,
        "title": "Will Example Subject happen?",
        "prices": [0.4, 0.6],
        "tokens": tokens or {"yes": "yes-token", "no": "no-token"},
    }


def _flagged_parent(leaf: dict) -> dict:
    return {
        "id": f"parent-{leaf['id']}",
        "slug": f"parent-{leaf['slug']}",
        "title": "Example parent",
        "metadata": {"isPolyArbitrage": True},
        "children": [leaf],
    }


def test_active_fetch_requests_explicit_limit_and_fails_closed_on_page_error(monkeypatch) -> None:
    calls = []

    def fail_on_page(_url, *, params, timeout):
        calls.append((params, timeout))
        raise OSError("offline")

    monkeypatch.setattr(scan.httpx, "get", fail_on_page)

    with pytest.raises(RuntimeError, match="refusing partial coverage"):
        scan.fetch_arb_candidates()
    assert calls == [({"page": 1, "limit": 25}, 15)]


def test_active_fetch_fails_closed_on_later_page_error(monkeypatch) -> None:
    calls = 0

    def first_then_fail(_url, *, params, timeout):
        nonlocal calls
        calls += 1
        assert params["limit"] == 25
        if calls == 1:
            return _Response({"data": [{}] * 25, "totalMarketsCount": 26})
        raise OSError("offline")

    monkeypatch.setattr(scan.httpx, "get", first_then_fail)

    with pytest.raises(RuntimeError, match="refusing partial coverage"):
        scan.fetch_arb_candidates()
    assert calls == 2


def test_active_fetch_fails_closed_on_unknown_or_early_empty_total(monkeypatch) -> None:
    monkeypatch.setattr(
        scan.httpx, "get",
        lambda *_args, **_kwargs: _Response({"data": [], "totalMarketsCount": None}),
    )
    with pytest.raises(RuntimeError, match="valid totalMarketsCount"):
        scan.fetch_arb_candidates()

    monkeypatch.setattr(
        scan.httpx, "get",
        lambda *_args, **_kwargs: _Response({"data": [], "totalMarketsCount": 1}),
    )
    with pytest.raises(RuntimeError, match="empty before totalMarketsCount"):
        scan.fetch_arb_candidates()


def test_active_fetch_aborts_at_page_cap_instead_of_publishing_partial(monkeypatch) -> None:
    monkeypatch.setattr(scan, "LIMITLESS_ACTIVE_PAGE_CAP", 1)
    monkeypatch.setattr(
        scan.httpx, "get",
        lambda *_args, **_kwargs: _Response({
            "data": [{}] * 25,
            "totalMarketsCount": 26,
        }),
    )

    with pytest.raises(RuntimeError, match="safety cap"):
        scan.fetch_arb_candidates()


def test_exact_duplicate_leaf_is_emitted_once() -> None:
    leaf = _flagged_leaf()

    result = scan._normalise_arb_markets([
        _flagged_parent(dict(leaf)),
        _flagged_parent(dict(leaf)),
    ])

    assert [market["id"] for market in result] == ["leaf-1"]
    assert scan.LAST_ARB_NORMALIZATION_STATS["excluded"] == 1


@pytest.mark.parametrize("mutation", ["slug", "tokens"])
def test_conflicting_leaf_identity_aborts_normalization(mutation) -> None:
    first = _flagged_leaf()
    second = _flagged_leaf()
    if mutation == "slug":
        second["slug"] = "different-slug"
    else:
        second["tokens"] = {"yes": "other-yes", "no": "other-no"}

    with pytest.raises(RuntimeError, match="conflicting identity"):
        scan._normalise_arb_markets([
            _flagged_parent(first),
            _flagged_parent(second),
        ])


def test_main_returns_two_and_does_not_publish_on_limitless_fetch_failure(
    monkeypatch, tmp_path, capsys,
) -> None:
    monkeypatch.setattr(scan, "OUT_DIR", tmp_path)
    stale = tmp_path / "limitless_arb_latest.json"
    stale.write_text(json.dumps({"verified_identical": [{"lim_id": "stale"}]}))
    monkeypatch.setattr(
        scan, "fetch_arb_candidates",
        lambda: (_ for _ in ()).throw(RuntimeError("refusing partial coverage")),
    )
    monkeypatch.setattr(sys, "argv", ["limitless_arb_scan.py"])

    assert scan.main() == 2
    assert json.loads(stale.read_text())["verified_identical"][0]["lim_id"] == "stale"
    assert "ABORT: Limitless universe unavailable" in capsys.readouterr().err


def test_leaf_normalization_rejects_fake_midpoint_and_duplicate_tokens(monkeypatch) -> None:
    parent = {
        "id": "parent-2",
        "slug": "parent-event-2",
        "title": "Will Another Subject happen?",
        "metadata": {"isPolyArbitrage": True},
        "children": [
            {
                "id": "child-no-price",
                "slug": "another-subject-no-price",
                "title": "Another Subject?",
                "prices": None,
                "tokens": {"yes": "yes", "no": "no"},
            },
            {
                "id": "child-same-token",
                "slug": "another-subject-same-token",
                "title": "Another Subject?",
                "prices": [0.4, 0.6],
                "tokens": {"yes": "same", "no": "same"},
            },
        ],
    }
    monkeypatch.setattr(
        scan.httpx,
        "get",
        lambda *_args, **_kwargs: _Response({"data": [parent], "totalMarketsCount": 1}),
    )

    result = scan.fetch_arb_candidates()

    assert result == []
    assert scan.LAST_ARB_NORMALIZATION_STATS["excluded"] == 2
    assert scan.LAST_ARB_NORMALIZATION_STATS["exclusions"] == {
        "missing_or_malformed_prices": 1,
        "missing_or_duplicate_tokens": 1,
    }


def test_main_overwrites_latest_json_when_no_eligible_leaves(
    monkeypatch, tmp_path, capsys,
) -> None:
    monkeypatch.setattr(scan, "OUT_DIR", tmp_path)
    (tmp_path / "limitless_arb_latest.json").write_text(json.dumps({
        "verified_identical": [{"lim_id": "stale"}],
        "verified_other": [{"lim_id": "stale"}],
    }))
    monkeypatch.setattr(scan, "fetch_arb_candidates", lambda: [])
    monkeypatch.setattr(sys, "argv", ["limitless_arb_scan.py"])

    assert scan.main() == 0

    payload = json.loads((tmp_path / "limitless_arb_latest.json").read_text())
    assert payload["total_candidates"] == 0
    assert payload["verified_identical"] == []
    assert payload["verified_other"] == []
    assert "wrote" in capsys.readouterr().out
