from pathlib import Path
import json,math,hashlib
p=Path(__file__).with_name("0523_primary_1215.json"); x=json.loads(p.read_text())
phi=lambda z:(1+math.erf(z/math.sqrt(2)))/2
pk=sum(r["weight"]*phi(-r["D_minus_K_margin_mean_pp"]/r["sd_pp"]) for r in x["election_model"])
pr=sum(r["weight_given_K_win"]*r["p_R_assignment"] for r in x["affiliation_model"])
p=pk*pr+(1-pk)*x["p_R_if_Pan_wins"]
assert abs(pk-x["p_K_win"])<1e-12 and abs(pr-x["p_R_given_K_win"])<1e-12 and abs(p-x["unrounded_p_yes"])<1e-12
print(json.dumps({"model_sha256":hashlib.sha256(Path(__file__).with_name("0523_primary_1215.json").read_bytes()).hexdigest(),"p_K_win":pk,"p_R_given_K_win":pr,"unrounded_p_yes":p,"rounded_p_yes":x["p_yes"],"basis":"Exact replay of saved primary judgment equations; parameters remain unfitted"},separators=(",",":")))
