import json,datetime as dt,statistics as st
U=dt.timezone.utc
d=json.load(open('posts.json'))['data']
ts=sorted(dt.datetime.fromisoformat(p['createdAt'].replace('Z','+00:00')) for p in d)
now=dt.datetime(2026,11,14,13,tzinfo=U); rem=dt.timedelta(hours=76); cur=112
sims=[]
for h in range(24,24*73,6):  # 6h step starts
    a=now-dt.timedelta(hours=h)-rem
    if a<ts[0]: break
    sims.append((a,sum(1 for t in ts if a<=t<a+rem)))
def rep(lab,xs):
    xs=sorted(xs); n=len(xs)
    f=lambda lo,hi: sum(lo<=cur+x<=hi for x in xs)/n
    print(f"{lab:12s} n={n} med={st.median(xs)} mean={st.mean(xs):.0f} <180 {f(0,179):.2f} 180-219 {f(180,219):.2f} 220-259 {f(220,259):.2f} 260+ {f(260,9999):.2f}")
rep('all',[x for a,x in sims])
rep('last30d',[x for a,x in sims if a>now-dt.timedelta(days=33)])
rep('first40d',[x for a,x in sims if a<=now-dt.timedelta(days=33)])
rep('sat-start',[x for a,x in sims if a.weekday() in (4,5)])
print('market: <180 ~0.06  180-219 ~0.28  220-259 ~0.43  260+ ~0.23 (mids)')
