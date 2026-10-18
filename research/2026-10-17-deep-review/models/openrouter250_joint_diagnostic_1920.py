#!/usr/bin/env python3
"""Offline same-path numerical diagnostics for OpenRouter cases 250 and 112."""
from __future__ import annotations
import gzip, hashlib, json, math, random
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/deep_review_20261017"
N = 200_000
SEED = 20261018182
REGIMES = [
    ("moderation", .45, .035, .065),
    ("historical_growth", .35, .08, .095),
    ("release_boom", .10, .20, .10),
    ("disruption", .10, -.15, .15),
]

def raw_point(summary_path: str, point_date: str) -> tuple[float, str]:
    summary = json.loads((ROOT / summary_path).read_text())
    rec = summary.get("new_snapshot") or summary.get("latest_snapshot")
    raw = gzip.decompress((ROOT / rec.get("gzip_path", rec.get("raw_gzip_path"))).read_bytes())
    actual = hashlib.sha256(raw).hexdigest()
    expected = rec.get("raw_sha256")
    if actual != expected:
        raise ValueError(f"raw source hash mismatch: {summary_path}")
    points = json.loads(raw)["data"]["data"]
    matches = [p for p in points if p["x"] == point_date]
    if len(points) != 53 or len(matches) != 1:
        raise ValueError(f"unexpected point count/date in {summary_path}")
    return sum(matches[0]["ys"].values()) / 1e12, actual

def run(partial: float, remaining_ui: float, n: int = N, seed: int = SEED) -> dict:
    rng = random.Random(seed)
    band250 = band112 = 0
    cells = {"250_yes_112_yes": 0, "250_yes_112_no": 0,
             "250_no_112_yes": 0, "250_no_112_no": 0}
    regime_counts = {r[0]: {"n": 0, "250_yes": 0, "112_yes": 0} for r in REGIMES}
    known = 165.856049857563 + 171.842501724714
    saturday = 18.33824279449
    elapsed_left = remaining_ui / saturday
    for _ in range(n):
        z = rng.random()
        if z < .25:
            s = saturday * math.exp(.25 * rng.gauss(0, 1))
        elif z < .90:
            s = saturday * elapsed_left * math.exp(.35 * rng.gauss(0, 1))
        else:
            s = rng.uniform(0, 36)
        current_week = partial + s
        q = rng.random()
        cumulative = 0.0
        for regime in REGIMES:
            cumulative += regime[1]
            if q <= cumulative:
                break
        name, _, mu, sd = regime
        common = rng.gauss(0, 1)
        weekly = []
        w = current_week
        for _week in range(5):
            g = mu + sd * (.5 * common + math.sqrt(.75) * rng.gauss(0, 1))
            w *= math.exp(g)
            weekly.append(w)
        correction = rng.gauss(0, 2) if rng.random() < .95 else rng.gauss(0, 10)
        total = sum(weekly[1:]) + correction
        y250 = 625 <= total < 675
        y112 = 725 <= total < 775
        band250 += y250
        band112 += y112
        cells[f"250_{'yes' if y250 else 'no'}_112_{'yes' if y112 else 'no'}"] += 1
        rc = regime_counts[name]
        rc["n"] += 1
        rc["250_yes"] += int(y250)
        rc["112_yes"] += int(y112)
    return {
        "n": n, "seed": seed,
        "case250_625_inclusive_675_exclusive": band250 / n,
        "case112_725_inclusive_775_exclusive": band112 / n,
        "joint_band_state_counts_same_draws": cells,
        "joint_band_state_fractions_same_draws": {k: v / n for k, v in cells.items()},
        "regime_counts_and_hits": regime_counts,
    }

def frozen_bindings() -> tuple[dict, str]:
    path = ROOT / "research/2026-10-17-primary-market-review-rules.jsonl.gz"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    selected = {}
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("review_index") in (112, 250):
                i = row["review_index"]
                selected[str(i)] = {
                    "market_id": row["id"],
                    "condition_id": row["conditionId"],
                    "criteria_sha256": row["criteria_sha256"],
                    "question": row["question"],
                }
    if set(selected) != {"112", "250"}:
        raise ValueError("frozen rules did not contain both exact cases")
    return selected, digest

def main() -> None:
    old_partial, old_hash = raw_point("data/deep_review_20261017/openrouter182_current_facts_1350.json", "2026-10-12")
    fresh_partial, fresh_hash = raw_point("data/deep_review_20261017/work/0250_source_update_1800.json", "2026-10-12")
    if abs(old_partial - 153.997357608352) > 1e-12 or abs(fresh_partial - 158.105052314724) > 1e-12:
        raise ValueError("unexpected captured partial-week raw sum")
    # 13:16 vintage from the existing model's inputs.
    old_remaining = 10.749748685685992
    base = run(old_partial, old_remaining)
    if abs(base["case112_725_inclusive_775_exclusive"] - .10867) > 1e-12:
        raise ValueError("did not reproduce the existing 112 band result")
    # Latest 16:59 cache hour, per the documented UTC-weekly UI forecast formula.
    elapsed_fraction = .8695 + .1305 * (16 / 24)
    fresh_remaining = fresh_partial * (1 / elapsed_fraction - 1)
    fresh_pace_total = fresh_partial / elapsed_fraction
    sensitivity = run(fresh_partial, fresh_remaining)
    binding, rules_hash = frozen_bindings()
    # Independent concentrated countermodel: lognormal with median 650T and log-sigma .03.
    lo = (math.log(625) - math.log(650)) / .03
    hi = (math.log(675) - math.log(650)) / .03
    counter_p250 = NormalDist().cdf(hi) - NormalDist().cdf(lo)
    result = {
        "schema": "openrouter_joint_band_diagnostic.v1",
        "review_index": 250,
        "scope": "Numerical model reproduction/sensitivity only; no adopted probability, selection, quote, reserve, or action.",
        "source_paths": [
            "work/0250_resume.json", "work/0250_source_update_1800.json",
            "openrouter_chart_display_semantics_1100.json",
            "openrouter182_current_facts_1350.json",
            "research/2026-10-17-primary-market-review-rules.jsonl.gz",
        ],
        "code_path": "research/2026-10-17-deep-review/models/openrouter250_joint_diagnostic_1920.py",
        "frozen_bindings": {
            "source_sha256": rules_hash,
            "cases": binding,
            "common_window_utc_week_starts": ["2026-10-26", "2026-11-02", "2026-11-09", "2026-11-16"],
            "case250_band_T": "[625,675)",
            "case112_band_T": "[725,775)",
            "measurement": "same summed displayed weekly Totals, so both band events are mutually exclusive",
        },
        "source_integrity": {
            "old_snapshot_sha256_verified": old_hash,
            "latest_snapshot_sha256_verified": fresh_hash,
            "old_partial_raw_sum_T": old_partial,
            "latest_partial_raw_sum_T": fresh_partial,
            "latest_completed_point_count": 52,
            "latest_open_partial_week": "2026-10-12",
            "cachedAt_utc": "2026-10-18T16:59:52.776000Z",
            "cache_time_is_not_actual_usage_cutoff": True,
        },
        "shared_model_parameters": {
            "draws": N, "seed": SEED,
            "future_weekly_paths": 5,
            "regimes_shared_per_path": REGIMES,
            "weekly_innovation_correlation": .25,
            "current_week_cutoff_weights": {"prior_complete_day_18T_remaining": .25, "noisy_UI_remaining_proxy": .65, "uniform_0_to_36T": .10},
            "prior_complete_day_anchor_T": 18.33824279449,
            "rounding_revision_noise": "95% Normal(0,2T), 5% Normal(0,10T), additive to four-week total",
            "existing_source_caveat": "Raw ten-series total is used as approximation; exact displayed aggregate first-publication values are not identified.",
        },
        "existing_vintage_reproduction": {
            "source_vintage": "13:16:29Z capture, cachedAt 12:37:35Z",
            "ui_remaining_proxy_T": old_remaining,
            "case250_probability": base["case250_625_inclusive_675_exclusive"],
            "case112_probability": base["case112_725_inclusive_775_exclusive"],
            "expected_existing_112_value": .10867,
            "reproduction_exact": base["case112_725_inclusive_775_exclusive"] == .10867,
            "joint_band_state_counts_same_paths": base["joint_band_state_counts_same_draws"],
            "joint_band_state_fractions_same_paths": base["joint_band_state_fractions_same_draws"],
        },
        "latest_source_sensitivity": {
            "source_vintage": "17:45:43Z capture, cachedAt 16:59:52Z; raw partial only, not proven data-through time",
            "ui_formula_elapsed_fraction_at_cached_utc_hour_16": elapsed_fraction,
            "ui_remaining_proxy_T": fresh_remaining,
            "ui_projected_week_total_T": fresh_pace_total,
            "cutoff_weights_and_all_other_parameters_unchanged": True,
            "case250_probability": sensitivity["case250_625_inclusive_675_exclusive"],
            "case112_probability": sensitivity["case112_725_inclusive_775_exclusive"],
            "joint_band_state_counts_same_paths": sensitivity["joint_band_state_counts_same_draws"],
            "joint_band_state_fractions_same_paths": sensitivity["joint_band_state_fractions_same_draws"],
        },
        "independent_countermodel": {
            "distribution": "Lognormal, median 650T, natural-log sigma 0.03",
            "case250_interval_T": "[625,675)",
            "case250_probability_analytic": counter_p250,
            "purpose": "Independent shape sensitivity only; not mixed into the shared primary sampler.",
        },
    }
    out = DATA / "work/0250_joint_numeric_1920.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(out.relative_to(ROOT)), "bytes": out.stat().st_size,
                      "old_vintage_p250": base["case250_625_inclusive_675_exclusive"],
                      "old_vintage_p112": base["case112_725_inclusive_775_exclusive"],
                      "latest_p250": sensitivity["case250_625_inclusive_675_exclusive"],
                      "latest_p112": sensitivity["case112_725_inclusive_775_exclusive"],
                      "latest_ui_remaining_T": fresh_remaining,
                      "countermodel_p250": counter_p250}, indent=2))

if __name__ == "__main__":
    main()
