import json,urllib.request
out=[];cur=""
while True:
    d=json.load(urllib.request.urlopen(urllib.request.Request(f"https://clob.polymarket.com/rewards/markets/current?next_cursor={cur}",headers={"User-Agent":"Mozilla/5.0"}),timeout=30))
    out+=d['data']; cur=d.get('next_cursor')
    if not cur or cur=="LTE=" or not d['data']: break
json.dump(out,open('rew.json','w'))
import collections
print(len(out)); r=[x['total_daily_rate'] for x in out]
print('sum daily',sum(r)); print(collections.Counter(r).most_common(12))
