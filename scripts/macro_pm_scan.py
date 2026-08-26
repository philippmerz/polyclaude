#!/usr/bin/env python3
"""Macro market scanner — Polymarket FOMC/CPI/macro markets vs CME-implied.

⚠ V1 LIMITATION: --with-consensus (default ON for top-N) is UNRELIABLE.
The CME FedWatch tool is JavaScript-rendered; haiku WebFetch returns no
content. Haiku then hallucinates probabilities from its training data
(knowledge cutoff Feb 2025), producing meaningless deltas. Verified
2026-05-09 18:50 UTC: top result claimed +27.4pp delta vs CME, but
yesterday's catalyst_check had CME at 95.5% no-change (matched PM 97%).
Haiku's "70% no-change" today was hallucination.

V1 USAGE: run with --no-consensus flag. The macro-market DISCOVERY side
(filtering Polymarket macro markets by keyword + volume + window) works
fine; the consensus comparison is broken until v2.

V2 plan: parse CME Fed Funds futures (ZQ contract) prices directly from
MarketWatch / Yahoo / TradingView. Implied probability of each rate target
= computed from (current rate - futures-implied rate) / 0.25. No JS.

Polymarket has macro markets like:
- "Will the Fed cut rates by June?"
- "Will the Fed cut rates by 50bps in 2026?"
- "Will May CPI YoY be above 3%?"
- "Will US Q1 GDP contract?"

For Fed-rate-decision markets, CME Fed Funds futures imply probabilities of
each target-rate outcome at each FOMC meeting. CME data is sharp + liquid;
Polymarket prices for the same questions can diverge by 2-10pp from the
CME-implied prior, especially in the days leading up to FOMC meetings.

This script:
1. Fetches Polymarket macro markets in next 60 days (FOMC/CPI/jobs)
2. For each, extracts the relevant numerical hurdle (rate change, CPI %, etc.)
3. Spawns a scoped fast research worker to fetch CME-implied probability
   (CME FedWatch tool, CME Group rate probabilities) for the same outcome
4. Computes Polymarket-vs-CME delta in pp
5. Surfaces candidates with delta > 3pp + adequate liquidity

Lesson source: 2026-05-09 operator directive — apply the entire body of
theory. Derivatives-implied probabilities are the cleanest fair-value
benchmark for macro Polymarket markets. FedWatch is publicly free.

Usage:
    python scripts/macro_pm_scan.py
    python scripts/macro_pm_scan.py --days 60 --top-n 5
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys

import httpx

from agent_runtime import run_agent


def fetch_macro_markets(days: int = 60, min_vol: float = 30000) -> list[dict]:
    """Pull Polymarket macro markets resolving within `days`."""
    out = []
    seen = set()
    keywords_macro = [
        "fed", "fomc", "rate cut", "rate hike", "interest rate",
        "cpi", "inflation", "jobs report", "unemployment", "gdp",
        "recession", "fed chair", "powell", "warsh",
    ]
    cutoff = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
    with httpx.Client(timeout=20) as c:
        for page in range(8):
            try:
                r = c.get("https://gamma-api.polymarket.com/markets", params={
                    "closed": "false", "active": "true",
                    # gamma caps pages at 100; offset stride must match (else skips 80%).
                    "limit": 100, "offset": page * 100,
                    "order": "volume24hr", "ascending": "false",
                })
                r.raise_for_status()
            except Exception:
                continue
            data = r.json() or []
            if not data:
                break
            for m in data:
                mid = m.get("id")
                if not mid or mid in seen:
                    continue
                seen.add(mid)
                if m.get("umaResolutionStatus") in ("proposed", "disputed"):
                    continue
                q = (m.get("question") or "").lower()
                if not any(k in q for k in keywords_macro):
                    continue
                end = m.get("endDate") or ""
                try:
                    end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)
                    if end_dt > cutoff:
                        continue
                except Exception:
                    continue
                vol = float(m.get("volume24hr", 0) or 0)
                if vol < min_vol:
                    continue
                out.append(m)
    return out


def fetch_derivatives_implied(question: str, lim_days: float, timeout: int = 120) -> dict:
    """Spawn a fast scoped worker to fetch a macro implied probability.

    Returns {"implied_prob": float, "source": str, "confidence": "high|med|low",
             "note": str} or {"error": "..."}
    """
    prompt = f"""Find the derivatives-market implied probability for this macro question.

Market question: {question}
Resolves within: {lim_days:.1f} days

For Fed-rate questions: use CME FedWatch tool (cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html) which shows Fed Funds futures-implied probabilities of each target rate outcome at upcoming FOMC meetings.

For CPI / jobs / GDP questions: use derivatives-market or consensus-economist data. If only economist consensus is available (no derivatives), output that with confidence "med".

For other macro questions: search for relevant fixed-income or derivatives markets that imply this outcome.

DO NOT use Polymarket itself as a source — circular.

Output ONE line of JSON only:
{{"implied_prob": <0.0-1.0>, "source": "<CME FedWatch / Bloomberg consensus / etc, NOT Polymarket>", "confidence": "high|med|low", "note": "<one-sentence>"}}

If no derivatives/consensus signal:
{{"error": "<one-sentence reason>"}}

Be concise. ONE line only."""
    try:
        r = run_agent(prompt, profile="fast", effort="low", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": "agent timeout"}
    if r.returncode != 0:
        return {"error": f"agent exit {r.returncode}"}

    out = r.stdout.strip()
    m = re.search(r"\{[^{}]*\}", out)
    if not m:
        return {"error": "no JSON in agent output"}
    try:
        return json.loads(m.group(0))
    except Exception as e:
        return {"error": f"json parse: {e}"}


def main() -> int:
    p = argparse.ArgumentParser(description="Macro PM market scan vs derivatives-implied probabilities.")
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--top-n", type=int, default=5)
    p.add_argument("--min-vol", type=float, default=30000)
    p.add_argument("--threshold-pp", type=float, default=3.0,
                   help="Surface markets with delta > threshold_pp (default 3pp).")
    p.add_argument("--no-consensus", action="store_true",
                   help="Skip derivatives lookup; just list macro markets.")
    args = p.parse_args()

    print(f"# macro_pm_scan: pulling Polymarket macro markets resolving <={args.days}d", file=sys.stderr)
    markets = fetch_macro_markets(days=args.days, min_vol=args.min_vol)
    print(f"# {len(markets)} macro markets pass volume threshold", file=sys.stderr)

    rows = []
    for m in markets:
        try:
            prices = json.loads(m.get("outcomePrices", "[]")) if isinstance(m.get("outcomePrices"), str) else m.get("outcomePrices", [])
            yes = float(prices[0])
            no = float(prices[1])
        except Exception:
            continue
        end = m.get("endDate", "")
        try:
            end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)
            days = (end_dt - datetime.datetime.now(datetime.timezone.utc)).total_seconds() / 86400
        except Exception:
            days = 0
        if days <= 0:
            continue
        rows.append({
            "question": m.get("question", "?"),
            "slug": m.get("slug", ""),
            "yes": yes,
            "no": no,
            "vol24h": float(m.get("volume24hr", 0) or 0),
            "liq": float(m.get("liquidityNum", 0) or 0),
            "days": round(days, 2),
            "id": m.get("id"),
        })
    rows.sort(key=lambda r: -r["vol24h"])

    if args.no_consensus:
        for r in rows[: args.top_n * 4]:
            print(f"  YES@${r['yes']:.4f}  d={r['days']:.1f}  v24=${r['vol24h']:>7.0f}  {r['question'][:60]}")
        return 0

    print(f"# fetching derivatives-implied for top {args.top_n} (~30s each)...", file=sys.stderr)
    for i, r in enumerate(rows[: args.top_n]):
        cons = fetch_derivatives_implied(r["question"], r["days"])
        if "implied_prob" in cons:
            implied = float(cons["implied_prob"])
            r["implied"] = implied
            r["delta_pp"] = round((r["yes"] - implied) * 100, 2)
            r["source"] = cons.get("source", "?")[:30]
            r["confidence"] = cons.get("confidence", "?")
        else:
            r["implied"] = None
            r["delta_pp"] = None
            r["error"] = cons.get("error", "?")[:60]
        print(f"  [{i+1}/{args.top_n}] {r['question'][:50]}: "
              f"{'PM=' + str(round(r['yes'],3)) + ' impl=' + str(round(r['implied'],3)) + ' Δ=' + str(r['delta_pp']) + 'pp' if r.get('implied') else 'NO_IMPLIED: ' + r.get('error','?')[:40]}",
              file=sys.stderr)

    print(f"\n# top {args.top_n} macro candidates with derivatives-implied:")
    print(f"  {'PM_yes':<7} {'impl':<7} {'Δ_pp':<8} {'days':<5} {'vol24h':<8} {'source':<20} {'question'}")
    for r in rows[: args.top_n]:
        if r.get("implied"):
            actionable = "✓" if abs(r["delta_pp"]) >= args.threshold_pp else " "
            print(f"  {r['yes']:<7.3f} {r['implied']:<7.3f} {r['delta_pp']:>+5.1f}pp{actionable} {r['days']:<5.1f} ${r['vol24h']:<7.0f} {r['source']:<20} {r['question'][:50]}")
        else:
            print(f"  {r['yes']:<7.3f} {'?':<7}  -      {r['days']:<5.1f} ${r['vol24h']:<7.0f} ERR: {r.get('error','?')[:30]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
