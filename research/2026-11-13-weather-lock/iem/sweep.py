"""Plateau base-rate sweep across PM weather stations (IEM hourly routine METARs 2023-01..2026-11-13).
Plateau = local-day max already reached by 13:00 local and latest obs at/after cut equals it.
Rise = rounded post-cut max > rounded pre-cut max. Offsets are fixed standard-time (Q4 approx)."""
import csv,collections,datetime as dt,sys,os
def load(st,off):
    rows=collections.defaultdict(list)
    for r in csv.DictReader(open(f"{st.lower()}.csv")):
        if r.get('tmpc') in (None,'M'):continue
        t=dt.datetime.strptime(r['valid'],'%Y-%m-%d %H:%M')+dt.timedelta(hours=off)
        rows[t.date()].append((t,float(r['tmpc'])))
    return rows
def stats(rows,ch,months):
    n=k=nall=kall=0
    for d,obs in rows.items():
        if months and d.month not in months:continue
        cut=dt.datetime(d.year,d.month,d.day,ch,10)
        pre=[v for t,v in obs if t<=cut]; post=[v for t,v in obs if t>cut]
        if len(pre)<10 or not post:continue
        M=max(pre); rise=round(max(post))>round(M); nall+=1;kall+=rise
        fc=dt.datetime(d.year,d.month,d.day,13,10)
        if max(v for t,v in obs if t<=fc)>=M and round(pre[-1])>=round(M): n+=1;k+=rise
    return nall,kall,n,k
print("st  | cut | Q4 all rise | Q4 plateau rise | all-yr plateau rise")
for line in open('stations.txt'):
    st,off=line.split(); off=int(off)
    if not os.path.exists(f"{st.lower()}.csv") or os.path.getsize(f"{st.lower()}.csv")<1000: continue
    rows=load(st,off)
    for ch in (14,15,16):
        a,b,c,d=stats(rows,ch,{10,11,12}); _,_,e,f=stats(rows,ch,None)
        print(f"{st} | {ch}:00 | {b}/{a} ({100*b/max(a,1):.0f}%) | {d}/{c} ({100*d/max(c,1):.1f}%) | {f}/{e} ({100*f/max(e,1):.1f}%)")
