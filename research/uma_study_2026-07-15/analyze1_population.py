#!/usr/bin/env python3
"""Population analysis v2 (index-based outcome mapping).
p2=1e18 -> outcomes[0] ; p1=0 -> outcomes[1] ; 0.5e18 -> HALF. Verified on-chain (4/4 anc texts).
Writes /tmp/uma_study/study_rows.json
"""
import json, datetime, statistics
from collections import Counter

j = json.load(open('/tmp/uma_study/disputed_markets.json'))
ms = [m for m in j['markets'] if m['disputes']]

def parse_json(p):
    if p is None: return None
    try:
        return json.loads(p) if isinstance(p, str) else p
    except Exception:
        return None

def parse_time(s):
    if not s: return None
    s = s.replace('+00', '+00:00').replace('Z', '+00:00')
    try:
        return datetime.datetime.fromisoformat(s).timestamp()
    except Exception:
        return None

rows = []
for m in ms:
    prices = parse_json(m['outcomePrices'])
    outs = parse_json(m['outcomes'])
    toks = parse_json(m['clobTokenIds'])
    first = m['disputes'][0]
    v = int(first['proposed_price'])
    if v == 10**18: prop_idx = 0
    elif v == 0: prop_idx = 1
    elif v == 5*10**17: prop_idx = -1  # HALF
    else: prop_idx = None
    final_idx = None
    if m['closed'] and prices and len(prices) == 2:
        p0, p1 = float(prices[0]), float(prices[1])
        if p0 > 0.99: final_idx = 0
        elif p1 > 0.99: final_idx = 1
        elif abs(p0-0.5) < 0.01 and abs(p1-0.5) < 0.01: final_idx = -1
    stood = None
    if prop_idx is not None and final_idx is not None:
        stood = (prop_idx == final_idx)
    ct = parse_time(m.get('closedTime')) or parse_time(m.get('umaEndDate'))
    dt = first.get('dispute_time')
    rows.append({
        'market_id': m['market_id'], 'slug': m['slug'], 'question': m['question'],
        'closed': m['closed'], 'volumeNum': m.get('volumeNum') or 0,
        'negRisk': m.get('negRisk'), 'resolvedBy': m.get('resolvedBy'),
        'n_disputes': len(m['disputes']),
        'first_dispute_time': dt, 'final_time': ct,
        'prop_idx': prop_idx, 'final_idx': final_idx, 'stood': stood,
        'hours_to_final': (ct - dt)/3600 if (ct and dt and ct > dt) else None,
        'clobTokenIds': toks, 'outcomes': outs, 'outcomePrices': prices,
    })

det = [r for r in rows if r['stood'] is not None]
print(f"disputed markets matched: {len(rows)} | closed: {sum(1 for r in rows if r['closed'])} | open: {sum(1 for r in rows if not r['closed'])}")
print(f"determinate (proposal+final known): {len(det)}")
nz = [r for r in rows if r['closed'] and r['stood'] is None]
print(f"closed but indeterminate: {len(nz)}  (why: prop HALF/other or final not 0/1/half)")
print()
stood_n = sum(1 for r in det if r['stood'])
print(f"PROPOSAL STOOD (first disputed proposal == final): {stood_n}/{len(det)} = {stood_n/len(det)*100:.1f}%")
import math
p = stood_n/len(det); se = math.sqrt(p*(1-p)/len(det))
print(f"  95% CI: [{(p-1.96*se)*100:.1f}%, {(p+1.96*se)*100:.1f}%]")
print()
for nd, lab in [(1,'1'),(2,'2'),(3,'3'),(4,'>=4')]:
    sub = [r for r in det if (r['n_disputes'] == nd if nd < 4 else r['n_disputes'] >= 4)]
    if sub:
        s = sum(1 for r in sub if r['stood'])
        hs = [r['hours_to_final'] for r in sub if r['hours_to_final']]
        print(f"  n_disputes={lab}: stood {s}/{len(sub)} = {s/len(sub)*100:.1f}%   med hours→final {statistics.median(hs):.1f}" if hs else f"  n_disputes={lab}: stood {s}/{len(sub)}")
print()
for lo, hi, lab in [(0,1e4,'<10k'),(1e4,1e5,'10k-100k'),(1e5,1e6,'100k-1M'),(1e6,1e12,'>1M')]:
    sub = [r for r in det if lo <= r['volumeNum'] < hi]
    if sub:
        s = sum(1 for r in sub if r['stood'])
        print(f"  vol {lab}: stood {s}/{len(sub)} = {s/len(sub)*100:.1f}%  (N={len(sub)})")
print()
# proposed-side direction: does YES-proposal vs NO-proposal matter?
for pi, lab in [(0,'proposal=outcome0 (YES-side)'), (1,'proposal=outcome1 (NO-side)')]:
    sub = [r for r in det if r['prop_idx'] == pi]
    if sub:
        s = sum(1 for r in sub if r['stood'])
        print(f"  {lab}: stood {s}/{len(sub)} = {s/len(sub)*100:.1f}%")
half_prop = [r for r in rows if r['prop_idx'] == -1 and r['final_idx'] is not None]
if half_prop:
    s = sum(1 for r in half_prop if r['final_idx'] == -1)
    print(f"  proposal=HALF: stood {s}/{len(half_prop)}")
print()
# sports vs non-sports proxy: resolver adapter
for rb, lab in Counter(r['resolvedBy'] for r in det).most_common():
    sub = [r for r in det if r['resolvedBy'] == rb]
    s = sum(1 for r in sub if r['stood'])
    medv = statistics.median(r['volumeNum'] for r in sub)
    print(f"  resolver {rb[:10]}: stood {s}/{len(sub)} = {s/len(sub)*100:.1f}%  medvol ${medv:,.0f}")
print()
hs = sorted(r['hours_to_final'] for r in det if r['hours_to_final'])
print(f"hours dispute→final: median {statistics.median(hs):.1f}, mean {statistics.mean(hs):.1f}, p10 {hs[int(len(hs)*.1)]:.1f}, p90 {hs[int(len(hs)*.9)]:.1f}, max {max(hs):.0f}")
# catch rate by month
months = Counter(datetime.datetime.utcfromtimestamp(r['first_dispute_time']).strftime('%Y-%m') for r in rows if r['first_dispute_time'])
print("\ndisputed markets per month:")
for mth in sorted(months):
    hv = sum(1 for r in rows if r['first_dispute_time'] and datetime.datetime.utcfromtimestamp(r['first_dispute_time']).strftime('%Y-%m')==mth and r['volumeNum']>=1e5)
    print(f"  {mth}: {months[mth]:4d}  (vol>=100k: {hv})")

json.dump(rows, open('/tmp/uma_study/study_rows.json','w'))
print('\nwrote study_rows.json')
