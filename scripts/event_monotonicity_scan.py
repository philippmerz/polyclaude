#!/usr/bin/env python3
"""Polymarket event-monotonicity arbitrage scanner.

TWO ladder shapes are checked (2026-08-10: the threshold pass was added after
finding the scanner could only ever see the date one):

  DATE ladder — "Will X happen by Y?" across by-May-15 / by-May-31 / by-Jun-30.
  THRESHOLD ladder — one deadline, a rising bar: HLE >=50/55/60/65/70,
    "FDV above $50M/$500M/$1B", vote share, temperature. For thresholds
    k1 < k2, P(X >= k2) <= P(X >= k1) — as monotone as the date case, and the
    arb construction is identical with "harder bar" in the role of "earlier
    date". These are common on Polymarket, and the scanner had the machinery
    to check them while explicitly skipping them as "categorical".

For event A occurring at time t (or before) on monotonic dates t1 < t2:

    P(A by t2) >= P(A by t1)

If prices on the YES side violate this (i.e., YES_t1 > YES_t2 + tolerance),
that's a pure decomposition arb:
- Buy YES_t2 (cheap) + Sell YES_t1 (expensive)
- If A happens by t1: YES_t1 wins (we paid 1.0 to the buyer); YES_t2 also wins
  (we receive 1.0 from the seller)
- If A happens between t1 and t2: only YES_t2 wins; we paid YES_t1 - YES_t2 < 0
  → we keep the spread
- If A doesn't happen by t2: neither wins; we keep the spread (sold YES_t1
  for more than we paid for YES_t2)

Profit per share = (price_YES_t1 - price_YES_t2) - fees, guaranteed.

This script:
1. Fetches active Polymarket events via gamma-api /events
2. For each event with 2+ markets, parses explicit child-question deadlines
3. Compares only identical child propositions/rules, ordered by semantic deadline
4. Flags monotonicity violations beyond tolerance (default 1pp)
5. Outputs: violation details + spread + fee-aware breakeven

Lesson source: operator suggestion 2026-05-15 — Polymarket UI glitched
showing June-30 < May-15 transiently. False alarm in that instance but
the GENERAL pattern of monotonicity violations is real arb if they occur.

Usage:
    python scripts/event_monotonicity_scan.py
    python scripts/event_monotonicity_scan.py --min-violation-pp 2
    python scripts/event_monotonicity_scan.py --json
"""

from __future__ import annotations

import argparse
import calendar
import datetime
from decimal import Decimal, InvalidOperation
import json
import math
import re
import sys

import httpx

import pm_fees  # per-market Gamma feeSchedule; see pm_fees.py for source-of-truth rules


def fetch_events(min_vol: float = 1000, max_pages: int = 15) -> list[dict]:
    out: list[dict] = []
    seen = set()
    with httpx.Client(timeout=20) as c:
        for page in range(max_pages):
            try:
                r = c.get("https://gamma-api.polymarket.com/events", params={
                    "closed": "false", "active": "true",
                    # gamma caps pages at 100; offset stride must match the cap,
                    # not the requested limit, else pages skip 80% (verified 2026-06-06).
                    "limit": 100, "offset": page * 100,
                    "order": "volume24hr", "ascending": "false",
                })
                r.raise_for_status()
            except Exception as e:
                print(f"events page {page} err: {e}", file=sys.stderr)
                continue
            data = r.json() or []
            if not data:
                break
            for ev in data:
                eid = ev.get("id")
                if not eid or eid in seen:
                    continue
                seen.add(eid)
                if (ev.get("volume24hr", 0) or 0) < min_vol:
                    continue
                if ev.get("closed"):
                    continue
                out.append(ev)
    return out


def parse_outcome_prices(p) -> tuple[float, float] | None:
    try:
        if isinstance(p, str):
            parsed = json.loads(p)
        else:
            parsed = p
        if isinstance(parsed, list) and len(parsed) >= 2:
            return float(parsed[0]), float(parsed[1])
    except Exception:
        pass
    return None


def _named_yes_no_prices(outcomes_value, prices: tuple[float, float]) -> tuple[float, float] | None:
    """Return prices in YES/NO order only when Gamma names both outcomes."""
    outcomes = _json_list(outcomes_value)
    if not outcomes or len(outcomes) != 2:
        return None
    names = [" ".join(str(value).casefold().split()) for value in outcomes]
    if set(names) != {"yes", "no"} or len(set(names)) != 2:
        return None
    if (not all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in prices)
            or not math.isclose(sum(prices), 1.0, rel_tol=0.0, abs_tol=1e-6)):
        return None
    by_name = dict(zip(names, prices))
    return by_name["yes"], by_name["no"]


# A date ladder is safe to compare only when the CHILD questions describe the
# same proposition and differ solely in a terminal deadline. Event membership
# is not enough: Polymarket category events commonly contain unrelated subjects
# (for example, one acquisition market per company). On 2026-08-28, a few
# resolved children in "Which companies will be acquired before 2027?"
# temporarily carried a Dec-31 Gamma endDate while live children carried Jan-1.
# Treating those metadata dates as rungs manufactured a +13.28pp "REAL ARB"
# between different companies. A real book walk cannot rescue a false logical
# pairing, so this parser deliberately fails closed.
_MONTH_NAMES = (
    "january|february|march|april|may|june|july|august|"
    "september|october|november|december"
)
_TERMINAL_DEADLINE_RE = re.compile(
    rf"^(?P<subject>.+?)\s+(?P<operator>by|before)\s+"
    rf"(?P<deadline>"
    rf"(?:{_MONTH_NAMES})\s+\d{{1,2}}(?:st|nd|rd|th)?\s*,?\s*\d{{4}}|"
    rf"(?:{_MONTH_NAMES})\s+\d{{4}}|"
    rf"q[1-4]\s+\d{{4}}|"
    rf"(?:the\s+)?end\s+of\s+\d{{4}}|"
    rf"\d{{4}}-\d{{2}}-\d{{2}}|"
    rf"\d{{1,2}}/\d{{1,2}}/\d{{2,4}}|"
    rf"\d{{4}}"
    rf")\s*\??$",
    re.IGNORECASE,
)


def _normalize_subject(value: str) -> str:
    # Preserve punctuation because it can carry meaning ("US-Iran" vs
    # "US/Iran", possessives, decimal points). Only case, repeated whitespace,
    # and the question's terminal punctuation are safely cosmetic.
    return " ".join(value.casefold().strip().removesuffix("?").split())


def _normalize_rule_text(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        return "<invalid>"
    return " ".join(value.casefold().split())


def _gamma_deadline_consistent(
    deadline: datetime.date, gamma_end: datetime.datetime,
) -> bool:
    """Allow exact calendar dates or the normal next-UTC-day rollover only."""
    return (gamma_end.date() - deadline).days in (0, 1)


def _parse_deadline_date(value: str, operator: str) -> datetime.date | None:
    """Parse a deliberately small set of unambiguous calendar deadlines.

    Gamma endDate is *not* used as the rung itself; it can be stale or shifted
    across UTC midnight, which caused the acquisition false alert above.
    Yearless dates are rejected instead of inferring logic from that metadata.
    """
    raw = " ".join(value.lower().replace(",", " ").split())
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            return datetime.date.fromisoformat(raw)
        if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", raw):
            month, day, year = (int(x) for x in raw.split("/"))
            if year < 100:
                year += 2000
            return datetime.date(year, month, day)

        m = re.fullmatch(r"q([1-4])\s+(\d{4})", raw)
        if m:
            quarter, year = int(m.group(1)), int(m.group(2))
            month = quarter * 3
            return datetime.date(year, month, calendar.monthrange(year, month)[1])

        m = re.fullmatch(r"(?:the\s+)?end\s+of\s+(\d{4})", raw)
        if m:
            return datetime.date(int(m.group(1)), 12, 31)

        if re.fullmatch(r"\d{4}", raw):
            year = int(raw)
            # "before 2027" means the Jan-1 boundary; "by 2027" means through
            # that calendar year. Keeping the operator in the proposition key
            # also prevents these distinct wordings from being mixed.
            return (datetime.date(year, 1, 1) if operator == "before"
                    else datetime.date(year, 12, 31))

        month_map = {
            name.lower(): number for number, name in enumerate(calendar.month_name)
            if name
        }
        m = re.fullmatch(rf"({_MONTH_NAMES})\s+(\d{{4}})", raw)
        if m:
            month, year = month_map[m.group(1)], int(m.group(2))
            return datetime.date(year, month, calendar.monthrange(year, month)[1])

        m = re.fullmatch(
            rf"({_MONTH_NAMES})\s+(\d{{1,2}})(?:st|nd|rd|th)?\s+(\d{{4}})",
            raw,
        )
        if m:
            month, day = month_map[m.group(1)], int(m.group(2))
            return datetime.date(int(m.group(3)), month, day)
    except (KeyError, TypeError, ValueError):
        return None
    return None


def parse_date_ladder_question(
    question: str, fallback_end: datetime.datetime,
) -> tuple[str, datetime.date] | None:
    """Return ``(proposition_key, semantic_deadline)`` or fail closed.

    The normalized subject plus deadline operator is the comparability key.
    Thus "Will Ink launch ... by Sep 30?" and "... by Dec 31?" match, while
    Warner Bros. and PayPal acquisition children in one event never do.
    """
    normalized = " ".join((question or "").split())
    match = _TERMINAL_DEADLINE_RE.fullmatch(normalized)
    if not match:
        return None
    subject = _normalize_subject(match.group("subject"))
    operator = match.group("operator").lower()
    if not subject:
        return None
    deadline = _parse_deadline_date(match.group("deadline"), operator)
    if deadline is None or not _gamma_deadline_consistent(deadline, fallback_end):
        return None
    return f"{subject}|{operator}", deadline


POLYMARKET_CLOB = "https://clob.polymarket.com"
PM_BOOK_MAX_AGE_SECONDS = 120
PM_BOOK_FUTURE_SKEW_SECONDS = 5
MAX_EXECUTABLE_CHECK_SIZE = Decimal("1000")


# A magnitude suffix MUST be captured and applied, never merely skipped.
# 2026-08-10, first live run of the threshold pass: an earlier version only
# refused to CONSUME "million"/"billion", which for the leading-comparator
# patterns ("above $1B") still returned the bare number. So "$1B" parsed as
# 1.0 and "$50M" as 50.0, inverting a perfectly-priced FDV ladder and
# manufacturing SIX "REAL ARB" fires that survived the live-CLOB walk — the
# books were real, the ORDERING was fabricated. Third instance of the same
# class (Montana duplicate members, WH per-day full-lid): a parse that groups
# non-comparable things as comparable. The CLOB walk cannot rescue a bad
# parse, so the parse carries the safety burden alone.
_SCALES = {"k": 1e3, "thousand": 1e3,
           "m": 1e6, "mm": 1e6, "mln": 1e6, "million": 1e6,
           "b": 1e9, "bn": 1e9, "billion": 1e9,
           "t": 1e12, "trillion": 1e12}
_SCALE_RE = r"(?P<scale>mln|mm|million|billion|trillion|thousand|bn|[kmbt])"
# Try the magnitude suffix first, then fall back to a plain unit (%/°F/bps/
# seats). Alternation order is what makes "$1B" scale and "95F" not.
_NUM = (
    rf"(?P<currency>\$)?(?P<val>[0-9][0-9,]*(?:\.[0-9]+)?)"
    rf"(?:\s*{_SCALE_RE}\b)?"
    rf"(?:\s*(?P<unit>%|°?[a-z]{{1,10}}))?"
)
_UP_WORDS = r"(?:or higher|or more|or greater|or above|or over)"
_DN_WORDS = r"(?:or lower|or less|or fewer|or below|or under)"
_UP_LEAD = r"(?:at least|above|over|greater than|more than|exceeds?)"
_DN_LEAD = r"(?:at most|below|under|less than|fewer than)"


def _threshold_dimension(match: re.Match) -> str | None:
    """Return a normalized measurement dimension, rejecting ambiguity.

    Magnitude suffixes change the numeric value, not its dimension: ``$50M``
    and ``$1B`` are both USD.  A lower-case bare single-letter suffix such as
    ``50m`` is ambiguous (million vs metres/minutes), so it is intentionally
    unsupported unless the currency marker disambiguates it.
    """
    currency = bool(match.groupdict().get("currency"))
    raw_scale = match.groupdict().get("scale") or ""
    raw_unit = match.groupdict().get("unit") or ""
    if raw_scale in {"k", "m", "b", "t"} and not currency:
        return None

    unit = raw_unit.casefold()
    if currency:
        if unit and unit not in {"usd", "dollar", "dollars"}:
            return None
        return "usd"
    if not unit:
        return "scalar"
    aliases = {
        "%": "percent",
        "bp": "basis_points",
        "bps": "basis_points",
        "°f": "fahrenheit",
        "f": "fahrenheit",
        "°c": "celsius",
        "c": "celsius",
    }
    return aliases.get(unit, f"unit:{unit}")


def _parse_threshold_detail(question: str) -> tuple[float, int, str, str] | None:
    """Extract ``(value, direction, proposition_template, dimension)``.

    direction +1 = "value or higher" (a HARDER bar as value rises, so YES must
    be non-increasing in value); -1 = "value or lower" (YES non-decreasing).

    The number MUST be anchored to an explicit comparator. That is the whole
    safety property: it rejects exact-value buckets ("will X win 3 seats"),
    which are a PARTITION and carry no monotone constraint, and it stops the
    scan from grabbing an unrelated number like the year in "...on HLE in 2026
    be 50% or higher?" — where an any-number parse would read 2026 as the bar.
    Same failure family as the Montana dedup and the WH per-day exclusion: a
    grouping heuristic treating a non-fungible structure as fungible.
    """
    # Preserve case while parsing so an upper-case financial ``M`` remains
    # distinguishable from an ambiguous lower-case bare ``m``. The template is
    # case-folded after the comparator span is removed.
    q = " ".join((question or "").split())
    if not q:
        return None
    for pat, direction in ((rf"{_NUM}\s*{_UP_WORDS}", +1),
                           (rf"{_NUM}\s*{_DN_WORDS}", -1),
                           (rf"{_UP_LEAD}\s*{_NUM}", +1),
                           (rf"{_DN_LEAD}\s*{_NUM}", -1)):
        m = re.search(pat, q, re.IGNORECASE)
        if m:
            try:
                val = float(m.group("val").replace(",", ""))
            except Exception:
                return None
            scale = (m.groupdict().get("scale") or "").strip()
            if scale:
                val *= _SCALES[scale.casefold()]
            dimension = _threshold_dimension(m)
            if dimension is None or not math.isfinite(val):
                return None
            template = " ".join(
                f"{q[:m.start()]} <threshold> {q[m.end():]}".casefold().split()
            )
            return val, direction, template, dimension
    return None


def parse_threshold(question: str) -> tuple[float, int] | None:
    """Public compatibility wrapper returning ``(value, direction)``.

    The scanner itself also consumes the proposition template from
    ``_parse_threshold_detail``. Event membership alone is not equivalence:
    distinct entities with distinct numeric bars can share one category event.
    """
    detail = _parse_threshold_detail(question)
    return detail[:2] if detail else None


def _decimal(value) -> Decimal | None:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def _json_list(value) -> list | None:
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, list) else None


def _named_binary_tokens(row: dict) -> dict[str, str] | None:
    """Map exact YES/NO outcome names to their paired CLOB token IDs."""
    outcomes = _json_list(row.get("outcomes"))
    tokens = _json_list(row.get("clob_tokens"))
    if not outcomes or not tokens or len(outcomes) != 2 or len(tokens) != 2:
        return None
    names = [" ".join(str(value).casefold().split()) for value in outcomes]
    token_ids = [str(value).strip() for value in tokens]
    if (set(names) != {"yes", "no"} or len(set(names)) != 2
            or len(set(token_ids)) != 2
            or not all(token.isdigit() for token in token_ids)):
        return None
    return dict(zip(names, token_ids))


def _known_fee_market(market: dict | None) -> bool:
    """Whether ``pm_fees`` has authoritative or explicit legacy inputs.

    Unknown fetched metadata must not be converted into the old meaning of an
    explicitly supplied null ``takerBaseFee`` (fee-free). Advisory midpoint
    math may use pm_fees' conservative fallback, but a ``REAL`` label requires
    fee inputs whose presence and shape are known.
    """
    if not isinstance(market, dict):
        return False
    flag_present = "feesEnabled" in market
    flag = market.get("feesEnabled")
    if flag_present and not isinstance(flag, bool):
        return False
    schedule_present = "feeSchedule" in market
    schedule = market.get("feeSchedule")
    if isinstance(schedule, dict):
        rate = _decimal(schedule.get("rate"))
        exponent = _decimal(schedule.get("exponent"))
        taker_only = schedule.get("takerOnly", True)
        if (rate is None or rate < 0 or exponent is None or exponent < 0
                or not isinstance(taker_only, bool)):
            return False
        # Contradictory sources are not evidence that either value is current.
        return not (flag is False and rate != 0)
    if schedule_present and schedule is not None:
        return False
    if flag is False:
        return True

    legacy_present = "takerBaseFee" in market
    legacy = market.get("takerBaseFee")
    if not legacy_present:
        return False
    if legacy in (None, "", "None"):
        return not flag_present
    parsed = _decimal(legacy)
    return parsed is not None and parsed >= 0 and not (flag is True and parsed == 0)


def _parse_clob_levels(raw_levels) -> list[tuple[Decimal, Decimal]] | None:
    if not isinstance(raw_levels, list):
        return None
    levels: list[tuple[Decimal, Decimal]] = []
    seen_prices: set[Decimal] = set()
    for raw in raw_levels:
        if not isinstance(raw, dict):
            return None
        price = _decimal(raw.get("price"))
        size = _decimal(raw.get("size"))
        if (price is None or size is None or not (Decimal("0") < price < Decimal("1"))
                or size <= 0 or price in seen_prices):
            return None
        seen_prices.add(price)
        levels.append((price, size))
    return levels


def _validated_clob_book(payload: dict, *, token_id: str, condition_id: str,
                         now: datetime.datetime) -> dict | None:
    """Validate identity, freshness, minimum size, and every visible level."""
    if not isinstance(payload, dict):
        return None
    if str(payload.get("asset_id") or "") != token_id:
        return None
    if str(payload.get("market") or "").casefold() != condition_id.casefold():
        return None
    timestamp_ms = _decimal(payload.get("timestamp"))
    if (timestamp_ms is None or timestamp_ms <= 0
            or timestamp_ms != timestamp_ms.to_integral_value()):
        return None
    try:
        timestamp = datetime.datetime.fromtimestamp(
            float(timestamp_ms / Decimal("1000")), datetime.timezone.utc,
        )
    except (OverflowError, OSError, ValueError):
        return None
    if now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)
    age = (now.astimezone(datetime.timezone.utc) - timestamp).total_seconds()
    if age > PM_BOOK_MAX_AGE_SECONDS or age < -PM_BOOK_FUTURE_SKEW_SECONDS:
        return None

    minimum = _decimal(payload.get("min_order_size"))
    asks = _parse_clob_levels(payload.get("asks"))
    bids = _parse_clob_levels(payload.get("bids"))
    if minimum is None or minimum <= 0 or asks is None or bids is None:
        return None
    if asks and bids and max(price for price, _ in bids) >= min(price for price, _ in asks):
        return None
    return {
        "asks": asks,
        "bids": bids,
        "min_order_size": minimum,
        "timestamp": timestamp,
        "age_seconds": age,
    }


def _fetch_validated_clob_book(token_id: str, condition_id: str) -> dict | None:
    try:
        response = httpx.get(
            f"{POLYMARKET_CLOB}/book", params={"token_id": token_id}, timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return None
    return _validated_clob_book(
        payload,
        token_id=token_id,
        condition_id=condition_id,
        now=datetime.datetime.now(datetime.timezone.utc),
    )


def _walk_clob_asks(levels: list[tuple[Decimal, Decimal]], size: Decimal,
                    fee_market: dict) -> dict | None:
    remaining = size
    cost = Decimal("0")
    fee = Decimal("0")
    fills = []
    for price, available in sorted(levels, key=lambda item: item[0]):
        take = min(remaining, available)
        if take <= 0:
            continue
        fee_per_share = _decimal(pm_fees.fee_per_share(fee_market, float(price)))
        if fee_per_share is None or fee_per_share < 0:
            return None
        cost += take * price
        fee += take * fee_per_share
        fills.append({
            "price": float(price),
            "size": float(take),
            "fee": float(take * fee_per_share),
        })
        remaining -= take
        if remaining <= 0:
            break
    if remaining > 0:
        return None
    return {
        "shares": float(size),
        "cost": cost,
        "fee": fee,
        "average_price": cost / size,
        "fills": fills,
    }


def _fee_market_from_row(row: dict) -> dict | None:
    """Return the best fee payload carried by a scanner row.

    New rows retain Gamma's complete fee inputs so ``pm_fees`` can honor
    ``feeSchedule.rate``, ``exponent``, and ``takerOnly``.  The legacy fallback
    keeps hand-built rows and old cached scanner fixtures working: an explicit
    ``taker_fee_bps=None`` is a known zero-fee market, while a row with no fee
    information at all is unknown and therefore receives pm_fees' conservative
    fallback.
    """
    if "fee_market" in row:
        fee_market = row.get("fee_market")
        return fee_market if isinstance(fee_market, dict) else None
    if "fee_schedule" in row:
        payload = {"feeSchedule": row.get("fee_schedule")}
        if "taker_fee_bps" in row:
            payload["takerBaseFee"] = row.get("taker_fee_bps")
        if "fees_enabled" in row:
            payload["feesEnabled"] = row.get("fees_enabled")
        return payload
    if "taker_fee_bps" in row:
        return {"takerBaseFee": row.get("taker_fee_bps")}
    return None


def _executable_monotonic_arb(row_early: dict, row_late: dict) -> dict | None:
    """LIVE-CLOB validation (2026-07-23): the monotonicity flag uses gamma
    MIDPOINTS, which sit between stub bids and real asks — the 2026-07-23
    outage surfaced a 3-hour 'actionable' false alarm (Elon-tweet-Hyperliquid:
    flagged +11.25pp on mids, but the earlier YES was 0.024 bid / 0.377 ask =
    no real price). The riskless capture of an (earlier_YES > later_YES)
    violation is BUY later_YES + BUY earlier_NO (min payoff 1.0 in every
    world). It's a real arb only if the EXECUTABLE cost of that pair, incl.
    taker fees, is < 1.0. This walks both books and returns the true edge or
    None if unexecutable."""
    late_tokens = _named_binary_tokens(row_late)
    early_tokens = _named_binary_tokens(row_early)
    late_condition = str(row_late.get("condition_id") or "").strip()
    early_condition = str(row_early.get("condition_id") or "").strip()
    late_fee_market = _fee_market_from_row(row_late)
    early_fee_market = _fee_market_from_row(row_early)
    if (late_tokens is None or early_tokens is None
            or not late_condition or not early_condition
            or not _known_fee_market(late_fee_market)
            or not _known_fee_market(early_fee_market)):
        return None

    # The riskless pair is later YES + earlier NO. Outcome names, not array
    # positions, select each token so a reversed Gamma array cannot invert it.
    late_book = _fetch_validated_clob_book(late_tokens["yes"], late_condition)
    early_book = _fetch_validated_clob_book(early_tokens["no"], early_condition)
    if late_book is None or early_book is None:
        return None

    late_gamma_min = _decimal(row_late.get("order_min_size"))
    early_gamma_min = _decimal(row_early.get("order_min_size"))
    if (late_gamma_min is None or late_gamma_min <= 0
            or early_gamma_min is None or early_gamma_min <= 0):
        return None
    comparison_size = max(
        late_gamma_min,
        early_gamma_min,
        late_book["min_order_size"],
        early_book["min_order_size"],
    )
    if comparison_size <= 0 or comparison_size > MAX_EXECUTABLE_CHECK_SIZE:
        return None

    late_walk = _walk_clob_asks(late_book["asks"], comparison_size, late_fee_market)
    early_walk = _walk_clob_asks(early_book["asks"], comparison_size, early_fee_market)
    if late_walk is None or early_walk is None:
        return None
    total_fee = late_walk["fee"] + early_walk["fee"]
    total_cost = late_walk["cost"] + early_walk["cost"] + total_fee
    cost_per_pair = total_cost / comparison_size
    fee_per_pair = total_fee / comparison_size
    return {
        "comparison_size": float(comparison_size),
        "late_yes_ask": float(late_walk["average_price"]),
        "early_no_ask": float(early_walk["average_price"]),
        "fee": round(float(fee_per_pair), 4),
        "total_fee_dollars": round(float(total_fee), 6),
        "total_cost_dollars": round(float(total_cost), 6),
        "exec_cost": round(float(cost_per_pair), 4),
        "exec_edge_pp": round(float((Decimal("1") - cost_per_pair) * Decimal("100")), 2),
        "late_yes_walk": {
            **late_walk,
            "cost": float(late_walk["cost"]),
            "fee": float(late_walk["fee"]),
            "average_price": float(late_walk["average_price"]),
            "book_timestamp": late_book["timestamp"].isoformat(),
        },
        "early_no_walk": {
            **early_walk,
            "cost": float(early_walk["cost"]),
            "fee": float(early_walk["fee"]),
            "average_price": float(early_walk["average_price"]),
            "book_timestamp": early_book["timestamp"].isoformat(),
        },
    }


_UNSET = object()   # "caller supplied nothing" — distinct from takerBaseFee=None,
                    # which is a real value meaning THIS MARKET CHARGES NO FEE.
                    # Collapsing the two charged zero-fee legs a 10% phantom fee
                    # and suppressed genuine arbs (caught by tests/test_money_math.py
                    # minutes after the suite first existed, in code written the
                    # same hour as the lesson warning against this exact mixup).


def fee_aware_breakeven(yes_t1: float, yes_t2: float,
                        bps_t1=_UNSET, bps_t2=_UNSET) -> float:
    """Fee-aware breakeven spread needed to profit on the arb.

    We BUY yes_t2 (paying yes_t2 + fee) and SELL yes_t1 (receiving yes_t1 - fee).
    ``bps_t1`` and ``bps_t2`` retain their historical public meaning: a scalar
    is treated as legacy ``takerBaseFee`` and explicit None means fee-free.
    Callers may now pass a complete Gamma market dict instead, which lets
    ``pm_fees`` consume the authoritative feeSchedule rate and exponent.

    2026-08-14: this used a hard-coded 0.072 while the live modal rate is 0.10
    (84/100 active markets; the other 16 charge nothing). Understating the fee
    by 28% in an ARB breakeven is the worst possible place for that error — it
    lowers the bar a violation must clear, which manufactures arbs that lose
    money on execution. The two legs can also carry DIFFERENT rates, which a
    single constant cannot express at all. market_rows already carried
    taker_fee_bps; it simply was not being read.
    """
    def _market(value):
        if value is _UNSET:
            return None  # unknown/unfetched: conservative pm_fees fallback
        if isinstance(value, dict):
            return value
        return {"takerBaseFee": value}

    sell_fee = pm_fees.fee_per_share(_market(bps_t1), yes_t1)
    buy_fee = pm_fees.fee_per_share(_market(bps_t2), yes_t2)
    return sell_fee + buy_fee


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--min-violation-pp", type=float, default=1.0,
                   help="Minimum violation in pp to flag (default 1pp).")
    p.add_argument("--min-event-vol24", type=float, default=1000,
                   help="Skip events with vol24hr below this (default $1k).")
    p.add_argument("--min-leg-vol24", type=float, default=500,
                   help="Require BOTH legs of a pair to have >= this 24h volume "
                        "(default $500). Filters stale-midpoint stub artifacts on "
                        "illiquid markets that aren't executable arbs.")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    print(f"# event_monotonicity_scan: fetching active events with vol24hr >= ${args.min_event_vol24}", file=sys.stderr)
    events = fetch_events(min_vol=args.min_event_vol24)
    print(f"# {len(events)} events to inspect", file=sys.stderr)

    violations = []
    multi_market_events = 0
    for ev in events:
        markets = ev.get("markets", [])
        if len(markets) < 2:
            continue
        # Extract (end_date, yes_price, slug, market_id, question)
        market_rows = []
        for m in markets:
            if m.get("closed"):
                continue
            if m.get("umaResolutionStatus") in ("proposed", "disputed", "resolved"):
                continue
            prices = parse_outcome_prices(m.get("outcomePrices"))
            if not prices:
                continue
            named_prices = _named_yes_no_prices(m.get("outcomes"), prices)
            if named_prices is None:
                continue
            end_iso = m.get("endDate") or m.get("endDateIso")
            if not end_iso:
                continue
            try:
                end_dt = datetime.datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
            except Exception:
                continue
            date_ladder = parse_date_ladder_question(m.get("question") or "", end_dt)
            market_rows.append({
                "end_dt": end_dt,
                "date_key": date_ladder[0] if date_ladder else None,
                "deadline_dt": date_ladder[1] if date_ladder else None,
                "date_rules_key": tuple(_normalize_rule_text(m.get(field)) for field in (
                    "description", "resolutionSource", "rules",
                )),
                "yes": named_prices[0],
                "no": named_prices[1],
                "slug": m.get("slug"),
                "market_id": m.get("id"),
                "question": m.get("question"),
                "vol24hr": float(m.get("volume24hr", 0) or 0),
                "outcomes": m.get("outcomes"),
                "clob_tokens": m.get("clobTokenIds"),
                "condition_id": m.get("conditionId"),
                "order_min_size": m.get("orderMinSize"),
                "taker_fee_bps": m.get("takerBaseFee"),
                # Keep the complete structured source of truth.  The legacy
                # scalar remains above for old consumers and cached fixtures.
                # Preserve both values and field presence. In pm_fees an absent
                # fee descriptor is unknown, while an explicitly supplied
                # legacy null can mean fee-free; manufacturing null keys here
                # would turn schema loss into a false executable edge.
                "fee_market": {
                    field: m[field] for field in (
                        "feesEnabled", "takerBaseFee", "feeSchedule",
                    ) if field in m
                },
            })
        if len(market_rows) < 2:
            continue
        multi_market_events += 1
        market_rows.sort(key=lambda r: r["end_dt"])

        # Check monotonicity: for semantic deadline i<j, yes[i] <= yes[j].
        # ONLY compare child questions with an identical proposition key and
        # DIFFERENT question-parsed deadlines. Gamma endDate is merely a loose
        # parsing hint: using it as the rung created the 2026-08-28 acquisition
        # false alert when unrelated company children had divergent metadata.
        # Same-deadline markets are usually categorical/threshold (e.g.
        # "temperature above X°F today" or "BTC above Y on date Z" with
        # different thresholds) — NOT monotonic arbs.
        date_rows = sorted(
            (r for r in market_rows if r["date_key"] and r["deadline_dt"]),
            key=lambda r: r["deadline_dt"],
        )
        for i in range(len(date_rows)):
            for j in range(i + 1, len(date_rows)):
                if date_rows[i]["date_key"] != date_rows[j]["date_key"]:
                    continue  # different proposition/entity: never comparable
                if date_rows[i]["date_rules_key"] != date_rows[j]["date_rules_key"]:
                    continue  # same words can still have different payout rules
                if date_rows[i]["deadline_dt"] >= date_rows[j]["deadline_dt"]:
                    continue  # not a proper monotonic pair
                # Heuristic: require event title to contain a "by ___" pattern
                # (the placeholder for date variability). Otherwise might still
                # be categorical even with different dates (e.g. event spanning
                # multiple weekly games has different end dates but isn't monotonic).
                title_low = (ev.get("title") or "").lower()
                if " by " not in title_low and "before " not in title_low:
                    continue
                # PER-DAY exclusion (2026-08-08): "by <TIME>" is a time-of-day
                # bar on INDEPENDENT days, not a cumulative date series — e.g.
                # "full lid by 6:30 PM" for Aug-10 vs Aug-11 are separate daily
                # events with no monotonicity constraint (Monday's probability
                # may legitimately exceed Tuesday's). The scan's first daemon
                # fire was exactly this false positive (+41.5pp "violation").
                # Same root as Montana-dedup: a grouping heuristic treating a
                # non-fungible structure as fungible.
                import re as _re
                if _re.search(r"by \d{1,2}(:\d{2})?\s*(am|pm)", title_low):
                    continue
                # Liquidity gate: a leg with ~no recent volume has a STALE gamma
                # midpoint (sits between a stub bid and no real ask), so the
                # "violation" is an artifact, not an executable arb. Require both
                # legs to have real 24h volume. (Lesson 2026-06-02: "Propr launch
                # a token" flagged +37.5pp but the t2 leg had $0 vol24hr — stub.)
                if (date_rows[i]["vol24hr"] < args.min_leg_vol24 or
                        date_rows[j]["vol24hr"] < args.min_leg_vol24):
                    continue
                vt1 = date_rows[i]["yes"]
                vt2 = date_rows[j]["yes"]
                violation_pp = (vt1 - vt2) * 100
                if violation_pp < args.min_violation_pp:
                    continue
                # arb math: spread yes_t1 - yes_t2, vs fee breakeven
                breakeven = fee_aware_breakeven(vt1, vt2,
                                               date_rows[i]["fee_market"],
                                               date_rows[j]["fee_market"])
                spread = (vt1 - vt2) - breakeven
                violations.append({
                    "event_title": ev.get("title", "?"),
                    "event_slug": ev.get("slug", "?"),
                    "t1_question": date_rows[i]["question"],
                    "t1_slug": date_rows[i]["slug"],
                    "t1_end": date_rows[i]["deadline_dt"].strftime("%Y-%m-%d"),
                    "t1_yes": vt1,
                    "t2_question": date_rows[j]["question"],
                    "t2_slug": date_rows[j]["slug"],
                    "t2_end": date_rows[j]["deadline_dt"].strftime("%Y-%m-%d"),
                    "t2_yes": vt2,
                    "violation_pp": round(violation_pp, 2),
                    "breakeven_pp": round(breakeven * 100, 2),
                    "net_spread_pp": round(spread * 100, 2),
                    "t1_vol24hr": round(date_rows[i]["vol24hr"], 0),
                    "t2_vol24hr": round(date_rows[j]["vol24hr"], 0),
                    # row refs for the live-CLOB validation pass (i=earlier, j=later)
                    "_row_early": date_rows[i],
                    "_row_late": date_rows[j],
                })

        # THRESHOLD-LADDER pass (2026-08-10). The date pass above deliberately
        # skips same-date families, and its comment called them "categorical/
        # threshold ... NOT monotonic arbs". That is half wrong, and the wrong
        # half is large: a THRESHOLD ladder is exactly as monotone as a date
        # ladder. For thresholds k1 < k2, P(X >= k2) <= P(X >= k1), and the arb
        # construction is identical with "harder bar" playing the role of
        # "earlier date". Polymarket runs these constantly — score ladders
        # (HLE 50/55/60/65/70), BTC price ladders, vote-share, temperature —
        # so the scanner was structurally blind to a whole population it had
        # the machinery to check. Found while pricing the HLE family, whose own
        # ladder showed a (sub-spread) inversion at the 65/70 rungs.
        same_day = len({r["end_dt"].date() for r in market_rows}) == 1
        parsed = [(r, _parse_threshold_detail(r["question"])) for r in market_rows]
        # Every child must parse, but parsing a number does not establish that
        # the children measure the same thing. Group by the complete child
        # proposition with only its comparator span replaced, plus identical
        # payout-rule templates. This is the threshold analogue of the
        # acquisition-event date false positive fixed above.
        groups: dict[tuple, list[tuple[dict, float, int]]] = {}
        if same_day and all(t is not None for _, t in parsed):
            for row, detail in parsed:
                assert detail is not None
                value, direction, template, dimension = detail
                key = (template, direction, dimension, row["date_rules_key"])
                groups.setdefault(key, []).append((row, value, direction))

        for rungs in groups.values():
            if len(rungs) < 2 or len({v for _, v, _ in rungs}) != len(rungs):
                continue
            direction = rungs[0][2]
            # Order by DIFFICULTY: hardest bar first. For a ">=" ladder the
            # hardest is the largest value; for "<=" it is the smallest.
            rungs.sort(key=lambda x: x[1], reverse=(direction > 0))
            for i in range(len(rungs)):
                for j in range(i + 1, len(rungs)):
                    hard_row, hard_v, _ = rungs[i]
                    easy_row, easy_v, _ = rungs[j]
                    if (hard_row["vol24hr"] < args.min_leg_vol24 or
                            easy_row["vol24hr"] < args.min_leg_vol24):
                        continue
                    # The HARDER bar must not price above the EASIER one.
                    vt1, vt2 = hard_row["yes"], easy_row["yes"]
                    violation_pp = (vt1 - vt2) * 100
                    if violation_pp < args.min_violation_pp:
                        continue
                    breakeven = fee_aware_breakeven(vt1, vt2,
                                               hard_row["fee_market"],
                                               easy_row["fee_market"])
                    violations.append({
                        "event_title": ev.get("title", "?"),
                        "event_slug": ev.get("slug", "?"),
                        "kind": "threshold",
                        "t1_question": hard_row["question"],
                        "t1_slug": hard_row["slug"],
                        "t1_end": f"bar>={hard_v}" if direction > 0 else f"bar<={hard_v}",
                        "t1_yes": vt1,
                        "t2_question": easy_row["question"],
                        "t2_slug": easy_row["slug"],
                        "t2_end": f"bar>={easy_v}" if direction > 0 else f"bar<={easy_v}",
                        "t2_yes": vt2,
                        "violation_pp": round(violation_pp, 2),
                        "breakeven_pp": round(breakeven * 100, 2),
                        "net_spread_pp": round(((vt1 - vt2) - breakeven) * 100, 2),
                        "t1_vol24hr": round(hard_row["vol24hr"], 0),
                        "t2_vol24hr": round(easy_row["vol24hr"], 0),
                        # same role mapping as the date pass: _row_early is the
                        # leg that SHOULD carry the lower YES.
                        "_row_early": hard_row,
                        "_row_late": easy_row,
                    })

    # Sort by net_spread_pp desc (largest profit first)
    violations.sort(key=lambda v: -v["net_spread_pp"])

    # LIVE-CLOB VALIDATION (2026-07-23): walk real books on each mid-flagged
    # violation — the midpoint spread is NOT executable. Keep the mid-flag as
    # a candidate list but split REAL (executable arb after fees) from ARTIFACT.
    n_mid = len(violations)
    real = []
    for v in violations:
        ex = _executable_monotonic_arb(v["_row_early"], v["_row_late"])
        if ex is not None:
            v["executable"] = ex
            if ex["exec_edge_pp"] > 0:
                real.append(v)
    for v in violations:
        v.pop("_row_early", None); v.pop("_row_late", None)

    if args.json:
        print(json.dumps({"violations": violations, "real_executable": real,
                          "events_inspected": multi_market_events}, indent=2))
        return 0

    print(f"\n# {multi_market_events} multi-market events inspected; {n_mid} midpoint violation(s) >= {args.min_violation_pp}pp; "
          f"{len(real)} REAL after live-CLOB walk\n")
    if not violations:
        print("(no violations)")
        return 0
    print(f"{'event_title':<44} {'t1':<11} {'t2':<11} {'mid_gross':<9} {'EXEC_edge':<9} {'verdict'}")
    print("-" * 110)
    for v in violations[:30]:
        ex = v.get("executable")
        exec_s = f"{ex['exec_edge_pp']:>+6.2f}pp" if ex else "  n/a  "
        verdict = ("REAL ARB" if ex and ex["exec_edge_pp"] > 0
                   else "ARTIFACT (mid-only)" if ex else "no book")
        print(f"{v['event_title'][:44]:<44} {v['t1_end']:<11} {v['t2_end']:<11} "
              f"{v['violation_pp']:>+6.2f}pp {exec_s:<9} {verdict}")
    if not real:
        print("\n# 0 REAL executable arbs — all midpoint flags evaporated on live books (the usual outcome).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
