#!/usr/bin/env python3
"""Join on-chain dispute events to gamma markets via question_ids (both hash variants).
Writes /tmp/uma_study/disputed_markets.json : one record per MARKET with dispute list + market meta.
"""
import httpx, json, sys, time

def main():
    d = json.load(open('/tmp/uma_study/disputes_onchain.json'))['disputes']
    # candidate qid -> dispute events
    by_qid = {}
    for x in d:
        for q in {x['qid_raw'], x['qid_stripped']}:
            by_qid.setdefault(q, []).append(x)
    qids = sorted(by_qid)
    print(f'{len(d)} dispute events, {len(qids)} candidate qids', file=sys.stderr)

    c = httpx.Client(timeout=60)
    markets = {}
    B = 50
    for i in range(0, len(qids), B):
        chunk = qids[i:i+B]
        got = []
        for closed_flag in ('true', 'false'):
            params = [('question_ids', q) for q in chunk] + [('limit', 100), ('closed', closed_flag)]
            for attempt in range(4):
                try:
                    r = c.get('https://gamma-api.polymarket.com/markets', params=params)
                    if r.status_code == 200:
                        got.extend(r.json())
                        break
                except Exception:
                    pass
                time.sleep(2*(attempt+1))
            else:
                print(f'batch {i} closed={closed_flag} FAILED', file=sys.stderr)
        for m in got:
            qid = (m.get('questionID') or '').lower()
            key = qid or (m.get('negRiskRequestID') or '').lower()
            if key in markets:
                continue
            markets[key] = {
                'market_id': m.get('id'),
                'slug': m.get('slug'),
                'question': m.get('question'),
                'questionID': qid,
                'conditionId': m.get('conditionId'),
                'closed': m.get('closed'),
                'closedTime': m.get('closedTime'),
                'endDate': m.get('endDate'),
                'umaEndDate': m.get('umaEndDate'),
                'umaResolutionStatus': m.get('umaResolutionStatus'),
                'umaResolutionStatuses': m.get('umaResolutionStatuses'),
                'outcomes': m.get('outcomes'),
                'outcomePrices': m.get('outcomePrices'),
                'clobTokenIds': m.get('clobTokenIds'),
                'volumeNum': m.get('volumeNum'),
                'liquidityNum': m.get('liquidityNum'),
                'resolvedBy': m.get('resolvedBy'),
                'negRisk': m.get('negRisk'),
                'negRiskRequestID': (m.get('negRiskRequestID') or '').lower(),
                'umaBond': m.get('umaBond'),
                'customLiveness': m.get('customLiveness'),
            }
        if (i//B) % 10 == 0:
            print(f'  {i}/{len(qids)} qids, {len(markets)} markets matched', file=sys.stderr)
        time.sleep(0.15)

    # attach dispute events to matched markets
    out = []
    matched_event_ids = set()
    for qid, meta in markets.items():
        evs = by_qid.get((meta.get('questionID') or '').lower(), []) + \
              [e for e in by_qid.get(meta.get('negRiskRequestID') or '', [])
               if e not in by_qid.get((meta.get('questionID') or '').lower(), [])]
        evs_sorted = sorted(evs, key=lambda e: e['block'])
        for e in evs_sorted:
            matched_event_ids.add(e['tx'] + str(e['block']))
        meta['disputes'] = [{k: e[k] for k in
                             ('oracle','block','tx','requester','proposer','disputer',
                              'request_ts','proposed_price','dispute_time')} for e in evs_sorted]
        out.append(meta)

    unmatched = [x for x in d if (x['tx']+str(x['block'])) not in matched_event_ids]
    json.dump({'markets': out, 'unmatched_events': unmatched},
              open('/tmp/uma_study/disputed_markets.json','w'))
    print(f'matched {len(out)} markets covering {len(d)-len(unmatched)} events; {len(unmatched)} events unmatched', file=sys.stderr)

if __name__ == '__main__':
    main()
