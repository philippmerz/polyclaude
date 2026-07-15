#!/usr/bin/env python3
"""Persistence: for liquid TRUE implication pairs, pull CLOB prices-history (mids)
on both legs, align, and measure violation episodes (p_narrow > p_broad + thr)."""
import json, sys, time
import httpx

PAIRS = [
    # (label, narrow_market_id, broad_id, relation)
    ("massie_pres_vs_nom", "561260", "562005", "P(win pres) <= P(win R nom)"),
    ("newsom_pres_vs_nom", None, None, "auto-find"),
    ("maxwell_dup", None, None, "by end 2026 == before 2027"),
    ("anthropic_ipo_dup", "676792", "2413330", "before 2027 ~= by Dec 31 2026"),
]


def yes_token(client, mid):
    g = client.get(f"https://gamma-api.polymarket.com/markets/{mid}").json()
    toks = json.loads(g["clobTokenIds"])
    return toks[0], g["question"]


def hist(client, tok, fidelity=60):
    r = client.get("https://clob.polymarket.com/prices-history",
                   params={"market": tok, "interval": "max", "fidelity": fidelity})
    h = r.json().get("history", [])
    return {p["t"] // 3600 * 3600: p["p"] for p in h}


def analyze(label, mid_n, mid_b, relation, client, thr=0.01):
    tn, qn = yes_token(client, mid_n)
    tb, qb = yes_token(client, mid_b)
    hn, hb = hist(client, tn), hist(client, tb)
    common = sorted(set(hn) & set(hb))
    if not common:
        print(f"{label}: no overlapping history")
        return None
    viol = [(t, hn[t] - hb[t]) for t in common]
    n = len(viol)
    above = [v for _, v in viol if v > thr]
    # episodes
    eps, cur = [], 0
    for _, v in viol:
        if v > thr:
            cur += 1
        else:
            if cur:
                eps.append(cur)
            cur = 0
    if cur:
        eps.append(cur)
    mx = max((v for _, v in viol), default=0)
    res = {
        "label": label, "relation": relation, "n_q": qn, "b_q": qb,
        "hours_overlap": n, "days": round(n / 24, 1),
        "pct_hours_viol_gt1pp": round(100 * len(above) / n, 2),
        "n_episodes": len(eps),
        "median_episode_h": sorted(eps)[len(eps) // 2] if eps else 0,
        "max_episode_h": max(eps) if eps else 0,
        "max_viol_pp": round(mx * 100, 2),
        "now_viol_pp": round(viol[-1][1] * 100, 2),
    }
    print(json.dumps(res, indent=1))
    return res


def main():
    out = []
    with httpx.Client(timeout=25) as c:
        # resolve auto-find pairs from pairs.jsonl
        prs = [json.loads(l) for l in open("/tmp/implication_study/pairs.jsonl")]
        newsom = [r for r in prs if r["cls"] == "A_nom" and "Newsom" in r["n_q"] and "presidential election" in r["n_q"].lower()]
        maxwell = [r for r in prs if r["sub"] == "dup" and "Maxwell" in r["n_q"] and "[rev]" not in r["note"]]
        jobs = [("massie_pres_vs_nom", "561260", "562005", "P(pres) <= P(R nom)")]
        if newsom:
            jobs.append(("newsom_pres_vs_nom", newsom[0]["n_id"], newsom[0]["b_id"], "P(pres) <= P(D nom)"))
        if maxwell:
            jobs.append(("maxwell_dup", maxwell[0]["n_id"], maxwell[0]["b_id"], "dup: by-end-2026 == before-2027"))
        jobs.append(("anthropic_ipo_dup", "676792", "2413330", "near-dup (criteria differ)"))
        for j in jobs:
            try:
                r = analyze(*j, client=c)
                if r:
                    out.append(r)
            except Exception as e:
                print(f"{j[0]}: ERR {e}", file=sys.stderr)
            time.sleep(0.3)
    json.dump(out, open("/tmp/implication_study/persistence.json", "w"), indent=1)


if __name__ == "__main__":
    main()
