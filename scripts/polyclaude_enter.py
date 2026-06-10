#!/usr/bin/env python3
"""Unified entry helper — catalyst_check + Kelly sizing + execute.

Wraps the multi-step workflow used for every Polymarket entry into one command:
1. Fetch market via gamma-api → check umaResolutionStatus (skip if disputed/proposed)
2. Run catalyst_check.py to get P(YES) estimate (with multiplicative breakdown
   for conjunction questions per philosophy 00 update)
3. Compute Kelly+ρ optimal size via per-position math (default half-Kelly,
   ρ=0.6 if cluster specified, ρ=0 if independent)
4. Print decision: SIZE / DON'T_TAKE / NEED_REVIEW with reasoning
5. With --execute flag: post buy via clob_v2.py

Output is logged to notes/entries_log.md (gitignored — local-only).

Operator directive 2026-05-09: aggressive engineering to capture untapped alpha.
This compounds across every future entry decision.

Usage:
    # Discovery: dry-run with reasoning
    python scripts/polyclaude_enter.py "Will US confirm aliens by 2027?" 2026-12-31

    # Quick mode: skip catalyst_check (use --my-p directly)
    python scripts/polyclaude_enter.py --my-p 0.95 --side NO 0.874 \\
        --resolve-date 2026-05-15 --slug us-x-iran-permanent-peace-deal-by-may-15-2026 \\
        "US x Iran permanent peace deal by May 15"

    # Execute: --execute --usd <amount>
    python scripts/polyclaude_enter.py --my-p 0.95 --side NO 0.874 ... --execute
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "notes" / "entries_log.md"


def fetch_market_by_slug_or_question(slug_or_q: str) -> dict | None:
    """Try slug lookup first; if fails, search by question."""
    with httpx.Client(timeout=15) as c:
        # Slug lookup
        if "-" in slug_or_q or "_" in slug_or_q:
            r = c.get("https://gamma-api.polymarket.com/markets", params={"slug": slug_or_q})
            if r.status_code == 200:
                d = r.json()
                if isinstance(d, list) and d:
                    return d[0]
        # Question search via paginate (gamma-api ?q is broken; client-side filter).
        # gamma caps pages at 100 regardless of limit, so paginate by 100 with an
        # early exit — the old limit=500 + offset=page*500 stride skipped 80% of
        # markets, so a question-based lookup could silently miss the target market.
        offset = 0
        while offset < 6000:
            r = c.get("https://gamma-api.polymarket.com/markets", params={
                "closed": "false", "active": "true",
                "limit": 100, "offset": offset,
                "order": "volume24hr", "ascending": "false",
            })
            if r.status_code != 200:
                break
            batch = r.json() or []
            if not batch:
                break
            for m in batch:
                q = m.get("question", "")
                if slug_or_q.lower() == q.lower() or slug_or_q.lower() in q.lower():
                    return m
            offset += len(batch)
    return None


def _existing_exposure(condition_id: str | None, question: str) -> dict | None:
    """Live data-api check: do we already hold this market? (DEC-0029 lesson:
    2026-06-01 bought a market already held, found out after.) Returns the
    matching position dict or None; never raises (warn-path only)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from polyclaude_client import Wallet
        addr = Wallet.load().address
        r = httpx.get("https://data-api.polymarket.com/positions",
                      params={"user": addr.lower(), "limit": "100"}, timeout=15)
        r.raise_for_status()
        for pos in r.json():
            if condition_id and pos.get("conditionId") == condition_id:
                return pos
            if pos.get("title") and pos["title"].strip().lower() == question.strip().lower():
                return pos
    except Exception as e:
        print(f"# existing-exposure check unavailable ({e}) — verify manually", file=sys.stderr)
    return None


def _best_ask(token_id: str, timeout: float = 12.0) -> float | None:
    """Lowest ask for a CLOB token = the price we'd actually PAY to buy it.
    Hits the CLOB book API directly (gamma midpoints are unreliable — they sit
    between stub bids and real asks). Returns None if the book is empty/unreachable
    so the caller can fall back to the gamma mark."""
    import httpx
    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.get("https://clob.polymarket.com/book", params={"token_id": str(token_id)})
            r.raise_for_status()
            asks = r.json().get("asks") or []
            prices = [float(a["price"]) for a in asks if a.get("price")]
            return min(prices) if prices else None
    except Exception:
        return None


def kelly_size(mark: float, p_win: float, bankroll: float, frac: float,
               rho: float, cluster_frac: float) -> tuple[float, dict]:
    """Compute Kelly-optimal $ size with details."""
    if mark >= 0.999 or p_win <= mark:
        return 0.0, {"full_kelly": 0.0, "reason": "no edge (p_win <= mark)"}
    full_k = (p_win - mark) / (1.0 - mark)
    rho_disc = max(0.0, 1.0 - rho * cluster_frac)
    kelly_dollar = full_k * rho_disc * frac * bankroll
    return kelly_dollar, {
        "full_kelly": full_k,
        "rho_disc": rho_disc,
        "frac": frac,
        "bankroll": bankroll,
        "kelly_dollar": kelly_dollar,
        "edge_pp": (p_win - mark) * 100,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("question", nargs="?", default=None,
                   help="Polymarket question or slug (or omit if --slug provided)")
    p.add_argument("--slug", default=None, help="Explicit slug (alternative to question lookup)")
    p.add_argument("--my-p", type=float, default=None,
                   help="My P(side wins) estimate. If omitted, will run catalyst_check.")
    p.add_argument("--side", choices=["YES", "NO"], default="NO",
                   help="Which side to buy (default NO for bond-like fades)")
    p.add_argument("--resolve-date", default=None,
                   help="Resolution date (YYYY-MM-DD). Required for catalyst_check.")
    p.add_argument("--bankroll", type=float, default=170.0)
    p.add_argument("--kelly-frac", type=float, default=0.5)
    p.add_argument("--rho", type=float, default=0.0,
                   help="Correlation to existing cluster (0=independent, 0.7=high)")
    p.add_argument("--cluster-frac", type=float, default=0.0,
                   help="Existing cluster fraction of bankroll (for ρ-discount)")
    p.add_argument("--execute", action="store_true", help="Actually post buy order")
    p.add_argument("--usd", type=float, default=None,
                   help="Override Kelly recommendation with manual $ size")
    p.add_argument("--skip-catalyst-check", action="store_true",
                   help="Skip catalyst_check (use only --my-p)")
    p.add_argument("--edge-haircut", type=float, default=0.05,
                   help="Pessimistic shift applied to p for the robust-edge gate "
                        "(default 0.05). Larger = demand fatter edge for fuzzier estimates; "
                        "smaller only for genuinely high-confidence mechanical-market estimates.")
    args = p.parse_args()

    # Resolve market
    lookup = args.slug or args.question
    if not lookup:
        print("ERROR: provide question or --slug", file=sys.stderr)
        return 2

    print(f"# polyclaude_enter: looking up '{lookup[:50]}'...", file=sys.stderr)
    m = fetch_market_by_slug_or_question(lookup)
    if not m:
        print(f"ERROR: market not found", file=sys.stderr)
        return 2

    question = m.get("question", "?")
    slug = m.get("slug", "?")
    market_id = m.get("id", "?")
    uma_status = m.get("umaResolutionStatus")
    end_iso = m.get("endDate") or m.get("endDateIso") or ""
    try:
        prices_raw = m.get("outcomePrices")
        prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
        yes_p, no_p = float(prices[0]), float(prices[1])
    except Exception:
        yes_p, no_p = None, None
    clob_token_ids = m.get("clobTokenIds")
    if isinstance(clob_token_ids, str):
        try:
            clob_token_ids = json.loads(clob_token_ids)
        except Exception:
            clob_token_ids = None
    yes_token = clob_token_ids[0] if clob_token_ids else None
    no_token = clob_token_ids[1] if clob_token_ids else None
    neg_risk = bool(m.get("negRisk"))
    try:
        tick = float(m.get("orderPriceMinTickSize") or 0.01)
    except Exception:
        tick = 0.01
    if tick <= 0:
        tick = 0.01

    print(f"\nMarket: {question}")
    print(f"  slug: {slug}")
    print(f"  market_id: {market_id}")
    print(f"  umaResolutionStatus: {uma_status}")
    print(f"  outcomePrices: YES={yes_p} NO={no_p}")
    print(f"  endDate: {end_iso}")
    print(f"  negRisk: {neg_risk}")

    # Reject if disputed
    if uma_status in ("proposed", "disputed"):
        print(f"\nDECISION: SKIP — umaResolutionStatus={uma_status}")
        print(f"  Market is in active UMA dispute. Cannot reliably enter.")
        return 0

    # Existing-exposure guard (warn, not block — deliberate adds are fine, the
    # failure mode is UNKNOWING adds). Sums what a fill would take the ticket to.
    held = _existing_exposure(m.get("conditionId"), question)
    if held:
        held_cost = held.get("initialValue", 0.0)
        held_side = held.get("outcome", "?")
        print(f"\n!! EXISTING POSITION in this market: {held_side} "
              f"cost ${held_cost:.2f} (mark {held.get('curPrice', '?')}, "
              f"mtm ${held.get('currentValue', 0.0):.2f})")
        if args.usd:
            combined = held_cost + args.usd
            print(f"!! combined ticket after this buy: ${combined:.2f} "
                  f"= {combined / args.bankroll * 100:.1f}% of bankroll "
                  f"(15% hard cap = ${args.bankroll * 0.15:.2f}, 00_philosophy §5 model-error guardrails)")
        print(f"!! this is an ADD — confirm cluster caps + run the sizing as a "
              f"size_change decision, not a fresh entry.")

    if yes_p is None:
        print(f"\nDECISION: NEED_REVIEW — could not parse outcomePrices")
        return 2

    side = args.side
    gamma_mark = no_p if side == "NO" else yes_p
    token = no_token if side == "NO" else yes_token
    if gamma_mark is None or token is None:
        print(f"DECISION: NEED_REVIEW — no token id for {side}")
        return 2

    # Walk the LIVE CLOB ask — do NOT trust the gamma midpoint for the gate.
    # Per the polymarket-midpoints-unreliable lesson, gamma outcomePrices sit
    # between stub bids and real asks; the robust-edge gate must evaluate EV at
    # the price we'd actually PAY (the ask), or it passes phantom edge that
    # evaporates on fill. This matters more now that the discovery funnel
    # (10x fix, 2026-05-29) surfaces thin-liquidity tail markets where the
    # mid↔ask gap is large. Falls back to the gamma mark if the book is empty.
    real_ask = _best_ask(token)
    if real_ask is not None:
        mark = real_ask
        if abs(real_ask - gamma_mark) >= 0.01:
            print(f"  [mark] gamma-mid {gamma_mark:.4f} → live ask {real_ask:.4f} "
                  f"({(real_ask-gamma_mark)*100:+.1f}pp) — using live ask for the gate")
    else:
        mark = gamma_mark
        print(f"  [mark] live ask unavailable; falling back to gamma mid {gamma_mark:.4f}")

    # Resolve P(side wins)
    my_p = args.my_p
    if my_p is None and not args.skip_catalyst_check:
        if not args.resolve_date:
            print(f"\nDECISION: NEED_REVIEW — provide --my-p or --resolve-date for catalyst_check")
            return 2
        print(f"\n# Running catalyst_check.py for P estimate...", file=sys.stderr)
        try:
            r = subprocess.run(
                [".venv/bin/python", "scripts/catalyst_check.py", question, args.resolve_date,
                 "--no-log"],
                cwd=REPO_ROOT, capture_output=True, text=True, timeout=600,
            )
            cc_out = r.stdout
            print(cc_out)
            # Extract central P(YES) from "Central: X%" line
            m_central = re.search(r"Central:\s*(\d+(?:\.\d+)?)%", cc_out)
            if m_central:
                p_yes = float(m_central.group(1)) / 100
                my_p = (1 - p_yes) if side == "NO" else p_yes
                print(f"\n# catalyst_check central P(YES)={p_yes:.4f} → P({side} win)={my_p:.4f}", file=sys.stderr)
            else:
                print(f"\nDECISION: NEED_REVIEW — couldn't parse central P from catalyst_check")
                return 2
        except subprocess.TimeoutExpired:
            print(f"DECISION: NEED_REVIEW — catalyst_check timed out")
            return 3

    if my_p is None:
        print(f"DECISION: NEED_REVIEW — no P estimate provided")
        return 2

    # Kelly sizing
    kelly_dollar, details = kelly_size(mark, my_p, args.bankroll, args.kelly_frac,
                                        args.rho, args.cluster_frac)

    deploy_dollar = args.usd if args.usd is not None else kelly_dollar
    if deploy_dollar < 1.0:
        print(f"\nDECISION: SKIP — Kelly size ${deploy_dollar:.2f} < $1 (no edge or marginal)")
        return 0

    shares = deploy_dollar / mark
    profit_if_win = shares * (1.0 - mark)

    # Robust-edge gate (2026-05-29: replaces the retired flat 10pp edge bar).
    # The edge bar was relaxed to "positive EV after op-cost" — but EV computed
    # on the CENTRAL p estimate is fragile: my p is itself uncertain, and Kelly
    # punishes overbetting a believed-but-wrong edge. So gate on the PESSIMISTIC
    # bound of the estimate, not the point estimate. This self-scales: a
    # confident mechanical-market estimate (small --edge-haircut) clears thin
    # edges; a fuzzy estimate (large haircut) demands a fat edge. Reproduces a
    # margin-of-safety proportional to estimation uncertainty rather than a flat
    # phantom floor. op_cost ≈ haiku catalyst_check (~$0.02) + gas + slippage.
    OP_COST = 0.05
    p_robust = my_p - args.edge_haircut
    ev_robust = shares * (p_robust - mark)  # EV of position at pessimistic p
    ev_central = shares * (my_p - mark)
    if p_robust <= mark or ev_robust <= OP_COST:
        print(f"\nDECISION: SKIP — edge not robust to estimation error.")
        print(f"  central p={my_p:.4f} → EV ${ev_central:+.2f}; "
              f"pessimistic p={p_robust:.4f} (haircut {args.edge_haircut:.2f}) → EV ${ev_robust:+.2f}")
        print(f"  Need EV > ${OP_COST:.2f} at the pessimistic bound. "
              f"Thin point-estimate edge dominated by estimation noise.")
        print(f"  Override with a smaller --edge-haircut only if the p estimate is "
              f"genuinely high-confidence (mechanical resolution, tight catalyst_check band).")
        return 0

    print(f"\n=== KELLY ANALYSIS ===")
    print(f"  Buying {side} @ ${mark:.4f}, P({side} wins) = {my_p:.4f}")
    print(f"  Edge: {details['edge_pp']:+.2f}pp")
    print(f"  Full Kelly: {details['full_kelly']*100:.1f}% of bankroll")
    print(f"  ρ-discount: {details['rho_disc']:.4f} (ρ={args.rho}, cluster_frac={args.cluster_frac})")
    print(f"  × Kelly fraction: {args.kelly_frac}")
    print(f"  Kelly $: ${kelly_dollar:.2f}")
    if args.usd is not None:
        print(f"  Manual override: ${args.usd:.2f}")
    print(f"  → Deploy: ${deploy_dollar:.2f} ({shares:.2f} shares)")
    print(f"  Profit if win: +${profit_if_win:.2f} (= {profit_if_win/deploy_dollar*100:.1f}%)")

    # Sensitivity: ±5% misestimate of p
    print(f"\n  Sensitivity (full-Kelly under p ±0.05):")
    for delta_p in (-0.10, -0.05, +0.05):
        p_alt = max(0.001, min(0.999, my_p + delta_p))
        if p_alt > mark:
            full_alt = (p_alt - mark) / (1.0 - mark)
            size_alt = full_alt * details['rho_disc'] * args.kelly_frac * args.bankroll
            print(f"    p={p_alt:.4f} ({delta_p:+.2f}): full_K={full_alt*100:.1f}% → ${size_alt:.2f}")
        else:
            print(f"    p={p_alt:.4f} ({delta_p:+.2f}): NO EDGE → $0")

    if not args.execute:
        print(f"\nDECISION: WOULD_BUY ${deploy_dollar:.2f} of {side} @ {mark:.4f}")
        print(f"  Re-run with --execute to actually post the order.")
        return 0

    # EXECUTE path
    # Round the limit price UP to the market's tick grid (to lift the ask). The
    # raw gamma midpoint is often off-grid (e.g. 0.935 on a 0.01-tick market) and
    # gets rejected with "breaks minimum tick size rule". Lesson: 2026-05-31
    # Satoshi entry bounced on the 0.935 midpoint. Buying → round UP so the limit
    # is marketable against the resting ask.
    import math
    tick_dec = max(0, -int(round(math.log10(tick))))  # 0.01 → 2 decimals
    buy_price = round(math.ceil(round(mark / tick, 6)) * tick, tick_dec)
    buy_price = min(buy_price, 0.99)  # never post above 0.99
    # Integer shares × on-grid price → clean maker (2-dec) / taker (int) amounts,
    # satisfying the CLOB's amount-precision rule.
    target_shares = max(1, round(deploy_dollar / buy_price))
    clean_usd = round(target_shares * buy_price, tick_dec)
    print(f"\n# Executing BUY {target_shares} shares ({side}) @ {buy_price} (tick {tick}) for ${clean_usd}")

    cmd = [".venv/bin/python", "scripts/clob_v2.py",
           "buy" if side in ("YES", "NO") else "sell",
           token, str(buy_price), str(clean_usd), "--order-type", "FAK"]
    if neg_risk:
        cmd.extend(["--neg-risk", "true"])
    print(f"  cmd: {' '.join(cmd)}", file=sys.stderr)
    r = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    print(r.stdout)
    if r.returncode != 0:
        print(f"  stderr: {r.stderr[:500]}", file=sys.stderr)
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
