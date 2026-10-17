"""Offline same-clock weekend sensitivity from public hourly OHLC; no account/network."""
import gzip,json,math,statistics
from pathlib import Path
from datetime import datetime,timezone,timedelta
R=Path(__file__).resolve().parents[3];src=R/'logs/deep_review_20261017/crypto_hourly_root'
out={'method':'Same-clock Saturday19UTC to Sunday16UTC terminal and Monday04UTC extrema. 1hOHLC analogs, not1m resolution proof or calibrated posterior.','limitations':['Only52 past weekends; selection/regime and overlapping crypto shocks invalidate independent-trial confidence claims.','Hourly measurement uses Saturday19open, not exact current19:06spot, and continuousOHLC within1h.','Historical absence/hit counts do not bound future jump tails; Binance USDT-specific source.'],'symbols':{}}
for sym in ['BTCUSDT','ETHUSDT']:
 rows=json.load(gzip.open(src/f'{sym.lower()}_combined.json.gz','rt'));by={r[0]:r for r in rows};arr=[];wkend=[];weekday=[]
 for row in rows:
  d=datetime.fromtimestamp(row[0]/1000,timezone.utc);r=math.log(float(row[4])/float(row[1]));(wkend if d.weekday()in[5,6]else weekday).append(r)
  if d.weekday()!=5 or d.hour!=19:continue
  target21=int((d+timedelta(hours=20)).timestamp()*1000);target33=int((d+timedelta(hours=32)).timestamp()*1000)
  if target33 not in by:continue
  chosen=[by.get(int((d+timedelta(hours=j)).timestamp()*1000))for j in range(33)]
  if any(x is None for x in chosen):raise RuntimeError('hourlygap')
  s=float(row[1]);end=float(by[target21][4]);arr.append({'saturday_19_utc':d.isoformat(),'terminal_21h_log_return':math.log(end/s),'max_33h_log_return':math.log(max(float(x[2])for x in chosen)/s),'min_33h_log_return':math.log(min(float(x[3])for x in chosen)/s)})
 values=[r['terminal_21h_log_return']for r in arr]
 x={'analog_count':len(arr),'first':arr[0]['saturday_19_utc'],'last':arr[-1]['saturday_19_utc'],'terminal_21h_mean':statistics.mean(values),'terminal_21h_sample_sd':statistics.stdev(values),'weekend_hourly_sample_sd':statistics.stdev(wkend),'weekday_hourly_sample_sd':statistics.stdev(weekday),'analog_rows':arr}
 spot=81489.84 if sym=='BTCUSDT' else 2415.10
 if sym=='BTCUSDT':x['case71_terminal_at_or_below80k_count']=sum(v<=math.log(80000/spot)for v in values);x['case43_low_at_or_below78k_count']=sum(v['min_33h_log_return']<=math.log(78000/spot)for v in arr)
 else:x['case36_high_at_or_above2600_count']=sum(v['max_33h_log_return']>=math.log(2600/spot)for v in arr)
 out['symbols'][sym]=x
Path(__file__).with_name('crypto_weekend_results.json').write_text(json.dumps(out,indent=2)+'\n')
for sym,x in out['symbols'].items():print(sym,{k:v for k,v in x.items()if k!='analog_rows'})
