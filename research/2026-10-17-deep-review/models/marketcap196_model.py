"""Exact-third joint-rank sensitivity; offline research, no execution path."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

BASE = Path("research/2026-10-17-deep-review/models")
INPUT = BASE / "marketcap_inputs.json"
SOURCE = Path("data/deep_review_20261017/market_cap_history_sources.json")


def run():
    x = json.loads(INPUT.read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == x["source_packet_sha256"]
    p = np.asarray(x["price_rows"], dtype=float)
    s = x["fixed_shares_billions"]
    caps = np.column_stack((p[:, 0] * s["NVDA"], p[:, 1] * s["AAPL"],
                            p[:, 2] * s["MSFT"],
                            p[:, 3] * s["Alphabet_A_B"] + p[:, 4] * s["Alphabet_C"])) / 1000
    assert np.allclose(caps[-1], x["latest_caps_trillion"])
    returns = np.diff(np.log(caps), axis=0)
    rng = np.random.default_rng(19620261018)
    n = 100000
    results = []
    for window in (20, 89):
        r = returns[-window:]
        centered = r - r.mean(axis=0)
        chol = np.linalg.cholesky(np.cov(r.T))
        row = {"returns": window, "company_order": x["marketcap_company_order"],
               "daily_sd": r.std(axis=0, ddof=1).tolist(), "scenarios": {}}
        for method in ("gaussian", "vector_bootstrap", "earnings_independent",
                       "earnings_correlated", "wide_earnings", "student_t5",
                       "MSFT_relative_minus5pct", "MSFT_relative_plus5pct"):
            if method == "vector_bootstrap":
                change = sum(centered[rng.integers(0, len(centered), n)] for _ in range(10))
            else:
                change = rng.standard_normal((n, 4)) @ chol.T * np.sqrt(10)
                if method == "student_t5":
                    change *= np.sqrt(3 / rng.chisquare(5, n))[:, None]
                if method.startswith("earnings") or method.startswith("MSFT_relative") or method == "wide_earnings":
                    sigma = np.array([.03, 0, .08, .08])
                    if method == "wide_earnings":
                        sigma *= 1.875
                    z = rng.standard_normal((n, 4))
                    if method == "earnings_correlated":
                        z[:, 3] = .5 * z[:, 2] + np.sqrt(.75) * z[:, 3]
                    change += z * sigma
                if method == "MSFT_relative_minus5pct":
                    change[:, 2] -= .05
                elif method == "MSFT_relative_plus5pct":
                    change[:, 2] += .05
            order = np.argsort(-(np.log(caps[-1]) + change), axis=1)
            rank = np.argmax(order == 2, axis=1)
            distribution = [float(np.mean(rank == j)) for j in range(4)]
            row["scenarios"][method] = {"MSFT_rank_1_to_4": distribution,
                                         "p_exact_third": distribution[2]}
        results.append(row)
    base = sum(row["scenarios"]["earnings_independent"]["p_exact_third"] for row in results) / 2
    # Explicit subjective allowance, not fitted frequencies or guaranteed bounds.
    # Outside four-firm universe: 2% weight, conditional exact-third .25.
    # Unspecified consensus/calendar/share-count convention: 5%, conditional .5.
    judgment = .95 * (.98 * base + .02 * .25) + .05 * .5
    result = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "review_index": 196,
        "before_reading_own_PM_quote": True, "seed": 19620261018, "samples_per_cell": n,
        "input_path": str(INPUT), "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "history_dates": [x["dates"][0], x["dates"][-1]], "latest_caps_trillion": caps[-1].tolist(),
        "full_joint_rank_not_pairwise_product": True, "future_sessions": 10,
        "main_assumptions": "Zero log drift, fixed dated issuer shares, last regular Oct30 close for Saturday Oct31; equal subjective recent20/long89 window weights; 8% MSFT and Alphabet independent earnings log-SD and 3% NVDA event SD, Apple0 before Nov2 call.",
        "results": results, "main_4company_probability": base,
        "subjective_outside_company_branch": {"weight": .02, "conditional_p": .25},
        "subjective_consensus_calendar_branch": {"weight": .05, "conditional_p": .5},
        "primary_raw_p_yes": judgment, "primary_p_yes": round(judgment, 2),
        "calibrated_posterior_or_lower_bound": False,
        "limitations": ["Historical covariance may change; no option-implied event distribution or directional alpha.",
                       "Window weights, earnings shocks, outsider and adjudication branches are primary assumptions.",
                       "Exact-third can lose on both overperformance to rank1/2 and underperformance to rank4+.",
                       "Actual October share counts, worldwide inclusion and Saturday convention are not specified by the two-sentence rule."]}
    dest = BASE / "marketcap196_results.json"
    assert not dest.exists(), "preserve the initial model; write an explicit new version for changes"
    dest.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"p_yes": result["primary_p_yes"], "raw": judgment,
                      "cells": [{"returns": v["returns"], "third": {k: y["p_exact_third"]
                                 for k, y in v["scenarios"].items()}} for v in results]}))


if __name__ == "__main__":
    run()
