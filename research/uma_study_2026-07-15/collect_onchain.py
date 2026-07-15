#!/usr/bin/env python3
"""Pull DisputePrice events from BOTH oracles Polymarket adapters use on Polygon
(OOv2 0xee3a... and managed OOv2 fork 0x2c03...), since 2025-06-01.
Decode, compute questionID candidates (raw keccak + initializer-suffix-stripped),
attach block timestamps. Writes /tmp/uma_study/disputes_onchain.json
"""
import httpx, json, sys, time
from eth_abi import decode as abi_decode
from eth_utils import keccak

ORACLES = {
    'oov2': '0xee3afe347d5c74317041e2618c49534daf887c24',
    'managed': '0x2c0367a9db231ddebd88a94b4f6461a6e47c58b1',
}
DISPUTE_T = '0x5165909c3d1c01c5d1e121ac6f6d01dda1ba24bc9e1f975b5a375339c15be7f3'
START_BLOCK = 72211746   # ~2025-06-01
HEAD = 90298675          # 2026-07-15
URLS = ['https://gateway.tenderly.co/public/polygon',
        'https://polygon.api.onfinality.io/public']

def rpc(method, params, timeout=120):
    last = None
    for url in URLS:
        for attempt in range(3):
            try:
                r = httpx.post(url, json={'jsonrpc':'2.0','id':1,'method':method,'params':params}, timeout=timeout)
                j = r.json()
                if 'result' in j:
                    return j['result']
                last = j.get('error')
                time.sleep(1+attempt)
            except Exception as e:
                last = str(e)
                time.sleep(1+attempt)
    raise RuntimeError(f"rpc failed: {last}")

def get_logs(addr, topic):
    def fetch(lo, hi):
        try:
            return rpc('eth_getLogs', [{'address': addr, 'topics': [topic],
                                        'fromBlock': hex(lo), 'toBlock': hex(hi)}])
        except RuntimeError:
            if hi - lo < 100_000:
                raise
            mid = (lo + hi) // 2
            return fetch(lo, mid) + fetch(mid+1, hi)
    return fetch(START_BLOCK, HEAD)

def main():
    disputes = []
    for oname, addr in ORACLES.items():
        print(f'fetching DisputePrice logs from {oname}...', file=sys.stderr)
        dlogs = get_logs(addr, DISPUTE_T)
        print(f'  {len(dlogs)} dispute events', file=sys.stderr)
        for lg in dlogs:
            ident, ts, anc, pp = abi_decode(['bytes32','uint256','bytes','int256'], bytes.fromhex(lg['data'][2:]))
            # strip ",initializer:<hex>" suffix the adapter appends before hitting the oracle
            stripped = anc
            marker = b',initializer:'
            if marker in anc:
                stripped = anc[:anc.rindex(marker)]
            try:
                anc_text = anc.decode('utf-8', errors='replace')
            except Exception:
                anc_text = ''
            disputes.append({
                'oracle': oname,
                'block': int(lg['blockNumber'],16),
                'tx': lg['transactionHash'],
                'requester': '0x'+lg['topics'][1][-40:],
                'proposer': '0x'+lg['topics'][2][-40:],
                'disputer': '0x'+lg['topics'][3][-40:],
                'identifier': ident.rstrip(b'\x00').decode('ascii', errors='replace'),
                'request_ts': ts,
                'qid_raw': '0x'+keccak(anc).hex(),
                'qid_stripped': '0x'+keccak(stripped).hex(),
                'proposed_price': str(pp),
                'anc_head': anc_text[:160],
            })

    blocks = sorted({d['block'] for d in disputes})
    print(f'fetching {len(blocks)} block timestamps...', file=sys.stderr)
    ts_map = {}
    B = 40
    for i in range(0, len(blocks), B):
        chunk = blocks[i:i+B]
        batch = [{'jsonrpc':'2.0','id':k,'method':'eth_getBlockByNumber','params':[hex(b), False]}
                 for k, b in enumerate(chunk)]
        done = False
        for url in URLS:
            try:
                r = httpx.post(url, json=batch, timeout=120)
                arr = r.json()
                if isinstance(arr, list):
                    for resp in arr:
                        res = resp.get('result')
                        if res:
                            ts_map[int(res['number'],16)] = int(res['timestamp'],16)
                    done = True
                    break
            except Exception:
                continue
        if not done:
            for b in chunk:
                try:
                    res = rpc('eth_getBlockByNumber',[hex(b),False])
                    ts_map[b] = int(res['timestamp'],16)
                except Exception:
                    pass
    for d in disputes:
        d['dispute_time'] = ts_map.get(d['block'])

    json.dump({'disputes': disputes}, open('/tmp/uma_study/disputes_onchain.json','w'))
    print(f'wrote {len(disputes)} disputes', file=sys.stderr)

if __name__ == '__main__':
    main()
