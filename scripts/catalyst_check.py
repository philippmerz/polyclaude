#!/usr/bin/env python3
"""Catalyst-calendar check for prospective bond-like longshot trades.

Spawns a scoped research worker with web search enabled and asks it to identify
catalysts in the resolution window that could shift P(YES) above the base rate.

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

Use --facts-only when the primary analyst owns the forecast. This mode gathers
source evidence without delegating probabilities or investment decisions.
"""

from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

from agent_runtime import run_agent
from gamma_market_lookup import GammaLookupError, lookup_active_market

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "notes" / "catalyst_log.md"


def _fetch_resolution_description(question: str, slug: str | None = None) -> str:
    """Look up the market on Polymarket gamma-api and return its description.

    Why: lesson from 2026-05-08 US-invade-Iran NO check. The prior small-model check read media
    framing ("invasion happened") and gave central 98% P(YES), but the
    literal resolution criteria says "intended to establish control" —
    a narrower bar. Without the literal text, a model can bias toward
    media-framed event descriptions. Injecting the description anchors
    the analysis on the actual oracle-resolution language.

    Missing, ambiguous, partial, or malformed lookup state raises. A catalyst
    model without the literal oracle criteria is unsafe for a capital path.
    """
    market = (lookup_active_market(slug=slug) if slug
              else lookup_active_market(question=question))
    market_question = " ".join(str(market.get("question") or "").split()).casefold()
    if market_question != " ".join(question.split()).casefold():
        raise GammaLookupError(
            f"slug {slug!r} resolved to a different question; refusing criteria injection"
        )
    description = (market.get("description") or "").strip()
    if not description:
        raise GammaLookupError(
            f"matched market {market.get('id')} has no literal resolution description"
        )
    return description


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

2b. **For benchmark, leaderboard, rank, price, count, or other measurable-threshold
questions, search for ALREADY-EXISTING qualifying evidence before forecasting future
catalysts.** Start with the entity's official release notes / system card / filing and
the criteria's named resolution source. For benchmarks, search the exact benchmark name
plus every material configuration label (for example `with tools`, `no tools`, `Pro`,
reasoning effort, pass@k). Report the score and configuration together. Never turn the
maximum on one third-party tracker into a claim about the maximum on “any surface.” If
the evidence may predate market entry, use a dated archive capture where possible and
state whether the literal criteria allow that earlier observation to qualify. A result
that already satisfies the question is not a future catalyst and must be reflected in
the central estimate.

3. For each catalyst found, classify impact:
   - HIGH: directly resolves the market (e.g., a scheduled formal confirmation/announcement).
   - MEDIUM: materially shifts probability (e.g., a hearing that could lead to confirmation).
   - LOW: ambient pressure, unlikely to directly trigger resolution.

4. Note historical base rate from analogous cases or markets that have resolved.

4b. **If the resolution criteria implies a CONJUNCTION (e.g., "Will X lead Iran" requires regime fall AND X installed; "Will X be confirmed" requires a specific event AND oracle interpretation), break the joint probability into components and SHOW THE MULTIPLICATIVE BREAKDOWN explicitly.** Don't just give a single number — give P(component A) × P(component B | A) × ... = joint. This prevents the operator from double-discounting (a real error encountered 2026-05-08 on the Pahlavi market: an earlier check gave joint 14% but didn't show the breakdown, so the operator re-applied a conditional adjustment thinking it was unconditional).

4c. **The Central P(YES) MUST EQUAL the structured multiplicative-breakdown joint — not a separate "base-rate + crisis-multiplier" gut number.** If your narrative intuition differs from the structured product, the STRUCTURED BREAKDOWN WINS for any conjunctive or strict-criteria question; do NOT inflate the Central above it. Lesson source: the 2026-06-11 (DEC-0036) and 2026-06-26 (DEC-0041) Iran regime-fall checks BOTH returned a narrative central (18%, then 14%) materially ABOVE their own multiplicative breakdown (~3.6%), over-weighting topple-conditional chains during a war-escalation news cycle; the inflated central nearly drove an overcautious trim (DEC-0036 did, and lost ~$0.45). During crisis/escalation coverage the narrative pull is UP; the conjunctive product of components is the discipline that corrects it.

5. Output a STRUCTURED REPORT in the following format. Be concise.

```
## CATALYST CHECK: <market question>

Resolution: <resolve_date> | Days: <N> | Today: <today_iso>

### Base rate
<one sentence on historical base rate for this kind of event in this kind of window>

### Existing qualifying evidence
- <date> - <measurement + exact configuration> - <first-party or named-source URL>
(if the question is not measurable-threshold based: "Not applicable."; if it is and no
qualifying evidence exists: "None found after first-party + named-source sweep.")

### Catalysts in window
- [HIGH/MED/LOW] YYYY-MM-DD - <catalyst description> - <source URL>
- ...
(if none: "None identified.")

### Recent news (last 14d)
- <date> - <headline>: <one-line significance>
(if none material: "None material.")

### P(YES) estimate
- Low: X%
- Central: Y%   (for a conjunction/strict-criteria question this MUST equal the multiplicative-breakdown joint below)
- High: Z%
- Reasoning: <1-3 sentences explaining the range>
- Multiplicative breakdown (if conjunction): P(A) × P(B|A) × ... = joint Y%
- Reconciliation: if a narrative/gut central differs from the breakdown joint by >5pp, STATE the divergence explicitly and set the Central to the structured breakdown (the conjunctive product is the anchor; the narrative pull inflates during crisis coverage — see 4c).

### Sources
- [Title](URL)
- ...
```

End with the report only. Do NOT add commentary outside the report. Be terse — the consumer of this output is an autonomous trader making sizing decisions.
"""



FACTS_PROMPT_TEMPLATE = """Collect source facts for the primary analyst's catalyst check.

Market question: {question}
Resolution date: {resolve_date} ({days_to_resolve} days from today {today_iso})
{resolution_block}

Read the complete literal rule. Identify the exact entity, metric, geography,
date window, source, fallback and any already-existing qualifying evidence.
Check dated primary sources for current facts, scheduled events and contrary
evidence relevant to that rule. Earlier events can matter when the rule permits
them; market creation alone does not truncate an annual ranking window.

Return a concise source inventory: claim; event/publication/retrieval dates;
direct URL; whether you read the body or only an indexed excerpt; exact units
and configuration; failures, gaps and unresolved interpretations. Forecasts
published by a source must be labeled forecasts, not observations. Missing
retrievals and unrendered pages are not evidence of absence. News-feed titles
are unverified leads until their source and contract relevance are checked.

Do not estimate probabilities, rank or reject candidates, recommend an action,
or use market prices. The primary analyst alone performs those judgments.
"""


def _news_lead_block(headlines: str) -> str:
    return (
        "\nUNVERIFIED NEWS LEADS (title matches from the project's feed; verify "
        "the original source, date, entity and literal-rule relevance before "
        "using them as evidence; they may be stale or unrelated):\n"
        + headlines + "\n"
    )


def _recent_alert_headlines(question: str, max_lines: int = 6) -> str | None:
    """Latest news_alerts.jsonl titles sharing keywords with the question.

    2026-06-12 lesson: model web search can lag breaking news by hours — twice
    in 24h it reasoned from a stale world-state (missed live strikes, then missed
    the deal-pivot). Titles are leads, not verified facts; a keyword match does
    not establish source authenticity, recency or relevance to the contract."""
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
    p.add_argument("--window-start", default=None,
                   help="Creation/start metadata (ISO), applied when the literal rule "
                        "uses that start. It does not override an explicit annual window.")
    p.add_argument("--profile", choices=["research", "fast"], default="research",
                   help="Model workload profile (default: research).")
    p.add_argument("--slug", default=None,
                   help="Exact Gamma slug (preferred identity path; question is cross-checked).")
    p.add_argument("--effort", default="medium",
                   help="Reasoning effort level (default: medium).")
    p.add_argument("--no-log", action="store_true",
                   help="Skip writing the result to notes/catalyst_log.md.")
    p.add_argument("--facts-only", action="store_true",
                   help="Collect sourced facts only; the primary analyst retains "
                        "probabilities and investment decisions.")
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

    # Capital path: literal criteria are mandatory. Network/miss/ambiguity is
    # different from a complete exact miss, but both stop before model work.
    try:
        resolution_description = _fetch_resolution_description(args.question, args.slug)
    except GammaLookupError as exc:
        print(f"ERROR: literal resolution criteria lookup failed closed: {exc}",
              file=sys.stderr)
        return 2
    resolution_block = (
        "\nLITERAL RESOLUTION CRITERIA (from Polymarket gamma-api):\n```\n"
        f"{resolution_description}\n```\n"
    )
    print(f"# resolution criteria fetched ({len(resolution_description)} chars)",
          file=sys.stderr)

    headlines = _recent_alert_headlines(args.question)
    if headlines:
        resolution_block += _news_lead_block(headlines)
        print(f"# injected {headlines.count(chr(10)) + 1} live headlines into prompt", file=sys.stderr)

    if args.window_start:
        resolution_block += (
            f"\nCREATION/START METADATA supplied by the caller: {args.window_start}. "
            "Exclude earlier events only when the literal criteria require an "
            "on/after-creation or on/after-start event. An explicit annual ranking "
            "or other stated evidence window remains controlling; creation alone "
            "does not remove earlier events from that window. State any ambiguity.\n")

    template = FACTS_PROMPT_TEMPLATE if args.facts_only else PROMPT_TEMPLATE
    prompt = template.format(
        question=args.question,
        resolve_date=args.resolve_date,
        days_to_resolve=days,
        today_iso=today.isoformat(),
        resolution_block=resolution_block,
    )

    print(f"# catalyst_check: {args.question}", file=sys.stderr)
    print(f"# resolve={args.resolve_date} ({days} days)  profile={args.profile}", file=sys.stderr)
    print("# spawning scoped research worker ...", file=sys.stderr)

    try:
        r = run_agent(prompt, profile=args.profile, effort=args.effort, timeout=300)
    except subprocess.TimeoutExpired:
        print("ERROR: research worker timed out after 5 minutes", file=sys.stderr)
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
            f.write(f"\n---\n\n## {ts} — catalyst_check\n\n")
            f.write(f"**Query:** `{args.question}` resolves {args.resolve_date} ({days}d)\n\n")
            f.write(output)
            f.write("\n")
        print(f"\n# logged to {LOG_PATH}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
