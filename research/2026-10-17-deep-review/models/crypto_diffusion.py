"""Offline physical-price sensitivities; no account/network/order functions."""
import math,json,gzip,statistics
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'data/deep_review_20261017/crypto_price_sources.json'
p=json.loads(SRC.read_text());asof=datetime.fromisoformat(p['quotes']['BTCUSDT']['last_price_ticker']['retrieved_utc'])
Phi=lambda z:.5*math.erfc(-z/math.sqrt(2))
def upper_hit(a,mu,s,t):
 if a<=0:return 1.
 z=s*math.sqrt(t)
 return Phi((mu*t-a)/z)+math.exp(2*mu*a/(s*s))*Phi((-mu*t-a)/z)
cases={36:('ETHUSDT',2600,'up','2026-10-19T04:00:00+00:00'),43:('BTCUSDT',78000,'down','2026-10-19T04:00:00+00:00'),50:('BTCUSDT',100000,'up','2027-01-01T05:00:00+00:00'),71:('BTCUSDT',80000,'terminal_above','2026-10-18T16:00:00+00:00'),99:('BTCUSDT',95000,'up','2026-11-01T04:00:00+00:00'),110:('XRPUSDT',2.60,'up','2027-01-01T05:00:00+00:00')}
out={'asof_utc':asof.isoformat(),'method':'Log-price Brownian first passage (reflection with drift) or single terminal marginal. Physical sensitivity, not risk-neutral quote or calibrated forecast. Zero log drift central; no historical mean extrapolation.','daily_return_statistics':{},'cases':{},'limitations':['Daily closes are lagged to Oct16; no derivatives/options implied vols captured.','Continuous high/low barrier approximates final one-minute candle extremes, includes actual intra-minute trades but may miss missing/exchange-bad-data effects.','Historical daily volatility does not bound jumps, weekend regime, liquidations, fat tails, event shocks or momentum.','Past no-hit established separately; this model only conditions future prices.','370d first daily bar is pre-window for some claims; full closed returns still used solely for volatility, never as eligible trigger data.']}
for sym,meta in p['daily_history_370d'].items():
 rows=json.load(gzip.open(ROOT/meta['receipt'],'rt'))
 rows=rows[:-1]
 closes=[float(x[4])for x in rows]
 ret=[math.log(b/a)for a,b in zip(closes,closes[1:])]
 out['daily_return_statistics'][sym]={str(n):{'n':n,'mean_log_return':statistics.mean(ret[-n:]),'sample_sd_daily':statistics.stdev(ret[-n:]),'annualized_sd_365':statistics.stdev(ret[-n:])*math.sqrt(365)}for n in [20,60,180]}
for i,(sym,k,kind,end)in cases.items():
 spot=float(p['quotes'][sym]['last_price_ticker']['payload']['price']);t=(datetime.fromisoformat(end)-asof).total_seconds()/86400
 arr=[]
 for n in [20,60,180]:
  s=out['daily_return_statistics'][sym][str(n)]['sample_sd_daily']
  for mult in [1.,1.5,2.]:
   vol=s*mult
   for mu in [0.,.001,-.001]:
    if kind=='terminal_above':v=Phi((math.log(spot/k)+mu*t)/(vol*math.sqrt(t)))
    elif kind=='up':v=upper_hit(math.log(k/spot),mu,vol,t)
    else:v=upper_hit(math.log(spot/k),-mu,vol,t)
    arr.append({'lookback_days':n,'vol_multiplier':mult,'log_drift_per_day':mu,'daily_vol':vol,'probability':v})
 out['cases'][str(i)]={'symbol':sym,'spot':spot,'barrier':k,'claim':kind,'expiry_utc':end,'remaining_days':t,'sensitivities':arr,'central_baseline_60d_zero_drift':next(x['probability']for x in arr if x['lookback_days']==60 and x['vol_multiplier']==1 and x['log_drift_per_day']==0)}
path=Path(__file__).with_name('crypto_diffusion_results.json');path.write_text(json.dumps(out,indent=2)+'\n')
for k,r in out['cases'].items():print(k,r['remaining_days'],r['central_baseline_60d_zero_drift'],min(x['probability']for x in r['sensitivities']),max(x['probability']for x in r['sensitivities']))
print(json.dumps(out['daily_return_statistics']))
