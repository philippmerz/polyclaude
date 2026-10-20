"""Primary-authored prequote scenario arithmetic, not calibrated sports model."""
from pathlib import Path
from itertools import product
import json, math, datetime, hashlib
ROOT=Path('/home/polyclaude/polyclaude')
DATA=ROOT/'data/deep_review_20261017/work'
facts=json.loads((DATA/'0440_followup_facts_0640.json').read_bytes())
stats=json.loads((DATA/'0440_results_reconstructed_0643.json').read_bytes())['team_reconstruction']
T,B,V='Tromsø','Bodø/Glimt','Viking'; focus=[T,B,V]
fixtures=set()
for f in facts['league_facts']['remaining_fixtures'].values():
 for text in f:
  h,a=text.split(' ',2)[2].split('–');fixtures.add((h,a))
fixtures=sorted(fixtures)
def norm(t):return 'Sandefjord Fotball' if t=='Sandefjord' else t
mean=sum(x['GF'] for x in stats.values())/sum(x['played'] for x in stats.values())
def wdl(h,a,tboost,leaderweak):
 def rate(team,field):
  d=stats[norm(team)];return (d[field]+5*mean)/(d['played']+5)
 lh=rate(h,'GF')*rate(a,'GA')/mean*1.12
 la=rate(a,'GF')*rate(h,'GA')/mean/1.12
 if h==T:lh*=tboost;la/=tboost
 if a==T:la*=tboost;lh/=tboost
 if h in [B,V]:lh*=leaderweak;la/=leaderweak
 if a in [B,V]:la*=leaderweak;lh/=leaderweak
 def pm(lam):
  q=[math.exp(-lam)]
  for k in range(1,31):q.append(q[-1]*lam/k)
  assert abs(sum(q)-1)<1e-8
  return q
 ph,pa=pm(lh),pm(la);p=[0.,0.,0.]
 for i,x in enumerate(ph):
  for j,y in enumerate(pa):p[0 if i>j else 1 if i==j else 2]+=x*y
 assert abs(sum(p)-1)<1e-8
 return p

def conv(d,p):
 z=[0.]*(len(d)+3)
 for n,x in enumerate(d):
  for pts,y in zip([3,1,0],p):z[n+pts]+=x*y
 return z

def scenario(label,weight,tboost,lweak):
 outside={t:[1.] for t in focus};shared=[]
 for h,a in fixtures:
  p=wdl(h,a,tboost,lweak)
  if h in focus and a in focus:shared.append((h,a,p))
  else:
   who=h if h in focus else a;p=p if who==h else p[::-1];outside[who]=conv(outside[who],p)
 assert len(shared)==4
 strict=inclusive=0.;mass=0.
 for outcomes in product(range(3),repeat=len(shared)):
  pts={T:40,B:56,V:56};prob=1.
  for (h,a,p),outcome in zip(shared,outcomes):
   prob*=p[outcome];pts[h]+=[3,1,0][outcome];pts[a]+=[0,1,3][outcome]
  mass+=prob
  for s,pr in enumerate(outside[T]):
   total=pts[T]+s
   for inc in [False,True]:
    ub=total-pts[B]-(0 if inc else 1);uv=total-pts[V]-(0 if inc else 1)
    term=prob*pr*sum(outside[B][:max(0,ub+1)])*sum(outside[V][:max(0,uv+1)])
    if inc:inclusive+=term
    else:strict+=term
 assert abs(mass-1)<1e-8 and 0<=strict<=inclusive<=1
 return {'label':label,'weight':weight,'T_goal_multiplier':tboost,'leader_goal_multiplier':lweak,'p_T_strictly_ahead_B_and_V':strict,'p_T_at_least_tied_with_B_and_V':inclusive,'p_with_5pct_tie_credit':strict+.05*(inclusive-strict)}
scenarios=[scenario('current_goals_regime',.90,1.,1.),scenario('T_form_up_both_leaders_down',.09,1.3,.8),scenario('extreme_common_collapse',.01,1.6,.6)]
weighted=sum(s['weight']*s['p_with_5pct_tie_credit'] for s in scenarios)
out={'schema':'0440.primary_prequote_model.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'price_exposure':'No case quote/book viewed; primary inputs from exactrules/currentpoints/goals/fixtures.','input_hashes':{x:hashlib.sha256((DATA/x).read_bytes()).hexdigest() for x in ['0440_followup_facts_0640.json','0440_results_reconstructed_0643.json']},'league_goal_mean_per_team_game':mean,'remaining_unique_focus_fixtures':fixtures,'starting_points':{T:40,B:56,V:56},'formulation':'5pseudogame shrink of23gameGF/GA towardleague mean, multiplicative goal rates/opponent defense, home1.12/away1/1.12. ExactindependentPoisson WDL with30goalcap; enumerateall81outcomes of4sharedgames thenconvolveothermatches. Conditionalothergamesindependent withinregime.','scenarios':scenarios,'weighted_T_above_B_V_with_5pct_tie_credit':weighted,'limitations':'Not calibrated or backtested; no lineup/injury/xG/fixture-specific motivation. Fourhead-to-heads coupled, otherlatent forms onlyhandweighted scenarios. Ignoresotherchampionshipcontenders, so pointscomparisons are upperenvelopes foractualtitle.5%tiecredit unfit, acknowledges27/26GDdeficit. Administrative/cancellation/source/adjudication risk not measured byfootball arithmetic.','forecast_pending_primary_synthesis':True}
p=ROOT/'research/2026-10-17-deep-review/models/0440_primary_model_0648.json';p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'scenarios':scenarios,'weighted':weighted,'model':str(p),'bytes':p.stat().st_size},indent=2))
