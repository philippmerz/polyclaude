#!/usr/bin/env python3
"""Additive threshold-partition diagnostic for the adopted OpenRouter 250/112 paths."""
from __future__ import annotations
import hashlib, importlib.util, json, random, math
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/deep_review_20261017"
SOURCE_MODEL = ROOT / "research/2026-10-17-deep-review/models/openrouter250_plateau_sensitivity_1925.py"
SOURCE_JSON = DATA / "work/0250_plateau_sensitivity_1925.json"
CURRENT_CHART = DATA / "work/0352_chart_weekly_totals_1220.json"
ADOPTED = ROOT / "research/2026-10-17-deep-review/models/openrouter250_112_primary_1940.json"
OUT = DATA / "work/0352_lower_tail_diagnostic_1225.json"

spec = importlib.util.spec_from_file_location("old_plateau_model", SOURCE_MODEL)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
base_partial, base_remaining, _ = old.get_latest_partial()
base_result = old.simulate(base_partial, base_remaining)
source_summary = json.loads(SOURCE_JSON.read_text())
chart = json.loads(CURRENT_CHART.read_text())
adopted = json.loads(ADOPTED.read_text())

# Repeat the source model's operations and random draws in the same order. The only
# extra operation is deterministic bucketing of the existing four-week total.
def simulate_with_partition(partial: float, remaining: float) -> dict:
    rng = random.Random(old.SEED)
    known = 165.856049857563 + 171.842501724714
    saturday = 18.33824279449
    buckets = {"lt625": 0, "625_675": 0, "675_725": 0, "725_775": 0, "ge775": 0}
    aggregate = {"250_yes": 0, "112_yes": 0, "neither": 0}
    for _ in range(old.N):
        z = rng.random()
        if z < .25:
            s = saturday * math.exp(.25 * rng.gauss(0, 1))
        elif z < .90:
            s = remaining * math.exp(.35 * rng.gauss(0, 1))
        else:
            s = rng.uniform(0, 36)
        week0 = partial + s
        q = rng.random()
        cumul = 0.0
        for branch in old.BRANCHES:
            cumul += branch[1]
            if q <= cumul:
                break
        name, _, mu, sd = branch
        common = rng.gauss(0, 1)
        value = week0
        future = []
        for _week in range(5):
            g = mu + sd * (.5 * common + math.sqrt(.75) * rng.gauss(0, 1))
            value *= math.exp(g)
            future.append(value)
        noise = rng.gauss(0, 2) if rng.random() < .95 else rng.gauss(0, 10)
        total = sum(future[1:]) + noise
        if total < 625:
            buckets["lt625"] += 1
        elif total < 675:
            buckets["625_675"] += 1
        elif total < 725:
            buckets["675_725"] += 1
        elif total < 775:
            buckets["725_775"] += 1
        else:
            buckets["ge775"] += 1
        aggregate["250_yes" if 625 <= total < 675 else "112_yes" if 725 <= total < 775 else "neither"] += 1
    return {"counts": buckets, "fractions": {k: v / old.N for k, v in buckets.items()}, "reconstructed_existing_fractions": {k: v / old.N for k, v in aggregate.items()}}

partition = simulate_with_partition(base_partial, base_remaining)
assert partition["reconstructed_existing_fractions"]["250_yes"] == base_result["three_state_joint_fractions"]["250_yes"] == .10271
assert partition["reconstructed_existing_fractions"]["112_yes"] == base_result["three_state_joint_fractions"]["112_yes"] == .115545
assert sum(partition["counts"].values()) == old.N
assert abs(sum(partition["fractions"].values()) - 1.0) < 1e-12

result = {
    "schema": "openrouter352_lower_tail_diagnostic.v1",
    "compiled_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Unadopted diagnostic only; identical 200,000 draws and RNG call order to existing model, with deterministic non-overlapping total buckets added. No probabilities adopted or action inferred.",
    "shared_path": {"draws": old.N, "seed": old.SEED, "branches": old.BRANCHES, "same_cutoff_weights": {"prior_complete_day_18T_remaining": .25, "latest_UI_remaining_proxy": .65, "uniform_0_to_36T": .10}, "innovation_correlation": .25, "rounding_noise": "95% N(0,2T), 5% N(0,10T)"},
    "input_hashes": {"source_model_sha256": hashlib.sha256(SOURCE_MODEL.read_bytes()).hexdigest(), "source_results_sha256": hashlib.sha256(SOURCE_JSON.read_bytes()).hexdigest(), "chart_summary_sha256": hashlib.sha256(CURRENT_CHART.read_bytes()).hexdigest(), "adopted_model_sha256": hashlib.sha256(ADOPTED.read_bytes()).hexdigest(), "chart_body_sha256": chart["receipt"]["raw_sha256"]},
    "base_replay": {"partial_week_T": base_partial, "remaining_proxy_T": base_remaining, "250_yes": base_result["three_state_joint_fractions"]["250_yes"], "112_yes": base_result["three_state_joint_fractions"]["112_yes"], "exact_match_adopted_raw_joint": {"250": base_result["three_state_joint_fractions"]["250_yes"] == adopted["raw_joint"]["250_yes"], "112": base_result["three_state_joint_fractions"]["112_yes"] == adopted["raw_joint"]["112_yes"]}},
    "partition_T": {"lt625": "(-inf,625)", "625_675": "[625,675)", "675_725": "[675,725)", "725_775": "[725,775)", "ge775": "[775,inf)"},
    "partition": partition,
    "optional_current_anchor": {"performed": False, "reason": "A sensitivity using the newly complete Oct12 week and Oct19 partial would require an additional intrawweek usage-cutoff assumption. This was omitted rather than silently reusing yesterday's cutoff proxy."},
    "source_timing_note": "New 12:17 chart snapshot revises Oct12 raw weekly sum from the 09:33 capture by +0.000006585049T and Oct19 is still partial; see work/0352_chart_weekly_totals_1220.json. This replay intentionally reproduces the model's frozen 17:45 input, not the newer source snapshot."
}
OUT.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"output": str(OUT.relative_to(ROOT)), "bytes": OUT.stat().st_size, "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(), "partition": partition, "base_replay": result["base_replay"]}, indent=2))
