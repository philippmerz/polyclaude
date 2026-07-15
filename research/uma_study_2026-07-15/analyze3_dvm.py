#!/usr/bin/env python3
"""DVM-window study: for markets with >=2 disputes, entry when the SECOND dispute fires
(question now goes to DVM vote with certainty). Buy the RE-PROPOSED side (the second
disputed proposal) at price 15-60min after 2nd dispute; hold to resolution.
Note: second proposal may differ from first. stood_2nd = (final == 2nd proposal).
"""
import httpx, json, sys, time, statistics, math

dm = {m['market_id']: m for m in json.load(open('/tmp/uma_study/disputed_markets.json'))['markets']}
rows = json.load(open('/tmp/uma_study/study_rows.json'))
cands = []
for r in rows:
    if not (r['closed'] and r['final_idx'] is not None and r['volumeNum'] >= 100_000):
        continue
    m = dm.get(r['market_id'])
    if not m or len(m['disputes']) < 2:
        continue
    d2 = m['disputes'][1]
    v = int(d2['proposed_price'])
    if v == 10**18: p2_idx = 0
    elif v == 0: p2_idx = 1
    else: continue
    if not r['clobTokenIds'] or not d2.get('dispute_time') or not r['final_time']:
        continue
    if r['final_time'] <= d2['dispute_time']:
        continue
    cands.append((r, d2, p2_idx))
print(f"2nd-dispute candidates: {len(cands)}", file=sys.stderr)

c = httpx.Client(timeout=30)
out = []
for i, (r, d2, p2_idx) in enumerate(cands):
    tok = r['clobTokenIds'][p2_idx]
    t_d = int(d2['dispute_time']); t_f = int(r['final_time'])
    fid = 10 if (t_f - t_d) / 3600 <= 100 else 60
    try:
        resp = c.get('https://clob.polymarket.com/prices-history',
                     params={'market': tok, 'startTs': t_d - 3600, 'endTs': min(t_f + 3600, t_d + 30*86400), 'fidelity': fid})
        hist = resp.json().get('history', [])
    except Exception:
        continue
    entry = None
    for h in hist:
        if t_d + 900 <= h['t'] <= t_d + 7200:
            entry = h['p']; break
    if entry is None:
        continue
    stood2 = (r['final_idx'] == p2_idx)
    out.append({'market_id': r['market_id'], 'q': r['question'], 'vol': r['volumeNum'],
                'entry': entry, 'stood2': stood2, 'hold_h': (t_f - t_d)/3600,
                'first_prop_idx': r['prop_idx'], 'p2_idx': p2_idx})
    if i % 40 == 0:
        print(f"  {i}/{len(cands)}", file=sys.stderr)
    time.sleep(0.08)

json.dump(out, open('/tmp/uma_study/dvm_rows.json', 'w'))
def agg(rs, label):
    if not rs:
        print(f"{label}: N=0"); return
    n = len(rs); s = sum(1 for x in rs if x['stood2'])
    rets = [(1-x['entry'])/x['entry'] if x['stood2'] else -1.0 for x in rs]
    m = statistics.mean(rets); se = statistics.stdev(rets)/math.sqrt(n) if n > 1 else 0
    print(f"{label}: N={n} stood2={s/n*100:.0f}% med_entry={statistics.median(x['entry'] for x in rs):.3f} "
          f"mean_ret={m*100:+.1f}% (SE {se*100:.1f}) med_hold={statistics.median(x['hold_h'] for x in rs):.0f}h")

print(f"\nBUY 2nd-PROPOSED SIDE at 2nd dispute +15-120min:")
agg(out, "ALL")
for lo, hi in [(0, 0.3), (0.3, 0.7), (0.7, 0.95), (0.95, 1.01)]:
    agg([x for x in out if lo <= x['entry'] < hi], f"  entry {lo}-{hi}")
agg([x for x in out if x['p2_idx'] == x['first_prop_idx']], "  2nd prop SAME as 1st")
agg([x for x in out if x['p2_idx'] != x['first_prop_idx']], "  2nd prop FLIPPED from 1st")
agg([x for x in out if x['vol'] >= 1e6], "  vol>=1M")
