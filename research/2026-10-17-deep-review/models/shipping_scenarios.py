"""Reproduce the primary's explicitly subjective shipping scenarios.

Observed transit data are not fitted event probabilities. Branch weights below
are judgmental sensitivities, separated from the mechanical observations.
"""
from pathlib import Path
from statistics import mean, stdev, NormalDist
import json
import math


def calculate():
    packet = json.loads(Path("data/deep_review_20261017/portwatch_fullwindow_sources.json").read_text())
    weekly = json.loads(Path("research/2026-10-17-deep-review/models/bab_weekly_observations.json").read_text())
    last_eight = [x["sum"] for x in weekly["same_weekday_complete_weeks"][-8:]]
    mu, sd = mean(last_eight), stdev(last_eight)
    stable_tail = NormalDist(mu, sd).cdf(169.5)
    eight_day_hazard = 1 - .85 ** (8 / 75)
    short_week = .97 * ((1-eight_day_hazard)*stable_tail + eight_day_hazard*.8) + .03
    cases = {
        "5": {"unrounded": .15*.50 + .85*.005, "p_yes": .08, "range": [.01, .30]},
        "19": {"unrounded": .10*.30 + .90*.01, "p_yes": .04, "range": [.005, .20]},
        "40": {"unrounded": .30*(.50*.80+.50*.05)+.70*.025, "p_yes": .15, "range": [.03, .45]},
        "61": {"unrounded": .45*(.50*.90+.50*.15)+.55*.05, "p_yes": .26, "range": [.08, .65]},
        "215": {"unrounded": short_week, "p_yes": .08, "range": [.01, .30]},
    }
    assert cases["19"]["p_yes"] <= cases["40"]["p_yes"] <= cases["61"]["p_yes"]
    for row in cases.values():
        assert 0 <= row["range"][0] <= row["p_yes"] <= row["range"][1] <= 1
    return {
        "author": "Primary judgment; not an empirical posterior or minimum tail estimate",
        "observed_data_latest": packet["source_timestamps"]["portwatch_max_observation_date"],
        "weekly_normal_sensitivity": {"weeks": last_eight, "mean": mu, "sample_sd": sd,
            "continuity_corrected_under170": stable_tail,
            "eight_day_shock_hazard_from_15pct_over75days": eight_day_hazard,
            "3pct_adverse_source_or_regime_branch_is_judgment_not_observed_frequency": True},
        "cases": cases,
        "limitations": ["Branch weights and event rates are not fitted or calibrated.",
            "Current daily data do not reconstruct every historically published chart or revision.",
            "The broad ranges are scenario ranges, not confidence intervals or entry guarantees."]
    }


if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2))
