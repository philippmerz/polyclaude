from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import case_distribution as cd


def inputs():
    model = {
        "purpose": "synthetic_replay",
        "variables": {"temperature": {"type": "integer", "unit": "C"},
                      "other": {"type": "integer", "unit": "C"}},
        "states": [
            {"id": "cold", "weight": .3, "values": {"temperature": 20, "other": 20}},
            {"id": "warm", "weight": .5, "values": {"temperature": 21, "other": 21}},
            {"id": "unknown", "weight": .2, "values": {}},
        ],
    }
    bindings, packets = [], []
    for i, variable in enumerate(("temperature", "other")):
        criteria = {"question": f"Will {variable} exceed 20?",
                    "description": "Synthetic literal test criteria, not a real forecast."}
        tokens = [f"yes-{i}", f"no-{i}"]
        condition = f"condition-{i}"
        key = cd._sha({"condition_id": condition, "tokens": tokens})
        case = {"case_key": key, "case_version": 1, "market_id": f"market-{i}",
                "condition_id": condition, "clob_token_ids": tokens,
                "outcome_labels": ["Yes", "No"], "criteria": criteria,
                "criteria_sha256": cd._sha(criteria)}
        packets.append({"case": case, "status": "unknown", "execution_ready": False})
        bindings.append({
            "case_key": key, "case_version": 1, "condition_id": condition,
            "criteria_sha256": cd._sha(criteria), "yes_token_id": tokens[0],
            "no_token_id": tokens[1], "rule_interpretation": "Strictly exceeds 20 C.",
            "expected_unit": "C",
            "predicate": {"variable": variable, "op": "gt", "value": 20},
        })
    return model, bindings, packets


def test_unknown_weight_is_retained_in_bounds_without_normalizing_known_cases():
    result = cd.project(*inputs())
    for row in result["projections"]:
        assert row["conditional_p_yes_bounds"] == pytest.approx([.5, .7])
        assert row["conditional_p_yes"] is None
        assert row["unknown_mass"] == pytest.approx(.2)
    assert result["execution_ready"] is False
    assert result["calibration_verified"] is False
    assert result["live_evidence_verified"] is False


def test_joint_states_preserve_dependence_instead_of_multiplying_marginals():
    result = cd.project(*inputs())
    assert [row["case_truths"] for row in result["joint_outcomes"]] == [
        [False, False], [True, True], [None, None]
    ]
    # The two cases are perfectly coupled in these declared states.
    assert not any(row["case_truths"] in ([True, False], [False, True])
                   for row in result["joint_outcomes"])


@pytest.mark.parametrize("op,value,expected", [
    ("eq", 20, [.3, .5]), ("le", 20, [.3, .5]), ("ge", 21, [.5, .7]),
    ("lt", 21, [.3, .5]), ("gt", 20, [.5, .7]),
])
def test_exact_threshold_comparators(op, value, expected):
    model, bindings, packets = inputs()
    bindings[0]["predicate"].update(op=op, value=value)
    result = cd.project(model, bindings, packets)
    assert result["projections"][0]["conditional_p_yes_bounds"] == pytest.approx(expected)


def test_range_includes_both_endpoints():
    model, bindings, packets = inputs()
    bindings[0]["predicate"] = {"variable": "temperature", "op": "range", "lower": 20, "upper": 21}
    assert cd.project(model, bindings, packets)["projections"][0]["conditional_p_yes_bounds"] == pytest.approx([.8, 1])


@pytest.mark.parametrize("field,new", [
    ("condition_id", "other-condition"), ("case_version", 2),
    ("criteria_sha256", "0" * 64), ("yes_token_id", "no-0"),
])
def test_wrong_exact_instrument_or_semantics_binding_is_rejected(field, new):
    model, bindings, packets = inputs()
    bindings[0][field] = new
    with pytest.raises(ValueError):
        cd.project(model, bindings, packets)


def test_tampered_or_budget_omitted_full_criteria_are_rejected():
    model, bindings, packets = inputs()
    packets[0]["case"]["criteria"]["description"] += " altered"
    with pytest.raises(ValueError, match="full literal"):
        cd.project(model, bindings, packets)
    packets[0]["case"]["criteria"] = None
    with pytest.raises(ValueError, match="full literal"):
        cd.project(model, bindings, packets)


def test_swapped_literal_outcome_order_is_not_inferred_from_token_position():
    model, bindings, packets = inputs()
    packets[0]["case"]["outcome_labels"] = ["No", "Yes"]
    with pytest.raises(ValueError, match="outcome tokens"):
        cd.project(model, bindings, packets)
    bindings[0]["yes_token_id"], bindings[0]["no_token_id"] = "no-0", "yes-0"
    result = cd.project(model, bindings, packets)
    assert result["projections"][0]["yes_token_id"] == "no-0"


@pytest.mark.parametrize("weight", [float("nan"), float("inf"), -0.1, True, "0.3"])
def test_invalid_scenario_weights_are_rejected(weight):
    model, bindings, packets = inputs()
    model["states"][0]["weight"] = weight
    with pytest.raises(ValueError):
        cd.project(model, bindings, packets)


def test_incomplete_weights_and_fractional_integer_values_are_rejected():
    model, bindings, packets = inputs()
    model["states"][0]["weight"] = .1
    with pytest.raises(ValueError, match="sum to 1"):
        cd.project(model, bindings, packets)
    model["states"][0]["weight"] = .3
    model["states"][0]["values"]["temperature"] = 20.4
    with pytest.raises(ValueError, match="fractional"):
        cd.project(model, bindings, packets)


def test_no_unreviewed_predicate_operations_or_extra_fields():
    model, bindings, packets = inputs()
    bindings[0]["predicate"]["op"] = "eval"
    with pytest.raises(ValueError, match="unsupported"):
        cd.project(model, bindings, packets)
    bindings[0]["predicate"]["op"] = "gt"
    bindings[0]["predicate"]["fallback"] = "lowest"
    with pytest.raises(ValueError, match="undeclared fields"):
        cd.project(model, bindings, packets)


def test_known_complete_distribution_returns_conditional_marginal_only():
    model, bindings, packets = inputs()
    model["states"][2]["values"] = {"temperature": 22, "other": 20}
    result = cd.project(model, bindings, packets)
    assert result["projections"][0]["conditional_p_yes"] == pytest.approx(.7)
    assert result["projections"][1]["conditional_p_yes"] == pytest.approx(.5)
    assert result["economic_evaluation_complete"] is False


def test_binding_unit_must_match_the_explicit_scenario_variable():
    model, bindings, packets = inputs()
    bindings[0]["expected_unit"] = "F"
    with pytest.raises(ValueError, match="binding unit"):
        cd.project(model, bindings, packets)


def test_stale_input_status_is_visible_and_does_not_certify_reuse():
    model, bindings, packets = inputs()
    packets[0]["status"] = "stale"
    result = cd.project(model, bindings, packets)
    assert result["projections"][0]["input_case_cache_status"] == "stale"
    assert result["cache_reuse_certified"] is False
    assert result["criteria_completeness_verified"] is False


def test_projection_does_not_mutate_case_model_or_binding_records():
    source = inputs()
    before = copy.deepcopy(source)
    cd.project(*source)
    assert source == before


def test_cli_emits_same_shadow_result(tmp_path, capsys):
    paths = []
    for name, value in zip(("model", "bindings", "packets"), inputs()):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value))
        paths.extend([f"--{name}", str(path)])
    assert cd.main(paths) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["case_count"] == 2
    assert result["execution_ready"] is False
