"""Case492 unfitted final-vote-margin scenarios; no network or price input."""
import json
import math
from pathlib import Path


def republican_win(model, baseline_shift=0):
    rows = model["conditional_major_party_regimes"]
    assert math.isclose(sum(row["mass"] for row in rows), 1)
    conditional = 0
    for row in rows:
        z = -(row["mean_D_minus_R_pp"] + baseline_shift) / row["sd_margin_pp"]
        conditional += row["mass"] * (1 + math.erf(z / math.sqrt(2))) / 2
    return (1 - model["other_winner_probability"]) * conditional


if __name__ == "__main__":
    p = Path(__file__).with_name("0492_wisconsin_primary_1820.json")
    model = json.loads(p.read_text())
    raw = republican_win(model)
    assert math.isclose(raw, model["raw_p_republican"])
    print(json.dumps({
        "raw_republican": raw,
        "rounded_yes": model["p_yes"],
        "D_margins_plus3pp": republican_win(model, 3),
        "D_margins_minus3pp": republican_win(model, -3),
    }, indent=2))
