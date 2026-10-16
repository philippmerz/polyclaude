from __future__ import annotations

import datetime
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sports_pm_scan  # noqa: E402


NOW = datetime.datetime(2026, 8, 31, 14, 0, tzinfo=datetime.timezone.utc)
FULHAM_CONTEXT = {
    "question": "Will Fulham win on 2026-10-17?",
    "description": "Fulham versus Hull; first 90 minutes plus stoppage. Otherwise NO, including draw.",
    "sportsMarketType": "moneyline",
    "outcomes": ["Yes", "No"],
}


def valid_payload(**overrides):
    payload = {
        "source_type": "bookmaker_decimal_odds",
        "bookmaker": "Example Sportsbook",
        "source_url": "https://example.com/live-odds",
        "source_at": "2026-08-31T10:00:00Z",
        "market_type": "1x2",
        "decimal_odds": [
            {"outcome": "Fulham", "odds": 1.9, "bookmaker": "Example Sportsbook"},
            {"outcome": "Draw", "odds": 3.4, "bookmaker": "Example Sportsbook"},
            {"outcome": "Hull", "odds": 4.5, "bookmaker": "Example Sportsbook"},
        ],
        "yes_outcomes": ["Fulham"],
        "mapping_note": "The contract resolves YES exactly if Fulham wins.",
        "confidence": "high",
        "note": "Prices and timestamp visible on the named-book page.",
    }
    payload.update(overrides)
    return payload


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
    assert sports_pm_scan.validate_consensus_freshness(
        valid_payload(), 24, now=NOW, expected_outcomes=["Yes", "No"],
        market_context=FULHAM_CONTEXT,
    )["yes_prob"] == (1 / 1.9) / ((1 / 1.9) + (1 / 3.4) + (1 / 4.5))


def test_consensus_freshness_rejects_old_near_deadline_article() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        valid_payload(source_at="2026-08-25T10:00:00Z"),
        14,
        now=NOW,
    )

    assert "stale" in result["error"]


def test_consensus_freshness_requires_verifiable_timestamp() -> None:
    assert "source_at" in sports_pm_scan.validate_consensus_freshness(
        valid_payload(source_at=None),
        36, now=NOW
    )["error"]


def test_consensus_freshness_requires_auditable_url() -> None:
    assert "source_url" in sports_pm_scan.validate_consensus_freshness(
        valid_payload(source_url=None),
        36, now=NOW
    )["error"]


def test_consensus_freshness_rejects_relabelled_dated_article() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        valid_payload(source_url="https://example.com/insight/20260825-old-odds",
                      source_at="2026-09-01T09:00:00Z"),
        14,
        now=datetime.datetime(2026, 9, 1, 14, tzinfo=datetime.timezone.utc),
    )

    assert "conflicts" in result["error"]


def test_consensus_error_passthrough_needs_no_timestamp() -> None:
    error = {"error": "no book"}
    assert sports_pm_scan.validate_consensus_freshness(error, 36, now=NOW) == error


def test_oddschecker_ai_probability_is_rejected_as_unverified_scalar() -> None:
    # Oddschecker Fulham page labels 53% as "AI Probability"; it is not a
    # named bookmaker's decimal-odds quote and cannot create consensus.
    result = sports_pm_scan.validate_consensus_freshness(
        {"yes_prob": 0.53, "source": "Oddschecker", "source_url": "https://example.com/oddschecker",
         "source_at": "2026-08-31T10:00:00Z", "ai_probability": 0.53},
        24, now=NOW,
    )
    assert "scalar/model" in result["error"]


def test_complete_1x2_odds_derive_yes_and_complementary_no() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        valid_payload(), 24, now=NOW, expected_outcomes=["Yes", "No"],
        market_context=FULHAM_CONTEXT,
    )
    expected = [(1 / 1.9), (1 / 3.4), (1 / 4.5)]
    total = sum(expected)
    assert result["yes_prob"] == expected[0] / total
    assert result["no_outcomes"] == ["Draw", "Hull"]
    assert math.isclose(sum(result["implied_probabilities"].values()), 1.0)
    assert result["bookmaker"] == "Example Sportsbook"
    assert len(result["decimal_odds"]) == 3


def test_missing_draw_in_1x2_market_is_rejected() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        valid_payload(decimal_odds=[{"outcome": "Fulham", "odds": 1.9, "bookmaker": "Example Sportsbook"},
                                    {"outcome": "Hull", "odds": 4.5, "bookmaker": "Example Sportsbook"}]),
        24, now=NOW, expected_outcomes=["Yes", "No"], market_context=FULHAM_CONTEXT,
    )
    assert "complete outcome odds" in result["error"]


def test_mixed_book_quotes_are_rejected() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        valid_payload(decimal_odds=[
            {"outcome": "Fulham", "odds": 1.9, "bookmaker": "Book A"},
            {"outcome": "Draw", "odds": 3.4, "bookmaker": "Book B"},
            {"outcome": "Hull", "odds": 4.5, "bookmaker": "Book A"},
        ]), 24, now=NOW, expected_outcomes=["Yes", "No"], market_context=FULHAM_CONTEXT,
    )
    assert "named bookmaker" in result["error"]


def test_model_probability_source_is_rejected() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        valid_payload(source_type="AI Probability"), 24, now=NOW,
    )
    assert "not identified" in result["error"]


def test_stale_capture_is_rejected_with_complete_odds() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        valid_payload(source_at="2026-08-30T10:00:00Z"), 14, now=NOW,
    )
    assert "stale" in result["error"]


def test_unknown_or_mismatched_market_type_is_rejected() -> None:
    unknown = sports_pm_scan.validate_consensus_freshness(
        valid_payload(market_type="moneyline"), 24, now=NOW,
        expected_outcomes=["Yes", "No"], market_context=FULHAM_CONTEXT,
    )
    mismatched = sports_pm_scan.validate_consensus_freshness(
        valid_payload(), 24, now=NOW, expected_outcomes=["Fulham", "Hull"]
    )
    assert "unsupported" in unknown["error"]
    assert "does not match" in mismatched["error"]


def test_binary_football_market_requires_verified_yes_team_and_no_draw_plus_opponent() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        valid_payload(), 24, now=NOW, expected_outcomes=["Yes", "No"],
        market_context=FULHAM_CONTEXT,
    )
    assert result["yes_outcomes"] == ["Fulham"]
    assert result["no_outcomes"] == ["Draw", "Hull"]

    unverified = sports_pm_scan.validate_consensus_freshness(
        valid_payload(), 24, now=NOW, expected_outcomes=["Yes", "No"],
        market_context={"question": "Who will win?", "description": "", "outcomes": ["Yes", "No"]},
    )
    assert "does not establish" in unverified["error"]


def test_non_finite_odds_are_rejected() -> None:
    for bad_price in (float("nan"), float("inf"), True):
        payload = valid_payload()
        payload["decimal_odds"][0]["odds"] = bad_price
        result = sports_pm_scan.validate_consensus_freshness(
            payload, 24, now=NOW, expected_outcomes=["Yes", "No"],
            market_context=FULHAM_CONTEXT,
        )
        assert "invalid" in result["error"]


def test_mocked_oddschecker_ai_worker_output_fails_closed(monkeypatch) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(
        sports_pm_scan,
        "run_agent",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stderr="",
            stdout='{"yes_prob":0.53,"source":"Oddschecker","source_url":"https://example.com/fulham","source_at":"2026-08-31T10:00:00Z","note":"AI Probability powered by oddschecker+"}',
        ),
    )
    result = sports_pm_scan.fetch_bookie_consensus(
        "Will Fulham beat Hull?", 24, outcomes=["Yes", "No"],
        market_context=FULHAM_CONTEXT,
    )
    assert "error" in result
    assert "yes_prob" not in result


def test_binary_football_cannot_be_downgraded_to_two_way(monkeypatch) -> None:
    payload = valid_payload(
        market_type="two_way",
        decimal_odds=[
            {"outcome": "Fulham", "odds": 1.9, "bookmaker": "Example Sportsbook"},
            {"outcome": "Hull", "odds": 4.5, "bookmaker": "Example Sportsbook"},
        ],
        yes_outcomes=["Fulham"],
    )
    result = sports_pm_scan.validate_consensus_freshness(
        payload, 24, now=NOW, expected_outcomes=["Yes", "No"],
        market_context=FULHAM_CONTEXT,
    )
    assert "does not match expected '1x2'" in result["error"]


def test_two_way_named_market_yes_must_match_first_gamma_outcome() -> None:
    payload = valid_payload(
        market_type="two_way",
        decimal_odds=[
            {"outcome": "Fulham", "odds": 1.9, "bookmaker": "Example Sportsbook"},
            {"outcome": "Hull", "odds": 2.1, "bookmaker": "Example Sportsbook"},
        ],
        yes_outcomes=["Hull"],
    )
    result = sports_pm_scan.validate_consensus_freshness(
        payload, 24, now=NOW, expected_outcomes=["Fulham", "Hull"],
    )
    assert "first Gamma market outcome" in result["error"]


def test_valid_two_way_spurs_first_team_mapping() -> None:
    payload = valid_payload(
        market_type="two_way",
        decimal_odds=[
            {"outcome": "Spurs", "odds": 2.1, "bookmaker": "Example Sportsbook"},
            {"outcome": "Thunder", "odds": 1.8, "bookmaker": "Example Sportsbook"},
        ],
        yes_outcomes=["Spurs"],
    )
    result = sports_pm_scan.validate_consensus_freshness(
        payload, 24, now=NOW, expected_outcomes=["Spurs", "Thunder"],
    )
    assert result["yes_outcomes"] == ["Spurs"]
    assert result["no_outcomes"] == ["Thunder"]


def test_named_three_way_inverted_yes_mapping_is_rejected() -> None:
    payload = valid_payload(yes_outcomes=["Hull"])
    result = sports_pm_scan.validate_consensus_freshness(
        payload, 24, now=NOW, expected_outcomes=["Fulham", "Draw", "Hull"],
    )
    assert "first Gamma 1x2 outcome" in result["error"]


def test_named_three_way_mismatched_book_outcomes_are_rejected() -> None:
    payload = valid_payload(decimal_odds=[
        {"outcome": "Fulham", "odds": 1.9, "bookmaker": "Example Sportsbook"},
        {"outcome": "Draw", "odds": 3.4, "bookmaker": "Example Sportsbook"},
        {"outcome": "Chelsea", "odds": 4.5, "bookmaker": "Example Sportsbook"},
    ])
    result = sports_pm_scan.validate_consensus_freshness(
        payload, 24, now=NOW, expected_outcomes=["Fulham", "Draw", "Hull"],
    )
    assert "do not match" in result["error"]


def test_valid_named_three_way_first_outcome_mapping() -> None:
    result = sports_pm_scan.validate_consensus_freshness(
        valid_payload(), 24, now=NOW, expected_outcomes=["Fulham", "Draw", "Hull"],
    )
    assert result["yes_outcomes"] == ["Fulham"]
    assert result["no_outcomes"] == ["Draw", "Hull"]


def test_mocked_nested_valid_worker_payload_is_parsed_and_derived(monkeypatch) -> None:
    from types import SimpleNamespace

    payload = valid_payload(source_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    monkeypatch.setattr(
        sports_pm_scan,
        "run_agent",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stderr="", stdout=json.dumps(payload),
        ),
    )
    result = sports_pm_scan.fetch_bookie_consensus(
        FULHAM_CONTEXT["question"], 24, outcomes=["Yes", "No"],
        market_context=FULHAM_CONTEXT,
    )
    assert result["bookmaker"] == "Example Sportsbook"
    assert result["yes_outcomes"] == ["Fulham"]
    assert result["no_outcomes"] == ["Draw", "Hull"]
    assert 0 < result["yes_prob"] < 1
