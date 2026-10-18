from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
from senate_primary_model import simulate
r=Path(__file__).resolve().parent
p=r/'senate_michigan_revision_0029_inputs.json';out=r/'senate_michigan_revision_0029_results.json'
assert not out.exists(),'Immutable datedresults alreadyexist'
a=json.loads(p.read_text())
options={'central':{},'no_mean_poll_bias':{'poll_bias':0.},'adverse_mean_poll_bias':{'poll_bias':-3.},'generic_D6':{'generic':6.},'generic_D10':{'generic':10.},'stronger_structural_prior':{'prior_sd':5.},'weaker_structural_prior':{'prior_sd':10.},'wider_common_error':{'national_sd':5.},'stacked_adverse_D':{'generic':6.,'poll_bias':-3.,'personal_retention':0.,'all_independent_d':0.,'protem_d':0.,'protem_other':0.},'stacked_favorable_D':{'generic':10.,'poll_bias':0.,'personal_retention':1.,'all_independent_d':1.,'protem_d':1.,'protem_other':0.}}
b={'authored_by':'primary_operator','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'Uncalibrated original-source Michigan addition; independent of new execution quote','source_files_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [p,Path(__file__),r/'senate_primary_model.py']},'previous_results_preserved':'senate_iowa_revision_0012_results.json','scenarios':{k:simulate(a,**v) for k,v in options.items()}}
out.write_text(json.dumps(b,indent=2)+'\n')
for k,v in b['scenarios'].items():
 ia=next(s for s in v['seat_outputs'] if s['seat']=='MI');print(k,'MI',ia,'controlD',v['D_senate_control'],'R',v['R_senate_control'],'Other',v['other_senate_control'],'DD',v['joint']['D_senate_D_house'])
