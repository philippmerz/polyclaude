"""Replay case488 subjective revenue-error CDF; no data fit/network/execution."""
import json,math
from pathlib import Path

def probability(a,core_mean=None):
    assert math.isclose(sum(x["weight"] for x in a["mixture_error_B"]),1)
    total=0
    for i,r in enumerate(a["mixture_error_B"]):
        mu=core_mean if i==0 and core_mean is not None else r["mean_error_B"]
        z=mu/r["sd_error_B"]
        total+=r["weight"]*(1+math.erf(z/math.sqrt(2)))/2
    return total*a["official_metric_timely_probability"]

if __name__=="__main__":
    a=json.loads(Path(__file__).with_name("0488_kla_primary_1740.json").read_text())
    print(json.dumps({"raw_yes":probability(a),"rounded_yes":a["p_yes"],"zero_core_bias_yes":probability(a,0),"100M_core_bias_yes":probability(a,.10),"qoq_required_pct":(4/3.657556-1)*100},indent=2))
