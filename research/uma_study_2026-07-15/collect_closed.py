#!/usr/bin/env python3
"""Collect all closed Polymarket markets (endDate >= 2025-06-01) via gamma keyset pagination.
Writes slim JSONL to /tmp/uma_study/closed_markets.jsonl. Progress to stderr.
"""
import httpx, json, sys, time

OUT = "/tmp/uma_study/closed_markets.jsonl"
KEEP = ["id", "slug", "question", "conditionId", "closedTime", "endDate", "createdAt",
        "umaResolutionStatuses", "outcomePrices", "outcomes", "clobTokenIds",
        "volumeNum", "liquidityNum", "negRiskOther", "category"]

def main():
    c = httpx.Client(timeout=60)
    cursor = None
    n = 0
    pages = 0
    with open(OUT, "w") as f:
        while True:
            params = {"closed": "true", "limit": 100, "end_date_min": "2025-06-01"}
            if cursor:
                params["after_cursor"] = cursor
            for attempt in range(5):
                try:
                    r = c.get("https://gamma-api.polymarket.com/markets/keyset", params=params)
                    if r.status_code == 200:
                        break
                    time.sleep(2 * (attempt + 1))
                except Exception as e:
                    print(f"err {e}", file=sys.stderr)
                    time.sleep(2 * (attempt + 1))
            else:
                print("FAILED page, aborting", file=sys.stderr)
                break
            j = r.json()
            ms = j.get("markets", [])
            if not ms:
                print("done: empty page", file=sys.stderr)
                break
            for m in ms:
                rec = {k: m.get(k) for k in KEEP}
                f.write(json.dumps(rec) + "\n")
            n += len(ms)
            pages += 1
            cursor = j.get("next_cursor")
            if pages % 50 == 0:
                f.flush()
                print(f"pages={pages} n={n} last_id={ms[-1].get('id')} last_end={ms[-1].get('endDate')}", file=sys.stderr)
            if not cursor:
                print("done: no cursor", file=sys.stderr)
                break
    print(f"TOTAL {n} markets, {pages} pages", file=sys.stderr)

if __name__ == "__main__":
    main()
