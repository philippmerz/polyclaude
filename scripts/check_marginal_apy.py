#!/usr/bin/env python3
"""Scan held positions for marginal-APY-below-hurdle (close candidates).

Long-tail NOs as resolution approaches: when mark > 0.97 with 6+ months
remaining, the marginal APY drops below stablecoin yield. Lesson source:
2026-05-08 DEC-0001 (Jesus 2027 NO) closed at 2.5% marginal APY vs Aave
hurdle 3.4% — capital was better deployed elsewhere even at near-zero
P(YES) belief.

This script reads current PM positions via positions.py-style data-api
fetch and flags any whose marginal-yield-to-resolution APY falls below
the hurdle. Prints a structured advisory; does NOT close anything.

Used by:
- The 02:00/14:00 UTC daily_checkin.sh cron prompt (step 3 catalyst scan).
- Manual ad-hoc invocation when reviewing the book.

Usage:
    python scripts/check_marginal_apy.py
    python scripts/check_marginal_apy.py --hurdle-apy 0.034

Exit code: 0 (always — this is informational, never errors out trades).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import httpx

# Default hurdle ≈ current Aave USDC supply APY. Was 0.034 (May-08 snapshot);
# bumped to 0.05 in the 2026-07-02 audit — the stale hurdle plus win-assumed
# math (below) had made the daily "6/6 clear" green light vacuous.
HURDLE_APY_DEFAULT = 0.05

PRIORS_PATH = Path(__file__).resolve().parent.parent / "notes" / "portfolio_kelly_priors.json"


def _resolve_wallet_address() -> str:
    """Read the polymarket wallet address from the secret-paths config.

    Mirrors the pattern in scripts/clob_v2.py / scripts/positions.py.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import _paths as _secrets
    d = json.loads(_secrets.path("POLYCLAUDE_WALLET").read_text())
    return d["address"]


def _fetch_positions(addr: str) -> list[dict]:
    """Fetch current positions from Polymarket data-api.

    Matches scripts/positions.py: lowercase address, limit=100.
    """
    url = "https://data-api.polymarket.com/positions"
    r = httpx.get(url, params={"user": addr.lower(), "limit": "100"}, timeout=20)
    r.raise_for_status()
    return r.json() or []


def _days_to_resolution(end_iso: str | None) -> float | None:
    """Parse data-api endDate (variable formats: '2026-05-15' or
    '2026-05-15T00:00:00Z') and return days from now.
    """
    if not end_iso:
        return None
    try:
        # Handle both date-only ("2026-05-15") and full datetime forms
        normalized = end_iso.replace("Z", "+00:00")
        end = dt.datetime.fromisoformat(normalized)
        # If naive (date-only input), treat as UTC midnight
        if end.tzinfo is None:
            end = end.replace(tzinfo=dt.timezone.utc)
        now = dt.datetime.now(dt.timezone.utc)
        return (end - now).total_seconds() / 86400
    except Exception:
        return None


def _load_priors() -> dict[str, float]:
    """Load per-position P(win) priors from portfolio_kelly_priors.json.

    Returns {slug_key: p_no}. Keys in the priors file are market slugs.
    2026-07-02 audit fix: the old formula (1-M)/M x 365/days was WIN-ASSUMED
    (no P(loss) term) — any NO below ~0.983 cleared a 3.4% hurdle at 180d,
    so the daily "N/N clear" line carried no information. Expected-edge math
    (p/M - 1) is what the close-candidate decision actually needs.
    """
    try:
        raw = json.loads(PRIORS_PATH.read_text())
    except Exception:
        return {}
    out = {}
    for k, v in raw.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and "p_no" in v:
            out[k] = float(v["p_no"])
    return out


def _match_prior(slug: str, priors: dict[str, float]) -> float | None:
    """Exact slug match first, then containment either way (slug variants)."""
    if not slug:
        return None
    if slug in priors:
        return priors[slug]
    for k, p in priors.items():
        if k in slug or slug in k:
            return p
    return None


def main() -> int:
    p = argparse.ArgumentParser(description="Flag held positions whose marginal-APY-to-resolution falls below a hurdle.")
    p.add_argument("--hurdle-apy", type=float, default=HURDLE_APY_DEFAULT,
                   help=f"hurdle APY (default {HURDLE_APY_DEFAULT*100:.2f}%% — Aave Base USDC supply, 2026-05-08).")
    p.add_argument("--drawdown-alert-pct", type=float, default=15.0,
                   help="flag positions with mtm_loss_pct >= this value as DRAWDOWN_ALERT (default 15%%). "
                        "Lesson source: 2026-05-08 DEC-0018 -40%% in 30 min would have surfaced "
                        "automatically on the next cron tick had this existed.")
    p.add_argument("--json", action="store_true",
                   help="emit machine-readable JSON instead of the human table.")
    args = p.parse_args()

    try:
        addr = _resolve_wallet_address()
    except Exception as e:
        print(f"ERROR: cannot resolve wallet: {e}", file=sys.stderr)
        return 0  # informational; never block

    try:
        positions = _fetch_positions(addr)
    except Exception as e:
        print(f"ERROR: data-api fetch failed: {e}", file=sys.stderr)
        return 0

    priors = _load_priors()
    flagged: list[dict] = []
    holds: list[dict] = []
    drawdowns: list[dict] = []
    for pos in positions:
        size = float(pos.get("size", 0) or 0)
        if size <= 0:
            continue
        # Outcome: "Yes" or "No" (Polymarket convention)
        outcome = pos.get("outcome", "")
        # Mark: data-api returns `curPrice` (current execution-style mark)
        mark = float(pos.get("curPrice", 0) or 0)
        if mark <= 0 or mark >= 1:
            continue
        # Days to resolution
        days = _days_to_resolution(pos.get("endDate"))
        if days is None or days <= 0:
            continue

        question = pos.get("title", "(unknown)")
        slug = pos.get("slug", "")
        avg_price = float(pos.get("avgPrice", 0) or 0)
        cost = avg_price * size
        mtm = mark * size
        # Drawdown check: regardless of side, flag if MTM is materially
        # below cost. This catches today's DEC-0018-style 40% drawdown
        # automatically on every cron tick / manual run, not requiring
        # the operator to be in an active turn at the moment.
        # Lesson source: 2026-05-08 Russia-Ukraine NO crashed 0.768 -> 0.456
        # in ~30 min after Trump's 3-day-ceasefire announcement.
        drawdown_pct = (mtm - cost) / cost * 100 if cost > 0 else 0
        # De-indexed-market guard: when Polymarket de-indexes a market (e.g.,
        # post-rapid-mark-movement), data-api sometimes returns mark=0.001
        # (the minimum tick) even though the position is intact on-chain.
        # Without this guard, a de-indexed market would always fire DRAWDOWN
        # ALERT at -99.9%. Lesson source: 2026-05-09 07:52 UTC Russia-Ukraine
        # NO showed -99.9% drawdown via data-api while on-chain balance was
        # 25 NO shares intact.
        if mark <= 0.005 and drawdown_pct < -50:
            # Treat as de-indexed; suppress drawdown alert but flag for review
            drawdown_pct = None  # mark unreliable
        if drawdown_pct is not None and drawdown_pct <= -args.drawdown_alert_pct:
            drawdowns.append({
                "question": question,
                "slug": slug,
                "outcome": outcome,
                "mark": round(mark, 4),
                "avg_entry": round(avg_price, 4),
                "size": round(size, 4),
                "cost": round(cost, 4),
                "mtm": round(mtm, 4),
                "drawdown_pct": round(drawdown_pct, 2),
                "days_to_resolve": round(days, 2),
                "verdict": "DRAWDOWN_ALERT" if drawdown_pct <= -args.drawdown_alert_pct else "DRAWDOWN_WATCH",
            })

        # 2026-07-02 audit fix — EXPECTATION math, not win-assumed carry.
        # Gross carry (1-M)/M assumes the position always wins; the decision
        # number is expected edge: E[value per $ held] = p/M, so
        # expected_edge_apy = (p/M - 1) x 365/days, with p from the priors
        # file. p < M means holding is NEGATIVE-EV at your own belief —
        # flag regardless of hurdle. Gross carry is kept as a column only.
        if mark >= 0.5:
            gross_carry_apy = (1.0 - mark) / mark * 365 / days
        else:
            # Sub-0.5 marks (e.g. iran-peace at 0.65) are NOT bond-like;
            # the marginal-APY-hurdle frame doesn't apply. Skip from the
            # advisory — these are speculative directional bets, not carries.
            continue

        prior_p = _match_prior(slug, priors) if outcome == "No" else None
        expected_edge_apy = None
        if prior_p is not None:
            expected_edge_apy = (prior_p / mark - 1.0) * 365 / days

        record = {
            "question": question,
            "slug": slug,
            "outcome": outcome,
            "mark": round(mark, 4),
            "prior_p": round(prior_p, 4) if prior_p is not None else None,
            "size": round(size, 4),
            "cost": round(cost, 4),
            "mtm": round(mtm, 4),
            "days_to_resolve": round(days, 2),
            "gross_carry_apy_pct": round(gross_carry_apy * 100, 2),
            "expected_edge_apy_pct": round(expected_edge_apy * 100, 2) if expected_edge_apy is not None else None,
            "drawdown_pct": round(drawdown_pct, 2) if drawdown_pct is not None else None,
        }
        if expected_edge_apy is not None:
            if prior_p < mark:
                record["verdict"] = "NEGATIVE_EDGE"
                flagged.append(record)
            elif expected_edge_apy < args.hurdle_apy:
                record["verdict"] = "CLOSE_CANDIDATE"
                flagged.append(record)
            else:
                record["verdict"] = "HOLD"
                holds.append(record)
        else:
            # No prior available: gross carry is the only number we have.
            # Mark it clearly so a win-assumed figure can't masquerade as EV.
            record["verdict"] = "NO_PRIOR (gross-carry only)"
            if gross_carry_apy < args.hurdle_apy:
                flagged.append(record)
            else:
                holds.append(record)

    if args.json:
        print(json.dumps({"hurdle_apy_pct": round(args.hurdle_apy * 100, 2),
                          "drawdown_alert_pct": args.drawdown_alert_pct,
                          "drawdowns": drawdowns,
                          "flagged": flagged, "holds": holds}, indent=2))
        return 0

    if drawdowns:
        print(f"!!! DRAWDOWN ALERTS — positions down ≥{args.drawdown_alert_pct:.0f}% on cost !!!")
        for r in sorted(drawdowns, key=lambda x: x["drawdown_pct"]):
            print(f"  {r['outcome']} entry={r['avg_entry']:.3f} mark={r['mark']:.3f} | "
                  f"cost=${r['cost']:.2f} mtm=${r['mtm']:.2f} | "
                  f"{r['drawdown_pct']:+.1f}% | {r['days_to_resolve']:>5.1f}d | "
                  f"{r['question'][:60]}")
        print()

    def _apy_col(r: dict) -> str:
        if r.get("expected_edge_apy_pct") is not None:
            return f"E{r['expected_edge_apy_pct']:>+7.2f}% (p={r['prior_p']:.3f}, gross {r['gross_carry_apy_pct']:+.1f}%)"
        return f"gross {r['gross_carry_apy_pct']:>+7.2f}% (NO PRIOR)"

    print(f"# marginal-APY scan (EXPECTED-edge vs prior) @ {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}")
    print(f"# hurdle: {args.hurdle_apy*100:.2f}% APY; drawdown alert: {args.drawdown_alert_pct:.0f}%; priors: {PRIORS_PATH.name}")
    print(f"# {len(holds)} clear; {len(flagged)} flagged (NEGATIVE_EDGE / below-hurdle)")
    print()
    if flagged:
        print("=== FLAGGED (negative edge at own prior, or expected edge < hurdle) ===")
        for r in flagged:
            print(f"  [{r['verdict']}] {r['outcome']} {r['mark']:.3f} | {r['days_to_resolve']:>5.1f}d | "
                  f"{_apy_col(r)}  {r['question'][:60]}")
        print()
    print("=== HOLDS (expected edge clears hurdle) ===")
    for r in sorted(holds, key=lambda x: (x.get("expected_edge_apy_pct") if x.get("expected_edge_apy_pct") is not None else x["gross_carry_apy_pct"])):
        print(f"  {r['outcome']} {r['mark']:.3f} | {r['days_to_resolve']:>5.1f}d | "
              f"{_apy_col(r)}  {r['question'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
