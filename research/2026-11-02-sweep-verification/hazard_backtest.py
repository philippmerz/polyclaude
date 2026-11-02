#!/usr/bin/env python3
"""Retrospective test of the strategy-sweep 'hazard-mismatch scanner' idea.

Question: on RESOLVED Polymarket date ladders ("X by <date>" siblings), does a
sibling's deviation from a constant-hazard fit of the whole ladder predict the
outcome better than the sibling's own price?  If a hazard-shape anomaly were a
mispricing signal, trading each sibling toward the fit should earn money even
at the (optimistic) midpoint, before fees and spread.

Read-only public data: gamma-api closed events + clob prices-history.
Output: JSON summary to stdout (and cached raw rows under --cache).
"""
from __future__ import annotations
import argparse, datetime as dt, json, math, re, sys, time
from pathlib import Path
import httpx

GAMMA = "https://gamma-api.polymarket.com/events"
HIST = "https://clob.polymarket.com/prices-history"
MONTHS = {m: i for i, m in enumerate(
    ["january","february","march","april","may","june","july","august",
     "september","october","november","december"], 1)}
DATE_RE = re.compile(r"\bby\s+(?:the\s+end\s+of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{1,2})?(?:st|nd|rd|th)?,?\s*(\d{4})?", re.I)


def parse_deadline(q: str, fallback_year: int) -> dt.datetime | None:
    m = DATE_RE.search(q)
    if not m:
        return None
    mon = MONTHS[m.group(1).lower()]
    year = int(m.group(3)) if m.group(3) else fallback_year
    if m.group(2):
        day = int(m.group(2))
    else:  # "by March" / "by end of March" -> last day of month
        nxt = dt.date(year + (mon == 12), mon % 12 + 1, 1)
        day = (nxt - dt.timedelta(days=1)).day
    try:
        return dt.datetime(year, mon, day, 23, 59, tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def template(q: str) -> str:
    return DATE_RE.sub("by <D>", q).strip().lower()


def fetch_events(client, pages: int) -> list[dict]:
    """Highest-volume closed events per calendar month (gamma caps limit at
    100 and rejects deep offsets), Jan 2025 .. last month. `pages` = pages of
    100 per month."""
    out, seen = [], set()
    today = dt.date.today()
    y, m = 2025, 1
    while (y, m) < (today.year, today.month):
        ny, nm = (y + (m == 12), m % 12 + 1)
        for p in range(pages):
            r = client.get(GAMMA, params={
                "closed": "true", "limit": 100, "offset": p * 100, "order": "volume",
                "ascending": "false", "end_date_min": f"{y}-{m:02d}-01T00:00:00Z",
                "end_date_max": f"{ny}-{nm:02d}-01T00:00:00Z"})
            if r.status_code != 200:
                break
            rows = [e for e in r.json() if e.get("id") not in seen]
            if not rows:
                break
            seen.update(e.get("id") for e in rows)
            out.extend(rows)
        y, m = ny, nm
    return out


def price_at(client, token: str, ts: int) -> float | None:
    r = client.get(HIST, params={"market": token, "startTs": ts - 86400, "endTs": ts + 3600, "fidelity": 60})
    if r.status_code != 200:
        return None
    hist = r.json().get("history") or []
    before = [h for h in hist if h["t"] <= ts]
    if not before:
        return None
    return float(before[-1]["p"])


def ladders(events: list[dict]):
    for e in events:
        mk = e.get("markets") or []
        if len(mk) < 3:
            continue
        year = int((e.get("endDate") or "2026")[:4])
        groups: dict[str, list] = {}
        for m in mk:
            q = m.get("question") or ""
            d = parse_deadline(q, year)
            if d is None:
                continue
            try:
                outcome = json.loads(m.get("outcomePrices") or "[]")
                toks = json.loads(m.get("clobTokenIds") or "[]")
            except ValueError:
                continue
            if len(outcome) != 2 or not toks or outcome[0] not in ("0", "1"):
                continue
            start = m.get("startDate") or m.get("createdAt")
            groups.setdefault(template(q), []).append(
                {"q": q, "deadline": d, "yes_won": outcome[0] == "1", "token": toks[0],
                 "start": start, "slug": m.get("slug")})
        for tpl, rows in groups.items():
            rows.sort(key=lambda r: r["deadline"])
            if len({r["deadline"] for r in rows}) >= 3:
                yield e.get("slug"), tpl, rows


def fit_hazard(taus, ps):
    ys = [-math.log(max(1e-6, 1 - p)) for p in ps]
    den = sum(t * t for t in taus)
    lam = sum(t * y for t, y in zip(taus, ys)) / den if den else 0.0
    return [1 - math.exp(-lam * t) for t in taus]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=8)
    ap.add_argument("--threshold", type=float, default=0.05)
    ap.add_argument("--cache", default="/tmp/hazard_rows.json")
    a = ap.parse_args()
    client = httpx.Client(timeout=30)
    cache = Path(a.cache)
    if cache.exists():
        rows_all = json.loads(cache.read_text())
    else:
        evs = fetch_events(client, a.pages)
        rows_all = []
        for slug, tpl, rows in ladders(evs):
            # Snapshot = first moment (sibling listing + 1 day) at which >=3
            # distinct-deadline siblings are listed with >= 7 days to run.
            def _st(r):
                return dt.datetime.fromisoformat(r["start"].replace("Z", "+00:00")) if r["start"] else None
            snap, live = None, []
            for cand in sorted({_st(r) for r in rows if _st(r)}):
                cand = cand + dt.timedelta(days=1)
                live = [r for r in rows if _st(r) and _st(r) <= cand
                        and r["deadline"] >= cand + dt.timedelta(days=7)]
                uniq = {}
                for r in live:
                    uniq.setdefault(r["deadline"], r)
                live = sorted(uniq.values(), key=lambda r: r["deadline"])
                if len(live) >= 3:
                    snap = cand
                    break
            if snap is None:
                continue
            ts = int(snap.timestamp())
            prices = [price_at(client, r["token"], ts) for r in live]
            if any(p is None for p in prices):
                continue
            rows_all.append({"event": slug, "template": tpl, "snapshot": snap.isoformat(),
                             "siblings": [{"q": r["q"], "deadline": r["deadline"].isoformat(),
                                           "yes_won": r["yes_won"], "p": p} for r, p in zip(live, prices)]})
            time.sleep(0.05)
        cache.write_text(json.dumps(rows_all))
    trades, brier_m, brier_h, n_sib, ev_pnl = [], 0.0, 0.0, 0, {}
    used = 0
    for lad in rows_all:
        sib = lad["siblings"]
        if max(s["p"] for s in sib) > 0.97 or min(s["p"] for s in sib) <= 0.0:
            continue  # already happened / dead at snapshot
        snap = dt.datetime.fromisoformat(lad["snapshot"])
        taus = [(dt.datetime.fromisoformat(s["deadline"]) - snap).total_seconds() / 86400 for s in sib]
        model = fit_hazard(taus, [s["p"] for s in sib])
        used += 1
        for s, mp in zip(sib, model):
            y = 1.0 if s["yes_won"] else 0.0
            brier_m += (s["p"] - y) ** 2
            brier_h += (mp - y) ** 2
            n_sib += 1
            d = mp - s["p"]
            if abs(d) >= a.threshold:
                pnl = (y - s["p"]) if d > 0 else ((1 - y) - (1 - s["p"]))
                cost = s["p"] if d > 0 else 1 - s["p"]
                trades.append({"event": lad["event"], "d": round(d, 4), "pnl": pnl, "cost": cost})
                ev_pnl.setdefault(lad["event"], 0.0)
                ev_pnl[lad["event"]] += pnl
    tot = sum(t["pnl"] for t in trades)
    cost = sum(t["cost"] for t in trades)
    print(json.dumps({
        "ladders_fetched": len(rows_all), "ladders_used": used, "siblings": n_sib,
        "brier_market": round(brier_m / n_sib, 4) if n_sib else None,
        "brier_const_hazard": round(brier_h / n_sib, 4) if n_sib else None,
        "threshold": a.threshold, "trades": len(trades),
        "pnl_per_share_sum_midpoint_no_fees": round(tot, 3),
        "return_on_cost_midpoint_no_fees": round(tot / cost, 4) if cost else None,
        "events_with_trades": len(ev_pnl),
        "events_positive": sum(1 for v in ev_pnl.values() if v > 0),
        "events_negative": sum(1 for v in ev_pnl.values() if v < 0),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
