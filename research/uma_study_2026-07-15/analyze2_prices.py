#!/usr/bin/env python3
"""Dispute-window price study.
For each determinate disputed market (vol>=MINVOL), pull CLOB prices-history of the
PROPOSED-side token around [first_dispute - 6h, final + 2h]; compute entry stats.
Writes /tmp/uma_study/price_rows.json ; prints aggregate EV.
"""
import httpx, json, sys, time, statistics

MINVOL = 100_000
rows = json.load(open('/tmp/uma_study/study_rows.json'))
cands = [r for r in rows if r['stood'] is not None and r['volumeNum'] >= MINVOL
         and r['clobTokenIds'] and r['first_dispute_time'] and r['final_time']
         and r['prop_idx'] in (0, 1) and r['final_time'] > r['first_dispute_time']]
print(f"candidates: {len(cands)}", file=sys.stderr)

c = httpx.Client(timeout=30)
out = []
fails = 0
for i, r in enumerate(cands):
    tok = r['clobTokenIds'][r['prop_idx']]
    t_d = int(r['first_dispute_time'])
    t_f = int(r['final_time'])
    window_h = (t_f - t_d) / 3600
    fid = 1 if window_h <= 8 else (10 if window_h <= 100 else 60)
    params = {'market': tok, 'startTs': t_d - 6*3600, 'endTs': t_f + 3600, 'fidelity': fid}
    hist = None
    for attempt in range(3):
        try:
            resp = c.get('https://clob.polymarket.com/prices-history', params=params)
            if resp.status_code == 200:
                hist = resp.json().get('history', [])
                break
            time.sleep(1 + attempt)
        except Exception:
            time.sleep(1 + attempt)
    if hist is None:
        fails += 1
        continue
    pre = [h['p'] for h in hist if t_d - 6*3600 <= h['t'] < t_d]
    w1  = [h['p'] for h in hist if t_d <= h['t'] < t_d + 3600]
    w6  = [h['p'] for h in hist if t_d + 3600 <= h['t'] < t_d + 6*3600]
    wall= [h['p'] for h in hist if t_d <= h['t'] < t_f]
    entry30 = None  # first observation 15-60 min after dispute (realistic detection lag)
    for h in hist:
        if t_d + 900 <= h['t'] <= t_d + 3600:
            entry30 = h['p']; break
    if entry30 is None and w6:
        entry30 = w6[0]
    rec = dict(r)
    rec.update({
        'p_pre': statistics.mean(pre) if pre else None,
        'p_w1': statistics.mean(w1) if w1 else None,
        'p_w6': statistics.mean(w6) if w6 else None,
        'p_all_mean': statistics.mean(wall) if wall else None,
        'p_all_min': min(wall) if wall else None,
        'p_all_max': max(wall) if wall else None,
        'entry30': entry30,
        'n_pts_window': len(wall),
    })
    out.append(rec)
    if i % 50 == 0:
        print(f"  {i}/{len(cands)} pulled, fails={fails}", file=sys.stderr)
    time.sleep(0.08)

json.dump(out, open('/tmp/uma_study/price_rows.json', 'w'))
print(f"done: {len(out)} rows, {fails} fails", file=sys.stderr)

# aggregate
have = [r for r in out if r['entry30'] is not None]
print(f"\nrows with entry price 15-60min post-dispute: {len(have)}")
def agg(rs, label):
    if not rs: return
    n = len(rs)
    stood = sum(1 for r in rs if r['stood'])
    entries = [r['entry30'] for r in rs]
    rets = [ (1-r['entry30'])/r['entry30'] if r['stood'] else -1.0 for r in rs ]
    mean_ret = statistics.mean(rets)
    med_entry = statistics.median(entries)
    print(f"{label}: N={n} stood={stood/n*100:.0f}% med_entry={med_entry:.3f} mean_ret={mean_ret*100:+.1f}%")

agg(have, "ALL (buy proposed side @15-60min post-dispute)")
print()
for lo, hi in [(0,0.3),(0.3,0.5),(0.5,0.7),(0.7,0.85),(0.85,0.95),(0.95,1.01)]:
    agg([r for r in have if lo <= r['entry30'] < hi], f"  entry {lo:.2f}-{hi:.2f}")
print()
agg([r for r in have if r['prop_idx']==0], "YES-side proposals")
agg([r for r in have if r['prop_idx']==1], "NO-side proposals")
print()
agg([r for r in have if r['n_disputes']==1], "single dispute")
agg([r for r in have if r['n_disputes']>=2], "2+ disputes (DVM)")
