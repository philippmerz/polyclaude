"""Pull active markets from Polymarket gamma API, filter for tradability and quality,
and emit a JSON snapshot to data/snapshots/<UTC ts>.json plus a markdown shortlist.

Read-only. Safe to run frequently.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

import httpx

GAMMA = "https://gamma-api.polymarket.com"
DATA = Path(__file__).resolve().parent.parent / "data"
SNAP_DIR = DATA / "snapshots"

import pm_fees  # per-market takerBaseFee; no single fee constant is correct

# Hurdle APY: any new bond-like NO/YES buy must beat this (idle USDC in Aave).
# 2026-08-14: this sat at 0.034 — an Aave-Base snapshot taken 2026-05-08 and
# never refreshed, despite a comment instructing exactly that. It is now read
# live (24h cache) from check_marginal_apy._live_hurdle so the ENTRY filter and
# the HOLD/close scan cannot silently disagree about the cost of capital, which
# is how you end up buying something you would immediately flag for closing.
HURDLE_APY_FALLBACK = 0.05


def live_hurdle_apy() -> float:
    """Resolved LAZILY, not at import. Module-level network I/O made this file
    unimportable offline and therefore untestable — which is how the fee bugs
    below survived: nothing could assert on them without a working RPC. Called
    once from main(); the 24h cache in check_marginal_apy absorbs the cost."""
    try:
        from check_marginal_apy import _live_hurdle
        return _live_hurdle()[0]
    except Exception:
        return HURDLE_APY_FALLBACK
# 2026-05-08: 7-day-to-resolution floor relaxed to 3 days — sub-week catalyst trades
# (e.g. DEC-0015 at 6.5d) have positive expected value despite annualization noise.
# The hurdle filter compares APY-equivalent yield, so sub-week trades that pass the
# threshold ARE genuinely attractive — the prior floor was overcautious.
HURDLE_DAYS_FLOOR_DEFAULT = 3


def annualized_yield_after_fee(p_buy: float, days: float,
                               market: dict | None = None) -> float | None:
    """For a buy at price p_buy resolving in `days` days, return APY assuming
    the buy side wins. None if degenerate (p_buy >= 1, days <= 1).

    2026-08-14 — TWO independent fee errors fixed here, both understating cost
    in the ENTRY filter, i.e. both making candidates look better than they are:

      1. The rate was hard-coded 0.072; the live modal rate is 0.10 and 16% of
         markets charge nothing. It is a per-market field (takerBaseFee).
      2. The fee was applied MULTIPLICATIVELY: `p_buy * (1 + fee_fraction)`.
         Polymarket charges rate x min(p, 1-p) in dollars PER SHARE, so it is
         additive. Multiplying scaled the fee by p_buy and understated it
         everywhere, worst at mid prices: at p=0.50 with the true 10% rate the
         real cost is 0.550 while this returned 0.518.

    Together they understated cost by ~3.2pp at p=0.50, which inflates the APY
    that the hurdle filter then compares against.
    """
    if p_buy >= 0.999 or days < 1.0:
        return None
    cost = p_buy + pm_fees.fee_per_share(market, p_buy)
    if cost >= 1.0:
        return None
    gross = (1.0 - cost) / cost
    # Cap gross at 99x to avoid overflow on tiny p_buy (e.g. 0.01 → 99x gross)
    gross = min(gross, 99.0)
    try:
        return (1.0 + gross) ** (365.0 / days) - 1.0
    except OverflowError:
        return float("inf")  # effectively infinite APY for ultra-short tail trades


def fetch_active_via_events(limit_per_page: int = 100, max_pages: int = 20) -> list[dict[str, Any]]:
    """Fetch active markets by paginating EVENTS (vol24 desc) and flattening members.

    Why (2026-08-01): the /markets endpoint's offset ceiling (~2000, 422 above)
    cuts off at ~$1.9k/day vol24, and ascending only reaches ~$10/day — markets
    between are UNREACHABLE by either direction (the HLE legs at ~$150/day sat
    in that dead zone, invisible to every scan until the operator browsed into
    them). The EVENTS universe is much smaller: 20 pages reach down to
    ~$240/day event-vol, spanning the thin tail where mispricings persist.
    Event-embedded market dicts carry the same fields the pipeline needs;
    the parent event is attached under 'events' for group-aware consumers.
    """
    out: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    with httpx.Client(timeout=20.0) as c:
        for page in range(max_pages):
            r = c.get(
                f"{GAMMA}/events",
                params={
                    "closed": "false", "archived": "false", "active": "true",
                    "limit": str(limit_per_page),
                    "offset": str(page * limit_per_page),
                    "order": "volume24hr", "ascending": "false",
                },
            )
            if r.status_code == 422:
                break
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            for ev in batch:
                for m in ev.get("markets") or []:
                    mid = str(m.get("id"))
                    if mid in seen_ids:
                        continue
                    seen_ids.add(mid)
                    m.setdefault("events", [{"id": ev.get("id"), "title": ev.get("title")}])
                    out.append(m)
            if len(batch) < limit_per_page:
                break
    return out


def fetch_active(limit_per_page: int = 100, max_pages: int = 8) -> list[dict[str, Any]]:
    """Fetch active+open markets sorted by 24h volume desc, paginated.

    NOTE (2026-05-29 fix): the gamma API hard-caps every response at 100 rows
    regardless of the `limit` param. The prior default limit_per_page=500 meant
    the very first page returned 100 < 500, tripping the short-batch break — so
    the scan only ever saw the TOP 100 markets by volume (vol24h >= ~$225k) and
    NEVER fetched the long tail. That silently capped sourcing at ~10% of intent
    and excluded exactly the neglected by-date longshots the strategy names as
    the edge zone ("the long tail is where mispricings live"). Setting page size
    to the API's true 100 lets pagination walk the tail: max_pages=8 → ~800
    markets, reaching down to ~$15-40k-vol mechanical-resolution fades."""
    out: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    with httpx.Client(timeout=20.0) as c:
        for page in range(max_pages):
            r = c.get(
                f"{GAMMA}/markets",
                params={
                    "closed": "false",
                    "archived": "false",
                    "active": "true",
                    "limit": str(limit_per_page),
                    "offset": str(page * limit_per_page),
                    "order": "volume24hr",
                    "ascending": "false",
                },
            )
            if r.status_code == 422:
                # gamma rejects offset >~2000 — the API's own pagination
                # ceiling. Stop cleanly with what we have (2026-08-01).
                break
            r.raise_for_status()
            batch = r.json()
            # Early-stop (2026-08-01): pages are volume24hr-DESC, so once a
            # page's minimum vol24 drops below ~$10 the remaining tail is dead
            # junk — stop paginating instead of walking 40 pages of zeros.
            # (Context: the volume-ordered fetch is itself a filter — HLE legs
            # at ~$150/day vol ranked below the top-1000 and were never even
            # FETCHED, making every downstream liquidity-floor debate moot.)
            if batch:
                try:
                    if max(float(m.get("volume24hr") or 0) for m in batch) < 10:
                        out.extend(m for m in batch if str(m.get("id")) not in seen_ids)
                        break
                except Exception:
                    pass
            if not batch:
                break
            for m in batch:
                mid = str(m.get("id"))
                if mid not in seen_ids:
                    seen_ids.add(mid)
                    out.append(m)
            # The API caps at 100/page; only stop when a page comes back SHORT of
            # that true cap (i.e., genuinely the end), not short of our request.
            if len(batch) < limit_per_page:
                break
    return out


def parse_outcome_prices(m: dict[str, Any]) -> tuple[float, float] | None:
    """Return (yes_price, no_price) for binary markets, else None."""
    raw = m.get("outcomePrices")
    outs = m.get("outcomes")
    if not raw or not outs:
        return None
    try:
        prices = json.loads(raw) if isinstance(raw, str) else raw
        outs_l = json.loads(outs) if isinstance(outs, str) else outs
    except Exception:
        return None
    if len(prices) != 2 or set(map(str, outs_l)) != {"Yes", "No"}:
        return None
    p_yes = float(prices[outs_l.index("Yes")])
    p_no = float(prices[outs_l.index("No")])
    return p_yes, p_no


def is_tradable(m: dict[str, Any]) -> bool:
    return bool(
        m.get("acceptingOrders")
        and m.get("enableOrderBook")
        and not m.get("closed")
        and not m.get("archived")
    )


def is_quality(m: dict[str, Any], min_liq: float, min_vol24: float, max_spread: float) -> bool:
    if not is_tradable(m):
        return False
    if float(m.get("liquidityNum") or 0) < min_liq:
        return False
    if float(m.get("volume24hr") or 0) < min_vol24:
        return False
    spread = m.get("spread")
    if spread is not None and float(spread) > max_spread:
        return False
    end = m.get("endDate") or m.get("endDateIso")
    if not end:
        return False
    return True


def days_to_resolution(m: dict[str, Any], now: dt.datetime) -> float | None:
    end = m.get("endDate") or m.get("endDateIso")
    if not end:
        return None
    try:
        if "T" in end:
            t = dt.datetime.fromisoformat(end.replace("Z", "+00:00"))
        else:
            t = dt.datetime.fromisoformat(end + "T00:00:00+00:00")
        return (t - now).total_seconds() / 86400
    except Exception:
        return None


def category_of(m: dict[str, Any]) -> str:
    """Heuristic category from question/event/tag fields."""
    q = (m.get("question") or "").lower()
    desc = (m.get("description") or "").lower()
    text = q + " " + desc
    if m.get("sportsMarketType") or any(
        k in text for k in [" vs. ", " vs ", "premier league", "serie a", "nba", "nfl", "nhl", "mlb", "uefa", "fifa"]
    ):
        return "sports"
    if any(k in text for k in ["bitcoin", "ethereum", "btc", "eth", "solana", "$1", "memecoin", "crypto"]):
        return "crypto"
    if any(k in text for k in ["fed", "interest rate", "cpi", "inflation", "recession", "gdp", "unemployment", "fomc", "rate cut", "treasury"]):
        return "macro"
    if any(k in text for k in [
        "election", "primary", "president", "senator", "congress", "house seat",
        "uk", "germany", "france", "russia", "putin", "ukraine", "israel", "gaza", "iran", "nato", "china",
        "taiwan", "war", "ceasefire", "treaty", "sanction", "tariff",
    ]):
        return "geopolitics"
    if any(k in text for k in ["openai", "anthropic", "google", "chatgpt", "gpt-", "ai ", "agi", "model release", "stargate", "tesla", "nvidia", "apple", "microsoft", "tiktok"]):
        return "tech"
    if any(k in text for k in ["movie", "box office", "oscar", "billboard", "song", "spotify", "album"]):
        return "entertainment"
    return "other"


def shortlist(
    markets: list[dict[str, Any]],
    *,
    min_liq: float,
    min_vol24: float,
    max_spread: float,
    horizon_days: float,
    top_n: int,
    hurdle_apy: float | None = None,
    hurdle_days_floor: float = HURDLE_DAYS_FLOOR_DEFAULT,
) -> list[dict[str, Any]]:
    # None means "resolve it yourself" — main() normally passes a value, but a
    # library caller taking the default must not reach the `> hurdle_apy`
    # comparison with None and hit a TypeError.
    if hurdle_apy is None:
        hurdle_apy = live_hurdle_apy()
    now = dt.datetime.now(dt.timezone.utc)
    rows: list[dict[str, Any]] = []
    for m in markets:
        if not is_quality(m, min_liq, min_vol24, max_spread):
            continue
        ttr = days_to_resolution(m, now)
        if ttr is None or ttr <= 0 or ttr > horizon_days:
            continue
        prices = parse_outcome_prices(m)
        if prices is None:
            yes = None
            no = None
            apy_dominant = None
            dominant_side = None
        else:
            yes, no = prices
            # Bond-like trade = buy the EXPENSIVE side (= bet against the tail).
            # If YES > 0.5 the bond-like buy is YES at p_yes; if YES < 0.5 it's
            # NO at p_no. APY = annualized yield-to-resolution if the dominant
            # outcome wins, after Polymarket fees.
            if yes >= 0.5:
                dominant_side = "YES"
                apy_dominant = annualized_yield_after_fee(yes, ttr, m)
            else:
                dominant_side = "NO"
                apy_dominant = annualized_yield_after_fee(no, ttr, m)
        rows.append({
            "id": m.get("id"),
            "slug": m.get("slug"),
            "question": m.get("question"),
            "category": category_of(m),
            "yes_price": yes,
            "no_price": no,
            "spread": float(m.get("spread") or 0),
            "best_bid": float(m.get("bestBid") or 0),
            "best_ask": float(m.get("bestAsk") or 0),
            "liquidity": float(m.get("liquidityNum") or 0),
            "vol24h": float(m.get("volume24hr") or 0),
            "vol_total": float(m.get("volumeNum") or m.get("volume") or 0) if not isinstance(m.get("volume"), str) else float(m.get("volume") or 0),
            "days_to_resolve": round(ttr, 2),
            "neg_risk": bool(m.get("negRisk")),
            "fees_enabled": bool(m.get("feesEnabled")),
            "fee_rate": (m.get("feeSchedule") or {}).get("rate"),
            "min_size_usd": float(m.get("orderMinSize") or 0),
            "tick": float(m.get("orderPriceMinTickSize") or 0.01),
            "clob_token_ids": m.get("clobTokenIds"),
            "end_date": m.get("endDate"),
            "url": f"https://polymarket.com/market/{m.get('slug')}",
            "dominant_side": dominant_side,
            "apy_dominant": round(apy_dominant, 4) if apy_dominant is not None and apy_dominant != float("inf") else None,
            "clears_hurdle": bool(
                apy_dominant is not None
                and apy_dominant > hurdle_apy
                and ttr >= hurdle_days_floor
            ),
        })
    rows.sort(key=lambda r: (-r["vol24h"], -r["liquidity"]))
    return rows[:top_n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-liquidity", type=float, default=20_000)
    ap.add_argument("--min-vol24", type=float, default=500,
                    help="Min 24h volume. Lowered 2026-05-29 from 2000 → 500: for a TAKER "
                         "lifting a resting NO/YES ask, fillability is guaranteed by --min-liquidity "
                         "(book depth), not recent volume. A high volume floor re-excluded the quiet, "
                         "neglected by-date tail — which is precisely where mispricings live (low volume "
                         "BECAUSE neglected). Liquidity + spread floors keep junk out.")
    ap.add_argument("--max-spread", type=float, default=0.05)
    ap.add_argument("--horizon-days", type=float, default=370)
    ap.add_argument("--top", type=int, default=80)
    ap.add_argument("--max-pages", type=int, default=10)
    ap.add_argument("--no-snapshot", action="store_true")
    ap.add_argument("--via-events", action="store_true",
                    help="fetch via /events pagination (reaches the thin tail the "
                         "/markets offset ceiling hides — see fetch_active_via_events)")
    ap.add_argument("--clears-hurdle-only", action="store_true",
                    help="filter to candidates whose dominant-side APY beats the Aave hurdle")
    ap.add_argument("--hurdle-apy", type=float, default=None,
                    help="hurdle APY for clears-hurdle filter (default: LIVE Aave-Polygon, 24h cache)")
    ap.add_argument("--hurdle-days-floor", type=float, default=HURDLE_DAYS_FLOOR_DEFAULT,
                    help=f"minimum days-to-resolution for hurdle filter (default: {HURDLE_DAYS_FLOOR_DEFAULT})")
    ap.add_argument("--check-catalysts", type=int, default=0, metavar="N",
                    help="run scripts/catalyst_check.py on the top N candidates (after filtering). "
                         "Each check spawns claude -p haiku with WebSearch (~5-10K tokens, ~30-60s). "
                         "0 = skip (default).")
    args = ap.parse_args()

    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    if args.via_events:
        markets = fetch_active_via_events(max_pages=args.max_pages)
    else:
        markets = fetch_active(max_pages=args.max_pages)
    print(f"fetched {len(markets)} active markets")

    if args.hurdle_apy is None:
        args.hurdle_apy = live_hurdle_apy()
    short = shortlist(
        markets,
        min_liq=args.min_liquidity,
        min_vol24=args.min_vol24,
        max_spread=args.max_spread,
        horizon_days=args.horizon_days,
        top_n=args.top,
        hurdle_apy=args.hurdle_apy,
        hurdle_days_floor=args.hurdle_days_floor,
    )
    if args.clears_hurdle_only:
        short = [r for r in short if r.get("clears_hurdle")]
        print(f"filtered to {len(short)} candidates clearing {args.hurdle_apy*100:.2f}% APY / {args.hurdle_days_floor:.0f}d-floor hurdle")

    if not args.no_snapshot:
        ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        snap_path = SNAP_DIR / f"shortlist_{ts}.json"
        snap_path.write_text(json.dumps(short, indent=2))
        latest = SNAP_DIR / "shortlist_latest.json"
        try:
            if latest.exists() or latest.is_symlink():
                latest.unlink()
        except FileNotFoundError:
            pass
        os.symlink(snap_path.name, latest)
        print(f"wrote {snap_path}")

    # Also print a compact table
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for r in short:
        by_cat.setdefault(r["category"], []).append(r)
    for cat in sorted(by_cat, key=lambda k: -sum(r["vol24h"] for r in by_cat[k])):
        rows = by_cat[cat][:8]
        print(f"\n=== {cat} ({sum(r['vol24h'] for r in by_cat[cat]):.0f} vol24h, {len(by_cat[cat])} mkts) ===")
        for r in rows:
            yp = f"{r['yes_price']:.3f}" if r["yes_price"] is not None else "  -  "
            apy = f"{r['apy_dominant']*100:>+5.1f}%" if r.get('apy_dominant') is not None else "   -  "
            hurdle = "✓" if r.get("clears_hurdle") else " "
            side = r.get('dominant_side') or "-"
            # gross_apy label (2026-07-18): this column is WIN-ASSUMED carry —
            # (1-M)/M annualized — NOT expected edge. Twice this week (Hormuz-
            # traffic 35% "APY", Hormuz-transit) it seduced until honest priors
            # showed negative expected edge. The ✓ means "gross carry clears
            # hurdle IF the fade always wins" — never an entry signal by itself.
            print(f"  yes={yp}  gross_apy_{side}={apy}{hurdle}  spd={r['spread']:.3f}  liq={r['liquidity']:>9.0f}  v24={r['vol24h']:>9.0f}  d={r['days_to_resolve']:>6.1f}  {r['question'][:80]}")
    print("\n# gross_apy = WIN-ASSUMED carry, not expected edge — price P(loss) with an honest prior before any entry (2026-07-02 guard lesson, applied to discovery 2026-07-18)")

    # Optional: run catalyst_check.py on top N candidates (post-philosophy update
    # 2026-05-08, mandatory for any bond-like fade actually being entered).
    if args.check_catalysts > 0:
        import subprocess
        import sys
        catalyst_script = Path(__file__).resolve().parent / "catalyst_check.py"
        candidates = short[: args.check_catalysts]
        print(f"\n=== catalyst_check.py on top {len(candidates)} candidate(s) ===")
        for i, r in enumerate(candidates, 1):
            q = r.get("question", "")
            end_date = r.get("end_date", "")
            if not q or not end_date:
                print(f"\n[{i}/{len(candidates)}] SKIP — missing question or end_date: {q[:60]}")
                continue
            resolve_iso = end_date[:10]  # YYYY-MM-DD prefix
            print(f"\n[{i}/{len(candidates)}] {q[:80]} (resolves {resolve_iso})")
            try:
                proc = subprocess.run(
                    [sys.executable, str(catalyst_script), q, resolve_iso, "--no-log"],
                    capture_output=True, text=True, timeout=180,
                )
                if proc.returncode != 0:
                    print(f"  ERROR rc={proc.returncode}: {proc.stderr[:200]}")
                    continue
                print(proc.stdout)
            except subprocess.TimeoutExpired:
                print("  TIMEOUT after 180s")


if __name__ == "__main__":
    main()
