#!/usr/bin/env python3
"""Keyset-crawl gamma /markets for the OPEN universe (implication study 2026-07-15).
Adapted from research/listing_study_2026-07-15/crawl_keyset.py: closed=false, no date window,
server-side volume_num_min. Streams slim rows to jsonl; resumable via cursor checkpoint.

Usage: crawl_open.py --out /tmp/implication_study/open_universe.jsonl --min-volume 500
"""
import argparse, json, os, sys, time
import httpx

KEYSET = "https://gamma-api.polymarket.com/markets/keyset"


def slim(m):
    ev = (m.get("events") or [{}])[0]
    return {
        "id": m.get("id"), "q": m.get("question"), "slug": m.get("slug"),
        "conditionId": m.get("conditionId"),
        "endDate": m.get("endDate"), "startDate": m.get("startDate"),
        "closed": m.get("closed"), "active": m.get("active"),
        "acceptingOrders": m.get("acceptingOrders"),
        "enableOrderBook": m.get("enableOrderBook"),
        "outcomes": m.get("outcomes"), "outcomePrices": m.get("outcomePrices"),
        "clobTokenIds": m.get("clobTokenIds"),
        "volumeNum": m.get("volumeNum"), "vol24": m.get("volume24hr"),
        "liquidityNum": m.get("liquidityNum"),
        "umaStatuses": m.get("umaResolutionStatuses"),
        "negRisk": m.get("negRisk"),
        "takerBaseFee": m.get("takerBaseFee"),
        "spread": m.get("spread"), "bestBid": m.get("bestBid"), "bestAsk": m.get("bestAsk"),
        "event_slug": ev.get("slug"), "event_id": ev.get("id"),
        "event_title": ev.get("title"),
        "series": bool(ev.get("series")),
        "orderMinSize": m.get("orderMinSize"),
    }


def keep(m):
    # binary, orderable, live
    if not m.get("active") or m.get("closed"):
        return False
    if not m.get("enableOrderBook"):
        return False
    oc = m.get("outcomes")
    if isinstance(oc, str):
        try:
            oc = json.loads(oc)
        except Exception:
            return False
    if not (isinstance(oc, list) and len(oc) == 2):
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-volume", type=float, default=500)
    ap.add_argument("--max-pages", type=int, default=3000)
    args = ap.parse_args()

    ckpt = args.out + ".cursor"
    cursor = None
    if os.path.exists(ckpt):
        cursor = open(ckpt).read().strip() or None
        print("# resuming from checkpoint cursor", file=sys.stderr)

    base = {"limit": 100, "closed": "false", "volume_num_min": args.min_volume}

    n_rows = sum(1 for _ in open(args.out)) if (cursor and os.path.exists(args.out)) else 0
    mode = "a" if (cursor and n_rows) else "w"
    pages = 0
    n_seen = 0
    t_start = time.time()
    with httpx.Client(timeout=30) as client, open(args.out, mode) as f:
        retries = 0
        while pages < args.max_pages:
            p = dict(base)
            if cursor:
                p["after_cursor"] = cursor
            try:
                r = client.get(KEYSET, params=p)
                b = r.json() if r.status_code == 200 else None
            except Exception:
                b = None
            if not isinstance(b, dict) or "markets" not in b:
                retries += 1
                if retries > 8:
                    print(f"# giving up after {pages} pages, {n_rows} rows", file=sys.stderr)
                    break
                time.sleep(2.5 * retries)
                continue
            retries = 0
            mk = b["markets"]
            if not mk:
                print(f"# done: end of data at page {pages}", file=sys.stderr)
                break
            n_seen += len(mk)
            for m in mk:
                if keep(m):
                    f.write(json.dumps(slim(m)) + "\n")
                    n_rows += 1
            f.flush()
            cursor = b.get("next_cursor")
            with open(ckpt, "w") as cf:
                cf.write(cursor or "")
            pages += 1
            if pages % 25 == 0:
                rate = n_seen / max(time.time() - t_start, 1)
                print(f"# page {pages}, kept {n_rows}/{n_seen} seen, {rate:.0f} rows/s", file=sys.stderr)
            if not cursor:
                print(f"# done: no next_cursor at page {pages}", file=sys.stderr)
                break
            time.sleep(0.15)
    print(f"# TOTAL kept: {n_rows} of {n_seen} seen, pages: {pages} -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
