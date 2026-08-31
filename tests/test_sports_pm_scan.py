from __future__ import annotations

import datetime
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sports_pm_scan  # noqa: E402


NOW = datetime.datetime(2026, 8, 31, 14, 0, tzinfo=datetime.timezone.utc)


def test_is_in_play_after_gamma_start() -> None:
    market = {"gameStartTime": "2026-08-31 13:30:00+00"}
    assert sports_pm_scan.is_in_play(market, NOW) is True


def test_is_in_play_false_before_start() -> None:
    market = {"gameStartTime": "2026-09-01T08:00:00Z"}
    assert sports_pm_scan.is_in_play(market, NOW) is False


def test_is_in_play_fails_open_for_missing_or_malformed_metadata() -> None:
    assert sports_pm_scan.is_in_play({}, NOW) is False
    assert sports_pm_scan.is_in_play({"gameStartTime": "not-a-time"}, NOW) is False


def test_is_in_play_normalizes_naive_start_and_now() -> None:
    naive_now = datetime.datetime(2026, 8, 31, 14, 0)
    market = {"gameStartTime": "2026-08-31 13:30:00"}
    assert sports_pm_scan.is_in_play(market, naive_now) is True
