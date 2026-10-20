"""Deterministic case486 subjective scenarios; no fit or execution."""
from pathlib import Path
from math import isclose
import json

def projection(m):
    r=m["conditional_future_regimes"]
    assert isclose(sum(x["mass"] for x in r),1)
    future=sum(x["mass"]*x["p_any_leader_encounter_by_cutoff"] for x in r)
    none=(1-m["prior_already_qualifying_encounter_probability"])*(1-future)
    assert isclose(future,m["raw_future_meeting_probability"]) and isclose(none,m["raw_no_meeting_probability"])
    return {"future_meeting":future,"raw_no_meeting":none,"rounded_yes":m["p_yes"],"sensitivity_breakthrough30":.97*(1-(.4*.08+.3*.35+.3*.75))}

if __name__=="__main__":
    print(json.dumps(projection(json.loads(Path(__file__).with_name("0486_no_meeting_primary_1730.json").read_text())),indent=2))
