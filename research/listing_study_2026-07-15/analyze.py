#!/usr/bin/env python3
"""Analyze new-listing price paths: calibration by age, drift, divergence, returns.

Input: paths.jsonl from fetch_paths.py
All prices are for outcome0 token; out0_won is the resolution.
"""
import json, math, sys, argparse
import numpy as np
from collections import defaultdict

AGES = ["1", "6", "24", "72"]
ALL_AGES = ["0.25", "0.5", "1", "2", "3", "6", "12", "24", "48", "72", "96"]
BINS = [(0.0, 0.1), (0.1, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.01)]
STALE_CAP_H = {"0.25": 1.5, "0.5": 2, "1": 3, "2": 6, "3": 9, "6": 12, "12": 18,
               "24": 24, "48": 36, "72": 48, "96": 48}  # max staleness (h) to accept a price


def load(fn, min_life_h=None, families=None, require_fresh=True):
    rows = []
    for l in open(fn):
        r = json.loads(l)
        if r.get("no_hist"):
            rows.append(r)
            continue
        rows.append(r)
    return rows


def family(r):
    q = (r.get("q") or "").lower()
    et = (r.get("event_title") or "").lower()
    s = q + " " + et
    if r.get("series"):
        return "series"
    if any(k in s for k in ["election", "president", "senate", "governor", "mayor", "nominee",
                            "minister", "parliament", "impeach", "coup", "ceasefire", "capture",
                            "russia", "ukraine", "iran", "israel", "tariff", "strait", "sanction"]):
        return "politics/geo"
    if any(k in s for k in ["bitcoin", "ethereum", "solana", "xrp", "btc", "eth", "crypto",
                            "token", "coinbase", "all time high", "market cap", "price of"]):
        return "crypto"
    if any(k in s for k in ["win", "champion", "playoff", "cup", "league", "tournament", "mvp",
                            "finals", "medal", "open", "grand slam", "relegat"]):
        return "sports/esports-futures"
    if any(k in s for k in ["emmy", "oscar", "grammy", "box office", "album", "movie", "trailer",
                            "season", "bachelor", "big brother", "say", "tweet", "mention"]):
        return "entertainment/mentions"
    return "other"


def get_px(r, age, require_fresh=True):
    a = r.get("ages", {}).get(age)
    if not a:
        return None
    p, stale = a
    if require_fresh and stale > STALE_CAP_H.get(age, 24) * 3600:
        return None
    return p


def calib_table(pairs, label):
    """pairs: list of (price_of_outcome0, out0_won). Prints table, returns (ece, brier, n)."""
    n = len(pairs)
    if n == 0:
        print(f"  {label}: N=0")
        return None
    briers = [(p - (1.0 if w else 0.0)) ** 2 for p, w in pairs]
    brier = float(np.mean(briers))
    ece_num = 0.0
    lines = []
    for lo, hi in BINS:
        b = [(p, w) for p, w in pairs if lo <= p < hi]
        if not b:
            continue
        emp = np.mean([1.0 if w else 0.0 for p, w in b])
        impl = np.mean([p for p, _ in b])
        se = math.sqrt(max(emp * (1 - emp), 1e-9) / len(b))
        ece_num += abs(emp - impl) * len(b)
        lines.append(f"    [{lo:.1f},{hi:.1f}) N={len(b):>4} impl={impl*100:5.1f}% emp={emp*100:5.1f}% "
                     f"gap={(emp-impl)*100:+5.1f}pp (SE {se*100:4.1f})")
    ece = ece_num / n
    print(f"  {label}: N={n} ECE={ece*100:.2f}pp Brier={brier:.4f}")
    for ln in lines:
        print(ln)
    return ece, brier, n


def bootstrap_ece_diff(pairs_a, pairs_b, iters=2000, seed=1):
    """Bootstrap CI for ECE(a) - ECE(b). Pairs resampled independently (different Ns)."""
    rng = np.random.default_rng(seed)
    def ece_of(sample):
        n = len(sample)
        tot = 0.0
        for lo, hi in BINS:
            b = [(p, w) for p, w in sample if lo <= p < hi]
            if b:
                emp = np.mean([1.0 if w else 0.0 for _, w in b])
                impl = np.mean([p for p, _ in b])
                tot += abs(emp - impl) * len(b)
        return tot / n
    diffs = []
    a = np.array(pairs_a, dtype=float)
    b = np.array(pairs_b, dtype=float)
    for _ in range(iters):
        sa = a[rng.integers(0, len(a), len(a))]
        sb = b[rng.integers(0, len(b), len(b))]
        diffs.append(ece_of([tuple(x) for x in sa]) - ece_of([tuple(x) for x in sb]))
    diffs = np.array(diffs)
    return float(np.mean(diffs)), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", default="/tmp/listing_study/paths.jsonl")
    ap.add_argument("--min-life-h", type=float, default=120)
    ap.add_argument("--family", default=None, help="restrict to family")
    ap.add_argument("--series", choices=["only", "exclude", "all"], default="exclude")
    ap.add_argument("--stale", choices=["fresh", "any"], default="fresh")
    args = ap.parse_args()
    require_fresh = args.stale == "fresh"

    rows = load(args.paths)
    print(f"# loaded {len(rows)} rows")
    nohist = [r for r in rows if r.get("no_hist")]
    rows = [r for r in rows if not r.get("no_hist")]
    print(f"# no_hist (never traded on CLOB despite vol>=floor): {len(nohist)}")

    if args.series == "exclude":
        rows = [r for r in rows if not r.get("series")]
    elif args.series == "only":
        rows = [r for r in rows if r.get("series")]
    rows = [r for r in rows if r["life_h"] >= args.min_life_h]
    for r in rows:
        r["_fam"] = family(r)
    if args.family:
        rows = [r for r in rows if r["_fam"] == args.family]
    print(f"# after series={args.series}, life>={args.min_life_h}h, family={args.family}: N={len(rows)}")

    # --- data availability by age ---
    print("\n== availability: markets with a (fresh) price at each age ==")
    for a in ALL_AGES:
        n = sum(1 for r in rows if get_px(r, a, require_fresh) is not None)
        n_any = sum(1 for r in rows if get_px(r, a, False) is not None)
        print(f"  T+{a:>4}h: fresh={n:>4} any={n_any:>4} / {len(rows)}")
    lags = [r["first_print_lag_min"] for r in rows if r.get("first_print_lag_min") is not None]
    if lags:
        q = np.percentile(lags, [10, 25, 50, 75, 90])
        print(f"  first-print lag min (N={len(lags)}): p10={q[0]:.0f} p25={q[1]:.0f} p50={q[2]:.0f} "
              f"p75={q[3]:.0f} p90={q[4]:.0f}")
        fp = [r["first_print_p"] for r in rows if r.get("first_print_p") is not None]
        near50 = sum(1 for p in fp if 0.45 <= p <= 0.55) / len(fp)
        print(f"  first prints in [0.45,0.55]: {near50*100:.1f}%")

    # --- calibration by age ---
    print("\n== calibration by age (outcome0 price vs outcome0 won) ==")
    stats = {}
    pairs_by_age = {}
    for a in AGES + ["96"]:
        pairs = [(get_px(r, a, require_fresh), r["out0_won"]) for r in rows]
        pairs = [(p, w) for p, w in pairs if p is not None and 0 < p < 1]
        pairs_by_age[a] = pairs
        stats[a] = calib_table(pairs, f"T+{a}h")
    for fr in ["0.25", "0.5"]:
        pairs = [(r["fracs"].get(fr, [None])[0], r["out0_won"]) for r in rows if r.get("fracs")]
        pairs = [(p, w) for p, w in pairs if p is not None and 0 < p < 1]
        calib_table(pairs, f"{float(fr)*100:.0f}%-of-life")
    pairs = [(r["preclose24"][0], r["out0_won"]) for r in rows if r.get("preclose24")]
    pairs = [(p, w) for p, w in pairs if p is not None and 0 < p < 1]
    calib_table(pairs, "close-24h")

    # matched-sample ECE comparison: only markets with BOTH 1h and 72h fresh prices
    both = [r for r in rows if get_px(r, "1", require_fresh) is not None
            and get_px(r, "72", require_fresh) is not None]
    pa = [(get_px(r, "1", require_fresh), r["out0_won"]) for r in both]
    pb = [(get_px(r, "72", require_fresh), r["out0_won"]) for r in both]
    if len(both) >= 50:
        d, lo, hi = bootstrap_ece_diff(pa, pb)
        print(f"\n  matched N={len(both)}: ECE(1h)-ECE(72h) = {d*100:+.2f}pp  95%CI [{lo*100:+.2f},{hi*100:+.2f}]")

    # --- martingale drift 1h -> 72h ---
    print("\n== drift: E[p72 - p_early | p_early bin] (matched markets) ==")
    for a in ["1", "6", "24"]:
        sub = [(get_px(r, a, require_fresh), get_px(r, "72", require_fresh)) for r in rows]
        sub = [(p0, p1) for p0, p1 in sub if p0 is not None and p1 is not None]
        if len(sub) < 30:
            continue
        print(f"  from T+{a}h (N={len(sub)}):")
        for lo, hi in BINS:
            b = [(p0, p1) for p0, p1 in sub if lo <= p0 < hi]
            if len(b) < 10:
                continue
            d = [p1 - p0 for p0, p1 in b]
            print(f"    [{lo:.1f},{hi:.1f}) N={len(b):>4} mean drift={np.mean(d)*100:+5.1f}pp "
                  f"(SE {np.std(d)/math.sqrt(len(b))*100:4.1f}) |drift|={np.mean(np.abs(d))*100:4.1f}pp")
        toward_extreme = [abs(p1 - 0.5) - abs(p0 - 0.5) for p0, p1 in sub]
        print(f"    extremization E[|p72-.5|-|p_e-.5|] = {np.mean(toward_extreme)*100:+.1f}pp")

    # --- divergence distribution ---
    print("\n== divergence |p_early - p72| (opportunity frequency proxy) ==")
    for a in ["1", "6", "24"]:
        sub = [(get_px(r, a, require_fresh), get_px(r, "72", require_fresh)) for r in rows]
        sub = [abs(p1 - p0) for p0, p1 in sub if p0 is not None and p1 is not None]
        if not sub:
            continue
        sub = np.array(sub)
        print(f"  T+{a:>2}h vs 72h: N={len(sub)} mean={sub.mean()*100:.1f}pp "
              f">=5pp: {(sub>=0.05).mean()*100:.0f}%  >=10pp: {(sub>=0.10).mean()*100:.0f}%  "
              f">=20pp: {(sub>=0.20).mean()*100:.0f}%")
    # maturity yardstick: 72h vs 50% of life
    sub = []
    for r in rows:
        p72 = get_px(r, "72", require_fresh)
        pm = r.get("fracs", {}).get("0.5", [None])[0]
        if p72 is not None and pm is not None:
            sub.append(abs(pm - p72))
    if sub:
        sub = np.array(sub)
        print(f"  72h vs 50%life: N={len(sub)} mean={sub.mean()*100:.1f}pp "
              f">=10pp: {(sub>=0.10).mean()*100:.0f}%  >=20pp: {(sub>=0.20).mean()*100:.0f}%")

    # --- hindsight winner cost by age ---
    print("\n== hindsight: mean price of EVENTUAL WINNER at each age (buy-winner cost) ==")
    for a in ALL_AGES:
        costs = []
        for r in rows:
            p = get_px(r, a, require_fresh)
            if p is None:
                continue
            costs.append(p if r["out0_won"] else 1 - p)
        if costs:
            print(f"  T+{a:>4}h: N={len(costs):>4} mean winner price={np.mean(costs)*100:5.1f}c "
                  f"(hindsight multiple {1/np.mean(costs):.2f}x)")

    # --- family breakdown at 1h vs 72h ---
    if not args.family:
        print("\n== by family: ECE at 1h / 72h ==")
        fams = defaultdict(list)
        for r in rows:
            fams[r["_fam"]].append(r)
        for f, rs in sorted(fams.items(), key=lambda kv: -len(kv[1])):
            p1 = [(get_px(r, "1", require_fresh), r["out0_won"]) for r in rs]
            p1 = [(p, w) for p, w in p1 if p is not None and 0 < p < 1]
            p72 = [(get_px(r, "72", require_fresh), r["out0_won"]) for r in rs]
            p72 = [(p, w) for p, w in p72 if p is not None and 0 < p < 1]
            def ece_of(sample):
                if len(sample) < 20:
                    return None
                tot = n = 0
                for lo, hi in BINS:
                    b = [(p, w) for p, w in sample if lo <= p < hi]
                    if b:
                        emp = np.mean([1.0 if w else 0.0 for _, w in b])
                        impl = np.mean([p for p, _ in b])
                        tot += abs(emp - impl) * len(b)
                        n += len(b)
                return tot / n if n else None
            e1, e72 = ece_of(p1), ece_of(p72)
            print(f"  {f:<26} N={len(rs):>4} ECE1h={'--' if e1 is None else f'{e1*100:5.1f}pp'}"
                  f" (n={len(p1):>3})  ECE72h={'--' if e72 is None else f'{e72*100:5.1f}pp'} (n={len(p72):>3})")

    # --- volume terciles at 1h ---
    print("\n== calibration at T+1h by final-volume tercile ==")
    withp = [r for r in rows if get_px(r, "1", require_fresh) is not None]
    if len(withp) >= 60:
        vols = sorted(r["vol"] for r in withp)
        t1, t2 = vols[len(vols)//3], vols[2*len(vols)//3]
        for lab, sel in [("low", lambda v: v < t1), ("mid", lambda v: t1 <= v < t2),
                         ("high", lambda v: v >= t2)]:
            pairs = [(get_px(r, "1", require_fresh), r["out0_won"]) for r in withp if sel(r["vol"])]
            pairs = [(p, w) for p, w in pairs if p is not None and 0 < p < 1]
            calib_table(pairs, f"vol-{lab} (cut {t1:.0f}/{t2:.0f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
