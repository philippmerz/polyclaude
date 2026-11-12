import json,urllib.request,concurrent.futures as cf
H={"User-Agent":"Mozilla/5.0","Content-Type":"application/json"}
rew={x['condition_id']:x for x in json.load(open('rew.json')) if x['total_daily_rate']>=2}
# sampling markets for tokens
toks={};cur=""
while True:
    d=json.load(urllib.request.urlopen(urllib.request.Request(f"https://clob.polymarket.com/sampling-markets?next_cursor={cur}",headers=H),timeout=30))
    for m in d['data']:
        if m['condition_id'] in rew and m.get('accepting_orders') and len(m['tokens'])==2:
            toks[m['condition_id']]=m
    cur=d.get('next_cursor')
    if not cur or cur=="LTE=" or not d['data']: break
print('markets',len(toks))
cids=list(toks); books={}
def fetch(batch):
    body=json.dumps([{"token_id":toks[c]['tokens'][0]['token_id']} for c in batch]).encode()
    return json.load(urllib.request.urlopen(urllib.request.Request("https://clob.polymarket.com/books",data=body,headers=H),timeout=60))
batches=[cids[i:i+200] for i in range(0,len(cids),200)]
with cf.ThreadPoolExecutor(6) as ex:
    for res in ex.map(fetch,batches):
        for b in res: books[b['asset_id']]=b
json.dump({'toks':toks,'books':books},open('raw.json','w'))
print('books',len(books))
