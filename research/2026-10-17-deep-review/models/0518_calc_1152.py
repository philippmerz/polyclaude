"""Offline source-number scenario calculation. No quotes or account access."""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[3]
PARAMS = Path(__file__).with_name("0518_parameters_1152.json")
p = json.loads(PARAMS.read_text())
raw = gzip.decompress((ROOT / p["history_body"]).read_bytes())
assert hashlib.sha256(raw).hexdigest() == p["history_raw_sha256"]
d = json.loads(raw)
h = sorted(d["history"], key=lambda x: x["window_end"])
hours = (datetime.fromisoformat(p["target_window_end"].replace("Z", "+00:00"))
         - datetime.fromisoformat(h[-1]["window_end"].replace("Z", "+00:00"))).total_seconds() / 3600
assert h[-1]["window_end"] == p["source_window_end"] and hours == 53
values = [100 * float(x["value"]) for x in h]
increments = [b - a for a, b in zip(values, values[1:])]
drift = statistics.mean(increments)
anchor = 100 * float(h[-1]["calculation"]["final_math"]["raw_value"])
terms = h[-1]["calculation"]["weighted_terms"]
weight_sum = sum(Decimal(t["weight"]) for t in terms)
weighted_mean = sum(Decimal(t["median"]) * Decimal(t["weight"]) for t in terms) / weight_sum
assert weighted_mean.quantize(Decimal(".001"), rounding=ROUND_HALF_UP) == Decimal(h[-1]["value"])
cdf = lambda z: .5 * (1 + math.erf(z / math.sqrt(2)))
lo, hi = p["latent_band_pct"]
prob = lambda mean, sigma: cdf((hi - mean) / sigma) - cdf((lo - mean) / sigma)
regimes = []
for r in p["ordinary_regimes"]:
    mean = anchor + r.get("mu_shift_pp", 0) + r.get("historical_drift_multiplier", 0) * drift * hours
    regimes.append({**r, "mean_pct": mean, "p_band": prob(mean, r["sigma_pp"])})
ordinary = sum(r["weight"] * r["p_band"] for r in regimes)
result = sum(r["weight"] * (ordinary if r["conditional"] == "ordinary_gaussian_mixture" else r["p_band"])
             if "conditional" in r else r["weight"] * r["p_band"]
             for r in p["publication_regimes"])
out = {
    "schema": "primary_senate_odds518_calculation.v1",
    "parameters_sha256": hashlib.sha256(PARAMS.read_bytes()).hexdigest(),
    "history_raw_sha256": hashlib.sha256(raw).hexdigest(),
    "n": len(h), "hours": hours, "raw_anchor_pct": anchor,
    "published_anchor_pct": values[-1], "hourly_drift_pp": drift,
    "hourly_sd_pp": statistics.pstdev(increments),
    "iid_diffusion_sigma53h_diagnostic_only": statistics.pstdev(increments) * math.sqrt(hours),
    "latest_weight_sum": str(weight_sum), "latest_weighted_mean": str(weighted_mean),
    "regimes": regimes, "ordinary_p_band": ordinary, "p_yes_raw": result,
    "countermodels": [{**r, "p_band": prob(r["mean_pct"], r["sigma_pp"])} for r in p["countermodels"]],
    "limits": "Unfitted forward weights/volatility/drift and publication assumptions. No election-winning probability, no source reliability guarantee, no quote or trade."
}
print(json.dumps(out, separators=(",", ":")))
