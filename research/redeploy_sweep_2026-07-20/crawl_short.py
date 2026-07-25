#!/usr/bin/env python3
"""Short-dated instance-mispricing sweep crawl (2026-07-15 evening).
Adapted from research/instance_sweep_2026-07-15/crawl_sweep.py. Changes:
  - dte window 5-20 days (endDate ~Jul-20 .. Aug-04), NOW = actual utcnow
  - volumeNum >= 1000 (thinner short-dated books)
  - extra exclusions: crypto-price/close-at/above-below markets,
    weather/temperature series, election-DAY (who-wins) markets
Streams slim rows to jsonl; resumable via cursor checkpoint.
"""
import argparse, json, os, re, sys, time
from datetime import datetime, timezone
import httpx

KEYSET = "https://gamma-api.polymarket.com/markets/keyset"
NOW = datetime.now(timezone.utc)

# series/sports/up-down exclusion (same as long sweep)
BAD_Q = re.compile(
    r"\bup or down\b|\bo/u\b|\bover/under\b|\bhandicap\b|\bmap \d|\bgame \d|"
    r"\b(1st|2nd|3rd|4th) (quarter|half|period|inning)\b|"
    r"\bvs\.?\s|\bspread\b.*\bpoints\b|\bmoneyline\b|\bwin by\b|\btotal (points|goals|runs|rounds)\b",
    re.I)
BAD_SLUG = re.compile(
    r"-vs-|up-or-down|-o-u-|over-under|handicap|-map-\d|-match-|moneyline|-spread-|"
    r"\b(nba|nfl|mlb|nhl|epl|ucl|laliga|serie-a|bundesliga|atp|wta|ufc|mma|csgo|cs2|lol|dota|valorant)-",
    re.I)
# crypto/asset price mechanics: above/below/close-at/hit $X/ATH/dip-to
PRICE_Q = re.compile(
    r"\b(close|closing) (at|above|below)\b|\babove or below\b|"
    r"\b(reach|hit|touch|dip to|drop to|fall to|trade (at|above|below))\s+\$|"
    r"\ball[- ]time high\b|\bprice of\b.{0,30}\$|\bwhat price\b|"
    r"\b(bitcoin|btc|ethereum|eth|solana|sol|xrp|dogecoin|doge|cardano|litecoin|gold|silver|oil)\b.{0,40}\$[\d,]|"
    r"\$[\d,.]+[kKmM]?\s+(by|on|before|in)\b",
    re.I)
PRICE_SLUG = re.compile(
    r"-close-at-|above-below|-ath-|all-time-high|-price-(above|below|at)-|"
    r"(bitcoin|ethereum|solana|xrp|doge)-(above|below|hits?|reach)", re.I)
# weather / temperature series
WEATHER = re.compile(
    r"\btemperature\b|\bdegrees? (f|c|fahrenheit|celsius)\b|°|\bhottest\b|\bcoldest\b|"
    r"\brain(fall)?\b|\bsnow(fall)?\b|\bheat index\b|\bhigh temp\b", re.I)
# election-DAY (who wins an election) — criteria = colloquial pure odds
ELECTION_DAY = re.compile(
    r"\bwin(s)? the\b.{0,60}\b(election|primary|runoff|run-off|mayoral race)\b|"
    r"\bbe elected\b|\belected (as )?(president|mayor|governor|pm|prime minister)\b|"
    r"\bnext (president|prime minister|mayor|governor|chancellor) of\b|"
    r"\bwin (the )?(presidency|governorship|mayoralty)\b|"
    r"\b(presidential|gubernatorial|mayoral|parliamentary|general|legislative) election\b.{0,30}\bwinner\b|"
    r"\bwhich party wins\b|\bpopular vote\b|\bmost seats\b|\bmargin of victory\b",
    re.I)


def days_to_end(m):
    ed = m.get("endDate")
    if not ed:
        return None
    try:
        d = datetime.fromisoformat(ed.replace("Z", "+00:00"))
        return (d - NOW).total_seconds() / 86400.0
    except Exception:
        return None


def keep(m):
    if not m.get("active") or m.get("closed"):
        return False
    if not m.get("acceptingOrders"):
        return False
    if not m.get("enableOrderBook"):
        return False
    us = m.get("umaResolutionStatuses") or m.get("umaResolutionStatus") or ""
    if isinstance(us, str) and ("proposed" in us.lower() or "disputed" in us.lower()):
        return False
    oc = m.get("outcomes")
    if isinstance(oc, str):
        try:
            oc = json.loads(oc)
        except Exception:
            return False
    if not (isinstance(oc, list) and len(oc) == 2):
        return False
    v = m.get("volumeNum") or 0
    if v < 1000:
        return False
    dte = days_to_end(m)
    if dte is None or dte < 3 or dte > 45:
        return False
    ev = (m.get("events") or [{}])[0]
    q = m.get("question") or ""
    slug = m.get("slug") or ""
    ev_slug = ev.get("slug") or ""
    ev_title = ev.get("title") or ""
    if ev.get("series"):
        return False
    if BAD_Q.search(q) or BAD_SLUG.search(slug) or BAD_SLUG.search(ev_slug):
        return False
    if "up or down" in ev_slug.lower() or "up-or-down" in ev_slug.lower():
        return False
    if PRICE_Q.search(q) or PRICE_SLUG.search(slug) or PRICE_SLUG.search(ev_slug):
        return False
    if WEATHER.search(q) or WEATHER.search(ev_title):
        return False
    if ELECTION_DAY.search(q):
        return False
    return True


def slim(m):
    ev = (m.get("events") or [{}])[0]
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
        "event_slug": ev.get("slug"), "event_title": ev.get("title"),
        "orderMinSize": m.get("orderMinSize"),
        "dte": round(days_to_end(m) or -1, 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-pages", type=int, default=3000)
    args = ap.parse_args()

    ckpt = args.out + ".cursor"
    cursor = None
    if os.path.exists(ckpt):
        cursor = open(ckpt).read().strip() or None
        print("# resuming from checkpoint cursor", file=sys.stderr)

    base = {"limit": 100, "closed": "false", "volume_num_min": 1000}

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
                if r.status_code == 429:
                    time.sleep(5 * (retries + 1)); retries += 1; continue
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
                print(f"# page {pages}, kept {n_rows}/{n_seen} seen, {rate:.0f} mkts/s", file=sys.stderr)
            if not cursor:
                print(f"# done: no next_cursor at page {pages}", file=sys.stderr)
                break
            time.sleep(0.2)
    print(f"# TOTAL kept: {n_rows} of {n_seen} seen, pages: {pages} -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
