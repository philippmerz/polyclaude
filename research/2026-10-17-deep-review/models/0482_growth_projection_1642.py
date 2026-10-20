"""Offline DOGE continuous log-price barrier scenarios; no market orders."""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/deep_review_20261017/work/0482_root_data_1640.json"
OUTPUT = Path(__file__).with_name("0482_growth_projection_1642.json")


def project():
    source = json.loads(DATA.read_text())
    horizon = source["days_to_final_candle_close"] / 365
    barrier = source["log_threshold"]

    def normal_cdf(x):
        return 0.5 * math.erfc(-x / math.sqrt(2))

    def hit_probability(log_drift, volatility):
        scaled = volatility * math.sqrt(horizon)
        return (normal_cdf((log_drift * horizon - barrier) / scaled)
                + math.exp(2 * log_drift * barrier / volatility**2)
                * normal_cdf((-log_drift * horizon - barrier) / scaled))

    definitions = [
        ("ordinary", 0.80, 1.0, source["returns"]["60"]["annualized_log_vol"]),
        ("broad_crypto_rally", 0.15, 2.0, 1.5),
        ("DOGE_mania", 0.05, 4.0, 2.0),
    ]
    scenarios = {}
    for name, weight, median_factor, volatility in definitions:
        drift = math.log(median_factor) / horizon
        scenarios[name] = {
            "weight": weight,
            "median_terminal_factor": median_factor,
            "annualized_log_drift": drift,
            "annualized_volatility": volatility,
            "continuous_hit_probability": hit_probability(drift, volatility),
        }

    def mixture(weights):
        assert abs(sum(weights) - 1) < 1e-12
        return sum(weight * scenarios[name]["continuous_hit_probability"]
                   for weight, name in zip(weights, scenarios))

    return {
        "schema": "primary_DOGE_log_barrier_sensitivity.v1",
        "review_index": 482,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "data": str(DATA.relative_to(ROOT)),
        "data_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "generator": str(Path(__file__).relative_to(ROOT)),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_asof": source["source_asof"],
        "spot": source["spot_USDT_per_DOGE"],
        "barrier": 0.48,
        "horizon_days": source["days_to_final_candle_close"],
        "scenarios": scenarios,
        "central_mixture": mixture([0.80, 0.15, 0.05]),
        "weak_rally_mixture": mixture([0.90, 0.09, 0.01]),
        "strong_rally_mixture": mixture([0.55, 0.30, 0.15]),
        "method": "Reflection-principle maximum for drifted Brownian log-price, mixed across subjective regimes; not terminal-only digital probability.",
        "limits": "Unfitted regime weights/conditional drift/volatility. Diffusion misses jumps, leverage feedback and exchange-specific wicks; actual contract uses finalized Binance 1m High. Historical overlapping windows are not independent probability samples. No measured short-horizon bond-tail licence.",
    }


if __name__ == "__main__":
    result = project()
    if OUTPUT.exists():
        saved = json.loads(OUTPUT.read_text())
        assert saved["scenarios"] == result["scenarios"]
        assert saved["central_mixture"] == result["central_mixture"]
        print(json.dumps({"verified_existing": str(OUTPUT.relative_to(ROOT))}))
    else:
        OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({key: result[key] for key in ["central_mixture", "weak_rally_mixture", "strong_rally_mixture"]}))
