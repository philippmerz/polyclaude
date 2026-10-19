"""Case376 current-cap rank sensitivity; offline, no quote/account access."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MD = ROOT / "research/2026-10-17-deep-review/models"
WORK = ROOT / "data/deep_review_20261017/work"
INPUT = MD / "marketcap_inputs.json"
EVENTS = WORK / "0260_earnings_event_history.json"
CAPS = WORK / "0364_primary_refresh_1646.json"
OUT = WORK / "0376_rank_sensitivity_1830.json"
FIRMS = ("NVDA", "AAPL", "MSFT", "Alphabet")
N, SEED = 100_000, 37620261019


def main():
    if OUT.exists():
        raise FileExistsError("preserve prior output")
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if sha(INPUT) != "32dafab53f6f77deb6ef862d670824e3f9fe7b5366393d3a27f688d32f2cfca7":
        raise ValueError("historical inputs changed")
    if sha(EVENTS) != "1b38ea38700ac4d813c596f9e63206d913abf311b2353f847fcb7a6b60ac1ead":
        raise ValueError("event history changed")
    x = json.loads(INPUT.read_text())
    p, s = np.array(x["price_rows"]), x["fixed_shares_billions"]
    old = np.column_stack((p[:, 0]*s["NVDA"], p[:, 1]*s["AAPL"],
          p[:, 2]*s["MSFT"], p[:, 3]*s["Alphabet_A_B"]+p[:, 4]*s["Alphabet_C"])) / 1000
    returns = np.diff(np.log(old), axis=0)
    dates = np.array(x["dates"][1:])
    # Current vendor observation, not synchronized official exchange closes.
    caps = np.array([5.267, 4.991, 3.962, 4.169])
    if not all(f"{v:.3f}" in CAPS.read_text() for v in caps):
        raise ValueError("current-cap source mismatch")
    rng, result = np.random.default_rng(SEED), {}
    for window in (20, 89):
        bg = returns[-window:]
        if window == 89:
            bg = bg[~np.isin(dates[-window:], ["07/23/2026", "07/30/2026"])]
        chol = np.linalg.cholesky(np.cov(bg.T))
        z, event = rng.standard_normal((N, 4)), rng.standard_normal((N, 4))
        cells = {}
        for name, days, sig, shift in [
            ("base", 52, .08, 0), ("51sessions", 51, .08, 0),
            ("no_extra_event", 52, 0, 0), ("wide_event", 52, .15, 0),
            ("NVDA_relative_minus5", 52, .08, -.05),
            ("NVDA_relative_plus5", 52, .08, .05),
        ]:
            changes = z @ chol.T * np.sqrt(days) + event*sig
            changes[:, 0] += shift
            winners = np.argmax(np.log(caps)+changes, axis=1)
            base = np.bincount(winners, minlength=4) / N
            # Allocate mutually exclusive outsider winners explicitly. Tesla's
            # prior3% is NOT added on top of a normalized four-firm total.
            alt = np.array([.40, .40, .06, .08, .03, .03])
            normal = np.r_[.96*base, .03, .01]
            joint = .95*normal + .05*alt
            if not np.isclose(joint.sum(), 1, atol=1e-12):
                raise ValueError("winner mass mismatch")
            cells[name] = dict(zip((*FIRMS, "Tesla", "Other"), map(float, joint)))
        result[str(window)] = {"used_background_rows": len(bg), "cells": cells}
    equal = {name: {f: sum(result[str(w)]["cells"][name][f] for w in (20, 89))/2
                    for f in (*FIRMS, "Tesla", "Other")}
             for name in result["20"]["cells"]}
    output = {
        "schema": "current_marketcap376_rank_sensitivity.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "On-chain PM Dec31 rank contract, not stock-investment research; sensitivity, not adoption.",
        "seed": SEED, "samples_per_cell": N,
        "source_hashes": {str(p.relative_to(ROOT)): sha(p) for p in (INPUT, EVENTS, CAPS)},
        "current_caps_trillion": dict(zip(FIRMS, caps)),
        "model": "Zero log drift; equal20/87 event-excluded covariance windows,52session horizon/51sensitivity, independent8% terminal event shocks; covariance and shocks judgmental/nonstationary.",
        "global_winner_fork": ".95*(.96 conditional4firm winner + .03 Tesla + .01 other) + .05 alternative[.40,.40,.06,.08,.03,.03]",
        "coherence_note": "Exactly one winner; Tesla3%/Other1.1% are subjective global tails. ExistingApple280 is a differently dated forecast; these are current joint diagnostics, not independent company signals.",
        "equal_window_winner_probabilities": equal,
        "window_cells": result,
        "limits": "Intraday vendor cap convention/FX/shares unverified; no drift alpha, options, global census or calibrated tail. Residual NVDA/Apple earnings in background may double-count shocks;51/52counts approximate current intraday session. Main must read issuer facts and adopt p/range before own quote.",
        "code_sha256": sha(Path(__file__)),
    }
    OUT.write_text(json.dumps(output, indent=2)+"\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "equal_window": equal}))


if __name__ == "__main__":
    main()
