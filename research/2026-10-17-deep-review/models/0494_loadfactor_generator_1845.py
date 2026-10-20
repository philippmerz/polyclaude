"""Unfitted case494 load-factor/printed-precision mixture; no price or network."""
import json
import math
from pathlib import Path


def exceed(model, threshold, mean_shift=0):
    regimes = model["load_factor_percent_regimes"]
    assert math.isclose(sum(row["mass"] for row in regimes), 1)
    return sum(
        row["mass"] * (1 + math.erf(
            (row["mean_pct"] + mean_shift - threshold)
            / row["sd_percentage_points"] / math.sqrt(2)
        )) / 2
        for row in regimes
    )


def probability(model, mean_shift=0):
    printed = model["one_decimal_reporting_probability"]
    normal = printed * exceed(model, 84.95, mean_shift)
    precise = (1 - printed) * exceed(model, 85, mean_shift)
    return model["timely_metric_probability"] * (normal + precise)


if __name__ == "__main__":
    p = Path(__file__).with_name("0494_ual_primary_1845.json")
    model = json.loads(p.read_text())
    result = probability(model)
    assert math.isclose(result, model["raw_yes"])
    print(json.dumps({
        "raw_yes": result,
        "rounded_yes": model["p_yes"],
        "mean_minus_half_point": probability(model, -.5),
        "mean_plus_half_point": probability(model, .5),
        "all_one_decimal_yes": .99 * exceed(model, 84.95),
        "all_higher_precision_yes": .99 * exceed(model, 85),
    }, indent=2))
