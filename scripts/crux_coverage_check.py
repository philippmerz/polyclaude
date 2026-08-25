#!/usr/bin/env python3
"""Does the news watcher cover every position I actually hold?

WHY THIS EXISTS (2026-08-14). Three separate news-coverage gaps have been found
on live positions, each one only because I happened to think of that market:

  * 2026-08-11 — HLE and Greenland cruxes: ZERO of 217 keywords matched either.
  * 2026-08-14 — the touchscreen-MacBook leg (largest position, catalyst three
    weeks out) had four keywords, all announcement PHRASINGS, none of which
    would fire on "MacBook Pro with touch display starts shipping" — and the
    market resolves on PURCHASABLE, not on unveiling.

Three instances found by hand is a class, not a coincidence. This checks the
whole book at once so a blind spot is discovered on a quiet tick rather than on
the morning the catalyst lands.

WHAT IT CATCHES: total absence — a held position with NO keyword that matches
its question at all. That is the severe, mechanical failure and it is exactly
what happened with HLE and Greenland.

WHAT IT CANNOT CATCH, stated plainly so the green light is not over-read:
PHRASING BRITTLENESS. The MacBook leg would have PASSED this check, because
'touchscreen macbook' does appear in its question — while still missing the
ship-date headline that actually decides the market. Judging whether a keyword
covers the RESOLUTION CRUX rather than merely the market's title needs a human
read of the criteria. So a clean run means "nothing is entirely unwatched", not
"coverage is adequate". The criteria-read rotation in position_state_audit is
where the crux itself gets re-examined.

Usage:
    python scripts/crux_coverage_check.py          # report
    python scripts/crux_coverage_check.py --quiet  # only failures
Exit code 1 if any live position has zero matching keywords.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import httpx

CONFIG_PATH = Path(__file__).resolve().parent / "news_watcher_config.json"

# Words too generic to count as coverage. A position "covered" only because the
# word "the" or "2026" appears in some keyword is not covered at all — and that
# false green light is the specific way this check could become worse than
# nothing, by converting an unknown risk into a believed-safe one.
STOP = {
    "will", "the", "a", "an", "of", "in", "on", "by", "be", "is", "are", "to",
    "for", "at", "and", "or", "any", "part", "before", "after", "than", "that",
    "this", "it", "its", "was", "were", "has", "have", "had", "not", "no",
    "yes", "score", "highest", "achieved", "released", "release", "2026",
    "2027", "january", "december", "president", "us", "new", "first", "more",
    "most", "least", "least", "up", "out", "with", "from", "as",
    # 2026-08-25: INCIDENTAL words — they appear in a market TITLE as structure
    # or timing, never as its subject, so a shared one is not evidence of
    # coverage. 'launch' is why three Metamask positions ("...one day after
    # LAUNCH") were reported COVERED by 'astra launch' / 'gpt-6 launch' while
    # the config held zero metamask keywords — ~$45 of false assurance.
    # NOTE what was tried and REJECTED first: scoring a word "generic" by how
    # many keywords contain it. That false-flagged Trump-out, because 'trump' is
    # frequent across my keywords precisely BECAUSE Trump matters to the book —
    # frequency conflates "common" with "uninformative". Entity words must stay
    # salient; only structural ones belong here.
    "launch", "launches", "launched", "debut", "debuts", "day", "days",
    "event", "above", "below", "higher", "lower", "one",
}


def _keywords() -> list[str]:
    cfg = json.loads(CONFIG_PATH.read_text())
    return [k.lower() for k in (cfg.get("tier1_keywords", []) + cfg.get("tier2_keywords", []))]


def _positions() -> list[dict]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import _paths as _secrets
    addr = json.loads(_secrets.path("POLYCLAUDE_WALLET").read_text())["address"]
    with httpx.Client(timeout=20.0) as c:
        r = c.get("https://data-api.polymarket.com/positions",
                  params={"user": addr.lower(), "limit": "100"})
        r.raise_for_status()
        return [p for p in r.json() if float(p.get("size", 0) or 0) > 0.5]


def _salient(question: str) -> set[str]:
    toks = re.findall(r"[a-z0-9']+", (question or "").lower())
    return {t for t in toks if t not in STOP and len(t) > 2}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--quiet", action="store_true", help="print only uncovered positions")
    args = ap.parse_args()

    kws = _keywords()
    try:
        positions = _positions()
    except Exception as e:
        print(f"crux_coverage_check: could not fetch positions ({str(e)[:60]})", file=sys.stderr)
        return 0          # never block a tick on an API hiccup

    uncovered = []
    for p in sorted(positions, key=lambda x: -float(x.get("currentValue", 0) or 0)):
        q = (p.get("title") or "").lower()
        sal = _salient(q)
        # A keyword covers this market if it appears in the question, or if any
        # of its own salient words does. Substring both ways: 'macbook' covers
        # "...touchscreen MacBook..." and 'touchscreen macbook' covers it too.
        # COVERAGE MATCH. A keyword covers this market if its full phrase is in
        # the question, or if they share a salient word. The salience STOP list
        # is what makes that sound — see below for why it grew on 2026-08-25.
        hits = [k for k in kws if k in q or (_salient(k) & sal)]
        val = float(p.get("currentValue", 0) or 0)
        if not hits:
            uncovered.append((val, p.get("title"), p.get("slug")))
            print(f"  !! UNWATCHED  ${val:7.2f}  {(p.get('title') or '')[:66]}")
        elif not args.quiet:
            print(f"     covered    ${val:7.2f}  {(p.get('title') or '')[:52]}  <- {hits[:3]}")

    if uncovered:
        tot = sum(v for v, _, _ in uncovered)
        print(f"\n{len(uncovered)} position(s) worth ${tot:.2f} have NO matching news keyword.")
        print("Add keywords to scripts/news_watcher_config.json (tier2 is LLM-triaged, "
              "so prefer a broad distinctive token over a clever phrase).")
        return 1
    if not args.quiet:
        print(f"\nAll {len(positions)} positions have at least one matching keyword.")
        print("NOTE: this proves nothing is UNWATCHED; it does not prove the keyword covers "
              "the RESOLUTION CRUX (the MacBook leg passed this check while missing its "
              "ship-date headline). Criteria-read rotation is the check for that.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
