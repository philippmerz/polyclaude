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


def polymarket_buy_fee(p: float) -> float:
    """Polymarket edge-aware fee on buying a token at price p.

    Source: gamma-api fee schedule on short-tenor markets.
    fee = 0.072 × min(p, 1-p) × notional
    """
    return POLYMARKET_FEE_RATE * min(p, 1 - p)


def limitless_buy_fee(p: float) -> float:
    """Limitless buy fee at price p, in fraction of notional.

    Per docs.limitless.exchange/user-guide/fees: 0.40% near parity, up to
    3.00% at extremes. Modeling as symmetric around p=0.5 since the docs
    are unclear on asymmetry; this is the conservative assumption (slightly
    over-estimates fees at high p, which suppresses false positives).
    Maker rebates exist but the arb requires takers on both legs.
    """
    distance_from_parity = abs(p - 0.5) * 2  # 0 at p=0.5, 1 at p=0 or p=1
    return 0.004 + (0.030 - 0.004) * distance_from_parity


def arb_breakeven(p_lim: float, p_pm: float) -> float:
    """Minimum spread |p_pm - p_lim| needed to clear fees on a paired arb.

    The trade (when lim_yes < pm_yes): buy Lim YES at p_lim + buy PM NO at
    (1 - p_pm). Pays one Limitless buy fee at p_lim and one Polymarket buy
    fee at (1 - p_pm). Symmetric for the inverse case.
    """
    if p_lim < p_pm:
        # Buy Lim YES at p_lim, Buy PM NO at (1 - p_pm)
        return limitless_buy_fee(p_lim) + polymarket_buy_fee(1 - p_pm)
    else:
        # Buy PM YES at p_pm, Buy Lim NO at (1 - p_lim)
        return polymarket_buy_fee(p_pm) + limitless_buy_fee(1 - p_lim)


def round_trip_breakeven(p_yes: float) -> float:
    """Approximate breakeven assuming the Polymarket side is at the same price.
    Used for the initial sort before Polymarket prices are looked up.
    """
    # Conservative estimate: Lim fee at this price + PM fee at (1-p_yes)
    # (we don't yet know p_pm; assume similar to p_yes and use the more
    # demanding of the two arb directions)
    return limitless_buy_fee(p_yes) + polymarket_buy_fee(1 - p_yes)


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


def _proper_nouns(title: str) -> set[str]:
    """Extract proper nouns (capitalized non-leading words) from a title.

    Used to require entity-name overlap on matches: 'Will Neymar play in the
    2026 FIFA WC' vs 'Will Lionel Messi play in the 2026 FIFA WC' share many
    distinctive words (play, fifa, world, cup, 2026) but DIFFERENT subjects.
    Without proper-noun overlap, fuzzy_match generates a false positive.

    Strips leading interrogative ("Will", "Does", "Is") and common
    framework tokens. Returns lowercased.

    Lesson source: 2026-05-09 limitless_arb_scan surfaced 'Neymar play 2026 WC'
    matched to 'Messi play 2026 WC' as +68% net-edge — both shared FIFA/WC/2026
    distinctive words but DIFFERENT player names.
    """
    import re as _re
    leading_skip = {"Will", "Does", "Is", "Can", "Has", "Did", "Should", "Would"}
    framework_skip = {"FIFA", "WC", "World", "Cup", "Olympics", "League", "Open",
                      "Premier", "Series", "Final", "Cup", "Day", "Year",
                      "Q1", "Q2", "Q3", "Q4", "USA", "US", "UK", "EU"}
    # Find capitalized word runs (1+ consecutive Cap-prefixed tokens)
    out: set[str] = set()
    tokens = _re.findall(r"[A-Z][A-Za-z]+", title)
    for i, t in enumerate(tokens):
        if i == 0 and t in leading_skip:
            continue
        if t in framework_skip:
            continue
        if len(t) <= 2:
            continue
        out.add(t.lower())
    return out


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


def index_polymarket(markets: list[dict]) -> list[dict]:
    """Build index entries with all fields needed downstream.

    Each entry: {words, nums, yes_price, question, slug, description}
    """
    idx: list[dict] = []
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
        idx.append({
            "words": _distinctive_words(q),
            "nums": _numeric_tokens(q),
            "propers": _proper_nouns(q),
            "yes_price": yes_price,
            "question": q,
            "slug": m.get("slug") or "",
            "description": m.get("description") or "",
        })
    return idx


def verify_resolution_match(lim_desc: str, pm_desc: str,
                             lim_title: str, pm_question: str) -> tuple[str, str]:
    """Ask claude -p haiku whether two resolution criteria will resolve identically.

    Returns (verdict, reason) where verdict is one of IDENTICAL / SIMILAR /
    DIFFERENT / UNCERTAIN. On agent error, returns (UNCERTAIN, reason).

    Used to gate autonomous arb execution. Only IDENTICAL pairs are eligible
    for cross-venue capital deployment — anything less is too risky given the
    asymmetric loss (a single resolution-language mismatch wipes both legs).
    """
    import subprocess as _sp

    # Strip HTML, keep readable text
    import re as _re
    def _clean(s: str) -> str:
        s = _re.sub(r"<[^>]+>", " ", s or "")
        s = _re.sub(r"\s+", " ", s)
        return s.strip()[:1500]

    prompt = (
        "Compare the resolution criteria of two prediction markets that claim "
        "to resolve on the same event. Will they ALWAYS resolve to the same "
        "outcome (both YES or both NO), or could they disagree in some scenario "
        "due to different language, oracle source, deadline, or definitions?\n\n"
        f"Market A (Limitless): {lim_title}\n"
        f"Resolution: {_clean(lim_desc)}\n\n"
        f"Market B (Polymarket): {pm_question}\n"
        f"Resolution: {_clean(pm_desc)}\n\n"
        "Respond on ONE line, exactly:\n"
        "- IDENTICAL: <one-line why they always agree>\n"
        "- SIMILAR: <one-line on edge case where they might differ>\n"
        "- DIFFERENT: <one-line on clear divergence>\n"
        "- UNCERTAIN: <one-line on what's missing>\n\n"
        "Be strict. Subtle differences in deadlines, oracle source, or "
        "language can cause edge-case disagreement. Default to UNCERTAIN if "
        "not 100% sure both markets always agree."
    )

    try:
        r = _sp.run(
            ["claude", "-p", "--model", "haiku", prompt],
            capture_output=True, text=True, timeout=45, cwd="/tmp",
        )
        line = (r.stdout or "").strip().splitlines()[0] if r.stdout else ""
    except (_sp.TimeoutExpired, _sp.CalledProcessError, FileNotFoundError) as e:
        return ("UNCERTAIN", f"agent error: {_secrets.scrub(str(e))[:120]}")

    upper = line.upper()
    for v in ("IDENTICAL", "SIMILAR", "DIFFERENT", "UNCERTAIN"):
        if upper.startswith(v):
            reason = line[len(v):].lstrip(": ").strip() or "(no reason)"
            return (v, reason)
    return ("UNCERTAIN", f"unparseable: {line[:120]}")


def fuzzy_match(title: str, pm_index: list[dict],
                min_overlap: int = 3) -> dict | None:
    """Find the best Polymarket match for a Limitless title.

    Returns the full pm_index entry (yes_price, question, slug, description,
    plus a `_jaccard` annotation) of the best match, or None.
    """
    lim_words = _distinctive_words(title)
    lim_nums = _numeric_tokens(title)
    lim_propers = _proper_nouns(title)
    if len(lim_words) < min_overlap:
        return None

    best = None  # (overlap, jaccard, entry)
    for entry in pm_index:
        pm_words = entry["words"]
        pm_nums = entry["nums"]
        pm_propers = entry.get("propers", set())
        common = lim_words & pm_words
        if len(common) < min_overlap:
            continue
        # If both sides have numeric tokens, require at least one in common
        if lim_nums and pm_nums:
            if not (lim_nums & pm_nums):
                continue
        # If Limitless has nums but PM has none → likely different (PM is the
        # general market, Limitless splits by threshold). Skip.
        elif lim_nums and not pm_nums:
            continue
        # PROPER-NOUN OVERLAP: if EITHER title has proper nouns, require at
        # least one common entity. Asymmetric (one has names, other doesn't)
        # → likely different markets. Lesson source: 2026-05-09 +68% false-
        # positive (Neymar vs Messi same template, then Neymar vs USA same
        # template) — both passed weaker overlap rule. Strict rule: any-side
        # has-propers AND no overlap → reject.
        if (lim_propers or pm_propers):
            if not (lim_propers & pm_propers):
                continue
        union = lim_words | pm_words
        jaccard = len(common) / len(union) if union else 0
        # Bumped 0.35 -> 0.55 to reject same-subject-different-verb matches:
        # "Cristiano Ronaldo announce retirement 2026" vs "Cristiano Ronaldo
        # win Ballon d'Or 2026" share {cristiano,ronaldo,2026} (jaccard 0.43)
        # but ask different questions. 0.55 requires more semantic alignment.
        if jaccard < 0.55:
            continue
        if best is None or (len(common), jaccard) > (best[0], best[1]):
            best = (len(common), jaccard, entry)

    if best is None:
        return None
    overlap, jaccard, entry = best
    out = dict(entry)
    out["_jaccard"] = jaccard
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--threshold-edge", type=float, default=0.015,
                   help="net-edge threshold for autonomous-execution eligibility (default 1.5%)")
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
            m["_pm_yes"] = result["yes_price"]
            m["_pm_question"] = result["question"]
            m["_pm_slug"] = result["slug"]
            m["_pm_description"] = result["description"]
            m["_match_confidence"] = result["_jaccard"]
            m["_spread"] = result["yes_price"] - m["_yes_price"]
            # Real fee-aware breakeven uses both sides' actual fees
            m["_breakeven"] = arb_breakeven(m["_yes_price"], result["yes_price"])
            m["_net_edge"] = abs(m["_spread"]) - m["_breakeven"]
        else:
            m["_pm_yes"] = None
            m["_net_edge"] = None

    # Agent-verify resolution criteria for the top profitable candidates only
    # (verification is the expensive step; gate by net edge first)
    matched_for_verify = sorted(
        [m for m in top_for_lookup
         if (m.get("_net_edge") or -1) > 0
         and (m.get("_match_confidence") or 0) >= 0.5],
        key=lambda m: -(m.get("_net_edge") or 0),
    )[:10]
    print(f"\nverifying resolution-language equivalence on top {len(matched_for_verify)} "
          f"profitable matches with claude -p haiku...")
    for m in matched_for_verify:
        verdict, reason = verify_resolution_match(
            lim_desc=m.get("description", ""),
            pm_desc=m.get("_pm_description", ""),
            lim_title=m["title"],
            pm_question=m.get("_pm_question", ""),
        )
        m["_verify_verdict"] = verdict
        m["_verify_reason"] = reason
        print(f"  {verdict:9}  net_edge={m['_net_edge']*100:+.2f}%  {m['title'][:60]}")

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
        f.write("Three-layer screening: (1) distinctive-word overlap ≥ 3 with Jaccard ≥ 0.35, ")
        f.write("(2) numeric-token parity, (3) agent-verified resolution-language equivalence ")
        f.write("(claude -p haiku). Only `IDENTICAL` verdicts qualify for autonomous execution; ")
        f.write("`SIMILAR`/`UNCERTAIN`/`DIFFERENT` are visibility-only.\n\n")
        f.write(f"Polymarket fee = {POLYMARKET_FEE_RATE} × min(p, 1-p) per side. ")
        f.write(f"Limitless buy fee = 0.4-3.0% (rises away from parity). ")
        f.write(f"Net edge = |spread| − (lim_fee + pm_fee). Positive = arb-profitable.\n\n")
        f.write("## Matched (sorted by net edge)\n\n")
        f.write(f"| Lim YES | PM YES | Spread | Breakeven | Net Edge | Conf | Verdict | Lim title / PM question |\n")
        f.write(f"|---:|---:|---:|---:|---:|---:|:---:|---|\n")
        for m in matched:
            verdict = m.get("_verify_verdict", "—")
            f.write(f"| {m['_yes_price']:.3f} | {m['_pm_yes']:.3f} | "
                    f"{m['_spread']*100:+.2f}% | {m['_breakeven']*100:.2f}% | "
                    f"{m['_net_edge']*100:+.2f}% | {m.get('_match_confidence', 0):.2f} | "
                    f"{verdict} | "
                    f"L: {m['title'][:60]}<br>PM: {m.get('_pm_question','')[:60]} |\n")
        f.write("\n## Unmatched (Limitless markets with no clear Polymarket counterpart)\n\n")
        for m in unmatched[:20]:
            f.write(f"- YES {m['_yes_price']:.3f}  breakeven {m['_breakeven']*100:.2f}%  — {m['title'][:80]}\n")

    # Also dump a machine-readable JSON for the executor to consume
    out_json = OUT_DIR / "limitless_arb_latest.json"
    payload = {
        "generated_at": ts,
        "total_candidates": len(cands),
        "matched_count": len(matched),
        "verified_identical": [],
        "verified_other": [],
    }
    for m in matched:
        chainlink_enabled = bool((m.get("metadata") or {})
                                  .get("chainlinkDataStream", {}).get("enabled"))
        record = {
            "lim_id": m["id"],
            "lim_title": m["title"],
            "lim_yes_price": m["_yes_price"],
            "lim_yes_token": (m.get("tokens") or {}).get("yes"),
            "lim_no_token": (m.get("tokens") or {}).get("no"),
            "lim_condition_id": m.get("conditionId"),
            "lim_chainlink_enabled": chainlink_enabled,
            "lim_categories": m.get("categories") or [],
            "pm_question": m.get("_pm_question"),
            "pm_slug": m.get("_pm_slug"),
            "pm_yes_price": m["_pm_yes"],
            "spread": m["_spread"],
            "breakeven": m["_breakeven"],
            "net_edge": m["_net_edge"],
            "match_confidence": m.get("_match_confidence"),
            "verify_verdict": m.get("_verify_verdict"),
            "verify_reason": m.get("_verify_reason"),
        }
        if m.get("_verify_verdict") == "IDENTICAL":
            payload["verified_identical"].append(record)
        else:
            payload["verified_other"].append(record)
    out_json.write_text(json.dumps(payload, indent=2, default=str))

    print(f"wrote {out_path}")
    print(f"wrote {out_json}\n")

    # Stdout summary
    print(f"matched {len(matched)} of {len(top_for_lookup)} top candidates")
    print(f"\n{'Lim':>6} {'PM':>6} {'spread':>8} {'breakeven':>10} {'net edge':>9}  title")
    for m in matched[:15]:
        print(f"{m['_yes_price']:>6.3f} {m['_pm_yes']:>6.3f} {m['_spread']*100:>+7.2f}% "
              f"{m['_breakeven']*100:>9.2f}% {m['_net_edge']*100:>+8.2f}%  {m['title'][:80]}")

    # Notify only on candidates that are (a) agent-verified IDENTICAL,
    # (b) above the edge threshold, AND (c) have mechanical resolution
    # (Limitless Chainlink Data Stream). Subjective-resolution markets carry
    # outsized resolution-language divergence risk that's not worth the small
    # absolute edge at our size — they get logged for visibility but not
    # telegrammed.
    identical = [m for m in matched
                 if m.get("_verify_verdict") == "IDENTICAL"
                 and (m.get("_net_edge") or 0) >= args.threshold_edge]
    mechanical = [m for m in identical
                  if (m.get("metadata") or {}).get("chainlinkDataStream", {}).get("enabled")]
    subjective = [m for m in identical if m not in mechanical]
    print(f"\n{len(identical)} IDENTICAL above net edge >= {args.threshold_edge*100:.1f}% — "
          f"{len(mechanical)} mechanical resolution, {len(subjective)} subjective")
    if subjective:
        print("subjective-resolution candidates (logged, not alerted):")
        for m in subjective[:5]:
            print(f"  +{m['_net_edge']*100:.2f}%  {m['title'][:80]}")
    if mechanical and args.notify:
        lines = [f"limitless arb: {len(mechanical)} mechanical-resolution IDENTICAL "
                 f"candidate(s) above {args.threshold_edge*100:.1f}% net edge"]
        for m in mechanical[:5]:
            direction = "LONG Lim YES + LONG PM NO" if m["_yes_price"] < m["_pm_yes"] else "LONG PM YES + LONG Lim NO"
            lines.append(
                f"\n• midpoint net edge +{m['_net_edge']*100:.2f}%  ({direction})\n"
                f"  Lim YES {m['_yes_price']:.3f}  /  PM YES {m['_pm_yes']:.3f}\n"
                f"  {m['title'][:90]}\n"
                f"  agent: {m.get('_verify_reason','')[:120]}\n"
                f"  manual review required: midpoint estimate; check real orderbook depth before trading"
            )
        lines.append(f"\nfull table: logs/limitless_arb_<ts>.md")
        _telegram("\n".join(lines))

    return 0


if __name__ == "__main__":
    sys.exit(main())
