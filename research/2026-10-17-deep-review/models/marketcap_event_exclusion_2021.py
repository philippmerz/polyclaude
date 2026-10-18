"""Sensitivity replay removing dated July earnings-session returns from 89-day covariance.
Uses only existing marketcap inputs, official event-history packet, and prior diagnostics.
"""
from __future__ import annotations
import gzip, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
MODEL=ROOT/'research/2026-10-17-deep-review/models'; DATA=ROOT/'data/deep_review_20261017/work'
INPUT=MODEL/'marketcap_inputs.json'; BASE=DATA/'0260_joint_diagnostic.json'; SENS=DATA/'0260_event_vol_sensitivity_2035.json'
EVENT=DATA/'0260_earnings_event_history.json'; RULES=ROOT/'research/2026-10-17-primary-market-review-rules.jsonl.gz'
SUMMARY=DATA/'0260_event_exclusion_sensitivity_2026.json'; ARRAYS=DATA/'0260_event_exclusion_rank_marginals_2026.json'
N=100_000; SEED=19620261018; WINDOWS=(20,89); SIGMAS=(0.0,.04,.06,.08)
COMPANIES=('NVDA','AAPL','MSFT','Alphabet')
METHODS=('gaussian','vector_bootstrap','earnings_independent','earnings_correlated','wide_earnings','student_t5','MSFT_relative_minus5pct','MSFT_relative_plus5pct')
def sha(b): return hashlib.sha256(b).hexdigest()
def ids():
 out={}
 with gzip.open(RULES,'rt',encoding='utf-8') as f:
  for line in f:
   x=json.loads(line); i=int(x['review_index'])
   if i in (260,268): out[str(i)]={'market_id':str(x['id']),'condition_id':str(x['conditionId']),'criteria_sha256':x['criteria_sha256'],'description_sha256':sha(str(x['description']).encode())}
 if len(out)!=2: raise ValueError('frozen identity validation failed')
 return out
def run():
 if SUMMARY.exists() or ARRAYS.exists(): raise FileExistsError('refusing to overwrite exclusion sensitivity outputs')
 inp=json.loads(INPUT.read_text()); event=json.loads(EVENT.read_text()); base=json.loads(BASE.read_text()); sens=json.loads(SENS.read_text())
 if base['inputs_sha256']!=sha(INPUT.read_bytes()) or sens['inputs_sha256']!=sha(INPUT.read_bytes()): raise ValueError('input hash mismatch')
 if base['frozen_identities']!=ids() or sens['frozen_identities']!=ids(): raise ValueError('identity mismatch')
 excluded_iso=sorted({e['tickers']['MSFT']['next_session_close']['date'] for e in event['q2_events'] if e['company']=='Microsoft'}|{e['tickers']['GOOGL']['next_session_close']['date'] for e in event['q2_events'] if e['company']=='Alphabet'})
 # Verify primary event evidence receipts and input row alignment.
 official_receipts=[]
 for ev in event['q2_events']:
  rp=ROOT/ev['official_release_receipt']; rec=json.loads(rp.read_text())
  if rec.get('status')!=200: raise ValueError(f'official release receipt not successful: {rp}')
  body=ROOT/rec['gzip_path']; raw=gzip.open(body,'rb').read()
  if len(raw)!=rec['body_bytes'] or sha(raw)!=rec['sha256_uncompressed'] or sha(body.read_bytes())!=rec['sha256_gzip']: raise ValueError(f'official release body hash mismatch: {rp}')
  official_receipts.append({'company':ev['company'],'url':rec['url'],'retrieved_utc':rec['retrieved_utc'],'status':rec['status'],'receipt_path':str(rp.relative_to(ROOT)),'body_path':str(body.relative_to(ROOT)),'body_sha256':rec['sha256_uncompressed'],'gzip_sha256':rec['sha256_gzip']})
  for sym, fields in ev['tickers'].items():
   p=ROOT/fields['nasdaq_archive']['source_path']
   if sha(gzip.open(p,'rb').read())!=fields['nasdaq_archive']['source_sha256_uncompressed']: raise ValueError(f'price receipt hash mismatch: {sym}')
 dates=inp['dates']; aligned=dates[1:]
 to_input_date=lambda iso: f"{iso[5:7]}/{iso[8:10]}/{iso[:4]}"
 excluded=[to_input_date(d) for d in excluded_iso]
 if not all(d in aligned for d in excluded): raise ValueError(f'event-return date not in return sample: {excluded}')
 price=np.asarray(inp['price_rows'],float); sh=inp['fixed_shares_billions']
 caps=np.column_stack((price[:,0]*sh['NVDA'],price[:,1]*sh['AAPL'],price[:,2]*sh['MSFT'],price[:,3]*sh['Alphabet_A_B']+price[:,4]*sh['Alphabet_C']))/1000
 returns=np.diff(np.log(caps),axis=0); rng=np.random.default_rng(SEED); outputs={}; covariance_meta={}
 for w in WINDOWS:
  r0=returns[-w:]; date0=aligned[-w:]
  mask=np.array([d not in excluded for d in date0]) if w==89 else np.ones(len(r0),dtype=bool)
  r=r0[mask]; date_used=[d for d,m in zip(date0,mask) if m]
  centered=r-r.mean(axis=0); cov=np.cov(r.T); eig=np.linalg.eigvalsh(cov)
  if np.min(eig)<=0: raise ValueError(f'covariance not positive definite for {w}: {eig.tolist()}')
  chol=np.linalg.cholesky(cov); outputs[str(w)]={}
  covariance_meta[str(w)]={'source_return_rows':len(r0),'used_return_rows':len(r),'removed_dates':[d for d,m in zip(date0,mask) if not m],'first_used_return_date':date_used[0],'last_used_return_date':date_used[-1],'covariance_min_eigenvalue':float(np.min(eig)),'covariance_positive_definite':True}
  target=None
  for method in METHODS:
   if method=='vector_bootstrap':
    for _ in range(10): rng.integers(0,len(centered),N)
    continue
   change=rng.standard_normal((N,4))@chol.T*np.sqrt(10)
   if method=='student_t5': change*=np.sqrt(3/rng.chisquare(5,N))[:,None]
   if method=='earnings_independent': target=(change,rng.standard_normal((N,4)))
   elif method.startswith('earnings') or method in ('wide_earnings','MSFT_relative_minus5pct','MSFT_relative_plus5pct'):
    z=rng.standard_normal((N,4))
    if method=='earnings_correlated':z[:,3]=.5*z[:,2]+np.sqrt(.75)*z[:,3]
  ch,z=target
  for sig in SIGMAS:
   incr=z*np.array([.03,0,sig,sig]); order=np.argsort(-(np.log(caps[-1])+ch+incr),axis=1); ranks={}
   for j,name in enumerate(COMPANIES):
    rank=np.argmax(order==j,axis=1); ranks[name]=[float(np.mean(rank==k)) for k in range(4)]
   if not np.isclose(sum(ranks[c][0] for c in COMPANIES),1,atol=1e-12) or not np.allclose([sum(ranks[c][k] for c in COMPANIES) for k in range(4)],[1]*4,atol=1e-12): raise ValueError('rank marginals fail normalization')
   outputs[str(w)][f'{sig:.0%}']={'rank_1_to_4':ranks,'exact_third':{c:ranks[c][2] for c in COMPANIES},'sum_rank_marginals':[sum(ranks[c][k] for c in COMPANIES) for k in range(4)]}
 # Confirm untouched 20-day results equal the prior unfiltered sensitivity run exactly.
 for s in SIGMAS:
  k=f'{s:.0%}'; sk=f'{s:.2%}'
  if outputs['20'][k]['exact_third']!=sens['exact_third_by_window_and_added_sigma']['20'][sk]['exact_third']: raise AssertionError(f'20-day baseline changed at {k}')
 base_alpha=base['equal_window_earnings_independent_third_by_company']['Alphabet']
 prior_alpha89=sens['exact_third_by_window_and_added_sigma']['89']
 alpha_equal={f'{s:.0%}':(outputs['20'][f'{s:.0%}']['exact_third']['Alphabet']+outputs['89'][f'{s:.0%}']['exact_third']['Alphabet'])/2 for s in SIGMAS}
 out={'schema':'polyclaude.marketcap_event_exclusion_sensitivity.v1','created_utc':datetime.now(timezone.utc).isoformat(),'review_indices_validated':[260,268],'frozen_identities':ids(),'inputs_path':str(INPUT.relative_to(ROOT)),'inputs_sha256':sha(INPUT.read_bytes()),'base_diagnostic_sha256':sha(BASE.read_bytes()),'event_vol_sensitivity_sha256':sha(SENS.read_bytes()),'official_event_history_path':str(EVENT.relative_to(ROOT)),'official_event_history_sha256':sha(EVENT.read_bytes()),'official_event_receipts_verified':official_receipts,'seed':SEED,'samples_per_cell':N,'horizon_sessions':10,'windows_sessions':[20,89],'event_shock_sd_msft_alphabet':[0,.04,.06,.08],'covariance_rows':covariance_meta,'results_path':str(ARRAYS.relative_to(ROOT)),'equal_window_alphabet_exact_third_by_sigma':alpha_equal,'change_vs_original89day8pct_pp':{f'{s:.0%}':100*(alpha_equal[f'{s:.0%}']-base_alpha) for s in SIGMAS},'change_vs_prior_unexcluded_equalwindow_same_sigma_pp':{f'{s:.0%}':100*(alpha_equal[f'{s:.0%}']-(sens['exact_third_by_window_and_added_sigma']['20'][f'{s:.2%}']['exact_third']['Alphabet']+prior_alpha89[f'{s:.2%}']['exact_third']['Alphabet'])/2) for s in SIGMAS},'one_47pp_margin_exceeded_by_covariance_exclusion':{f'{s:.0%}':abs(100*(alpha_equal[f'{s:.0%}']-(sens['exact_third_by_window_and_added_sigma']['20'][f'{s:.2%}']['exact_third']['Alphabet']+prior_alpha89[f'{s:.2%}']['exact_third']['Alphabet'])/2))>=1.47 for s in SIGMAS},'limitations':'Removing two dated historical sessions is a sensitivity only. The remaining sample is still sparse and nonstationary; event observations do not calibrate the forward shock distribution. No forecast or probability adopted.'}
 arr={'schema':'polyclaude.marketcap_event_exclusion_rank_marginals.v1','created_utc':out['created_utc'],'inputs_sha256':out['inputs_sha256'],'event_history_sha256':out['official_event_history_sha256'],'rank_1_to_4':outputs}
 SUMMARY.write_text(json.dumps(out,separators=(',',':'))+'\n'); ARRAYS.write_text(json.dumps(arr,indent=2)+'\n')
 if SUMMARY.stat().st_size>4096: raise ValueError(f'summary exceeds 4KB: {SUMMARY.stat().st_size}')
 print(json.dumps({'summary':str(SUMMARY.relative_to(ROOT)),'summary_bytes':SUMMARY.stat().st_size,'arrays':str(ARRAYS.relative_to(ROOT)),'array_bytes':ARRAYS.stat().st_size,'removed':covariance_meta['89']['removed_dates'],'rows_89':covariance_meta['89']['used_return_rows'],'covariance_pd':{w:v['covariance_positive_definite'] for w,v in covariance_meta.items()},'equal_alpha':alpha_equal,'delta_vs_unexcluded_pp':out['change_vs_prior_unexcluded_equalwindow_same_sigma_pp'],'margin_crossed':out['one_47pp_margin_exceeded_by_covariance_exclusion']}))
if __name__=='__main__':run()
