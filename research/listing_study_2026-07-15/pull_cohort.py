#!/usr/bin/env python3
"""Pull the listing cohort (markets whose startDate falls in a window) from gamma.

Two outputs:
  cohort_meta.jsonl   — resolved, binary, decisive, vol-floored members (for path study)
  census_all.jsonl    — EVERY market in a subwindow, no filters (survivorship denominators)

Resumable: skips work if output exists and --force not given.
"""
import argparse, ast, json, os, sys, time
import httpx

GAMMA = "https://gamma-api.polymarket.com/markets"


def parse(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else x
    except Exception:
        return None


def fetch_window(client, params_extra, max_pages=400, label=""):
    out, offset, retries = [], 0, 0
    while offset < max_pages * 100:
        p = {"limit": 100, "offset": offset, "order": "startDate", "ascending": "true"}
        p.update(params_extra)
        try:
            r = client.get(GAMMA, params=p, timeout=30).json()
        except Exception:
            r = None
        if not isinstance(r, list):
            retries += 1
            if retries > 6:
                print(f"# {label} giving up at offset {offset}", file=sys.stderr)
                break
            time.sleep(2.0)
            continue
        retries = 0
        if not r:
            break
        out.extend(m for m in r if isinstance(m, dict))
        offset += 100
        if offset % 1000 == 0:
            print(f"# {label} offset {offset}, have {len(out)}", file=sys.stderr)
        time.sleep(0.12)
    return out


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
        "negRisk": m.get("negRisk"),
        "series": bool(ev.get("series")), "event_title": ev.get("title"),
        "spread": m.get("spread"), "bestBid": m.get("bestBid"), "bestAsk": m.get("bestAsk"),
        "feesEnabled": m.get("feesEnabled"), "orderMinSize": m.get("orderMinSize"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort-start", default="2026-04-01T00:00:00Z")
    ap.add_argument("--cohort-end", default="2026-06-01T00:00:00Z")
    ap.add_argument("--census-start", default="2026-04-01T00:00:00Z")
    ap.add_argument("--census-end", default="2026-04-08T00:00:00Z")
    ap.add_argument("--min-volume", type=float, default=1000)
    ap.add_argument("--outdir", default="/tmp/listing_study")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    cohort_path = os.path.join(args.outdir, "cohort_meta.jsonl")
    census_path = os.path.join(args.outdir, "census_all.jsonl")

    with httpx.Client() as client:
        # --- census: everything in a one-week subwindow, no filters ---
        if args.force or not os.path.exists(census_path):
            allm = fetch_window(client, {
                "start_date_min": args.census_start, "start_date_max": args.census_end,
            }, label="census")
            with open(census_path, "w") as f:
                for m in allm:
                    f.write(json.dumps(slim(m)) + "\n")
            print(f"# census: {len(allm)} markets -> {census_path}", file=sys.stderr)
        else:
            print(f"# census exists, skipping", file=sys.stderr)

        # --- cohort: resolved binary decisive, volume-floored, whole window ---
        if args.force or not os.path.exists(cohort_path):
            closed = fetch_window(client, {
                "start_date_min": args.cohort_start, "start_date_max": args.cohort_end,
                "closed": "true", "volume_num_min": args.min_volume,
            }, label="cohort")
            kept, drop = [], {"not_binary": 0, "not_resolved": 0, "not_decisive": 0,
                              "no_tokens": 0, "no_times": 0}
            for m in closed:
                oc, op = parse(m.get("outcomes")), parse(m.get("outcomePrices"))
                if oc != ["Yes", "No"] or not op:
                    drop["not_binary"] += 1
                    continue
                if m.get("umaResolutionStatus") != "resolved":
                    drop["not_resolved"] += 1
                    continue
                try:
                    p0 = float(op[0])
                except Exception:
                    drop["not_decisive"] += 1
                    continue
                if p0 not in (0.0, 1.0):
                    drop["not_decisive"] += 1
                    continue
                toks = parse(m.get("clobTokenIds"))
                if not toks:
                    drop["no_tokens"] += 1
                    continue
                if not (m.get("acceptingOrdersTimestamp") or m.get("createdAt")) or not m.get("closedTime"):
                    drop["no_times"] += 1
                    continue
                s = slim(m)
                s["yes_won"] = (p0 == 1.0)
                s["yes_tok"] = toks[0]
                kept.append(s)
            with open(cohort_path, "w") as f:
                for m in kept:
                    f.write(json.dumps(m) + "\n")
            print(f"# cohort: {len(closed)} closed vol>={args.min_volume:.0f}; kept {len(kept)} "
                  f"binary-decisive; drops {drop} -> {cohort_path}", file=sys.stderr)
        else:
            print(f"# cohort exists, skipping", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
