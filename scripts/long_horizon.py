"""Filter the latest snapshot for markets with resolution between min_days and max_days,
sorted by liquidity. Useful for finding longer-horizon, research-driven candidates.
"""

import argparse
import json
from pathlib import Path

SNAP = Path("<PROJECT>/data/snapshots/shortlist_latest.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-days", type=float, default=45)
    ap.add_argument("--max-days", type=float, default=365)
    ap.add_argument("--top", type=int, default=60)
    ap.add_argument("--exclude-categories", default="sports")
    args = ap.parse_args()

    rows = json.loads(SNAP.read_text())
    excl = {c.strip() for c in args.exclude_categories.split(",") if c.strip()}
    rows = [
        r for r in rows
        if args.min_days <= r["days_to_resolve"] <= args.max_days
        and r["category"] not in excl
    ]
    rows.sort(key=lambda r: -r["liquidity"])

    by_cat: dict[str, list[dict]] = {}
    for r in rows[: args.top]:
        by_cat.setdefault(r["category"], []).append(r)
    for cat in sorted(by_cat, key=lambda k: -sum(r["liquidity"] for r in by_cat[k])):
        bucket = by_cat[cat]
        print(f"\n=== {cat} ({len(bucket)} mkts, total liq ${sum(r['liquidity'] for r in bucket):,.0f}) ===")
        for r in bucket:
            yp = f"{r['yes_price']:.3f}" if r["yes_price"] is not None else "  -  "
            print(f"  yes={yp}  spd={r['spread']:.3f}  liq={r['liquidity']:>9.0f}  v24={r['vol24h']:>8.0f}  d={r['days_to_resolve']:>6.1f}  {r['question'][:90]}")


if __name__ == "__main__":
    main()
