from pathlib import Path
import json,hashlib
p=Path(__file__).with_name("0529_primary_1342.json");x=json.loads(p.read_text())
assert abs(sum(r["weight"] for r in x["branches"])-1)<1e-12
v=sum(r["weight"]*r["p_R_assignment"] for r in x["branches"])
assert abs(v-x["unrounded_p_yes"])<1e-12 and round(v,3)==x["p_yes"]
print(json.dumps({"unrounded_p_yes":v,"rounded_p_yes":x["p_yes"],"model_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"limitation":"Rare contingency weights not calibrated"},separators=(",",":")))
