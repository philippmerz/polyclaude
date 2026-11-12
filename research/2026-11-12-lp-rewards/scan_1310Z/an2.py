import json,datetime
R={x['condition_id']:x for x in json.load(open('rew.json'))}
D=json.load(open('raw.json')); toks,books=D['toks'],D['books']
now=datetime.datetime(2026,11,12,13,10,tzinfo=datetime.timezone.utc)
res=[]
for c,m in toks.items():
    b=books.get(m['tokens'][0]['token_id']);
    if not b: continue
    v=R[c]['rewards_max_spread']; S=R[c]['rewards_min_size']; rate=R[c]['total_daily_rate']
    end=m.get('end_date_iso')
    if not end: continue
    e=datetime.datetime.fromisoformat(end.replace('Z','+00:00'))
    if (e-now).days<3: continue
    bids=[(float(x['price']),float(x['size'])) for x in b['bids']]; asks=[(float(x['price']),float(x['size'])) for x in b['asks']]
    bq=[p for p,s in bids if s>=S]; aq=[p for p,s in asks if s>=S]
    if not bq or not aq: continue
    bb,ba=max(bq),min(aq); mid=(bb+ba)/2
    if not (0.12<=mid<=0.88): continue
    tick=float(b.get('tick_size',0.01))
    def q(lv):
        return sum(s*((v-abs(mid-p)*100)/v)**2 for p,s in lv if s>=S and abs(mid-p)*100<v)
    Q1,Q2=q(bids),q(asks); comp=max(min(Q1,Q2),max(Q1,Q2)/3)
    # we bid one tick below adjusted mid on YES only, but never cross raw best ask
    rawask=min(p for p,s in asks)
    p=min(round(int(mid/tick)*tick,4), rawask-tick)
    if p<=0: continue
    d=(mid-p)*100
    if d>=v: continue
    Qo=S*((v-d)/v)**2/3; day=rate*Qo/(Qo+comp); cost=S*p
    res.append(dict(q=m['question'][:75],slug=m.get('market_slug'),mid=round(mid,3),bid=p,rawbb=max(x for x,_ in bids),rawask=rawask,v=v,S=S,rate=rate,Q1=round(Q1),Q2=round(Q2),cost=round(cost,2),day=round(day,2),roi=round(day/cost,3),end=end[:10]))
res.sort(key=lambda r:-r['roi'])
json.dump(res,open('res2.json','w'))
print(len(res))
for r in res[:25]: print(r)
