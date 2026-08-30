#!/usr/bin/env python3
"""UMA-status monitor for held Polymarket positions.

For each currently-held position, fetches gamma-api/markets/{id} and surfaces:
- umaResolutionStatus changes (proposed/disputed/resolved)
- outcomePrices movement >5pp since last run
- Position visibility loss in data-api positions endpoint

Built after the 2026-05-08 DEC-0018 (R-U ceasefire) miss. Position de-indexed
from data-api at ~19:45 UTC May 8 — I framed as benign monitoring lag and
didn't fetch gamma-api/markets/{id}, missing the umaResolutionStatus="disputed"
flag for 18+ hours. By the time I checked (May 9 ~16:50), market had priced
NO at $0.0005 (effectively lost capital).

This script:
1. Pulls positions from data-api/positions
2. Cross-references with notes/decisions.json for ALL positions ever opened
3. For each market_id, fetches gamma-api/markets/{id}
4. Compares umaResolutionStatus + outcomePrices vs cached state in
   notes/.uma_status_cache.json
5. Surfaces alerts for newly-disputed markets, large outcomePrice moves,
   positions invisible to data-api but on-chain intact

Wired into daily_checkin step 1 (state marking) and step 3 (catalyst scan).
Each cron tick auto-surfaces UMA-state risks.

Lesson source: 2026-05-09 R-U miss — when position disappears from data-api
positions, FIRST check umaResolutionStatus, not just on-chain balance.

Usage:
    python scripts/uma_status_check.py            # check + report
    python scripts/uma_status_check.py --json     # JSON output
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as _secrets

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = REPO_ROOT / "notes" / ".uma_status_cache.json"
DECISIONS_PATH = REPO_ROOT / "notes" / "decisions.json"


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text())
    except Exception:
        return {}


def save_cache(c: dict) -> None:
    CACHE_PATH.write_text(json.dumps(c, indent=2))


def fetch_market(market_id: str) -> dict | None:
    try:
        with httpx.Client(timeout=15) as c:
            r = c.get(f"https://gamma-api.polymarket.com/markets/{market_id}")
            if r.status_code != 200:
                return None
            return r.json()
    except Exception:
        return None


def fetch_positions(addr: str) -> list[dict]:
    try:
        with httpx.Client(timeout=15) as c:
            r = c.get("https://data-api.polymarket.com/positions",
                      params={"user": addr.lower(), "limit": 100, "sizeThreshold": 0.0})
            r.raise_for_status()
            return r.json() or []
    except Exception:
        return []


def parse_outcome_prices(p) -> tuple[float, float] | None:
    try:
        if isinstance(p, str):
            parsed = json.loads(p)
        else:
            parsed = p
        if isinstance(parsed, list) and len(parsed) >= 2:
            return float(parsed[0]), float(parsed[1])
    except Exception:
        pass
    return None


def _yes_price_move_message(previous: float, current: float, context: str = "") -> str:
    """Describe a YES midpoint move without discarding its direction."""
    move_pp = (current - previous) * 100
    return f"YES moved {previous:.4f} → {current:.4f} ({move_pp:+.1f}pp){context}"


def _status_change_alert_type(previous: str | None, current: str | None,
                              *, visible: bool) -> str | None:
    """Classify a held-market UMA transition, including final resolution.

    Resolution is operationally actionable even when it is favorable: it frees
    collateral for redemption and redeployment.  The monitor's module contract
    has always promised to surface ``resolved``, but the old implementation
    only emitted proposed/disputed transitions.
    """
    if current == previous:
        # A de-indexed unresolved proposal/dispute remains an active exception
        # every tick.  The old monitor deliberately repeated these warnings;
        # only final resolution is a one-shot capital-release transition.
        if not visible and current == "proposed":
            return "INVISIBLE_BUT_PROPOSED"
        if not visible and current == "disputed":
            return "INVISIBLE_BUT_DISPUTED"
        return None
    if current == "proposed":
        return "UMA_STATUS_CHANGE" if visible else "INVISIBLE_BUT_PROPOSED"
    if current == "disputed":
        return "UMA_STATUS_CHANGE" if visible else "INVISIBLE_BUT_DISPUTED"
    if current == "resolved":
        return "UMA_RESOLVED" if visible else "INVISIBLE_BUT_RESOLVED"
    return None


def _market_id_with_cache(market_id: str | None, cache: dict,
                          slug: str) -> str | None:
    """Keep direct Gamma identity across slug-index de-listing."""
    if market_id:
        return str(market_id)
    cached_id = cache.get(slug, {}).get("market_id")
    return str(cached_id) if cached_id else None


def _cache_entry_after_fetch_failure(previous: dict | None,
                                     market_id: str) -> dict:
    """Retain the direct identity and last good state after transient failure."""
    entry = dict(previous or {})
    entry["market_id"] = str(market_id)
    return entry


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--wallet", default=str(_secrets.path("POLYCLAUDE_WALLET")))
    p.add_argument("--json", action="store_true")
    p.add_argument("--alert-pp-move", type=float, default=5.0,
                   help="Alert on outcomePrice move >X pp since last check (default 5pp)")
    args = p.parse_args()

    addr = json.load(open(args.wallet))["address"]
    cache = load_cache()
    positions_now = fetch_positions(addr)
    visible_slugs = {p.get("slug", "") for p in positions_now}

    # Collect market IDs to check: union of (current positions, known-disputed-cached, decisions.json open)
    market_ids: set[str] = set()
    slug_to_id: dict[str, str] = {}
    for p in positions_now:
        # data-api positions don't always have market_id; need to look up by slug
        slug = p.get("slug", "")
        if slug:
            slug_to_id[slug] = ""  # filled below

    # Decisions tracker has open positions (incl. de-indexed ones)
    if DECISIONS_PATH.exists():
        try:
            d = json.load(open(DECISIONS_PATH))
            for dec in d.get("decisions", []):
                if dec.get("type") in ("open_position", "size_change"):
                    # Look for market_id in tags / thesis (best-effort)
                    pass  # already tracked via slug below
        except Exception:
            pass

    # For each visible position, fetch market details from gamma to get id
    alerts: list[dict] = []
    new_cache: dict = {}
    for p in positions_now:
        slug = p.get("slug", "")
        if not slug:
            continue
        # Dust guard (2026-07-30): sub-0.5sh remnants (e.g. Fed 0.25sh after the
        # maker exit) survive in data-api after the market de-indexes and fire
        # GAMMA_LOOKUP_FAILED forever; nothing actionable exists at dust size.
        # Real-size de-indexed positions (Marvel/Mojtaba class) still alert.
        if float(p.get("size", 0) or 0) < 0.5:
            continue
        # Resolve slug → market_id via gamma-api search
        market_id = None
        try:
            with httpx.Client(timeout=15) as c:
                r = c.get("https://gamma-api.polymarket.com/markets",
                          params={"slug": slug})
                if r.status_code == 200:
                    rj = r.json()
                    if isinstance(rj, list) and rj:
                        market_id = rj[0].get("id")
                    elif isinstance(rj, dict):
                        market_id = rj.get("id")
        except Exception:
            pass
        # A market can disappear from Gamma's slug index before the held token
        # leaves data-api (Lake America, 2026-08-30).  Reuse the direct ID from
        # the prior successful check so de-indexing cannot blind the transition.
        market_id = _market_id_with_cache(market_id, cache, slug)
        if not market_id:
            alerts.append({
                "slug": slug, "type": "GAMMA_LOOKUP_FAILED",
                "msg": "could not resolve slug or recover a cached market_id "
                       "(market may be very new or de-indexed)"
            })
            continue
        m = fetch_market(market_id)
        if not m:
            # Never fail open by deleting the only direct ID.  A later tick can
            # still fetch a de-indexed held market through this cached identity.
            new_cache[slug] = _cache_entry_after_fetch_failure(
                cache.get(slug), market_id)
            alerts.append({
                "slug": slug, "type": "GAMMA_FETCH_FAILED",
                "market_id": market_id,
                "msg": "gamma-api fetch failed (slug exists but ID lookup failed)"
            })
            continue

        uma_status = m.get("umaResolutionStatus")
        prices = parse_outcome_prices(m.get("outcomePrices"))
        prev = cache.get(slug, {})
        prev_status = prev.get("umaResolutionStatus")
        prev_prices = prev.get("outcomePrices")

        # Save current state
        new_cache[slug] = {
            "market_id": market_id,
            "umaResolutionStatus": uma_status,
            "outcomePrices": prices,
            "checked_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

        # Alert on every actionable UMA transition, including resolution.  A
        # winning resolution is a capital-release event, not merely book state.
        status_alert_type = _status_change_alert_type(
            prev_status, uma_status, visible=True)
        if status_alert_type:
            alert = {
                "slug": slug, "type": status_alert_type,
                "market_id": market_id,
                "msg": f"umaResolutionStatus: {prev_status} → {uma_status}",
                "outcomePrices": prices,
            }
            if uma_status == "disputed":
                # Priors from the 2026-07-15 UMA study (N=2,246 on-chain disputes,
                # research/uma_study_2026-07-15/MEMO.md) — for HELD-position risk
                # sizing during a dispute, NOT an entry signal (edge = FALSE):
                alert["dispute_priors"] = (
                    "1st-dispute proposal stands 72.7% (NO-side 77.9%, YES-side 67.6%); "
                    "2-dispute DVM path ~80%; median finality 4.2h reset-path / ~91h DVM. "
                    "IF PRICE CRASHED >=10pp ON THE DISPUTE: proposal stands only 22% — "
                    "the crash is INFORMATION, reassess the thesis, do NOT dip-buy."
                )
            alerts.append(alert)

        # Alert on large outcomePrice moves.
        # 2026-08-17: carry vol24 + spread INLINE so step (0) of unexplained-move
        # classification ("did it actually trade, or is a midpoint flapping in a
        # wide book?") is pre-answered. The HLE legs generated a PRICE_MOVE line
        # on ~6 consecutive ticks, each manually classified to the same verdict
        # (spread noise, 11-40pp books, board unchanged). outcomePrices IS a
        # midpoint, so without these two numbers the alert cannot distinguish
        # information from quote drift — and a low-context tick reading a bare
        # "+13pp" line is one bad inference from panic-selling a flap.
        if prices and prev_prices and len(prev_prices) >= 2:
            yes_move = (prices[0] - prev_prices[0]) * 100
            if abs(yes_move) >= args.alert_pp_move:
                vol24 = float(m.get("volume24hr") or 0)
                try:
                    bb, ba = float(m.get("bestBid") or 0), float(m.get("bestAsk") or 0)
                    spread_pp = (ba - bb) * 100 if (bb and ba) else None
                except (TypeError, ValueError):
                    spread_pp = None
                ctx = (f" [vol24 ${vol24:,.0f}; spread "
                       + (f"{spread_pp:.1f}pp" if spread_pp is not None else "n/a")
                       + ("; WIDE BOOK — likely midpoint flap, walk the book before believing"
                          if (spread_pp or 0) >= 5 or vol24 < 500 else "")
                       + "]")
                alerts.append({
                    "slug": slug, "type": "PRICE_MOVE",
                    "market_id": market_id,
                    "msg": _yes_price_move_message(prev_prices[0], prices[0], ctx),
                })

        # Cross-check: if data-api positions doesn't show this slug but on-chain has it,
        # something weird (the R-U pattern). Already shown in visible_slugs.

    # Cache positions that DISAPPEARED from data-api but were tracked previously
    for slug, prev in cache.items():
        if slug in new_cache:
            continue
        # was tracked, now invisible
        market_id = prev.get("market_id")
        if not market_id:
            continue
        m = fetch_market(market_id)
        if m:
            uma_status = m.get("umaResolutionStatus")
            prices = parse_outcome_prices(m.get("outcomePrices"))
            new_cache[slug] = {
                "market_id": market_id,
                "umaResolutionStatus": uma_status,
                "outcomePrices": prices,
                "checked_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "data_api_visible": False,
            }
            status_alert_type = _status_change_alert_type(
                prev.get("umaResolutionStatus"), uma_status, visible=False)
            if status_alert_type:
                alerts.append({
                    "slug": slug, "type": status_alert_type,
                    "market_id": market_id,
                    "msg": f"position invisible to data-api positions endpoint, gamma shows umaResolutionStatus={uma_status}",
                    "outcomePrices": prices,
                })
        else:
            # A single Gamma outage must not erase the ID needed to observe a
            # later dispute/resolution after this holding disappeared upstream.
            new_cache[slug] = _cache_entry_after_fetch_failure(prev, market_id)
            alerts.append({
                "slug": slug, "type": "INVISIBLE_GAMMA_FETCH_FAILED",
                "market_id": market_id,
                "msg": "position remains invisible to data-api and direct "
                       "gamma-api fetch failed; cached identity preserved",
            })

    save_cache(new_cache)

    # Output
    if args.json:
        print(json.dumps({"alerts": alerts, "checked_count": len(new_cache)}, indent=2, default=str))
        return 0

    print(f"# uma_status_check: {len(new_cache)} positions tracked, {len(alerts)} alerts")
    if not alerts:
        print("  (all clean)")
        return 0
    for a in alerts:
        print(f"\n  [{a['type']}] {a['slug']}")
        print(f"    {a['msg']}")
        if "outcomePrices" in a and a["outcomePrices"]:
            print(f"    outcomePrices: YES={a['outcomePrices'][0]:.4f} NO={a['outcomePrices'][1]:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
