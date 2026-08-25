#!/usr/bin/env python3
"""Is a named resolution source actually UPDATING? Measure it, don't assume it.

WHY THIS EXISTS (2026-08-25). Several positions resolve on a named web source
(agi.safe.ai for the HLE cluster), and the whole thesis is "that source is
frozen". That claim was carried for weeks as an INFERENCE from what was missing
from the page. Inference is not measurement, and the market disagreed with me by
~65pp on exactly this variable — so it got measured: fetch the live page and an
archived snapshot, parse BOTH with ONE instrument, and diff.

THE STEP THAT MATTERS MOST IS --validate. A diff showing "no change" has two
causes: the source really is frozen, or the parser is blind (it reads a static
list, a JS bundle, or a cached shell). Those are indistinguishable from the
output alone, and the blind case argues FOR whatever you already believe. So
before trusting a no-change result, run the SAME parser across a window where
change is known to have happened; if it detects nothing there either, the
instrument is broken and the finding is void. On first use this converted "the
board looks stale" into a located change-point: additions in 2025-09 (gpt-5) and
2025-12 (gemini-3-pro, gpt-5-mini, plus five REMOVALS), then nothing at all
across 2026. Same shape as the empty-list lesson — absent output and broken
output look identical until you check against a known truth.

CLI:
  source_freeze_check.py --url https://agi.safe.ai/ --since 20260115
  source_freeze_check.py --url https://agi.safe.ai/ --validate 20250601 20251201
"""

from __future__ import annotations

import argparse
import re
import sys

import httpx

WAYBACK = "http://web.archive.org/web/{stamp}/{url}"
# Default: model-name shapes on AI leaderboards. Override with --pattern for
# other sources (registries, official lists, index pages).
# 2026-08-25: the first version required a HYPHEN (`claude-`, `grok-`) and was
# therefore BLIND to space-separated names — the live board lists "claude 4.5
# sonnet" and "grok 4". A blind pattern manufactures a false FROZEN verdict,
# which is the failure this tool exists to prevent, so the default now matches
# both spellings across every lab that appears on these boards.
DEFAULT_PATTERN = (r"gpt[\w.\-]{0,10}|gemini[\w.\- ]{0,10}pro"
                   r"|claude[\w.\- ]{0,16}(?:sonnet|opus|haiku)|grok[\w.\- ]{0,6}"
                   r"|deepseek[\w.\-]{0,10}|kimi[\w.\- ]{0,8}|llama[\w.\- ]{0,12}"
                   r"|qwen[\w.\-]{0,12}|o[34]-?\w*")


def tokens(html: str, pattern: str) -> set[str]:
    """Extract the comparable item set. ONE instrument, used on every side of
    every comparison — a differenced measurement means nothing if the two sides
    go through different parsers."""
    txt = re.sub(r"<[^>]+>", " ", html).lower()
    return {m.strip() for m in re.findall(pattern, txt) if m.strip()}


def fetch(client: httpx.Client, url: str, stamp: str | None) -> set[str] | None:
    target = WAYBACK.format(stamp=stamp, url=url) if stamp else url
    try:
        return tokens(client.get(target).text, PATTERN)
    except Exception as e:
        print(f"  fetch fail ({stamp or 'live'}): {type(e).__name__} {e}", file=sys.stderr)
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--url", required=True)
    ap.add_argument("--since", help="Wayback stamp (YYYYMMDD) to diff the LIVE page against")
    ap.add_argument("--validate", nargs=2, metavar=("EARLY", "LATE"),
                    help="two stamps spanning a period where change is KNOWN to have "
                         "occurred; proves the parser can see change at all")
    ap.add_argument("--pattern", default=DEFAULT_PATTERN)
    a = ap.parse_args()
    global PATTERN
    PATTERN = a.pattern

    with httpx.Client(timeout=60, follow_redirects=True) as c:
        if a.validate:
            early, late = (fetch(c, a.url, s) for s in a.validate)
            if early is None or late is None:
                print("VALIDATION INCONCLUSIVE — a snapshot could not be fetched")
                return 2
            moved = (late - early) | (early - late)
            print(f"[validate {a.validate[0]} -> {a.validate[1]}] "
                  f"added {sorted(late - early)} removed {sorted(early - late)}")
            print("INSTRUMENT VALID — the parser detects real change" if moved else
                  "!! INSTRUMENT SUSPECT — no change detected across a window that should "
                  "contain some; treat any freeze finding as VOID until the pattern is fixed")
            if not moved:
                return 1

        if a.since:
            live, old = fetch(c, a.url, None), fetch(c, a.url, a.since)
            if live is None or old is None:
                return 2
            added, removed = sorted(live - old), sorted(old - live)
            print(f"[live vs {a.since}] added {added or 'NONE'} | removed {removed or 'NONE'}")
            print(f"  live set ({len(live)}): {sorted(live)}")
            if not added and not removed:
                print("VERDICT: FROZEN over this window (run --validate before trusting it)")
            else:
                print("VERDICT: source is UPDATING — any freeze-based thesis needs re-pricing")
    return 0


if __name__ == "__main__":
    PATTERN = DEFAULT_PATTERN
    sys.exit(main())
