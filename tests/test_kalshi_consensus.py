from __future__ import annotations

import copy
import builtins
import datetime as dt
import json
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from kalshi_consensus import KalshiConsensusAdapter  # noqa: E402
import sports_pm_scan  # noqa: E402


RULES_HALF = (
    "If the game is canceled, this market will resolve 50-50. "
    "If the game is postponed, this market will remain open until the game has been completed."
)
TEST_NOW = dt.datetime(2026, 8, 28, 22, 0, tzinfo=dt.timezone.utc)


def pm_rules(line: float, participants: tuple[str, str], exceptions: str = RULES_HALF) -> str:
    left, right = participants
    return (
        f"In the upcoming MLB game between {left} and {right}, scheduled for "
        f"August 28 at 9:00 PM ET, the market resolves Over if {left} and {right} "
        f"combine to score more than {line} runs in this game. {exceptions}"
    )


def gamma_market(*, line: float = 8.5, participants=("Alpha Bears", "Beta Birds")) -> dict:
    left, right = participants
    slug_line = str(line).replace(".", "pt")
    return {
        "id": "pm-1",
        "question": f"{left} vs. {right}: O/U {line}",
        "slug": f"mlb-alpha-beta-2026-08-29-total-{slug_line}",
        "active": True,
        "closed": False,
        "acceptingOrders": True,
        "enableOrderBook": True,
        "sportsMarketType": "totals",
        "line": line,
        "gameStartTime": "2026-08-29 01:00:00+00",
        "outcomes": '["Over", "Under"]',
        "outcomePrices": '["0.10", "0.90"]',  # intentionally stale
        "clobTokenIds": '["101", "202"]',
        "orderMinSize": 5,
        "conditionId": "0xabc123",
        "feesEnabled": True,
        "feeSchedule": {"rate": 0.05, "exponent": 1, "takerOnly": True},
        "description": pm_rules(line, participants),
        "events": [{
            "id": "event-1",
            "title": f"{left} vs. {right}",
            "description": RULES_HALF,
            "live": False,
            "ended": False,
            "startTime": "2026-08-29T01:00:00Z",
        }],
    }


def kalshi_market(*, line: float = 8.5, rules: str = RULES_HALF,
                  provisional: bool = False) -> dict:
    return {
        "ticker": "KXMLBTOTAL-26AUG282100ALPBET-9",
        "event_ticker": "KXMLBTOTAL-26AUG282100ALPBET",
        "status": "active",
        "title": f"Over {line} runs scored",
        "yes_sub_title": f"Over {line} runs scored",
        "strike_type": "greater",
        "floor_strike": line,
        "rules_primary": (
            f"If Alpha Bears and Beta Birds collectively score more {line} runs, "
            "in the Alpha Bears vs Beta Birds professional baseball game originally "
            f"scheduled for Aug 28, 2026 at 9:00 PM EDT, then this market resolves to Yes. {rules}"
        ),
        "rules_secondary": "",
        "is_provisional": provisional,
        "mve_collection_ticker": None,
        "mve_selected_legs": [],
    }


def moneyline_gamma_market() -> dict:
    market = gamma_market()
    market.update({
        "question": "Will Alpha Bears win on 2026-08-28?",
        "groupItemTitle": "Alpha Bears",
        "slug": "mlb-alpha-beta-2026-08-29-alpha",
        "sportsMarketType": "moneyline",
        "outcomes": '["Yes", "No"]',
        "description": (
            "In the professional baseball game scheduled for August 28 at 9:00 PM ET, "
            "if Alpha Bears wins, this market resolves to Yes. " + RULES_HALF
        ),
    })
    market.pop("line")
    return market


def configure_moneyline(fake: "FakeClient") -> None:
    event_ticker = "KXMLBGAME-26AUG282100ALPBET"
    fake.milestone_payload["milestones"][0]["related_event_tickers"] = [event_ticker]
    fake.event_payload = {
        "event": {
            "event_ticker": event_ticker,
            "series_ticker": "KXMLBGAME",
            "title": "Alpha Bears vs Beta Birds",
        },
        "markets": [{
            "ticker": event_ticker + "-ALP",
            "event_ticker": event_ticker,
            "status": "active",
            "title": "Alpha Bears wins",
            "yes_sub_title": "Alpha Bears",
            "rules_primary": (
                "If Alpha Bears wins the Alpha Bears vs Beta Birds professional baseball "
                "game originally scheduled for Aug 28, 2026 at 9:00 PM EDT, this market "
                "resolves to Yes. " + RULES_HALF
            ),
            "rules_secondary": "",
            "is_provisional": False,
            "mve_collection_ticker": None,
            "mve_selected_legs": [],
        }],
    }
    fake.series_payload = {
        "series": {"ticker": "KXMLBGAME", "fee_type": "quadratic", "fee_multiplier": 0.5}
    }


class FakeResponse:
    def __init__(self, status: int, payload: dict | None = None, headers: dict | None = None):
        self.status_code = status
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self) -> dict:
        return copy.deepcopy(self._payload)


class FakeClient:
    def __init__(self, *, milestone_title: str = "Alpha Bears vs Beta Birds",
                 line: float = 8.5, rules: str = RULES_HALF,
                 provisional: bool = False):
        self.calls: list[tuple[str, dict]] = []
        self.fail_pm_token: str | None = None
        self.transient_pm_429s: dict[str, int] = {}
        self.milestone_payload = {
            "milestones": [{
                "id": "mile-1",
                "category": "Sports",
                "type": "baseball_game",
                "title": milestone_title,
                "start_date": "2026-08-29T01:00:00Z",
                "details": {"status": "scheduled"},
                "related_event_tickers": ["KXMLBTOTAL-26AUG282100ALPBET"],
            }],
            "cursor": "",
        }
        self.event_payload = {
            "event": {"event_ticker": "KXMLBTOTAL-26AUG282100ALPBET",
                      "series_ticker": "KXMLBTOTAL",
                      "title": "Alpha Bears vs Beta Birds: Total Runs"},
            "markets": [kalshi_market(line=line, rules=rules, provisional=provisional)],
        }
        self.series_payload = {
            "series": {"ticker": "KXMLBTOTAL", "fee_type": "quadratic",
                       "fee_multiplier": 0.5},
        }
        # Deliberately unsorted and multi-level: the implementation must walk
        # exactly five shares/contracts, not use Gamma or a partial top level.
        timestamp = str(int(TEST_NOW.timestamp() * 1000))
        self.pm_books = {
            "101": {"asset_id": "101", "market": "0xabc123", "timestamp": timestamp,
                    "min_order_size": "5", "bids": [{"price": "0.44", "size": "5"}],
                    "asks": [{"price": "0.46", "size": "3"},
                             {"price": "0.45", "size": "2"}]},
            "202": {"asset_id": "202", "market": "0xabc123", "timestamp": timestamp,
                    "min_order_size": "5", "bids": [{"price": "0.54", "size": "5"}],
                    "asks": [{"price": "0.55", "size": "5"}]},
        }
        self.kalshi_book = {
            "orderbook_fp": {
                "yes_dollars": [["0.42", "1"], ["0.46", "5"]],
                "no_dollars": [["0.52", "3"], ["0.53", "2"]],
            }
        }

    def get(self, url: str, params: dict | None = None) -> FakeResponse:
        params = dict(params or {})
        self.calls.append((url, params))
        if url.endswith("/milestones"):
            return FakeResponse(200, self.milestone_payload)
        if "/events/" in url:
            return FakeResponse(200, self.event_payload)
        if "/series/" in url:
            return FakeResponse(200, self.series_payload)
        if url.endswith("/book"):
            token = str(params.get("token_id"))
            if token == self.fail_pm_token:
                return FakeResponse(429, headers={"Retry-After": "0"})
            if self.transient_pm_429s.get(token, 0) > 0:
                self.transient_pm_429s[token] -= 1
                return FakeResponse(429, headers={"Retry-After": "0"})
            return FakeResponse(200, self.pm_books[token])
        if url.endswith("/orderbook"):
            return FakeResponse(200, self.kalshi_book)
        raise AssertionError(f"unexpected GET {url} {params}")

    def close(self) -> None:
        pass


def compare(fake: FakeClient, market: dict | None = None, sleeps: list | None = None) -> dict:
    sleep_log = sleeps if sleeps is not None else []
    with KalshiConsensusAdapter(fake, sleep_fn=sleep_log.append,
                                backoff_seconds=0, max_attempts=3,
                                now_fn=lambda: TEST_NOW) as adapter:
        return adapter.compare(market or gamma_market())


def test_stale_gamma_never_drives_comparison_and_valid_pair_walks_five_shares():
    fake = FakeClient()
    result = compare(fake)

    assert result["status"] == "matched"
    assert result["price_source"] == "live_pm_clob_and_live_kalshi_orderbook"
    assert result["gamma_outcome_prices_ignored"] == '["0.10", "0.90"]'
    over = next(row for row in result["directions"] if row["pm_outcome"] == "Over")
    assert over["pm_live_book"]["shares"] == 5.0
    assert over["pm_live_book"]["average_price"] == pytest.approx((2 * .45 + 3 * .46) / 5)
    # Buying Kalshi NO consumes the highest YES bid: 1 - .46 = .54.
    assert over["kalshi_side"] == "NO"
    assert over["kalshi_live_book"]["average_price"] == pytest.approx(.54)
    assert over["kalshi_same_outcome_side"] == "YES"
    assert over["kalshi_same_outcome_live_book"]["average_price"] == pytest.approx(
        (2 * .47 + 3 * .48) / 5
    )
    assert over["pm_vs_kalshi_ask_pp"] == pytest.approx(-2.0)
    assert over["pm_live_book"]["average_price"] != pytest.approx(.10)
    assert result["execution"] == "disabled_read_only"
    assert result["snapshot_atomic"] is False
    assert "best_fee_only_snapshot_spread_pp" in result
    assert "best_net_edge_pp" not in result
    assert "net_profit_dollars" in over
    assert "net_payout_dollars" not in over
    milestone_params = next(params for url, params in fake.calls if url.endswith("/milestones"))
    assert milestone_params["minimum_start_date"] == "2026-08-29T00:55:00Z"
    assert milestone_params["maximum_start_date"] == "2026-08-29T01:05:00Z"


def test_reversed_pm_outcome_order_maps_named_complement_not_array_index():
    fake = FakeClient()
    market = gamma_market()
    market["outcomes"] = '["Under", "Over"]'
    market["clobTokenIds"] = '["202", "101"]'
    result = compare(fake, market)

    assert result["status"] == "matched"
    under = next(row for row in result["directions"] if row["pm_outcome"] == "Under")
    over = next(row for row in result["directions"] if row["pm_outcome"] == "Over")
    assert under["kalshi_side"] == "YES"
    assert over["kalshi_side"] == "NO"


def test_live_nested_event_response_shape_is_supported():
    fake = FakeClient()
    fake.event_payload["event"]["markets"] = fake.event_payload.pop("markets")
    fake.event_payload["markets"] = []  # current API keeps a deprecated empty field
    result = compare(fake)

    assert result["status"] == "matched"


def test_wrong_total_line_rejected_before_any_book_fetch():
    fake = FakeClient(line=7.5)
    result = compare(fake, gamma_market(line=8.5))

    assert result["status"] == "rejected"
    assert result["reason"] == "wrong_or_ambiguous_kalshi_line_or_predicate"
    assert not any(url.endswith("/book") or url.endswith("/orderbook") for url, _ in fake.calls)


def test_wrong_participant_rejected_before_event_or_book_fetch():
    fake = FakeClient(milestone_title="Alpha Bears vs Gamma Goats")
    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "no_exact_participant_time_lineage_match"
    assert not any("/events/" in url or url.endswith("/book") for url, _ in fake.calls)


@pytest.mark.parametrize("details", [None, {}, {"status": "started"}])
def test_milestone_must_affirmatively_be_pre_event(details):
    fake = FakeClient()
    fake.milestone_payload["milestones"][0]["details"] = details

    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "no_exact_participant_time_lineage_match"
    assert not any("/events/" in url for url, _ in fake.calls)


def test_rules_mismatch_suppresses_all_quotes():
    mismatch = (
        "If the game is canceled, this market will resolve to a fair price. "
        "If the game is postponed, this market will remain open until the game has been completed."
    )
    fake = FakeClient(rules=mismatch)
    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "cancellation_void_rules_mismatch"
    assert "directions" not in result
    assert not any(url.endswith("/book") or url.endswith("/orderbook") for url, _ in fake.calls)


def test_matching_fair_price_rules_still_are_not_fixed_complements():
    fair = (
        "If the game is canceled, this market will resolve to a fair price. "
        "If the game is postponed, this market will remain open until the game has been completed."
    )
    market = gamma_market()
    market["description"] = pm_rules(8.5, ("Alpha Bears", "Beta Birds"), fair)
    fake = FakeClient(rules=fair)
    result = compare(fake, market)

    assert result["status"] == "rejected"
    assert result["reason"] == "non_binary_fixed_payout_rules"
    assert "directions" not in result


def test_unparsed_recognized_exception_is_ambiguous_not_silently_ignored():
    ambiguous = RULES_HALF + " If the game is shortened, league house rules apply."
    market = gamma_market()
    market["description"] = pm_rules(8.5, ("Alpha Bears", "Beta Birds"), ambiguous)
    fake = FakeClient(rules=ambiguous)
    result = compare(fake, market)

    assert result["status"] == "rejected"
    assert result["reason"] == "ambiguous_cancellation_or_postponement_rules"


def test_429_exhaustion_never_reuses_a_previous_live_quote():
    fake = FakeClient()
    sleeps: list[float] = []
    adapter = KalshiConsensusAdapter(fake, sleep_fn=sleeps.append,
                                     backoff_seconds=0, max_attempts=3,
                                     now_fn=lambda: TEST_NOW)
    try:
        first = adapter.compare(gamma_market())
        assert first["status"] == "matched"
        fake.fail_pm_token = "101"
        second = adapter.compare(gamma_market())
    finally:
        adapter.close()

    assert second["status"] == "error"
    assert second["reason"] == "http_429_exhausted"
    assert "directions" not in second
    token_calls = [params for url, params in fake.calls
                   if url.endswith("/book") and params.get("token_id") == "101"]
    assert len(token_calls) == 4  # one successful refresh, then exactly three retries
    assert len(sleeps) == 2


def test_transient_429_retries_then_uses_fresh_successful_book():
    fake = FakeClient()
    fake.transient_pm_429s["101"] = 2
    sleeps: list[float] = []

    result = compare(fake, sleeps=sleeps)

    assert result["status"] == "matched"
    token_calls = [params for url, params in fake.calls
                   if url.endswith("/book") and params.get("token_id") == "101"]
    assert len(token_calls) == 3
    assert len(sleeps) == 2


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda m: m.update({"clobTokenIds": '["101", "101"]'}),
         "pm_outcome_token_not_unique"),
        (lambda m: m.update({"feeSchedule": None, "feesEnabled": True}),
         "unknown_pm_fee_schedule"),
        (lambda m: m.update({"live": True}), "live_or_ended_event"),
    ],
)
def test_ambiguous_or_unpriceable_pm_inputs_fail_closed(mutate, reason):
    market = gamma_market()
    mutate(market)
    fake = FakeClient()
    result = compare(fake, market)

    assert result["status"] == "rejected"
    assert result["reason"] == reason


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda m: m.pop("active"), "pm_market_not_tradeable"),
        (lambda m: m.update({"active": False}), "pm_market_not_tradeable"),
        (lambda m: m.update({"active": 1}), "pm_market_not_tradeable"),
        (lambda m: m.pop("closed"), "pm_market_not_tradeable"),
        (lambda m: m.update({"closed": True}), "pm_market_not_tradeable"),
        (lambda m: m.update({"closed": None}), "pm_market_not_tradeable"),
        (lambda m: m.pop("acceptingOrders"), "pm_market_not_tradeable"),
        (lambda m: m.update({"acceptingOrders": False}), "pm_market_not_tradeable"),
        (lambda m: m.update({"acceptingOrders": "true"}), "pm_market_not_tradeable"),
        (lambda m: m.pop("enableOrderBook"), "pm_orderbook_not_enabled"),
        (lambda m: m.update({"enableOrderBook": False}), "pm_orderbook_not_enabled"),
        (lambda m: m.update({"enableOrderBook": 1}), "pm_orderbook_not_enabled"),
    ],
)
def test_pm_tradeability_must_be_affirmative_and_typed(mutate, reason):
    market = gamma_market()
    mutate(market)
    fake = FakeClient()

    result = compare(fake, market)

    assert result["status"] == "rejected"
    assert result["reason"] == reason
    assert fake.calls == []


def test_integer_total_push_is_unsupported_before_discovery():
    market = gamma_market(line=8.0)
    fake = FakeClient(line=8.0)
    result = compare(fake, market)

    assert result["status"] == "rejected"
    assert result["reason"] == "integer_total_push_unsupported"
    assert fake.calls == []


def test_same_line_with_wrong_structured_predicate_is_rejected():
    fake = FakeClient(line=8.5)
    fake.event_payload["markets"][0]["strike_type"] = "less"
    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "wrong_or_ambiguous_kalshi_line_or_predicate"
    assert not any(url.endswith("/book") or url.endswith("/orderbook") for url, _ in fake.calls)


@pytest.mark.parametrize("field", ["cap_strike", "functional_strike"])
def test_malformed_present_total_strike_fields_are_not_treated_as_absent(field):
    fake = FakeClient(line=8.5)
    fake.event_payload["markets"][0][field] = "not-a-valid-strike"

    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "wrong_or_ambiguous_kalshi_line_or_predicate"


def test_pm_displayed_total_line_must_equal_structured_line():
    market = gamma_market(line=7.5)
    market["question"] = "Alpha Bears vs. Beta Birds: O/U 8.5"
    market["slug"] = "mlb-alpha-beta-2026-08-29-total-8pt5"
    fake = FakeClient(line=7.5)

    result = compare(fake, market)

    assert result["status"] == "rejected"
    assert result["reason"] == "pm_displayed_total_line_mismatch"
    assert fake.calls == []


def test_partial_event_scope_is_rejected_even_with_same_line_and_exceptions():
    fake = FakeClient()
    child = fake.event_payload["markets"][0]
    child["rules_primary"] = child["rules_primary"].replace(
        "collectively score", "collectively score in the first five innings and"
    )

    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "period_or_partial_event_scope"
    assert not any(url.endswith("/book") or url.endswith("/orderbook") for url, _ in fake.calls)


@pytest.mark.parametrize("venue", ["pm", "kalshi"])
def test_total_rule_predicate_must_canonicalize_to_the_structured_line(venue):
    market = gamma_market()
    fake = FakeClient()
    if venue == "pm":
        market["description"] = market["description"].replace(
            "more than 8.5 runs", "10 or more runs"
        )
    else:
        child = fake.event_payload["markets"][0]
        child["rules_primary"] = child["rules_primary"].replace(
            "more 8.5 runs", "more 10.5 runs"
        )

    result = compare(fake, market)

    assert result["status"] == "rejected"
    assert result["reason"] == "ordinary_total_rule_predicate_mismatch"
    assert not any(url.endswith("/book") or url.endswith("/orderbook") for url, _ in fake.calls)


@pytest.mark.parametrize(
    ("venue", "qualifier"),
    [
        ("pm", " Runs scored in extra innings count."),
        ("kalshi", " Runs scored in extra innings are excluded."),
        ("pm", " This applies provided that the game reaches nine innings."),
        ("kalshi", " This applies if and only if the game is declared official."),
        ("pm", " The total uses runs through the ninth inning."),
        ("kalshi", " The total excludes unearned runs."),
        ("pm", " The total uses runs through regulation."),
        ("kalshi", " The total covers nine regulation innings."),
    ],
)
def test_extra_innings_and_unparsed_ordinary_qualifiers_fail_closed(venue, qualifier):
    market = gamma_market()
    fake = FakeClient()
    if venue == "pm":
        market["description"] += qualifier
    else:
        fake.event_payload["markets"][0]["rules_primary"] += qualifier

    result = compare(fake, market)

    assert result["status"] == "rejected"
    assert result["reason"] == "unparsed_ordinary_predicate_qualifier"
    assert not any(url.endswith("/book") or url.endswith("/orderbook") for url, _ in fake.calls)


def test_child_market_rules_override_incompatible_parent_event_description():
    market = gamma_market()
    market["events"][0]["description"] = (
        "If the game is canceled, this market resolves to a fair price. "
        "If postponed, it remains open until completed."
    )

    result = compare(FakeClient(), market)

    assert result["status"] == "matched"
    assert result["rules"][0]["pm_source"] == "market.description"


def test_moneyline_winner_predicate_names_the_selected_participant_on_both_venues():
    valid_fake = FakeClient()
    configure_moneyline(valid_fake)
    valid = compare(valid_fake, moneyline_gamma_market())
    assert valid["status"] == "matched"

    wrong_pm_fake = FakeClient()
    configure_moneyline(wrong_pm_fake)
    wrong_pm = moneyline_gamma_market()
    wrong_pm["description"] = wrong_pm["description"].replace(
        "if Alpha Bears wins", "if Beta Birds wins"
    )
    pm_result = compare(wrong_pm_fake, wrong_pm)
    assert pm_result["reason"] == "pm_moneyline_rules_participant_mismatch"

    wrong_kalshi_fake = FakeClient()
    configure_moneyline(wrong_kalshi_fake)
    child = wrong_kalshi_fake.event_payload["markets"][0]
    child["rules_primary"] = child["rules_primary"].replace(
        "If Alpha Bears wins", "If Beta Birds wins"
    )
    kalshi_result = compare(wrong_kalshi_fake, moneyline_gamma_market())
    assert kalshi_result["reason"] == "kalshi_moneyline_rules_participant_mismatch"


def test_returned_event_and_series_lineage_is_exact():
    wrong_event_series = FakeClient()
    wrong_event_series.event_payload["event"]["series_ticker"] = "KXMLBGAME"
    first = compare(wrong_event_series)
    assert first["reason"] == "kalshi_league_or_market_type_mismatch"

    wrong_series_response = FakeClient()
    wrong_series_response.series_payload["series"]["ticker"] = "KXMLBGAME"
    second = compare(wrong_series_response)
    assert second["reason"] == "kalshi_series_response_ticker_mismatch"


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda f: f.pm_books["101"].update({"asset_id": "202"}),
         "pm_book_asset_id_mismatch"),
        (lambda f: f.pm_books["101"].update({"market": "0xforeign"}),
         "pm_book_condition_id_mismatch"),
        (lambda f: f.pm_books["101"]["asks"].append({"price": "nan", "size": "1"}),
         "invalid_pm_book_level"),
        (lambda f: f.pm_books["101"]["bids"].append({"price": "0.46", "size": "1"}),
         "crossed_pm_book"),
        (lambda f: f.pm_books["101"].update({
            "timestamp": str(int((TEST_NOW - dt.timedelta(seconds=121)).timestamp() * 1000))
        }), "stale_or_future_pm_book"),
    ],
)
def test_pm_live_book_identity_freshness_and_integrity_fail_closed(mutate, reason):
    fake = FakeClient()
    mutate(fake)

    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == reason


def test_any_malformed_kalshi_level_rejects_the_snapshot():
    fake = FakeClient()
    fake.kalshi_book["orderbook_fp"]["no_dollars"].append(["bad-price", "1"])

    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "invalid_or_crossed_kalshi_book"


def test_missing_same_outcome_depth_is_nullable_when_hedge_direction_is_priceable():
    fake = FakeClient()
    # For PM Over, buying the Kalshi hedge (NO) consumes YES bids and remains
    # priceable. Informational same-outcome YES consumes an empty NO side;
    # Kalshi's public JSON represents an empty side as null on some books.
    fake.kalshi_book["orderbook_fp"]["no_dollars"] = None

    result = compare(fake)

    assert result["status"] == "matched"
    assert [row["pm_outcome"] for row in result["directions"]] == ["Over"]
    over = result["directions"][0]
    assert over["kalshi_live_book"] is not None
    assert over["kalshi_same_outcome_live_book"] is None
    assert over["kalshi_same_outcome_priceability"] == "insufficient"
    assert over["pm_vs_kalshi_ask_pp"] is None
    assert over["pm_vs_kalshi_all_in_pp"] is None
    under_evidence = next(
        row for row in result["direction_priceability"] if row["pm_outcome"] == "Under"
    )
    assert under_evidence["emitted"] is False
    assert under_evidence["kalshi_hedge_depth"] == "insufficient"


def test_one_pm_outcome_without_ask_depth_does_not_suppress_other_hedge():
    fake = FakeClient()
    fake.pm_books["101"]["asks"] = []

    result = compare(fake)

    assert result["status"] == "matched"
    assert [row["pm_outcome"] for row in result["directions"]] == ["Under"]
    over_evidence = next(
        row for row in result["direction_priceability"] if row["pm_outcome"] == "Over"
    )
    assert over_evidence["pm_ask_depth"] == "insufficient"
    assert over_evidence["emitted"] is False


def test_no_priceable_hedge_directions_rejects_with_per_direction_evidence():
    fake = FakeClient()
    for book in fake.pm_books.values():
        book["asks"] = []

    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "no_fully_priceable_pm_kalshi_hedge_direction"
    assert len(result["direction_priceability"]) == 2
    assert not any(row["emitted"] for row in result["direction_priceability"])
    assert "directions" not in result


def test_null_bid_sides_are_valid_empty_ladders_but_yield_no_hedge():
    fake = FakeClient()
    fake.kalshi_book["orderbook_fp"] = {
        "yes_dollars": None,
        "no_dollars": None,
    }

    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "no_fully_priceable_pm_kalshi_hedge_direction"
    assert len(result["direction_priceability"]) == 2
    assert all(row["kalshi_hedge_depth"] == "insufficient"
               for row in result["direction_priceability"])


def test_comparison_size_uses_live_and_gamma_minimums_on_both_venues():
    fake = FakeClient()
    market = gamma_market()
    market["orderMinSize"] = 7
    for book in fake.pm_books.values():
        book["min_order_size"] = "6"
        book["asks"][0]["size"] = "10"
        book["bids"][0]["size"] = "10"
    fake.kalshi_book["orderbook_fp"] = {
        "yes_dollars": [["0.46", "10"]],
        "no_dollars": [["0.53", "10"]],
    }

    result = compare(fake, market)

    assert result["status"] == "matched"
    assert result["comparison_size"] == 7.0
    assert all(row["pm_live_book"]["shares"] == 7.0 for row in result["directions"])
    assert all(row["kalshi_live_book"]["contracts"] == 7.0 for row in result["directions"])


def test_started_or_near_start_candidate_is_rejected_before_network():
    market = gamma_market()
    market["gameStartTime"] = "2026-08-28T22:04:00Z"
    market["events"][0]["startTime"] = "2026-08-28T22:04:00Z"
    fake = FakeClient()

    result = compare(fake, market)

    assert result["status"] == "rejected"
    assert result["reason"] == "event_started_or_inside_start_safety_window"
    assert fake.calls == []


def test_nonempty_bounded_milestone_cursor_is_ambiguous_even_with_match():
    fake = FakeClient()
    fake.milestone_payload["cursor"] = "another-page"
    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "bounded_milestone_page_incomplete"
    assert not any("/events/" in url for url, _ in fake.calls)


def test_provisional_kalshi_market_is_not_accepted():
    fake = FakeClient(provisional=True)
    result = compare(fake)

    assert result["status"] == "rejected"
    assert result["reason"] == "kalshi_provisional_market_unsupported"


def test_cli_default_never_imports_or_calls_kalshi(monkeypatch, capsys):
    monkeypatch.setattr(sports_pm_scan, "fetch_active_sports_markets", lambda *_: [])
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "kalshi_consensus":
            raise AssertionError("default scan must not load the Kalshi adapter")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(sys, "argv", ["sports_pm_scan.py", "--json", "--hurdle-apy", "0.03"])

    assert sports_pm_scan.main() == 0
    assert json.loads(capsys.readouterr().out) == {"results": []}
