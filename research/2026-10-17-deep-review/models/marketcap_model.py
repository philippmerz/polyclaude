"""Primary-authored dated market-rank sensitivity. No network, orders or calibrated claims."""
from pathlib import Path
import json,math,hashlib
import numpy as np
BASE=Path('research/2026-10-17-deep-review/models')
src=Path('data/deep_review_20261017/market_cap_history_sources.json')
p=json.loads(src.read_text())
tickers=['NVDA','AAPL','MSFT','GOOGL','GOOG']
series={s:{r['date']:float(r['close'].replace('$','').replace(',','')) for r in p['daily_closes'][s]['latest90_rows']} for s in tickers}
from datetime import datetime
all_dates=sorted(set.intersection(*(set(v) for v in series.values())),key=lambda x:datetime.strptime(x,'%m/%d/%Y'))
# Dated issuer-reported shares, billions. Alphabet B valued at A as explicit sensitivity.
shares={'NVDA':24.10,'AAPL':14.59418,'MSFT':7.425545491,'Alphabet_A_B':6.703,'Alphabet_C':5.527}
prices=np.array([[series[s][d] for s in tickers] for d in all_dates])
caps=np.column_stack([prices[:,0]*shares['NVDA'],prices[:,1]*shares['AAPL'],prices[:,2]*shares['MSFT'],prices[:,3]*shares['Alphabet_A_B']+prices[:,4]*shares['Alphabet_C']])/1000
rets=np.diff(np.log(caps),axis=0);centered=rets-rets.mean(axis=0);cov=np.cov(rets.T);L=np.linalg.cholesky(cov);rng=np.random.default_rng(20261017);n=200000
company=['NVDA','AAPL','MSFT','Alphabet']
out={}
for days in [10,52]:
 scenarios={}
 for method in ['gaussian','vector_bootstrap','earnings_jumps','wide_jump_stress','student_t5']:
  if method=='vector_bootstrap':
   change=np.zeros((n,4))
   for _ in range(days):change+=centered[rng.integers(0,len(centered),n)]
  else:
   change=rng.standard_normal((n,4))@L.T*math.sqrt(days)
   if method=='student_t5':change*=np.sqrt(3/rng.chisquare(5,n))[:,None]
   if method in ['earnings_jumps','wide_jump_stress']:
    sig=np.array([.03,0,.08,.08]) if days==10 else np.array([.10,.06,.08,.08])
    if method=='wide_jump_stress':sig*=1.875
    change+=rng.standard_normal((n,4))*sig
  terminal=np.log(caps[-1])+change
  order=np.argsort(-terminal,axis=1)
  scenarios[method]={'largest':{s:float(np.mean(order[:,0]==j)) for j,s in enumerate(company)},'AAPL_exact_third':float(np.mean(order[:,2]==1))}
 out[str(days)]=scenarios
inputs={'as_of':'2026-10-17','source_packet_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_urls':{s:p['daily_closes'][s]['url'] for s in tickers},'dates':all_dates,'tickers':tickers,'price_rows':prices.tolist(),'fixed_shares_billions':shares,'marketcap_company_order':company,'latest_caps_trillion':caps[-1].tolist(),'log_gap_to_NVDA':dict(zip(company,np.log(caps[-1,0]/caps[-1]).tolist())),'empirical_daily_logreturn_sd':dict(zip(company,np.std(rets,axis=0,ddof=1).tolist())),'correlation':np.corrcoef(rets.T).tolist(),'covariance':cov.tolist()}
(BASE/'marketcap_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
result={'primary_author':True,'seed':20261017,'samples_per_method':n,'input_dates':[all_dates[0],all_dates[-1]],'horizons_sessions':[10,52],'zero_expected_log_return':'No recent-rally drift extrapolation; not risk-neutral option pricing. Holding shares fixed; dividends not added to market cap.','earnings_logshock_sd_short':[.03,0,.08,.08],'earnings_logshock_sd_long':[.10,.06,.08,.08],'wide_jump_multiplier':1.875,'result':out,'limitations':['Only top4 priced jointly; other global contenders treated as explicit residual judgment in each report','Fixed quarterly shares and unlisted B=A assumption; exact resolution consensus can use different company aggregation','Independent earnings surprises with unknown real tails; empirical covariance can shift','Gaussian/bootstrap distributions not calibrated tail probabilities; short series cannot prove absence of unprecedented jumps','Studentt5 terminal scale is sensitivity, not calibrated dynamic process','Oct31 is Saturday: assume last regular Oct30 close; no explicit venue weekend clarification','52remainingDecsessions uses standard Thanksgiving/Christmas closures; extraordinary closure can differ']}
(BASE/'marketcap_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'latest_caps':inputs['latest_caps_trillion'],'sd':inputs['empirical_daily_logreturn_sd'],'corr':inputs['correlation'],'results':out}))
