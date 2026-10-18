#!/usr/bin/env python3
"""Prespecified plateau-mode sensitivity for shared OpenRouter 250/112 paths."""
from __future__ import annotations
import gzip, hashlib, json, math, random
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data/deep_review_20261017"
N, SEED = 200_000, 20261018182
BRANCHES = [
    ("moderation", .36, .035, .065),
    ("historical_growth", .28, .08, .095),
    ("release_boom", .08, .20, .10),
    ("disruption", .08, -.15, .15),
    ("plateau", .20, 0.0, .05),
]

def get_latest_partial():
    summary = json.loads((DATA / "work/0250_source_update_1800.json").read_text())
    rec = summary["latest_snapshot"]
    raw = gzip.decompress((ROOT / rec["raw_gzip_path"]).read_bytes())
    sha = hashlib.sha256(raw).hexdigest()
    if sha != rec["raw_sha256"]:
        raise ValueError("latest source hash mismatch")
    pts = json.loads(raw)["data"]["data"]
    if len(pts) != 53 or pts[-1]["x"] != "2026-10-12":
        raise ValueError("unexpected latest Top Models series")
    partial = sum(pts[-1]["ys"].values()) / 1e12
    if abs(partial - 158.105052314724) > 1e-12:
        raise ValueError("unexpected latest partial point")
    elapsed = .8695 + .1305 * (16 / 24)
    remaining = partial * (1 / elapsed - 1)
    return partial, remaining, sha

def simulate(partial, remaining):
    rng = random.Random(SEED)
    known = 165.856049857563 + 171.842501724714
    saturday = 18.33824279449
    counts = {"250_yes": 0, "112_yes": 0, "neither": 0}
    branches = {r[0]: {"n": 0, "sum_total_T": 0.0, "250_yes": 0, "112_yes": 0, "neither": 0} for r in BRANCHES}
    for _ in range(N):
        z = rng.random()
        if z < .25:
            s = saturday * math.exp(.25 * rng.gauss(0, 1))
        elif z < .90:
            s = remaining * math.exp(.35 * rng.gauss(0, 1))
        else:
            s = rng.uniform(0, 36)
        week0 = partial + s
        q = rng.random()
        cumul = 0.0
        for branch in BRANCHES:
            cumul += branch[1]
            if q <= cumul:
                break
        name, _, mu, sd = branch
        common = rng.gauss(0, 1)
        value = week0
        future = []
        for _week in range(5):
            g = mu + sd * (.5 * common + math.sqrt(.75) * rng.gauss(0, 1))
            value *= math.exp(g)
            future.append(value)
        noise = rng.gauss(0, 2) if rng.random() < .95 else rng.gauss(0, 10)
        total = sum(future[1:]) + noise
        y250 = 625 <= total < 675
        y112 = 725 <= total < 775
        state = "250_yes" if y250 else "112_yes" if y112 else "neither"
        counts[state] += 1
        b = branches[name]
        b["n"] += 1
        b["sum_total_T"] += total
        b[state] += 1
    branch_out = {}
    for name, b in branches.items():
        branch_out[name] = {
            "n": b["n"],
            "mean_four_week_total_T": b["sum_total_T"] / b["n"],
            "case250_yes_count": b["250_yes"],
            "case250_yes_fraction_within_branch": b["250_yes"] / b["n"],
            "case112_yes_count": b["112_yes"],
            "case112_yes_fraction_within_branch": b["112_yes"] / b["n"],
            "neither_count": b["neither"],
            "neither_fraction_within_branch": b["neither"] / b["n"],
        }
    return {
        "n": N, "seed": SEED,
        "aggregate_mean_four_week_total_T": sum(b["sum_total_T"] for b in branches.values()) / N,
        "branch_results": branch_out,
        "three_state_joint_counts": counts,
        "three_state_joint_fractions": {k: v / N for k, v in counts.items()},
    }

def main():
    partial, remaining, sha = get_latest_partial()
    result = {
        "schema": "openrouter_plateau_mode_sensitivity.v1",
        "review_index": 250,
        "scope": "Prespecified computational sensitivity only; no adopted probability, trade, or portfolio action.",
        "source_paths": ["work/0250_resume.json", "work/0250_source_update_1800.json", "openrouter_chart_display_semantics_1100.json", "research/2026-10-17-primary-market-review-rules.jsonl.gz"],
        "code_path": "research/2026-10-17-deep-review/models/openrouter250_plateau_sensitivity_1925.py",
        "source": {"latest_chart_sha256": sha, "partial_week_2026_10_12_raw_sum_T": partial, "cachedAt_utc_hour": 16, "ui_remaining_proxy_T": remaining, "cutoff_note": "cache anchor, not verified usage cutoff"},
        "parameters": {"draws": N, "seed": SEED, "branch_weights_and_weekly_log_mu_sigma": BRANCHES, "same_cutoff_weights": {"prior_complete_day_18T_remaining": .25, "latest_UI_remaining_proxy": .65, "uniform_0_to_36T": .10}, "same_innovation_correlation": .25, "same_rounding_revision_noise": "95% Normal(0,2T), 5% Normal(0,10T), additive to four-week total", "bands_T": {"250": "[625,675)", "112": "[725,775)"}},
        "results": simulate(partial, remaining),
    }
    out = DATA / "work/0250_plateau_sensitivity_1925.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(out.relative_to(ROOT)), "bytes": out.stat().st_size, **result["results"]}, indent=2))

if __name__ == "__main__":
    main()
