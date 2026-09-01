from __future__ import annotations

import math
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import positions  # noqa: E402
import bankroll  # noqa: E402


def test_resolved_winner_is_realizable_at_fee_free_payout() -> None:
    assert positions.resolved_realizable_value(
        {"redeemable": True, "curPrice": 1, "size": "12.5"}
    ) == 12.5


def test_resolved_loser_has_zero_realizable_value() -> None:
    assert positions.resolved_realizable_value(
        {"redeemable": True, "curPrice": 0, "size": 31}
    ) == 0


def test_active_or_malformed_row_stays_on_book_walk_path() -> None:
    assert positions.resolved_realizable_value(
        {"redeemable": False, "curPrice": 1, "size": 12}
    ) is None
    assert positions.resolved_realizable_value(
        {"redeemable": True, "curPrice": "bad", "size": 12}
    ) is None
    assert positions.resolved_realizable_value(
        {"redeemable": True, "curPrice": 1, "size": math.nan}
    ) is None


def test_bankroll_basis_excludes_final_rows_from_unrealized_split() -> None:
    rows = [
        {"initialValue": 10, "currentValue": 12, "redeemable": False},
        {"initialValue": 5, "currentValue": 0, "redeemable": True},
        {"initialValue": 4, "currentValue": 10, "redeemable": True},
    ]

    assert bankroll.active_pm_basis(rows) == (10, 12)
