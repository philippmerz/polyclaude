import json,datetime as dt,urllib.request
U=dt.timezone.utc
d=json.load(open('posts.json'))['data']
ts=sorted(dt.datetime.fromisoformat(p['createdAt'].replace('Z','+00:00')) for p in d)
now=dt.datetime(2026,11,14,13,tzinfo=U)
for slug,s,e in [('elon-musk-of-tweets-november-10-november-17-2026',dt.datetime(2026,11,10,17,tzinfo=U),dt.datetime(2026,11,17,17,tzinfo=U)),
                 ('elon-musk-of-tweets-november-13-november-20-2026',dt.datetime(2026,11,13,17,tzinfo=U),dt.datetime(2026,11,20,17,tzinfo=U))]:
    cur=sum(1 for t in ts if s<=t<now); rem=e-now
    # empirical remaining-window counts over history (sliding by 1 day)
    sims=[]
    for k in range(1,80):
        a=now-dt.timedelta(days=k)-rem
        if a<ts[0]: break
        sims.append(sum(1 for t in ts if a<=t<a+rem))
    req=urllib.request.Request('https://gamma-api.polymarket.com/events?slug='+slug,headers={'User-Agent':'x'})
    ev=json.load(urllib.request.urlopen(req))[0]
    print(slug,'cur',cur,'rem_h',rem.total_seconds()/3600,'n',len(sims))
    for m in ev['markets']:
        if m.get('closed'): continue
        g=m['groupItemTitle']
        lo,hi=(int(g[:-1]),10**9) if g.endswith('+') else (lambda x:(int(x[0]),int(x[1])))(g.split('-')) if '-' in g else (0,int(g.split('<')[-1])-1 if '<' in g else 0)
        p=sum(1 for x in sims if lo<=cur+x<=hi)/len(sims)
        print(f"  {g:10s} bid {m.get('bestBid')} ask {m.get('bestAsk')} emp {p:.3f}")
