"""Offline, reproducible joint daily Treasury barrier sensitivity; no orders."""
import csv
import gzip
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CSV_RECEIPT = ROOT / "logs/deep_review_20261017/case475_treasury_csv_1455/treasury_csv_2026.receipt.json"
PARAMS = ROOT / "research/2026-10-17-deep-review/models/0475_firstpass_sensitivity_1503.json"
OUTPUT = ROOT / "research/2026-10-17-deep-review/models/0481_joint_projection_1634.json"


def project():
    receipt = json.loads(CSV_RECEIPT.read_text())
    compressed = (CSV_RECEIPT.parent / receipt["body_path"]).read_bytes()
    raw = gzip.decompress(compressed)
    assert hashlib.sha256(compressed).hexdigest() == receipt["gzip_sha256"]
    assert hashlib.sha256(raw).hexdigest() == receipt["raw_sha256"]
    rows = []
    for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
        rows.append((datetime.strptime(row["Date"], "%m/%d/%Y").date(), float(row["2 Yr"])))
    rows.sort()
    assert str(rows[-1][0]) == "2026-10-19" and rows[-1][1] == 4.77
    changes = np.diff([value for _, value in rows])[-60:] * 100
    previous = json.loads(PARAMS.read_text())
    rng = np.random.default_rng(47520261020)
    count = 80000
    results = {}
    for key, settings in previous["scenarios"].items():
        mode = settings["mode"]
        if mode == "Gaussian":
            increments = rng.normal(settings["daily_drift_bp"], settings["daily_volatility_bp"], (count, 9))
        else:
            increments = rng.choice(changes, (count, 9))
            if mode == "centered_bootstrap":
                increments -= changes.mean()
        increments[:, 6] += settings["event_day7_jump_bp"]
        paths = 477 + np.cumsum(increments, axis=1)
        lower = (paths < 454.5).any(axis=1)
        upper = (paths >= 494.5).any(axis=1)
        cells = {
            "both": float((lower & upper).mean()),
            "lower_only": float((lower & ~upper).mean()),
            "upper_only": float((~lower & upper).mean()),
            "neither": float((~lower & ~upper).mean()),
        }
        assert abs(sum(cells.values()) - 1) < 1e-12
        results[key] = {
            **cells,
            "p_lower": float(lower.mean()),
            "p_upper": float(upper.mean()),
            "upper_mc_standard_error": float(np.sqrt(upper.mean() * (1 - upper.mean()) / count)),
        }
    weights = previous["provisional_weights_before_CPI_bridge"]
    mixture = {key: sum(weight * results[name][key] for name, weight in weights.items())
               for key in ["both", "lower_only", "upper_only", "neither", "p_lower", "p_upper"]}
    assert abs(sum(mixture[k] for k in ["both", "lower_only", "upper_only", "neither"]) - 1) < 1e-12
    return {
        "schema": "primary_joint_daily_barrier_projection.v1",
        "review_index": 481,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "seed": 47520261020,
        "generator": str(Path(__file__).relative_to(ROOT)),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "csv_receipt": str(CSV_RECEIPT.relative_to(ROOT)),
        "csv_raw_sha256": receipt["raw_sha256"],
        "source_observed_through": "2026-10-19",
        "prior_parameters": str(PARAMS.relative_to(ROOT)),
        "prior_parameters_sha256": hashlib.sha256(PARAMS.read_bytes()).hexdigest(),
        "paths_per_scenario": count,
        "daily_observations": 9,
        "start_yield_pct": 4.77,
        "barriers": "Published lower<4.55 (latent<4.545), upper>=4.95 (latent>=4.945); daily observations, not intraday.",
        "scenarios": results,
        "weights": weights,
        "mixture": mixture,
        "replay_limit": "Same saved475 parameters/seed, newly specified RNG order. Original generator/draw sequence was not saved; this is not an exact replay of475 simulations. Original18% forecast remains unchanged.",
        "model_limits": "Subjective regime weights/jumps, non-IID historical changes and volatility clustering. MC error is computation only, not probability calibration. Both barriers can hit on one path; not exclusive complements.",
    }


if __name__ == "__main__":
    result = project()
    if OUTPUT.exists():
        saved = json.loads(OUTPUT.read_text())
        assert saved["mixture"] == result["mixture"]
        assert saved["scenarios"] == result["scenarios"]
        print(json.dumps({"verified_existing": str(OUTPUT.relative_to(ROOT)), "mixture": saved["mixture"]}))
    else:
        OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"saved": str(OUTPUT.relative_to(ROOT)), "mixture": result["mixture"]}))
