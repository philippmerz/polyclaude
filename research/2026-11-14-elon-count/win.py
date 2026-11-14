import json,datetime as dt,collections
d=json.load(open('posts.json'))['data']
ts=sorted(dt.datetime.fromisoformat(p['createdAt'].replace('Z','+00:00')) for p in d)
U=dt.timezone.utc
res=[]
for k in range(1,74):
    day=dt.datetime(2026,11,14,13,tzinfo=U)-dt.timedelta(days=k)
    if day<dt.datetime(2026,9,1,6,tzinfo=U): break
    n=sum(1 for t in ts if day<=t<day+dt.timedelta(hours=4))
    pre=sum(1 for t in ts if day-dt.timedelta(hours=5)<=t<day)
    res.append((day.date(),n,pre))
ns=[r[1] for r in res]
print('days',len(ns),'mean',sum(ns)/len(ns))
print('P(>=19)',sum(n>=19 for n in ns)/len(ns),'P(>=44)',sum(n>=44 for n in ns)/len(ns))
print('last30 P>=19',sum(n>=19 for n in ns[:30])/30, sorted(ns[:30]))
q=[r for r in res if r[2]==0]; print('pre-gap0 days',len(q),[r[1] for r in q])
