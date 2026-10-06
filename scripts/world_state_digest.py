#!/usr/bin/env python3
"""On-demand primary-source digest for project-relevant on-chain opportunities.

The old Sunday stock/brokerage rotation is retired. Select source domains only
for a held thesis, material trigger or concrete opportunity the project can
lawfully access. This catalog includes macro/industry facts because they can
inform Polymarket, crypto and named on-chain exposures, not a stock watchlist.

Example:
    python scripts/world_state_digest.py --domain crypto-on-chain
    python scripts/world_state_digest.py --domain macro-fiscal-labor,trade-regulation

No argument starts a default rotation. Findings are research inputs, not trading
or scheduling authority; reports are retained in notes/world_state_log.md.
"""

from __future__ import annotations

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

from agent_runtime import run_agent

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


PROMPT_TEMPLATE = """Produce a bounded primary-source digest for this investment project.
Date: {today_iso} | Domains: {domains_csv} | Lookback: {lookback_days} days

Source catalog:
{sources_block}

Scope: held-position catalysts and lawfully accessible on-chain opportunities,
with less-than-one-year holds and evaluation at the start of January 2027.
Off-chain stock picking, personal-brokerage watchlists/alerts and a recurring
Sunday domain rotation are retired. Do not propose restoring them or create a
catch-up task from historical research timestamps.

Read current primary sources. Date facts and distinguish announcements,
implemented state and economic results. Independently verify any factual
claim material to a position or allocation; a catalog or previous model digest
is not ground truth. Report source failures and gaps rather than filling them.

Infer candidate themes only when facts support an edge in a named instrument
that could be accessed on-chain. For each, identify the exact instrument,
chain/venue and access evidence, holder value-accrual mechanism, catalyst
before evaluation, current quote/depth and cost gaps, downside and model
uncertainty. An industry trend or cheap off-chain stock is not a project
candidate. Unknown route/access or executable economics must remain unverified;
no instrument may be recommended for execution from this report alone.

Output only:
# PROJECT WORLD-STATE DIGEST — {today_iso}
Domains: {domains_csv} | Lookback: {lookback_days}d
## PRIMARY FACTS
Group dated facts by domain, with primary-source links.
## PROJECT CANDIDATE THEMES
For each: underlying facts; named on-chain instrument/venue; causal mechanism;
catalyst/timeframe; net-cost and access evidence/gaps; confidence HIGH/MED/LOW.
A null result is valid. Do not create off-chain stock or brokerage candidates.
## BOUNDED NEXT STEPS
Name only justified, concrete follow-up for the held thesis or accessible
on-chain candidate. longterm_check.py accepts crypto/tokenized-equity/onchain
research within the project horizon; catalyst_check.py handles specific
Polymarket questions. Current candidate notes are notes/longterm_watchlist.md;
its old mixed archive is historical evidence. Do not schedule an idle follow-up.
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
    p.add_argument("--profile", choices=["research", "fast"], default="research",
                   help="Model workload profile (default: research).")
    p.add_argument("--effort", default="medium",
                   help="Reasoning effort level (default medium).")
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

    print(f"# world_state_digest: {len(selected)} domain(s): {', '.join(selected)}", file=sys.stderr)
    print(f"# lookback={args.lookback_days}d  profile={args.profile}  timeout={args.timeout}s", file=sys.stderr)
    print(f"# {sum(len(sources[d]) for d in selected)} sources in scope", file=sys.stderr)
    print("# spawning scoped research worker ...", file=sys.stderr)

    try:
        r = run_agent(prompt, profile=args.profile, effort=args.effort, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(f"ERROR: research worker timed out after {args.timeout}s", file=sys.stderr)
        return 3

    if r.returncode != 0:
        print(f"ERROR: research worker exited {r.returncode}", file=sys.stderr)
        print(f"stderr: {r.stderr[:500]}", file=sys.stderr)
        return r.returncode

    output = r.stdout.strip()
    print(output)

    if not args.no_log:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(f"\n---\n\n## {ts} — world_state_digest\n\n")
            f.write(f"**Domains:** {', '.join(selected)} | **Lookback:** {args.lookback_days}d | **Profile:** {args.profile}\n\n")
            f.write(output)
            f.write("\n")
        print(f"\n# logged to {LOG_PATH}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
