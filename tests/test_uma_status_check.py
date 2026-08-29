"""Regressions for directional UMA price-move reporting."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import uma_status_check as uma  # noqa: E402


def test_yes_price_move_message_preserves_direction() -> None:
    assert "(-7.2pp)" in uma._yes_price_move_message(0.835, 0.763)
    assert "(+7.2pp)" in uma._yes_price_move_message(0.763, 0.835)
