"""Primary explicit margin sensitivity for twelve additional conditions.

Uses the already documented shared House assumptions, with additional official
historical returns. No prices, prior screen labels or external win odds enter.
Outputs are judgment scenarios, not calibrated probabilities.
"""
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('previous_house_model',Path(__file__).with_name('house_extension_model.py'))
previous=importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

HISTORY={
 'CT05':dict(D=171337+8931,R=157258,other=76+3,page=15),
 'NV01':dict(D=167885,R=143650,other=3321+2736+2711+2596,page=44),
 'NV03':dict(D=191304,R=181084,other=0,page=44),
 'MT01':dict(D=143783,R=168529,other=9954,page=42),
 'AZ01':dict(D=208966,R=225538,other=0,page=6),
 'AZ02':dict(D=184963,R=221413,other=28+22+5,page=6),
 'VA06':dict(D=141612,R=256933,other=7980+510,page=74),
 'NY01':dict(D=181647+1893,R=200802+25483,other=275,page=48),
 'MI04':dict(D=184641,R=234489,other=6687,page=36),
}
for v in HISTORY.values():
 v['valid_votes']=v['D']+v['R']+v['other']
 v['D_margin_pp']=100*(v['D']-v['R'])/v['valid_votes']

CASES={
 259:dict(district='CT05',yes='D',pvi=3,inc=2,adj=0,other=.005,history_weight=.5,low=.60,high=.999),
 265:dict(district='NV01',yes='D',pvi=2,inc=2,adj=0,other=.005,history_weight=.5,low=.60,high=.999),
 271:dict(district='MT01',yes='D',pvi=-5,inc=0,adj=0,other=.02,history_weight=.2,poll=-1,moe=6,common=4,age=5.5,poll_bias=0,low=.12,high=.85),
 277:dict(district='AZ01',yes='D',pvi=-1,inc=0,adj=0,other=.01,history_weight=.35,history_adjustment=2,low=.35,high=.99),
 283:dict(district='NV03',yes='D',pvi=1,inc=2,adj=0,other=.005,history_weight=.5,low=.55,high=.999),
 325:dict(district='AZ02',yes='D',pvi=-7,inc=-2,adj=0,other=.003,history_weight=.6,low=.01,high=.80),
 337:dict(district='FL26',yes='D',pvi=-7,inc=-2,adj=-1,other=.01,low=.001,high=.70),
 373:dict(district='TX23',yes='R',pvi=-7,inc=0,adj=0,other=.01,low=.20,high=.99),
 385:dict(district='VA06',yes='D',pvi=-12,inc=-2,adj=1,other=.003,history_weight=.5,low=.001,high=.45),
 409:dict(district='NY01',yes='D',pvi=-4,inc=-2,adj=-3,other=.005,history_weight=.6,history_adjustment=-2,low=.03,high=.85),
 415:dict(district='TX25',yes='R',pvi=-11,inc=-2,adj=0,other=.005,low=.45,high=.9995),
 421:dict(district='MI04',yes='R',pvi=-3,inc=-2,adj=0,other=.005,history_weight=.6,history_adjustment=-1,low=.10,high=.97),
}

def run():
 out={'authority':'Primary uncalibrated judgment and source-sensitive margin model; not an automatic screen.',
      'source':'Official House Clerk2024statistics PDF, pages are PDF page numbers; current Census continuity verified except redrawnFL/TX; same shared model assumptions as house_extension_method.md.',
      'historical_returns':HISTORY,'cases':{}}
 for i,base in CASES.items():
  c=base.copy()
  if c['district'] in HISTORY:c['history']=HISTORY[c['district']]['D_margin_pp']
  p,d=previous.probability(c)
  grid=[previous.probability(c,national=n,beta=b,poll_shift=s,history_reference=h)[0]
        for n in [4,8,12] for b in [.6,.8,1] for s in [-3,0,3] for h in [-4.5,-2.5,-.5]]
  assert c['low']<=min(grid) and max(grid)<=c['high'],(i,min(grid),max(grid))
  out['cases'][str(i)]={'inputs':c,**d,'unrounded_p_yes':p,'primary_p_yes':round(p,2),
                       'scenario_range':[c['low'],c['high']],'grid_min':min(grid),'grid_max':max(grid)}
 return out

if __name__=='__main__':print(json.dumps(run(),indent=2))
