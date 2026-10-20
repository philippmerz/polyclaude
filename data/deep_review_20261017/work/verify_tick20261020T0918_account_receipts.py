#!/usr/bin/env python3
"""Verify receipt/body hashes listed in tick20261020T0918_account_receipt_index.json."""
import gzip, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
INDEX = ROOT / 'data/deep_review_20261017/work/tick20261020T0918_account_receipt_index.json'
doc = json.loads(INDEX.read_text())
checks = []
for item in doc['successful_pairs']:
    receipt = json.loads((ROOT / item['receipt']).read_text())
    body_path = ROOT / item['body']
    raw = gzip.decompress(body_path.read_bytes())
    checks.append((item['receipt'],
        hashlib.sha256(raw).hexdigest() == receipt['raw_sha256'] == item['raw_sha256'],
        hashlib.sha256(body_path.read_bytes()).hexdigest() == receipt['gzip_sha256'] == item['gzip_sha256']))
failed = [x for x in checks if not all(x[1:])]
print(json.dumps({'pairs': len(checks), 'raw_and_gzip_hashes_valid': not failed,
                  'failures': [x[0] for x in failed]}, indent=2))
raise SystemExit(bool(failed))
