"""Scan Limitless for `isPolyArbitrage: true` markets and surface arb candidates.

Limitless tags its markets that mirror a Polymarket counterpart with
`metadata.isPolyArbitrage: true`. This script paginates the active-markets
endpoint, expands flagged groups into priced leaves, and computes a
conditional midpoint screen. Polymarket uses its full feeSchedule through
`pm_fees.py`; only explicit legacy scalar callers use the capped exponent-1
compatibility path. Limitless assumes a maximum 3% deduction from received
contracts, not a USDC surcharge. Exact fees, rounding, depth, freshness and
cross-venue resolution equivalence remain unverified by this screen. It
dumps a sorted table to:

  - stdout
  - logs/limitless_arb_<UTC ts>.md (gitignored — fresh each run)

For each candidate, the table shows:
  - Limitless and matched Polymarket YES midpoints
  - Conditional spread hurdle and net edge per matched net payout share
  - Match confidence and an agent's resolution-language assessment

This script provides data collection, fuzzy matching and visibility only.
The downstream public-book inspector is also execution-disabled. Neither a
positive midpoint edge nor an IDENTICAL label authorizes trading.

Usage:
    python scripts/limitless_arb_scan.py
    python scripts/limitless_arb_scan.py --threshold-edge 0.02 --notify

The `--notify` flag summarizes IDENTICAL mechanical-resolution candidates
above the conditional midpoint-edge threshold; it is not an execution alert.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

import _paths as _secrets
from agent_runtime import run_agent

_secrets.install_scrubbing_excepthook()


_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
OUT_DIR = _REPO_ROOT / "logs"  # gitignored; routine scans don't need to be committed

LIMITLESS_API = "https://api.limitless.exchange"
POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"
import pm_fees

LIMITLESS_CONTRACT_FEE_BOUND = 0.03  # conditional documented CLOB maximum, not an exact curve
LIMITLESS_ACTIVE_PAGE_LIMIT = 25
LIMITLESS_ACTIVE_PAGE_CAP = 80

POLYMARKET_PAGE_LIMIT = 100
POLYMARKET_PAGE_RETRIES = 3
POLYMARKET_UNIVERSE_LIMIT = 3000

LAST_ARB_NORMALIZATION_STATS: dict[str, object] = {
    "flagged_parents": 0,
    "expanded_children": 0,
    "eligible_leaves": 0,
    "excluded": 0,
    "exclusions": {},
}


def _telegram(text: str) -> None:
    try:
        subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            cwd=_REPO_ROOT, check=False, timeout=15, capture_output=True,
        )
    except Exception:
        pass


def _market_title(market: dict) -> str:
    return str(market.get("title") or market.get("question") or "").strip()


def _market_description(market: dict) -> str:
    for key in ("description", "resolution", "rules"):
        value = market.get(key)
        if value:
            return str(value).strip()
    return ""


def _parse_binary_prices(raw: object) -> list[float] | None:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            return None
    if not isinstance(raw, list) or len(raw) != 2:
        return None
    try:
        prices = [float(value) for value in raw]
    except (TypeError, ValueError):
        return None
    if any(not math.isfinite(price) or not 0.0 <= price <= 1.0 for price in prices):
        return None
    return prices


def _parse_binary_tokens(raw: object) -> dict[str, str] | None:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            return None
    if isinstance(raw, dict):
        yes = raw.get("yes") or raw.get("YES")
        no = raw.get("no") or raw.get("NO")
    elif isinstance(raw, list) and len(raw) == 2:
        yes, no = raw
    else:
        return None
    yes, no = str(yes or "").strip(), str(no or "").strip()
    if not yes or not no or yes == no:
        return None
    return {"yes": yes, "no": no}


def _child_markets(market: dict) -> list[object]:
    for key in ("children", "markets", "subMarkets", "submarkets"):
        children = market.get(key)
        if isinstance(children, list):
            return children
    return []


def _record_exclusion(stats: dict[str, object], reason: str) -> None:
    stats["excluded"] = int(stats.get("excluded", 0)) + 1
    exclusions = stats.setdefault("exclusions", {})
    assert isinstance(exclusions, dict)
    exclusions[reason] = int(exclusions.get(reason, 0)) + 1


def _normalise_leaf(
    parent: dict,
    leaf: dict,
    stats: dict[str, object],
    parent_title: str,
    parent_description: str,
) -> dict | None:
    """Return one fully identified/priced leaf, or exclude it explicitly.

    Parent metadata is used only to carry discovery context. Execution fields
    (prices, tokens, descriptions, and oracle metadata) must come from the
    leaf itself; no parent midpoint or token is synthesized.
    """
    leaf_id = str(leaf.get("id") or "").strip()
    leaf_slug = str(leaf.get("slug") or "").strip()
    if not leaf_id or not leaf_slug:
        _record_exclusion(stats, "missing_leaf_identity")
        return None
    child_title = _market_title(leaf)
    if not child_title and not parent_title:
        _record_exclusion(stats, "missing_leaf_title")
        return None
    prices = _parse_binary_prices(leaf.get("prices"))
    if prices is None:
        _record_exclusion(stats, "missing_or_malformed_prices")
        return None
    tokens = _parse_binary_tokens(leaf.get("tokens"))
    if tokens is None:
        _record_exclusion(stats, "missing_or_duplicate_tokens")
        return None

    child_description = _market_description(leaf)
    title_parts: list[str] = []
    for part in (parent_title, child_title):
        if part and part not in title_parts:
            title_parts.append(part)
    match_title = " — ".join(title_parts)
    # Avoid repeating an identical parent/child title while retaining both
    # levels whenever the group provides useful context.
    if parent_title and child_title == parent_title:
        match_title = parent_title
    match_description = "\n\n".join(
        part for part in (
            f"Parent market: {parent_description}" if parent_description else "",
            f"Child market: {child_description}" if child_description else "",
        ) if part
    )

    candidate = dict(leaf)
    candidate["id"] = leaf_id
    candidate["slug"] = leaf_slug
    candidate["prices"] = prices
    candidate["tokens"] = tokens
    candidate["title"] = child_title or parent_title
    candidate["description"] = child_description
    candidate["_match_title"] = match_title or child_title or parent_title
    candidate["_match_description"] = match_description or child_description or parent_description
    candidate["_discovery_parent_id"] = str(parent.get("id") or "").strip() or None
    candidate["_discovery_parent_slug"] = str(parent.get("slug") or "").strip() or None
    # This is intentionally the only inherited metadata: a flagged parent
    # authorizes discovery, not execution/oracle/fee assumptions.
    child_metadata_raw = leaf.get("metadata")
    child_metadata = dict(child_metadata_raw) if isinstance(child_metadata_raw, dict) else {}
    child_metadata["isPolyArbitrage"] = True
    candidate["metadata"] = child_metadata
    stats["eligible_leaves"] = int(stats.get("eligible_leaves", 0)) + 1
    return candidate


def _normalise_arb_markets(parents: list[dict]) -> list[dict]:
    stats: dict[str, object] = {
        "flagged_parents": len(parents),
        "expanded_children": 0,
        "eligible_leaves": 0,
        "excluded": 0,
        "exclusions": {},
    }
    out: list[dict] = []
    seen: dict[str, dict] = {}

    def walk(parent: dict, node: dict, parent_title: str, parent_description: str) -> None:
        children = _child_markets(node)
        if children:
            stats["expanded_children"] = int(stats.get("expanded_children", 0)) + len(children)
            node_title = _market_title(node) or parent_title
            node_description = _market_description(node) or parent_description
            for child in children:
                if not isinstance(child, dict):
                    _record_exclusion(stats, "malformed_child_record")
                    continue
                walk(parent, child, node_title, node_description)
            return
        candidate = _normalise_leaf(parent, node, stats, parent_title, parent_description)
        if candidate is None:
            return
        identity = candidate["id"]
        previous = seen.get(identity)
        if previous is not None:
            if (previous["slug"] != candidate["slug"]
                    or previous["tokens"] != candidate["tokens"]
                    or previous["prices"] != candidate["prices"]):
                raise RuntimeError(
                    f"Limitless leaf id {identity} has conflicting identity or pricing"
                )
            _record_exclusion(stats, "duplicate_leaf_identity")
            return
        seen[identity] = candidate
        out.append(candidate)

    for parent in parents:
        title = _market_title(parent)
        description = _market_description(parent)
        walk(parent, parent, title, description)

    stats["eligible_leaves"] = len(out)
    global LAST_ARB_NORMALIZATION_STATS
    LAST_ARB_NORMALIZATION_STATS = stats
    return out


def fetch_arb_candidates() -> list[dict]:
    """Paginate active markets and return only fully identified priced leaves.

    A partial or malformed response is not a valid empty universe: callers
    must be able to distinguish it from a successful zero-candidate scan.
    """
    flagged: list[dict] = []
    fetched = 0
    page = 1
    while True:
        try:
            r = httpx.get(f"{LIMITLESS_API}/markets/active",
                          params={"page": page, "limit": LIMITLESS_ACTIVE_PAGE_LIMIT},
                          timeout=15)
            r.raise_for_status()
            d = r.json()
        except Exception as exc:
            raise RuntimeError(
                f"Limitless active-market page {page} failed; refusing partial coverage"
            ) from exc
        if not isinstance(d, dict):
            raise RuntimeError(
                f"Limitless active-market page {page} returned a malformed response"
            )
        markets = d.get("data")
        total = d.get("totalMarketsCount")
        if not isinstance(markets, list):
            raise RuntimeError(
                f"Limitless active-market page {page} omitted its data list"
            )
        if (isinstance(total, bool) or not isinstance(total, int)
                or total < 0):
            raise RuntimeError(
                "Limitless active-market response omitted a valid totalMarketsCount"
            )
        if not markets:
            if fetched < total:
                raise RuntimeError(
                    f"Limitless active-market page {page} was empty before totalMarketsCount"
                )
            break
        if len(markets) > LIMITLESS_ACTIVE_PAGE_LIMIT:
            raise RuntimeError(
                f"Limitless active-market page {page} exceeded its requested limit"
            )
        for m in markets:
            if not isinstance(m, dict):
                raise RuntimeError(
                    f"Limitless active-market page {page} contains a malformed record"
                )
            metadata = m.get("metadata")
            if metadata is not None and not isinstance(metadata, dict):
                raise RuntimeError(
                    f"Limitless active-market page {page} contains malformed metadata"
                )
            if (metadata or {}).get("isPolyArbitrage") is True:
                flagged.append(m)
        fetched += len(markets)
        if fetched > total:
            raise RuntimeError(
                "Limitless active-market response totalMarketsCount was smaller "
                "than the records returned"
            )
        if fetched >= total:
            break
        page += 1
        if page > LIMITLESS_ACTIVE_PAGE_CAP:
            raise RuntimeError(
                "Limitless active-market pagination exceeded its safety cap; "
                "refusing partial coverage"
            )
    candidates = _normalise_arb_markets(flagged)
    LAST_ARB_NORMALIZATION_STATS["fetch_pages"] = page
    LAST_ARB_NORMALIZATION_STATS["fetch_total"] = total
    LAST_ARB_NORMALIZATION_STATS["fetch_complete"] = True
    return candidates


def polymarket_buy_fee(p: float, fee_rate: dict | float | None = None) -> float:
    """Polymarket fee per share when buying a token at price ``p``.

    Full market dictionaries preserve the authoritative rate and exponent.
    Explicit scalar inputs retain the legacy capped exponent-1 estimate.
    Before a match is known the legacy fallback is only a ranking heuristic,
    not an upper bound on all possible structured schedules.
    """
    if isinstance(fee_rate, dict):
        return pm_fees.fee_per_share(fee_rate, p)
    raw_rate = pm_fees.FEE_RATE_FALLBACK if fee_rate is None else fee_rate
    return pm_fees.fee_per_share_at(raw_rate, p)


def limitless_buy_fee(p: float) -> float:
    """Extra cash per NET matched share under the 3% contract-fee assumption.

    Buying 1/(1-r) gross contracts at p supplies one net contract if the
    deduction is r: cash cost p/(1-r), incremental cost p*r/(1-r).
    This is NOT a notional fee rate or the venue's exact unpublished curve.
    Source: https://docs.limitless.exchange/user-guide/fees (2026-09-07).
    Unknown per-maker rounding and market-specific applicability remain gates.
    """
    if not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("Limitless price must be finite and in [0, 1]")
    return p * LIMITLESS_CONTRACT_FEE_BOUND / (1 - LIMITLESS_CONTRACT_FEE_BOUND)


def arb_breakeven(p_lim: float, p_pm: float,
                  pm_fee_rate: dict | float | None = None) -> float:
    """Conditional midpoint spread hurdle per NET matched payout share.

    The trade (when lim_yes < pm_yes): buy Lim YES at p_lim + buy PM NO at
    (1 - p_pm). Pays one Limitless buy fee at p_lim and one Polymarket buy
    fee at (1 - p_pm). Both quantities are net matched shares. This ignores
    spreads/depth and is not an execution quote; see limitless_quote_math.py.
    """
    if p_lim < p_pm:
        # Buy Lim YES at p_lim, Buy PM NO at (1 - p_pm)
        return limitless_buy_fee(p_lim) + polymarket_buy_fee(1 - p_pm, pm_fee_rate)
    else:
        # Buy PM YES at p_pm, Buy Lim NO at (1 - p_lim)
        return polymarket_buy_fee(p_pm, pm_fee_rate) + limitless_buy_fee(1 - p_lim)


def round_trip_breakeven(p_yes: float) -> float:
    """Approximate breakeven assuming the Polymarket side is at the same price.
    Used for the initial sort before Polymarket prices are looked up.
    """
    # Conservative estimate: Lim fee at this price + PM fee at (1-p_yes)
    # (we don't yet know p_pm; assume similar to p_yes and use the more
    # demanding of the two arb directions)
    return max(limitless_buy_fee(p_yes) + polymarket_buy_fee(1 - p_yes),
               limitless_buy_fee(1 - p_yes) + polymarket_buy_fee(p_yes))


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


@dataclass(frozen=True)
class PolymarketUniverseFetch:
    """A bounded keyset slice plus an honest statement of its coverage."""

    markets: list[dict]
    max_markets: int
    pages: int
    complete: bool

    @property
    def coverage(self) -> str:
        return "complete" if self.complete else "bounded_partial"

    @property
    def coverage_label(self) -> str:
        if self.complete:
            return (
                "COMPLETE: Gamma /markets/keyset exhausted after "
                f"{len(self.markets)} active open markets"
            )
        return (
            "BOUNDED PARTIAL: first "
            f"{len(self.markets)} active open markets ranked by volume24hr "
            f"order (cap {self.max_markets}; more markets exist)"
        )

    def metadata(self) -> dict:
        return {
            "endpoint": "/markets/keyset",
            "coverage": self.coverage,
            "coverage_label": self.coverage_label,
            "markets_returned": len(self.markets),
            "max_markets": self.max_markets,
            "pages": self.pages,
            "complete": self.complete,
            "ordering": "volume24hr descending",
        }


def _fetch_polymarket_keyset_page(params: dict[str, str]) -> dict:
    """Fetch one keyset page, retrying transient request/shape failures."""
    last_error: Exception | None = None
    for attempt in range(POLYMARKET_PAGE_RETRIES):
        try:
            response = httpx.get(
                f"{POLYMARKET_GAMMA}/markets/keyset",
                params=params,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise RuntimeError("keyset response is not an object")
            if not isinstance(payload.get("markets"), list):
                raise RuntimeError("keyset response omitted its markets list")
            cursor = payload.get("next_cursor")
            if cursor not in (None, "") and not isinstance(cursor, str):
                raise RuntimeError("keyset response has a malformed next_cursor")
            return payload
        except Exception as exc:
            last_error = exc
            if attempt + 1 < POLYMARKET_PAGE_RETRIES:
                time.sleep(0.5 * (2 ** attempt))
    raise RuntimeError(
        "Polymarket keyset page failed after "
        f"{POLYMARKET_PAGE_RETRIES} attempts at cursor "
        f"{params.get('after_cursor', '<start>')!r}; refusing partial coverage"
    ) from last_error


def fetch_polymarket_universe(
    max_markets: int = POLYMARKET_UNIVERSE_LIMIT,
) -> PolymarketUniverseFetch:
    """Fetch a bounded, stable slice from Gamma's official market keyset.

    The scanner intentionally does not crawl the entire active universe: its
    practical phase-one budget is ``max_markets`` full market records. Reaching
    that cap while Gamma supplies another cursor is a valid but explicitly
    labeled partial scan. Any request, payload, identity, or cursor defect
    raises instead of returning a smaller list that could masquerade as clean.
    """
    if (not isinstance(max_markets, int) or isinstance(max_markets, bool)
            or max_markets <= 0):
        raise ValueError("max_markets must be a positive integer")

    out: list[dict] = []
    seen_ids: set[str] = set()
    seen_cursors: set[str] = set()
    cursor: str | None = None
    pages = 0
    last_volume = math.inf

    while len(out) < max_markets:
        request_limit = min(POLYMARKET_PAGE_LIMIT, max_markets - len(out))
        params = {
            "active": "true",
            "closed": "false",
            "limit": str(request_limit),
            "order": "volume24hr",
            "ascending": "false",
        }
        if cursor is not None:
            params["after_cursor"] = cursor
        payload = _fetch_polymarket_keyset_page(params)
        batch = payload["markets"]
        pages += 1
        if len(batch) > request_limit:
            raise RuntimeError(
                "Polymarket keyset returned more markets than requested; "
                "refusing ambiguous coverage"
            )

        for market in batch:
            if not isinstance(market, dict):
                raise RuntimeError(
                    "Polymarket keyset contains a non-object market record"
                )
            market_id = str(market.get("id") or "").strip()
            if not market_id:
                raise RuntimeError(
                    "Polymarket keyset market lacks a stable id"
                )
            if market_id in seen_ids:
                raise RuntimeError(
                    f"Polymarket keyset repeated market id {market_id}; "
                    "refusing ambiguous coverage"
                )
            if market.get("active") is not True or market.get("closed") is not False:
                raise RuntimeError(
                    f"Polymarket keyset violated active/open filters for {market_id}"
                )
            raw_volume = market.get("volume24hr")
            if isinstance(raw_volume, bool):
                raise RuntimeError(
                    f"Polymarket keyset has malformed volume24hr for {market_id}"
                )
            try:
                volume = float(raw_volume)
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"Polymarket keyset has malformed volume24hr for {market_id}"
                ) from exc
            if not math.isfinite(volume) or volume < 0.0:
                raise RuntimeError(
                    f"Polymarket keyset has malformed volume24hr for {market_id}"
                )
            if volume > last_volume + 1e-6:
                raise RuntimeError(
                    "Polymarket keyset violated requested volume24hr ordering"
                )
            last_volume = volume
            seen_ids.add(market_id)
            out.append(market)

        raw_next = payload.get("next_cursor")
        next_cursor = raw_next if isinstance(raw_next, str) and raw_next else None
        if next_cursor is None:
            return PolymarketUniverseFetch(
                markets=out,
                max_markets=max_markets,
                pages=pages,
                complete=True,
            )
        if not batch:
            raise RuntimeError(
                "Polymarket keyset returned an empty page with a next cursor"
            )
        if next_cursor == cursor or next_cursor in seen_cursors:
            raise RuntimeError(
                "Polymarket keyset repeated a cursor; refusing partial coverage"
            )
        seen_cursors.add(next_cursor)
        cursor = next_cursor

    return PolymarketUniverseFetch(
        markets=out,
        max_markets=max_markets,
        pages=pages,
        complete=False,
    )


def index_polymarket(markets: list[dict]) -> list[dict]:
    """Build index entries with all fields needed downstream.

    Retain the full fee market, and map the YES price by its outcome label.
    Non-binary, missing-label or malformed-price markets are excluded.
    """
    idx: list[dict] = []
    for m in markets:
        q = m.get("question") or m.get("title") or ""
        if not q:
            continue
        prices_raw = m.get("outcomePrices") or "[]"
        try:
            prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
            prices = _parse_binary_prices(prices)
            outcomes = m.get("outcomes")
            outcomes = json.loads(outcomes) if isinstance(outcomes, str) else outcomes
            if not prices or not isinstance(outcomes, list) or len(outcomes) != 2:
                continue
            labels = [str(label).strip().casefold() for label in outcomes]
            if set(labels) != {"yes", "no"}:
                continue
            yes_price = prices[labels.index("yes")]
        except Exception:
            continue
        idx.append({
            "words": _distinctive_words(q),
            "nums": _numeric_tokens(q),
            "propers": _proper_nouns(q),
            "yes_price": yes_price,
            "fee_rate": pm_fees.fee_rate(m),
            "fee_market": m,
            "question": q,
            "slug": m.get("slug") or "",
            "description": m.get("description") or "",
        })
    return idx


def verify_resolution_match(lim_desc: str, pm_desc: str,
                             lim_title: str, pm_question: str) -> tuple[str, str]:
    """Ask a fast scoped worker whether two criteria resolve identically.

    Returns (verdict, reason) where verdict is one of IDENTICAL / SIMILAR /
    DIFFERENT / UNCERTAIN. On agent error, returns (UNCERTAIN, reason).

    Used only to prioritize human review. Even IDENTICAL is an agent judgment,
    not proof of resolution identity or authorization to deploy capital.
    """
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
        r = run_agent(prompt, profile="fast", effort="low", timeout=45)
        if r.returncode != 0:
            return ("UNCERTAIN", f"agent exited {r.returncode}")
        line = (r.stdout or "").strip().splitlines()[0] if r.stdout else ""
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
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


def _write_empty_latest_scan() -> None:
    """Replace any prior candidate payload when this scan finds no leaves."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "generated_at": ts,
        "total_candidates": 0,
        "matched_count": 0,
        "normalization": LAST_ARB_NORMALIZATION_STATS,
        "screening_only": True,
        "execution_ready": False,
        "verified_identical": [],
        "verified_other": [],
    }
    (OUT_DIR / "limitless_arb_latest.json").write_text(json.dumps(payload, indent=2))
    print(f"wrote {OUT_DIR / 'limitless_arb_latest.json'}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--threshold-edge", type=float, default=0.015,
                   help="conditional midpoint-edge threshold for review (default 1.5%)")
    p.add_argument("--notify", action="store_true",
                   help="post a Telegram if any candidate clears the threshold")
    p.add_argument("--max-show", type=int, default=40)
    args = p.parse_args()

    print("fetching Limitless active markets (isPolyArbitrage filter)...")
    try:
        cands = fetch_arb_candidates()
    except (RuntimeError, ValueError) as exc:
        print(f"ABORT: Limitless universe unavailable: {exc}", file=sys.stderr)
        return 2
    # Keep the execution boundary fail-closed even when a caller/test supplies
    # candidates without going through fetch_arb_candidates().
    valid: list[dict] = []
    for candidate in cands:
        if not str(candidate.get("id") or "").strip() or not str(candidate.get("slug") or "").strip():
            _record_exclusion(LAST_ARB_NORMALIZATION_STATS, "missing_leaf_identity")
            continue
        if not _market_title(candidate):
            _record_exclusion(LAST_ARB_NORMALIZATION_STATS, "missing_leaf_title")
            continue
        prices = _parse_binary_prices(candidate.get("prices"))
        tokens = _parse_binary_tokens(candidate.get("tokens"))
        if prices is None:
            _record_exclusion(LAST_ARB_NORMALIZATION_STATS, "missing_or_malformed_prices")
            continue
        if tokens is None:
            _record_exclusion(LAST_ARB_NORMALIZATION_STATS, "missing_or_duplicate_tokens")
            continue
        candidate["prices"] = prices
        candidate["tokens"] = tokens
        valid.append(candidate)
    cands = valid
    print(f"found {len(cands)} candidates")
    excluded = int(LAST_ARB_NORMALIZATION_STATS.get("excluded", 0))
    if excluded:
        print(f"excluded {excluded} malformed/duplicate/non-leaf records: "
              f"{LAST_ARB_NORMALIZATION_STATS.get('exclusions', {})}")
    if not cands:
        _write_empty_latest_scan()
        return 0

    # Annotate each with breakeven + arbability
    for m in cands:
        prices = m["prices"]
        yes_price = prices[0]
        m["_yes_price"] = yes_price
        m["_breakeven"] = round_trip_breakeven(yes_price)

    # Sort: lowest-breakeven first (easiest arbs)
    cands.sort(key=lambda m: m["_breakeven"])

    # Pull a wide slice of the Polymarket active-market universe and build a
    # client-side index for fuzzy matching (gamma-api ?q= search is broken;
    # it ignores the query and returns the same default page).
    print("pulling bounded Polymarket active-market universe "
          "(official gamma-api keyset pagination)...")
    try:
        pm_fetch = fetch_polymarket_universe(
            max_markets=POLYMARKET_UNIVERSE_LIMIT)
    except (RuntimeError, ValueError) as exc:
        print(f"ABORT: Polymarket universe unavailable: {exc}", file=sys.stderr)
        return 2
    print(f"  coverage: {pm_fetch.coverage_label}")
    print(f"  pulled {len(pm_fetch.markets)} markets, indexing...")
    pm_index = index_polymarket(pm_fetch.markets)
    print(f"  indexed {len(pm_index)} markets with valid prices")

    # Match each candidate
    top_for_lookup = cands[: max(args.max_show, 50)]
    print(f"\nfuzzy-matching top {len(top_for_lookup)} candidates...")
    for m in top_for_lookup:
        result = fuzzy_match(m.get("_match_title") or m["title"], pm_index)
        if result:
            m["_pm_yes"] = result["yes_price"]
            m["_pm_question"] = result["question"]
            m["_pm_slug"] = result["slug"]
            m["_pm_description"] = result["description"]
            m["_pm_fee_rate"] = result["fee_rate"]
            m["_match_confidence"] = result["_jaccard"]
            m["_spread"] = result["yes_price"] - m["_yes_price"]
            # Conditional Limitless bound plus the full PM fee descriptor.
            m["_breakeven"] = arb_breakeven(
                m["_yes_price"], result["yes_price"], result["fee_market"]
            )
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
          f"profitable matches with a scoped worker...")
    for m in matched_for_verify:
        verdict, reason = verify_resolution_match(
            lim_desc=m.get("_match_description", m.get("description", "")),
            pm_desc=m.get("_pm_description", ""),
            lim_title=m.get("_match_title") or m["title"],
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
        f.write(f"Polymarket universe coverage: **{pm_fetch.coverage_label}**\n")
        f.write(f"Polymarket-matched (top {len(top_for_lookup)} by breakeven): {len(matched)}\n\n")
        f.write("Three-layer screening: (1) distinctive-word overlap ≥ 3 with Jaccard ≥ 0.55, ")
        f.write("(2) numeric-token parity, (3) agent-verified resolution-language equivalence ")
        f.write("(scoped fast profile). Only `IDENTICAL` verdicts qualify for manual review; ")
        f.write("`SIMILAR`/`UNCERTAIN`/`DIFFERENT` are visibility-only. Downstream ")
        f.write("auto-execution remains disabled.\n\n")
        f.write("Polymarket uses its full feeSchedule rate/exponent via pm_fees.py. ")
        f.write("Limitless assumes at most 3% of received contracts deducted: ")
        f.write("cash per net share = price / 0.97, not price plus a notional fee. ")
        f.write("Net edge = |midpoint spread| minus incremental fee costs per net share. ")
        f.write("Positive is conditional screening only, not executable profit: exact ")
        f.write("fees/rounding, book depth/freshness and rule equivalence remain unverified.\n\n")
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
        "normalization": LAST_ARB_NORMALIZATION_STATS,
        "polymarket_universe": pm_fetch.metadata(),
        "screening_only": True,
        "execution_ready": False,
        "limitless_contract_fee_bound": LIMITLESS_CONTRACT_FEE_BOUND,
        "verified_identical": [],
        "verified_other": [],
    }
    for m in matched:
        chainlink_enabled = bool((m.get("metadata") or {})
                                  .get("chainlinkDataStream", {}).get("enabled"))
        record = {
            "lim_id": m["id"],
            "lim_slug": m["slug"],
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
            "pm_fee_rate_raw": m.get("_pm_fee_rate"),
            "spread": m["_spread"],
            "breakeven": m["_breakeven"],
            "net_edge": m["_net_edge"],
            "screening_only": True,
            "execution_ready": False,
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
        lines = [f"Limitless screening ONLY: {len(mechanical)} mechanical-resolution IDENTICAL "
                 f"candidate(s) above {args.threshold_edge*100:.1f}% conditional midpoint edge; "
                 "not execution-ready"]
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
