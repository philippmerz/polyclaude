#!/usr/bin/env python3
"""World-state digest: pull bare facts from primary sources, distill underpriced themes.

Companion to longterm_check.py and catalyst_check.py.

- catalyst_check.py: targeted vetting of a single Polymarket question with a
  known oracle resolution.
- longterm_check.py: targeted vetting of a single asset (equity/crypto) for
  multi-year-horizon thesis intactness.
- world_state_digest.py: BROAD discovery — pulls factual updates from
  primary sources (no narrative filter), distills "what's underpriced given
  these facts", outputs candidate list.

Pipeline:
  primary_sources.md (curated factual URLs by domain)
    -> world_state_digest.py (this) -> raw fact aggregation + synthesis
    -> candidate list (printed + appended to notes/world_state_log.md)
    -> longterm_check.py for individual-ticker vetting
    -> notes/longterm_watchlist.md for active monitoring

Usage:
    python scripts/world_state_digest.py --domain energy
    python scripts/world_state_digest.py --domain "energy,critical-minerals,trade"
    python scripts/world_state_digest.py --all  # all domains

Lesson source: 2026-05-08 user articulation — retail relies on pre-made
inferences from outlets; LLM operating on bare facts has structural edge
because it skips the narrative-compression layer. This script operationalizes
that edge by reading FACTS not COMMENTARY.
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_PATH = REPO_ROOT / "notes" / "primary_sources.md"
LOG_PATH = REPO_ROOT / "notes" / "world_state_log.md"


def parse_sources() -> dict[str, list[tuple[str, str]]]:
    """Parse notes/primary_sources.md into {domain_slug: [(name, url), ...]}.

    Sections are headed `## Domain: <name>`; bullet lines have shape
    `- **NAME** ... — <description>: <URL>`. Robust to minor formatting drift.
    """
    text = SOURCES_PATH.read_text()
    domains: dict[str, list[tuple[str, str]]] = {}
    current: str | None = None
    for line in text.splitlines():
        m = re.match(r"^##\s+Domain:\s+(.+?)\s*$", line)
        if m:
            current = m.group(1).strip().lower().replace(" / ", "-").replace(" ", "-")
            domains[current] = []
            continue
        if current is None:
            continue
        # bullet form: - **NAME** ... <URL>
        if line.startswith("- "):
            urls = re.findall(r"https?://[^\s)\]]+", line)
            name_m = re.search(r"\*\*([^*]+)\*\*", line)
            if urls and name_m:
                for url in urls:
                    domains[current].append((name_m.group(1).strip(), url))
    return domains


PROMPT_TEMPLATE = """You are doing a WORLD-STATE FACT DIGEST — pulling bare facts from primary sources to identify mispriced asset categories.

Today: {today_iso}
Domains: {domains_csv}
Lookback: last {lookback_days} days

You have WebSearch + WebFetch. Tools available: pull each source URL, extract recent FACTUAL updates (numerical data, official statements, regulatory filings, primary statistics — not editorial framing).

The principle is structural: retail relies on pre-made inferences from outlets (3-4 layers of narrative compression). You operate on bare facts and skip the narrative step. Your edge is reading the BLS jobs report directly, not "what the WSJ said about the BLS report".

Sources to consult (curated primary sources for the selected domains):

{sources_block}

## Your task

1. **Fetch + extract facts.** For each source above, fetch the latest few news/release pages and extract the most material FACTUAL updates from the last {lookback_days} days. For each fact: cite the source, give the date, give the raw number/statement.

   Be ruthless about facts vs framing. "Q1 GDP grew 1.4% annualized" is a fact. "Economy disappoints expectations" is framing — IGNORE.

   You don't need to hit every source — prioritize sources that yield material recent updates. Skip ones that 404 or have no recent material.

2. **Aggregate into a bare-fact snapshot.** Organize by domain. Group related facts. Note when multiple sources confirm the same trend.

3. **Synthesize: what's underpriced given THESE facts?** Now apply first-principles inference. Given the bare facts, what asset categories or specific tickers should be mispriced?

   For each candidate:
   - Asset (specific ticker if equity/crypto; category if too early)
   - Mechanism: which fact(s) drive the mispricing? Be specific.
   - Direction: long / short
   - Time horizon: weeks / months / years
   - Why retail might miss it: what narrative-layer obscuring is happening?
   - Confidence: HIGH / MEDIUM / LOW (only HIGH if multiple independent facts converge)

   Only include candidates where the FACTS support the thesis. If the digest yields no high-conviction candidates, say so — null result is fine.

4. **Cross-reference.** If any candidate is in the existing `notes/longterm_watchlist.md` (don't read it — just flag if you recall the obvious ones), note that for downstream filtering.

## Output format

```
# WORLD-STATE DIGEST — {today_iso}

Domains: {domains_csv}  |  Lookback: {lookback_days}d

## BARE FACTS (by domain)

### <Domain 1>
- [YYYY-MM-DD] <Source>: <raw factual statement with number/specific>
- ...

### <Domain 2>
- ...

## CANDIDATE THEMES

### <Theme name>
- Underlying facts: <which fact(s) from above>
- Implication: <first-principles inference>
- Possible plays: <ticker(s) / category>
- Direction: long/short
- Horizon: weeks/months/years
- Retail blindspot: <why this isn't priced>
- Confidence: HIGH/MED/LOW

### <Theme name 2>
...

## NEXT-STEPS

- Run longterm_check.py on: <ticker1>, <ticker2>, ...
- Run catalyst_check.py on: <Polymarket question 1>, ... (if any)
- Skip / pass: <list any themes that look interesting but factual basis is too thin>
```

End with the report only. No preamble, no commentary outside the report. Be terse but specific — this output feeds downstream tooling that vets individual names.
"""


def build_sources_block(selected_domains: list[str], all_sources: dict[str, list[tuple[str, str]]]) -> str:
    """Render the source list for selected domains."""
    out: list[str] = []
    for d in selected_domains:
        srcs = all_sources.get(d, [])
        if not srcs:
            continue
        out.append(f"### {d}")
        for name, url in srcs:
            out.append(f"- {name}: {url}")
        out.append("")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description="World-state fact digest from primary sources.")
    p.add_argument("--domain", default=None,
                   help="Comma-separated domain slugs (e.g. 'energy,trade'). See primary_sources.md headings.")
    p.add_argument("--all", action="store_true",
                   help="Run against all domains. Token-heavy — prefer per-domain scoped runs.")
    p.add_argument("--lookback-days", type=int, default=30,
                   help="How far back to look for facts (default 30).")
    p.add_argument("--model", default="haiku",
                   help="Claude model (default haiku — cheap/fast for fact extraction).")
    p.add_argument("--effort", default="medium",
                   help="Claude effort level (default medium).")
    p.add_argument("--list-domains", action="store_true",
                   help="List available domain slugs and exit.")
    p.add_argument("--no-log", action="store_true",
                   help="Skip writing the result to notes/world_state_log.md.")
    p.add_argument("--timeout", type=int, default=900,
                   help="Subprocess timeout seconds (default 900 = 15 min).")
    args = p.parse_args()

    sources = parse_sources()
    if not sources:
        print("ERROR: parsed 0 domains from primary_sources.md", file=sys.stderr)
        return 2

    if args.list_domains:
        print("Available domain slugs:")
        for d, srcs in sources.items():
            print(f"  {d:32s} ({len(srcs)} sources)")
        return 0

    if args.all:
        selected = list(sources.keys())
    elif args.domain:
        raw = [d.strip().lower() for d in args.domain.split(",") if d.strip()]
        selected = []
        for r in raw:
            # accept exact match or substring match
            matched = [d for d in sources.keys() if d == r or r in d]
            if not matched:
                print(f"WARN: no domain matches '{r}'. Available: {list(sources.keys())}", file=sys.stderr)
                continue
            selected.extend(matched)
        selected = list(dict.fromkeys(selected))  # dedup, preserve order
    else:
        print("ERROR: provide --domain <slug[,slug2]> or --all", file=sys.stderr)
        return 2

    if not selected:
        print("ERROR: no valid domains selected", file=sys.stderr)
        return 2

    today = datetime.date.today()
    sources_block = build_sources_block(selected, sources)
    prompt = PROMPT_TEMPLATE.format(
        today_iso=today.isoformat(),
        domains_csv=", ".join(selected),
        lookback_days=args.lookback_days,
        sources_block=sources_block,
    )

    cmd = [
        "claude", "-p",
        "--model", args.model,
        "--effort", args.effort,
        "--allowed-tools", "WebSearch,WebFetch,Bash",
        "--permission-mode", "acceptEdits",
    ]

    print(f"# world_state_digest: {len(selected)} domain(s): {', '.join(selected)}", file=sys.stderr)
    print(f"# lookback={args.lookback_days}d  model={args.model}  timeout={args.timeout}s", file=sys.stderr)
    print(f"# {sum(len(sources[d]) for d in selected)} sources in scope", file=sys.stderr)
    print(f"# spawning claude -p ...", file=sys.stderr)

    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f"ERROR: claude -p timed out after {args.timeout}s", file=sys.stderr)
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
            f.write(f"\n---\n\n## {ts} — world_state_digest\n\n")
            f.write(f"**Domains:** {', '.join(selected)} | **Lookback:** {args.lookback_days}d | **Model:** {args.model}\n\n")
            f.write(output)
            f.write("\n")
        print(f"\n# logged to {LOG_PATH}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
