"""Replay case490 subjective Google scenarios; no fit, network or execution."""
import json
import math
from pathlib import Path


def project(model):
    rows = model["conditional_published_list_regimes"]
    assert math.isclose(sum(row["mass"] for row in rows), 1)
    conditional = sum(row["mass"] * row["p_lebron_first"] for row in rows)
    raw = model["p_official_list_by_fallback"] * conditional
    assert math.isclose(raw, model["raw_yes"])
    joint = model["compatible_central_winner_masses"]
    assert all(value >= 0 for value in joint.values())
    assert math.isclose(sum(joint.values()), 1)
    assert math.isclose(joint["LeBron490"], model["p_yes"])
    return {
        "raw_yes": raw,
        "rounded_yes": model["p_yes"],
        "rounded_no": 1 - model["p_yes"],
        "ordinary_only_yes": model["p_official_list_by_fallback"] * rows[0]["p_lebron_first"],
        "large_future_story_mass10pct_yes": .98 * (.84 * .006 + .06 * .20 + .10 * .45),
        "known_winner_joint_sum": sum(joint.values()),
    }


if __name__ == "__main__":
    model_path = Path(__file__).with_name("0490_lebron_primary_1810.json")
    print(json.dumps(project(json.loads(model_path.read_text())), indent=2))
