#!/usr/bin/env python3
"""Read-only, contribution-timed passive ETF benchmark.

The benchmark answers a narrow counterfactual: what would the project's actual
trading-capital contributions be worth if each had instead bought a broad index
ETF and held it with distributions reinvested?  It does not inspect wallets,
place orders, or write caches.

Entry is deliberately conservative.  A contribution buys at the raw close of
the first completed exchange session *strictly after* its ledger date.  This
prevents a same-day close from being selected with hindsight when the transfer
time or brokerage availability is uncertain.  Raw closes determine the initial
fractional shares; adjusted-close growth factors model split adjustments and
reinvested distributions.

Usage:
    .venv/bin/python scripts/index_benchmark.py
    .venv/bin/python scripts/index_benchmark.py --as-of 2027-01-01
    .venv/bin/python scripts/index_benchmark.py --as-of 2026-09-10 --json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "notes" / "index_benchmark_policy.json"
USER_AGENT = "polyclaude-index-benchmark/1.0"


class BenchmarkError(RuntimeError):
    """A condition that makes the benchmark unsafe to report."""


@dataclass(frozen=True)
class Contribution:
    date: date
    amount: Decimal


@dataclass(frozen=True)
class Fund:
    ticker: str
    name: str
    fund_url: str


@dataclass(frozen=True)
class Policy:
    currency: str
    reference_capital: Decimal
    evaluation_start: date
    contributions: tuple[Contribution, ...]
    funds: tuple[Fund, ...]
    endpoint_template: str
    interval: str
    adjustment_definition_url: str
    max_entry_lag_days: int
    max_price_age_days: int
    entry_rule: str
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class PriceBar:
    session: date
    close: Decimal
    adjusted_close: Decimal


@dataclass(frozen=True)
class PriceSeries:
    ticker: str
    exchange_timezone: str
    bars: tuple[PriceBar, ...]
    source_url: str


def _date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise BenchmarkError(f"{label} must be an ISO date string")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BenchmarkError(f"invalid {label}: {value!r}") from exc


def _positive_decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool):
        raise BenchmarkError(f"{label} must be a positive decimal")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise BenchmarkError(f"{label} must be a positive decimal") from exc
    if not result.is_finite() or result <= 0:
        raise BenchmarkError(f"{label} must be a positive finite decimal")
    return result


def _bounded_days(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10:
        raise BenchmarkError(f"{label} must be an integer from 1 through 10")
    return value


def load_policy(path: Path = DEFAULT_POLICY) -> Policy:
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkError(f"cannot load benchmark policy {path}: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise BenchmarkError("benchmark policy schema_version must be 1")
    if raw.get("currency") != "USD":
        raise BenchmarkError("benchmark policy currency must be USD")

    contributions_raw = raw.get("contributions")
    if not isinstance(contributions_raw, list) or not contributions_raw:
        raise BenchmarkError("benchmark policy must contain contributions")
    contributions: list[Contribution] = []
    for index, item in enumerate(contributions_raw):
        if not isinstance(item, dict):
            raise BenchmarkError(f"contributions[{index}] must be an object")
        contributions.append(Contribution(
            _date(item.get("date"), f"contributions[{index}].date"),
            _positive_decimal(item.get("amount"), f"contributions[{index}].amount"),
        ))
    if tuple(contributions) != tuple(sorted(contributions, key=lambda row: row.date)):
        raise BenchmarkError("benchmark contributions must be in date order")

    reference_capital = _positive_decimal(raw.get("reference_capital"), "reference_capital")
    if sum((row.amount for row in contributions), Decimal("0")) != reference_capital:
        raise BenchmarkError("contributions do not sum to reference_capital")

    funds_raw = raw.get("benchmarks")
    if not isinstance(funds_raw, list) or not funds_raw:
        raise BenchmarkError("benchmark policy must contain funds")
    funds: list[Fund] = []
    seen: set[str] = set()
    for index, item in enumerate(funds_raw):
        if not isinstance(item, dict):
            raise BenchmarkError(f"benchmarks[{index}] must be an object")
        ticker = item.get("ticker")
        name = item.get("name")
        fund_url = item.get("fund_url")
        if not isinstance(ticker, str) or not ticker or ticker != ticker.upper():
            raise BenchmarkError(f"benchmarks[{index}].ticker must be uppercase")
        if ticker in seen:
            raise BenchmarkError(f"duplicate benchmark ticker: {ticker}")
        if not isinstance(name, str) or not name:
            raise BenchmarkError(f"benchmarks[{index}].name is required")
        if not isinstance(fund_url, str) or not fund_url.startswith("https://"):
            raise BenchmarkError(f"benchmarks[{index}].fund_url must be HTTPS")
        seen.add(ticker)
        funds.append(Fund(ticker, name, fund_url))

    source = raw.get("price_source")
    if not isinstance(source, dict):
        raise BenchmarkError("price_source must be an object")
    endpoint = source.get("endpoint_template")
    if not isinstance(endpoint, str) or not endpoint.startswith("https://") or "{ticker}" not in endpoint:
        raise BenchmarkError("price_source.endpoint_template must be an HTTPS ticker template")
    interval = source.get("interval")
    if interval != "1d":
        raise BenchmarkError("price_source.interval must be 1d")
    if source.get("purchase_price_field") != "chart.result[0].indicators.quote[0].close":
        raise BenchmarkError("unsupported price_source.purchase_price_field")
    if source.get("total_return_field") != "chart.result[0].indicators.adjclose[0].adjclose":
        raise BenchmarkError("unsupported price_source.total_return_field")
    definition_url = source.get("adjustment_definition_url")
    if not isinstance(definition_url, str) or not definition_url.startswith("https://"):
        raise BenchmarkError("price_source.adjustment_definition_url must be HTTPS")
    entry_rule = raw.get("entry_rule")
    if entry_rule != "first_complete_trading_session_strictly_after_contribution_date":
        raise BenchmarkError("unsupported benchmark entry_rule")
    assumptions = raw.get("assumptions")
    if not isinstance(assumptions, list) or not assumptions or not all(
        isinstance(item, str) and item for item in assumptions
    ):
        raise BenchmarkError("benchmark assumptions must be non-empty strings")

    evaluation_start = _date(raw.get("evaluation_start"), "evaluation_start")
    if evaluation_start <= contributions[-1].date:
        raise BenchmarkError("evaluation_start must follow all contributions")

    return Policy(
        currency="USD",
        reference_capital=reference_capital,
        evaluation_start=evaluation_start,
        contributions=tuple(contributions),
        funds=tuple(funds),
        endpoint_template=endpoint,
        interval=interval,
        adjustment_definition_url=definition_url,
        max_entry_lag_days=_bounded_days(
            source.get("max_entry_lag_calendar_days"),
            "price_source.max_entry_lag_calendar_days",
        ),
        max_price_age_days=_bounded_days(
            source.get("max_price_age_calendar_days"),
            "price_source.max_price_age_calendar_days",
        ),
        entry_rule=entry_rule,
        assumptions=tuple(assumptions),
    )


def _epoch(day: date) -> int:
    return int(datetime.combine(day, time.min, tzinfo=timezone.utc).timestamp())


def source_url(policy: Policy, ticker: str, as_of: date) -> str:
    start = policy.contributions[0].date - timedelta(days=7)
    end = as_of + timedelta(days=2)  # Yahoo period2 is exclusive.
    query = urlencode({
        "period1": _epoch(start),
        "period2": _epoch(end),
        "interval": policy.interval,
        "events": "div,splits",
        "includeAdjustedClose": "true",
    })
    return f"{policy.endpoint_template.format(ticker=ticker)}?{query}"


def _regular_session_has_closed(meta: dict[str, Any], now: datetime) -> bool:
    periods = meta.get("currentTradingPeriod")
    if not isinstance(periods, dict):
        return False
    regular = periods.get("regular")
    if not isinstance(regular, dict):
        return False
    end = regular.get("end")
    if isinstance(end, bool) or not isinstance(end, (int, float)) or not math.isfinite(end):
        return False
    return now.timestamp() >= float(end)


def parse_chart_payload(
    payload: Any,
    ticker: str,
    as_of: date,
    now: datetime,
    url: str,
) -> PriceSeries:
    """Validate Yahoo's response and retain completed daily adjusted closes."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise BenchmarkError("now must be timezone-aware")
    if not isinstance(payload, dict):
        raise BenchmarkError(f"{ticker}: price response is not an object")
    chart = payload.get("chart")
    if not isinstance(chart, dict) or chart.get("error") is not None:
        raise BenchmarkError(f"{ticker}: price provider returned an error")
    results = chart.get("result")
    if not isinstance(results, list) or len(results) != 1 or not isinstance(results[0], dict):
        raise BenchmarkError(f"{ticker}: price response has no unique result")
    result = results[0]
    meta = result.get("meta")
    if not isinstance(meta, dict):
        raise BenchmarkError(f"{ticker}: price response is missing metadata")
    if meta.get("symbol") != ticker:
        raise BenchmarkError(f"{ticker}: provider symbol mismatch")
    if meta.get("currency") != "USD" or meta.get("instrumentType") != "ETF":
        raise BenchmarkError(f"{ticker}: provider did not return a USD ETF")
    timezone_name = meta.get("exchangeTimezoneName")
    if not isinstance(timezone_name, str):
        raise BenchmarkError(f"{ticker}: exchange timezone is missing")
    try:
        exchange_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise BenchmarkError(f"{ticker}: unknown exchange timezone {timezone_name!r}") from exc

    timestamps = result.get("timestamp")
    indicators = result.get("indicators")
    if not isinstance(timestamps, list) or not isinstance(indicators, dict):
        raise BenchmarkError(f"{ticker}: daily price arrays are missing")
    adjusted_blocks = indicators.get("adjclose")
    quote_blocks = indicators.get("quote")
    if (
        not isinstance(adjusted_blocks, list)
        or len(adjusted_blocks) != 1
        or not isinstance(adjusted_blocks[0], dict)
    ):
        raise BenchmarkError(f"{ticker}: adjusted-close series is missing")
    if (
        not isinstance(quote_blocks, list)
        or len(quote_blocks) != 1
        or not isinstance(quote_blocks[0], dict)
    ):
        raise BenchmarkError(f"{ticker}: raw-close series is missing")
    adjusted_closes = adjusted_blocks[0].get("adjclose")
    closes = quote_blocks[0].get("close")
    if (
        not isinstance(adjusted_closes, list)
        or len(adjusted_closes) != len(timestamps)
        or not adjusted_closes
    ):
        raise BenchmarkError(f"{ticker}: adjusted-close series length mismatch")
    if not isinstance(closes, list) or len(closes) != len(timestamps) or not closes:
        raise BenchmarkError(f"{ticker}: raw-close series length mismatch")

    local_today = now.astimezone(exchange_timezone).date()
    today_is_complete = _regular_session_has_closed(meta, now)
    bars: list[PriceBar] = []
    seen_dates: set[date] = set()
    for index, (stamp, close, adjusted) in enumerate(
        zip(timestamps, closes, adjusted_closes)
    ):
        if isinstance(stamp, bool) or not isinstance(stamp, (int, float)) or not math.isfinite(stamp):
            raise BenchmarkError(f"{ticker}: invalid timestamp at row {index}")
        raw_close = _positive_decimal(close, f"{ticker} raw close row {index}")
        adjusted_close = _positive_decimal(
            adjusted,
            f"{ticker} adjusted close row {index}",
        )
        try:
            session = datetime.fromtimestamp(float(stamp), timezone.utc).astimezone(
                exchange_timezone
            ).date()
        except (OverflowError, OSError, ValueError) as exc:
            raise BenchmarkError(f"{ticker}: invalid timestamp at row {index}") from exc
        if session in seen_dates:
            raise BenchmarkError(f"{ticker}: duplicate price session {session}")
        seen_dates.add(session)
        if session > as_of or session > local_today:
            continue
        if session == local_today and not today_is_complete:
            continue
        bars.append(PriceBar(session, raw_close, adjusted_close))
    bars.sort(key=lambda row: row.session)
    if not bars:
        raise BenchmarkError(f"{ticker}: no completed adjusted-close prices through {as_of}")
    return PriceSeries(ticker, timezone_name, tuple(bars), url)


def fetch_series(
    client: httpx.Client,
    policy: Policy,
    ticker: str,
    as_of: date,
    now: datetime,
) -> PriceSeries:
    url = source_url(policy, ticker, as_of)
    try:
        response = client.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, json.JSONDecodeError, ValueError) as exc:
        raise BenchmarkError(f"{ticker}: price request failed: {exc}") from exc
    return parse_chart_payload(payload, ticker, as_of, now, url)


def calculate_fund(policy: Policy, fund: Fund, series: PriceSeries, as_of: date) -> dict[str, Any]:
    if series.ticker != fund.ticker:
        raise BenchmarkError(f"{fund.ticker}: wrong price series supplied")
    latest = series.bars[-1]
    price_age = (as_of - latest.session).days
    if price_age < 0 or price_age > policy.max_price_age_days:
        raise BenchmarkError(
            f"{fund.ticker}: latest completed price {latest.session} is stale for {as_of} "
            f"({price_age} calendar days; maximum {policy.max_price_age_days})"
        )

    lots: list[dict[str, Any]] = []
    with localcontext() as context:
        context.prec = 28
        active_capital = Decimal("0")
        value = Decimal("0")
        for contribution in policy.contributions:
            if contribution.date > as_of:
                continue
            entry = next(
                (bar for bar in series.bars if bar.session > contribution.date),
                None,
            )
            if entry is None or entry.session > as_of:
                raise BenchmarkError(
                    f"{fund.ticker}: no completed entry session after contribution "
                    f"{contribution.date} and through {as_of}"
                )
            lag = (entry.session - contribution.date).days
            if lag > policy.max_entry_lag_days:
                raise BenchmarkError(
                    f"{fund.ticker}: entry session {entry.session} is {lag} days after "
                    f"contribution {contribution.date}; maximum {policy.max_entry_lag_days}"
                )
            initial_shares = contribution.amount / entry.close
            total_return_factor = latest.adjusted_close / entry.adjusted_close
            ending_value = contribution.amount * total_return_factor
            active_capital += contribution.amount
            value += ending_value
            lots.append({
                "contribution_date": contribution.date.isoformat(),
                "amount": contribution.amount,
                "entry_session": entry.session.isoformat(),
                "entry_close": entry.close,
                "entry_adjusted_close": entry.adjusted_close,
                "initial_fractional_shares": initial_shares,
                "total_return_factor": total_return_factor,
                "ending_value": ending_value,
            })
        if active_capital == 0:
            raise BenchmarkError(f"{fund.ticker}: no contributions exist by {as_of}")
        gain = value - active_capital
        return_pct = gain / active_capital * Decimal("100")

    return {
        "ticker": fund.ticker,
        "name": fund.name,
        "fund_url": fund.fund_url,
        "exchange_timezone": series.exchange_timezone,
        "valuation_session": latest.session.isoformat(),
        "price_age_calendar_days": price_age,
        "valuation_adjusted_close": latest.adjusted_close,
        "lots": lots,
        "contributed_capital": active_capital,
        "value": value,
        "gain": gain,
        "return_pct": return_pct,
        "source_url": series.source_url,
    }


def build_report(
    policy: Policy,
    as_of: date,
    now: datetime,
    client: httpx.Client,
) -> dict[str, Any]:
    if now.tzinfo is None or now.utcoffset() is None:
        raise BenchmarkError("now must be timezone-aware")
    if as_of > now.astimezone(timezone.utc).date():
        raise BenchmarkError(f"as-of date {as_of} is in the future")
    if as_of > policy.evaluation_start:
        raise BenchmarkError(
            f"as-of date {as_of} is after configured evaluation start {policy.evaluation_start}"
        )
    if as_of <= policy.contributions[-1].date:
        raise BenchmarkError(
            f"as-of date must be after final contribution {policy.contributions[-1].date}"
        )

    # Fetch and validate every fund before returning anything.  One failed or
    # stale series invalidates the report rather than producing a cherry-picked
    # subset of benchmarks.
    series = [
        fetch_series(client, policy, fund.ticker, as_of, now)
        for fund in policy.funds
    ]
    rows = [
        calculate_fund(policy, fund, prices, as_of)
        for fund, prices in zip(policy.funds, series)
    ]
    return {
        "schema_version": 1,
        "as_of": as_of.isoformat(),
        "retrieved_at": now.astimezone(timezone.utc).isoformat(),
        "currency": policy.currency,
        "reference_capital": policy.reference_capital,
        "evaluation_start": policy.evaluation_start.isoformat(),
        "entry_rule": policy.entry_rule,
        "adjustment_definition_url": policy.adjustment_definition_url,
        "assumptions": list(policy.assumptions),
        "benchmarks": rows,
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def print_report(report: dict[str, Any]) -> None:
    print("PASSIVE INDEX BENCHMARK — contribution-timed total return")
    print(f"As of requested date: {report['as_of']}")
    print(f"Data retrieved:       {report['retrieved_at']}")
    print(f"Reference capital:    ${report['reference_capital']:.2f}")
    print("Entry rule:           first completed session strictly after each contribution date")
    print("Return series:         raw entry closes; adjusted-close total-return growth")
    for row in report["benchmarks"]:
        print()
        print(f"{row['ticker']} — {row['name']}")
        for lot in row["lots"]:
            print(
                f"  ${lot['amount']:.2f} on {lot['contribution_date']} -> "
                f"{lot['entry_session']} @ ${lot['entry_close']:.6f} close; "
                f"{lot['initial_fractional_shares']:.9f} initial shares "
                f"(adjusted close ${lot['entry_adjusted_close']:.6f})"
            )
        print(
            f"  {row['valuation_session']} adjusted close ${row['valuation_adjusted_close']:.6f} "
            f"({row['price_age_calendar_days']} calendar day(s) before requested date)"
        )
        print(
            f"  VALUE ${row['value']:.2f} | GAIN {row['gain']:+.2f} USD | "
            f"RETURN {row['return_pct']:+.2f}%"
        )
        print(f"  prices: {row['source_url']}")
        print(f"  fund:   {row['fund_url']}")
    print()
    print("Assumptions and limits:")
    for item in report["assumptions"]:
        print(f"  - {item}")
    print(f"  - Adjusted-close definition: {report['adjustment_definition_url']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", help="ISO date; defaults to today's UTC date")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    try:
        as_of = _date(args.as_of, "as-of") if args.as_of else now.date()
        policy = load_policy(args.policy)
        with httpx.Client(follow_redirects=True) as client:
            report = build_report(policy, as_of, now, client)
    except BenchmarkError as exc:
        print(f"BENCHMARK UNAVAILABLE: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(_json_ready(report), indent=2, sort_keys=True))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
