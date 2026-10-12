#!/usr/bin/env python3
"""Project one explicit joint scenario model onto exact shadow market cases.

No forecasting, source retrieval, allocation, or execution occurs here. Scenario
weights and literal-rule bindings are supplied by the reviewer. Unknown facts
stay unknown; conditional scenario probabilities are not calibrated forecasts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("scenario numbers must be finite numeric values")
    try:
        finite = math.isfinite(value)
    except OverflowError as exc:
        raise ValueError("scenario numbers must be finite numeric values") from exc
    if not finite:
        raise ValueError("scenario numbers must be finite numeric values")
    return value


def _predicate(spec, variables):
    if not isinstance(spec, dict) or spec.get("variable") not in variables:
        raise ValueError("predicate must name a declared variable")
    op = spec.get("op")
    keys = {"variable", "op", "value"}
    if op == "range":
        keys = {"variable", "op", "lower", "upper"}
        lower, upper = _number(spec.get("lower")), _number(spec.get("upper"))
        if lower > upper:
            raise ValueError("predicate lower bound exceeds upper bound")
    elif op in {"eq", "le", "ge", "lt", "gt"}:
        _number(spec.get("value"))
    else:
        raise ValueError("unsupported predicate operation")
    if set(spec) != keys:
        raise ValueError("predicate has missing or undeclared fields")


def _truth(spec, values):
    value = values.get(spec["variable"])
    if value is None:
        return None
    op = spec["op"]
    if op == "range":
        return spec["lower"] <= value <= spec["upper"]
    target = spec["value"]
    if op == "eq":
        return value == target
    if op == "le":
        return value <= target
    if op == "ge":
        return value >= target
    if op == "lt":
        return value < target
    return value > target


def project(model: dict, bindings: list[dict], packets: list[dict]) -> dict:
    """Return conditional marginals and a shared truth matrix, never orders.

    Freshness belongs to case_memory and the reviewer. This pure calculation
    accepts a synthetic replay or a shadow review, and always reports that live
    evidence, calibration, and executable economics have not been certified.
    """
    if not isinstance(model, dict) or model.get("purpose") not in {
        "synthetic_replay", "shadow_review"
    }:
        raise ValueError("model purpose must be synthetic_replay or shadow_review")
    variables = model.get("variables")
    states = model.get("states")
    if not isinstance(variables, dict) or not variables:
        raise ValueError("model requires declared variables with type and unit")
    for key, spec in variables.items():
        if (not isinstance(key, str) or not key or not isinstance(spec, dict)
                or spec.get("type") not in {"integer", "number"}
                or not isinstance(spec.get("unit"), str) or not spec["unit"]):
            raise ValueError("model requires declared variables with type and unit")
    if not isinstance(states, list) or not 1 <= len(states) <= 1024:
        raise ValueError("model requires 1..1024 explicit joint states")
    state_ids, weights = set(), []
    for state in states:
        if not isinstance(state, dict):
            raise ValueError("each state must be an object")
        sid, values = state.get("id"), state.get("values")
        if not isinstance(sid, str) or not sid or sid in state_ids:
            raise ValueError("state IDs must be distinct non-empty strings")
        state_ids.add(sid)
        weight = _number(state.get("weight"))
        if not 0 <= weight <= 1:
            raise ValueError("state weights must lie in [0,1]")
        weights.append(weight)
        if not isinstance(values, dict) or set(values) - set(variables):
            raise ValueError("state values must use declared variables")
        for key, value in values.items():
            if value is None:
                continue
            _number(value)
            if variables[key]["type"] == "integer" and value != int(value):
                raise ValueError("integer variable cannot receive a fractional value")
    if not math.isclose(math.fsum(weights), 1, rel_tol=0, abs_tol=1e-12):
        raise ValueError("joint state weights must sum to 1; no silent normalization")
    if not isinstance(bindings, list) or not 1 <= len(bindings) <= 256:
        raise ValueError("requires 1..256 exact case bindings")
    if not isinstance(packets, list):
        raise ValueError("packets must be a list")
    cases, cache_states = {}, {}
    for packet in packets:
        case = packet.get("case") if isinstance(packet, dict) else None
        if not isinstance(case, dict) or not isinstance(case.get("case_key"), str):
            raise ValueError("each packet must contain an exact case")
        if case["case_key"] in cases:
            raise ValueError("duplicate case packet")
        cases[case["case_key"]] = case
        cache_states[case["case_key"]] = packet.get("status", "unknown")
    seen, projections, matrix = set(), [], []
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ValueError("binding must be an object")
        key = binding.get("case_key")
        if key in seen or key not in cases:
            raise ValueError("binding requires one unique known case")
        seen.add(key)
        case = cases[key]
        if (type(case.get("case_version")) is not int or case["case_version"] < 1
                or not isinstance(case.get("condition_id"), str) or not case["condition_id"]):
            raise ValueError("case requires an exact condition and positive integer version")
        for field in ("case_version", "condition_id", "criteria_sha256"):
            if binding.get(field) != case.get(field):
                raise ValueError(f"binding {field} differs from current exact case")
        if type(binding.get("case_version")) is not int:
            raise ValueError("binding case_version must be an integer")
        criteria = case.get("criteria")
        if not isinstance(criteria, dict) or _sha(criteria) != case["criteria_sha256"]:
            raise ValueError("full literal criteria with matching hash are required")
        tokens, labels = case.get("clob_token_ids"), case.get("outcome_labels")
        if (not isinstance(tokens, list) or not isinstance(labels, list)
                or len(tokens) != 2 or len(labels) != 2 or set(labels) != {"Yes", "No"}
                or not all(isinstance(token, str) and token for token in tokens)
                or len(set(tokens)) != 2):
            raise ValueError("case must contain two exact Yes/No outcome tokens")
        if _sha({"condition_id": case["condition_id"], "tokens": tokens}) != key:
            raise ValueError("case_key does not match the exact ordered token identity")
        mapping = dict(zip(labels, tokens))
        if (binding.get("yes_token_id") != mapping["Yes"]
                or binding.get("no_token_id") != mapping["No"]):
            raise ValueError("binding outcome tokens differ from literal outcome order")
        if not isinstance(binding.get("rule_interpretation"), str) or not binding["rule_interpretation"]:
            raise ValueError("binding requires an explicit reviewer rule interpretation")
        spec = binding.get("predicate")
        _predicate(spec, variables)
        if binding.get("expected_unit") != variables[spec["variable"]]["unit"]:
            raise ValueError("binding unit differs from declared scenario variable unit")
        outcomes = [_truth(spec, state["values"]) for state in states]
        true_mass = min(1.0, math.fsum(w for w, value in zip(weights, outcomes) if value is True))
        unknown_mass = math.fsum(w for w, value in zip(weights, outcomes) if value is None)
        upper = min(1.0, true_mass + unknown_mass)
        projections.append({
            "case_key": key, "market_id": case.get("market_id"),
            "case_version": case["case_version"], "condition_id": case["condition_id"],
            "criteria_sha256": case["criteria_sha256"],
            "yes_token_id": mapping["Yes"], "no_token_id": mapping["No"],
            "predicate": spec, "rule_interpretation": binding["rule_interpretation"],
            "expected_unit": binding["expected_unit"],
            "input_case_cache_status": cache_states[key],
            "conditional_p_yes_bounds": [true_mass, upper],
            "conditional_p_yes": true_mass if unknown_mass == 0 else None,
            "unknown_mass": unknown_mass,
        })
        matrix.append(outcomes)
    return {
        "schema_version": 1, "purpose": model["purpose"], "model_sha256": _sha(model),
        "bindings_sha256": _sha(bindings), "case_count": len(projections),
        "projections": projections,
        "joint_outcomes": [{"state_id": state["id"], "weight": weight,
                            "case_truths": [column[i] for column in matrix]}
                           for i, (state, weight) in enumerate(zip(states, weights))],
        "case_order": [row["case_key"] for row in projections],
        "uncertainty_basis": "conditional on supplied scenarios and reviewer rule bindings",
        "calibration_verified": False, "live_evidence_verified": False,
        "criteria_completeness_verified": False, "cache_reuse_certified": False,
        "economic_evaluation_complete": False, "execution_ready": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True)
    parser.add_argument("--bindings", required=True)
    parser.add_argument("--packets", required=True)
    args = parser.parse_args(argv)
    try:
        def read(path):
            return json.loads(Path(path).read_text(encoding="utf-8"))
        print(_json(project(read(args.model), read(args.bindings), read(args.packets))))
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
