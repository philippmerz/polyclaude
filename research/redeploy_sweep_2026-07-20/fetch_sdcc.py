#!/usr/bin/env python3
"""Targeted SDCC 2026 satellite fetch. Pulls markets by tag/slug/search keywords
regardless of volume floor (satellites are thin). Streams slim rows to jsonl.
Strategy: (1) gamma /events?search=, (2) gamma /markets keyset scan filtering
slug/question for comic-con|sdcc|hall-h keywords.
"""
import json, re, sys, time
from datetime import datetime, timezone
import httpx

MARKETS = "https://gamma-api.polymarket.com/markets"
EVENTS = "https://gamma-api.polymarket.com/events"
NOW = datetime.now(timezone.utc)

KW = re.compile(r"comic[- ]?con|sdcc|hall\s*h|comiccon|san diego comic", re.I)

def days_to_end(m):
    ed = m.get("endDate")
    if not ed:
        return None
    try:
        d = datetime.fromisoformat(ed.replace("Z", "+00:00"))
        return (d - NOW).total_seconds() / 86400.0
    except Exception:
        return None

def slim(m):
    ev = (m.get("events") or [{}])
    ev = ev[0] if ev else {}
    return {
        "id": m.get("id"), "q": m.get("question"), "slug": m.get("slug"),
        "conditionId": m.get("conditionId"),
        "description": m.get("description"),
        "endDate": m.get("endDate"),
        "outcomes": m.get("outcomes"), "outcomePrices": m.get("outcomePrices"),
        "clobTokenIds": m.get("clobTokenIds"),
        "volumeNum": m.get("volumeNum"), "vol24": m.get("volume24hr"),
        "liquidityNum": m.get("liquidityNum"),
        "umaStatuses": m.get("umaResolutionStatuses"),
        "negRisk": m.get("negRisk"),
        "takerBaseFee": m.get("takerBaseFee"),
        "spread": m.get("spread"), "bestBid": m.get("bestBid"), "bestAsk": m.get("bestAsk"),
        "active": m.get("active"), "closed": m.get("closed"),
        "acceptingOrders": m.get("acceptingOrders"),
        "enableOrderBook": m.get("enableOrderBook"),
        "event_slug": ev.get("slug"), "event_title": ev.get("title"),
        "orderMinSize": m.get("orderMinSize"),
        "dte": round(days_to_end(m) or -1, 1),
    }

def main():
    out = {}
    with httpx.Client(timeout=30) as c:
        # 1) events search
        for term in ["comic-con", "sdcc", "comic con", "hall h", "san diego comic"]:
            try:
                r = c.get(EVENTS, params={"search": term, "closed": "false", "limit": 100})
                evs = r.json() if r.status_code == 200 else []
                if isinstance(evs, dict):
                    evs = evs.get("events") or evs.get("data") or []
                for ev in (evs or []):
                    for m in (ev.get("markets") or []):
                        if m.get("id"):
                            m.setdefault("events", [ev])
                            out[m["id"]] = m
            except Exception as e:
                print(f"# events search {term} failed: {e}", file=sys.stderr)
            time.sleep(0.3)
        # 2) markets keyset scan by keyword (broad, closed=false)
        cursor = None
        pages = 0
        while pages < 400:
            p = {"limit": 100, "closed": "false"}
            if cursor:
                p["after_cursor"] = cursor
            try:
                r = c.get("https://gamma-api.polymarket.com/markets/keyset", params=p)
                if r.status_code == 429:
                    time.sleep(4); continue
                b = r.json() if r.status_code == 200 else None
            except Exception:
                b = None
            if not isinstance(b, dict) or "markets" not in b:
                break
            mk = b["markets"]
            if not mk:
                break
            for m in mk:
                q = (m.get("question") or "") + " " + (m.get("slug") or "")
                ev = (m.get("events") or [{}])
                et = (ev[0].get("title") or "") + " " + (ev[0].get("slug") or "") if ev else ""
                if KW.search(q) or KW.search(et):
                    if m.get("id"):
                        out[m["id"]] = m
            cursor = b.get("next_cursor")
            pages += 1
            if not cursor:
                break
            time.sleep(0.2)
    with open("/tmp/redeploy_sweep/sdcc_markets.jsonl", "w") as f:
        for m in out.values():
            f.write(json.dumps(slim(m)) + "\n")
    print(f"# SDCC markets found: {len(out)} (pages scanned {pages})", file=sys.stderr)

if __name__ == "__main__":
    main()
