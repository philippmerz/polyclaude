from pathlib import Path
import json,hashlib
p=Path(__file__).with_name("0526_primary_1238.json");x=json.loads(p.read_text())
assert abs(sum(b["weight"] for b in x["branches"])-1)<1e-12
v=sum(b["weight"]*b["p_meta_first_at_final_check"] for b in x["branches"])
assert abs(v-x["unrounded_p_yes"])<1e-12
print(json.dumps({"unrounded_p_yes":v,"rounded_p_yes":x["p_yes"],"model_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"limitation":"Unfitted judgment scenarios, not innovation-frequency calibration"},separators=(",",":")))
