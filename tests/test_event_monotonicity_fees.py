"""Focused regression coverage for event scanner fee routing."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import event_monotonicity_scan as scanner  # noqa: E402


def _market(slug: str, bar: int, yes: float, fee_schedule: dict | None) -> dict:
    return {
        "id": slug,
        "slug": slug,
        "question": f"Will the result be {bar} or higher?",
        "outcomes": json.dumps(["Yes", "No"]),
        "outcomePrices": json.dumps([yes, 1.0 - yes]),
        "endDate": "2026-09-20T00:00:00Z",
        "volume24hr": 1_000,
        "clobTokenIds": json.dumps([f"{slug}-yes", f"{slug}-no"]),
        "takerBaseFee": 1000 if fee_schedule is not None else None,
        "feeSchedule": fee_schedule,
    }


def _date_market(
    slug: str, question: str, end_date: str, yes: float, description: str = "",
) -> dict:
    return {
        "id": slug,
        "slug": slug,
        "question": question,
        "outcomes": json.dumps(["Yes", "No"]),
        "outcomePrices": json.dumps([yes, 1.0 - yes]),
        "endDate": end_date,
        "volume24hr": 1_000,
        "clobTokenIds": json.dumps([f"{slug}-yes", f"{slug}-no"]),
        "takerBaseFee": None,
        "feeSchedule": None,
        "description": description,
    }


def test_breakeven_accepts_full_gamma_fee_curves_and_legacy_scalars() -> None:
    structured = {
        "takerBaseFee": 1000,
        "feeSchedule": {"rate": 0.25, "exponent": 2, "takerOnly": False},
    }
    free = {"takerBaseFee": None, "feeSchedule": None}

    assert scanner.fee_aware_breakeven(0.5, 0.4, structured, free) == 0.25 * 0.25**2
    # Preserve the public legacy call shape and its explicit-zero semantics.
    assert scanner.fee_aware_breakeven(0.5, 0.5, 1000, None) == 0.07 * 0.25


def test_live_clob_validation_uses_each_rows_full_fee_schedule(monkeypatch) -> None:
    timestamp = datetime(2026, 8, 28, tzinfo=timezone.utc)
    books = {
        "101": {
            "asks": [(Decimal("0.40"), Decimal("5"))],
            "bids": [],
            "min_order_size": Decimal("5"),
            "timestamp": timestamp,
        },
        "202": {
            "asks": [(Decimal("0.70"), Decimal("5"))],
            "bids": [],
            "min_order_size": Decimal("5"),
            "timestamp": timestamp,
        },
    }
    monkeypatch.setattr(
        scanner, "_fetch_validated_clob_book", lambda token, _condition: books[token],
    )
    row_late = {
        "outcomes": json.dumps(["Yes", "No"]),
        "clob_tokens": json.dumps(["101", "102"]),
        "condition_id": "late-condition",
        "order_min_size": 5,
        "taker_fee_bps": 1000,
        "fee_market": {
            "takerBaseFee": 1000,
            "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True},
        },
    }
    row_early = {
        "outcomes": json.dumps(["Yes", "No"]),
        "clob_tokens": json.dumps(["201", "202"]),
        "condition_id": "early-condition",
        "order_min_size": 5,
        "taker_fee_bps": 1000,
        "fee_market": {
            "takerBaseFee": 1000,
            "feeSchedule": {"rate": 0.25, "exponent": 2, "takerOnly": False},
        },
    }

    result = scanner._executable_monotonic_arb(row_early, row_late)

    expected = 0.04 * (0.4 * 0.6) + 0.25 * (0.7 * 0.3) ** 2
    assert result is not None
    assert result["fee"] == round(expected, 4)
    assert result["exec_cost"] == round(0.4 + 0.7 + expected, 4)


def test_threshold_group_key_preserves_dimension_and_rejects_ambiguous_suffix() -> None:
    usd_m = scanner._parse_threshold_detail("Will Alpha be $50M or higher?")
    usd_b = scanner._parse_threshold_detail("Will Alpha be $1B or higher?")
    percent = scanner._parse_threshold_detail("Will Alpha be 20% or higher?")
    fahrenheit = scanner._parse_threshold_detail("Will Alpha be 50°F or higher?")
    celsius = scanner._parse_threshold_detail("Will Alpha be 20°C or higher?")

    assert usd_m is not None and usd_b is not None and percent is not None
    assert usd_m[2:] == usd_b[2:] == ("will alpha be <threshold> ?", "usd")
    assert percent[3] == "percent"
    assert fahrenheit is not None and celsius is not None
    assert fahrenheit[3] == "fahrenheit"
    assert celsius[3] == "celsius"
    assert scanner._parse_threshold_detail("Will Alpha be 50m or higher?") is None


def test_threshold_pass_never_groups_currency_with_percent(monkeypatch, capsys) -> None:
    dollars = _market("alpha-usd", 50, 0.80, None)
    dollars["question"] = "Will Alpha be $50 or higher?"
    percent = _market("alpha-percent", 20, 0.10, None)
    percent["question"] = "Will Alpha be 20% or higher?"
    event = {
        "id": "mixed-dimensions",
        "slug": "mixed-dimensions",
        "title": "Alpha thresholds",
        "markets": [dollars, percent],
    }
    monkeypatch.setattr(scanner, "fetch_events", lambda **_kwargs: [event])
    monkeypatch.setattr(
        scanner,
        "_executable_monotonic_arb",
        lambda *_args: pytest.fail("different dimensions reached live-book validation"),
    )
    monkeypatch.setattr(sys, "argv", ["event_monotonicity_scan.py", "--json"])

    assert scanner.main() == 0
    assert json.loads(capsys.readouterr().out)["violations"] == []


def test_executable_walk_uses_named_tokens_common_size_and_full_depth(monkeypatch) -> None:
    timestamp = datetime(2026, 8, 28, tzinfo=timezone.utc)
    books = {
        # Late outcomes are reversed below; token 101 is still named YES.
        "101": {
            "asks": [(Decimal("0.50"), Decimal("3")),
                     (Decimal("0.40"), Decimal("2")),
                     (Decimal("0.55"), Decimal("1"))],
            "bids": [],
            "min_order_size": Decimal("5"),
            "timestamp": timestamp,
        },
        # Early outcomes are reversed; token 202 is named NO.
        "202": {
            "asks": [(Decimal("0.30"), Decimal("6"))],
            "bids": [],
            "min_order_size": Decimal("6"),
            "timestamp": timestamp,
        },
    }
    calls = []

    def fetch(token, condition):
        calls.append((token, condition))
        return books[token]

    monkeypatch.setattr(scanner, "_fetch_validated_clob_book", fetch)
    free = {"feesEnabled": False}
    late = {
        "outcomes": json.dumps(["No", "Yes"]),
        "clob_tokens": json.dumps(["102", "101"]),
        "condition_id": "late-condition",
        "order_min_size": 5,
        "fee_market": free,
    }
    early = {
        "outcomes": json.dumps(["No", "Yes"]),
        "clob_tokens": json.dumps(["202", "201"]),
        "condition_id": "early-condition",
        "order_min_size": 5,
        "fee_market": free,
    }

    result = scanner._executable_monotonic_arb(early, late)

    assert result is not None
    assert calls == [("101", "late-condition"), ("202", "early-condition")]
    assert result["comparison_size"] == 6.0
    assert result["late_yes_ask"] == pytest.approx((2 * .40 + 3 * .50 + 1 * .55) / 6)
    assert result["early_no_ask"] == pytest.approx(.30)
    assert result["late_yes_walk"]["fills"] == [
        {"price": .4, "size": 2.0, "fee": 0.0},
        {"price": .5, "size": 3.0, "fee": 0.0},
        {"price": .55, "size": 1.0, "fee": 0.0},
    ]


def test_executable_walk_rejects_dust_and_unknown_fee_metadata(monkeypatch) -> None:
    timestamp = datetime(2026, 8, 28, tzinfo=timezone.utc)
    dust = {
        "asks": [(Decimal("0.10"), Decimal("0.01"))],
        "bids": [],
        "min_order_size": Decimal("5"),
        "timestamp": timestamp,
    }
    deep = {
        "asks": [(Decimal("0.10"), Decimal("5"))],
        "bids": [],
        "min_order_size": Decimal("5"),
        "timestamp": timestamp,
    }
    books = {"101": dust, "202": deep}
    monkeypatch.setattr(
        scanner, "_fetch_validated_clob_book", lambda token, _condition: books[token],
    )
    base = {
        "outcomes": json.dumps(["Yes", "No"]),
        "condition_id": "condition",
        "order_min_size": 5,
        "fee_market": {"feesEnabled": False},
    }
    late = {**base, "clob_tokens": json.dumps(["101", "102"])}
    early = {**base, "clob_tokens": json.dumps(["201", "202"])}
    assert scanner._executable_monotonic_arb(early, late) is None

    books["101"] = deep
    late["fee_market"] = {
        "feesEnabled": True,
        "takerBaseFee": None,
        "feeSchedule": None,
    }
    assert scanner._executable_monotonic_arb(early, late) is None


def test_main_preserves_unknown_fee_field_presence(monkeypatch, capsys) -> None:
    easy = _market("easy-fee", 10, 0.20, None)
    hard = _market("hard-fee", 20, 0.80, None)
    for market in (easy, hard):
        market["feesEnabled"] = True
        market["takerBaseFee"] = None
        market["feeSchedule"] = None
    event = {
        "id": "unknown-fee",
        "slug": "unknown-fee",
        "title": "Unknown fee threshold",
        "markets": [easy, hard],
    }
    captured = []
    monkeypatch.setattr(scanner, "fetch_events", lambda **_kwargs: [event])
    monkeypatch.setattr(
        scanner,
        "_executable_monotonic_arb",
        lambda early, late: captured.extend([early, late]) or None,
    )
    monkeypatch.setattr(sys, "argv", ["event_monotonicity_scan.py", "--json"])

    assert scanner.main() == 0
    capsys.readouterr()
    assert len(captured) == 2
    for row in captured:
        assert row["fee_market"] == {
            "feesEnabled": True,
            "takerBaseFee": None,
            "feeSchedule": None,
        }
        assert scanner._known_fee_market(row["fee_market"]) is False


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.update({"asset_id": "999"}),
        lambda payload: payload.update({"market": "foreign"}),
        lambda payload: payload.update({
            "timestamp": str(int(datetime(2026, 8, 27, tzinfo=timezone.utc).timestamp() * 1000)),
        }),
        lambda payload: payload["asks"].append({"price": "0.30", "size": "1"}),
    ],
)
def test_clob_book_identity_freshness_and_integrity_fail_closed(mutation) -> None:
    now = datetime(2026, 8, 28, tzinfo=timezone.utc)
    payload = {
        "asset_id": "101",
        "market": "condition",
        "timestamp": str(int(now.timestamp() * 1000)),
        "min_order_size": "5",
        "bids": [{"price": "0.30", "size": "5"}],
        "asks": [{"price": "0.40", "size": "5"}],
    }
    assert scanner._validated_clob_book(
        payload, token_id="101", condition_id="condition", now=now,
    ) is not None
    mutation(payload)
    assert scanner._validated_clob_book(
        payload, token_id="101", condition_id="condition", now=now,
    ) is None


def test_threshold_pass_uses_sorted_hard_and_easy_rows_for_fees(
    monkeypatch, capsys,
) -> None:
    # Deliberately scramble source order.  The historical bug sorted by bar but
    # then indexed this original list for fees, assigning unrelated rung fees.
    easy = _market("easy", 10, 0.20, None)
    hard = _market("hard", 30, 0.60,
                   {"rate": 0.04, "exponent": 1, "takerOnly": True})
    middle = _market("middle", 20, 0.40,
                     {"rate": 0.25, "exponent": 2, "takerOnly": False})
    event = {
        "id": "ladder",
        "slug": "ladder",
        "title": "Threshold ladder",
        "markets": [easy, hard, middle],
    }
    monkeypatch.setattr(scanner, "fetch_events", lambda **_kwargs: [event])
    monkeypatch.setattr(scanner, "_executable_monotonic_arb", lambda *_args: None)
    monkeypatch.setattr(sys, "argv", ["event_monotonicity_scan.py", "--json"])

    assert scanner.main() == 0
    payload = json.loads(capsys.readouterr().out)
    hard_easy = next(
        v for v in payload["violations"]
        if v["t1_slug"] == "hard" and v["t2_slug"] == "easy"
    )
    expected_fee = 0.04 * (0.60 * 0.40)  # easy is explicitly fee-free
    assert hard_easy["breakeven_pp"] == round(expected_fee * 100, 2)
    assert hard_easy["net_spread_pp"] == round((0.60 - 0.20 - expected_fee) * 100, 2)


def test_threshold_pass_groups_by_child_proposition_not_event_membership(
    monkeypatch, capsys,
) -> None:
    alpha_easy = _market("alpha-easy", 10, 0.20, None)
    alpha_easy["question"] = "Will Alpha score 10 or higher?"
    alpha_hard = _market("alpha-hard", 30, 0.60, None)
    alpha_hard["question"] = "Will Alpha score 30 or higher?"
    beta = _market("beta", 20, 0.90, None)
    beta["question"] = "Will Beta score 20 or higher?"
    event = {
        "id": "mixed-thresholds",
        "slug": "mixed-thresholds",
        "title": "Who will clear their score threshold?",
        "markets": [alpha_easy, beta, alpha_hard],
    }
    monkeypatch.setattr(scanner, "fetch_events", lambda **_kwargs: [event])
    monkeypatch.setattr(scanner, "_executable_monotonic_arb", lambda *_args: None)
    monkeypatch.setattr(sys, "argv", ["event_monotonicity_scan.py", "--json"])

    assert scanner.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["violations"]) == 1
    assert payload["violations"][0]["t1_slug"] == "alpha-hard"
    assert payload["violations"][0]["t2_slug"] == "alpha-easy"


def test_date_parser_uses_question_deadline_not_divergent_gamma_metadata() -> None:
    end = datetime(2027, 1, 1, tzinfo=timezone.utc)
    wbd = scanner.parse_date_ladder_question(
        "Will Warner Bros. Discovery be acquired before 2027?", end,
    )
    paypal = scanner.parse_date_ladder_question(
        "Will PayPal be acquired before 2027?", end,
    )

    assert wbd is not None and paypal is not None
    assert wbd[1].isoformat() == "2027-01-01"
    assert paypal[1].isoformat() == "2027-01-01"
    assert wbd[0] != paypal[0]


def test_date_parser_rejects_yearless_and_inconsistent_gamma_dates() -> None:
    assert scanner.parse_date_ladder_question(
        "Will Ink launch a token by March 31?",
        datetime(2027, 4, 1, tzinfo=timezone.utc),
    ) is None
    assert scanner.parse_date_ladder_question(
        "Will Ink launch a token by March 31, 2027?",
        datetime(2028, 4, 1, tzinfo=timezone.utc),
    ) is None


def test_date_pass_rejects_different_entities_inside_one_category_event(
    monkeypatch, capsys,
) -> None:
    # This models the 2026-08-28 false fire. Gamma temporarily exposed a
    # one-day endDate difference among acquisition children. They are neither
    # different deadlines (the questions both say before 2027) nor the same
    # proposition (WBD vs PayPal), regardless of their executable books.
    event = {
        "id": "acquisitions",
        "slug": "which-companies-will-be-acquired-before-2027",
        "title": "Which companies will be acquired before 2027?",
        "markets": [
            _date_market(
                "wbd", "Will Warner Bros. Discovery be acquired before 2027?",
                "2026-12-31T00:00:00Z", 0.95,
            ),
            _date_market(
                "paypal", "Will PayPal be acquired before 2027?",
                "2027-01-01T04:59:00Z", 0.10,
            ),
        ],
    }
    monkeypatch.setattr(scanner, "fetch_events", lambda **_kwargs: [event])
    monkeypatch.setattr(
        scanner,
        "_executable_monotonic_arb",
        lambda *_args: pytest.fail("unrelated acquisition markets reached book walk"),
    )
    monkeypatch.setattr(sys, "argv", ["event_monotonicity_scan.py", "--json"])

    assert scanner.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["violations"] == []
    assert payload["real_executable"] == []


def test_date_pass_keeps_true_same_proposition_ladder(monkeypatch, capsys) -> None:
    event = {
        "id": "ink",
        "slug": "will-ink-launch-a-token-by",
        "title": "Will Ink launch a token by ___?",
        "markets": [
            _date_market(
                "ink-sep", "Will Ink launch a token by September 30, 2026?",
                "2026-10-01T00:00:00Z", 0.70,
            ),
            _date_market(
                "ink-dec", "Will Ink launch a token by December 31, 2026?",
                "2027-01-01T00:00:00Z", 0.20,
            ),
        ],
    }
    monkeypatch.setattr(scanner, "fetch_events", lambda **_kwargs: [event])
    monkeypatch.setattr(scanner, "_executable_monotonic_arb", lambda *_args: None)
    monkeypatch.setattr(sys, "argv", ["event_monotonicity_scan.py", "--json"])

    assert scanner.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["violations"]) == 1
    violation = payload["violations"][0]
    assert violation["t1_slug"] == "ink-sep"
    assert violation["t2_slug"] == "ink-dec"
    assert violation["t1_end"] == "2026-09-30"
    assert violation["t2_end"] == "2026-12-31"


def test_date_pass_rejects_rule_template_mismatch(monkeypatch, capsys) -> None:
    event = {
        "id": "ink-rules",
        "slug": "will-ink-launch-a-token-by",
        "title": "Will Ink launch a token by ___?",
        "markets": [
            _date_market(
                "ink-sep", "Will Ink launch a token by September 30, 2026?",
                "2026-10-01T00:00:00Z", 0.70,
                "An announcement counts.",
            ),
            _date_market(
                "ink-dec", "Will Ink launch a token by December 31, 2026?",
                "2027-01-01T00:00:00Z", 0.20,
                "The token must be publicly tradable; announcements do not count.",
            ),
        ],
    }
    monkeypatch.setattr(scanner, "fetch_events", lambda **_kwargs: [event])
    monkeypatch.setattr(
        scanner,
        "_executable_monotonic_arb",
        lambda *_args: pytest.fail("rule-mismatched markets reached book walk"),
    )
    monkeypatch.setattr(sys, "argv", ["event_monotonicity_scan.py", "--json"])

    assert scanner.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["violations"] == []
