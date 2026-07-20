#!/usr/bin/env python3
"""Kimi K3 adversarial second-opinion on a Polymarket entry thesis.

Validated 2026-07-19 (research/kimi_eval_2026-07-19/): kimi-k3 caught 3/3
trap markets, beat our own sweep agents on their stale-fact misses, and — the
decisive test — when handed the adversarial rejection of its OWN idea it
withdrew cleanly and corrected two of our overreaches. That earns it a standing
role: a ~$0.10-0.30 independent read BEFORE we pull the trigger on an entry,
especially the >$10 / new-class / structural ones that already warrant
skeptic+champion. It is a SECOND opinion, never the decider — our gate math
stands; kimi's job is to surface a fact or criteria-reading we missed.

Reuses the Moonshot harness primitives from kimi_eval_runner (custom web_search
tool fulfilled locally via DDG, because k3's builtin search 400s at the gateway).

CLI:
  kimi_advisor.py --slug <slug> --side NO --my-p 0.96 \
      --thesis "GPT-6 by Aug-31: no announcement exists, strict public-access bar"
  # or free-form:
  kimi_advisor.py --question "..." --side YES --my-p 0.55 --thesis "..." --criteria "..."
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kimi_eval_runner as _K  # _chat, _ddg_search, CUSTOM_SEARCH_TOOL, _fetch_market

# k3 reasons a lot; give the answer room + a longer HTTP timeout than the eval default
_K.MAX_TOKENS = 20000
# 10 rounds = ~6-8 searches, plenty for a second opinion and a tighter time
# bound than the eval's 18 (2026-07-20: paired with the wall-clock deadline so
# a hung advisor never blocks an entry).
_K.MAX_ROUNDS = 10
_orig_post = httpx.post
httpx.post = lambda *a, **kw: _orig_post(*a, **{**kw, "timeout": kw.get("timeout") or 600})

PROMPT = """You are an independent second opinion for an autonomous prediction-market trader.
Another agent wants to place this trade; your job is NOT to agree, it is to find any fact,
resolution-criteria nuance, or reasoning gap that would make the trade WRONG. Use web search
to verify current real-world state — cite source + date for every load-bearing fact.

MARKET: {question}
{criteria_block}
THE PROPOSED TRADE: BUY {side}, because — {thesis}
The trader's fair P(YES) estimate: {my_p_yes}

Deliver, concisely:
1. Your own fair P(YES) with one paragraph of reasoning, anchored on the LITERAL criteria.
2. Do you AGREE with BUY {side}, or not? If the criteria bar differs from the colloquial
   reading, say exactly how.
3. The single fact or nuance most likely to make this trade lose — the thing the trader may
   have missed. Be specific; if you can't find one, say so plainly (don't manufacture doubt).
4. Anything you could NOT verify.
Be honest and concrete. If the trade looks right, say it looks right."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None, help="gamma slug (auto-fills question + criteria)")
    ap.add_argument("--question", default=None)
    ap.add_argument("--criteria", default=None)
    ap.add_argument("--side", required=True, choices=["YES", "NO"])
    ap.add_argument("--my-p", type=float, required=True,
                    help="your P(the SIDE you are buying wins), 0-1")
    ap.add_argument("--thesis", required=True)
    ap.add_argument("--model", default="kimi-k3")
    ap.add_argument("--timeout", type=float, default=300.0,
                    help="wall-clock cap in seconds (default 300); on breach the "
                         "model gives its best answer from gathered context, never hangs")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    question, criteria = args.question, args.criteria
    if args.slug:
        mk = _K._fetch_market(args.slug)
        if mk:
            question = question or mk.get("question")
            criteria = criteria or mk.get("description")
    if not question:
        print("ERROR: need --slug or --question", file=sys.stderr)
        return 2

    # convert my_p (prob the bought side wins) → P(YES) for a shared frame
    my_p_yes = args.my_p if args.side == "YES" else round(1 - args.my_p, 4)
    criteria_block = f"RESOLUTION CRITERIA (verbatim):\n{criteria}\n" if criteria else \
        "(resolution criteria not supplied — reason from the question text under a strict reading)\n"

    prompt = PROMPT.format(question=question, criteria_block=criteria_block,
                           side=args.side, thesis=args.thesis, my_p_yes=my_p_yes)
    transcript: list = []
    t0 = time.time()
    print(f"# kimi_advisor: asking {args.model} for a second opinion on BUY {args.side} "
          f"@ P(YES)={my_p_yes}...", file=sys.stderr)
    # Hard wall-clock cap (2026-07-20): a hung advisor must NEVER block a
    # verified entry — the gate decides, this is only a second opinion.
    deadline = t0 + args.timeout
    try:
        ans = _K._chat([{"role": "user", "content": prompt}], args.model, True,
                       transcript, deadline=deadline)
    except Exception as e:
        ans = f"[ADVISOR UNAVAILABLE: {e} — proceed on your own gated analysis; do NOT treat absence of a second opinion as confirmation]"
    searches = [c.get("search_query") for c in transcript if c.get("search_query")]
    mins = (time.time() - t0) / 60

    if args.json:
        print(json.dumps({"opinion": ans, "searches": searches, "minutes": round(mins, 1)}))
    else:
        print(ans)
        print(f"\n# ({mins:.1f} min, {len(searches)} web searches: {searches})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
