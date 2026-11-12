"""Read our LP-reward earnings/percentages (L2 auth via clob_v2; prints no secrets)."""
import sys, json, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import httpx, clob_v2 as C
address, _ = C._load_wallet(); creds = C._load_creds()
ST = 0
day = datetime.datetime.utcnow().strftime("%Y-%m-%d")
for path, params in [("/rewards/user/percentages", {"signature_type": ST}), ("/rewards/user/total", {"date": day, "signature_type": ST}), ("/rewards/user/markets", {"date": day, "signature_type": ST})]:
    h = C._hmac_headers("GET", path, None, creds, address)
    r = httpx.get(f"{C.CLOB_HOST}{path}", params=params, headers=h, timeout=20)
    print(path, r.status_code, json.dumps(C._safe_json(r))[:1500])
