"""Focused regression coverage for event scanner fee routing."""

from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import event_monotonicity_scan as scanner  # noqa: E402


def _market(slug: str, bar: int, yes: float, fee_schedule: dict | None) -> dict:
    return {
        "id": slug,
        "slug": slug,
        "question": f"Will the result be {bar} or higher?",
        "outcomePrices": json.dumps([yes, 1.0 - yes]),
        "endDate": "2026-09-20T00:00:00Z",
        "volume24hr": 1_000,
        "clobTokenIds": json.dumps([f"{slug}-yes", f"{slug}-no"]),
        "takerBaseFee": 1000 if fee_schedule is not None else None,
        "feeSchedule": fee_schedule,
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
    asks = {"late-yes": 0.40, "early-no": 0.70}
    monkeypatch.setattr(scanner, "_best_ask", asks.__getitem__)
    row_late = {
        "clob_tokens": json.dumps(["late-yes", "late-no"]),
        "taker_fee_bps": 1000,
        "fee_market": {
            "takerBaseFee": 1000,
            "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True},
        },
    }
    row_early = {
        "clob_tokens": json.dumps(["early-yes", "early-no"]),
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
