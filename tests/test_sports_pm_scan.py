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


def test_consensus_freshness_accepts_recent_timestamp() -> None:
    row = {
        "yes_prob": 0.6,
        "source": "live book",
        "source_url": "https://example.com/live-odds",
        "source_at": "2026-08-31T10:00:00Z",
    }

    assert sports_pm_scan.validate_consensus_freshness(
        row, 24, now=NOW
    ) == row


def test_consensus_freshness_rejects_old_near_deadline_article() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        {"yes_prob": 0.6, "source_url": "https://example.com/odds",
         "source_at": "2026-08-25T10:00:00Z"},
        14,
        now=NOW,
    )

    assert "stale" in result["error"]


def test_consensus_freshness_requires_verifiable_timestamp() -> None:
    assert "source_at" in sports_pm_scan.validate_consensus_freshness(
        {"yes_prob": 0.6, "source_url": "https://example.com/odds"},
        36, now=NOW
    )["error"]


def test_consensus_freshness_requires_auditable_url() -> None:
    assert "source_url" in sports_pm_scan.validate_consensus_freshness(
        {"yes_prob": 0.6, "source_at": "2026-08-31T10:00:00Z"},
        36, now=NOW
    )["error"]


def test_consensus_freshness_rejects_relabelled_dated_article() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        {
            "yes_prob": 0.6,
            "source_url": "https://example.com/insight/20260825-old-odds",
            "source_at": "2026-09-01T09:00:00Z",
        },
        14,
        now=datetime.datetime(2026, 9, 1, 14, tzinfo=datetime.timezone.utc),
    )

    assert "conflicts" in result["error"]


def test_consensus_error_passthrough_needs_no_timestamp() -> None:
    error = {"error": "no book"}
    assert sports_pm_scan.validate_consensus_freshness(error, 36, now=NOW) == error
