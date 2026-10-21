"""Offline primary scenario calculation; no account, quote or network access."""
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PARAMS = HERE / "0514_primary_parameters_1114.json"
p = json.loads(PARAMS.read_text())
rng = np.random.default_rng(p["seed"])
n = p["sample_n"]
regimes = p["growth_regimes"]
which = rng.choice(len(regimes), n, p=[x["weight"] for x in regimes])
mu = np.array([x["mu"] for x in regimes])[which]
sigma = np.array([x["sigma"] for x in regimes])[which]
rho = p["rho_innovations"]
noise = (math.sqrt(rho) * rng.normal(size=(n, 1))
         + math.sqrt(1 - rho) * rng.normal(size=(n, 5)))
weekly = p["anchor_T"] * np.exp(np.cumsum(mu[:, None] + sigma[:, None] * noise, axis=1))
# Oct19 is a projected current week; only columns1..4 enter the contract.
error_sigma = np.where(rng.random(n) < .95, 2.0, 10.0)
error = rng.normal(size=n) * error_sigma
total = weekly[:, 1:].sum(axis=1) + error
hit = (total >= 675) & (total < 725)
held_hit = (total >= 725) & (total < 775)
rounded_total = np.rint(weekly[:, 1:]).sum(axis=1) + error
rounded_hit = (rounded_total >= 675) & (rounded_total < 725)
normal_cdf = lambda z: .5 * (1 + math.erf(z / math.sqrt(2)))
concentrated = (normal_cdf(math.log(725 / 700) / .03)
                - normal_cdf(math.log(675 / 700) / .03))
out = {
    "schema": "primary_openrouter514_calculation.v1",
    "parameters_sha256": hashlib.sha256(PARAMS.read_bytes()).hexdigest(),
    "n": n,
    "p514_raw": float(hit.mean()),
    "p514_mc_standard_error_conditional_on_model": float(np.sqrt(hit.mean() * (1 - hit.mean()) / n)),
    "p112_diagnostic_not_prior_change": float(held_hit.mean()),
    "joint": {"514only": float(hit.mean()), "112only": float(held_hit.mean()),
              "neither": float((~hit & ~held_hit).mean()), "both": int((hit & held_hit).sum())},
    "total_T_quantiles_05_50_95": np.quantile(total, [.05, .50, .95]).tolist(),
    "round_each_week_nearest_whole_T_sensitivity": float(rounded_hit.mean()),
    "current_projected_week_below_observed_partial_fraction": float((weekly[:, 0] < p["current_week_partial_T"]).mean()),
    "per_regime": {x["name"]: {"n": int((which == i).sum()),
                    "p514": float(hit[which == i].mean()),
                    "p112": float(held_hit[which == i].mean())}
                   for i, x in enumerate(regimes)},
    "countermodel_median700_logsigma03_p514": concentrated,
    "limits": "Simulation error is not model error. No empirical mixture fit, calibrated bounds, actual usage cutoff, first-display archive or current UI guarantee. Hypothetical rounding/error are sensitivities, not measured distributions. No quote or financial action."
}
print(json.dumps(out, separators=(",", ":")))
