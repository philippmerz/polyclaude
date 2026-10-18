#!/usr/bin/env python3
"""Offline Treasury-228 daily-barrier calculation from the already captured source."""
from __future__ import annotations
import datetime as dt
import gzip
import hashlib
import json
import pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3]
RAW_GZ = ROOT / "logs/deep_review_20261017/treasury228/treasury_2026_daily_par_curve.html.gz"
RECEIPT = ROOT / "logs/deep_review_20261017/treasury228/treasury_receipt.json"
OUT = ROOT / "data/deep_review_20261017/work/0228_model_calc.json"
N = 100_000
SEED = 20261018228
START = 4.89
THRESHOLD_LATENT = 4.495  # continuity-corrected proxy for official rounded <4.50
REGIMES = [
    {"name": "plateau", "weight": 0.45, "drift_pp_per_day": 0.0, "sigma_pp_per_day": 0.055},
    {"name": "inflation", "weight": 0.35, "drift_pp_per_day": 0.0035, "sigma_pp_per_day": 0.065},
    {"name": "easing", "weight": 0.20, "drift_pp_per_day": -0.005, "sigma_pp_per_day": 0.070},
]
BASE_SENSITIVITY = {"name": "zero_drift_sigma_0.075", "drift_pp_per_day": 0.0, "sigma_pp_per_day": 0.075}

class TableParser:
    """Minimal table parser for Treasury's already-saved HTML response."""
    def __init__(self):
        from html.parser import HTMLParser
        class P(HTMLParser):
            def __init__(self):
                super().__init__(); self.rows=[]; self.row=None; self.cell=None
            def handle_starttag(self, tag, attrs):
                if tag == "tr": self.row=[]
                elif tag in ("td", "th") and self.row is not None: self.cell=[]
            def handle_data(self, data):
                if self.cell is not None: self.cell.append(data.strip())
            def handle_endtag(self, tag):
                if tag in ("td", "th") and self.row is not None and self.cell is not None:
                    self.row.append(" ".join(x for x in self.cell if x)); self.cell=None
                elif tag == "tr" and self.row is not None:
                    self.rows.append(self.row); self.row=None
        self.parser=P()
    def feed(self, source):
        self.parser.feed(source)
        return self.parser.rows

def source_rows():
    raw=gzip.decompress(RAW_GZ.read_bytes())
    receipt=json.loads(RECEIPT.read_text())
    actual=hashlib.sha256(raw).hexdigest()
    if actual != receipt["raw_sha256"]:
        raise SystemExit(f"Treasury source hash mismatch: {actual} != {receipt['raw_sha256']}")
    table=TableParser(); rows=table.feed(raw.decode("utf-8", "replace"))
    header=next(r for r in rows if r and r[0] == "Date")
    ix=header.index("5 Yr")
    out=[]
    for r in rows:
        if not r or len(r) <= ix: continue
        try: day=dt.datetime.strptime(r[0], "%m/%d/%Y").date()
        except ValueError: continue
        if r[ix] not in ("N/A", ""):
            out.append((day, float(r[ix])))
    if len(out) != 199:
        raise SystemExit(f"Expected 199 source rows; found {len(out)}")
    return raw, actual, out

def change_stats(values):
    changes=np.diff(np.asarray(values, dtype=np.float64))
    return {"n_changes":int(changes.size), "mean_pp_per_day":float(changes.mean()),
            "sample_sd_pp_per_day":float(changes.std(ddof=1)),
            "min_change_pp":float(changes.min()), "max_change_pp":float(changes.max())}

def simulate(rng, days, drift, sigma):
    # Compare daily close observations only; no intraday or between-close crossing.
    inc=rng.normal(loc=drift, scale=sigma, size=(N, days))
    levels=START+np.cumsum(inc, axis=1)
    return float(np.mean(np.any(levels < THRESHOLD_LATENT, axis=1)))

def main():
    raw, raw_sha, rows=source_rows()
    dates=[x[0] for x in rows]; values=[x[1] for x in rows]
    changes=np.diff(np.asarray(values))
    diagnostics={str(n):change_stats(values[-(n+1):]) for n in (20,40,60)}
    diagnostics["all_199_rows"]=change_stats(values)
    future_days=51
    rng=np.random.default_rng(SEED)
    results=[]
    for regime in REGIMES:
        p=simulate(rng, future_days, regime["drift_pp_per_day"], regime["sigma_pp_per_day"])
        results.append({**regime,"n_paths":N,"future_publications":future_days,"event_fraction":p})
    weighted=sum(r["weight"]*r["event_fraction"] for r in results)
    sensitivity={"parameters":BASE_SENSITIVITY,"n_paths":N,"future_publications":future_days,
                 "event_fraction":simulate(rng, future_days, BASE_SENSITIVITY["drift_pp_per_day"], BASE_SENSITIVITY["sigma_pp_per_day"])}
    horizons={}
    for days in (48,53):
        rr=[{**reg,"event_fraction":simulate(rng, days, reg["drift_pp_per_day"],reg["sigma_pp_per_day"])} for reg in REGIMES]
        horizons[str(days)]={"regimes":rr,"weighted_event_fraction":sum(a["weight"]*a["event_fraction"] for a in rr)}
    obj={"case_id":228,"input":{"raw_source_gzip":"logs/deep_review_20261017/treasury228/treasury_2026_daily_par_curve.html.gz",
          "raw_source_sha256":raw_sha,"rows":len(rows),"first_observation":{"date":dates[0].isoformat(),"5yr_pct":values[0]},
          "last_observation":{"date":dates[-1].isoformat(),"5yr_pct":values[-1]},"rows_rehashed_and_reparsed":True},
         "parameters":{"n_paths_per_regime":N,"seed":SEED,"starting_level_pct":START,"strict_published_condition":"Daily Treasury 5 Yr column <4.50%",
          "latent_threshold_pct":THRESHOLD_LATENT,"threshold_note":"Approximate latent proxy for official two-decimal publication strictly below 4.50%; compare only simulated daily closes.",
          "future_publications":future_days,"future_window":"Oct 19-Dec 31 2026","calendar_note":"51 assumed publication days excluding Nov 11, Nov 26, and Dec 25; schedule assumption, not guarantee.",
          "regime_weights_note":"Weights are explicitly supplied scenario assumptions, not estimated probabilities.","method":"For each regime, draw 100,000 paths of iid Gaussian daily changes with the regime drift/sigma; accumulate from 4.89 and test only the 51 end-of-day levels."},
         "daily_change_diagnostics":diagnostics,"regime_simulations":results,"weighted_scenario_average":weighted,
         "base_sensitivity":sensitivity,"publication_count_sensitivities":horizons,
         "limitations":["This is a computational scenario output only, not an adopted probability or forecast.","Independent Gaussian daily increments and regime weights are assumptions; volatility/drift may change.","The event tests published daily observations only, with no intraday first-passage.","Actual Treasury publication dates may differ from the 51-day calendar assumption."]}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(obj,separators=(",",":"))+"\n")
    print(json.dumps({"output":str(OUT),"bytes":OUT.stat().st_size,"output_sha256":hashlib.sha256(OUT.read_bytes()).hexdigest(),
                      "source_sha256":raw_sha,"rows":len(rows),"diagnostics":diagnostics,"regimes":results,"weighted":weighted,
                      "base_sensitivity":sensitivity,"horizons":horizons},indent=2))
if __name__ == "__main__": main()
