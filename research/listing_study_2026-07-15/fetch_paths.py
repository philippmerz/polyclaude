#!/usr/bin/env python3
"""Fetch CLOB price paths anchored at listing time for sampled cohort markets.

Input:  cohort JSONL (from crawl_keyset.py), filtered+sampled here.
Output: paths.jsonl — one row per market with prices at fixed ages after listing,
        fixed fractions of life, first-print lag, and metadata. Resumable (skips ids
        already present in output).

Sampling: ALL usable non-series markets + --series-sample random series markets.
Usable = 2 outcomes, decisive resolution (p0 in {0,1}), umaResolutionStatus resolved,
         has clobTokenIds + acceptingOrdersTimestamp/createdAt + closedTime,
         lifetime >= --min-life-h hours, volumeNum >= --min-volume.
"""
import argparse, ast, json, os, random, sys, time
from datetime import datetime
import httpx

CLOB_PH = "https://clob.polymarket.com/prices-history"
AGES_H = [0.25, 0.5, 1, 2, 3, 6, 12, 24, 48, 72, 96]
FRACS = [0.25, 0.5, 0.75]


def parse(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else x
    except Exception:
        return None


def iso2ts(s):
    if not s:
        return None
    s = s.strip().replace("Z", "+00:00")
    if " " in s and "T" not in s:
        s = s.replace(" ", "T")
    if s.endswith("+00"):
        s += ":00"
    try:
        return int(datetime.fromisoformat(s).timestamp())
    except Exception:
        return None


def get_hist(client, tok, params):
    for _ in range(3):
        try:
            r = client.get(CLOB_PH, params=dict(market=tok, **params), timeout=25)
            if r.status_code == 200:
                b = r.json()
                if isinstance(b, dict):
                    return b.get("history", [])
        except Exception:
            pass
        time.sleep(0.7)
    return None


def px_at(hist, target_ts):
    """Last point at/before target; returns (price, staleness_seconds) or (None, None)."""
    best = None
    for pt in hist:
        if pt["t"] <= target_ts:
            best = pt
        else:
            break
    if best is None:
        return None, None
    return float(best["p"]), target_ts - best["t"]


def usable(m, min_life_h, min_volume):
    oc, op = parse(m.get("outcomes")), parse(m.get("outcomePrices"))
    if not oc or len(oc) != 2 or not op:
        return None
    if m.get("umaResolutionStatus") != "resolved":
        return None
    try:
        p0 = float(op[0])
    except Exception:
        return None
    if p0 not in (0.0, 1.0):
        return None
    toks = parse(m.get("clobTokenIds"))
    if not toks:
        return None
    t0 = iso2ts(m.get("acceptingOrdersTimestamp")) or iso2ts(m.get("createdAt"))
    tc = iso2ts(m.get("closedTime"))
    if not t0 or not tc:
        return None
    life_h = (tc - t0) / 3600
    if life_h < min_life_h:
        return None
    if (m.get("volumeNum") or 0) < min_volume:
        return None
    return {"t0": t0, "tc": tc, "life_h": life_h, "tok0": toks[0],
            "out0_won": p0 == 1.0, "outcomes": oc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", default="/tmp/listing_study/cohort_apr_may.jsonl")
    ap.add_argument("--out", default="/tmp/listing_study/paths.jsonl")
    ap.add_argument("--min-life-h", type=float, default=96)
    ap.add_argument("--min-volume", type=float, default=1000)
    ap.add_argument("--series-sample", type=int, default=200)
    ap.add_argument("--nonseries-cap", type=int, default=900)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    done = set()
    if os.path.exists(args.out):
        for l in open(args.out):
            try:
                done.add(json.loads(l)["id"])
            except Exception:
                pass
        print(f"# resuming: {len(done)} already fetched", file=sys.stderr)

    nonseries, series = [], []
    seen = set()
    for l in open(args.cohort):
        m = json.loads(l)
        if m["id"] in seen:
            continue
        seen.add(m["id"])
        u = usable(m, args.min_life_h, args.min_volume)
        if not u:
            continue
        m["_u"] = u
        (series if m.get("series") else nonseries).append(m)
    rng = random.Random(args.seed)
    if len(nonseries) > args.nonseries_cap:
        nonseries = rng.sample(nonseries, args.nonseries_cap)
    ser = rng.sample(series, min(args.series_sample, len(series)))
    todo = [m for m in nonseries + ser if m["id"] not in done]
    print(f"# usable: {len(nonseries)} non-series (cap {args.nonseries_cap}), "
          f"{len(series)} series (sampling {len(ser)}); to fetch: {len(todo)}", file=sys.stderr)

    n_ok = n_nohist = 0
    with httpx.Client() as client, open(args.out, "a") as f:
        for i, m in enumerate(todo):
            u = m["_u"]
            t0, tc = u["t0"], u["tc"]
            # early window: listing -> +100h (capped at close)
            end_early = min(t0 + int(100 * 3600), tc)
            h_early = get_hist(client, u["tok0"], {"startTs": t0 - 3600, "endTs": end_early, "fidelity": 10})
            time.sleep(0.10)
            # whole life at coarse fidelity for fraction-of-life + pre-close prices
            h_life = get_hist(client, u["tok0"], {"interval": "max", "fidelity": 360})
            time.sleep(0.10)
            row = {"id": m["id"], "q": m["q"], "series": bool(m.get("series")),
                   "neg_risk": m.get("negRisk"), "vol": m.get("volumeNum"),
                   "liq": m.get("liquidityNum"), "t0": t0, "tc": tc,
                   "life_h": round(u["life_h"], 2), "out0_won": u["out0_won"],
                   "outcomes": u["outcomes"], "event_title": m.get("event_title"),
                   "startDate": m.get("startDate"), "createdAt": m.get("createdAt"),
                   "accepting": m.get("acceptingOrdersTimestamp")}
            if not h_early and not h_life:
                row["no_hist"] = True
                n_nohist += 1
                f.write(json.dumps(row) + "\n")
                f.flush()
                continue
            h_early = h_early or []
            h_life = h_life or []
            # trim early hist to >= t0-1h (paranoia) and record first print
            h_early = [pt for pt in h_early if pt["t"] >= t0 - 3600]
            if h_early:
                row["first_print_lag_min"] = round((h_early[0]["t"] - t0) / 60, 1)
                row["first_print_p"] = float(h_early[0]["p"])
                row["n_prints_early"] = len(h_early)
            ages = {}
            for a in AGES_H:
                tgt = t0 + int(a * 3600)
                if tgt > tc:  # age beyond market life
                    continue
                p, stale = px_at(h_early, tgt)
                if p is None and h_life:
                    p, stale = px_at(h_life, tgt)
                if p is not None:
                    ages[str(a)] = [round(p, 4), int(stale)]
            row["ages"] = ages
            fracs = {}
            for fr in FRACS:
                tgt = t0 + int(fr * (tc - t0))
                p, stale = px_at(h_life, tgt)
                if p is None:
                    p, stale = px_at(h_early, tgt)
                if p is not None:
                    fracs[str(fr)] = [round(p, 4), int(stale)]
            row["fracs"] = fracs
            # pre-close price (24h before close) as sanity control
            p, stale = px_at(h_life, tc - 86400)
            if p is not None:
                row["preclose24"] = [round(p, 4), int(stale)]
            f.write(json.dumps(row) + "\n")
            f.flush()
            n_ok += 1
            if (i + 1) % 50 == 0:
                print(f"# {i+1}/{len(todo)} fetched ({n_ok} ok, {n_nohist} no-hist)", file=sys.stderr)
    print(f"# DONE: {n_ok} ok, {n_nohist} no-hist -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
