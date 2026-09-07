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

2026-09-07: the default for agi.safe.ai now compares EVERY results-table row,
including both displayed numeric columns. The old whole-page name regex missed
Flash/o1, included prose-only names and could not detect a score-only revision.
Other URLs and custom --pattern uses retain explicitly labeled token-only mode.
An unchanged table is not evidence that the dataset, prose or institution is idle.

CLI:
  source_freeze_check.py --url https://agi.safe.ai/ --since 20260115
  source_freeze_check.py --url https://agi.safe.ai/ --validate 20250601 20251201
"""

from __future__ import annotations

import argparse
from decimal import Decimal
from html.parser import HTMLParser
import re
import sys
from urllib.parse import urlsplit

import httpx

WAYBACK = "https://web.archive.org/web/{stamp}/{url}"
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
PATTERN = DEFAULT_PATTERN
Inventory = set[str] | dict[str, tuple[str, str]]


class _Tables(HTMLParser):
    """Read explicit table cells without a model-name allowlist.

    Incomplete/nested markup is an inconclusive fetch, never an empty diff.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.table = None
        self.row = None
        self.cell = None
        self.cell_tag = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            if self.table is not None:
                raise ValueError("nested results table")
            self.table = []
        elif tag == "tr" and self.table is not None:
            if self.row is not None:
                raise ValueError("unclosed table row")
            self.row = []
        elif tag in ("td", "th") and self.table is not None:
            if self.row is None or self.cell is not None:
                raise ValueError("malformed table cell")
            self.cell = []
            self.cell_tag = tag

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.table is not None:
            if self.cell is None or self.row is None or tag != self.cell_tag:
                raise ValueError("unmatched table cell")
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
            self.cell_tag = None
        elif tag == "tr" and self.table is not None:
            if self.row is None or self.cell is not None:
                raise ValueError("incomplete table row")
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            if self.row is not None or self.cell is not None:
                raise ValueError("incomplete results table")
            self.tables.append(self.table)
            self.table = None


def hle_results(html: str) -> dict[str, tuple[str, str]]:
    """All model rows, accuracy AND calibration, from the named HLE table.

    Names in prose are not rows; new naming families and score-only changes
    must remain visible. Unknown schemas/invalid/duplicate rows fail closed.
    """
    parser = _Tables()
    parser.feed(html)
    parser.close()
    if parser.table is not None:
        raise ValueError("unclosed results table")
    expected = ["model", "accuracy", "calibrationerror"]
    tables = [t for t in parser.tables if t and
              [re.sub(r"[^a-z]", "", c.lower()) for c in t[0]] == expected]
    if len(tables) != 1:
        raise ValueError("expected exactly one recognizable HLE results table")

    def score(cell: str, *, missing_ok: bool = False) -> str:
        if missing_ok and cell in ("", "-"):
            return "-"  # 2025 snapshots use both blank and '-' for missing calibration.
        value = cell.removesuffix("%").strip()
        if not re.fullmatch(r"\d+(?:\.\d+)?", value):
            raise ValueError(f"invalid result value: {cell!r}")
        number = Decimal(value)
        if not 0 <= number <= 100:
            raise ValueError("result outside percentage range")
        return format(number.normalize(), "f")

    rows = {}
    for cells in tables[0][1:]:
        if len(cells) != 3 or not cells[0]:
            raise ValueError("incomplete HLE result row")
        name = cells[0].casefold()
        if name in rows:
            raise ValueError(f"duplicate model row: {name}")
        rows[name] = (score(cells[1]), score(cells[2], missing_ok=True))
    if not rows:
        raise ValueError("empty HLE results table")
    return rows


def uses_hle_results(url: str) -> bool:
    target = urlsplit(url)
    return (target.hostname == "agi.safe.ai" and target.path in ("", "/")
            and PATTERN == DEFAULT_PATTERN)


def differences(old: Inventory, new: Inventory) -> tuple[list, list, list]:
    if type(old) is not type(new):
        raise ValueError("inconsistent inventory types")
    changed = ([(name, old[name], new[name]) for name in sorted(set(old) & set(new))
                if old[name] != new[name]] if isinstance(old, dict) else [])
    return sorted(set(new) - set(old)), sorted(set(old) - set(new)), changed


def tokens(html: str, pattern: str) -> set[str]:
    """Extract the comparable item set. ONE instrument, used on every side of
    every comparison — a differenced measurement means nothing if the two sides
    go through different parsers."""
    txt = re.sub(r"<[^>]+>", " ", html).lower()
    return {m.strip() for m in re.findall(pattern, txt) if m.strip()}


def fetch(client: httpx.Client, url: str, stamp: str | None) -> Inventory | None:
    target = WAYBACK.format(stamp=stamp, url=url) if stamp else url
    try:
        response = client.get(target)
        response.raise_for_status()
        parsed = (hle_results(response.text) if uses_hle_results(url)
                  else tokens(response.text, PATTERN))
        # Fail closed. Wayback occasionally returns a successful-looking empty
        # shell (or an upstream error body); treating that as a real empty
        # inventory can manufacture either FROZEN or a complete-removal event.
        if not parsed:
            raise ValueError("parser returned an empty inventory")
        return parsed
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
    ap.add_argument("--pattern", default=DEFAULT_PATTERN,
                    help="non-default regex uses token-only mode; default on agi.safe.ai "
                         "compares every result row and both score columns")
    ap.add_argument("--expect", default=None,
                    help="comma-separated substrings that MUST appear in the live parse "
                         "(e.g. 'claude,grok'). --validate only proves the parser sees SOME "
                         "change; it cannot prove the parser sees EVERYTHING, and a partially "
                         "blind parser still returns FROZEN. On 2026-08-25 --validate passed "
                         "while the pattern was blind to space-separated names, and the gap was "
                         "caught only by cross-checking a known inventory. This is that check, "
                         "mechanised.")
    a = ap.parse_args()
    global PATTERN
    PATTERN = a.pattern
    table_mode = uses_hle_results(a.url)
    print("[mode] HLE results table: all model rows + accuracy + calibration" if table_mode else
          "[mode] regex tokens only: no claim about scores or whole-page stasis")

    # Wayback intermittently returns 503 to the library default user-agent
    # while serving the same capture to a normal browser/curl client.
    with httpx.Client(timeout=60, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0 (polyclaude source monitor)"}) as c:
        if a.validate:
            early, late = (fetch(c, a.url, s) for s in a.validate)
            if early is None or late is None:
                print("VALIDATION INCONCLUSIVE — a snapshot could not be fetched")
                return 2
            # A known-change control should retain at least one anchor item.
            # Disjoint sets are indistinguishable from a partially fetched/error
            # snapshot and must not be allowed to certify the instrument.
            if not set(early).intersection(late):
                print("VALIDATION INCONCLUSIVE — snapshots share no parsed anchor; "
                      "cannot distinguish wholesale change from a partial/error page")
                return 2
            added, removed, changed = differences(early, late)
            moved = added or removed or changed
            print(f"[validate {a.validate[0]} -> {a.validate[1]}] "
                  f"added {added} removed {removed} changed {changed}")
            print("INSTRUMENT VALID — the parser detects real change" if moved else
                  "!! INSTRUMENT SUSPECT — no change detected across a window that should "
                  "contain some; treat any freeze finding as VOID until the pattern is fixed")
            if not moved:
                return 1

        if a.since:
            live, old = fetch(c, a.url, None), fetch(c, a.url, a.since)
            if live is None or old is None:
                return 2
            if a.expect:
                blob = " ".join(sorted(live))
                missing = [e.strip() for e in a.expect.split(",")
                           if e.strip() and e.strip().lower() not in blob]
                if missing:
                    print(f"!! PARSER INCOMPLETE — expected but not found: {missing}. "
                          f"A blind parser returns FROZEN for the wrong reason; widen --pattern "
                          f"before believing any verdict below.")
                    return 1
                print(f"[coverage] all expected items present: {a.expect}")
            added, removed, changed = differences(old, live)
            print(f"[live vs {a.since}] added {added or 'NONE'} | removed {removed or 'NONE'} "
                  f"| changed {changed or 'NONE'}")
            print(f"  live inventory ({len(live)}): "
                  f"{dict(sorted(live.items())) if isinstance(live, dict) else sorted(live)}")
            if not added and not removed and not changed:
                subject = "RESULTS TABLE" if table_mode else "REGEX TOKEN SET"
                print(f"VERDICT: {subject} UNCHANGED over this window "
                      "(run --validate before trusting it; not a whole-page claim)")
            else:
                print("VERDICT: compared inventory is UPDATING — any freeze-based thesis "
                      "needs re-evaluation")
    return 0


if __name__ == "__main__":
    PATTERN = DEFAULT_PATTERN
    sys.exit(main())
