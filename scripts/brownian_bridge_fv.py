#!/usr/bin/env python3
"""Hazard-decay fair-value tool for explicitly modelled Polymarket positions.

For an event-by-date market under a constant hazard rate, an immutable entry
prior can be rolled forward conditional on no event having happened. Given:
- p_entry: P(the held outcome wins) at entry
- t/T: fraction of horizon elapsed (0 at entry, 1 at resolution)

The formula depends on what the held outcome means:
- survival (the held outcome wins if no event occurs): p_entry^(1-t/T)
- occurrence (the held outcome wins if the event occurs):
  1 - (1-p_entry)^(1-t/T)

This model is deliberately opt-in. A prior must contain both ``bb_entry_p``
and ``bb_mode`` (``survival`` or ``occurrence``), and the entry time must be
tracked. The ordinary ``p_yes``/``p_no`` fields are mutable current posteriors;
rolling them forward from the original entry time double-counts elapsed time.
Missing model metadata therefore produces a clearly non-actionable row rather
than a guessed signal.

For each held position, this script:
1. Pulls current mark from data-api
2. Loads immutable, explicit hazard metadata from portfolio_kelly_priors.json
3. Computes time-elapsed fraction t/T from entry timestamp + horizon
4. Computes a side-aware conditional fair mark
5. Surfaces delta = mark - fair_mark_BB:
   - delta > +2pp → TRIM signal (mark overshot fair-value)
   - delta < -3pp → SCALE_UP signal (mark below fair-value, edge to capture)
   - else → HOLD

This complements Kelly's current-posterior check only for positions whose
constant-hazard assumption has been explicitly reviewed and recorded.

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
MIN_POSITION_SHARES = 0.5
BB_MODES = frozenset({"survival", "occurrence"})


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


def filter_operational_positions(positions: list[dict]) -> list[dict]:
    """Drop dust and economically settled rows from the operational book."""
    kept = []
    for pos in positions:
        try:
            size = float(pos.get("size", 0) or 0)
        except (TypeError, ValueError):
            continue
        if size > MIN_POSITION_SHARES and pos.get("redeemable") is not True:
            kept.append(pos)
    return kept


def fetch_positions(addr: str) -> list[dict]:
    with httpx.Client(timeout=15) as c:
        r = c.get(
            "https://data-api.polymarket.com/positions",
            params={"user": addr.lower(), "limit": 100,
                    "sizeThreshold": MIN_POSITION_SHARES},
        )
        r.raise_for_status()
        # Keep the local filter even though the API accepts sizeThreshold: an
        # upstream default/parameter regression must not reintroduce resolved
        # dust into the operational book or its headline count.
        return filter_operational_positions(r.json() or [])


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


def fair_mark_hazard(p_entry: float, t_frac: float, mode: str) -> float:
    """Roll an immutable entry prior forward under a constant hazard.

    ``survival`` means the held outcome pays when the event has *not* occurred
    by the deadline. ``occurrence`` means it pays when the event *does* occur.
    The mode is explicit because inferring it from a Yes/No label is unsafe.
    """
    try:
        p_entry = float(p_entry)
        t_frac = float(t_frac)
    except (TypeError, ValueError) as exc:
        raise ValueError("p_entry and t_frac must be numeric") from exc
    if not 0.0 <= p_entry <= 1.0:
        raise ValueError("p_entry must be in [0, 1]")
    if mode not in BB_MODES:
        raise ValueError(f"mode must be one of {sorted(BB_MODES)}")

    t_frac = max(0.0, min(1.0, t_frac))
    remaining = 1.0 - t_frac
    if remaining == 0.0:
        return 1.0 if mode == "survival" else 0.0
    if mode == "survival":
        return p_entry ** remaining
    return 1.0 - (1.0 - p_entry) ** remaining


def assess_brownian_signal(
    mark: float,
    prior: dict,
    t_frac: float | None,
    *,
    trim_threshold: float = 2.0,
    scale_threshold: float = 3.0,
) -> dict:
    """Return an actionable signal only for a complete, valid opt-in model."""
    missing = [key for key in ("bb_entry_p", "bb_mode") if key not in prior]
    if missing:
        return {
            "status": "NON_ACTIONABLE",
            "actionable": False,
            "verdict": "NO_BB_MODEL",
            "fair_bb": None,
            "delta_pp": None,
            "reason": "missing immutable " + ", ".join(missing),
        }
    if t_frac is None:
        return {
            "status": "NON_ACTIONABLE",
            "actionable": False,
            "verdict": "NO_ENTRY_TIMING",
            "fair_bb": None,
            "delta_pp": None,
            "reason": "no tracked entry time; refusing to infer elapsed fraction",
        }
    try:
        fair_bb = fair_mark_hazard(prior["bb_entry_p"], t_frac, prior["bb_mode"])
    except ValueError as exc:
        return {
            "status": "NON_ACTIONABLE",
            "actionable": False,
            "verdict": "INVALID_BB_MODEL",
            "fair_bb": None,
            "delta_pp": None,
            "reason": str(exc),
        }

    delta_pp = (float(mark) - fair_bb) * 100
    if delta_pp > trim_threshold:
        verdict = "TRIM"
    elif delta_pp < -scale_threshold:
        verdict = "SCALE_UP"
    else:
        verdict = "HOLD"
    return {
        "status": "MODELED",
        "actionable": verdict in {"TRIM", "SCALE_UP"},
        "verdict": verdict,
        "fair_bb": fair_bb,
        "delta_pp": delta_pp,
        "reason": None,
    }


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
    positions = fetch_positions(addr)

    now_ts = datetime.datetime.utcnow().timestamp()
    rows = []
    for pos in positions:
        slug = pos.get("slug", "")
        size = float(pos.get("size", 0) or 0)
        if size <= MIN_POSITION_SHARES:
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
            p_source = "missing"
        else:
            p_source = "priors"

        # Get horizon timing from decisions tracker
        entry_ts, horizon_days = find_entry_for_slug(slug, decisions)
        if entry_ts and horizon_days and horizon_days > 0:
            elapsed_days = (now_ts - entry_ts) / 86400
            t_frac = max(0.0, min(1.0, elapsed_days / horizon_days))
            t_source = "tracked"
        else:
            # An end date says when the market resolves, not when this position
            # and its immutable prior began. Treat missing entry timing as
            # non-actionable instead of pretending t/T=0.
            t_frac = None
            horizon_days = None
            t_source = "missing-entry"

        assessment = assess_brownian_signal(
            mark,
            prior,
            t_frac,
            trim_threshold=args.trim_threshold,
            scale_threshold=args.scale_threshold,
        )

        rows.append({
            "slug": slug[:50],
            "side": side,
            "size": round(size, 2),
            "cost": round(cost, 2),
            "mark": round(mark, 4),
            "p_my": p_my,
            "p_source": p_source,
            "bb_entry_p": prior.get("bb_entry_p"),
            "bb_mode": prior.get("bb_mode"),
            "t_frac": round(t_frac, 3) if t_frac is not None else None,
            "horizon_d": round(horizon_days, 1) if horizon_days is not None else None,
            "fair_bb": (round(assessment["fair_bb"], 4)
                        if assessment["fair_bb"] is not None else None),
            "delta_pp": (round(assessment["delta_pp"], 2)
                         if assessment["delta_pp"] is not None else None),
            "verdict": assessment["verdict"],
            "actionable": assessment["actionable"],
            "status": assessment["status"],
            "reason": assessment["reason"],
            "t_source": t_source,
        })

    # Sort by abs(delta_pp) desc to surface biggest discrepancies
    rows.sort(key=lambda r: -abs(r.get("delta_pp", 0) or 0))

    if args.json:
        print(json.dumps({"results": rows}, indent=2, default=str))
        return 0

    print(f"\n{'='*132}")
    print(f"HAZARD-DECAY FAIR-VALUE (opt-in) — {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M UTC')}")
    print("  survival: p_entry^(1-t/T)  |  occurrence: 1-(1-p_entry)^(1-t/T)")
    print("  Actions require immutable bb_entry_p + explicit bb_mode + tracked entry timing; current p_yes/p_no is never rolled forward.")
    print(f"{'='*132}")
    print(f"{'Slug':<45} {'Side':<4} {'mark':<6} {'curP':<6} {'entryP':<7} {'mode':<10} {'t/T':<5} {'fair':<7} {'Δpp':<7} {'verdict':<15}")
    print(f"{'-'*132}")
    for r in rows:
        if r.get("status") == "DE_INDEXED":
            print(f"{r['slug'][:45]:<45} {r['side']:<3} {r['mark']:<6.4f} (de-indexed)")
            continue
        current_p = "-" if r["p_my"] is None else f"{r['p_my']:.3f}"
        if r.get("status") != "MODELED":
            print(f"{r['slug'][:45]:<45} {r['side']:<4} {r['mark']:<6.4f} {current_p:<6} "
                  f"{'-':<7} {'-':<10} {'-':<5} {'-':<7} {'-':<7} "
                  f"{r['verdict']:<15} ({r['reason']})")
            continue
        print(f"{r['slug'][:45]:<45} {r['side']:<4} {r['mark']:<6.4f} {current_p:<6} "
              f"{r['bb_entry_p']:<7.3f} {r['bb_mode']:<10} {r['t_frac']:<5.2f} "
              f"{r['fair_bb']:<7.4f} {r['delta_pp']:>+5.2f}pp {r['verdict']:<15}")

    # Summary actions
    trim = [r for r in rows if r.get("actionable") and r.get("verdict") == "TRIM"]
    scale = [r for r in rows if r.get("actionable") and r.get("verdict") == "SCALE_UP"]
    unmodeled = [r for r in rows if r.get("status") == "NON_ACTIONABLE"]
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

    if unmodeled:
        print(f"\nNon-actionable/unmodeled ({len(unmodeled)}): add immutable bb_entry_p and "
              "bb_mode=survival|occurrence to a reviewed prior before this tool may signal.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
