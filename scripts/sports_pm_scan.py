#!/usr/bin/env python3
"""Sports-market scanner for Polymarket — surfaces short-tail trade candidates.

discover_markets.py covers the bond-like-fade lens (high APY tail). This script
adds a SPORTS-specific filter:
- Resolves within next 36-72h (matches <1y horizon)
- Liquid book (vol24h > $50k, liq > $10k)
- Categorizes by lens:
  - BOND_LIKE_FADE: dominant side > 0.93, decent APY
  - MID_50_50: 0.40 <= yes <= 0.60 (requires fair-value model to enter)
  - PROP_TAIL: extreme tails on prop bets (over/under, spread)
- Future v2: integrate bookie consensus odds via the-odds-api or similar to
  find Polymarket vs bookie-consensus deltas.

Operator directive 2026-05-09 ~17:10 UTC: aggressive engineering campaign
to recoup R-U drawdown via untapped sports + cross-venue alpha.

Usage:
    python scripts/sports_pm_scan.py
    python scripts/sports_pm_scan.py --hours 72
    python scripts/sports_pm_scan.py --json
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys

import re
import subprocess

import httpx


def fetch_bookie_consensus(question: str, lim_hours: float, timeout: int = 120) -> dict:
    """Spawn claude -p haiku with WebSearch to fetch bookie-consensus odds.

    Returns {"yes_prob": float, "source": str, "confidence": "high|med|low",
             "note": str} or {"error": "..."} on failure.

    Lesson source: 2026-05-09 operator directive — bookie consensus is the
    single biggest mid-market alpha signal; Polymarket vs sharps-book deltas
    > 3pp suggest mispricing. Cron-friendly via haiku (cheap/fast).
    """
    prompt = f"""Find the bookie-consensus implied probability for the following sports event/market.

Market question: {question}
Resolves within: {lim_hours:.1f} hours

Search public sportsbook aggregators (Pinnacle, DraftKings, FanDuel, Bet365, etc.) or odds-comparison sites (oddsportal.com, oddschecker, ESPN BetTrend) for the YES side implied probability.

Output ONE line of JSON only, no preamble:
{{"yes_prob": <0.0-1.0>, "source": "<which book or aggregator>", "confidence": "high|med|low", "note": "<one-sentence sanity check>"}}

If no consensus is fetchable (event too obscure, props market with no public odds, etc.), output:
{{"error": "<one-sentence reason>"}}

Be concise. ONE line only."""
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "haiku", "--effort", "low",
             "--allowed-tools", "WebSearch,WebFetch",
             "--permission-mode", "acceptEdits"],
            input=prompt, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"haiku timeout after {timeout}s"}
    if r.returncode != 0:
        return {"error": f"haiku exited {r.returncode}: {r.stderr[:100]}"}

    out = r.stdout.strip()
    # Extract first JSON object from the output (haiku may add commentary)
    m = re.search(r"\{[^{}]*\}", out)
    if not m:
        return {"error": "no JSON in haiku output"}
    try:
        import json as _json
        return _json.loads(m.group(0))
    except Exception as e:
        return {"error": f"json parse: {e}"}


def fetch_active_sports_markets(min_vol24: float = 30000, min_liq: float = 5000) -> list[dict]:
    out: list[dict] = []
    seen_ids: set[str] = set()
    with httpx.Client(timeout=20) as c:
        for page in range(6):
            try:
                r = c.get("https://gamma-api.polymarket.com/markets", params={
                    "closed": "false", "active": "true", "limit": 500,
                    "offset": page * 500,
                    "order": "volume24hr", "ascending": "false",
                })
                r.raise_for_status()
            except Exception as e:
                print(f"page {page} fetch err: {e}", file=sys.stderr)
                continue
            data = r.json() or []
            if not data:
                break
            for m in data:
                mid = m.get("id")
                if not mid or mid in seen_ids:
                    continue
                seen_ids.add(mid)
                if m.get("umaResolutionStatus") in ("proposed", "disputed"):
                    continue
                if not _is_sports(m):
                    continue
                vol = float(m.get("volume24hr", 0) or 0)
                liq = float(m.get("liquidityNum", 0) or 0)
                if vol < min_vol24 or liq < min_liq:
                    continue
                out.append(m)
    return out


def _is_sports(m: dict) -> bool:
    if m.get("sportsMarketType"):
        return True
    text = ((m.get("question") or "") + " " + (m.get("description") or "") + " " + (m.get("slug") or "")).lower()
    return any(k in text for k in [
        " vs. ", " vs ", "premier league", "serie a", "nba", "nfl", "nhl",
        "mlb", "uefa", "fifa", "ufc", "f1 ", "tennis", "match", "mls",
        "champions league", "atletico", "real madrid", "manchester",
        "lakers", "warriors", "celtics", "thunder", "pistons", "cavaliers",
    ])


def categorize(m: dict) -> tuple[str, float, float, float]:
    """Return (lens, yes_price, no_price, days_to_resolve)."""
    try:
        prices = json.loads(m.get("outcomePrices", "[]")) if isinstance(m.get("outcomePrices"), str) else m.get("outcomePrices", [])
        yes = float(prices[0])
        no = float(prices[1])
    except Exception:
        return "UNKNOWN", 0.0, 0.0, 0.0

    # Prefer endDate (datetime) over endDateIso (date-only); date-only collapses
    # same-day events to 00:00 UTC which is in the past for any afternoon scan.
    end = m.get("endDate") or m.get("endDateIso") or ""
    try:
        end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        days = (end_dt - now_dt).total_seconds() / 86400
    except Exception:
        days = 0.0

    if yes >= 0.93:
        lens = "BOND_LIKE_FADE_YES"
    elif no >= 0.93:
        lens = "BOND_LIKE_FADE_NO"
    elif 0.40 <= yes <= 0.60:
        lens = "MID_50_50"
    elif yes >= 0.85 or no >= 0.85:
        lens = "STRONG_FAVORITE"
    else:
        lens = "OTHER"
    return lens, yes, no, days


def annualized_apy(p: float, days: float, fee_rate: float = 0.072) -> float:
    """APY for hold-to-resolution at price p, days. Capped at 10000x for display."""
    if p >= 0.999 or days < 0.5:
        return 0.0
    fee = fee_rate * min(p, 1 - p)
    cost = p * (1 + fee)
    if cost >= 1.0:
        return 0.0
    gross = (1.0 - cost) / cost
    # Cap APY at 10000x (1,000,000%) to avoid overflow on sub-day windows.
    # For sub-day windows the APY math becomes meaningless anyway; absolute
    # return-per-dollar is the meaningful metric there.
    try:
        apy = (1.0 + gross) ** (365.0 / max(days, 0.5)) - 1.0
    except OverflowError:
        apy = 1e4
    return min(apy, 1e4)


def main() -> int:
    p = argparse.ArgumentParser(description="Sports-market scanner for Polymarket trade candidates.")
    p.add_argument("--hours", type=float, default=48,
                   help="Resolution-window cutoff hours (default 48).")
    p.add_argument("--min-vol24", type=float, default=30000)
    p.add_argument("--min-liq", type=float, default=5000)
    p.add_argument("--hurdle-apy", type=float, default=0.034,
                   help="Hurdle APY for bond-like-fade surfacing (default 3.4%%).")
    p.add_argument("--json", action="store_true")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--with-consensus", action="store_true",
                   help="Fetch bookie-consensus odds per top-5 candidate via "
                        "claude -p haiku WebSearch. Slower (~30s per market) "
                        "but surfaces Polymarket-vs-bookie pricing deltas.")
    p.add_argument("--consensus-top-n", type=int, default=5,
                   help="Number of top candidates to fetch consensus for "
                        "(default 5, to bound haiku token cost).")
    args = p.parse_args()

    print(f"# sports_pm_scan window=<={args.hours}h vol24h>=${args.min_vol24:.0f} liq>=${args.min_liq:.0f}", file=sys.stderr)

    markets = fetch_active_sports_markets(args.min_vol24, args.min_liq)
    print(f"# fetched {len(markets)} sports markets passing thresholds", file=sys.stderr)

    rows = []
    for m in markets:
        lens, yes, no, days = categorize(m)
        if days <= 0 or days * 24 > args.hours:
            continue
        # APY for the dominant side
        if yes >= no:
            apy = annualized_apy(yes, days)
            buy_side = "YES"
            mark = yes
        else:
            apy = annualized_apy(no, days)
            buy_side = "NO"
            mark = no
        rows.append({
            "question": m.get("question", "?"),
            "slug": m.get("slug", ""),
            "lens": lens,
            "yes": yes,
            "no": no,
            "buy_side": buy_side,
            "mark": mark,
            "apy_pct": apy * 100 if apy != float("inf") else float("inf"),
            "clears_hurdle": apy >= args.hurdle_apy if apy != float("inf") else True,
            "days_to_resolve": round(days, 2),
            "vol24h": float(m.get("volume24hr", 0) or 0),
            "liq": float(m.get("liquidityNum", 0) or 0),
            "id": m.get("id"),
            "tokens": m.get("clobTokenIds"),
        })

    rows.sort(key=lambda r: r["apy_pct"] if r["apy_pct"] != float("inf") else 9e9, reverse=True)
    rows = rows[: args.limit]

    # Fetch bookie consensus for top-N if requested
    if args.with_consensus:
        print(f"# fetching bookie consensus for top {args.consensus_top_n} candidates "
              f"(~30s each via haiku)...", file=sys.stderr)
        for i, r in enumerate(rows[: args.consensus_top_n]):
            cons = fetch_bookie_consensus(r["question"], r["days_to_resolve"] * 24)
            r["consensus"] = cons
            if "yes_prob" in cons:
                bookie_yes = float(cons["yes_prob"])
                pm_yes = r["yes"]
                # Delta: PM YES - bookie YES (positive = PM overprices YES)
                r["pm_vs_bookie_pp"] = round((pm_yes - bookie_yes) * 100, 2)
                r["consensus_summary"] = f"bookie={bookie_yes:.3f} delta={r['pm_vs_bookie_pp']:+.1f}pp ({cons.get('confidence','?')}/{cons.get('source','?')[:25]})"
            else:
                r["pm_vs_bookie_pp"] = None
                r["consensus_summary"] = f"NO_CONSENSUS: {cons.get('error', '?')[:60]}"
            print(f"  [{i+1}/{args.consensus_top_n}] {r['question'][:50]}: {r.get('consensus_summary','?')}", file=sys.stderr)

    if args.json:
        print(json.dumps({"results": rows}, indent=2, default=str))
        return 0

    print(f"\n# top {len(rows)} candidates (resolves <={args.hours}h):\n")
    for r in rows:
        # Profit per $1 if dominant side wins
        profit_per_dollar = (1.0 - r['mark']) / r['mark'] if r['mark'] > 0 else 0
        # APY display
        apy_pct = r['apy_pct']
        if apy_pct >= 1e6:
            apy_str = "  >1e6%"
        else:
            apy_str = f"{apy_pct:>9.1f}%"
        hurdle = "✓" if r['clears_hurdle'] else " "
        cons_str = ""
        if "consensus_summary" in r:
            cons_str = f"  {r['consensus_summary']}"
        print(f"  {r['lens']:20s} {r['buy_side']}@${r['mark']:.4f}  +{profit_per_dollar*100:5.2f}%  d={r['days_to_resolve']:.1f}  v24=${r['vol24h']:>7.0f}  {r['question'][:55]}{cons_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
