"""Focused tests for resting_watch policy gates (no network, no orders)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "resting_watch", REPO / "scripts" / "resting_watch.py")
rw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rw)


def _rest(**over):
    base = {
        "slug": "s", "asset": "1", "side": "SELL", "shares": 5,
        "min_price": 0.9, "premium_pp": 0.05,
        "justification": "test", "alert_keys": [], "enabled": True,
    }
    base["class"] = over.pop("cls", "hidden")
    base.update(over)
    return base


def test_hidden_rest_above_fair_plus_premium_passes():
    assert rw.validate_rest(_rest(), fair=0.385) == []


def test_hidden_rest_below_fair_plus_premium_rejected():
    problems = rw.validate_rest(_rest(min_price=0.40), fair=0.385)
    assert any("hidden-info" in p for p in problems)


def test_ordinary_rest_below_fair_rejected():
    problems = rw.validate_rest(_rest(cls="ordinary", min_price=0.55), fair=0.60)
    assert any("below fair" in p for p in problems)


def test_ordinary_rest_at_or_above_fair_passes():
    assert rw.validate_rest(_rest(cls="ordinary", min_price=0.65), fair=0.60) == []


def test_missing_justification_rejected():
    problems = rw.validate_rest(_rest(justification=""), fair=0.385)
    assert any("justification" in p for p in problems)


def test_buy_side_rejected_in_v1():
    problems = rw.validate_rest(_rest(side="BUY"), fair=0.385)
    assert any("SELL only" in p for p in problems)


def test_missing_fair_rejected():
    problems = rw.validate_rest(_rest(), fair=None)
    assert any("no fair" in p for p in problems)


def test_nonpositive_shares_rejected():
    problems = rw.validate_rest(_rest(shares=0), fair=0.385)
    assert any("shares" in p for p in problems)
