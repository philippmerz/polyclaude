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
        "title": "Will Example Subject happen in 2026?",
        "prices": [0.5, 0.5],
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
        "title": "Will Example Subject happen in 2026?",
        "prices": [0.5, 0.5],
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
