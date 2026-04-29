"""Scan Limitless for `isPolyArbitrage: true` markets and surface arb candidates.

Limitless tags its markets that mirror a Polymarket counterpart with
`metadata.isPolyArbitrage: true`. This script paginates the active-markets
endpoint, filters to those flagged, computes a fee-aware breakeven against
Polymarket's edge-aware fee structure (`fee = 0.072 * min(p, 1-p) * notional`),
and dumps a sorted table to:

  - stdout
  - notes/limitless_arb_<UTC ts>.md (gitignored — fresh each run)

For each candidate, the table shows:
  - Limitless YES price + volume
  - The fee-aware breakeven spread Polymarket would need to make this profitable
  - Whether p is favorable (near 0.9+ = low Polymarket fee, arb-able with small spreads)

Phase 1 (this script): data collection + visibility. No automated trading.
Phase 2 (deferred until phase 1 shows ≥ X profitable cycles per week): add
fuzzy-match against Polymarket gamma-api + auto-execution. Phase 2 is only
worth building if phase 1 surfaces real opportunities at our $30 working capital.

Usage:
    python scripts/limitless_arb_scan.py
    python scripts/limitless_arb_scan.py --threshold-edge 0.02 --notify

The `--notify` flag posts a Telegram summary if any candidate has a fee-aware
breakeven < the threshold (i.e., a small spread would already be profitable).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import httpx

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
OUT_DIR = _REPO_ROOT / "logs"  # gitignored; routine scans don't need to be committed

LIMITLESS_API = "https://api.limitless.exchange"
POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"
POLYMARKET_FEE_RATE = 0.072  # edge-aware: fee = rate * min(p, 1-p) * notional


def _telegram(text: str) -> None:
    try:
        subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            cwd=_REPO_ROOT, check=False, timeout=15, capture_output=True,
        )
    except Exception:
        pass


def fetch_arb_candidates() -> list[dict]:
    """Paginate /markets/active and return all markets with isPolyArbitrage=true."""
    out: list[dict] = []
    page = 1
    while True:
        try:
            r = httpx.get(f"{LIMITLESS_API}/markets/active",
                          params={"page": page}, timeout=15)
            r.raise_for_status()
            d = r.json()
        except Exception as e:
            print(f"page {page} fetch failed: {e}", file=sys.stderr)
            break
        markets = d.get("data") or []
        total = d.get("totalMarketsCount") or 0
        if not markets:
            break
        for m in markets:
            if (m.get("metadata") or {}).get("isPolyArbitrage"):
                out.append(m)
        if page * 25 >= total:
            break
        page += 1
        if page > 80:  # safety cap
            break
    return out


def polymarket_fee_per_side(p: float) -> float:
    """Return the Polymarket fee as a fraction of notional, given price p."""
    return POLYMARKET_FEE_RATE * min(p, 1 - p)


def round_trip_breakeven(p_yes: float) -> float:
    """Min cross-venue spread (fraction) needed to break even after Polymarket fees.

    Assumes Limitless side is fee-free (Coinbase-subsidized gas, plus
    Limitless's own fee — small but non-zero; we treat as 0 here for
    simplicity. Refine when phase-2 arrives.)
    """
    return polymarket_fee_per_side(p_yes) * 2


_STOPWORDS = {
    "will", "the", "a", "an", "by", "in", "on", "of", "to", "be", "before",
    "above", "below", "is", "and", "or", "for", "at", "vs", "between",
    "this", "that", "any", "are", "as", "with", "has", "had", "have",
    "do", "does", "did", "from", "into", "out", "over", "under",
    "one", "day", "after", "launch",  # extremely common in FDV-launch markets
}


def _distinctive_words(title: str) -> set[str]:
    """Return the lowercase distinctive-word set of a title."""
    cleaned = "".join(c if c.isalnum() or c.isspace() else " " for c in title)
    return {w.lower() for w in cleaned.split() if len(w) > 2 and w.lower() not in _STOPWORDS}


def _numeric_tokens(title: str) -> set[str]:
    """Extract numeric tokens (thresholds, dates, prices) from a title.

    Critical for arb-matching: 'MegaETH FDV above $1B' ≠ 'MegaETH FDV above $4B'.
    Matching must require numeric tokens to overlap, otherwise we'll cross
    threshold-variant markets.
    """
    import re as _re
    out: set[str] = set()
    # Currencies / sizes: $1B, $4.5B, 200M, 1.5K, etc.
    for m in _re.finditer(r"\$?(\d+(?:\.\d+)?)\s*([bmktBMKT])?", title):
        n, suf = m.group(1), (m.group(2) or "").lower()
        if suf:
            out.add(f"{n}{suf}")
        else:
            out.add(n)
    # Dates: "Apr 30", "2026", "Q1 2026", etc.
    for m in _re.finditer(r"\b(20\d{2}|Q[1-4]|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
                          title.lower()):
        out.add(m.group(0))
    return out


def fetch_polymarket_universe(max_markets: int = 3000) -> list[dict]:
    """Pull active Polymarket markets in 500-batches via gamma-api offset pagination."""
    out: list[dict] = []
    offset = 0
    while len(out) < max_markets:
        try:
            r = httpx.get(
                f"{POLYMARKET_GAMMA}/markets",
                params={"active": "true", "closed": "false",
                        "limit": "500", "offset": str(offset)},
                timeout=20,
            )
            r.raise_for_status()
            batch = r.json()
        except Exception as e:
            print(f"polymarket fetch offset={offset} failed: {e}", file=sys.stderr)
            break
        if not batch:
            break
        out.extend(batch)
        offset += len(batch)
        if len(batch) < 500:
            break
    return out


def index_polymarket(markets: list[dict]) -> list[tuple[set[str], set[str], float, str, str]]:
    """Build index: (word-set, numeric-set, yes_price, question, slug)."""
    idx: list[tuple[set[str], set[str], float, str, str]] = []
    for m in markets:
        q = m.get("question") or m.get("title") or ""
        if not q:
            continue
        prices_raw = m.get("outcomePrices") or "[]"
        try:
            prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
            if not (isinstance(prices, list) and prices):
                continue
            yes_price = float(prices[0])
        except Exception:
            continue
        idx.append((_distinctive_words(q), _numeric_tokens(q), yes_price, q, m.get("slug") or ""))
    return idx


def fuzzy_match(title: str, pm_index: list[tuple[set[str], set[str], float, str, str]],
                min_overlap: int = 3) -> tuple[float, str, float] | None:
    """Find the best Polymarket match for a Limitless title.

    Requires:
      - >= min_overlap distinctive-word matches
      - numeric tokens (thresholds, dates) must match exactly: if Limitless
        has '$4B' and best PM candidate has '$1B', that's a different market

    Returns (yes_price, question, confidence) where confidence is Jaccard
    similarity, or None if no match.
    """
    lim_words = _distinctive_words(title)
    lim_nums = _numeric_tokens(title)
    if len(lim_words) < min_overlap:
        return None

    best = None  # (overlap, jaccard, entry)
    for entry in pm_index:
        pm_words, pm_nums, _, _, _ = entry
        common = lim_words & pm_words
        if len(common) < min_overlap:
            continue
        # If both sides have numeric tokens, they must match (modulo subset)
        if lim_nums and pm_nums:
            num_overlap = lim_nums & pm_nums
            # Require at least one numeric token in common when both have any
            if not num_overlap:
                continue
        # If Limitless has nums but PM has none → likely different (PM is the
        # general market, Limitless splits by threshold). Penalize.
        elif lim_nums and not pm_nums:
            continue
        union = lim_words | pm_words
        jaccard = len(common) / len(union) if union else 0
        # Require reasonable confidence
        if jaccard < 0.35:
            continue
        if best is None or (len(common), jaccard) > (best[0], best[1]):
            best = (len(common), jaccard, entry)

    if best is None:
        return None
    overlap, jaccard, entry = best
    _, _, yes_price, question, _ = entry
    return (yes_price, question, jaccard)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--threshold-edge", type=float, default=0.02,
                   help="alert if Polymarket-side breakeven < this fraction (i.e., near-certain markets where small spreads pencil)")
    p.add_argument("--notify", action="store_true",
                   help="post a Telegram if any candidate clears the threshold")
    p.add_argument("--max-show", type=int, default=40)
    args = p.parse_args()

    print("fetching Limitless active markets (isPolyArbitrage filter)...")
    cands = fetch_arb_candidates()
    print(f"found {len(cands)} candidates")
    if not cands:
        return 0

    # Annotate each with breakeven + arbability
    for m in cands:
        prices = m.get("prices") or [0.5, 0.5]
        yes_price = float(prices[0]) if prices else 0.5
        m["_yes_price"] = yes_price
        m["_breakeven"] = round_trip_breakeven(yes_price)

    # Sort: lowest-breakeven first (easiest arbs)
    cands.sort(key=lambda m: m["_breakeven"])

    # Pull a wide slice of the Polymarket active-market universe and build a
    # client-side index for fuzzy matching (gamma-api ?q= search is broken;
    # it ignores the query and returns the same default page).
    print("pulling Polymarket active-market universe (gamma-api offset pagination)...")
    pm_universe = fetch_polymarket_universe(max_markets=3000)
    print(f"  pulled {len(pm_universe)} markets, indexing...")
    pm_index = index_polymarket(pm_universe)
    print(f"  indexed {len(pm_index)} markets with valid prices")

    # Match each candidate
    top_for_lookup = cands[: max(args.max_show, 50)]
    print(f"\nfuzzy-matching top {len(top_for_lookup)} candidates...")
    for m in top_for_lookup:
        result = fuzzy_match(m["title"], pm_index)
        if result:
            pm_yes, pm_q, conf = result
            m["_pm_yes"] = pm_yes
            m["_pm_question"] = pm_q
            m["_match_confidence"] = conf
            m["_spread"] = pm_yes - m["_yes_price"]  # positive = Polymarket richer
            m["_net_edge"] = abs(m["_spread"]) - m["_breakeven"]
        else:
            m["_pm_yes"] = None
            m["_net_edge"] = None

    # Re-sort the top by net edge (matched markets first, descending edge)
    matched = [m for m in top_for_lookup if m.get("_net_edge") is not None]
    unmatched = [m for m in top_for_lookup if m.get("_net_edge") is None]
    matched.sort(key=lambda m: -m["_net_edge"])

    # Output
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"limitless_arb_{ts}.md"
    with out_path.open("w") as f:
        f.write(f"# Limitless arb scan — {ts} UTC\n\n")
        f.write(f"Total `isPolyArbitrage:true` markets: {len(cands)}\n")
        f.write(f"Polymarket-matched (top {len(top_for_lookup)} by breakeven): {len(matched)}\n\n")
        f.write("**Manual verification required before any trade.** Matching is heuristic ")
        f.write("(distinctive-word overlap + numeric-token parity, Jaccard ≥ 0.35). ")
        f.write("Threshold-variant markets (e.g., 'X above $1B' vs 'X above $4B') often ")
        f.write("evade the numeric-token guard if one side phrases the threshold differently. ")
        f.write("Always click through to both venues before crossing capital.\n\n")
        f.write(f"Polymarket fee = {POLYMARKET_FEE_RATE} × min(p, 1-p) per side. ")
        f.write(f"Net edge = |spread| − breakeven. Positive = arb-profitable in theory.\n\n")
        f.write("## Matched (sorted by net edge)\n\n")
        f.write(f"| Lim YES | PM YES | Spread | Breakeven | Net Edge | Conf | Lim title / PM question |\n")
        f.write(f"|---:|---:|---:|---:|---:|---:|---|\n")
        for m in matched:
            f.write(f"| {m['_yes_price']:.3f} | {m['_pm_yes']:.3f} | "
                    f"{m['_spread']*100:+.2f}% | {m['_breakeven']*100:.2f}% | "
                    f"{m['_net_edge']*100:+.2f}% | {m.get('_match_confidence', 0):.2f} | "
                    f"L: {m['title'][:60]}<br>PM: {m.get('_pm_question','')[:60]} |\n")
        f.write("\n## Unmatched (Limitless markets with no clear Polymarket counterpart)\n\n")
        for m in unmatched[:20]:
            f.write(f"- YES {m['_yes_price']:.3f}  breakeven {m['_breakeven']*100:.2f}%  — {m['title'][:80]}\n")

    print(f"wrote {out_path}\n")

    # Stdout summary
    print(f"matched {len(matched)} of {len(top_for_lookup)} top candidates")
    print(f"\n{'Lim':>6} {'PM':>6} {'spread':>8} {'breakeven':>10} {'net edge':>9}  title")
    for m in matched[:15]:
        print(f"{m['_yes_price']:>6.3f} {m['_pm_yes']:>6.3f} {m['_spread']*100:>+7.2f}% "
              f"{m['_breakeven']*100:>9.2f}% {m['_net_edge']*100:>+8.2f}%  {m['title'][:80]}")

    # Notify if any actually-profitable markets found
    profitable = [m for m in matched if m["_net_edge"] > 0]
    print(f"\n{len(profitable)} markets with positive net edge after Polymarket fees")
    if profitable and args.notify:
        lines = [f"limitless arb: {len(profitable)} markets with positive net edge"]
        for m in profitable[:5]:
            lines.append(f"  Lim {m['_yes_price']:.3f} vs PM {m['_pm_yes']:.3f} "
                         f"(net +{m['_net_edge']*100:.2f}%) — {m['title'][:80]}")
        _telegram("\n".join(lines))

    return 0


if __name__ == "__main__":
    sys.exit(main())
