#!/usr/bin/env python3
"""Multi-year-horizon thesis check for equity / crypto / tokenized-equity candidates.

Companion to catalyst_check.py (which targets event-driven Polymarket questions
with explicit oracle resolution). This script targets continuous markets with
no resolution date — multi-year holds where the question is "is the thesis
intact / accelerating / decaying" rather than "will event X happen by date Y."

Selection framework anchored on the 4-dimensional grid from
notes/longterm_watchlist.md: cyclical position / secular tailwind / specific
catalyst / margin of safety. Candidate must score on ≥3 of 4 strongly.

Usage:
    python scripts/longterm_check.py "<asset>" <asset_type> [--horizon-years N]

Examples:
    python scripts/longterm_check.py "Solana ($SOL)" crypto
    python scripts/longterm_check.py "Micron Technology ($MU)" equity
    python scripts/longterm_check.py "Arbitrum ($ARB)" crypto --horizon-years 3

Asset types: equity / crypto / tokenized-equity.

Output: structured markdown report; logged to notes/longterm_log.md.

Lesson source: 2026-05-08 user directive to scan multi-year generational-
mispricing candidates. catalyst_check.py couldn't be repurposed cleanly —
the P(YES)/resolution-criteria framing doesn't fit continuous markets.
"""

from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "notes" / "longterm_log.md"


PROMPT_TEMPLATE = """You are doing a multi-year-horizon thesis check for a long-term investment candidate.

Asset: {asset}
Asset type: {asset_type}
Horizon: {horizon_years} years from today {today_iso}

This is for `notes/longterm_watchlist.md` — generational-mispricing candidates that fit the 4-dimensional framework: cyclical position / secular tailwind / specific catalyst / margin of safety. Candidate must score on ≥3 of 4 strongly to merit watchlist inclusion.

Reference pattern: SanDisk 2023-2025 — memory-cycle bottom + AI-compute secular demand + Western-Digital-spinoff catalyst + balance-sheet margin of safety = generational return.

Task: web-search current state of the asset and produce a structured thesis-check report. Anchor on FACTS (current valuation, recent earnings, on-chain metrics, etc.) — not vibes. If the thesis can't be substantiated, say so.

Steps:

1. **Fetch current price + recent performance.** Use web search for: "<ticker> price", "<ticker> 1-year chart", "<asset> recent earnings". Note current vs 52-week high/low + 1-year return.

2. **Cyclical position assessment.** Where is this asset in its cycle? At/near multi-year bottom, mid-cycle, or topping? Cite specific evidence (industry cycle indicators, valuation multiples vs history, sentiment indicators).

3. **Secular tailwind identification.** What multi-year demand driver supports this asset? Is the driver intact, accelerating, or decaying? Cite recent data (e.g., AI capex growth rate, on-chain TVL trend).

4. **Catalyst window.** What specific event in the next {horizon_years} years could force re-rating? Scheduled or probable events: product launches, mainnet activations, regulatory shifts, M&A, spinoffs, supply-cycle inflections. Be specific on dates where known.

5. **Margin-of-safety check.** What bounds the downside if thesis is wrong? Strong balance sheet, profitable already, low debt, hard-asset backing, low entry multiple, network-effect moat?

6. **Risks (top 3).** What are the most likely thesis-breakers? Be honest — not bullish.

7. **Scenario probabilities** (5-year outcomes, sum to ~1.0):
   - Generational (10x+ from current entry): X%
   - Strong (3-5x): Y%
   - Modest (1.5-3x): Z%
   - Flat / mild loss (-30% to +50%): W%
   - Thesis broken (-50%+): V%

8. **Entry trigger.** What price or event would make this an actual entry? Now, on a specific dip, on a specific event?

9. **Watchlist verdict.** SCORE/4 on the framework + recommendation:
   - WATCH: keep on list, monitor for entry trigger
   - ENTER NOW: trigger met, size per Kelly/4 with downside scenario
   - PASS: <3/4 dimensions, drop from watchlist
   - FOLLOW-UP NEEDED: missing data, retry in N weeks

Output format:

```
## LONGTERM CHECK: {asset}

Date: {today_iso} | Type: {asset_type} | Horizon: {horizon_years}y

### Current state
<price + 1y return + valuation metric one-liner>

### Cyclical position
<one paragraph + evidence>

### Secular tailwind
<one paragraph + evidence>

### Catalyst window
- [HIGH/MED/LOW] YYYY-QQ — <description> — <source>
- ...

### Margin of safety
<one paragraph + concrete number/metric>

### Top 3 risks
1. <risk> — <how it breaks thesis>
2. ...

### 5-year scenario probabilities
- Generational (10x+): X%
- Strong (3-5x): Y%
- Modest (1.5-3x): Z%
- Flat (-30% to +50%): W%
- Thesis broken (-50%+): V%

### Entry trigger
<concrete entry price / event>

### Verdict: <SCORE/4> — <WATCH | ENTER NOW | PASS | FOLLOW-UP NEEDED>
<one-sentence reasoning>

### Sources
- [Title](URL)
- ...
```

End with the report only. Do NOT add commentary outside the report. Be concise but specific — the consumer makes capital-allocation decisions from this output.
"""


def main() -> int:
    p = argparse.ArgumentParser(description="Multi-year thesis check for long-term watchlist candidates.")
    p.add_argument("asset", help="Asset name + ticker, e.g., 'Solana ($SOL)' or 'Micron Technology ($MU)'.")
    p.add_argument("asset_type", choices=["equity", "crypto", "tokenized-equity"],
                   help="Asset class — informs the search/analysis approach.")
    p.add_argument("--horizon-years", type=int, default=3,
                   help="Investment horizon in years (default: 3).")
    p.add_argument("--model", default="haiku",
                   help="Claude model for the lookup (default: haiku — cheap/fast).")
    p.add_argument("--effort", default="medium",
                   help="Claude effort level (default: medium).")
    p.add_argument("--no-log", action="store_true",
                   help="Skip writing the result to notes/longterm_log.md.")
    args = p.parse_args()

    today = datetime.date.today()
    prompt = PROMPT_TEMPLATE.format(
        asset=args.asset,
        asset_type=args.asset_type,
        horizon_years=args.horizon_years,
        today_iso=today.isoformat(),
    )

    cmd = [
        "claude", "-p",
        "--model", args.model,
        "--effort", args.effort,
        "--allowed-tools", "WebSearch,WebFetch,Bash",
        "--permission-mode", "acceptEdits",
    ]

    print(f"# longterm_check: {args.asset}", file=sys.stderr)
    print(f"# type={args.asset_type} horizon={args.horizon_years}y model={args.model}", file=sys.stderr)
    print(f"# spawning claude -p ...", file=sys.stderr)

    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print("ERROR: claude -p timed out after 10 minutes", file=sys.stderr)
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
            f.write(f"\n---\n\n## {ts} — longterm_check\n\n")
            f.write(f"**Query:** `{args.asset}` ({args.asset_type}, {args.horizon_years}y horizon)\n\n")
            f.write(output)
            f.write("\n")
        print(f"\n# logged to {LOG_PATH}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
