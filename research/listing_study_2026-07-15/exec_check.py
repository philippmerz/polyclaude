#!/usr/bin/env python3
"""Executability check: for mid-priced new listings (the miscalibrated zone),
what NO price did takers ACTUALLY get filled at in the first hours?

Sample: non-series paths rows with fresh T+6h mid in [0.25,0.75].
For each: gamma detail -> conditionId; data-api /trades paginated (newest first)
until we pass t0+48h or page cap; keep early-window trades.
Output: exec_trades.jsonl (resumable).
"""
import json, os, sys, time, argparse, random
import httpx

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", default="/tmp/listing_study/paths.jsonl")
    ap.add_argument("--out", default="/tmp/listing_study/exec_trades.jsonl")
    ap.add_argument("--sample", type=int, default=260)
    ap.add_argument("--page-cap", type=int, default=8)
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    done = set()
    if os.path.exists(args.out):
        for l in open(args.out):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass
        print(f"# resuming, {len(done)} done", file=sys.stderr)

    rows = []
    for l in open(args.paths):
        r = json.loads(l)
        if r.get("series") or r.get("no_hist"):
            continue
        if r["life_h"] < 120:
            continue
        a6 = r.get("ages", {}).get("6")
        if not a6:
            continue
        p6, stale = a6
        if not (0.25 <= p6 <= 0.75):
            continue
        rows.append(r)
    rng = random.Random(args.seed)
    if len(rows) > args.sample:
        rows = rng.sample(rows, args.sample)
    todo = [r for r in rows if r["id"] not in done]
    print(f"# candidates {len(rows)}, todo {len(todo)}", file=sys.stderr)

    with httpx.Client(timeout=25) as c, open(args.out, "a") as f:
        for i, r in enumerate(todo):
            out = {"id": r["id"], "q": r["q"], "t0": r["t0"], "out0_won": r["out0_won"],
                   "p6_mid": r["ages"]["6"][0], "vol": r["vol"], "life_h": r["life_h"]}
            try:
                g = c.get(f"https://gamma-api.polymarket.com/markets/{r['id']}").json()
                cid = g.get("conditionId")
            except Exception:
                cid = None
            if not cid:
                out["err"] = "no_cid"
                f.write(json.dumps(out) + "\n")
                f.flush()
                continue
            cutoff = r["t0"] + 48 * 3600
            early, n_total, reached = [], 0, False
            for pg in range(args.page_cap):
                try:
                    tr = c.get("https://data-api.polymarket.com/trades",
                               params={"market": cid, "limit": 500, "offset": pg * 500}).json()
                except Exception:
                    tr = None
                if not isinstance(tr, list) or not tr:
                    reached = True  # ran out of trades -> we saw them all
                    break
                n_total += len(tr)
                for t in tr:
                    if t.get("timestamp") and t["timestamp"] <= cutoff:
                        early.append({"ts": t["timestamp"], "side": t.get("side"),
                                      "outcome": t.get("outcome"), "p": float(t.get("price") or 0),
                                      "sz": float(t.get("size") or 0)})
                if tr[-1].get("timestamp", 0) <= r["t0"]:  # paged past listing time
                    reached = True
                    break
                if len(tr) < 500:
                    reached = True
                    break
                time.sleep(0.08)
            out["n_trades_total_seen"] = n_total
            out["complete_early_window"] = reached
            out["early_trades"] = sorted(early, key=lambda x: x["ts"])
            f.write(json.dumps(out) + "\n")
            f.flush()
            if (i + 1) % 25 == 0:
                print(f"# {i+1}/{len(todo)}", file=sys.stderr)
            time.sleep(0.08)
    print("# DONE", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
