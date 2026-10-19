#!/usr/bin/env python3
"""Paired sensitivity anchoring the latest complete OpenRouter week to Oct12."""
from __future__ import annotations
import gzip, hashlib, importlib.util, json, math, random
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'data/deep_review_20261017'
SOURCE_MODEL=ROOT/'research/2026-10-17-deep-review/models/openrouter250_plateau_sensitivity_1925.py'
CHART_SUMMARY=DATA/'work/0352_chart_weekly_totals_1220.json'
OUT=DATA/'work/0352_oct12_anchor_sensitivity_1230.json'
spec=importlib.util.spec_from_file_location('parent_plateau_model',SOURCE_MODEL)
parent=importlib.util.module_from_spec(spec); spec.loader.exec_module(parent)
chart=json.loads(CHART_SUMMARY.read_text())
series=json.loads(gzip.decompress((ROOT/chart['receipt']['gzip_path']).read_bytes()))['data']['data']
assert hashlib.sha256(gzip.decompress((ROOT/chart['receipt']['gzip_path']).read_bytes())).hexdigest()==chart['receipt']['raw_sha256']
points={r['x']:sum(r['ys'].values())/1e12 for r in series}
anchor=points['2026-10-12']
assert abs(anchor-164.043985914931)<1e-12
partial,remaining,_=parent.get_latest_partial()

bins=('lt625','625_675','675_725','725_775','ge775')
old_counts={k:0 for k in bins}; new_counts={k:0 for k in bins}
paired_transitions={}
rng=random.Random(parent.SEED)
for _ in range(parent.N):
    z=rng.random()
    if z<.25: s=18.33824279449*math.exp(.25*rng.gauss(0,1))
    elif z<.90: s=remaining*math.exp(.35*rng.gauss(0,1))
    else: s=rng.uniform(0,36)
    old_week0=partial+s  # consume the parent's old current-week uncertainty draw
    q=rng.random(); cumul=0.0
    for branch in parent.BRANCHES:
        cumul+=branch[1]
        if q<=cumul: break
    _,_,mu,sd=branch
    common=rng.gauss(0,1)
    old_value=old_week0; new_value=anchor
    old_future=[]; new_future=[]
    for _week in range(5):
        g=mu+sd*(.5*common+math.sqrt(.75)*rng.gauss(0,1))
        old_value*=math.exp(g); new_value*=math.exp(g)
        old_future.append(old_value); new_future.append(new_value)
    noise=rng.gauss(0,2) if rng.random()<.95 else rng.gauss(0,10)
    old_total=sum(old_future[1:])+noise
    new_total=sum(new_future[1:])+noise
    def bucket(x):
        if x<625: return 'lt625'
        if x<675: return '625_675'
        if x<725: return '675_725'
        if x<775: return '725_775'
        return 'ge775'
    ob,nb=bucket(old_total),bucket(new_total)
    old_counts[ob]+=1; new_counts[nb]+=1
    paired_transitions[f'{ob}->{nb}']=paired_transitions.get(f'{ob}->{nb}',0)+1
old_frac={k:v/parent.N for k,v in old_counts.items()}
new_frac={k:v/parent.N for k,v in new_counts.items()}
assert old_frac=={'lt625':.16901,'625_675':.10271,'675_725':.1221,'725_775':.115545,'ge775':.490635}
assert sum(old_counts.values())==sum(new_counts.values())==parent.N
assert abs(sum(new_frac.values())-1)<1e-12
result={
 'schema':'openrouter352_oct12_anchor_sensitivity.v1',
 'compiled_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'Unadopted paired mathematical sensitivity. Consumes parent current-week uncertainty draws, then replaces week0 with the observed completed Oct12 raw total. No Oct19 extrapolation, adopted probability, or action.',
 'identity':{'review_index':352,'condition_id':'0x5c1af819b4f93f4fdfb9389478ab381d8b4eed221ed8a0db5cad0cdfb9c418b7','market_id':'5763812','criteria_sha256':'6a4aca71a493c91b3b731927bd33e409c7b4d2862d1a56a4bde181f6ddfa8c7d'},
 'inputs':{'draws':parent.N,'seed':parent.SEED,'branches':parent.BRANCHES,'same_cutoff_weights':{'prior_complete_day_18T_remaining':.25,'latest_UI_remaining_proxy':.65,'uniform_0_to_36T':.10},'innovation_correlation':.25,'revision_noise':'same paired noise: 95% N(0,2T), 5% N(0,10T)','parent_partial_T':partial,'parent_remaining_proxy_T':remaining,'observed_completed_2026_10_12_T':anchor,'ignored_partial_2026_10_19_T':points['2026-10-19']},
 'hashes':{'parent_model_sha256':hashlib.sha256(SOURCE_MODEL.read_bytes()).hexdigest(),'chart_summary_sha256':hashlib.sha256(CHART_SUMMARY.read_bytes()).hexdigest(),'chart_raw_sha256':chart['receipt']['raw_sha256']},
 'bucket_ranges_T':{'lt625':'(-inf,625)','625_675':'[625,675)','675_725':'[675,725)','725_775':'[725,775)','ge775':'[775,inf)'},
 'parent_replay':{'counts':old_counts,'fractions':old_frac,'asserted_exact_against_parent':True},
 'oct12_anchor':{'counts':new_counts,'fractions':new_frac,'paired_delta_vs_parent':{k:new_frac[k]-old_frac[k] for k in bins}},
 'paired_bucket_transition_counts':paired_transitions,
 'target_window':'Each simulated path keeps five generated weeks as Oct19, Oct26, Nov2, Nov9, Nov16; sum of generated weeks 2–5 (Oct26–Nov16) is compared with the same four-week band.'
}
OUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'output':str(OUT.relative_to(ROOT)),'bytes':OUT.stat().st_size,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'parent':old_frac,'anchor':new_frac,'delta':result['oct12_anchor']['paired_delta_vs_parent']},indent=2))
