#!/usr/bin/env python3
"""Brownian-bridge fair-value tool for bond-like Polymarket positions.

For "X by date Y" markets where one side wins iff no event happens by date Y,
the mark dynamics under no-info-flow follow a hazard-rate model. Given:
- p_initial: my static P(NO wins by full horizon T)
- t/T: fraction of horizon elapsed (0 at entry, 1 at resolution)

Fair-mark at time t under constant hazard rate λ where exp(-λT) = p_initial:
    fair_mark(t) = exp(-λ(T-t)) = p_initial^((T-t)/T) = p_initial^(1-t/T)

Properties:
- fair_mark(t=0) = p_initial (mark equals my P estimate at entry)
- fair_mark(t=1) = 1.0 (mark drifts to certainty at resolution if no event)
- monotonically increasing as t→1

For each held position, this script:
1. Pulls current mark from data-api
2. Loads my static P from notes/portfolio_kelly_priors.json
3. Computes time-elapsed fraction t/T from entry timestamp + horizon
4. Computes fair_mark_BB = p^(1-t/T)
5. Surfaces delta = mark - fair_mark_BB:
   - delta > +2pp → TRIM signal (mark overshot fair-value)
   - delta < -3pp → SCALE_UP signal (mark below fair-value, edge to capture)
   - else → HOLD

This complements Kelly's static p-vs-mark check by adding TIME-DECAY DRIFT.
A position can be at static-Kelly-optimal but below Brownian-bridge fair-value
if the mark hasn't caught up to its expected drift toward 1.0.

Operator directive 2026-05-09: apply pricing theory rigorously. This is
the cleanest first-principles pricing model for bond-like fade markets.

Usage:
    python scripts/brownian_bridge_fv.py
    python scripts/brownian_bridge_fv.py --json
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
PRIORS_PATH = REPO_ROOT / "notes" / "portfolio_kelly_priors.json"
DECISIONS_PATH = REPO_ROOT / "notes" / "decisions.json"


def load_priors() -> dict:
    if not PRIORS_PATH.exists():
        return {}
    return json.loads(PRIORS_PATH.read_text())


def load_decisions() -> list[dict]:
    if not DECISIONS_PATH.exists():
        return []
    try:
        return json.load(open(DECISIONS_PATH)).get("decisions", [])
    except Exception:
        return []


def find_entry_for_slug(slug: str, decisions: list[dict]) -> tuple[float | None, float | None]:
    """Find earliest open_position decision for slug; return (entry_ts, full_horizon_days).

    Match heuristics:
    - slug substring in thesis (lowercase) — works when journal mentions the slug
    - slug words individually appear in thesis — fallback fuzzy
    - tag overlap: e.g., 'iran-peace' tag matches multiple may-X markets
    """
    slug_words = set(slug.lower().split("-"))
    slug_words -= {"the", "a", "an", "of", "by", "in", "to", "for", "us", "x", "and"}
    for d in decisions:
        if d.get("type") != "open_position":
            continue
        thesis = d.get("thesis", "").lower()
        # Direct slug-substring match
        if slug.replace("-", " ") in thesis or slug in thesis:
            ts_str = d.get("timestamp", "")
            res_str = d.get("resolution_at", "")
            try:
                ts_dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                res_dt = datetime.datetime.fromisoformat(res_str + "T23:59:59+00:00")
                horizon_days = (res_dt - ts_dt).total_seconds() / 86400
                return ts_dt.timestamp(), horizon_days
            except Exception:
                continue
        # Word-overlap fallback: if 4+ slug words appear in thesis
        thesis_words = set(thesis.split())
        if len(slug_words & thesis_words) >= 3:
            ts_str = d.get("timestamp", "")
            res_str = d.get("resolution_at", "")
            try:
                ts_dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                res_dt = datetime.datetime.fromisoformat(res_str + "T23:59:59+00:00")
                horizon_days = (res_dt - ts_dt).total_seconds() / 86400
                return ts_dt.timestamp(), horizon_days
            except Exception:
                continue
    return None, None


def fair_mark_brownian_bridge(p_initial: float, t_frac: float) -> float:
    """fair_mark = p^(1 - t/T) where t_frac = t/T in [0,1]."""
    if t_frac <= 0:
        return p_initial
    if t_frac >= 1:
        return 1.0
    return p_initial ** (1.0 - t_frac)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--wallet", default=str(_secrets.path("POLYCLAUDE_WALLET")))
    p.add_argument("--json", action="store_true")
    p.add_argument("--trim-threshold", type=float, default=2.0,
                   help="Flag TRIM if mark > fair_BB by this pp (default 2pp).")
    p.add_argument("--scale-threshold", type=float, default=3.0,
                   help="Flag SCALE_UP if mark < fair_BB by this pp (default 3pp).")
    args = p.parse_args()

    priors = load_priors()
    decisions = load_decisions()

    addr = json.load(open(args.wallet))["address"]
    with httpx.Client(timeout=15) as c:
        r = c.get("https://data-api.polymarket.com/positions",
                  params={"user": addr.lower(), "limit": 100, "sizeThreshold": 0.0})
        positions = r.json() or []

    now_ts = datetime.datetime.utcnow().timestamp()
    rows = []
    for pos in positions:
        slug = pos.get("slug", "")
        size = float(pos.get("size", 0) or 0)
        if size <= 0:
            continue
        mark = float(pos.get("curPrice", 0) or 0)
        side = pos.get("outcome", "?")
        avg = float(pos.get("avgPrice", 0) or 0)
        cost = avg * size

        # Skip de-indexed
        if mark <= 0.005:
            rows.append({"slug": slug, "side": side, "status": "DE_INDEXED", "size": size,
                         "mark": mark, "cost": cost})
            continue

        # Get my P from priors (exact match first; prefix fallback for
        # data-api slugs with random numeric suffixes — same bug pattern
        # fixed in portfolio_kelly 2026-05-19 commit 98a5e43).
        prior = priors.get(slug, {})
        if not prior:
            for k, v in priors.items():
                if slug.startswith(k):
                    prior = v
                    break
        p_my = prior.get("p_no" if side == "No" else "p_yes")
        if p_my is None:
            # Fallback: use mark + 0.05 as rough P
            p_my = min(0.99, mark + 0.05)
            p_source = "fallback"
        else:
            p_source = "priors"

        # Get horizon timing from decisions tracker
        entry_ts, horizon_days = find_entry_for_slug(slug, decisions)
        if entry_ts and horizon_days and horizon_days > 0:
            elapsed_days = (now_ts - entry_ts) / 86400
            t_frac = max(0.0, min(1.0, elapsed_days / horizon_days))
            t_source = "tracked"
        else:
            # Fallback: use end_date from data-api position if available
            try:
                end_iso = pos.get("endDate", "") or pos.get("endDateIso", "")
                end_dt = datetime.datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)
                days_remaining = (end_dt.timestamp() - now_ts) / 86400
                # Without entry-time, assume horizon == days_remaining (conservative)
                t_frac = 0.0
                horizon_days = days_remaining
                t_source = "fallback-no-entry"
            except Exception:
                rows.append({"slug": slug, "side": side, "status": "NO_TIMING_DATA"})
                continue

        # Brownian-bridge fair value
        fair_bb = fair_mark_brownian_bridge(p_my, t_frac)
        delta_pp = (mark - fair_bb) * 100

        # Verdict
        if delta_pp > args.trim_threshold:
            verdict = "TRIM"
        elif delta_pp < -args.scale_threshold:
            verdict = "SCALE_UP"
        else:
            verdict = "HOLD"

        rows.append({
            "slug": slug[:50],
            "side": side,
            "size": round(size, 2),
            "cost": round(cost, 2),
            "mark": round(mark, 4),
            "p_my": p_my,
            "p_source": p_source,
            "t_frac": round(t_frac, 3),
            "horizon_d": round(horizon_days, 1),
            "fair_bb": round(fair_bb, 4),
            "delta_pp": round(delta_pp, 2),
            "verdict": verdict,
            "t_source": t_source,
        })

    # Sort by abs(delta_pp) desc to surface biggest discrepancies
    rows.sort(key=lambda r: -abs(r.get("delta_pp", 0) or 0))

    if args.json:
        print(json.dumps({"results": rows}, indent=2, default=str))
        return 0

    print(f"\n{'='*110}")
    print(f"BROWNIAN-BRIDGE FAIR-VALUE — {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M UTC')}")
    print(f"  fair_bb(t) = p^(1 - t/T)  |  TRIM if mark > fair+{args.trim_threshold}pp  |  SCALE_UP if mark < fair-{args.scale_threshold}pp")
    print(f"{'='*110}")
    print(f"{'Slug':<45} {'Side':<3} {'mark':<6} {'p':<5} {'t/T':<5} {'fair_BB':<7} {'Δpp':<7} {'verdict':<10}")
    print(f"{'-'*110}")
    for r in rows:
        if r.get("status") == "DE_INDEXED":
            print(f"{r['slug'][:45]:<45} {r['side']:<3} {r['mark']:<6.4f} (de-indexed)")
            continue
        if r.get("status") == "NO_TIMING_DATA":
            print(f"{r['slug'][:45]:<45} {r['side']:<3} (no timing data)")
            continue
        print(f"{r['slug'][:45]:<45} {r['side']:<3} {r['mark']:<6.4f} {r['p_my']:<5.3f} "
              f"{r['t_frac']:<5.2f} {r['fair_bb']:<7.4f} {r['delta_pp']:>+5.2f}pp {r['verdict']:<10}")

    # Summary actions
    trim = [r for r in rows if r.get("verdict") == "TRIM"]
    scale = [r for r in rows if r.get("verdict") == "SCALE_UP"]
    print()
    if trim:
        print(f"TRIM candidates ({len(trim)}):")
        for r in trim:
            print(f"  - {r['slug'][:55]:<55} {r['side']:<3} mark={r['mark']:.4f} fair={r['fair_bb']:.4f} (Δ {r['delta_pp']:+.1f}pp)")
    else:
        print("(no TRIM candidates)")

    if scale:
        print(f"\nSCALE_UP candidates ({len(scale)}):")
        for r in scale:
            print(f"  - {r['slug'][:55]:<55} {r['side']:<3} mark={r['mark']:.4f} fair={r['fair_bb']:.4f} (Δ {r['delta_pp']:+.1f}pp)")
    else:
        print("(no SCALE_UP candidates)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
