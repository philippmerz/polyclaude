#!/usr/bin/env python3
"""Kimi K3 capability evaluation — January-decision evidence (2026-07-19).

Drives kimi-k3 through the polyclaude eval battery via the Moonshot API
(operator-provided key at ~/secrets/moonshot; NEVER printed). Two parts:

  A. TRAP BATTERY — 5 live markets whose correct assessment requires fresh
     news verification + exact criteria reading. I provide question, verbatim
     criteria, and live book; the model must verify world state (server-side
     $web_search builtin if supported) and give fair p + recommendation.
  B. SELECTIVITY TEST — 8 recent funnel candidates (criteria + price
     provided), exactly ONE of which has real instance edge per our own
     assessments; includes the win-assumed-carry bait. Rank by mispricing.

Output: /tmp/kimi_eval_result.md (same grading path as the tmux plan) plus
/tmp/kimi_eval_transcript.json (per-call tool-use log for the honesty grade).

Usage: kimi_eval_runner.py [--model kimi-k3] [--no-search]
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

import httpx

API = "https://api.moonshot.ai/v1"
KEY_PATH = Path.home() / "secrets" / "moonshot"
RESULT_PATH = Path("/tmp/kimi_eval_result.md")
TRANSCRIPT_PATH = Path("/tmp/kimi_eval_transcript.json")

MAX_ROUNDS = 12          # tool-call loop cap per question
MAX_TOKENS = 3000

PART_A_SLUGS = [
    "will-the-chicago-bears-leave-illinois-by-dec-31",
    "iran-charges-hormuz-fees-by-august-31-20260625175039062-177",
    "will-there-be-at-least-5000-cyclosporiasis-cases-in-the-uptspt-by-july-31-2026-20260715005153975",
    "will-apple-release-a-touchscreen-macbook-in-2026",
    "will-spacex-have-the-highest-ipo-market-cap-2026-516",
]

PART_B_SLUGS = [
    # exactly one of these carries real instance edge per our assessments
    # (deliberately not marked here to keep this file spoiler-free-ish; the
    # grader knows). Includes the gross-carry bait and efficient classes.
    "strait-of-hormuz-traffic-returns-to-normal-by-july-31",
    "tamas-sulyok-out-as-president-of-hungary-by-july-31-20260626200424352",
    "will-wti-reach-110-by-july-20-2026",
    "iran-leadership-change-by-july-31-20260629143932628",
    "will-france-send-warships-through-the-strait-of-hormuz-by-july-31-2026-20260701001952740",
    "will-60-ships-transit-the-strait-of-hormuz-on-any-day-by-july-31-2026-20260626152655082-171-832",
    "will-there-be-no-change-in-fed-interest-rates-after-the-july-2026-meeting",
    "will-prime-video-announce-a-new-project-at-sdcc-2026-20260713165131276",
]

A_PROMPT = """You are being evaluated as a research model for an autonomous prediction-market
trading system. Below is a live Polymarket market: its question, its VERBATIM resolution
criteria, and the current order book. Your job:
1. Verify the current real-world state with web search — cite source + date for every
   load-bearing fact. The resolution criteria wording is exact; read it precisely.
2. Give your fair probability of YES with one paragraph of reasoning.
3. Recommend BUY YES / BUY NO / SKIP at the current book prices.
4. Name the single biggest risk to your recommendation.
Be honest about anything you could not verify.

MARKET: {question}
END DATE: {end}
CRITERIA:
{description}

CURRENT BOOK: YES bid {yes_bid} / ask {yes_ask}  (NO is the complement)
"""

B_PROMPT = """You are screening candidates for a prediction-market trading system whose only
edge is CASE-BY-CASE instance mispricing (a market price that contradicts a verifiable
fact or a precise reading of the resolution criteria). Population patterns, "high APY"
on likely-to-win favorites, and efficient consensus markets are all NON-edges.

Below are 8 live Polymarket markets with verbatim criteria and current prices. Rank
them from MOST to LEAST attractive as an actual trade for that system, with 1-2
sentences each. State explicitly which ones you would NOT trade at all and why. Use
web search where a fact matters. At most 1-2 of these are genuinely attractive —
selectivity is the test.

{markets_block}
"""


def _key() -> str:
    return KEY_PATH.read_text().strip()


def _fetch_market(slug: str) -> dict | None:
    try:
        m = httpx.get("https://gamma-api.polymarket.com/markets",
                      params={"slug": slug}, timeout=20).json()
        if not m:
            return None
        m = m[0]
        toks = json.loads(m.get("clobTokenIds") or "[]")
        bid = ask = None
        if toks:
            b = httpx.get("https://clob.polymarket.com/book",
                          params={"token_id": toks[0]}, timeout=20).json()
            bid = max((float(x["price"]) for x in b.get("bids", [])), default=None)
            ask = min((float(x["price"]) for x in b.get("asks", [])), default=None)
        return {"slug": slug, "question": m.get("question"), "end": m.get("endDate"),
                "description": m.get("description"), "yes_bid": bid, "yes_ask": ask,
                "mid": m.get("outcomePrices")}
    except Exception as e:
        print(f"# fetch failed {slug}: {e}", file=sys.stderr)
        return None


def _ddg_search(query: str) -> str:
    """Local search fulfillment for the custom tool: DuckDuckGo lite scrape,
    top results as titles+snippets. Used because Moonshot's builtin
    $web_search echo round-trip 400s on kimi-k3 (works on k2.6 — verified
    2026-07-19); standard function-calling works fine on k3."""
    import re as _re
    try:
        r = httpx.get("https://html.duckduckgo.com/html/",
                      params={"q": query},
                      headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"},
                      timeout=25)
        titles = _re.findall(r'class="result__a"[^>]*>(.*?)</a>', r.text)
        snips = _re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', r.text)
        clean = lambda s: _re.sub(r"<[^>]+>", "", s).strip()
        out = []
        for i in range(min(6, len(titles))):
            sn = clean(snips[i]) if i < len(snips) else ""
            out.append(f"- {clean(titles[i])}: {sn[:300]}")
        return "\n".join(out) or "[no results]"
    except Exception as e:
        return f"[search failed: {e}]"


CUSTOM_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web. Returns top result titles and snippets.",
        "parameters": {"type": "object",
                       "properties": {"query": {"type": "string"}},
                       "required": ["query"]},
    },
}


def _chat(messages: list, model: str, use_search: bool, transcript: list,
          deadline: float | None = None) -> str:
    """Chat with tool-call loop; custom web_search fulfilled locally via DDG.

    deadline: optional wall-clock epoch-seconds cap. When set, the loop stops
    starting new rounds past it (2026-07-20: the Marvel advisor run hung ~10min
    in the search loop; a hang must never block a verified entry). On breach it
    forces one final no-tools completion so the caller still gets an answer.
    """
    headers = {"Authorization": f"Bearer {_key()}"}
    tools = [CUSTOM_SEARCH_TOOL] if use_search else None
    forced_final = False
    for round_i in range(MAX_ROUNDS):
        if not forced_final and deadline is not None and time.time() > deadline:
            # out of time: force ONE final no-tools completion so the caller
            # still gets an answer from whatever search context was gathered.
            tools = None
            forced_final = True
            messages.append({"role": "user", "content":
                             "TIME LIMIT REACHED — give your best answer NOW from "
                             "what you have; do not search further."})
            transcript.append({"deadline_hit": round_i})
        body = {"model": model, "messages": messages, "temperature": 1,
                "max_tokens": MAX_TOKENS}
        if tools:
            body["tools"] = tools
        r = httpx.post(f"{API}/chat/completions", headers=headers, json=body,
                       timeout=180)
        if r.status_code != 200:
            transcript.append({"error": r.text[:300]})
            return f"[API ERROR {r.status_code}: {r.text[:200]}]"
        d = r.json()
        choice = d["choices"][0]
        msg = choice["message"]
        usage = d.get("usage", {})
        transcript.append({"round": round_i, "finish": choice.get("finish_reason"),
                           "tool_calls": [tc["function"]["name"] for tc in (msg.get("tool_calls") or [])],
                           "tokens": usage.get("total_tokens")})
        if choice.get("finish_reason") == "tool_calls":
            # sanitize: resubmitting the raw message (with reasoning fields
            # etc.) trips "tokenization failed" — keep only the API shape
            messages.append({"role": "assistant",
                             "content": msg.get("content") or "",
                             "tool_calls": msg.get("tool_calls")})
            for tc in msg.get("tool_calls") or []:
                try:
                    q = json.loads(tc["function"]["arguments"]).get("query", "")
                except Exception:
                    q = ""
                result = _ddg_search(q) if q else "[bad arguments]"
                transcript.append({"search_query": q, "result_chars": len(result)})
                messages.append({"role": "tool", "tool_call_id": tc["id"],
                                 "name": tc["function"]["name"],
                                 "content": result})
            continue
        return msg.get("content") or "[empty]"
    return "[MAX ROUNDS exceeded]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="kimi-k3")
    ap.add_argument("--no-search", action="store_true")
    args = ap.parse_args()

    t0 = time.time()
    transcript: list = []
    out = [f"# Kimi eval result — model={args.model} — {datetime.datetime.utcnow().isoformat()}Z\n"]

    print(f"# Part A: {len(PART_A_SLUGS)} markets", file=sys.stderr)
    for slug in PART_A_SLUGS:
        mk = _fetch_market(slug)
        if not mk:
            out.append(f"\n## A: {slug}\n[market fetch failed]\n")
            continue
        prompt = A_PROMPT.format(**{k: mk.get(k) for k in
                                    ("question", "end", "description", "yes_bid", "yes_ask")})
        section_transcript: list = []
        ans = _chat([{"role": "user", "content": prompt}], args.model,
                    not args.no_search, section_transcript)
        transcript.append({"part": "A", "slug": slug, "calls": section_transcript})
        out.append(f"\n## A: {mk['question']}\n(book YES {mk['yes_bid']}/{mk['yes_ask']})\n\n{ans}\n")
        print(f"#   done {slug} ({len(section_transcript)} rounds)", file=sys.stderr)

    print("# Part B: selectivity ranking", file=sys.stderr)
    blocks = []
    for i, slug in enumerate(PART_B_SLUGS, 1):
        mk = _fetch_market(slug)
        if not mk:
            blocks.append(f"[{i}] {slug} — fetch failed")
            continue
        desc = (mk.get("description") or "")[:1200]
        blocks.append(f"[{i}] {mk['question']}\n  book YES {mk['yes_bid']}/{mk['yes_ask']} | ends {mk['end']}\n  criteria: {desc}\n")
    section_transcript = []
    ans = _chat([{"role": "user", "content": B_PROMPT.format(markets_block='\n'.join(blocks))}],
                args.model, not args.no_search, section_transcript)
    transcript.append({"part": "B", "calls": section_transcript})
    out.append(f"\n## B: selectivity ranking\n\n{ans}\n")

    mins = (time.time() - t0) / 60
    total_tokens = sum(c.get("tokens") or 0 for t in transcript for c in
                       (t.get("calls") or []) if isinstance(c, dict))
    out.append(f"\n## runner stats\nwall-clock: {mins:.1f} min; total tokens (billed): {total_tokens}\n")
    RESULT_PATH.write_text("\n".join(out))
    TRANSCRIPT_PATH.write_text(json.dumps(transcript, indent=1))
    print(f"# done in {mins:.1f} min, {total_tokens} tokens -> {RESULT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
