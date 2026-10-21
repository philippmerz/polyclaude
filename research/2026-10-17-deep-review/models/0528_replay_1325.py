from pathlib import Path
import json,math,hashlib
p=Path(__file__).with_name("0528_primary_1325.json");x=json.loads(p.read_text());phi=lambda z:(1+math.erf(z/math.sqrt(2)))/2
assert abs(sum(r["weight"] for r in x["regimes"])-1)<1e-12
v=sum(r["weight"]*phi(r["D_minus_R_margin_mean_pp"]/r["sd_pp"]) for r in x["regimes"])*(1-x["other_exception_probability"])
assert abs(v-x["unrounded_p_yes"])<1e-12
print(json.dumps({"unrounded_p_yes":v,"rounded_p_yes":x["p_yes"],"model_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"calibration":"Unfitted primary judgment, not a calibrated poll-error distribution"},separators=(",",":")))
