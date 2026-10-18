"""Dated, assumption-led CDC-counter projection; not an epidemiological fit."""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

SOURCE = Path("logs/deep_review_20261017/measles208_facts_1815/weekly_2026_aligned.json")
EXPECTED_SHA = "6a7254c53b72fa12aec886538beec1d029383ea54008c76b3f52705cfcef04e3"
OUT = Path(__file__).with_name("measles208_results.json")
SCENARIOS = [
    {"name": "declining", "weight": .35, "growth_mean": -.06,
     "growth_sd": .04, "growth_persistence": .85},
    {"name": "plateau", "weight": .45, "growth_mean": 0,
     "growth_sd": .04, "growth_persistence": .85},
    {"name": "renewed_expansion", "weight": .20, "growth_mean": .12,
     "growth_sd": .06, "growth_persistence": .98},
]


def percentile(values, p):
    return sorted(values)[min(len(values) - 1, int(len(values) * p))]


def simulate(scenario, level, weeks, n=20000, seed=208, backfill_max=350,
             growth_shift=0, count_shape=10):
    rng = random.Random(seed)
    totals = []
    for _ in range(n):
        intensity = level * rng.lognormvariate(-.5 * .20**2, .20)
        growth = rng.gauss(scenario["growth_mean"] + growth_shift,
                           scenario["growth_sd"])
        future = 0
        # Gamma intensity is a continuous proxy for overdispersed counts;
        # rounding error is immaterial at a 3,090-case threshold gap.
        for week in range(math.ceil(weeks)):
            fraction = min(1, weeks - week)
            intensity *= math.exp(growth * fraction)
            future += rng.gammavariate(count_shape, intensity / count_shape) * fraction
            growth = scenario["growth_persistence"] * growth + rng.gauss(0, .025)
        backfill = rng.uniform(0, backfill_max)
        negative_revision = rng.uniform(0, 100) if rng.random() < .10 else 0
        totals.append(4410 + future + backfill - negative_revision)
    return {"n": n, "future_week_equivalents": weeks,
            "p_counter_at_least7500": sum(x >= 7500 for x in totals) / n,
            "median_total": statistics.median(totals),
            "p05_p95_total": [percentile(totals, .05), percentile(totals, .95)]}


def mixture(level, weeks, weights=None, **kwargs):
    scenarios = []
    for i, scenario in enumerate(SCENARIOS):
        result = simulate(scenario, level, weeks, seed=208 + i, **kwargs)
        weight = scenario["weight"] if weights is None else weights[i]
        scenarios.append({**scenario, "actual_weight": weight, "result": result})
    assert math.isclose(sum(x["actual_weight"] for x in scenarios), 1)
    return {"p_yes": sum(x["actual_weight"] * x["result"]["p_counter_at_least7500"]
                         for x in scenarios), "scenarios": scenarios}


def main():
    source_bytes = SOURCE.read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == EXPECTED_SHA
    source = json.loads(source_bytes)
    weeks = source["weeks"]
    assert len(weeks) == 41 and sum(x["cases"] for x in weeks) == 4410
    recent = weeks[-12:-2]
    mature_candidate = recent[-6:]
    level = math.exp(statistics.mean(math.log(x["cases"]) for x in mature_candidate))
    base10 = mixture(level, 10)
    base11 = mixture(level, 11)
    # Publication-time interpretation: strict available counter by Dec31 vs
    # annual count including a later report. Weights are judgment, not history.
    combined = .75 * base10["p_yes"] + .25 * base11["p_yes"]
    sensitivities = {
        "all11weeks": base11["p_yes"],
        "no_prior_backfill": mixture(level, 10, backfill_max=0)["p_yes"],
        "higher_level250": mixture(250, 11)["p_yes"],
        "lower_level150": mixture(150, 10)["p_yes"],
        "expansion_weight40pct": mixture(level, 11, weights=[.25, .35, .40])["p_yes"],
        "persistent_growth_shift5pp": mixture(level, 11, growth_shift=.05)["p_yes"],
    }
    result = {
        "written_utc": datetime.now(timezone.utc).isoformat(), "review_index": 208,
        "before_reading_own_PM_quote": True, "source_path": str(SOURCE),
        "source_sha256": EXPECTED_SHA, "counter": 4410, "threshold": 7500,
        "gap": 3090, "cdc_asof": "2026-10-15T12:00:00-04:00",
        "source_last_two_buckets_excluded_from_level_fit": weeks[-2:],
        "level_fit_rows": mature_candidate, "weekly_level": level,
        "recent10_week_mean": statistics.mean(x["cases"] for x in recent),
        "base_10weeks": base10, "base_11weeks": base11,
        "publication_interpretation_weight_strict10_full11": [.75, .25],
        "raw_mixture_p_yes": combined, "sensitivities": sensitivities,
        "primary_p_yes": None, "primary_range": None,
        "actual_entry_reserve_pp": None,
        "calibration": "Scenario probabilities follow subjective growth/regime/backfill assumptions; no calibrated epidemiological posterior or low-end bound.",
        "limits": [
            "Rash-onset buckets are revised and recent completeness is unknown; dropping two buckets does not prove earlier maturity.",
            "Current state outbreaks can diverge; no assumption that all probable/state-reported cases will enter CDC.",
            "Ten/eleven week equivalents approximate publication/cutoff uncertainty, not an exact modeled release calendar.",
            "Branch weights, growth persistence, 20% starting-level uncertainty and 0–350 backfill are judgments, not fitted frequencies.",
            "No seasonal winter multiplier: CDC says measles is not seasonal; travel/undervaccinated clusters can still change spread.",
            "Negative revisions, source outage/fallback and adjudication can change the published counter outcome.",
        ],
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"raw_p": combined, "level": level,
                      "base10": base10["p_yes"], "base11": base11["p_yes"],
                      "sensitivities": sensitivities}))


if __name__ == "__main__":
    main()
