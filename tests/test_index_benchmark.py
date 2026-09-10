from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import index_benchmark as benchmark  # noqa: E402


NOW_DURING_SESSION = datetime(2026, 9, 10, 18, 0, tzinfo=timezone.utc)


def _timestamp(day: date) -> int:
    # NYSE daily bars are stamped at 09:30 EDT (13:30 UTC) in this period.
    return int(datetime.combine(day, time(13, 30), tzinfo=timezone.utc).timestamp())


def _payload(ticker: str, rows: list[tuple[date, float | None]]) -> dict:
    return {
        "chart": {
            "error": None,
            "result": [{
                "meta": {
                    "symbol": ticker,
                    "currency": "USD",
                    "instrumentType": "ETF",
                    "exchangeTimezoneName": "America/New_York",
                    "currentTradingPeriod": {
                        "regular": {
                            "start": _timestamp(date(2026, 9, 10)),
                            "end": int(datetime(2026, 9, 10, 20, 0, tzinfo=timezone.utc).timestamp()),
                        }
                    },
                },
                "timestamp": [_timestamp(day) for day, _close in rows],
                "indicators": {
                    "quote": [{"close": [close for _day, close in rows]}],
                    "adjclose": [{"adjclose": [close for _day, close in rows]}],
                },
            }],
        }
    }


def _one_fund_policy() -> benchmark.Policy:
    policy = benchmark.load_policy()
    return replace(policy, funds=(policy.funds[0],))


class _Response:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _Client:
    def __init__(self, payloads: dict[str, dict]):
        self.payloads = payloads
        self.urls: list[str] = []

    def get(self, url: str, **_kwargs) -> _Response:
        self.urls.append(url)
        ticker = url.split("/chart/", 1)[1].split("?", 1)[0]
        return _Response(self.payloads[ticker])


def test_default_policy_pins_real_cash_flows_and_broad_funds() -> None:
    policy = benchmark.load_policy()

    assert [(row.date.isoformat(), row.amount) for row in policy.contributions] == [
        ("2026-04-25", Decimal("70.00")),
        ("2026-04-29", Decimal("100.00")),
    ]
    assert policy.reference_capital == Decimal("170.00")
    assert [fund.ticker for fund in policy.funds] == ["VT", "VTI", "SPY"]
    assert policy.evaluation_start == date(2027, 1, 1)


def test_contributions_enter_strictly_after_dates_and_intraday_bar_is_excluded() -> None:
    policy = _one_fund_policy()
    payload = _payload("VT", [
        (date(2026, 4, 24), 90.0),
        (date(2026, 4, 27), 100.0),
        (date(2026, 4, 29), 110.0),
        (date(2026, 4, 30), 125.0),
        (date(2026, 9, 9), 150.0),
        (date(2026, 9, 10), 999.0),  # current, incomplete session: must be ignored
    ])
    client = _Client({"VT": payload})

    report = benchmark.build_report(
        policy,
        date(2026, 9, 10),
        NOW_DURING_SESSION,
        client,
    )
    row = report["benchmarks"][0]

    assert [lot["entry_session"] for lot in row["lots"]] == ["2026-04-27", "2026-04-30"]
    assert row["valuation_session"] == "2026-09-09"
    assert row["valuation_adjusted_close"] == Decimal("150.0")
    # 70/100 + 100/125 = 1.5 fractional shares; value is therefore $225.
    assert [lot["initial_fractional_shares"] for lot in row["lots"]] == [
        Decimal("0.7"),
        Decimal("0.8"),
    ]
    assert row["value"] == Decimal("225.00")
    assert row["gain"] == Decimal("55.00")
    assert row["return_pct"] == pytest.approx(Decimal("32.35294117647058823529411765"))
    assert "includeAdjustedClose=true" in client.urls[0]


def test_current_bar_is_accepted_only_after_regular_session_close() -> None:
    payload = _payload("VT", [
        (date(2026, 4, 27), 100.0),
        (date(2026, 4, 30), 125.0),
        (date(2026, 9, 10), 160.0),
    ])
    now_after_close = datetime(2026, 9, 10, 20, 5, tzinfo=timezone.utc)

    series = benchmark.parse_chart_payload(
        payload,
        "VT",
        date(2026, 9, 10),
        now_after_close,
        "https://example.test/VT",
    )

    assert series.bars[-1] == benchmark.PriceBar(
        date(2026, 9, 10),
        Decimal("160.0"),
        Decimal("160.0"),
    )


def test_missing_adjusted_close_fails_closed() -> None:
    payload = _payload("VT", [
        (date(2026, 4, 27), 100.0),
        (date(2026, 4, 30), None),
        (date(2026, 9, 9), 150.0),
    ])
    payload["chart"]["result"][0]["indicators"]["quote"][0]["close"][1] = 125.0

    with pytest.raises(benchmark.BenchmarkError, match="positive decimal"):
        benchmark.parse_chart_payload(
            payload,
            "VT",
            date(2026, 9, 10),
            NOW_DURING_SESSION,
            "https://example.test/VT",
        )


def test_stale_valuation_price_fails_closed() -> None:
    policy = _one_fund_policy()
    series = benchmark.PriceSeries(
        "VT",
        "America/New_York",
        (
            benchmark.PriceBar(date(2026, 4, 27), Decimal("100"), Decimal("100")),
            benchmark.PriceBar(date(2026, 4, 30), Decimal("125"), Decimal("125")),
            benchmark.PriceBar(date(2026, 9, 4), Decimal("150"), Decimal("150")),
        ),
        "https://example.test/VT",
    )

    with pytest.raises(benchmark.BenchmarkError, match="is stale"):
        benchmark.calculate_fund(
            policy,
            policy.funds[0],
            series,
            date(2026, 9, 10),
        )


def test_future_and_post_evaluation_dates_fail_before_network() -> None:
    policy = _one_fund_policy()
    client = _Client({})

    with pytest.raises(benchmark.BenchmarkError, match="in the future"):
        benchmark.build_report(
            policy,
            date(2026, 9, 11),
            NOW_DURING_SESSION,
            client,
        )
    assert client.urls == []

    after_eval = datetime(2027, 1, 3, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(benchmark.BenchmarkError, match="after configured evaluation start"):
        benchmark.build_report(
            policy,
            date(2027, 1, 2),
            after_eval,
            client,
        )
    assert client.urls == []


def test_exact_evaluation_start_uses_prior_completed_session() -> None:
    policy = _one_fund_policy()
    client = _Client({"VT": _payload("VT", [
        (date(2026, 4, 27), 100.0),
        (date(2026, 4, 30), 125.0),
        (date(2026, 12, 31), 175.0),
    ])})
    evaluation_now = datetime(2027, 1, 1, 12, 0, tzinfo=timezone.utc)

    report = benchmark.build_report(
        policy,
        date(2027, 1, 1),
        evaluation_now,
        client,
    )

    row = report["benchmarks"][0]
    assert row["valuation_session"] == "2026-12-31"
    assert row["price_age_calendar_days"] == 1
    assert row["value"] == Decimal("262.500")


def test_provider_identity_mismatch_fails_closed() -> None:
    payload = _payload("VTI", [(date(2026, 9, 9), 150.0)])

    with pytest.raises(benchmark.BenchmarkError, match="symbol mismatch"):
        benchmark.parse_chart_payload(
            payload,
            "VT",
            date(2026, 9, 10),
            NOW_DURING_SESSION,
            "https://example.test/VT",
        )
