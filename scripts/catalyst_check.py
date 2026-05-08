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


PROMPT_TEMPLATE = """You are doing a catalyst-calendar check for a Polymarket market.

Market question: {question}
Resolution date: {resolve_date} ({days_to_resolve} days from today {today_iso})

Task: identify catalysts in the {days_to_resolve}-day window that could shift P(YES) above the historical base rate. The point is to catch known catalysts (scheduled hearings, reports, deadlines, programs, elections, releases, deliverables) that might be priced into the market but missed by a naive analyst who relies on intuition.

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

    prompt = PROMPT_TEMPLATE.format(
        question=args.question,
        resolve_date=args.resolve_date,
        days_to_resolve=days,
        today_iso=today.isoformat(),
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
