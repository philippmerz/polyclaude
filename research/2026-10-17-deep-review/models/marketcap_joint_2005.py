"""Offline full-rank marginals and coherent third-place forks for case 260."""
from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = ROOT / "research/2026-10-17-deep-review/models"
DATA_DIR = ROOT / "data/deep_review_20261017/work"
INPUT = MODEL_DIR / "marketcap_inputs.json"
OLD_RESULTS = MODEL_DIR / "marketcap196_results.json"
RULES = ROOT / "research/2026-10-17-primary-market-review-rules.jsonl.gz"
DIAGNOSTIC = DATA_DIR / "0260_joint_diagnostic.json"
RANKS = DATA_DIR / "0260_joint_rank_marginals.json"
N = 100_000
SEED = 19620261018
METHODS = (
    "gaussian", "vector_bootstrap", "earnings_independent",
    "earnings_correlated", "wide_earnings", "student_t5",
    "MSFT_relative_minus5pct", "MSFT_relative_plus5pct",
)
COMPANIES = ("NVDA", "AAPL", "MSFT", "Alphabet")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def frozen_identities() -> dict:
    wanted = {260, 268}
    found = {}
    with gzip.open(RULES, "rt", encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            index = int(row["review_index"])
            if index in wanted:
                found[index] = {
                    "market_id": str(row["id"]),
                    "condition_id": str(row["conditionId"]),
                    "criteria_sha256": row["criteria_sha256"],
                    "description_sha256": sha(str(row["description"]).encode()),
                }
    if set(found) != wanted:
        raise RuntimeError(f"frozen identity coverage mismatch: {sorted(found)}")
    return {str(k): found[k] for k in sorted(found)}


def paths() -> tuple[dict, dict]:
    inputs = json.loads(INPUT.read_text())
    source = ROOT / "data/deep_review_20261017/market_cap_history_sources.json"
    if sha(source.read_bytes()) != inputs["source_packet_sha256"]:
        raise RuntimeError("market-cap source packet hash mismatch")
    price = np.asarray(inputs["price_rows"], dtype=float)
    shares = inputs["fixed_shares_billions"]
    caps = np.column_stack((
        price[:, 0] * shares["NVDA"],
        price[:, 1] * shares["AAPL"],
        price[:, 2] * shares["MSFT"],
        price[:, 3] * shares["Alphabet_A_B"] + price[:, 4] * shares["Alphabet_C"],
    )) / 1000
    if not np.allclose(caps[-1], inputs["latest_caps_trillion"]):
        raise RuntimeError("input latest-cap check failed")
    returns = np.diff(np.log(caps), axis=0)
    rng = np.random.default_rng(SEED)
    result = {}
    rank_result = {}
    for window in (20, 89):
        r = returns[-window:]
        centered = r - r.mean(axis=0)
        chol = np.linalg.cholesky(np.cov(r.T))
        result[window] = {}
        rank_result[window] = {}
        for method in METHODS:
            if method == "vector_bootstrap":
                change = sum(centered[rng.integers(0, len(centered), N)] for _ in range(10))
            else:
                change = rng.standard_normal((N, 4)) @ chol.T * np.sqrt(10)
                if method == "student_t5":
                    change *= np.sqrt(3 / rng.chisquare(5, N))[:, None]
                if method.startswith("earnings") or method.startswith("MSFT_relative") or method == "wide_earnings":
                    sigma = np.array([.03, 0, .08, .08])
                    if method == "wide_earnings":
                        sigma *= 1.875
                    z = rng.standard_normal((N, 4))
                    if method == "earnings_correlated":
                        z[:, 3] = .5 * z[:, 2] + np.sqrt(.75) * z[:, 3]
                    change += z * sigma
                if method == "MSFT_relative_minus5pct":
                    change[:, 2] -= .05
                elif method == "MSFT_relative_plus5pct":
                    change[:, 2] += .05
            order = np.argsort(-(np.log(caps[-1]) + change), axis=1)
            marginals = {}
            for company_index, company in enumerate(COMPANIES):
                rank = np.argmax(order == company_index, axis=1)
                marginals[company] = [float(np.mean(rank == j)) for j in range(4)]
            rank_result[window][method] = marginals
            result[window][method] = {company: marginals[company][2] for company in COMPANIES}
    return {"inputs": inputs, "caps": caps, "thirds": result, "ranks": rank_result}


def run() -> None:
    if DIAGNOSTIC.exists() or RANKS.exists():
        raise FileExistsError("refusing to overwrite joint diagnostic outputs")
    computed = paths()
    old = json.loads(OLD_RESULTS.read_text())
    # The MSFT exact-third cells must reproduce all old methods/windows exactly.
    for row in old["results"]:
        window = int(row["returns"])
        for method in METHODS:
            actual = computed["thirds"][window][method]["MSFT"]
            expected = row["scenarios"][method]["p_exact_third"]
            if actual != expected:
                raise AssertionError(f"MSFT reproduction mismatch {window}/{method}: {actual} != {expected}")

    # Equal-weight the two independently simulated earnings-independent windows.
    avg_third = {
        company: sum(computed["thirds"][w]["earnings_independent"][company] for w in (20, 89)) / 2
        for company in COMPANIES
    }
    four_firm = [avg_third[c] for c in COMPANIES] + [0.0]
    uniform = [.2] * 5
    consensus = [.1, .1, .5, .25, .05]
    joint = [
        .95 * (.98 * four_firm[i] + .02 * uniform[i]) + .05 * consensus[i]
        for i in range(5)
    ]
    if not np.isclose(sum(joint), 1.0, atol=1e-12):
        raise AssertionError("joint five-outcome fork does not sum to one")

    identities = frozen_identities()
    inputs_sha = sha(INPUT.read_bytes())
    diagnostic = {
        "schema": "polyclaude.marketcap_joint_diagnostic.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "review_indices_validated": [260, 268], "frozen_identities": identities,
        "inputs_path": str(INPUT.relative_to(ROOT)), "inputs_sha256": inputs_sha,
        "old_marketcap196_results_sha256": sha(OLD_RESULTS.read_bytes()),
        "seed": SEED, "samples_per_cell": N, "windows_sessions": [20, 89],
        "rank_order": list(COMPANIES), "all_cell_thirds": computed["thirds"],
        "equal_window_earnings_independent_third_by_company": avg_third,
        "third_place_fork": {
            "outcome_order": list(COMPANIES) + ["Other"],
            "four_firm_input_plus_other_zero": four_firm,
            "outside_company_branch": {"weight": .02, "distribution": uniform},
            "consensus_branch": {"weight": .05, "distribution": consensus},
            "formula": ".95*(.98*four_firm_plus_Other0 + .02*uniform5) + .05*consensus5",
            "result": joint,
            "sum": sum(joint),
            "note": "Prespecified coherence diagnostic only; no adopted probability.",
        },
        "msft_old_cell_assertions": "all 16 window/method exact-third values matched marketcap196_results.json exactly",
        "rank_arrays_path": str(RANKS.relative_to(ROOT)),
    }
    rank_output = {
        "schema": "polyclaude.marketcap_joint_rank_marginals.v1",
        "created_utc": diagnostic["created_utc"], "inputs_sha256": inputs_sha,
        "seed": SEED, "samples_per_cell": N,
        "rank_1_to_4_marginals": computed["ranks"],
        "equal_window_earnings_independent_marginals": {
            company: [sum(computed["ranks"][w]["earnings_independent"][company][j] for w in (20, 89)) / 2 for j in range(4)]
            for company in COMPANIES
        },
    }
    DIAGNOSTIC.write_text(json.dumps(diagnostic, indent=2) + "\n")
    RANKS.write_text(json.dumps(rank_output, indent=2) + "\n")
    print(json.dumps({"diagnostic": str(DIAGNOSTIC.relative_to(ROOT)),
                      "diagnostic_bytes": DIAGNOSTIC.stat().st_size,
                      "rank_arrays": str(RANKS.relative_to(ROOT)),
                      "rank_arrays_bytes": RANKS.stat().st_size,
                      "inputs_sha256": inputs_sha,
                      "msft_cells_match": True,
                      "joint_sum": sum(joint)}))


if __name__ == "__main__":
    run()
