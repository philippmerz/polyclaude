"""Primary scenario model of the official US annual runner-up.

Not calibrated. Archived observations, calendar-boundary corrections, unknown
weeks, below-chart activity, future pace and version uncertainty are distinct.
No price or former screening label enters. Units: million streams.
"""
from pathlib import Path
import json,random,math,collections

HERE=Path(__file__).parent
INPUTS=json.loads((HERE/'spotify_joint_inputs.json').read_text())['rows']
SEED=202610172
N_DRAWS=20000
CUTOFFS=[('November15 hypothesis',31,.70),('November30 hypothesis',46,.20),
         ('December31 hypothesis',77,.10)]
UNSEEN=.10
EXCEPTION=.05
# Explicit subjective allocation of an exceptional alias/methodology/viral
# winner. This does not declare these events equally likely or infer actual
# missing streams. It prevents modeled zero tails from being called certainty.
EXCEPTION_WEIGHTS={2:.10,30:.10,58:.08,86:.05,114:.12,140:.04,142:.16,
                   170:.10,198:.08,219:.07,233:.10}
assert abs(sum(EXCEPTION_WEIGHTS.values())-1)<1e-10

def prepare():
    out=[]
    for row in INPUTS:
        r=dict(row);idx=r['review_index']
        r['base']=r['weekly_ytd_charted_streams']/1e6
        actual=[a['streams']/1e6 for a in r['first_actual_ytd_rows'] if a['streams']]
        old=[a['streams']/1e6 for a in r['late_2025_rows'] if a['streams']]
        r['early_anchor']=sum(actual+old)/len(actual+old) if actual+old else 1.0
        r['has_prior_december_data']=bool(old) or idx in [30,86,198]
        r['missing_jan1']='2026/01/01'in(r['weekly_ytd_absent_table_dates']or[])
        r['missing_other']=len(r['weekly_ytd_absent_table_dates']or[])-int(r['missing_jan1'])
        latest=r['weekly_latest']or{}
        r['last_pace']=latest.get('streams')/1e6 if latest.get('streams') else None
        r['pace_parameters']={2:(1.02,.20),142:(.90,.25),30:(1.0,.30)}.get(idx,(.90,.35))
        if r['title']=='Earrings':r['pace_parameters']=(.98,.15)
        if r['title']=='Babydoll'and r['artist']=='Dominic Fike':r['pace_parameters']=(1,.25)
        if r['title']=='Mr. Brightside':r['pace_parameters']=(1,.15)
        out.append(r)
    return out

def run(days,seed,unknown_scale=1.0,stateside_alias_prob=.15,boundary=True,draws=N_DRAWS):
    rng=random.Random(seed); rows=prepare(); wins=collections.Counter()
    for _ in range(draws):
        totals=[]
        uncertain_history=[j for j,r in enumerate(rows) if r['missing_other'] and not r['has_prior_december_data']]
        older_alias=rng.choice(uncertain_history) if uncertain_history and rng.random()<.10 else None
        fraction=rng.triangular(.08,.25,1/7) if boundary else 1.0
        # One shared fraction models where Jan1 lies in its seven-day label;
        # this is not a recovered daily observation or annual counting rule.
        common=rng.gauss(0,.06)
        for j,r in enumerate(rows):
            total=r['base'];idx=r['review_index'];jan=r['january1_chart_streams']
            if jan is not None:total-=jan/1e6*(1-fraction)
            if r['missing_jan1']:
                total+=rng.triangular(0,max(.5,r['early_anchor']*1.5),r['early_anchor']*.5)*fraction
            if r['missing_other']:
                anchor=r['early_anchor']
                if r['has_prior_december_data']:
                    avg=rng.triangular(.5*anchor,1.6*anchor,anchor)
                elif j==older_alias:
                    avg=rng.triangular(.5*anchor,2*anchor,anchor)
                else:
                    # Explicit low/pre-release forecast scenario, never data
                    # reconstruction. A shared exceptional-history branch and
                    # reserved unseen/alias outcomes cover its potential failure.
                    avg=rng.triangular(0,.30,.03)
                total+=r['missing_other']*avg*unknown_scale
            # Current #200 has1.99761m. Historical thresholds vary; this is
            # an imputation distribution, not an actual historical upper bound.
            if r['weekly_censored_rows']:
                total+=r['weekly_censored_rows']*rng.triangular(.10,2.50,.90)*unknown_scale
            base=r['last_pace'] if r['last_pace'] is not None else rng.triangular(.10,2.50,.90)
            med,sigma=r['pace_parameters']
            total+=(days/7)*base*math.exp(math.log(med)+common+rng.gauss(0,sigma))
            total+=rng.gauss(0,5)
            # Never sum the two duet IDs or the solo recording. This is an
            # explicit *hypothetical* aggregate-method branch for unknown
            # nonduplicated coverage, not observed extra listening.
            if idx==142 and rng.random()<stateside_alias_prob:
                total+=rng.triangular(0,110,40)
            totals.append((total,r['title'],r['track_id']))
        # Largest two totals, using title alphabetical order on an exact tie.
        top=sorted(totals,key=lambda a:(-a[0],a[1]))[:2]
        wins[top[1][2]]+=1
    return {tid:count/draws for tid,count in wins.items()}

def main():
    probabilities=collections.Counter(); by_cutoff=[]
    for j,(label,days,weight)in enumerate(CUTOFFS):
        conditional=run(days,SEED+j)
        by_cutoff.append(dict(label=label,days_from_Oct15=days,weight=weight,
                              conditional_runner_up_by_track=conditional))
        for tid,p in conditional.items():probabilities[tid]+=(1-UNSEEN-EXCEPTION)*weight*p
    by_index={r['review_index']:r for r in INPUTS if r['review_index']is not None}
    for idx,weight in EXCEPTION_WEIGHTS.items():probabilities[by_index[idx]['track_id']]+=EXCEPTION*weight
    index_p={str(idx):probabilities[r['track_id']]for idx,r in by_index.items()}
    sensitivities=[]
    for j,(days,unknown,alias,boundary)in enumerate([(31,.5,0,True),(31,1.5,.30,True),
                                                  (77,1.5,.30,True),(31,1,.15,False)]):
        p=run(days,SEED+100+j,unknown,alias,boundary,draws=5000)
        sensitivities.append(dict(days=days,unknown_scale=unknown,alias_probability=alias,
          boundary_adjusted=boundary,conditional_named={str(i):p.get(r['track_id'],0)for i,r in by_index.items()}))
    out=dict(author='primary',calibrated=False,seed=SEED,draws_per_cutoff=N_DRAWS,
       source_asof='2026-10-17, latest weekly label2026/10/15',cohort_size=len(INPUTS),
       interpretation='Annual official US#2 forecast from incomplete row-window proxy; scenario probabilities, not annual stream observations.',
       named_probabilities=index_p,unobserved_or_unmodeled_runner_up_mass=UNSEEN,
       exceptional_named_winner_mass=EXCEPTION,
       total_modeled_mass=sum(probabilities.values())+UNSEEN,
       top_forecasts=[dict(track_id=t,title=next(r['title']for r in INPUTS if r['track_id']==t),p=p)
                      for t,p in probabilities.most_common(15)],
       cutoff_scenarios=by_cutoff,sensitivities=sensitivities,
       parameter_caveats=['Missing dates never factual zero; censored counts imputed separately.',
          'Jan1 weekly label contains six2025 days; calendar allocation is assumed, not actual daily data.',
          'No exact official2026 aggregate cutoff or song-ID aggregation rule verified.',
          'All version uplift, rare winner, unknown history and future-persistence distributions are subjective.'])
    (HERE/'spotify_joint_results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k]for k in ['cohort_size','named_probabilities','total_modeled_mass','top_forecasts']},indent=2))

if __name__=='__main__':main()
