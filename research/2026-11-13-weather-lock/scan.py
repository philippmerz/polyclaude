"""Dead-bucket scan for PM daily temperature events (METAR-resolved). Observed running extreme on the station's
local date rules out buckets; edge = NO ask on a dead bucket well below 1, or YES ask on the only-live bucket."""
import httpx,json,re,datetime as dt,sys
from zoneinfo import ZoneInfo
from timezonefinder import TimezoneFinder
TF=TimezoneFinder(); C=httpx.Client(timeout=20)
date=sys.argv[1] if len(sys.argv)>1 else "2026-11-13"
D=dt.date.fromisoformat(date); mon=D.strftime("%B").lower()
evs=C.get("https://gamma-api.polymarket.com/events",params={"tag_slug":"weather","closed":"false","limit":300,"end_date_min":f"{date}T00:00:00Z","end_date_max":f"{date}T23:00:00Z"}).json()
def temp(raw):
    if raw.startswith("SPECI"): return None
    m=re.search(r"\sT([01])(\d{3})[01]\d{3}",raw)
    if m: return (-1 if m.group(1)=="1" else 1)*int(m.group(2))/10
    m=re.search(r"\s(M?\d{2})/(M?\d{2})?\s",raw)
    if m: v=m.group(1); return -int(v[1:]) if v.startswith("M") else int(v)
def rnd(x): import math; return math.floor(x+0.5)
def bucket(title):
    t=title.replace("°C","").replace("°F","").strip()
    if "or below" in t: return (-999,int(t.split()[0]))
    if "or higher" in t or "or above" in t: return (int(t.split()[0]),999)
    if "-" in t[1:]: a,b=t.rsplit("-",1); return (int(a),int(b))
    return (int(t),int(t))
rows=[]
for e in evs:
    s=e['slug']
    if f"{mon}-{D.day}-" not in s or "temperature" not in s: continue
    desc=e['markets'][0]['description']; m=re.search(r"metar\?ids=([A-Z0-9]{4})",desc)
    if not m: continue
    st=m.group(1); fahr="°F" in e['markets'][0].get('groupItemTitle','')
    obs=C.get("https://aviationweather.gov/api/data/metar",params={"ids":st,"format":"json","hours":36}).json()
    if not obs: continue
    tz=ZoneInfo(TF.timezone_at(lat=obs[0]['lat'],lng=obs[0]['lon']))
    now_local=dt.datetime.now(tz)
    vals=[]
    for o in obs:
        t=dt.datetime.fromtimestamp(o['obsTime'],dt.UTC).astimezone(tz)
        if t.date()!=D: continue
        v=temp(o['rawOb']);
        if v is None: continue
        if fahr: v=v*9/5+32
        vals.append(v)
    if not vals: continue
    hi="highest" in s; ext=rnd(max(vals) if hi else min(vals))
    for mk in e['markets']:
        lo,up=bucket(mk['groupItemTitle'])
        dead = (up<ext) if hi else (lo>ext)
        rows.append(dict(ev=s,st=st,local=now_local.strftime("%H:%M"),ext=ext,b=mk['groupItemTitle'],dead=dead,bid=mk.get('bestBid'),ask=mk.get('bestAsk'),last=mk.get('lastTradePrice')))
json.dump(rows,open(f"rows_{date}.json","w"),indent=0)
# Report: dead buckets whose YES still bids >=0.02 (=> NO ask <=0.98)
for r in rows:
    if r['dead'] and (r['bid'] or 0)>=0.02: print("DEAD-YES-BID",r)
print("events",len({r['ev'] for r in rows}),"rows",len(rows),"dead",sum(r['dead'] for r in rows))
