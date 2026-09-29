from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import aave_deposit  # noqa: E402


def _reserve(*, active: bool = True, frozen: bool = False,
             paused: bool = False):
    raw = ((int(active) << 56) | (int(frozen) << 57)
           | (int(paused) << 60))
    return [(raw,)]


def test_reserve_supply_status_decodes_live_and_closed_states() -> None:
    assert aave_deposit._reserve_supply_status(_reserve()) == (True, "live")
    assert aave_deposit._reserve_supply_status(
        _reserve(frozen=True)) == (False, "frozen")
    assert aave_deposit._reserve_supply_status(
        _reserve(paused=True)) == (False, "paused")
    assert aave_deposit._reserve_supply_status(
        _reserve(active=False)) == (False, "inactive")
