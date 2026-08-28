"""Regressions for topology-aware multi-leg portfolio analytics."""

from __future__ import annotations

import copy
import datetime as dt
import json
import math
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import position_groups as groups  # noqa: E402


def _duma_priors() -> dict:
    legs = {
        "a": {"slug": "duma-a", "outcome": "Yes", "asset": "asset-a"},
        "b": {"slug": "duma-b", "outcome": "Yes", "asset": "asset-b"},
        "c": {"slug": "duma-c", "outcome": "Yes", "asset": "asset-c"},
    }
    priors = {
        "_groups": {
            "duma": {
                "label": "Duma covered union",
                "add_gate": "test gate",
                "add_policy": {
                    "manual_gate": True,
                    "max_component_all_in": {"covered": 0.57},
                    "min_component_fair": {"covered": 0.75},
                    "max_total_component_quantity": {"covered": 34},
                },
                "quantity_mode": "proportional_live",
                "event_model": {
                    "kind": "exclusive",
                    "event_id": "event-duma",
                    "end_date": "2026-09-20",
                    "negative_risk": True,
                    "covered": ["a", "b", "c"],
                },
                "legs": legs,
                "components": [
                    {
                        "id": "covered",
                        "quantity": 1,
                        "weights": {"a": 1, "b": 1, "c": 1},
                        "directional": True,
                    }
                ],
            }
        }
    }
    for leg_id, probability in zip(("a", "b", "c"), (0.08, 0.40, 0.28)):
        priors[legs[leg_id]["slug"]] = {
            "p_yes": probability,
            "set_only": "Duma covered union",
            "verified": "2026-08-28",
        }
    return priors


def _duma_positions(
    sizes: tuple[float, float, float] = (20, 20, 20),
    marks: tuple[float, float, float] = (0.02, 0.48, 0.07),
) -> list[dict]:
    initial = (1.0, 4.0, 6.0)
    fees = (0.1, 0.2, 0.1)
    return [
        {
            "slug": f"duma-{leg}",
            "outcome": "Yes",
            "asset": f"asset-{leg}",
            "conditionId": f"condition-{leg}",
            "eventId": "event-duma",
            "endDate": "2026-09-20",
            "negativeRisk": True,
            "size": size,
            "curPrice": mark,
            "initialValue": cost,
            "entryFeesUsdc": fee,
            "avgPrice": cost / size if size else 0,
            "title": f"Duma {leg}",
        }
        for leg, size, mark, cost, fee in zip("abc", sizes, marks, initial, fees)
    ]


def _duma_group(
    *,
    sizes: tuple[float, float, float] = (20, 20, 20),
    marks: tuple[float, float, float] = (0.02, 0.48, 0.07),
) -> dict:
    book = groups.evaluate_groups(_duma_priors(), _duma_positions(sizes, marks))
    assert book.issues == []
    return book.groups["duma"]


def _meta_priors() -> dict:
    legs = {
        "700": {"slug": "meta-700", "outcome": "Yes", "asset": "asset-700"},
        "3b": {"slug": "meta-3b", "outcome": "No", "asset": "asset-3b"},
        "4b": {"slug": "meta-4b", "outcome": "No", "asset": "asset-4b"},
    }
    marker = "overlapping pairs plus crumb"
    return {
        "_groups": {
            "meta": {
                "label": "MetaMask structure",
                "add_gate": "test gate",
                "add_policy": {"manual_gate": True},
                "event_model": {
                    "kind": "monotone_yes",
                    "event_id": "event-meta",
                    "end_date": "2027-01-01",
                    "negative_risk": False,
                    "order": ["700", "3b", "4b"],
                    "thresholds": {
                        "700": 700_000_000,
                        "3b": 3_000_000_000,
                        "4b": 4_000_000_000,
                    },
                },
                "legs": legs,
                "components": [
                    {
                        "id": "pair3",
                        "quantity": 29.7173,
                        "weights": {"700": 1, "3b": 1},
                        "directional": False,
                    },
                    {
                        "id": "pair4",
                        "quantity": 15.0337,
                        "weights": {"700": 1, "4b": 1},
                        "directional": False,
                    },
                    {
                        "id": "crumb",
                        "quantity": 2.9686,
                        "weights": {"700": 1},
                        "directional": True,
                    },
                ],
            }
        },
        "meta-700": {"p_yes": 0.078, "arb_paired": marker, "verified": "2026-08-28"},
        "meta-3b": {"p_no": 0.947, "arb_paired": marker, "verified": "2026-08-28"},
        "meta-4b": {"p_no": 0.956, "arb_paired": marker, "verified": "2026-08-28"},
    }


def _meta_positions() -> list[dict]:
    rows = []
    for leg, outcome, size, mark, cost in (
        ("700", "Yes", 47.7196, 0.09, 3.5),
        ("3b", "No", 29.7173, 0.92, 25.5),
        ("4b", "No", 15.0337, 0.93, 14.0),
    ):
        rows.append(
            {
                "slug": f"meta-{leg}",
                "outcome": outcome,
                "asset": f"asset-{leg}",
                "eventId": "event-meta",
                "endDate": "2027-01-01",
                "negativeRisk": False,
                "size": size,
                "curPrice": mark,
                "initialValue": cost,
                "entryFeesUsdc": 0,
            }
        )
    return rows


def test_duma_equal_union_aggregates_probability_cost_and_redistribution() -> None:
    group = _duma_group()

    assert group["union_probability"] == pytest.approx(0.76)
    assert group["fair_value"] == pytest.approx(15.20)
    assert group["covered_payout"] == pytest.approx(20)
    assert group["outside_payout"] == 0
    assert group["cost_basis"] == pytest.approx(11.40)
    assert group["mark_value"] == pytest.approx(11.40)
    assert group["drawdown_pct"] == pytest.approx(0)
    assert [state["payout"] for state in group["states"]] == [20, 20, 20, 0]


def test_duma_real_group_decline_is_one_group_drawdown() -> None:
    group = _duma_group(marks=(0.05, 0.25, 0.10))

    assert group["mark_value"] == pytest.approx(8.0)
    assert group["drawdown_pct"] == pytest.approx(-29.8245614035)


def test_duma_infers_equal_live_quantity_but_enforces_tolerance() -> None:
    assert _duma_group(sizes=(25, 25, 25))["covered_payout"] == 25
    assert _duma_group(sizes=(20, 20.01, 20))["status"] == "OK"

    broken = groups.evaluate_groups(
        _duma_priors(), _duma_positions((20, 19.989, 20))
    )
    assert broken.groups["duma"]["status"] == "GROUP_BROKEN"
    assert "live size" in broken.issues[0]
    assert set(broken.by_slug) == {"duma-a", "duma-b", "duma-c"}

    anchor_middle = groups.evaluate_groups(
        _duma_priors(), _duma_positions((20.01, 20.00, 20.02))
    )
    assert anchor_middle.groups["duma"]["status"] == "GROUP_BROKEN"

    all_zero = groups.evaluate_groups(
        _duma_priors(), _duma_positions((0, 0, 0))
    )
    assert all_zero.groups["duma"]["status"] == "GROUP_BROKEN"


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "wrong_outcome",
        "wrong_asset",
        "wrong_event",
        "wrong_deadline",
        "wrong_neg_risk",
        "nan_size",
        "infinite_size",
        "negative_size",
        "malformed_size",
        "boolean_size",
        "missing_fee",
        "malformed_fee",
        "missing_cost",
        "exact_slug_mismatch",
    ],
)
def test_duma_topology_failures_are_broken_and_remain_protected(mutation: str) -> None:
    positions = _duma_positions()
    if mutation == "missing":
        positions.pop()
    elif mutation == "duplicate":
        positions.append(copy.deepcopy(positions[0]))
    elif mutation == "wrong_outcome":
        positions[0]["outcome"] = "No"
    elif mutation == "wrong_asset":
        positions[0]["asset"] = "other-token"
    elif mutation == "wrong_event":
        positions[0]["eventId"] = "other-event"
    elif mutation == "wrong_deadline":
        positions[0]["endDate"] = "2026-09-21"
    elif mutation == "wrong_neg_risk":
        positions[0]["negativeRisk"] = False
    elif mutation == "nan_size":
        positions[0]["size"] = math.nan
    elif mutation == "infinite_size":
        positions[0]["size"] = math.inf
    elif mutation == "negative_size":
        positions[0]["size"] = -1
    elif mutation == "malformed_size":
        positions[0]["size"] = "twenty"
    elif mutation == "boolean_size":
        positions[0]["size"] = True
    elif mutation == "missing_fee":
        positions[0].pop("entryFeesUsdc")
    elif mutation == "malformed_fee":
        positions[0]["entryFeesUsdc"] = "free-ish"
    elif mutation == "missing_cost":
        positions[0].pop("initialValue")
        positions[0].pop("avgPrice")
    elif mutation == "exact_slug_mismatch":
        positions[0]["slug"] += "-suffix"

    book = groups.evaluate_groups(_duma_priors(), positions)

    assert book.groups["duma"]["status"] == "GROUP_BROKEN"
    assert "fair_value" not in book.groups["duma"]
    assert {"duma-a", "duma-b", "duma-c"} <= set(book.by_slug)
    if mutation == "exact_slug_mismatch":
        assert book.by_slug["duma-a-suffix"] == "duma"


def test_metamask_explicit_components_state_payoffs_and_joint_fair() -> None:
    book = groups.evaluate_groups(_meta_priors(), _meta_positions())
    group = book.groups["meta"]

    assert book.issues == []
    assert group["expected_qty"] == pytest.approx(
        {"700": 47.7196, "3b": 29.7173, "4b": 15.0337}
    )
    assert [state["probability"] for state in group["states"]] == pytest.approx(
        [0.922, 0.025, 0.009, 0.044]
    )
    assert [state["payout"] for state in group["states"]] == pytest.approx(
        [44.7510, 92.4706, 62.7533, 47.7196]
    )
    assert group["fair_value"] == pytest.approx(46.2366291)
    assert group["guaranteed_floor"] == pytest.approx(44.7510)
    assert group["guaranteed_floor"] - group["cost_basis"] == pytest.approx(1.7510)
    assert group["maximum_payout"] > group["guaranteed_floor"]
    components = {component["id"]: component for component in group["components"]}
    assert components["pair3"]["fair_per_unit"] == pytest.approx(1.025)
    assert components["pair4"]["fair_per_unit"] == pytest.approx(1.034)
    assert components["crumb"]["fair_per_unit"] == pytest.approx(0.078)
    assert components["crumb"]["quantity"] == pytest.approx(2.9686)


def test_live_metamask_gross_cost_is_reconciled_and_not_double_charged() -> None:
    positions = _meta_positions()
    cost_fields = (
        (3.8099, 0.2454, 4.055355),
        (25.2299, 0.26668, 25.496650),
        (13.3499, 0.10466, 13.454648),
    )
    for position, (initial, fee, gross) in zip(positions, cost_fields):
        position.update(
            {
                "initialValue": initial,
                "entryFeesUsdc": fee,
                "grossInitialValue": gross,
            }
        )

    group = groups.evaluate_groups(_meta_priors(), positions).groups["meta"]

    assert group["cost_basis"] == pytest.approx(43.006653)
    assert group["guaranteed_floor"] - group["cost_basis"] == pytest.approx(1.744347)


@pytest.mark.parametrize(
    ("leg", "size"),
    [("meta-700", 44.7510), ("meta-3b", 29.70)],
)
def test_metamask_explicit_quantity_drift_breaks_group(leg: str, size: float) -> None:
    positions = _meta_positions()
    next(row for row in positions if row["slug"] == leg)["size"] = size

    group = groups.evaluate_groups(_meta_priors(), positions).groups["meta"]

    assert group["status"] == "GROUP_BROKEN"
    assert "fair_value" not in group


def test_incoherent_exclusive_and_monotone_priors_fail_closed() -> None:
    duma = _duma_priors()
    duma["duma-a"]["p_yes"] = 0.50
    duma["duma-b"]["p_yes"] = 0.40
    duma["duma-c"]["p_yes"] = 0.28
    assert groups.evaluate_groups(duma, _duma_positions()).groups["duma"]["status"] == "GROUP_BROKEN"

    meta = _meta_priors()
    meta["meta-3b"]["p_no"] = 0.90  # underlying p_yes=.10 > p(>700m)=.078
    assert groups.evaluate_groups(meta, _meta_positions()).groups["meta"]["status"] == "GROUP_BROKEN"

    meta = _meta_priors()
    meta["meta-3b"]["p_yes"] = 0.20  # conflicts with p_no=.947
    assert groups.evaluate_groups(meta, _meta_positions()).groups["meta"]["status"] == "GROUP_BROKEN"


def test_tiny_monotone_rounding_inversion_is_normalized_consistently() -> None:
    meta = _meta_priors()
    meta["meta-3b"]["p_no"] = 1.0 - 0.0780005

    group = groups.evaluate_groups(meta, _meta_positions()).groups["meta"]

    assert group["status"] == "OK"
    probabilities = [state["probability"] for state in group["states"]]
    assert all(probability >= 0 for probability in probabilities)
    assert sum(probabilities) == pytest.approx(1.0)


def test_malformed_schema_still_suppresses_raw_members() -> None:
    priors = _duma_priors()
    priors["_groups"]["duma"]["components"][0]["weights"]["unknown"] = 1

    book = groups.evaluate_groups(priors, _duma_positions())

    assert set(book.groups) == {"duma"}
    assert book.groups["duma"]["status"] == "GROUP_BROKEN"
    assert book.groups["duma"]["slugs"] == ["duma-a", "duma-b", "duma-c"]
    assert book.issues[0].startswith("GROUP_BROKEN configuration")
    assert set(book.by_slug) == {"duma-a", "duma-b", "duma-c"}


def test_blank_malformed_group_id_still_protects_live_slug_drift_by_asset() -> None:
    priors = _duma_priors()
    raw_group = priors["_groups"].pop("duma")
    priors["_groups"]["   "] = raw_group
    positions = _duma_positions()
    positions[0]["slug"] = "renamed-duma-a"

    book = groups.evaluate_groups(priors, positions)

    protected_id = book.by_slug["renamed-duma-a"]
    assert protected_id
    assert book.by_asset["asset-a"] == protected_id
    assert book.groups[protected_id]["status"] == "GROUP_BROKEN"
    assert "renamed-duma-a" in book.groups[protected_id]["slugs"]
    assert book.issues[0].startswith("GROUP_BROKEN configuration")


def test_normalized_duplicate_group_ids_and_unhashable_covered_fail_safely() -> None:
    priors = _duma_priors()
    duplicate = copy.deepcopy(priors["_groups"]["duma"])
    duplicate["legs"] = {
        key: {**leg, "slug": leg["slug"] + "-other", "asset": leg["asset"] + "-other"}
        for key, leg in duplicate["legs"].items()
    }
    priors["_groups"][" duma "] = duplicate
    book = groups.evaluate_groups(priors, _duma_positions())
    assert set(book.groups) == {"duma"}
    assert book.groups["duma"]["status"] == "GROUP_BROKEN"
    assert "duplicated" in book.issues[0]
    assert set(("duma-a", "duma-b", "duma-c")) <= set(book.by_slug)

    priors = _duma_priors()
    priors["_groups"]["duma"]["event_model"]["covered"] = [{"not": "hashable"}]
    book = groups.evaluate_groups(priors, _duma_positions())
    assert set(book.groups) == {"duma"}
    assert book.groups["duma"]["status"] == "GROUP_BROKEN"
    assert book.issues[0].startswith("GROUP_BROKEN configuration")
    assert set(book.by_slug) == {"duma-a", "duma-b", "duma-c"}


@pytest.mark.parametrize("mutation", ["duplicate_leg_id", "duplicate_asset", "duplicate_covered", "unknown_policy", "threshold_key"])
def test_schema_identity_and_policy_typos_fail_closed(mutation: str) -> None:
    priors = _duma_priors() if mutation != "threshold_key" else _meta_priors()
    raw = next(iter(priors["_groups"].values()))
    if mutation == "duplicate_leg_id":
        raw["legs"][" a "] = {
            "slug": "duma-other",
            "outcome": "Yes",
            "asset": "asset-other",
        }
    elif mutation == "duplicate_asset":
        raw["legs"]["b"]["asset"] = raw["legs"]["a"]["asset"]
    elif mutation == "duplicate_covered":
        raw["event_model"]["covered"].append("a")
    elif mutation == "unknown_policy":
        raw["add_policy"]["max_component_allin"] = {"covered": 0.57}
    elif mutation == "threshold_key":
        raw["event_model"]["thresholds"]["wrong"] = raw["event_model"]["thresholds"].pop("4b")

    positions = _duma_positions() if mutation != "threshold_key" else _meta_positions()
    book = groups.evaluate_groups(priors, positions)

    expected_group_id = "meta" if mutation == "threshold_key" else "duma"
    assert set(book.groups) == {expected_group_id}
    assert book.groups[expected_group_id]["status"] == "GROUP_BROKEN"
    assert book.issues[0].startswith("GROUP_BROKEN configuration")


def test_legacy_marker_absent_from_strict_topology_is_reported_and_protected() -> None:
    priors = _duma_priors()
    priors["extra-protected"] = {"p_yes": 0.5, "set_only": "forgotten leg"}
    positions = _duma_positions() + [
        {
            "slug": "extra-protected",
            "outcome": "Yes",
            "asset": "extra-token",
            "eventId": "other",
            "endDate": "2026-09-20",
            "negativeRisk": False,
            "size": 2,
            "curPrice": 0.5,
            "initialValue": 1,
            "entryFeesUsdc": 0,
        }
    ]
    book = groups.evaluate_groups(priors, positions)
    assert "extra-protected" in book.by_slug
    assert any("absent from _groups topology" in issue for issue in book.issues)


def test_complete_group_exit_aggregates_exact_quotes_and_synthetic_price() -> None:
    group = _duma_group()
    quotes = {
        "duma-a": {"gross": 2.0, "fee": 0.0, "net": 2.0, "filled": 20, "unfilled": 0},
        "duma-b": {"gross": 4.0, "fee": 0.224, "net": 3.776, "filled": 20, "unfilled": 0},
        "duma-c": {
            "gross": 7.0,
            "fee": 0.25425,
            "net": 6.74575,
            "filled": 20,
            "unfilled": 0,
        },
    }

    quote = groups.quote_group_exit(group, quotes)

    assert quote["status"] == "OK"
    assert quote["gross"] == pytest.approx(13.0)
    assert quote["fee"] == pytest.approx(0.47825)
    assert quote["net"] == pytest.approx(12.52175)
    assert quote["synthetic_exit_price"] == pytest.approx(0.6260875)


def test_partial_or_depthless_group_exit_is_never_actionable() -> None:
    group = _duma_group()
    complete = {
        slug: {"gross": 2.0, "fee": 0.0, "net": 2.0, "filled": 20, "unfilled": 0}
        for slug in ("duma-a", "duma-b", "duma-c")
    }
    partial = copy.deepcopy(complete)
    partial["duma-c"].update(
        {"gross": 1.999, "net": 1.999, "filled": 19.99, "unfilled": 0.01}
    )
    quote = groups.quote_group_exit(group, partial)
    assert quote["status"] == "GROUP_UNPRICED"
    assert quote["actionable"] is False
    assert groups.group_exit_verdict(group, quote)["actionable"] is False

    depthless = copy.deepcopy(complete)
    depthless["duma-c"].pop("filled")
    assert groups.quote_group_exit(group, depthless)["status"] == "GROUP_UNPRICED"

    false_full = copy.deepcopy(complete)
    false_full["duma-c"].update(
        {"gross": 1.9991, "net": 1.9991, "filled": 19.991, "unfilled": 0}
    )
    assert groups.quote_group_exit(group, false_full)["status"] == "GROUP_UNPRICED"

    above_payout = copy.deepcopy(complete)
    above_payout["duma-c"].update(
        {"gross": 21.0, "net": 21.0, "filled": 20, "unfilled": 0}
    )
    assert groups.quote_group_exit(group, above_payout)["status"] == "GROUP_UNPRICED"


def test_hurdle_aware_verdict_is_preserved_by_human_formatter() -> None:
    group = _duma_group()
    quote = {
        "status": "OK",
        "actionable": True,
        "gross": 15.10,
        "fee": 0.0,
        "net": 15.10,
        "synthetic_exit_price": 0.755,
        "unfilled_by_leg": {},
    }
    assert groups.group_exit_verdict(group, quote)["verdict"].startswith(
        "GROUP_PRIOR_FRESHNESS_UNCHECKED"
    )
    verdict = groups.group_exit_verdict(
        group,
        quote,
        hurdle_apy=0.05,
        days=365,
        as_of=dt.date(2026, 8, 28),
    )
    assert verdict["verdict"] == "EXIT_COMPLETE_GROUP"
    assert "EXIT_COMPLETE_GROUP" in groups.format_group_summary(group, quote, verdict)


@pytest.mark.parametrize(
    "verdict_inputs",
    [
        {"hurdle_apy": math.nan, "days": 1},
        {"hurdle_apy": math.inf, "days": 1},
        {"hurdle_apy": -0.01, "days": 1},
        {"hurdle_apy": 0.05, "days": math.inf},
    ],
)
def test_group_exit_verdict_rejects_nonfinite_or_negative_inputs(
    verdict_inputs: dict[str, float],
) -> None:
    verdict = groups.group_exit_verdict(
        _duma_group(),
        {"status": "OK", "net": 12.0},
        as_of=dt.date(2026, 8, 28),
        **verdict_inputs,
    )

    assert verdict["actionable"] is False
    assert verdict["verdict"].startswith("GROUP_VERDICT_UNPRICED")
    assert verdict["margin"] is None


def test_stale_member_prior_gates_complete_group_exit_and_add() -> None:
    priors = _duma_priors()
    priors["duma-a"]["verified"] = "2026-08-01"
    group = groups.evaluate_groups(priors, _duma_positions()).groups["duma"]
    exit_quote = {
        "status": "OK",
        "actionable": True,
        "gross": 20.0,
        "fee": 0.0,
        "net": 20.0,
        "unfilled_by_leg": {},
    }
    exit_verdict = groups.group_exit_verdict(
        group, exit_quote, as_of=dt.date(2026, 8, 28)
    )
    assert exit_verdict["actionable"] is False
    assert exit_verdict["verdict"].startswith("GROUP_PRIOR_STALE")

    add_quote = {
        "status": "OK",
        "actionable": True,
        "component_deltas": {"covered": 1.0},
        "raw_share_increment": 3.0,
        "edge_value": 0.20,
        "total": 0.56,
        "fair_value": 0.76,
    }
    add_verdict = groups.group_add_verdict(
        group, add_quote, as_of=dt.date(2026, 8, 28)
    )
    assert add_verdict["actionable"] is False
    assert add_verdict["verdict"].startswith("ADD_PRIOR_STALE")


def test_short_dated_group_actions_require_same_day_member_priors() -> None:
    duma_priors = _duma_priors()
    for slug in ("duma-a", "duma-b", "duma-c"):
        duma_priors[slug]["verified"] = "2026-08-27"
    duma = groups.evaluate_groups(duma_priors, _duma_positions()).groups["duma"]

    assert groups.group_prior_issues(
        duma, as_of=dt.date(2026, 8, 28)
    ) == [
        "a prior is stale (1d > 0d)",
        "b prior is stale (1d > 0d)",
        "c prior is stale (1d > 0d)",
    ]

    meta_priors = _meta_priors()
    for slug in ("meta-700", "meta-3b", "meta-4b"):
        meta_priors[slug]["verified"] = "2026-08-20"
    meta = groups.evaluate_groups(meta_priors, _meta_positions()).groups["meta"]
    assert groups.group_prior_issues(
        meta, as_of=dt.date(2026, 8, 28)
    ) == []


def test_buy_walk_charges_each_level_and_group_add_uses_all_in_cost() -> None:
    group = _duma_group()
    legacy_paid = {"takerBaseFee": 1000}
    asks = {"duma-a": 0.05, "duma-b": 0.19, "duma-c": 0.32}
    paid_quotes = {
        slug: groups.walk_asks([{"price": price, "size": 1}], 1, legacy_paid)
        for slug, price in asks.items()
    }
    paid = groups.quote_group_add(group, {"covered": 1}, paid_quotes)

    assert paid["status"] == "OK"
    assert paid["gross"] == pytest.approx(0.56)
    assert paid["total"] == pytest.approx(0.58933)
    assert paid["fair_value"] == pytest.approx(0.76)
    assert groups.group_add_verdict(
        group, paid, as_of=dt.date(2026, 8, 28)
    )["verdict"] == "SKIP_ADD_POLICY_PRICE_CAP"

    fee_free = {"takerBaseFee": 0}
    free_quotes = {
        slug: groups.walk_asks([{"price": price, "size": 1}], 1, fee_free)
        for slug, price in asks.items()
    }
    free = groups.quote_group_add(group, {"covered": 1}, free_quotes)
    assert free["total"] == pytest.approx(0.56)
    assert "POLICY_GATED" in groups.group_add_verdict(
        group, free, as_of=dt.date(2026, 8, 28)
    )["verdict"]


def test_buy_walk_structured_exponent_is_applied_per_level() -> None:
    market = {"feeSchedule": {"rate": 0.25, "exponent": 2, "takerOnly": True}}
    quote = groups.walk_asks(
        [{"price": 0.40, "size": 10}, {"price": 0.30, "size": 10}],
        20,
        market,
    )
    expected_fee = 10 * 0.25 * (0.30 * 0.70) ** 2 + 10 * 0.25 * (0.40 * 0.60) ** 2
    assert quote["gross"] == pytest.approx(7.0)
    assert quote["fee"] == pytest.approx(expected_fee)


def test_partial_component_add_is_unpriced() -> None:
    group = _duma_group()
    quotes = {
        slug: groups.walk_asks([{"price": 0.10, "size": 1}], 1, {"takerBaseFee": 0})
        for slug in ("duma-a", "duma-b", "duma-c")
    }
    quotes["duma-c"] = groups.walk_asks(
        [{"price": 0.10, "size": 0.99}], 1, {"takerBaseFee": 0}
    )

    add = groups.quote_group_add(group, {"covered": 1}, quotes)

    assert add["status"] == "GROUP_UNPRICED"
    assert groups.group_add_verdict(group, add)["actionable"] is False


def test_deindexed_member_makes_group_mark_and_drawdown_unpriced() -> None:
    positions = _duma_positions()
    positions[0]["curPrice"] = 0.001

    group = groups.evaluate_groups(_duma_priors(), positions).groups["duma"]

    assert group["status"] == "OK"
    assert group["mark_status"] == "UNPRICED"
    assert group["mark_value"] is None
    assert group["drawdown_pct"] is None


def test_deindexed_member_blocks_otherwise_actionable_group_add() -> None:
    priors = _meta_priors()
    priors["_groups"]["meta"]["add_policy"]["manual_gate"] = False
    positions = _meta_positions()
    positions[0]["curPrice"] = 0.001
    group = groups.evaluate_groups(priors, positions).groups["meta"]
    component = next(item for item in group["components"] if item["id"] == "pair3")
    delta = 5.0
    quotes = {
        group["positions"][leg_id]["slug"]: groups.walk_asks(
            [{"price": "0.10", "size": "20"}],
            delta * weight,
            {"takerBaseFee": 0},
        )
        for leg_id, weight in component["weights"].items()
    }
    minimums = {slug: 5.0 for slug in quotes}
    add_quote = groups.quote_group_add(
        group,
        {component["id"]: delta},
        quotes,
        minimum_order_by_slug=minimums,
    )

    verdict = groups.group_add_verdict(
        group, add_quote, as_of=dt.date(2026, 8, 28)
    )

    assert group["mark_status"] == "UNPRICED"
    assert add_quote["status"] == "OK"
    assert verdict["actionable"] is False
    assert verdict["verdict"].startswith("ADD_GROUP_MARK_UNPRICED")


def test_group_add_requires_and_respects_exchange_minimum_order_proof() -> None:
    priors = _meta_priors()
    priors["_groups"]["meta"]["add_policy"]["manual_gate"] = False
    group = groups.evaluate_groups(priors, _meta_positions()).groups["meta"]
    component = next(item for item in group["components"] if item["id"] == "pair3")
    minimum_by_leg = {leg_id: 5.0 for leg_id in component["weights"]}
    delta = groups.minimum_executable_component_delta(component, minimum_by_leg)
    assert delta == pytest.approx(5.0)

    quotes = {
        group["positions"][leg_id]["slug"]: groups.walk_asks(
            [{"price": "0.10", "size": "20"}],
            delta * weight,
            {"takerBaseFee": 0},
        )
        for leg_id, weight in component["weights"].items()
    }
    unproven = groups.quote_group_add(
        group, {component["id"]: delta}, quotes
    )
    assert groups.group_add_verdict(
        group, unproven, as_of=dt.date(2026, 8, 28)
    )["verdict"] == "ADD_EXECUTION_MINIMUM_UNPROVEN"

    below_minimum_quotes = {
        group["positions"][leg_id]["slug"]: groups.walk_asks(
            [{"price": "0.10", "size": "20"}],
            weight,
            {"takerBaseFee": 0},
        )
        for leg_id, weight in component["weights"].items()
    }
    below_minimum = groups.quote_group_add(
        group,
        {component["id"]: 1.0},
        below_minimum_quotes,
        minimum_order_by_slug={slug: 5.0 for slug in below_minimum_quotes},
    )
    assert below_minimum["status"] == "GROUP_UNPRICED"
    assert "below minimum order" in below_minimum["issues"][0]

    minimum_by_slug = {slug: 5.0 for slug in quotes}
    proven = groups.quote_group_add(
        group,
        {component["id"]: delta},
        quotes,
        minimum_order_by_slug=minimum_by_slug,
    )
    verdict = groups.group_add_verdict(
        group, proven, as_of=dt.date(2026, 8, 28)
    )
    assert proven["minimum_order_proven"] is True
    assert verdict["actionable"] is True
    assert verdict["verdict"] == "ADD_CLEARS_ALL_GATES"


def test_directional_component_cannot_be_relabelled_nondirectional() -> None:
    priors = _duma_priors()
    priors["_groups"]["duma"]["components"][0]["directional"] = False

    group = groups.evaluate_groups(priors, _duma_positions()).groups["duma"]

    assert group["status"] == "GROUP_BROKEN"
    assert "guaranteed payout" in group["issues"][0]


class _Response:
    def __init__(self, payload: object):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


@pytest.mark.parametrize("malformed_size", [False, True])
def test_exit_cli_replaces_member_rows_with_one_group_row(
    monkeypatch, tmp_path: Path, capsys, malformed_size: bool
) -> None:
    import exit_analysis as exits

    priors_path = tmp_path / "priors.json"
    priors_path.write_text(json.dumps(_duma_priors()))
    positions = _duma_positions()
    if malformed_size:
        positions[0]["size"] = "twenty"

    def get(url: str, **kwargs) -> _Response:
        if "data-api.polymarket.com/positions" in url:
            return _Response(positions)
        if "/clob-markets/" in url:
            condition_id = url.rsplit("/", 1)[-1]
            return _Response(
                {"c": condition_id, "fd": {"r": 0, "e": 1, "to": True}}
            )
        if url.endswith("/book"):
            return _Response({"bids": [{"price": "0.10", "size": "20"}]})
        raise AssertionError(url)

    monkeypatch.setattr(exits, "PRIORS", priors_path)
    monkeypatch.setattr(exits.httpx, "get", get)
    monkeypatch.setattr(sys, "argv", ["exit_analysis.py"])

    assert exits.main() == 0
    output = capsys.readouterr().out
    assert output.count("Duma covered union") == 1
    assert "duma-a" not in output
    assert "duma-b" not in output
    assert "duma-c" not in output
    if malformed_size:
        assert "GROUP_BROKEN" in output
    else:
        assert "full exit=$6.00" in output
        assert "exit=UNPRICED" not in output


def test_marginal_json_emits_one_group_drawdown_and_no_member_actions(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    import check_marginal_apy as marginal

    positions = _duma_positions(marks=(0.05, 0.25, 0.10))
    monkeypatch.setattr(marginal, "_resolve_wallet_address", lambda: "0xabc")
    monkeypatch.setattr(marginal, "_fetch_positions", lambda _addr: positions)
    monkeypatch.setattr(marginal, "_load_priors", lambda _raw=None: {
        slug: ("Yes", prior["p_yes"], "2026-08-28")
        for slug, prior in _duma_priors().items()
        if not slug.startswith("_")
    })
    monkeypatch.setattr(
        marginal.exact_exit, "_execution_fee_market", lambda _condition: {"takerBaseFee": 0}
    )
    monkeypatch.setattr(
        marginal.exact_exit,
        "_walk_bids",
        lambda _asset, size, _market: (size * 0.10, size, 0.0),
    )
    priors_path = tmp_path / "priors.json"
    priors_path.write_text(json.dumps(_duma_priors()))
    monkeypatch.setattr(marginal, "PRIORS_PATH", priors_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_marginal_apy.py", "--json", "--hurdle-apy", "0.03"],
    )

    assert marginal.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["flagged"] == []
    assert payload["holds"] == []
    assert len(payload["drawdowns"]) == 1
    assert payload["drawdowns"][0]["outcome"] == "GROUP"
    assert payload["drawdowns"][0]["drawdown_pct"] == pytest.approx(-29.82)
    assert len(payload["groups"]) == 1


@pytest.mark.parametrize(
    "bad_probability",
    ["not-a-number", math.nan, math.inf, -0.01, 1.01, True, None],
)
def test_marginal_prior_projection_rejects_malformed_probabilities(
    bad_probability: object,
) -> None:
    import check_marginal_apy as marginal

    with pytest.raises(ValueError, match="bad-market: p_yes"):
        marginal._load_priors(
            {"bad-market": {"p_yes": bad_probability, "verified": "2026-08-28"}}
        )


def test_marginal_malformed_group_prior_suppresses_all_actions(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    import check_marginal_apy as marginal

    priors = _duma_priors()
    priors["duma-a"]["p_yes"] = "not-a-number"
    priors_path = tmp_path / "priors.json"
    priors_path.write_text(json.dumps(priors))
    monkeypatch.setattr(marginal, "PRIORS_PATH", priors_path)
    monkeypatch.setattr(marginal, "_resolve_wallet_address", lambda: "0xabc")
    monkeypatch.setattr(marginal, "_fetch_positions", lambda _addr: _duma_positions())
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_marginal_apy.py", "--json", "--hurdle-apy", "0.03"],
    )

    assert marginal.main() == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "malformed prior probability" in captured.err
    assert "all actions suppressed" in captured.err
    assert "Traceback" not in captured.err


def test_kelly_cli_reserves_group_cost_once_and_never_prints_member_kelly(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    import portfolio_kelly as kelly

    wallet = tmp_path / "wallet.json"
    wallet.write_text(json.dumps({"address": "0xabc"}))
    positions = _duma_positions()
    monkeypatch.setattr(kelly, "load_priors", _duma_priors)
    monkeypatch.setattr(kelly, "fetch_positions", lambda _addr: positions)
    monkeypatch.setattr(
        kelly.exact_exit, "_execution_fee_market", lambda _condition: {"takerBaseFee": 0}
    )
    monkeypatch.setattr(
        kelly.httpx,
        "get",
        lambda *_args, **_kwargs: _Response(
            {
                "asks": [{"price": "0.10", "size": "20"}],
                "min_order_size": "5",
            }
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "portfolio_kelly.py",
            "--wallet",
            str(wallet),
            "--bankroll",
            "100",
            "--constrained",
        ],
    )

    assert kelly.main() == 0
    captured = capsys.readouterr()
    assert captured.out.count("duma") == 1
    assert "duma-a" not in captured.out
    assert "duma-b" not in captured.out
    assert "duma-c" not in captured.out
    assert "TOTAL: cost=$11.40" in captured.out
    assert "executable +5" in captured.out
    assert "ADD_ECONOMICS_CLEAR_BUT_POLICY_GATED" in captured.out


@pytest.mark.parametrize("live_suffix", ["", "-current"])
def test_state_audit_legacy_fallback_reports_broken_without_naked_divergence(
    monkeypatch, capsys, live_suffix: str
) -> None:
    import position_state_audit as audit

    today = dt.date.today().isoformat()
    prior_slugs = ("legacy-a", "legacy-b")
    positions = [
        {
            "slug": f"{slug}{live_suffix}",
            "outcome": "Yes",
            "asset": f"asset-{slug}{live_suffix}",
            "size": 20,
            "curPrice": 0.50,
            "endDate": "2027-12-31",
        }
        for slug in prior_slugs
    ]
    priors = {
        slug: {
            "p_yes": 0.90,
            "set_only": "legacy equal set",
            "verified": today,
            "criteria_read": today,
        }
        for slug in prior_slugs
    }
    snapshot = {
        "positions": [
            {"slug": row["slug"], "size": row["size"], "asset": row["asset"]}
            for row in positions
        ]
    }

    def load(name: str, default):
        return {
            "position_condition_ids.json": snapshot,
            "portfolio_kelly_priors.json": priors,
            "opportunity_triggers.json": [],
            "acknowledged_holds.json": [],
        }.get(name, default)

    monkeypatch.setattr(audit, "_live_positions", lambda: positions)
    monkeypatch.setattr(audit, "_load", load)
    monkeypatch.setattr(sys, "argv", ["position_state_audit.py"])

    assert audit.main() == 1
    output = capsys.readouterr().out
    assert "GROUP_BROKEN configuration" in output
    assert "size up" not in output
    assert "trim" not in output
