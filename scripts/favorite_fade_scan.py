#!/usr/bin/env python3
"""Favorite-fade scanner — CANDIDATE SURFACER for instance-thesis evaluation.

*** POPULATION EDGE FALSIFIED 2026-07-03 — do not infer probability or edge from this profile. ***
The original localization (longshot_calibration_backtest.py, N=1513, 2026-06-02:
  0.90-0.95 +4.8pp/3.2sigma, 0.95-0.98 +2.8pp/4.7sigma at ~7d) FAILED REPLICATION on 836
fresh resolved markets (same methodology): 0.90-0.95 -0.5pp+-2.9, 0.95-0.98 -0.5pp+-1.9 —
calibrated at mid, NEGATIVE at executable asks, at both 3d and 7d horizons
(logs/backtest_askadjust_v3_20260703.log; doctrine in AGENTS.md Philosophy §3.1). Either
arbed away since June or the original was window-specific; both forbid POPULATION harvesting.
The historical population calibration is falsified at executable asks and is not used to
estimate probability, edge, yield, selection order, or inclusion. This scanner only surfaces
liquid short-horizon markets whose live favorite ask is in the transparent 0.90-0.98 profile.
Any trade requires independent case-by-case resolution-criteria and catalyst analysis under
the current doctrine, including the 0.10 default haircut for instance/catalyst theses (or the
separately justified 0.05 tail/monitoring-fade class).

This finds current liquid binary markets with a 2-14 day horizon and a favorite live CLOB ask
in the 0.90-0.98 zone. Results are ranked by shorter horizon, then greater liquidity; this is
only a browsing order and carries no probability or expected-return claim.

Compute-bounded: gamma candidate pre-filter, then live-book walks capped at --max-walks.
Rows are candidate-only context, never a buy-list or execution certification. Any later
evaluation must re-read exact criteria and obtain current execution evidence.

Caveats: (1) a favorite-price profile is not a fair-value estimate. (2) resolution ambiguity
is not fully mechanical; proposed/disputed UMA states are skipped, but exact criteria and
catalyst checks remain necessary. (3) these candidate rows are not execution-ready.

CLI: favorite_fade_scan.py [--min-days 2] [--max-days 14] [--min-liq 20000]
                           [--min-edge-pp LEGACY] [--max-walks 40] [--json]
"""
from __future__ import annotations

import argparse
import ast
import json
import math
import sys
from datetime import datetime, timezone

import httpx

from clob_books import fetch_books

GAMMA = "https://gamma-api.polymarket.com/markets"
MAX_BOOK_AGE_SECONDS = 120.0

def _parse(x):
    return ast.literal_eval(x) if isinstance(x, str) else x


def categorize(q: str) -> str:
    """Coarse question category for context only; it is not a probability prior."""
    s = (q or "").lower()
    if any(k in s for k in [" vs ", " vs.", "world cup", "french open", "champion",
                            "premier league", "super bowl", "stanley cup", "nba finals",
                            "win the 2026 men", "win the 2026 women", " beat ", "grand prix",
                            "f1 ", "drivers' champion", "iem ", "major 2026", "playoff",
                            "win on 2026"]):
        return "sports"
    if any(k in s for k in ["bitcoin", "ethereum", "btc", "eth ", "solana", " sol ",
                            "hyperliquid", "dogecoin", "xrp", "price of", "launch a token",
                            "all time high", "market cap"]):
        return "crypto/price"
    if any(k in s for k in ["fed ", "interest rate", "ecb", " cpi", "inflation", "recession",
                            "gdp", "jobs report", "rate cut", "rate hike", "basis point"]):
        return "macro"
    if any(k in s for k in ["president", "election", "senate", "house", "governor",
                            "prime minister", "regime", "coup", "nuclear", "invade", " war",
                            "peace deal", "ceasefire", "sanction", "minister", "parliament",
                            "nominee", "mayor", "impeach", "out as ", "airspace", "blockade",
                            "strait", "leader of", "head of state"]):
        return "politics/geo"
    return "other/meme"


class MarketFetchResult(list):
    """List-compatible market rows with explicit pagination coverage metadata."""

    def __init__(self, rows: list, coverage: dict):
        super().__init__(rows)
        self.coverage = coverage


def fetch_active(max_pages: int, client: httpx.Client) -> MarketFetchResult:
    page_size = 100
    retry_budget = 5
    rows: list[dict] = []
    failures: list[dict] = []
    pages_attempted = 0
    pages_succeeded = 0
    stop_reason = "max_pages"
    complete = False

    if max_pages < 1:
        return MarketFetchResult(rows, {
            "complete": False, "pages_attempted": 0, "pages_succeeded": 0,
            "failures": [], "stop_reason": "invalid_max_pages",
            "command_failed": True,
        })

    for page_index in range(max_pages):
        offset = page_index * page_size
        page = None
        for attempt in range(1, retry_budget + 1):
            pages_attempted += 1
            try:
                response = client.get(GAMMA, params={
                    "closed": "false", "active": "true", "limit": page_size,
                    "offset": offset, "order": "volume24hr", "ascending": "false",
                }, timeout=25)
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
                    raise ValueError("response schema is not a list of market objects")
                page = payload
                pages_succeeded += 1
                break
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else None
                failures.append({
                    "offset": offset, "attempt": attempt,
                    "http_status": status, "reason": "http_status_error",
                })
                if status == 422:
                    stop_reason = "http_422_offset_or_page_limit"
                    break
            except Exception as exc:
                # Keep diagnostics bounded and avoid echoing request URLs or bodies.
                failures.append({
                    "offset": offset, "attempt": attempt,
                    "http_status": getattr(getattr(exc, "response", None), "status_code", None),
                    "reason": "invalid_json_or_schema" if isinstance(exc, ValueError)
                              else type(exc).__name__,
                })
        if page is None:
            if stop_reason != "http_422_offset_or_page_limit":
                stop_reason = "retry_budget_exhausted"
            break
        rows.extend(page)
        if len(page) == 0:
            stop_reason = "valid_empty_page"
            complete = True
            break
        if len(page) < page_size:
            stop_reason = "valid_short_page"
            complete = True
            break
    else:
        # Reaching the configured page cap with full pages is a bounded partial
        # scan; it cannot be represented as complete universe coverage.
        stop_reason = "max_pages"

    return MarketFetchResult(rows, {
        "complete": complete,
        "pages_attempted": pages_attempted,
        "pages_succeeded": pages_succeeded,
        "failures": failures,
        "stop_reason": stop_reason,
        "command_failed": stop_reason == "retry_budget_exhausted",
        "max_pages": max_pages,
        "page_size": page_size,
    })


def _validated_book(book: dict | None, token: str, condition_id: str) -> dict | None:
    """Validate one batched book before using its ask/depth advisory quote."""
    if (not isinstance(book, dict) or book.get("asset_id") != token
            or str(book.get("market") or "").casefold() != condition_id.casefold()):
        return None
    try:
        age = datetime.now(timezone.utc).timestamp() - float(book["timestamp"]) / 1000
        if age < -30 or age > MAX_BOOK_AGE_SECONDS:
            return None
        asks = book["asks"]
        bids = book["bids"]
        if not isinstance(asks, list) or not isinstance(bids, list):
            return None
        def levels(raw):
            out = []
            seen = set()
            for level in raw:
                if not isinstance(level, dict):
                    return None
                price, size = float(level["price"]), float(level["size"])
                if (not math.isfinite(price) or not math.isfinite(size)
                        or not 0 < price < 1 or size <= 0 or price in seen):
                    return None
                seen.add(price)
                out.append((price, size))
            return out
        asks_v, bids_v = levels(asks), levels(bids)
        if asks_v is None or bids_v is None:
            return None
        if asks_v and bids_v and max(p for p, _ in bids_v) >= min(p for p, _ in asks_v):
            return None
        return {"asks": asks_v, "bids": bids_v}
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-days", type=float, default=2.0)
    ap.add_argument("--max-days", type=float, default=14.0)
    ap.add_argument("--min-liq", type=float, default=20000)
    ap.add_argument(
        "--min-edge-pp", type=float, default=None,
        help="deprecated compatibility flag; ignored because historical population edge was falsified",
    )
    ap.add_argument("--max-walks", type=int, default=40)
    ap.add_argument("--max-pages", type=int, default=10)
    ap.add_argument("--exclude-cats", default="",
                    help="optional comma-separated categories to omit from this profile scan")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.min_edge_pp is not None:
        print(
            "WARNING: --min-edge-pp is deprecated and ignored; no population edge is used.",
            file=sys.stderr,
        )
    exclude_cats = {c.strip() for c in args.exclude_cats.split(",") if c.strip()}

    now = datetime.now(timezone.utc)
    with httpx.Client() as client:
        fetched = fetch_active(args.max_pages, client)
        mkts = fetched if isinstance(fetched, list) else []
        fetch_coverage = getattr(fetched, "coverage", None)
        if not isinstance(fetch_coverage, dict):
            fetch_coverage = {
                "complete": False, "pages_attempted": None,
                "pages_succeeded": None, "failures": [],
                "stop_reason": "legacy_list_without_coverage",
                "command_failed": False,
            }
        print(f"# fetched {len(mkts)} active markets", file=sys.stderr)
        cands = []
        for m in mkts:
            if not isinstance(m, dict):
                continue
            # This is a new-entry candidate surfacer. Require explicit current
            # tradability, and never surface resolved/proposed/disputed markets.
            if (m.get("active") is not True or m.get("closed") is not False
                    or m.get("acceptingOrders") is not True
                    or m.get("enableOrderBook") is not True
                    or m.get("archived") is not False):
                continue
            try:
                outcomes = _parse(m.get("outcomes"))
            except (ValueError, SyntaxError, TypeError):
                continue
            if outcomes != ["Yes", "No"]:
                continue
            uma_status = str(m.get("umaResolutionStatus") or "").strip()
            if uma_status:
                continue  # any populated state, including resolved, is not a new entry
            try:
                op = _parse(m.get("outcomePrices") or "[]")
            except (ValueError, SyntaxError, TypeError):
                continue
            if not isinstance(op, list) or len(op) != 2:
                continue
            try:
                yes = float(op[0])
                no = float(op[1])
            except Exception:
                continue
            if (not math.isfinite(yes) or not math.isfinite(no)
                    or not 0 < yes < 1 or not 0 < no < 1):
                continue
            fav = max(yes, 1 - yes)
            if not (0.88 <= fav <= 0.99):  # rough zone; live ask refines
                continue
            end = m.get("endDate")
            if not end:
                continue
            try:
                edt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                if edt.tzinfo is None:
                    edt = edt.replace(tzinfo=timezone.utc)
                days = (edt - now).total_seconds() / 86400
            except Exception:
                continue
            if not math.isfinite(days) or not (args.min_days <= days <= args.max_days):
                continue
            try:
                liq = float(m.get("liquidity") or 0)
                vol24 = float(m.get("volume24hr") or 0)
            except (TypeError, ValueError, OverflowError):
                continue
            if not math.isfinite(liq) or not math.isfinite(vol24):
                continue
            if liq < args.min_liq:
                continue
            try:
                toks = _parse(m.get("clobTokenIds") or "[]")
            except (ValueError, SyntaxError, TypeError):
                continue
            market_id = str(m.get("id") or "")
            slug = str(m.get("slug") or "")
            condition_id = str(m.get("conditionId") or "")
            if (not isinstance(toks, list) or len(toks) != 2
                    or not all(str(token or "") for token in toks)
                    or len({str(token) for token in toks}) != 2
                    or not market_id or not slug or not condition_id):
                continue
            cat = categorize(m.get("question", ""))
            if cat in exclude_cats:
                continue
            # Doctrine-skip pattern classes (2026-07-17 noise cut): these
            # surface every tick and are NEVER instance candidates — exact
            # scorelines (population edge overstated for plausible scores,
            # Jul-02 pre-skip), tweet-count buckets, player props.
            _ql = m.get("question", "").lower()
            if any(p in _ql for p in ("exact score", "tweets from", "tweet count",
                                       "o/u", "over/under", ": assists", ": points",
                                       ": rebounds", "handicap")):
                continue
            fav_is_yes = yes >= 0.5
            cands.append({
                "q": m.get("question", ""), "fav_is_yes": fav_is_yes,
                "market_id": market_id,
                "slug": slug,
                "condition_id": condition_id,
                "yes_tok": str(toks[0]), "no_tok": str(toks[1]),
                "yes_gamma_price": float(op[0]), "no_gamma_price": float(op[1]),
                "days": days, "liq": liq, "cat": cat,
                "vol24": vol24,
            })
        # Sort by deadline and liquidity only. Population calibration is not
        # valid evidence for ranking or filtering these candidates.
        cands.sort(key=lambda c: (c["days"], -c["liq"], c["market_id"]))
        rough_survivors = len(cands)
        cands = cands[:args.max_walks]
        print(f"# {len(cands)} candidates in rough zone; walking live books", file=sys.stderr)

        rows = []
        valid_favorite_books = 0
        missing_favorite_books = 0
        outside_profile_books = 0
        book_batch_error = None
        tokens = list(dict.fromkeys(
            token for c in cands for token in (c["yes_tok"], c["no_tok"])
        ))
        try:
            books = fetch_books(tokens, client=client, timeout=15)
            if not isinstance(books, dict):
                book_batch_error = "invalid_batch_response_type"
                books = {}
        except Exception as exc:
            book_batch_error = type(exc).__name__
            books = {}
        for c in cands:
            if not c["condition_id"]:
                continue
            fav_side = "YES" if c["fav_is_yes"] else "NO"
            opposite_side = "NO" if c["fav_is_yes"] else "YES"
            fav_tok = c["yes_tok"] if c["fav_is_yes"] else c["no_tok"]
            opposite_tok = c["no_tok"] if c["fav_is_yes"] else c["yes_tok"]
            book = _validated_book(books.get(fav_tok), fav_tok, c["condition_id"])
            opposite_book = _validated_book(
                books.get(opposite_tok), opposite_tok, c["condition_id"],
            )
            if book is None or not book["asks"]:
                missing_favorite_books += 1
                continue
            valid_favorite_books += 1
            best = min(book["asks"], key=lambda a: a[0])
            ask = best[0]
            if not 0.90 <= ask <= 0.98:
                outside_profile_books += 1
                continue
            opp_ask = None
            opp_bid = None
            if opposite_book is not None:
                opp_ask = min((p for p, _ in opposite_book["asks"]), default=None)
                opp_bid = max((p for p, _ in opposite_book["bids"]), default=None)
            rows.append({
                "market_id": c["market_id"], "slug": c["slug"],
                "condition_id": c["condition_id"], "question": c["q"],
                "candidate_only": True, "execution_ready": False,
                "live_rewalk_required": True,
                "selected_side": fav_side, "selected_token_id": fav_tok,
                "selected_ask": round(ask, 4),
                "selected_depth_usd_within_2c": round(sum(
                    price * size for price, size in book["asks"] if price <= ask + 0.02
                ), 0),
                "opposite_side": {
                    "side": opposite_side, "token_id": opposite_tok,
                    "gamma_price": c["no_gamma_price"] if c["fav_is_yes"] else c["yes_gamma_price"],
                    "book_validated": opposite_book is not None,
                    "best_ask": round(opp_ask, 4) if opp_ask is not None else None,
                    "best_bid": round(opp_bid, 4) if opp_bid is not None else None,
                },
                "tokens": {"YES": c["yes_tok"], "NO": c["no_tok"]},
                "gamma_prices": {"YES": c["yes_gamma_price"], "NO": c["no_gamma_price"]},
                "days": c["days"], "liquidity": c["liq"],
                "volume24h": c["vol24"], "category": c["cat"],
            })

        coverage_report = {
            "market_fetch": fetch_coverage,
            "rough_survivors_before_book_cap": rough_survivors,
            "max_walks": args.max_walks,
            "walk_cap_omissions": max(0, rough_survivors - len(cands)),
            "selected_for_book_walk": len(cands),
            "valid_favorite_books": valid_favorite_books,
            "missing_or_invalid_favorite_books": missing_favorite_books,
            "valid_books_outside_favorite_price_profile": outside_profile_books,
            "candidate_rows_emitted": len(rows),
            "book_batch_error": book_batch_error,
        }
        print("SCAN_COVERAGE " + json.dumps(coverage_report, sort_keys=True), file=sys.stderr)
        command_failed = bool(fetch_coverage.get("command_failed")) or book_batch_error is not None

    if args.json:
        print(json.dumps(rows, indent=1))
        return 1 if command_failed else 0
    print(f"\n# {len(rows)} favorite-price profile candidates (live ask 0.90-0.98, "
          f"{args.min_days:.0f}-{args.max_days:.0f}d; no probability/edge estimate)\n")
    if not rows:
        print("  none")
        return 1 if command_failed else 0
    print(f"{'side':>4} {'ask':>6} {'days':>5} {'depth$':>9} {'liq$':>10} {'cat':>12}  question")
    print("-" * 92)
    for r in rows:
        side = r["selected_side"]
        print(f"{side:>4} {r['selected_ask']:.3f} {r['days']:>4.0f}d "
              f"{r['selected_depth_usd_within_2c']:>9.0f} {r['liquidity']:>10.0f} "
              f"{r['category']:>12}  {r['question'][:50]}")
    print("\n# Profile only: these rows contain no probability, edge, or APY estimate and "
          "are not execution-ready.")
    return 1 if command_failed else 0


if __name__ == "__main__":
    sys.exit(main())
