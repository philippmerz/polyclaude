#!/usr/bin/env python3
"""Pure, fail-closed analytics for multi-leg economic positions.

Per-leg edge, drawdown, and exit math is unsafe for structures whose payoff
depends on keeping several contracts together.  The canonical topology lives
under ``_groups`` in ``notes/portfolio_kelly_priors.json``.  This module turns
that topology plus a position snapshot into one economic row per group.

No network, wallet, clock, or file writes live here.  Advisory scripts supply
their already-fetched positions and (when needed) depth-walked exit quotes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import datetime as dt
import math
from typing import Any

from pm_fees import fee_per_share


SIZE_TOLERANCE = 0.01
DEPTH_TOLERANCE = 1e-9
VALUE_TOLERANCE = 1e-6
SHORT_DATED_WINDOW_DAYS = 30


class GroupConfigError(ValueError):
    """The topology cannot safely be interpreted."""


@dataclass(frozen=True)
class GroupSpec:
    group_id: str
    label: str
    event_model: dict[str, Any]
    legs: dict[str, dict[str, str]]
    components: tuple[dict[str, Any], ...]
    expected_qty: dict[str, float]
    quantity_mode: str
    add_gate: str
    add_policy: dict[str, Any]


@dataclass
class GroupBook:
    groups: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_slug: dict[str, str] = field(default_factory=dict)
    by_asset: dict[str, str] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


_BLANK_GROUP_ID = "malformed-group:<blank-id>"


def _protected_group_id(raw_id: Any) -> str:
    """Return a non-empty ID usable even before strict schema validation."""
    normalized = str(raw_id).strip()
    return normalized or _BLANK_GROUP_ID


def protected_slug_map(priors: dict[str, Any]) -> dict[str, str]:
    """Best-effort protection map independent of strict topology parsing.

    A malformed schema must never re-enable the very per-leg advice the schema
    exists to suppress.  Extract exact slugs from both raw groups and legacy
    markers before validation; strict parsing can then fail without fallthrough.
    """
    protected: dict[str, str] = {}
    if not isinstance(priors, dict):
        return protected
    raw_groups = priors.get("_groups")
    if isinstance(raw_groups, dict):
        for raw_id, raw_group in raw_groups.items():
            if not isinstance(raw_group, dict):
                continue
            legs = raw_group.get("legs")
            if not isinstance(legs, dict):
                continue
            for raw_leg in legs.values():
                if isinstance(raw_leg, dict) and isinstance(raw_leg.get("slug"), str):
                    slug = raw_leg["slug"].strip()
                    if slug:
                        protected[slug] = _protected_group_id(raw_id)
    for slug, prior in priors.items():
        if str(slug).startswith("_") or not isinstance(prior, dict):
            continue
        if prior.get("set_only") or prior.get("arb_paired"):
            marker = prior.get("set_only") or prior.get("arb_paired")
            protected.setdefault(str(slug), f"legacy:{str(marker).strip()}")
    return protected


def protected_asset_map(priors: dict[str, Any]) -> dict[str, str]:
    """Best-effort immutable token→group map for live slug-drift suppression."""
    protected: dict[str, str] = {}
    if not isinstance(priors, dict):
        return protected
    raw_groups = priors.get("_groups")
    if not isinstance(raw_groups, dict):
        return protected
    for raw_id, raw_group in raw_groups.items():
        if not isinstance(raw_group, dict) or not isinstance(raw_group.get("legs"), dict):
            continue
        for raw_leg in raw_group["legs"].values():
            if isinstance(raw_leg, dict) and isinstance(raw_leg.get("asset"), str):
                asset = raw_leg["asset"].strip()
                if asset:
                    group_id = _protected_group_id(raw_id)
                    previous = protected.get(asset)
                    protected[asset] = (
                        group_id
                        if previous is None or previous == group_id
                        else f"ambiguous-asset:{asset}"
                    )
    return protected


def _populate_broken_group_placeholders(
    priors: dict[str, Any], book: GroupBook, issue: str
) -> None:
    """Expose protected structures even when strict parsing fails globally.

    Consumers suppress member legs from ``by_slug`` and report structures from
    ``groups``. Leaving the latter empty made a malformed topology look like
    "zero protected groups" despite the former correctly suppressing actions.
    """
    labels: dict[str, str] = {}
    if isinstance(priors, dict):
        raw_groups = priors.get("_groups")
        if isinstance(raw_groups, dict):
            for raw_id, raw_group in raw_groups.items():
                group_id = _protected_group_id(raw_id)
                raw_label = raw_group.get("label") if isinstance(raw_group, dict) else None
                if isinstance(raw_label, str) and raw_label.strip():
                    labels.setdefault(group_id, raw_label.strip())
        for slug, prior in priors.items():
            if str(slug).startswith("_") or not isinstance(prior, dict):
                continue
            marker = prior.get("set_only") or prior.get("arb_paired")
            if marker:
                marker_text = str(marker).strip()
                labels.setdefault(
                    f"legacy:{marker_text}", marker_text or "Malformed protected group"
                )

    protected_ids = {
        group_id
        for group_id in (*book.by_slug.values(), *book.by_asset.values())
        if isinstance(group_id, str) and group_id
    }
    for group_id in sorted(protected_ids):
        if group_id in book.groups:
            continue
        label = labels.get(group_id)
        if label is None:
            if group_id == _BLANK_GROUP_ID:
                label = "Unnamed protected group"
            elif group_id.startswith("legacy:"):
                label = group_id.removeprefix("legacy:") or "Malformed protected group"
            elif group_id.startswith("ambiguous-asset:"):
                label = "Ambiguous protected-token membership"
            else:
                label = group_id
        book.groups[group_id] = {
            "group_id": group_id,
            "label": label,
            "status": "GROUP_BROKEN",
            "actionable": False,
            "issues": [issue],
            "expected_qty": {},
            "slugs": sorted(
                slug for slug, owner in book.by_slug.items() if owner == group_id
            ),
        }


def _finite_number(value: Any, *, name: str, minimum: float | None = None) -> float:
    if isinstance(value, bool):
        raise GroupConfigError(f"{name} is boolean, not numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise GroupConfigError(f"{name} is not numeric") from exc
    if not math.isfinite(number):
        raise GroupConfigError(f"{name} is not finite")
    if minimum is not None and number < minimum:
        raise GroupConfigError(f"{name} is below {minimum:g}")
    return number


def parse_group_specs(priors: dict[str, Any]) -> dict[str, GroupSpec]:
    """Parse the canonical ``_groups`` topology, raising on any ambiguity."""
    if not isinstance(priors, dict):
        raise GroupConfigError("portfolio priors are not an object")
    raw_groups = priors.get("_groups")
    if not isinstance(raw_groups, dict) or not raw_groups:
        raise GroupConfigError("portfolio priors have no non-empty _groups object")

    specs: dict[str, GroupSpec] = {}
    all_slugs: dict[str, str] = {}
    all_assets: dict[str, str] = {}
    for raw_id, raw in raw_groups.items():
        group_id = str(raw_id).strip()
        if not group_id or not isinstance(raw, dict):
            raise GroupConfigError("group id/configuration is malformed")
        if group_id in specs:
            raise GroupConfigError(f"normalized group id {group_id!r} is duplicated")
        label = raw.get("label")
        if not isinstance(label, str) or not label.strip():
            raise GroupConfigError(f"{group_id}: label is missing")
        add_gate = raw.get("add_gate")
        if not isinstance(add_gate, str) or not add_gate.strip():
            raise GroupConfigError(f"{group_id}: add_gate is missing")
        add_policy = raw.get("add_policy")
        if not isinstance(add_policy, dict):
            raise GroupConfigError(f"{group_id}: add_policy is missing")
        allowed_policy_keys = {
            "manual_gate",
            "max_component_all_in",
            "min_component_fair",
            "max_total_component_quantity",
        }
        unknown_policy_keys = set(add_policy) - allowed_policy_keys
        if unknown_policy_keys:
            raise GroupConfigError(
                f"{group_id}: unknown add_policy keys: "
                + ", ".join(sorted(unknown_policy_keys))
            )
        if not isinstance(add_policy.get("manual_gate"), bool):
            raise GroupConfigError(f"{group_id}: add_policy.manual_gate must be boolean")
        event_model = raw.get("event_model")
        quantity_mode = raw.get("quantity_mode", "fixed")
        if quantity_mode not in ("fixed", "proportional_live"):
            raise GroupConfigError(
                f"{group_id}: quantity_mode must be fixed or proportional_live"
            )
        legs_raw = raw.get("legs")
        components_raw = raw.get("components")
        if not isinstance(event_model, dict):
            raise GroupConfigError(f"{group_id}: event_model is not an object")
        if not isinstance(legs_raw, dict) or len(legs_raw) < 2:
            raise GroupConfigError(f"{group_id}: at least two legs are required")
        if not isinstance(components_raw, list) or not components_raw:
            raise GroupConfigError(f"{group_id}: components must be a non-empty list")

        legs: dict[str, dict[str, str]] = {}
        for raw_leg_id, raw_leg in legs_raw.items():
            leg_id = str(raw_leg_id).strip()
            if not leg_id or not isinstance(raw_leg, dict):
                raise GroupConfigError(f"{group_id}: malformed leg")
            if leg_id in legs:
                raise GroupConfigError(f"{group_id}: normalized leg ids are not unique")
            slug = raw_leg.get("slug")
            outcome = raw_leg.get("outcome")
            asset = raw_leg.get("asset")
            if not isinstance(slug, str) or not slug.strip():
                raise GroupConfigError(f"{group_id}/{leg_id}: slug is missing")
            if outcome not in ("Yes", "No"):
                raise GroupConfigError(f"{group_id}/{leg_id}: outcome must be Yes or No")
            if not isinstance(asset, str) or not asset.strip():
                raise GroupConfigError(f"{group_id}/{leg_id}: asset is missing")
            slug = slug.strip()
            asset = asset.strip()
            if slug in all_slugs:
                raise GroupConfigError(
                    f"{slug}: belongs to both {all_slugs[slug]} and {group_id}"
                )
            all_slugs[slug] = group_id
            if asset in all_assets:
                raise GroupConfigError(
                    f"asset {asset}: belongs to both {all_assets[asset]} and {group_id}"
                )
            all_assets[asset] = group_id
            legs[leg_id] = {"slug": slug, "outcome": outcome, "asset": asset}

        expected = {leg_id: 0.0 for leg_id in legs}
        component_ids: set[str] = set()
        components: list[dict[str, Any]] = []
        for index, raw_component in enumerate(components_raw):
            if not isinstance(raw_component, dict):
                raise GroupConfigError(f"{group_id}: component {index} is malformed")
            component_id = str(raw_component.get("id") or "").strip()
            if not component_id or component_id in component_ids:
                raise GroupConfigError(f"{group_id}: component ids must be unique and non-empty")
            component_ids.add(component_id)
            quantity = _finite_number(
                raw_component.get("quantity"),
                name=f"{group_id}/{component_id} quantity",
                minimum=0.0,
            )
            if quantity <= 0:
                raise GroupConfigError(f"{group_id}/{component_id}: quantity must be positive")
            weights_raw = raw_component.get("weights")
            if not isinstance(weights_raw, dict) or not weights_raw:
                raise GroupConfigError(f"{group_id}/{component_id}: weights are missing")
            weights: dict[str, float] = {}
            for raw_leg_id, raw_weight in weights_raw.items():
                leg_id = str(raw_leg_id)
                if leg_id not in legs:
                    raise GroupConfigError(
                        f"{group_id}/{component_id}: unknown leg {leg_id}"
                    )
                weight = _finite_number(
                    raw_weight,
                    name=f"{group_id}/{component_id}/{leg_id} weight",
                    minimum=0.0,
                )
                if weight <= 0:
                    raise GroupConfigError(
                        f"{group_id}/{component_id}/{leg_id}: weight must be positive"
                    )
                weights[leg_id] = weight
                expected[leg_id] += quantity * weight
            if "directional" not in raw_component or not isinstance(
                raw_component.get("directional"), bool
            ):
                raise GroupConfigError(
                    f"{group_id}/{component_id}: directional must be explicit boolean"
                )
            components.append(
                {
                    "id": component_id,
                    "quantity": quantity,
                    "weights": weights,
                    "directional": bool(raw_component.get("directional", False)),
                }
            )
        unused = [leg_id for leg_id, quantity in expected.items() if quantity <= 0]
        if unused:
            raise GroupConfigError(f"{group_id}: legs unused by components: {', '.join(unused)}")

        kind = event_model.get("kind")
        if kind == "exclusive":
            covered = event_model.get("covered")
            if (
                not isinstance(covered, list)
                or not all(isinstance(leg_id, str) for leg_id in covered)
                or len(covered) != len(set(covered))
                or set(covered) != set(legs)
            ):
                raise GroupConfigError(f"{group_id}: exclusive covered legs must equal legs")
            if any(legs[leg_id]["outcome"] != "Yes" for leg_id in legs):
                raise GroupConfigError(f"{group_id}: exclusive bundle currently requires YES legs")
        elif kind == "monotone_yes":
            order = event_model.get("order")
            if (
                not isinstance(order, list)
                or not all(isinstance(leg_id, str) for leg_id in order)
                or len(order) != len(legs)
                or len(order) != len(set(order))
                or set(order) != set(legs)
            ):
                raise GroupConfigError(f"{group_id}: monotone order must list every leg once")
            thresholds = event_model.get("thresholds")
            if not isinstance(thresholds, dict) or set(thresholds) != set(order):
                raise GroupConfigError(
                    f"{group_id}: monotone thresholds must map every ordered leg"
                )
            numeric_thresholds = [
                _finite_number(
                    thresholds[leg_id],
                    name=f"{group_id}/{leg_id} threshold",
                    minimum=0,
                )
                for leg_id in order
            ]
            if any(left >= right for left, right in zip(numeric_thresholds, numeric_thresholds[1:])):
                raise GroupConfigError(f"{group_id}: monotone thresholds must strictly increase")
        else:
            raise GroupConfigError(f"{group_id}: unsupported event_model kind {kind!r}")
        event_id = event_model.get("event_id")
        end_date = event_model.get("end_date")
        if not isinstance(event_id, str) or not event_id.strip():
            raise GroupConfigError(f"{group_id}: event_id is missing")
        if not isinstance(end_date, str) or not end_date.strip():
            raise GroupConfigError(f"{group_id}: end_date is missing")
        try:
            dt.date.fromisoformat(end_date.strip())
        except ValueError as exc:
            raise GroupConfigError(
                f"{group_id}: end_date must be an ISO calendar date"
            ) from exc
        if not isinstance(event_model.get("negative_risk"), bool):
            raise GroupConfigError(f"{group_id}: negative_risk must be boolean")
        for policy_key in (
            "max_component_all_in",
            "min_component_fair",
            "max_total_component_quantity",
        ):
            values = add_policy.get(policy_key, {})
            if not isinstance(values, dict):
                raise GroupConfigError(f"{group_id}: add_policy.{policy_key} must be an object")
            for component_id, raw_value in values.items():
                if component_id not in component_ids:
                    raise GroupConfigError(
                        f"{group_id}: add_policy.{policy_key} names unknown component {component_id}"
                    )
                _finite_number(
                    raw_value,
                    name=f"{group_id} add_policy {policy_key}/{component_id}",
                    minimum=0,
                )

        specs[group_id] = GroupSpec(
            group_id=group_id,
            label=label.strip(),
            event_model=dict(event_model),
            legs=legs,
            components=tuple(components),
            expected_qty=expected,
            quantity_mode=quantity_mode,
            add_gate=add_gate.strip(),
            add_policy=dict(add_policy),
        )
    return specs


def _underlying_yes(prior: dict[str, Any], leg: dict[str, str], group_id: str) -> float:
    """Underlying market P(YES), independent of the held side."""
    if not isinstance(prior, dict):
        raise GroupConfigError(f"{group_id}/{leg['slug']}: exact prior is missing")
    p_yes = (
        _finite_number(prior["p_yes"], name=f"{leg['slug']} p_yes")
        if "p_yes" in prior else None
    )
    p_no = (
        _finite_number(prior["p_no"], name=f"{leg['slug']} p_no")
        if "p_no" in prior else None
    )
    if p_yes is None and p_no is None:
        raise GroupConfigError(f"{group_id}/{leg['slug']}: prior has no p_yes/p_no")
    for label, probability in (("p_yes", p_yes), ("p_no", p_no)):
        if probability is not None and not 0.0 <= probability <= 1.0:
            raise GroupConfigError(
                f"{group_id}/{leg['slug']}: {label} is outside [0,1]"
            )
    if p_yes is not None and p_no is not None:
        if abs(p_yes + p_no - 1.0) > VALUE_TOLERANCE:
            raise GroupConfigError(
                f"{group_id}/{leg['slug']}: p_yes and p_no are inconsistent"
            )
    if p_yes is None:
        p_yes = 1.0 - float(p_no)
    if not 0.0 <= p_yes <= 1.0:
        raise GroupConfigError(f"{group_id}/{leg['slug']}: probability is outside [0,1]")
    held_key = "p_yes" if leg["outcome"] == "Yes" else "p_no"
    if held_key not in prior:
        raise GroupConfigError(
            f"{group_id}/{leg['slug']}: prior lacks held-side {held_key}"
        )
    return p_yes


def _position_cost(position: dict[str, Any]) -> float:
    if "entryFeesUsdc" not in position:
        raise GroupConfigError("entryFeesUsdc is missing")
    fee = _finite_number(position.get("entryFeesUsdc"), name="entryFeesUsdc", minimum=0)
    if position.get("initialValue") is not None:
        initial = _finite_number(position["initialValue"], name="initialValue", minimum=0)
    else:
        initial = (
            _finite_number(position.get("avgPrice"), name="avgPrice", minimum=0)
            * _finite_number(position.get("size"), name="size", minimum=0)
        )
    rounded_sum = initial + fee
    if position.get("grossInitialValue") is None:
        return rounded_sum
    gross = _finite_number(
        position["grossInitialValue"], name="grossInitialValue", minimum=0
    )
    # data-api rounds initialValue/entryFeesUsdc for display while preserving a
    # more precise grossInitialValue. Trust that precision only after proving it
    # reconciles to the stated components within one tenth of a cent.
    if abs(gross - rounded_sum) > 0.001:
        raise GroupConfigError(
            f"grossInitialValue {gross:g} does not reconcile to "
            f"initialValue + entryFeesUsdc {rounded_sum:g}"
        )
    return gross


def position_cost(position: dict[str, Any]) -> float:
    """Public all-in cost parser used when reserving even a broken group."""
    return _position_cost(position)


def _state_model(
    spec: GroupSpec,
    p_yes: dict[str, float],
    expected_qty: dict[str, float],
) -> tuple[list[dict[str, Any]], float]:
    kind = spec.event_model["kind"]
    states: list[dict[str, Any]] = []
    if kind == "exclusive":
        covered = list(spec.event_model["covered"])
        total_p = sum(p_yes[leg_id] for leg_id in covered)
        if total_p > 1.0 + VALUE_TOLERANCE:
            raise GroupConfigError(f"{spec.group_id}: exclusive probabilities sum to {total_p:g}")
        for leg_id in covered:
            states.append(
                {
                    "state": leg_id,
                    "probability": p_yes[leg_id],
                    "payout": expected_qty[leg_id],
                    "truth": {candidate: candidate == leg_id for candidate in covered},
                }
            )
        states.append(
            {
                "state": "outside-covered-range",
                "probability": max(0.0, 1.0 - total_p),
                "payout": 0.0,
                "truth": {candidate: False for candidate in covered},
            }
        )
    else:
        order = list(spec.event_model["order"])
        probs = [p_yes[leg_id] for leg_id in order]
        for left, right in zip(probs, probs[1:]):
            if left + VALUE_TOLERANCE < right:
                raise GroupConfigError(
                    f"{spec.group_id}: monotone YES priors increase ({left:g} < {right:g})"
                )
        state_probabilities = [1.0 - probs[0]]
        state_probabilities.extend(probs[i] - probs[i + 1] for i in range(len(probs) - 1))
        state_probabilities.append(probs[-1])
        state_names = [f"not-{order[0]}"]
        state_names.extend(
            f"{order[i]}-but-not-{order[i + 1]}" for i in range(len(order) - 1)
        )
        state_names.append(order[-1])
        for state_index, (name, probability) in enumerate(zip(state_names, state_probabilities)):
            payout = 0.0
            # In state i, exactly the first i threshold predicates are true.
            true_count = state_index
            for index, leg_id in enumerate(order):
                underlying_true = index < true_count
                held_yes = spec.legs[leg_id]["outcome"] == "Yes"
                if underlying_true == held_yes:
                    payout += expected_qty[leg_id]
            states.append(
                {
                    "state": name,
                    "probability": probability,
                    "payout": payout,
                    "truth": {
                        leg_id: index < true_count
                        for index, leg_id in enumerate(order)
                    },
                }
            )
    if any(state["probability"] < -VALUE_TOLERANCE for state in states):
        raise GroupConfigError(f"{spec.group_id}: state model has a negative probability")
    for state in states:
        if state["probability"] < 0:
            state["probability"] = 0.0
    probability_sum = sum(state["probability"] for state in states)
    if abs(probability_sum - 1.0) > VALUE_TOLERANCE:
        raise GroupConfigError(
            f"{spec.group_id}: state probabilities sum to {probability_sum:g}"
        )
    fair = sum(state["probability"] * state["payout"] for state in states)
    return states, fair


def evaluate_group(
    spec: GroupSpec,
    priors: dict[str, Any],
    positions: list[dict[str, Any]],
    *,
    size_tolerance: float = SIZE_TOLERANCE,
) -> dict[str, Any]:
    """Evaluate one group. Any unsafe ambiguity returns ``GROUP_BROKEN``."""
    base: dict[str, Any] = {
        "group_id": spec.group_id,
        "label": spec.label,
        "status": "GROUP_BROKEN",
        "actionable": False,
        "issues": [],
        "expected_qty": dict(spec.expected_qty),
        "slugs": [leg["slug"] for leg in spec.legs.values()],
    }
    try:
        rows_by_slug: dict[str, list[dict[str, Any]]] = {
            leg["slug"]: [] for leg in spec.legs.values()
        }
        for row in positions:
            if isinstance(row, dict) and row.get("slug") in rows_by_slug:
                rows_by_slug[str(row["slug"])].append(row)

        live_rows: dict[str, dict[str, Any]] = {}
        live_sizes: dict[str, float] = {}
        for leg_id, leg in spec.legs.items():
            rows = rows_by_slug[leg["slug"]]
            if len(rows) != 1:
                qualifier = "missing" if not rows else f"ambiguous duplicate rows ({len(rows)})"
                raise GroupConfigError(f"{spec.group_id}/{leg_id}: {qualifier}")
            row = rows[0]
            if row.get("outcome") != leg["outcome"]:
                raise GroupConfigError(
                    f"{spec.group_id}/{leg_id}: held outcome {row.get('outcome')!r}, "
                    f"expected {leg['outcome']}"
                )
            if str(row.get("asset") or "") != leg["asset"]:
                raise GroupConfigError(
                    f"{spec.group_id}/{leg_id}: live asset does not match configured token"
                )
            if str(row.get("eventId") or "") != str(spec.event_model["event_id"]):
                raise GroupConfigError(
                    f"{spec.group_id}/{leg_id}: live eventId does not match topology"
                )
            if str(row.get("endDate") or "") != str(spec.event_model["end_date"]):
                raise GroupConfigError(
                    f"{spec.group_id}/{leg_id}: live endDate does not match topology"
                )
            if row.get("negativeRisk") is not spec.event_model["negative_risk"]:
                raise GroupConfigError(
                    f"{spec.group_id}/{leg_id}: live negativeRisk does not match topology"
                )
            size = _finite_number(row.get("size"), name=f"{spec.group_id}/{leg_id} size", minimum=0)
            live_sizes[leg_id] = size
            live_rows[leg_id] = row

        if spec.quantity_mode == "proportional_live":
            scale = min(
                live_sizes[leg_id] / spec.expected_qty[leg_id]
                for leg_id in spec.legs
            )
            if scale <= 0:
                raise GroupConfigError(
                    f"{spec.group_id}: proportional-live quantity must be positive"
                )
            expected_qty = {
                leg_id: base_quantity * scale
                for leg_id, base_quantity in spec.expected_qty.items()
            }
        else:
            scale = 1.0
            expected_qty = dict(spec.expected_qty)
        for leg_id, size in live_sizes.items():
            expected = expected_qty[leg_id]
            if abs(size - expected) > size_tolerance + 1e-9:
                raise GroupConfigError(
                    f"{spec.group_id}/{leg_id}: live size {size:g} != expected "
                    f"{expected:g} (tolerance {size_tolerance:g})"
                )

        p_yes = {
            leg_id: _underlying_yes(priors.get(leg["slug"]), leg, spec.group_id)
            for leg_id, leg in spec.legs.items()
        }
        verified_by_leg = {
            leg_id: priors[leg["slug"]].get("verified")
            for leg_id, leg in spec.legs.items()
        }
        if spec.event_model["kind"] == "monotone_yes":
            order = list(spec.event_model["order"])
            for easier, harder in zip(order, order[1:]):
                if 0 < p_yes[harder] - p_yes[easier] <= VALUE_TOLERANCE:
                    p_yes[harder] = p_yes[easier]
        states, state_fair = _state_model(spec, p_yes, expected_qty)
        marginal_fair = sum(
            expected_qty[leg_id]
            * (p_yes[leg_id] if leg["outcome"] == "Yes" else 1.0 - p_yes[leg_id])
            for leg_id, leg in spec.legs.items()
        )
        if abs(state_fair - marginal_fair) > VALUE_TOLERANCE:
            raise GroupConfigError(
                f"{spec.group_id}: state fair {state_fair:g} != marginal fair {marginal_fair:g}"
            )

        member_costs = {
            leg_id: _position_cost(row) for leg_id, row in live_rows.items()
        }
        cost = sum(member_costs.values())
        mark_prices = {
            leg_id: _finite_number(
                row.get("curPrice"),
                name=f"{spec.group_id}/{leg_id} curPrice",
                minimum=0,
            )
            for leg_id, row in live_rows.items()
        }
        if any(price > 1.0 for price in mark_prices.values()):
            raise GroupConfigError(f"{spec.group_id}: curPrice is outside [0,1]")
        deindexed_legs = [
            leg_id
            for leg_id, price in mark_prices.items()
            if price <= 0.005
            and member_costs[leg_id] > 0
            and (
                price * expected_qty[leg_id] - member_costs[leg_id]
            ) / member_costs[leg_id] < -0.50
        ]
        mark = (
            None
            if deindexed_legs
            else sum(
                mark_prices[leg_id] * expected_qty[leg_id]
                for leg_id in live_rows
            )
        )
        total_shares = sum(expected_qty.values())
        components = []
        for component in spec.components:
            per_state_payouts: list[float] = []
            for state in states:
                payout_per_unit = 0.0
                for leg_id, weight in component["weights"].items():
                    held_yes = spec.legs[leg_id]["outcome"] == "Yes"
                    if bool(state["truth"][leg_id]) == held_yes:
                        payout_per_unit += float(weight)
                per_state_payouts.append(payout_per_unit)
            floor_per_unit = min(per_state_payouts)
            if not component["directional"] and floor_per_unit < 1.0 - VALUE_TOLERANCE:
                raise GroupConfigError(
                    f"{spec.group_id}/{component['id']}: non-directional component "
                    f"has only {floor_per_unit:g} guaranteed payout/unit"
                )
            components.append(
                {
                    **component,
                    "quantity": float(component["quantity"]) * scale,
                    "fair_per_unit": sum(
                        state["probability"] * payout
                        for state, payout in zip(states, per_state_payouts)
                    ),
                    "floor_per_unit": floor_per_unit,
                    "state_payouts_per_unit": per_state_payouts,
                }
            )
        result = {
            **base,
            "status": "OK",
            "actionable": True,
            "issues": [],
            "positions": live_rows,
            "expected_qty": expected_qty,
            "p_yes": p_yes,
            "verified_by_leg": verified_by_leg,
            "states": states,
            "event_model": dict(spec.event_model),
            "add_gate": spec.add_gate,
            "add_policy": dict(spec.add_policy),
            "components": components,
            "total_shares": total_shares,
            "cost_basis": cost,
            "mark_value": mark,
            "fair_value": state_fair,
            "edge_value": state_fair - mark if mark is not None else None,
            "drawdown_pct": (
                ((mark - cost) / cost * 100.0) if cost > 0 else 0.0
            ) if mark is not None else None,
            "mark_status": "UNPRICED" if mark is None else "OK",
            "deindexed_legs": deindexed_legs,
            "guaranteed_floor": min(state["payout"] for state in states),
            "maximum_payout": max(state["payout"] for state in states),
        }
        if spec.event_model["kind"] == "exclusive":
            result["union_probability"] = sum(p_yes.values())
            result["covered_payout"] = min(expected_qty.values())
            result["outside_payout"] = 0.0
        return result
    except (GroupConfigError, TypeError, ValueError) as exc:
        base["issues"] = [f"GROUP_BROKEN {spec.group_id}: {exc}"]
        return base


def evaluate_groups(
    priors: dict[str, Any],
    positions: list[dict[str, Any]],
    *,
    size_tolerance: float = SIZE_TOLERANCE,
) -> GroupBook:
    """Evaluate every configured group and retain protection even when broken."""
    book = GroupBook(
        by_slug=protected_slug_map(priors),
        by_asset=protected_asset_map(priors),
    )
    # Exact slug is a topology invariant, but immutable token identity is the
    # suppression fallback: a data-api slug-format drift must break valuation
    # without exposing that same token to naked-leg advice.
    for position in positions:
        if not isinstance(position, dict):
            continue
        asset = str(position.get("asset") or "")
        actual_slug = position.get("slug")
        group_id = book.by_asset.get(asset)
        if group_id and isinstance(actual_slug, str) and actual_slug.strip():
            book.by_slug[actual_slug.strip()] = group_id
    try:
        specs = parse_group_specs(priors)
    except (GroupConfigError, TypeError, ValueError) as exc:
        issue = f"GROUP_BROKEN configuration: {exc}"
        book.issues.append(issue)
        _populate_broken_group_placeholders(priors, book, issue)
        return book

    for group_id, spec in specs.items():
        for leg in spec.legs.values():
            book.by_slug[leg["slug"]] = group_id
        result = evaluate_group(spec, priors, positions, size_tolerance=size_tolerance)
        book.groups[group_id] = result
        book.issues.extend(result["issues"])

    # Migration guard: prose markers suppressing per-leg actions are not a
    # topology. Every protected prior must be represented exactly once here.
    strict_slugs = {
        leg["slug"] for spec in specs.values() for leg in spec.legs.values()
    }
    for slug, prior in priors.items():
        if str(slug).startswith("_") or not isinstance(prior, dict):
            continue
        if prior.get("set_only") or prior.get("arb_paired"):
            if slug not in strict_slugs:
                book.issues.append(
                    f"GROUP_BROKEN {slug}: protected prior is absent from _groups topology"
                )
    return book


def group_issues(priors: dict[str, Any], positions: list[dict[str, Any]]) -> list[str]:
    """Convenience safety-audit interface."""
    return evaluate_groups(priors, positions).issues


def group_prior_issues(
    group: dict[str, Any],
    *,
    as_of: dt.date,
    max_age_days: int = 14,
) -> list[str]:
    """Return member-prior freshness failures for a group-level action."""
    issues: list[str] = []
    verified = group.get("verified_by_leg")
    if group.get("status") != "OK" or not isinstance(verified, dict):
        return ["group prior metadata is unavailable"]
    effective_max_age_days = max_age_days
    try:
        deadline = dt.date.fromisoformat(str(group["event_model"]["end_date"]))
    except (KeyError, TypeError, ValueError):
        issues.append("group deadline is unavailable/malformed")
    else:
        # The state audit requires same-day re-derivation throughout the final
        # 30 days.  Group trade verdicts must enforce the same clock rather
        # than becoming actionable on a prior that the audit already calls
        # stale merely because their generic default is fourteen days.
        if (deadline - as_of).days <= SHORT_DATED_WINDOW_DAYS:
            effective_max_age_days = 0
    for leg_id, raw_date in verified.items():
        try:
            checked = dt.date.fromisoformat(str(raw_date))
        except (TypeError, ValueError):
            issues.append(f"{leg_id} prior is undated/malformed ({raw_date!r})")
            continue
        age = (as_of - checked).days
        if age < 0:
            issues.append(f"{leg_id} prior has future verified date {checked.isoformat()}")
        elif age > effective_max_age_days:
            issues.append(
                f"{leg_id} prior is stale ({age}d > {effective_max_age_days}d)"
            )
    return issues


def quote_group_exit(
    group: dict[str, Any],
    quotes_by_slug: dict[str, dict[str, Any]],
    *,
    depth_tolerance: float = DEPTH_TOLERANCE,
) -> dict[str, Any]:
    """Aggregate full-size fee-aware leg walks; never price a partial group."""
    result: dict[str, Any] = {
        "status": "GROUP_UNPRICED",
        "actionable": False,
        "issues": [],
        "unfilled_by_leg": {},
    }
    if group.get("status") != "OK":
        result["issues"] = [f"{group.get('group_id', 'group')}: topology is broken"]
        return result
    gross = fee = net = 0.0
    try:
        for leg_id, position in group["positions"].items():
            slug = str(position["slug"])
            quote = quotes_by_slug.get(slug)
            if not isinstance(quote, dict):
                raise GroupConfigError(f"{slug}: exit quote is missing")
            quote_gross = _finite_number(quote.get("gross"), name=f"{slug} exit gross", minimum=0)
            quote_fee = _finite_number(quote.get("fee"), name=f"{slug} exit fee", minimum=0)
            quote_net = _finite_number(quote.get("net"), name=f"{slug} exit net", minimum=0)
            if "filled" not in quote or "unfilled" not in quote:
                raise GroupConfigError(
                    f"{slug}: quote lacks explicit filled/unfilled depth proof"
                )
            unfilled = _finite_number(quote.get("unfilled"), name=f"{slug} unfilled", minimum=0)
            expected = float(group["expected_qty"][leg_id])
            filled = _finite_number(
                quote.get("filled"),
                name=f"{slug} filled",
                minimum=0,
            )
            if abs((filled + unfilled) - expected) > depth_tolerance:
                raise GroupConfigError(f"{slug}: quote size does not reconcile to {expected:g}")
            if quote_gross > filled + VALUE_TOLERANCE:
                raise GroupConfigError(
                    f"{slug}: exit gross exceeds the binary payout ceiling"
                )
            if unfilled > depth_tolerance:
                result["unfilled_by_leg"][slug] = unfilled
            if abs((quote_gross - quote_fee) - quote_net) > VALUE_TOLERANCE:
                raise GroupConfigError(f"{slug}: quote net does not equal gross minus fee")
            gross += quote_gross
            fee += quote_fee
            net += quote_net
        if result["unfilled_by_leg"]:
            legs = ", ".join(
                f"{slug}={amount:g}" for slug, amount in result["unfilled_by_leg"].items()
            )
            raise GroupConfigError(f"incomplete depth ({legs})")
        result.update(
            {
                "status": "OK",
                "actionable": True,
                "gross": gross,
                "fee": fee,
                "net": net,
                "net_per_raw_share": net / group["total_shares"] if group["total_shares"] else 0.0,
                "issues": [],
            }
        )
        if group.get("event_model", {}).get("kind") == "exclusive":
            result["synthetic_exit_price"] = net / float(group["covered_payout"])
    except (GroupConfigError, TypeError, ValueError) as exc:
        result["issues"] = [f"GROUP_UNPRICED {group.get('group_id', 'group')}: {exc}"]
    return result


def walk_asks(
    asks: list[dict[str, Any]],
    size: float,
    fee_market: dict[str, Any] | None,
) -> dict[str, float]:
    """Exact all-in taker BUY quote, charging nonlinear fees per fill level."""
    requested = _finite_number(size, name="buy size", minimum=0)
    remaining = requested
    gross = fee = 0.0
    levels: list[tuple[float, float]] = []
    for index, level in enumerate(asks or []):
        if not isinstance(level, dict):
            raise GroupConfigError(f"ask level {index} is malformed")
        price = _finite_number(level.get("price"), name=f"ask {index} price", minimum=0)
        available = _finite_number(level.get("size"), name=f"ask {index} size", minimum=0)
        if price > 1.0:
            raise GroupConfigError(f"ask {index} price is above 1")
        if available > 0:
            levels.append((price, available))
    for price, available in sorted(levels):
        if remaining <= 0:
            break
        take = min(remaining, available)
        gross += take * price
        fee += take * fee_per_share(fee_market, price)
        remaining -= take
    filled = requested - remaining
    return {
        "requested": requested,
        "gross": gross,
        "fee": fee,
        "total": gross + fee,
        "filled": filled,
        "unfilled": max(0.0, remaining),
    }


def minimum_executable_component_delta(
    component: dict[str, Any],
    minimum_order_by_leg: dict[str, Any],
) -> float:
    """Return the smallest component increment executable on every member leg.

    Component weights are raw shares bought per component unit.  Every required
    leg must independently meet its CLOB minimum order size, so the binding
    component increment is ``max(minimum_order / weight)``.
    """
    if not isinstance(component, dict) or not isinstance(component.get("weights"), dict):
        raise GroupConfigError("component weights are missing")
    if not isinstance(minimum_order_by_leg, dict):
        raise GroupConfigError("minimum-order metadata is missing")

    component_id = str(component.get("id") or "component")
    required_deltas: list[float] = []
    for leg_id, raw_weight in component["weights"].items():
        if leg_id not in minimum_order_by_leg:
            raise GroupConfigError(
                f"{component_id}/{leg_id}: minimum-order metadata is missing"
            )
        weight = _finite_number(
            raw_weight,
            name=f"{component_id}/{leg_id} weight",
            minimum=0,
        )
        minimum_order = _finite_number(
            minimum_order_by_leg[leg_id],
            name=f"{component_id}/{leg_id} minimum order",
            minimum=0,
        )
        if weight <= 0 or minimum_order <= 0:
            raise GroupConfigError(
                f"{component_id}/{leg_id}: weight and minimum order must be positive"
            )
        required_deltas.append(minimum_order / weight)
    if not required_deltas:
        raise GroupConfigError(f"{component_id}: component has no executable legs")
    return max(required_deltas)


def quote_group_add(
    group: dict[str, Any],
    component_deltas: dict[str, float],
    quotes_by_slug: dict[str, dict[str, Any]],
    *,
    minimum_order_by_slug: dict[str, Any] | None = None,
    depth_tolerance: float = DEPTH_TOLERANCE,
) -> dict[str, Any]:
    """Price an add expressed in topology components, never in naked legs."""
    result: dict[str, Any] = {
        "status": "GROUP_UNPRICED",
        "actionable": False,
        "issues": [],
        "required_by_slug": {},
        "unfilled_by_leg": {},
    }
    if group.get("status") != "OK":
        result["issues"] = [f"{group.get('group_id', 'group')}: topology is broken"]
        return result
    try:
        component_map = {component["id"]: component for component in group["components"]}
        if not isinstance(component_deltas, dict) or not component_deltas:
            raise GroupConfigError("component deltas are missing")
        requested_by_leg_id = {leg_id: 0.0 for leg_id in group["positions"]}
        fair_increment = 0.0
        raw_share_increment = 0.0
        normalized_deltas: dict[str, float] = {}
        for component_id, raw_delta in component_deltas.items():
            component = component_map.get(component_id)
            if component is None:
                raise GroupConfigError(f"unknown component {component_id}")
            delta = _finite_number(
                raw_delta, name=f"{component_id} add quantity", minimum=0
            )
            if delta <= 0:
                raise GroupConfigError(f"{component_id}: add quantity must be positive")
            normalized_deltas[component_id] = delta
            fair_increment += delta * float(component["fair_per_unit"])
            for leg_id, weight in component["weights"].items():
                leg_delta = delta * float(weight)
                requested_by_leg_id[leg_id] += leg_delta
                raw_share_increment += leg_delta

        gross = fee = total = 0.0
        for leg_id, requested in requested_by_leg_id.items():
            if requested <= 0:
                continue
            position = group["positions"][leg_id]
            slug = str(position["slug"])
            result["required_by_slug"][slug] = requested
            if minimum_order_by_slug is not None:
                if slug not in minimum_order_by_slug:
                    raise GroupConfigError(f"{slug}: minimum-order proof is missing")
                minimum_order = _finite_number(
                    minimum_order_by_slug[slug],
                    name=f"{slug} minimum order",
                    minimum=0,
                )
                if minimum_order <= 0:
                    raise GroupConfigError(f"{slug}: minimum order must be positive")
                if requested + depth_tolerance < minimum_order:
                    raise GroupConfigError(
                        f"{slug}: requested {requested:g} is below minimum order "
                        f"{minimum_order:g}"
                    )
            quote = quotes_by_slug.get(slug)
            if not isinstance(quote, dict):
                raise GroupConfigError(f"{slug}: add quote is missing")
            for required_key in ("requested", "gross", "fee", "total", "filled", "unfilled"):
                if required_key not in quote:
                    raise GroupConfigError(f"{slug}: add quote lacks {required_key}")
            quote_requested = _finite_number(
                quote["requested"], name=f"{slug} requested", minimum=0
            )
            quote_gross = _finite_number(quote["gross"], name=f"{slug} gross", minimum=0)
            quote_fee = _finite_number(quote["fee"], name=f"{slug} fee", minimum=0)
            quote_total = _finite_number(quote["total"], name=f"{slug} total", minimum=0)
            filled = _finite_number(quote["filled"], name=f"{slug} filled", minimum=0)
            unfilled = _finite_number(quote["unfilled"], name=f"{slug} unfilled", minimum=0)
            if abs(quote_requested - requested) > depth_tolerance:
                raise GroupConfigError(
                    f"{slug}: quote requested {quote_requested:g}, need {requested:g}"
                )
            if abs((filled + unfilled) - requested) > depth_tolerance:
                raise GroupConfigError(f"{slug}: add depth does not reconcile")
            if abs((quote_gross + quote_fee) - quote_total) > VALUE_TOLERANCE:
                raise GroupConfigError(f"{slug}: all-in total != gross plus fee")
            if unfilled > depth_tolerance:
                result["unfilled_by_leg"][slug] = unfilled
            gross += quote_gross
            fee += quote_fee
            total += quote_total
        if result["unfilled_by_leg"]:
            legs = ", ".join(
                f"{slug}={amount:g}" for slug, amount in result["unfilled_by_leg"].items()
            )
            raise GroupConfigError(f"incomplete add depth ({legs})")
        result.update(
            {
                "status": "OK",
                "actionable": True,
                "component_deltas": normalized_deltas,
                "gross": gross,
                "fee": fee,
                "total": total,
                "fair_value": fair_increment,
                "edge_value": fair_increment - total,
                "raw_share_increment": raw_share_increment,
                "minimum_order_proven": minimum_order_by_slug is not None,
                "issues": [],
            }
        )
    except (GroupConfigError, TypeError, ValueError) as exc:
        result["issues"] = [f"GROUP_UNPRICED {group.get('group_id', 'group')}: {exc}"]
    return result


def group_add_verdict(
    group: dict[str, Any],
    add_quote: dict[str, Any],
    *,
    as_of: dt.date | None = None,
    max_prior_age_days: int = 14,
) -> dict[str, Any]:
    """Apply machine-readable component caps; manual evidence gates stay closed."""
    if group.get("status") != "OK" or add_quote.get("status") != "OK":
        return {
            "actionable": False,
            "verdict": "ADD_UNPRICED — never fall back to a leg-level buy",
            "margin": None,
        }
    tick_noise = float(add_quote["raw_share_increment"]) * 0.01
    margin = float(add_quote["edge_value"])
    if group.get("mark_status") != "OK":
        return {
            "actionable": False,
            "verdict": "ADD_GROUP_MARK_UNPRICED — de-indexed member requires review",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    if as_of is None:
        return {
            "actionable": False,
            "verdict": "ADD_PRIOR_FRESHNESS_UNCHECKED — re-underwrite required",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    prior_issues = group_prior_issues(
        group, as_of=as_of, max_age_days=max_prior_age_days
    )
    if prior_issues:
        return {
            "actionable": False,
            "verdict": "ADD_PRIOR_STALE — complete-set re-underwrite required",
            "margin": margin,
            "tick_noise": tick_noise,
            "prior_issues": prior_issues,
        }
    deltas = add_quote.get("component_deltas", {})
    if not isinstance(deltas, dict) or len(deltas) != 1:
        return {
            "actionable": False,
            "verdict": "ADD_POLICY_UNPRICED — policy checks require one component alternative",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    component_id, delta = next(iter(deltas.items()))
    delta = float(delta)
    component = next(
        (item for item in group["components"] if item["id"] == component_id), None
    )
    if component is None or delta <= 0:
        return {
            "actionable": False,
            "verdict": "ADD_POLICY_UNPRICED — component is not in the topology",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    policy = group.get("add_policy")
    if not isinstance(policy, dict):
        return {
            "actionable": False,
            "verdict": "ADD_POLICY_UNPRICED — add policy is missing",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    all_in_per_unit = float(add_quote["total"]) / delta
    fair_per_unit = float(add_quote["fair_value"]) / delta
    max_all_in = policy.get("max_component_all_in", {}).get(component_id)
    if max_all_in is not None and all_in_per_unit > float(max_all_in) + VALUE_TOLERANCE:
        return {
            "actionable": False,
            "verdict": "SKIP_ADD_POLICY_PRICE_CAP",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    min_fair = policy.get("min_component_fair", {}).get(component_id)
    if min_fair is not None and fair_per_unit + VALUE_TOLERANCE < float(min_fair):
        return {
            "actionable": False,
            "verdict": "SKIP_ADD_POLICY_FAIR_FLOOR",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    max_total = policy.get("max_total_component_quantity", {}).get(component_id)
    if max_total is not None and float(component["quantity"]) + delta > float(max_total) + VALUE_TOLERANCE:
        return {
            "actionable": False,
            "verdict": "SKIP_ADD_POLICY_SIZE_CAP",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    if margin <= tick_noise:
        return {
            "actionable": False,
            "verdict": "SKIP_ADD_AT_CURRENT_ASK",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    if policy.get("manual_gate") is True:
        return {
            "actionable": False,
            "verdict": "ADD_ECONOMICS_CLEAR_BUT_POLICY_GATED",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    if component.get("directional"):
        return {
            "actionable": False,
            "verdict": "ADD_ECONOMICS_CLEAR_BUT_DIRECTIONAL_REUNDERWRITE_REQUIRED",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    if add_quote.get("minimum_order_proven") is not True:
        return {
            "actionable": False,
            "verdict": "ADD_EXECUTION_MINIMUM_UNPROVEN",
            "margin": margin,
            "tick_noise": tick_noise,
        }
    return {
        "actionable": True,
        "verdict": "ADD_CLEARS_ALL_GATES",
        "margin": margin,
        "tick_noise": tick_noise,
    }


def group_exit_verdict(
    group: dict[str, Any],
    exit_quote: dict[str, Any],
    *,
    hurdle_apy: float = 0.0,
    days: float = 0.0,
    as_of: dt.date | None = None,
    max_prior_age_days: int = 14,
) -> dict[str, Any]:
    """Compare complete-group liquidation/redeployment with resolution fair."""
    if group.get("status") != "OK" or exit_quote.get("status") != "OK":
        return {
            "actionable": False,
            "verdict": "GROUP_UNPRICED — HOLD; never fall back to leg-level action",
            "margin": None,
        }
    try:
        hurdle = _finite_number(hurdle_apy, name="hurdle_apy", minimum=0)
        horizon_days = _finite_number(days, name="days", minimum=0)
    except GroupConfigError as exc:
        return {
            "actionable": False,
            "verdict": f"GROUP_VERDICT_UNPRICED — {exc}",
            "margin": None,
        }
    redeployed = float(exit_quote["net"]) * (
        1.0 + hurdle * horizon_days / 365.0
    )
    fair = float(group["fair_value"])
    # One tick across all sold shares is the minimum materiality floor for a
    # snapshot-based all-leg action.
    tick_noise = float(group["total_shares"]) * 0.01
    margin = redeployed - fair
    if as_of is None:
        return {
            "actionable": False,
            "verdict": "GROUP_PRIOR_FRESHNESS_UNCHECKED — HOLD",
            "margin": margin,
            "exit_then_hurdle": redeployed,
            "hold_to_fair": fair,
            "tick_noise": tick_noise,
        }
    prior_issues = group_prior_issues(
        group, as_of=as_of, max_age_days=max_prior_age_days
    )
    if prior_issues:
        return {
            "actionable": False,
            "verdict": "GROUP_PRIOR_STALE — HOLD pending complete-set re-underwrite",
            "margin": margin,
            "exit_then_hurdle": redeployed,
            "hold_to_fair": fair,
            "tick_noise": tick_noise,
            "prior_issues": prior_issues,
        }
    if margin > tick_noise:
        verdict = "EXIT_COMPLETE_GROUP"
    else:
        verdict = "HOLD_COMPLETE_GROUP"
    return {
        "actionable": True,
        "verdict": verdict,
        "margin": margin,
        "exit_then_hurdle": redeployed,
        "hold_to_fair": fair,
        "tick_noise": tick_noise,
    }


def format_group_summary(
    group: dict[str, Any],
    quote: dict[str, Any] | None = None,
    verdict: dict[str, Any] | None = None,
) -> str:
    """Compact human row shared by advisory CLIs."""
    if group.get("status") != "OK":
        return f"{group.get('label', group.get('group_id', 'group'))}: " + "; ".join(group.get("issues", []))
    if group.get("mark_status") == "OK":
        mark_text = (
            f"mark=${group['mark_value']:.2f} "
            f"drawdown={group['drawdown_pct']:+.1f}%"
        )
    else:
        mark_text = "mark/drawdown=UNPRICED (de-indexed member)"
    text = (
        f"{group['label']}: cost=${group['cost_basis']:.2f} "
        f"{mark_text} fair=${group['fair_value']:.2f} "
        f"floor=${group['guaranteed_floor']:.2f}"
    )
    if quote is None:
        return text
    if quote.get("status") != "OK":
        return text + " | exit=UNPRICED (" + "; ".join(quote.get("issues", [])) + ")"
    verdict = verdict or group_exit_verdict(group, quote)
    return (
        text
        + f" | full exit=${quote['net']:.2f} (fee ${quote['fee']:.2f}) "
        + f"| {verdict['verdict']} ({verdict['margin']:+.2f} vs fair)"
    )
