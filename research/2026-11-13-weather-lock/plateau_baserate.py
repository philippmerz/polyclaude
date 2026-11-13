"""Base rate: after a flat afternoon plateau, how often does a station's daily max still rise (rounded bucket)?
Data: IEM ASOS archive (hourly routine METARs). Usage: python plateau_baserate.py WMKK 8  (station, UTC offset h)
Fetch: curl 'https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=WMKK&data=tmpc&year1=2023&month1=1&day1=1&year2=2026&month2=11&day2=13&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&report_type=3' -o wmkk.csv"""
import csv,collections,datetime as dt,sys
st=sys.argv[1]; off=int(sys.argv[2]); f=sys.argv[3] if len(sys.argv)>3 else f"{st.lower()}.csv"
rows=collections.defaultdict(list)
for r in csv.DictReader(open(f)):
    if r['tmpc']=='M':continue
    t=dt.datetime.strptime(r['valid'],'%Y-%m-%d %H:%M')+dt.timedelta(hours=off)
    rows[t.date()].append((t,float(r['tmpc'])))
def stats(ch,cm,flat_h,months=None):
    n=k=nall=kall=0
    for d,obs in rows.items():
        if months and d.month not in months:continue
        cut=dt.datetime(d.year,d.month,d.day,ch,cm)
        pre=[v for t,v in obs if t<=cut]; post=[v for t,v in obs if t>cut]
        if len(pre)<10 or not post:continue
        M=max(pre); rise=round(max(post))>round(M); nall+=1;kall+=rise
        fc=dt.datetime(d.year,d.month,d.day,flat_h,0)
        if max(v for t,v in obs if t<=fc)>=M and pre[-1]>=M: n+=1;k+=rise
    return dict(all_days=nall,all_rise=kall,plateau_days=n,plateau_rise=k)
for cut in [(15,30),(16,0)]:
    for m in [None,{10,11,12}]: print(st,cut,m,stats(*cut,13,m))
