#!/usr/bin/env python3
"""Keyset-crawl gamma /markets for the listing cohort. Resumable via cursor checkpoint.

Usage: crawl_keyset.py --out cohort_meta2.jsonl [--closed true] [--min-volume 1000]
                       [--start 2026-04-01T00:00:00Z] [--end 2026-06-01T00:00:00Z]
                       [--max-pages 2000]
Writes ALL rows slim (series flagged). Filtering to decisive 2-outcome happens later.
"""
import argparse, ast, json, os, sys, time
import httpx

KEYSET = "https://gamma-api.polymarket.com/markets/keyset"


def parse(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else x
    except Exception:
        return None


def slim(m):
    ev = (m.get("events") or [{}])[0]
    return {
        "id": m.get("id"), "q": m.get("question"), "slug": m.get("slug"),
        "createdAt": m.get("createdAt"), "startDate": m.get("startDate"),
        "acceptingOrdersTimestamp": m.get("acceptingOrdersTimestamp"),
        "endDate": m.get("endDate"), "closedTime": m.get("closedTime"),
        "closed": m.get("closed"), "active": m.get("active"),
        "outcomes": m.get("outcomes"), "outcomePrices": m.get("outcomePrices"),
        "clobTokenIds": m.get("clobTokenIds"),
        "volumeNum": m.get("volumeNum"), "liquidityNum": m.get("liquidityNum"),
        "umaResolutionStatus": m.get("umaResolutionStatus"),
        "negRisk": m.get("negRisk"), "enableOrderBook": m.get("enableOrderBook"),
        "series": bool(ev.get("series")), "series_slug": (ev.get("series") or [{}])[0].get("slug") if isinstance(ev.get("series"), list) else None,
        "event_title": ev.get("title"),
        "spread": m.get("spread"), "bestBid": m.get("bestBid"), "bestAsk": m.get("bestAsk"),
        "feesEnabled": m.get("feesEnabled"), "orderMinSize": m.get("orderMinSize"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--closed", default="true")
    ap.add_argument("--min-volume", type=float, default=None)
    ap.add_argument("--start", default="2026-04-01T00:00:00Z")
    ap.add_argument("--end", default="2026-06-01T00:00:00Z")
    ap.add_argument("--max-pages", type=int, default=2000)
    args = ap.parse_args()

    ckpt = args.out + ".cursor"
    cursor = None
    if os.path.exists(ckpt):
        cursor = open(ckpt).read().strip() or None
        print(f"# resuming from checkpoint cursor", file=sys.stderr)

    base = {"limit": 100, "start_date_min": args.start, "start_date_max": args.end}
    if args.closed in ("true", "false"):
        base["closed"] = args.closed
    if args.min_volume is not None:
        base["volume_num_min"] = args.min_volume

    n_rows = sum(1 for _ in open(args.out)) if os.path.exists(ckpt) and os.path.exists(args.out) else 0
    mode = "a" if (cursor and n_rows) else "w"
    pages = 0
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
                time.sleep(2.5)
                continue
            retries = 0
            mk = b["markets"]
            if not mk:
                print(f"# done: end of data at page {pages}", file=sys.stderr)
                break
            for m in mk:
                f.write(json.dumps(slim(m)) + "\n")
                n_rows += 1
            f.flush()
            cursor = b.get("next_cursor")
            with open(ckpt, "w") as cf:
                cf.write(cursor or "")
            pages += 1
            if pages % 25 == 0:
                rate = n_rows / max(time.time() - t_start, 1)
                print(f"# page {pages}, rows {n_rows}, {rate:.0f} rows/s", file=sys.stderr)
            if not cursor:
                print(f"# done: no next_cursor at page {pages}", file=sys.stderr)
                break
            time.sleep(0.12)
    print(f"# TOTAL rows: {n_rows} pages: {pages} -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
