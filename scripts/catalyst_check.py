#!/usr/bin/env python3
"""Catalyst-calendar check for prospective bond-like longshot trades.

Spawns a `claude -p --model haiku` session with WebSearch + WebFetch enabled,
and asks it to identify catalysts in the resolution window that could shift
P(YES) above the base rate.

Triggered by the calibration miss on DEC-0016 (2026-05-08): I claimed
P(YES)=1% on aliens-by-May-31 NO without checking the news. The PURSUE UAP
disclosure program had launched the same day; market's 3% was correct or
slightly underpriced; I was wrong. A 5-minute web search would have caught
it. This script automates that check.

Usage:
    python scripts/catalyst_check.py "<market question>" <resolve_date_iso>

Examples:
    python scripts/catalyst_check.py \\
        "Will the US confirm that aliens exist by May 31, 2026?" 2026-05-31

    python scripts/catalyst_check.py \\
        "Will Reza Pahlavi lead Iran in 2026?" 2026-12-31

Output: text written to stdout, also appended to notes/catalyst_log.md.

Per philosophy edge source #1, bond-like fades require a *modelled* fair
value, not intuition. This script is the model.
"""

from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "notes" / "catalyst_log.md"


def _fetch_resolution_description(question: str) -> str | None:
    """Look up the market on Polymarket gamma-api and return its description.

    Why: lesson from 2026-05-08 US-invade-Iran NO check. Haiku read media
    framing ("invasion happened") and gave central 98% P(YES), but the
    literal resolution criteria says "intended to establish control" —
    a narrower bar. Without the literal text, haiku biases toward
    media-framed event descriptions. Injecting the description anchors
    the analysis on the actual oracle-resolution language.

    Returns the description string, or None on any failure (network,
    no match, etc.) — best-effort.
    """
    try:
        import httpx
        # Search by paginated active markets, pick best fuzzy match
        # on question. Keeps it simple — full text match is fine since
        # operator passes the exact market question.
        with httpx.Client(timeout=15.0) as c:
            # gamma-api caps pages at 100 regardless of limit, so paginate by 100
            # across the active universe with an early exit on match. The old
            # limit=500 + offset=page*500 stride skipped 80% of markets, so this
            # exact-question lookup silently missed anything outside the top ~600
            # by volume — and the resolution-criteria anchoring (the whole point of
            # this function) failed for exactly those less-traded markets.
            offset = 0
            while offset < 6000:
                r = c.get(
                    "https://gamma-api.polymarket.com/markets",
                    params={"closed": "false", "archived": "false", "active": "true",
                            "limit": 100, "offset": offset,
                            "order": "volume24hr", "ascending": "false"},
                )
                if r.status_code != 200:
                    break
                batch = r.json() or []
                if not batch:
                    break
                for m in batch:
                    if (m.get("question") or "").strip() == question.strip():
                        return (m.get("description") or "").strip() or None
                offset += len(batch)
        return None
    except Exception:
        return None


PROMPT_TEMPLATE = """You are doing a catalyst-calendar check for a Polymarket market.

Market question: {question}
Resolution date: {resolve_date} ({days_to_resolve} days from today {today_iso})
{resolution_block}

Task: identify catalysts in the {days_to_resolve}-day window that could shift P(YES) above the historical base rate. The point is to catch known catalysts (scheduled hearings, reports, deadlines, programs, elections, releases, deliverables) that might be priced into the market but missed by a naive analyst who relies on intuition.

**Critical: anchor your P(YES) on the LITERAL resolution-criteria language above (when present), not on media framing of the underlying event.** Lesson source: 2026-05-08 US-invade-Iran check returned 98% P(YES) on "ground operations occurred" media framing, but the literal criteria required "intended to establish control over any portion of Iran" — a narrower bar that punitive strikes / freedom-of-navigation / uranium-seizure don't satisfy. Market priced 22.5% YES, which was correct under strict reading. ALWAYS check the literal resolution language and flag if media catalysts don't meet the strict bar.

Steps:

1. Identify the entity / factor in the resolution criteria (e.g., "US confirms aliens" -> US government, AARO, Pentagon, congressional UAP committee).

2. Web-search for scheduled events / catalysts in the window. Search terms to try:
   - "<entity> <year> scheduled report"
   - "<entity> hearing <month> <year>"
   - "<entity> deadline" / "<entity> announcement"
   - Any specific keyword from the resolution criteria + the year/month

3. For each catalyst found, classify impact:
   - HIGH: directly resolves the market (e.g., a scheduled formal confirmation/announcement).
   - MEDIUM: materially shifts probability (e.g., a hearing that could lead to confirmation).
   - LOW: ambient pressure, unlikely to directly trigger resolution.

4. Note historical base rate from analogous cases or markets that have resolved.

4b. **If the resolution criteria implies a CONJUNCTION (e.g., "Will X lead Iran" requires regime fall AND X installed; "Will X be confirmed" requires a specific event AND oracle interpretation), break the joint probability into components and SHOW THE MULTIPLICATIVE BREAKDOWN explicitly.** Don't just give a single number — give P(component A) × P(component B | A) × ... = joint. This prevents the operator from double-discounting (a real error encountered 2026-05-08 on the Pahlavi market: haiku gave joint 14% but didn't show the breakdown, operator re-applied a conditional adjustment thinking it was unconditional).

5. Output a STRUCTURED REPORT in the following format. Be concise.

```
## CATALYST CHECK: <market question>

Resolution: <resolve_date> | Days: <N> | Today: <today_iso>

### Base rate
<one sentence on historical base rate for this kind of event in this kind of window>

### Catalysts in window
- [HIGH/MED/LOW] YYYY-MM-DD - <catalyst description> - <source URL>
- ...
(if none: "None identified.")

### Recent news (last 14d)
- <date> - <headline>: <one-line significance>
(if none material: "None material.")

### P(YES) estimate
- Low: X%
- Central: Y%
- High: Z%
- Reasoning: <1-3 sentences explaining the range>
- Multiplicative breakdown (if conjunction): P(A) × P(B|A) × ... = joint Y%

### Sources
- [Title](URL)
- ...
```

End with the report only. Do NOT add commentary outside the report. Be terse — the consumer of this output is an autonomous trader making sizing decisions.
"""



def _recent_alert_headlines(question: str, max_lines: int = 6) -> str | None:
    """Latest news_alerts.jsonl titles sharing keywords with the question.

    2026-06-12 lesson: the haiku's websearch lags breaking news by hours — twice
    in 24h it reasoned from a stale world-state (missed live strikes, then missed
    the deal-pivot). The alerts file has the freshest verified headlines; inject
    them so the model anchors on live state."""
    import json as _json
    import re as _re
    try:
        path = Path(__file__).resolve().parent.parent / "notes" / "news_alerts.jsonl"
        if not path.exists():
            return None
        stop = {"will", "the", "a", "an", "by", "in", "on", "of", "to", "and", "or",
                "before", "after", "2026", "2027", "x", "us", "any", "part"}
        qwords = {w for w in _re.findall(r"[a-z]+", question.lower()) if w not in stop and len(w) > 2}
        if not qwords:
            return None
        lines = path.read_text(errors="replace").splitlines()[-150:]
        hits = []
        for ln in lines:
            try:
                d = _json.loads(ln)
            except Exception:
                continue
            title = d.get("title") or ""
            twords = set(_re.findall(r"[a-z]+", title.lower()))
            if len(qwords & twords) >= 1:
                hits.append(f"- [{d.get('ts','?')}] {title[:140]}")
        if not hits:
            return None
        return "\n".join(hits[-max_lines:])
    except Exception:
        return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("question", help="The Polymarket market question, in quotes.")
    p.add_argument("resolve_date", help="Resolution date, ISO format YYYY-MM-DD.")
    p.add_argument("--model", default="haiku",
                   help="Claude model for the lookup (default: haiku — cheap/fast).")
    p.add_argument("--effort", default="medium",
                   help="Claude effort level (default: medium).")
    p.add_argument("--no-log", action="store_true",
                   help="Skip writing the result to notes/catalyst_log.md.")
    args = p.parse_args()

    try:
        resolve = datetime.date.fromisoformat(args.resolve_date)
    except ValueError as e:
        print(f"ERROR: bad resolve date: {e}", file=sys.stderr)
        return 2

    today = datetime.date.today()
    days = (resolve - today).days
    if days < 0:
        print(f"ERROR: resolution date {resolve} is in the past", file=sys.stderr)
        return 2

    # Best-effort fetch of the literal resolution description so haiku anchors
    # on oracle language, not media framing.
    resolution_description = _fetch_resolution_description(args.question)
    if resolution_description:
        resolution_block = f"\nLITERAL RESOLUTION CRITERIA (from Polymarket gamma-api):\n```\n{resolution_description}\n```\n"
        print(f"# resolution criteria fetched ({len(resolution_description)} chars)", file=sys.stderr)
    else:
        resolution_block = "\n(No literal resolution criteria fetched — analyze under reasonable strict interpretation of the question.)\n"
        print("# resolution criteria unavailable; haiku will use strict interpretation of question text", file=sys.stderr)

    headlines = _recent_alert_headlines(args.question)
    if headlines:
        resolution_block += (
            "\nLATEST VERIFIED HEADLINES (from the project's live news feed — your "
            "websearch may lag these; treat them as ground truth for current state):\n"
            + headlines + "\n")
        print(f"# injected {headlines.count(chr(10)) + 1} live headlines into prompt", file=sys.stderr)

    prompt = PROMPT_TEMPLATE.format(
        question=args.question,
        resolve_date=args.resolve_date,
        days_to_resolve=days,
        today_iso=today.isoformat(),
        resolution_block=resolution_block,
    )

    cmd = [
        "claude", "-p",
        "--model", args.model,
        "--effort", args.effort,
        "--allowed-tools", "WebSearch,WebFetch,Bash",
        "--permission-mode", "acceptEdits",
    ]

    print(f"# catalyst_check: {args.question}", file=sys.stderr)
    print(f"# resolve={args.resolve_date} ({days} days)  model={args.model}", file=sys.stderr)
    print(f"# spawning claude -p ...", file=sys.stderr)

    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        print("ERROR: claude -p timed out after 5 minutes", file=sys.stderr)
        return 3

    if r.returncode != 0:
        print(f"ERROR: claude -p exited {r.returncode}", file=sys.stderr)
        print(f"stderr: {r.stderr[:500]}", file=sys.stderr)
        return r.returncode

    output = r.stdout.strip()
    print(output)

    if not args.no_log:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(f"\n---\n\n## {ts} — catalyst_check\n\n")
            f.write(f"**Query:** `{args.question}` resolves {args.resolve_date} ({days}d)\n\n")
            f.write(output)
            f.write("\n")
        print(f"\n# logged to {LOG_PATH}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
