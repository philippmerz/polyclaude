"""Recompute case484 subjective tree; no network, fit, pricing or execution."""
import json
from pathlib import Path
from math import isclose

def projection(a):
    b=a["branches"]
    p=b[0]["mass"]*b[0]["conditional_yes"]+b[1]["mass"]*b[1]["p60_given_update"]*b[1]["official_timely_given60"]+b[2]["mass"]*b[2]["p60_remeasurement_or_equivalence"]*b[2]["official_timely_given60"]
    joint=a["threshold_central_joint_states"]
    assert isclose(sum(x["mass"] for x in b),1) and isclose(sum(joint.values()),1)
    assert all(x>=0 for x in joint.values()) and isclose(p,a["p_yes"])
    assert isclose(joint["60throughunder65"]+joint["65orabove"],p)
    assert isclose(1-joint["under55"],.3402125)
    return {"p_yes":p,"p_no":1-p,"joint":joint,"low_update_probability":.015+.585*.20*.75+.315*.06*.5,"high_update_probability":.015+.585*.50*.75+.315*.06*.5}

if __name__=="__main__":
    model=Path(__file__).with_name("0484_kimi60_primary_1717.json")
    print(json.dumps(projection(json.loads(model.read_text())),indent=2))
