from pathlib import Path
import json,gzip,hashlib,random,math,importlib.util,datetime
ROOT=Path('/home/polyclaude/polyclaude');DATA=ROOT/'data/deep_review_20261017/work'
old_path=ROOT/'research/2026-10-17-deep-review/models/openrouter250_plateau_sensitivity_1925.py'
spec=importlib.util.spec_from_file_location('prior',old_path);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
prior=json.loads((DATA/'0352_oct12_anchor_sensitivity_1230.json').read_bytes());cur=json.loads((DATA/'tick060240_sources.json').read_bytes())['openrouter'];rp=ROOT/cur['receipt'];receipt=json.loads(rp.read_bytes());z=(rp.parent/receipt['body_path']).read_bytes();raw=gzip.decompress(z);assert hashlib.sha256(raw).hexdigest()==cur['raw_sha256'];assert hashlib.sha256(z).hexdigest()==cur['gzip_sha256'];points={r['x']:sum(r['ys'].values())/1e12 for r in json.loads(raw)['data']['data']};anchor=points['2026-10-12'];assert anchor==prior['inputs']['observed_completed_2026_10_12_T']
partial,remaining,oldsha=old.get_latest_partial();rng=random.Random(old.SEED);counts={k:0 for k in ['lt625','625_675','675_725','725_775','ge775']};branches={x[0]:{'n':0,'ge775':0} for x in old.BRANCHES}
for _ in range(old.N):
 # Consume the parent's uncertain-partial draw solely to preserve paired RNG paths.
 z=rng.random()
 if z<.25:unused=18.33824279449*math.exp(.25*rng.gauss(0,1))
 elif z<.90:unused=remaining*math.exp(.35*rng.gauss(0,1))
 else:unused=rng.uniform(0,36)
 q=rng.random();cum=0
 for name,w,mu,sd in old.BRANCHES:
  cum+=w
  if q<=cum:break
 common=rng.gauss(0,1);value=anchor;future=[]
 for k in range(5):
  value*=math.exp(mu+sd*(.5*common+math.sqrt(.75)*rng.gauss(0,1)));future.append(value)
 noise=rng.gauss(0,2) if rng.random()<.95 else rng.gauss(0,10);total=sum(future[1:])+noise
 bucket='lt625' if total<625 else '625_675' if total<675 else '675_725' if total<725 else '725_775' if total<775 else 'ge775';counts[bucket]+=1;branches[name]['n']+=1;branches[name]['ge775']+=int(bucket=='ge775')
assert counts==prior['oct12_anchor']['counts'];assert sum(counts.values())==old.N
for b in branches.values():b['ge775_fraction']=b['ge775']/b['n']
def total(g):return sum(anchor*(1+g)**k for k in range(2,6))
lo,hi=0.,.2
for _ in range(80):
 mid=(lo+hi)/2
 if total(mid)>=775:hi=mid
 else:lo=mid
record={'schema':'0442.primary_pre_own_quote.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'review_index':442,'p_yes':.44,'p_no':.56,'range_yes':[.05,.95],'actual_entry_reserve_pp':20,'own442_quote_not_viewed':True,'other_prices_known':'Held112quote/priorandotherfamilypricesknown; not an all-prices-blind forecast.','literal_binding':'442and112and352 full descriptions byteidentical, question thresholds differ:442[775,infinity),112[725,775),352<625. SamefourOct26/Nov2/Nov9/Nov16weeks andfirstNov23/Nov27ETfallback. Raw APIinput, separate chartTotals govern.','source':{'received_utc':cur['received_utc'],'raw_sha256':cur['raw_sha256'],'completed_anchor_T':anchor,'partial_Oct19_T_context_only':points['2026-10-19'],'targets_absent':True},'replay':{'N':old.N,'seed':old.SEED,'bin_counts':counts,'bin_probabilities':{k:v/old.N for k,v in counts.items()},'exact_prior_anchor_diagnostic_reproduced':True,'branches':old.BRANCHES,'by_branch':branches,'noise':'95%N0,2T/5%N0,10T; unmeasured aggregate rounding/revision distribution','correlation':.25},'adoption':'43.5135% >=775 pathfrequency rounded44%YES,56NO. Regimeweights/drifts/vols are primaryjudgment, not calibratedfutureodds; MC samplingprecision notmodelconfidence.','reserve_reason':'20pp samefamilyuncertainty budget:10futuregrowth/model+5display/vintage/source+5conditionalfill. SelectedYES24/NO36, no K5futuretail.','deterministic_countermodels':{'flat164_weekly_total_T':4*anchor,'weekly_growth_required_for775':hi,'fivepct_weekly_growth_total_T':total(.05),'interpretation':'FlatplateauNO;near5%weeklygrowthYES. Recent4.54%weeklydecline alone cannotbeanotherpenalty: originalpartialforecast/recentcompletedanchor alreadyincluded it.'},'joint_research_sensitivity':{'total_below725':.44,'725to775_exclusive':.12,'atleast775':.44,'limits':'Coherent3stateillustrationusingheld11212%andnew44244% roundedjudgments. No silentheldpriorchange or new adopted250partition; sourceandregimes shared.'},'portfolio':'Existing1125NO pays5/0/5 acrossbelow725/middle/upper. New442YES5 pays0/0/5: bothloseinmiddle, bothwinupper. New442NO5 pays5/5/0: combinedconditionalfloor5, not freeprofit/atomicitycertificate. CommonAI/venue/source/cutoff risks withKimi/112; no independencecredit.','hashes':{'parent_code':hashlib.sha256(old_path.read_bytes()).hexdigest(),'prior_anchor_diagnostic':hashlib.sha256((DATA/'0352_oct12_anchor_sensitivity_1230.json').read_bytes()).hexdigest()},'limitations':'Unknownfutureadoption/release/usage/competition; firstdisplayvintageandruleexactdisplayrounding vsraw projection notcertified. Category/language datasets notsubstitutes, partial/currentpace not actualweek. No transaction/heldfinancialprior mutation.'}
p=ROOT/'research/2026-10-17-deep-review/models/0442_primary_0658.json';p.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'p_yes':.44,'raw_probability':counts['ge775']/old.N,'required_weekly_growth':hi,'flat_total':4*anchor,'growth5pct_total':total(.05),'branch_probabilities':branches,'model_bytes':p.stat().st_size},indent=2))
