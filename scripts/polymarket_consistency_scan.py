"""Polymarket cross-market consistency scanner.

Finds neg-risk event groups (mutually-exclusive multi-outcome events on
Polymarket) where the YES probabilities don't sum to ~1 — a structural
arb signal. Two directions:

  • sum(YES) < 1 → arb by buying ONE YES of every contender. One wins,
    pays $1; total cost was sum(YES) < 1; profit = 1 - sum(YES) - fees.

  • sum(YES) > 1 → arb by buying ONE NO of every contender. Exactly one
    contender wins, so N-1 NO tokens pay $1 each. Total payout = N-1.
    Total cost = sum(NO) = N - sum(YES). Profit = (N - 1) - (N - sum(YES))
    - fees = sum(YES) - 1 - fees.

Either direction profits when |1 - sum(YES)| > fee-eaten threshold.

CRITICAL: gamma-api outcomePrices midpoints are NOT executable. On thin
markets they sit between a $0.01 stub bid and a real ask, producing a
displayed mid (e.g. 0.46) that has no live counter-side. To get real
fillable edge we MUST fetch CLOB orderbook asks for every member. The
scanner runs in two passes:

  pass 1: gamma-api scan flags groups whose displayed yes_sum violates
          consistency (cheap, 1 API call paginated).
  pass 2: for each pass-1 hit, pull CLOB orderbook for every member's
          buy side (NO ask if sum>1, YES ask if sum<1) and recompute
          net edge from actual top-of-book asks. This is `live_*` in
          the output.

Telegram alerts and the `arb_free` flag now use live fills, not midpoints.

Output: logs/polymarket_consistency_<ts>.md + logs/polymarket_consistency_latest.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
OUT_DIR = _REPO_ROOT / "logs"

POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"
POLYMARKET_CLOB = "https://clob.polymarket.com"
POLYMARKET_FEE_RATE = 0.072  # edge-aware: fee = rate * min(p, 1-p) * notional

# How big the consistency violation must be (after-fee, after-slippage net)
# to surface in Telegram. Below this, the violation is logged but not alerted.
TELEGRAM_THRESHOLD_NET = 0.02  # 2% net edge after fees

# How many YES-sum deviation pp to log at all
LOG_THRESHOLD_GROSS = 0.005  # 0.5% gross deviation

# At what gross deviation to bother spending API calls fetching live orderbooks.
# Anything below this is dominated by fees + slippage even in the best case.
LIVE_QUOTE_THRESHOLD_GROSS = 0.05  # 5% gross deviation


def _telegram(text: str) -> None:
    try:
        subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            cwd=_REPO_ROOT, check=False, timeout=15, capture_output=True,
        )
    except Exception:
        pass


def fetch_universe(max_markets: int = 5000) -> list[dict]:
    """Paginate gamma-api active markets via offset."""
    out: list[dict] = []
    offset = 0
    while len(out) < max_markets:
        try:
            # gamma-api caps page size at 100 regardless of the limit param, so
            # request 100 — otherwise the short-batch break below trips on page 1
            # and we only ever scan 100 markets (cf. discover_markets.fetch_active,
            # same bug fixed there 2026-05-29). Verified 2026-06-06: limit=500
            # returns 100; offset pagination is clean.
            r = httpx.get(
                f"{POLYMARKET_GAMMA}/markets",
                params={"active": "true", "closed": "false",
                        "limit": "100", "offset": str(offset)},
                timeout=25,
            )
            r.raise_for_status()
            batch = r.json()
        except Exception as e:
            print(f"page offset={offset} failed: {e}", file=sys.stderr)
            break
        if not batch:
            break
        out.extend(batch)
        offset += len(batch)
        if len(batch) < 100:
            break
    return out


def _yes_price(m: dict) -> float | None:
    raw = m.get("outcomePrices") or "[]"
    try:
        prices = json.loads(raw) if isinstance(raw, str) else raw
        if not (isinstance(prices, list) and len(prices) >= 2):
            return None
        return float(prices[0])
    except Exception:
        return None


def _market_fee_buy(p: float) -> float:
    """Polymarket fee fraction on buying a token at price p."""
    return POLYMARKET_FEE_RATE * min(p, 1 - p)


def _orderbook(token_id: str) -> dict | None:
    """Fetch CLOB orderbook for a token. Returns {'bids':[(p,sz)...], 'asks':[(p,sz)...]} or None."""
    try:
        r = httpx.get(f"{POLYMARKET_CLOB}/book", params={"token_id": token_id}, timeout=10)
        r.raise_for_status()
        b = r.json()
        bids = sorted([(float(x["price"]), float(x["size"])) for x in b.get("bids", [])], key=lambda x: -x[0])
        asks = sorted([(float(x["price"]), float(x["size"])) for x in b.get("asks", [])], key=lambda x: x[0])
        return {"bids": bids, "asks": asks}
    except Exception:
        return None


def _walk_ask(asks: list[tuple[float, float]], target_shares: float) -> tuple[float, float] | None:
    """Walk asks (sorted ascending) consuming `target_shares`. Return (avg_fill_price, shares_filled)."""
    if not asks:
        return None
    remaining = target_shares
    spent = 0.0
    filled = 0.0
    for price, size in asks:
        take = min(remaining, size)
        spent += take * price
        filled += take
        remaining -= take
        if remaining <= 1e-9:
            break
    if filled <= 0:
        return None
    return spent / filled, filled


def live_quote_group(members: list[tuple[dict, float]], action: str, target_shares: float = 5.0) -> dict | None:
    """For each member, fetch CLOB orderbook for the side we'd buy and walk to target_shares.
    Returns realistic cost/payout summary; None if any member has no quote."""
    side_quotes = []
    for m, _yp in members:
        tokens_raw = m.get("clobTokenIds") or "[]"
        try:
            tokens = json.loads(tokens_raw) if isinstance(tokens_raw, str) else tokens_raw
        except Exception:
            return None
        if not isinstance(tokens, list) or len(tokens) < 2:
            return None
        # action == buy_all_no  → buy NO token (index 1)
        # action == buy_all_yes → buy YES token (index 0)
        token = tokens[1] if action.startswith("buy_all_no") else tokens[0]
        ob = _orderbook(token)
        if not ob or not ob["asks"]:
            return None
        walk = _walk_ask(ob["asks"], target_shares)
        if walk is None:
            return None
        avg_p, filled = walk
        side_quotes.append({"member": m.get("groupItemTitle") or m["question"][:40],
                            "avg_ask": avg_p, "filled": filled,
                            "best_ask": ob["asks"][0][0], "best_ask_sz": ob["asks"][0][1]})
    if not side_quotes:
        return None
    n = len(side_quotes)
    sum_avg_ask = sum(q["avg_ask"] for q in side_quotes)
    # Per unit: cost = sum(ask), payout if exactly one YES wins:
    #   buy_all_no  → n-1
    #   buy_all_yes → 1
    if action.startswith("buy_all_no"):
        gross_payout = n - 1
    else:
        gross_payout = 1.0
    fees = sum(q["avg_ask"] * _market_fee_buy(q["avg_ask"]) for q in side_quotes)
    net_profit_per_unit = gross_payout - sum_avg_ask - fees
    capital_per_unit = sum_avg_ask
    return {
        "live_capital_per_unit": capital_per_unit,
        "live_gross_payout": gross_payout,
        "live_fees": fees,
        "live_net_per_unit": net_profit_per_unit,
        "live_net_edge_frac": net_profit_per_unit / capital_per_unit if capital_per_unit > 0 else 0,
        "live_quotes": side_quotes,
    }


def group_by_event(markets: list[dict]) -> dict[str, list[dict]]:
    # Dedup members by conditionId (2026-08-01): the paginated market fetch can
    # return the SAME market twice (overlapping pages / re-fetch drift — the
    # duplicates carried slightly different liquidity snapshots). A duplicated
    # member double-counts its YES in the sum AND breaks the buy-all-NO payout
    # assumption (duplicates resolve YES together), which manufactured a phantom
    # "28.7% live-validated free arb" on Montana-Senate (2×R + 2×I + 1×D,
    # yes_sum 2.006) and daemon-fired a tick for it.
    groups: dict[str, list[dict]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for m in markets:
        events = m.get("events") or []
        if not events:
            continue
        eid = events[0].get("id")
        if not eid:
            continue
        key = (eid, str(m.get("conditionId") or m.get("id")))
        if key in seen:
            continue
        seen.add(key)
        groups[eid].append(m)
    return groups


def evaluate_group(eid: str, members: list[dict]) -> dict | None:
    """Compute the consistency-violation arb potential for a neg-risk event."""
    if len(members) < 2:
        return None
    # Filter to members that are negRisk + have prices
    valid = []
    for m in members:
        if not m.get("negRisk"):
            return None
        yp = _yes_price(m)
        if yp is None:
            continue
        valid.append((m, yp))
    if len(valid) < 2:
        return None

    yes_sum = sum(yp for _, yp in valid)
    n = len(valid)
    deviation = yes_sum - 1.0

    # Compute realistic net edge.
    #
    # Critical asymmetry: the two sides differ in robustness to "missing markets"
    # (cases where Polymarket lists 20 named candidates but the actual event has
    # more, with the residual unmodeled).
    #
    #   • sum(YES) > 1 (overpriced): buying all NOs is a TRUE free arb. Exactly
    #     one outcome wins; if it's a listed candidate, n-1 NOs pay $1 each
    #     (total $n-1); if it's a non-listed write-in, ALL n NOs pay $1 each
    #     (total $n) — even better. Cost is locked at sum(NO) = n - sum(YES).
    #
    #   • sum(YES) < 1 (underpriced): buying all YESes is NOT a free arb. The
    #     "missing mass" 1 - sum(YES) is the market's implied probability that
    #     none of the listed candidates wins. If that's a real probability
    #     (e.g., a Nobel write-in actually wins), ALL n YESes resolve to $0
    #     and you eat the full sum(YES) loss. Only safe if you have a Field
    #     market to capture the residual, OR you're directionally betting
    #     against the implied non-listed-candidate probability.
    #
    # We compute both directions but only mark the first as `arb_free`.
    if deviation > 0:
        no_prices = [(1 - p) for _, p in valid]
        total_fees = sum(np_ * _market_fee_buy(np_) for np_ in no_prices)
        capital = sum(no_prices)  # = n - yes_sum
        gross_profit = (n - 1) - capital
        net_profit = gross_profit - total_fees
        action = "buy_all_no"
        arb_free = True
    elif deviation < 0:
        total_fees = sum(yp * _market_fee_buy(yp) for _, yp in valid)
        gross_profit = 1.0 - yes_sum
        net_profit = gross_profit - total_fees
        action = "buy_all_yes (DIRECTIONAL — bets against missing-mass)"
        capital = yes_sum
        arb_free = False
    else:
        return None

    # Liquidity: sum of liquidityNum across members (rough; some are 0 for thin markets)
    liquidity = sum(float(m.get("liquidityNum") or 0) for m, _ in valid)

    # Resolution date: earliest endDate among members
    end_dates = [m.get("endDateIso") or m.get("endDate") for m, _ in valid]
    end_dates = [e for e in end_dates if e]
    earliest_end = min(end_dates) if end_dates else None
    days_to_resolution = None
    if earliest_end:
        try:
            d = dt.datetime.fromisoformat(earliest_end.replace("Z", "+00:00"))
            days_to_resolution = (d - dt.datetime.now(dt.timezone.utc)).days
        except Exception:
            pass

    title = (members[0].get("events") or [{}])[0].get("title", "?")
    return {
        "event_id": eid,
        "title": title,
        "members": n,
        "yes_sum": yes_sum,
        "deviation": deviation,
        "action": action,
        "arb_free": arb_free,
        "capital_required": capital,
        "gross_profit": gross_profit,
        "fees_estimate": total_fees,
        "net_profit": net_profit,
        "net_edge_frac": net_profit / capital if capital > 0 else 0,
        "liquidity": liquidity,
        "days_to_resolution": days_to_resolution,
        "top_contenders": sorted(
            [{"name": m.get("groupItemTitle") or m["question"][:60],
              "yes": yp,
              "liq": float(m.get("liquidityNum") or 0)}
             for m, yp in valid],
            key=lambda x: -x["yes"],
        )[:6],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max-markets", type=int, default=5000)
    p.add_argument("--notify", action="store_true")
    p.add_argument("--telegram-threshold-net", type=float, default=TELEGRAM_THRESHOLD_NET,
                   help="net-edge threshold (frac) above which to Telegram")
    args = p.parse_args()

    print(f"fetching Polymarket active universe (target {args.max_markets})...")
    markets = fetch_universe(args.max_markets)
    print(f"  pulled {len(markets)}")

    print("grouping by event...")
    groups = group_by_event(markets)
    print(f"  {len(groups)} distinct events")

    print("evaluating consistency (pass 1: gamma-api midpoints)...")
    candidates = []
    valid_members_by_eid: dict[str, list[tuple[dict, float]]] = {}
    for eid, members in groups.items():
        # Re-derive valid (m, yp) inside evaluate_group; cache it for live pass.
        valid_pairs = []
        if all(m.get("negRisk") for m in members):
            for m in members:
                yp = _yes_price(m)
                if yp is not None:
                    valid_pairs.append((m, yp))
        result = evaluate_group(eid, members)
        if result and abs(result["deviation"]) >= LOG_THRESHOLD_GROSS:
            candidates.append(result)
            valid_members_by_eid[eid] = valid_pairs

    # Sort by net edge (largest profit per dollar locked)
    candidates.sort(key=lambda c: -c["net_edge_frac"])
    print(f"  {len(candidates)} groups exceed {LOG_THRESHOLD_GROSS*100:.1f}% gross deviation (gamma midpoint)")

    # Pass 2: live CLOB orderbook recompute for high-deviation candidates only.
    live_candidates = [c for c in candidates if abs(c["deviation"]) >= LIVE_QUOTE_THRESHOLD_GROSS]
    print(f"\nlive-quote pass: fetching CLOB orderbooks for {len(live_candidates)} candidates above {LIVE_QUOTE_THRESHOLD_GROSS*100:.1f}% gross deviation")
    for i, c in enumerate(live_candidates):
        eid = c["event_id"]
        members = valid_members_by_eid.get(eid) or []
        if not members:
            c["live_skipped"] = "no valid members"
            continue
        live = live_quote_group(members, c["action"])
        if live is None:
            c["live_skipped"] = "no orderbook"
            continue
        c.update(live)
        if (i + 1) % 20 == 0:
            print(f"  ...{i+1}/{len(live_candidates)} done")
    print(f"  {sum(1 for c in live_candidates if 'live_net_edge_frac' in c)} got live quotes")

    # Output
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_md = OUT_DIR / f"polymarket_consistency_{ts}.md"
    out_json = OUT_DIR / "polymarket_consistency_latest.json"

    free_arb = [c for c in candidates if c["arb_free"]]
    directional = [c for c in candidates if not c["arb_free"]]
    # "Real" candidates have live orderbook data and still show positive net edge.
    real_free_arb = [c for c in free_arb if c.get("live_net_edge_frac", -1) > 0]
    real_free_arb.sort(key=lambda c: -c["live_net_edge_frac"])

    with out_md.open("w") as f:
        f.write(f"# Polymarket consistency scan — {ts} UTC\n\n")
        f.write(f"Universe: {len(markets)} active markets, {len(groups)} events, "
                f"{len(candidates)} midpoint-violations > {LOG_THRESHOLD_GROSS*100:.1f}%.\n\n")
        f.write(f"- **{len(real_free_arb)} REAL free-arb candidates (live CLOB asks pencil)**\n")
        f.write(f"- {len(free_arb)} sum>1 (midpoint), {len(directional)} sum<1 (midpoint, directional)\n\n")
        f.write("> WARNING: gamma-api `outcomePrices` shows midpoints between stale stub bids "
                "(often $0.01) and real asks. Most midpoint-only \"free arb\" signals evaporate "
                "when orderbook asks are checked. Only the **REAL** section below should be acted on.\n\n")

        f.write("## REAL free arb (live-quote validated)\n\n")
        f.write("Computed by walking CLOB asks for buy-all-NO of every member (target 5 shares each). "
                "Profit assumes exactly one YES wins.\n\n")
        if real_free_arb:
            f.write(f"| Live Edge | Mid Edge | YES-sum | Members | Capital | Liquidity | Title |\n")
            f.write(f"|---:|---:|---:|---:|---:|---:|---|\n")
            for c in real_free_arb[:30]:
                f.write(f"| {c['live_net_edge_frac']*100:+.2f}% | {c['net_edge_frac']*100:+.2f}% | "
                        f"{c['yes_sum']:.4f} | "
                        f"{c['members']} | ${c['live_capital_per_unit']:.2f}/unit | "
                        f"${c['liquidity']:,.0f} | "
                        f"{c['title'][:60]} |\n")
        else:
            f.write("None — every midpoint-flagged candidate evaporated under live CLOB asks.\n")

        f.write("\n## Midpoint-only sum>1 candidates (likely stale orderbooks)\n\n")
        f.write("Sorted by midpoint net edge. These are NOT executable; included for diagnostic only.\n\n")
        f.write(f"| Mid Edge | Live Edge | YES-sum | Members | Liquidity | Title |\n")
        f.write(f"|---:|---:|---:|---:|---:|---|\n")
        for c in free_arb[:30]:
            live_e = c.get("live_net_edge_frac")
            live_str = f"{live_e*100:+.2f}%" if live_e is not None else c.get("live_skipped", "—")
            f.write(f"| {c['net_edge_frac']*100:+.2f}% | {live_str} | {c['yes_sum']:.4f} | "
                    f"{c['members']} | "
                    f"${c['liquidity']:,.0f} | "
                    f"{c['title'][:60]} |\n")

        f.write("\n## Midpoint-only sum<1 candidates (directional, missing-mass risk)\n\n")
        f.write(f"| Mid Edge | YES-sum | Members | Liquidity | Title |\n")
        f.write(f"|---:|---:|---:|---:|---|\n")
        for c in directional[:15]:
            f.write(f"| {c['net_edge_frac']*100:+.2f}% | {c['yes_sum']:.4f} | "
                    f"{c['members']} | "
                    f"${c['liquidity']:,.0f} | "
                    f"{c['title'][:60]} |\n")

        if real_free_arb:
            f.write("\n## REAL free-arb breakdown\n\n")
            for c in real_free_arb[:8]:
                f.write(f"### {c['title']}\n")
                f.write(f"- members: {c['members']}, YES-sum (mid): {c['yes_sum']:.4f}\n")
                f.write(f"- live capital/unit: ${c['live_capital_per_unit']:.4f}, "
                        f"gross ${c['live_gross_payout']:.4f}, fees ${c['live_fees']:.4f}, "
                        f"**net ${c['live_net_per_unit']:.4f} ({c['live_net_edge_frac']*100:+.2f}%)**\n")
                f.write(f"- live quotes (per-member NO ask, walking 5 shares):\n")
                for q in c.get("live_quotes", []):
                    f.write(f"  - {q['member'][:55]}: avg_ask={q['avg_ask']:.4f} "
                            f"(best={q['best_ask']:.3f} sz={q['best_ask_sz']:.0f})\n")
                f.write("\n")

    payload = {"generated_at": ts, "candidates": candidates}
    out_json.write_text(json.dumps(payload, indent=2, default=str))

    print(f"\nwrote {out_md}")
    print(f"wrote {out_json}\n")

    # Stdout summary — REAL free-arb candidates (live-validated)
    print("\n=== REAL FREE ARB (live-quote validated) ===")
    if real_free_arb:
        print(f"{'live edge':>10}  {'mid edge':>9}  {'YES-sum':>8}  {'members':>7}  {'cap/unit':>9}  {'liq':>10}  title")
        for c in real_free_arb[:15]:
            print(f"{c['live_net_edge_frac']*100:>+9.2f}%  "
                  f"{c['net_edge_frac']*100:>+8.2f}%  {c['yes_sum']:>8.4f}  "
                  f"{c['members']:>7}  ${c['live_capital_per_unit']:>7.2f}  "
                  f"${c['liquidity']:>9,.0f}  {c['title'][:60]}")
    else:
        print("none — every midpoint-flagged candidate evaporated under live CLOB asks.")
    print(f"\n{len(free_arb)} midpoint sum>1 / {len(directional)} midpoint sum<1 / "
          f"{len(real_free_arb)} real after live-quote check")

    # Telegram only on REAL free-arb candidates above threshold.
    profitable_real = [c for c in real_free_arb if c["live_net_edge_frac"] > args.telegram_threshold_net]
    print(f"{len(profitable_real)} REAL free-arb candidates exceed {args.telegram_threshold_net*100:.1f}% net edge")

    if profitable_real and args.notify:
        lines = [f"polymarket free-arb: {len(profitable_real)} live-validated group(s) above {args.telegram_threshold_net*100:.1f}% net edge"]
        for c in profitable_real[:5]:
            lines.append(
                f"\n• live net +{c['live_net_edge_frac']*100:.2f}%  buy-all-NO\n"
                f"  YES-sum {c['yes_sum']:.4f} across {c['members']} members  "
                f"cap/unit ${c['live_capital_per_unit']:.2f}  net/unit ${c['live_net_per_unit']:.4f}\n"
                f"  {c['title'][:80]}"
            )
        lines.append(f"\nfull table: {out_md.name}")
        _telegram("\n".join(lines))

    return 0


if __name__ == "__main__":
    sys.exit(main())
