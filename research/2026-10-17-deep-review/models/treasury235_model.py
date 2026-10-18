#!/usr/bin/env python3
"""Offline case-235 daily-barrier scenario calculation; no network or market data fetch."""
from __future__ import annotations
import datetime as dt
import gzip, hashlib, json, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3]
SOURCE_GZ = ROOT / "logs/deep_review_20261017/treasury228/treasury_2026_daily_par_curve.html.gz"
RECEIPT = ROOT / "logs/deep_review_20261017/treasury228/treasury_receipt.json"
OUT = ROOT / "data/deep_review_20261017/work/0235_model_calc.json"
N = 100_000
SEED = 20261018235
START = 5.43
LATENT_THRESHOLD = 4.895  # continuity-corrected proxy for strict published <4.90%
REGIMES = [
    {"name": "plateau", "weight": 0.45, "drift_pp_per_day": 0.0, "sigma_pp_per_day": 0.050},
    {"name": "inflation", "weight": 0.35, "drift_pp_per_day": 0.0035, "sigma_pp_per_day": 0.060},
    {"name": "easing", "weight": 0.20, "drift_pp_per_day": -0.005, "sigma_pp_per_day": 0.065},
]
BASE_SENSITIVITY = {"name": "zero_drift_sigma_0.075", "drift_pp_per_day": 0.0, "sigma_pp_per_day": 0.075}

class TreasuryTable:
    def __init__(self):
        from html.parser import HTMLParser
        class Parser(HTMLParser):
            def __init__(self): super().__init__(); self.rows=[]; self.row=None; self.cell=None
            def handle_starttag(self,tag,attrs):
                if tag == "tr": self.row=[]
                elif tag in ("td","th") and self.row is not None: self.cell=[]
            def handle_data(self,data):
                if self.cell is not None: self.cell.append(data.strip())
            def handle_endtag(self,tag):
                if tag in ("td","th") and self.row is not None and self.cell is not None:
                    self.row.append(" ".join(x for x in self.cell if x)); self.cell=None
                elif tag == "tr" and self.row is not None:
                    self.rows.append(self.row); self.row=None
        self.parser=Parser()
    def parse(self,html):
        self.parser.feed(html)
        return self.parser.rows

def get_30yr_rows():
    raw=gzip.decompress(SOURCE_GZ.read_bytes())
    receipt=json.loads(RECEIPT.read_text())
    sha=hashlib.sha256(raw).hexdigest()
    if sha != receipt["raw_sha256"]: raise SystemExit("Treasury raw-source hash mismatch")
    rows=TreasuryTable().parse(raw.decode("utf-8","replace"))
    header=next(r for r in rows if r and r[0]=="Date")
    col=header.index("30 Yr")
    out=[]
    for row in rows:
        if not row or len(row)<=col: continue
        try: day=dt.datetime.strptime(row[0],"%m/%d/%Y").date()
        except ValueError: continue
        if row[col] not in ("", "N/A"): out.append((day,float(row[col])))
    if len(out)!=199: raise SystemExit(f"expected 199 Treasury rows; got {len(out)}")
    return sha,out

def simulate(rng, days, drift, sigma):
    # Sample iid daily changes, accumulate daily closes, and test closes only.
    innovations=rng.normal(loc=drift,scale=sigma,size=(N,days))
    daily_closes=START+np.cumsum(innovations,axis=1)
    return float(np.mean(np.any(daily_closes<LATENT_THRESHOLD,axis=1)))

def run_horizon(rng, days):
    out=[]
    for regime in REGIMES:
        out.append({**regime,"n_paths":N,"future_publications":days,
                    "event_fraction":simulate(rng,days,regime["drift_pp_per_day"],regime["sigma_pp_per_day"])})
    return {"regimes":out,"weighted_scenario_average":sum(x["weight"]*x["event_fraction"] for x in out)}

def main():
    sha,rows=get_30yr_rows()
    dates=[x[0] for x in rows]; values=[x[1] for x in rows]
    window=[(d,v) for d,v in rows if dt.date(2026,9,2)<=d<=dt.date(2026,10,16)]
    if len(window)!=31 or window[-1][1]!=5.43: raise SystemExit("case-235 frozen window check failed")
    days=51 # Oct19-Dec31 weekdays assumed, excluding Nov11, Nov26, Dec25
    rng=np.random.default_rng(SEED)
    primary=run_horizon(rng,days)
    sensitivity={"parameters":BASE_SENSITIVITY,"n_paths":N,"future_publications":days,
                 "event_fraction":simulate(rng,days,BASE_SENSITIVITY["drift_pp_per_day"],BASE_SENSITIVITY["sigma_pp_per_day"])}
    horizons={str(h):run_horizon(rng,h) for h in (48,53)}
    result={"case_id":235,"input":{"source_gzip":"logs/deep_review_20261017/treasury228/treasury_2026_daily_par_curve.html.gz",
              "source_raw_sha256":sha,"column":"30 Yr","source_rows":len(rows),
              "window_observations_sep2_oct16":len(window),"latest_observation":{"date":dates[-1].isoformat(),"30yr_pct":values[-1]}},
        "parameters":{"n_paths_per_regime":N,"seed":SEED,"starting_level_pct":START,"published_event":"official Treasury Daily Treasury Par Yield Curve Rates, 30 Yr column strictly <4.90%",
              "latent_threshold_pct":LATENT_THRESHOLD,"threshold_note":"Approximate latent proxy for two-decimal published strict <4.90%; daily-close comparisons only.",
              "future_publication_days":days,"future_window":"Oct19-Dec31 2026","calendar_assumption":"51 weekdays excluding Nov11, Nov26, Dec25; actual release schedule may vary.",
              "regime_weights_note":"Scenario weights are explicit assumptions, not estimated probabilities.",
              "method":"100,000 iid Gaussian daily changes per branch with specified branch drift/sigma; accumulate from 5.43 and test only daily closes."},
        "primary_scenario_computations":primary,"zero_drift_sigma075_sensitivity":sensitivity,
        "publication_count_sensitivities":horizons,
        "limitations":["Computational scenario outputs only; no adopted probability, forecast, range, or decision.","Gaussian daily changes, drift, regime weights, and publication-day calendar are assumptions.","No intraday or between-close first-passage is modeled."]}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,separators=(",",":"))+"\n")
    print(json.dumps({"output":str(OUT),"bytes":OUT.stat().st_size,"output_sha256":hashlib.sha256(OUT.read_bytes()).hexdigest(),
                      "source_sha256":sha,"rows":len(rows),"window_rows":len(window),"primary":primary,"sensitivity":sensitivity,"horizons":horizons},indent=2))
if __name__=="__main__":main()
