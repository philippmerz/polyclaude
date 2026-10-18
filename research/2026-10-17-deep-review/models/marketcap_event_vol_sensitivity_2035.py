"""Sensitivity-only replay of the four-firm rank model's MSFT/Alphabet event shocks.

Reads only the frozen case rules, marketcap_inputs, and existing output. Never changes those.
"""
from __future__ import annotations
import gzip, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
MODEL=ROOT/'research/2026-10-17-deep-review/models'
DATA=ROOT/'data/deep_review_20261017/work'
INPUT=MODEL/'marketcap_inputs.json'
BASE=DATA/'0260_joint_diagnostic.json'
OUT=DATA/'0260_event_vol_sensitivity_2035.json'
RULES=ROOT/'research/2026-10-17-primary-market-review-rules.jsonl.gz'
N=100_000; SEED=19620261018; WINDOWS=(20,89); SHOCKS=(0.0,0.04,0.06,0.08)
COMPANIES=('NVDA','AAPL','MSFT','Alphabet')
METHODS=('gaussian','vector_bootstrap','earnings_independent','earnings_correlated','wide_earnings','student_t5','MSFT_relative_minus5pct','MSFT_relative_plus5pct')
def sha(b): return hashlib.sha256(b).hexdigest()
def identities():
 found={}
 with gzip.open(RULES,'rt',encoding='utf-8') as f:
  for line in f:
   r=json.loads(line)
   if int(r['review_index']) in (260,268):
    i=int(r['review_index']); found[str(i)]={'market_id':str(r['id']),'condition_id':str(r['conditionId']),'criteria_sha256':r['criteria_sha256'],'description_sha256':sha(str(r['description']).encode())}
 if len(found)!=2: raise ValueError('frozen identity coverage failure')
 return found
def consume_method(rng, method):
 """Consume the existing model's RNG sequence for a non-target method."""
 if method=='vector_bootstrap':
  for _ in range(10): rng.integers(0,100_000,N)
  return
 rng.standard_normal((N,4))
 if method=='student_t5': rng.chisquare(5,N)
 if method.startswith('earnings') or method in ('wide_earnings','MSFT_relative_minus5pct','MSFT_relative_plus5pct'):
  z=rng.standard_normal((N,4))
  if method=='earnings_correlated': pass

def run():
 if OUT.exists(): raise FileExistsError(f'refusing overwrite: {OUT}')
 inp=json.loads(INPUT.read_text()); base=json.loads(BASE.read_text())
 if base['inputs_sha256']!=sha(INPUT.read_bytes()): raise ValueError('base/input hash mismatch')
 if base['seed']!=SEED or base['samples_per_cell']!=N: raise ValueError('base simulation spec mismatch')
 if base['frozen_identities']!=identities(): raise ValueError('frozen IDs changed')
 price=np.asarray(inp['price_rows'],float); sh=inp['fixed_shares_billions']
 caps=np.column_stack((price[:,0]*sh['NVDA'],price[:,1]*sh['AAPL'],price[:,2]*sh['MSFT'],price[:,3]*sh['Alphabet_A_B']+price[:,4]*sh['Alphabet_C']))/1000
 returns=np.diff(np.log(caps),axis=0)
 rng=np.random.default_rng(SEED); results={}
 for window in WINDOWS:
  r=returns[-window:]; centered=r-r.mean(axis=0); chol=np.linalg.cholesky(np.cov(r.T))
  target=None
  for method in METHODS:
   if method=='vector_bootstrap':
    for _ in range(10): rng.integers(0,len(centered),N)
    continue
   base_change=rng.standard_normal((N,4))@chol.T*np.sqrt(10)
   if method=='student_t5': base_change*=np.sqrt(3/rng.chisquare(5,N))[:,None]
   if method=='earnings_independent':
    z=rng.standard_normal((N,4)); target=(base_change,z)
   elif method.startswith('earnings') or method in ('wide_earnings','MSFT_relative_minus5pct','MSFT_relative_plus5pct'):
    z=rng.standard_normal((N,4))
    if method=='earnings_correlated': z[:,3]=.5*z[:,2]+np.sqrt(.75)*z[:,3]
  if target is None: raise AssertionError('target draws not generated')
  base_change,z=target; results[str(window)]={}
  for shock in SHOCKS:
   sig=np.array([.03,0,shock,shock]); change=base_change+z*sig
   order=np.argsort(-(np.log(caps[-1])+change),axis=1)
   thirds={}; ranks={}
   for j,name in enumerate(COMPANIES):
    rank=np.argmax(order==j,axis=1)
    ranks[name]=[float(np.mean(rank==k)) for k in range(4)]
    thirds[name]=ranks[name][2]
   results[str(window)][f'{shock:.2%}']={'event_sigma_msft_alphabet':shock,'exact_third':thirds,'rank_1_to_4':ranks}
 # The .08 identical-random-path replay must match all existing cells exactly.
 for w in WINDOWS:
  got=results[str(w)]['8.00%']['exact_third']
  exp=base['all_cell_thirds'][str(w)]['earnings_independent']
  if got!=exp: raise AssertionError(f'8% baseline differs for window {w}: {got} != {exp}')
 # Reuse existing official-source receipts only; none identifies the July 2026
 # earnings announcement/session date for both firms, so don't remove any row.
 packet=json.loads((ROOT/'data/deep_review_20261017/market_cap_history_sources.json').read_text())
 payload={'schema':'polyclaude.marketcap_event_vol_sensitivity.v1','created_utc':datetime.now(timezone.utc).isoformat(),'inputs_path':str(INPUT.relative_to(ROOT)),'inputs_sha256':sha(INPUT.read_bytes()),'base_diagnostic_sha256':sha(BASE.read_bytes()),'frozen_identities':identities(),'seed':SEED,'samples_per_cell':N,'windows_sessions':list(WINDOWS),'method':'Existing earnings_independent terminal path; same simulated covariance draw and independent event-shock z across four sigma settings. NVDA event sigma remains 3%, Apple 0%; MSFT and Alphabet event sigmas are each 0/4/6/8%. No drift or forecast selected.','exact_third_by_window_and_added_sigma':results,'eight_percent_reproduction':'Both windows and all company exact-third cells equal the existing marketcap_joint_2005 diagnostic exactly.','july_return_exclusion':{'performed':False,'reason':'The captured official primary-source packet documents next Q3 earnings dates in October, but does not establish the July 2026 MSFT and Alphabet Q2 release dates plus corresponding next-session return dates from a saved primary receipt. No price row was excluded.','source_packet_sha256':sha((ROOT/'data/deep_review_20261017/market_cap_history_sources.json').read_bytes()),'covered_dates':'marketcap_inputs contains common dated price rows and 89 joint returns; event-date inputs were not present in the saved primary receipts inspected.'},'margin_sensitivity':{'reference_selected_margin_pp':1.47,'comparison':'Change in equal-window Alphabet exact-third output versus existing equal-window 8% earnings-independent value; purely a sensitivity comparison, not an adopted probability.','equal_window_alphabet_exact_third_by_sigma':{f'{s:.2%}':sum(results[str(w)][f'{s:.2%}']['exact_third']['Alphabet'] for w in WINDOWS)/2 for s in SHOCKS},'absolute_change_from_8pct_pp':{f'{s:.2%}':100*abs(sum(results[str(w)][f'{s:.2%}']['exact_third']['Alphabet'] for w in WINDOWS)/2 - base['equal_window_earnings_independent_third_by_company']['Alphabet']) for s in SHOCKS},'at_least_1_47pp_change':{f'{s:.2%}':100*abs(sum(results[str(w)][f'{s:.2%}']['exact_third']['Alphabet'] for w in WINDOWS)/2 - base['equal_window_earnings_independent_third_by_company']['Alphabet']) >= 1.47 for s in SHOCKS}},'interpretation':'Changing assumed MSFT/Alphabet event sigma changes modeled Alphabet rank output; the diagnostic only measures sensitivity of the specified path construction. It neither establishes the correct sigma nor resolves market economics.'}
 OUT.write_text(json.dumps(payload,indent=2)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'bytes':OUT.stat().st_size,'inputs_sha256':payload['inputs_sha256'],'8pct_exact_reproduction':True,'equal_window_alphabet':payload['margin_sensitivity']['equal_window_alphabet_exact_third_by_sigma'],'change_pp':payload['margin_sensitivity']['absolute_change_from_8pct_pp'],'threshold_crossed':payload['margin_sensitivity']['at_least_1_47pp_change']}))
if __name__=='__main__': run()
