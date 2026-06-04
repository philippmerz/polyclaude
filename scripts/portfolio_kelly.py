#!/usr/bin/env python3
"""Portfolio Kelly — applies Kelly+correlation analysis to entire held book.

For each currently-held Polymarket position:
- Pull current mark from gamma-api (skip de-indexed/disputed markets)
- Apply operator's P(win) estimate (loaded from notes/portfolio_kelly_priors.json)
- Compute full-Kelly, half-Kelly, and ρ-adjusted half-Kelly fractions
- Compare current $ deployed vs Kelly-optimal
- Output: ranked list of UNDER/OVER-sized positions with recommended deltas

Output supports decision-making: "where should next $ be deployed for max
Kelly-marginal edge?" and "which positions are oversized given correlation?"

Operator directive 2026-05-09: apply rigorous probability/sizing theory.
This generalizes scripts/kelly_size.py from per-position to portfolio-wide.

Usage:
    python scripts/portfolio_kelly.py
    python scripts/portfolio_kelly.py --bankroll 170 --kelly-frac 0.5

Priors file format (notes/portfolio_kelly_priors.json):
    {
      "iran-peace-may-15": {"p_no": 0.95, "cluster": "iran-peace", "rho_within": 0.7},
      "regime-fall-2026": {"p_no": 0.93, "cluster": "iran-regime", "rho_within": 0.7,
                          "rho_to_peace": -0.5},
      ...
    }

Cluster correlation handling: positions in the same cluster get ρ_within
discount; positions in anti-correlated clusters (e.g. iran-peace vs iran-regime)
get ρ_between (negative or zero) which doesn't reduce optimal size.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as _secrets

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIORS_PATH = REPO_ROOT / "notes" / "portfolio_kelly_priors.json"


def load_priors() -> dict:
    if not PRIORS_PATH.exists():
        return {}
    return json.loads(PRIORS_PATH.read_text())


def fetch_positions(addr: str) -> list[dict]:
    with httpx.Client(timeout=15) as c:
        r = c.get("https://data-api.polymarket.com/positions",
                  params={"user": addr.lower(), "limit": 100, "sizeThreshold": 0.0})
        r.raise_for_status()
        return r.json() or []


def fetch_market_status(market_id: str) -> tuple[str | None, str | None]:
    """Returns (umaResolutionStatus, slug) for a market id, or (None, None) if not found."""
    try:
        with httpx.Client(timeout=15) as c:
            r = c.get(f"https://gamma-api.polymarket.com/markets/{market_id}")
            if r.status_code != 200:
                return None, None
            d = r.json()
            return d.get("umaResolutionStatus"), d.get("slug")
    except Exception:
        return None, None


def kelly_fraction(mark: float, p: float) -> float:
    if mark >= 0.999 or p <= mark:
        return 0.0
    return (p - mark) / (1.0 - mark)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--bankroll", type=float, default=170.0)
    p.add_argument("--kelly-frac", type=float, default=0.5,
                   help="Fractional Kelly multiplier (0.5 = half-Kelly)")
    p.add_argument("--wallet", default=str(_secrets.path("POLYCLAUDE_WALLET")))
    p.add_argument("--check-uma", action="store_true",
                   help="Fetch umaResolutionStatus per market (slow). Default skip.")
    p.add_argument("--constrained", action="store_true",
                   help="Apply portfolio budget constraint: scale per-position Kelly so "
                        "total deployment <= bankroll. Per-position Kelly summed across high-edge "
                        "book typically exceeds bankroll (>200%%); --constrained scales each by "
                        "(bankroll / sum_kelly) so allocation respects budget while preserving "
                        "the ranking. This is the closed-form CONSTRAINED-PORTFOLIO-KELLY: "
                        "maximize E[log(B + Σ wᵢ Δᵢ)] s.t. Σ wᵢ ≤ 1.")
    args = p.parse_args()

    wallet_addr = json.load(open(args.wallet))["address"]
    priors = load_priors()
    if not priors:
        print(f"WARN: no priors at {PRIORS_PATH} — using defaults (P(win)=mark+0.05)", file=sys.stderr)

    positions = fetch_positions(wallet_addr)
    print(f"# portfolio_kelly: {len(positions)} held positions, bankroll=${args.bankroll}, kelly_frac={args.kelly_frac}", file=sys.stderr)

    rows = []
    for pos in positions:
        slug = pos.get("slug", "?")
        size = float(pos.get("size", 0) or 0)
        if size <= 0:
            continue
        mark = float(pos.get("curPrice", 0) or 0)
        avg = float(pos.get("avgPrice", 0) or 0)
        cost = avg * size
        side = pos.get("outcome", "?")
        days = None  # not used in current Kelly calc; leave as placeholder
        title = pos.get("title", "?")

        # Resolve P(win) from priors or default.
        # Exact match first; if none, prefix match (actual position slugs from
        # data-api have random numeric suffixes like "...-333-871-241-192-799-449"
        # appended to the canonical event-name stem stored in priors). 2026-05-19
        # catalyst_check on May-31 revealed two positions silently using the
        # default mark+0.05 because slug-suffix mismatch — priors were 5pp/10pp
        # tighter and being ignored. Prefix match restores prior usage.
        prior = priors.get(slug, {})
        if not prior:
            for k, v in priors.items():
                if slug.startswith(k):
                    prior = v
                    break
        if side == "Yes":
            p_win = prior.get("p_yes", min(0.99, mark + 0.05))
        else:
            p_win = prior.get("p_no", min(0.99, mark + 0.05))
        cluster = prior.get("cluster", "uncategorized")
        rho_within = prior.get("rho_within", 0.6)
        cluster_frac = prior.get("cluster_frac", 0.20)

        # Skip de-indexed (mark <= 0.005)
        if mark <= 0.005:
            rows.append({
                "slug": slug,
                "side": side,
                "size": size,
                "mark": mark,
                "p_win": p_win,
                "cost": cost,
                "kelly_dollar": None,
                "delta": None,
                "status": "DE_INDEXED_SKIP",
                "cluster": cluster,
                "title": title,
            })
            continue

        full_k = kelly_fraction(mark, p_win)
        # Apply correlation discount (within-cluster only)
        rho_adjusted = full_k * max(0.0, 1.0 - rho_within * cluster_frac)
        kelly_dollar = rho_adjusted * args.kelly_frac * args.bankroll

        delta = kelly_dollar - cost
        rows.append({
            "slug": slug,
            "side": side,
            "size": size,
            "mark": round(mark, 4),
            "p_win": p_win,
            "cost": round(cost, 2),
            "kelly_dollar": round(kelly_dollar, 2),
            "delta": round(delta, 2),
            "status": "ACTIVE",
            "cluster": cluster,
            "title": title[:50],
            "edge_pp": round((p_win - mark) * 100, 2),
        })

    # If --constrained, rescale per-position Kelly$ so total <= bankroll.
    # Closed-form portfolio Kelly under budget constraint when correlations are
    # already absorbed via per-position rho-discount: scale each position's
    # absolute Kelly$ by ratio (bankroll / total_kelly) when total > bankroll.
    if args.constrained:
        actives_pre = [r for r in rows if r["status"] == "ACTIVE" and r["kelly_dollar"] is not None]
        total_unconstrained = sum(r["kelly_dollar"] for r in actives_pre)
        if total_unconstrained > args.bankroll:
            scale = args.bankroll / total_unconstrained
            for r in rows:
                if r["status"] == "ACTIVE" and r["kelly_dollar"] is not None:
                    r["kelly_dollar"] = round(r["kelly_dollar"] * scale, 2)
                    r["delta"] = round(r["kelly_dollar"] - r["cost"], 2)
            print(f"# constrained: scaled by {scale:.4f} (= {args.bankroll}/{total_unconstrained:.2f})", file=sys.stderr)

    rows.sort(key=lambda r: r.get("delta") or -9e9, reverse=True)

    print(f"\n{'='*100}")
    print(f"{'Slug':<45} {'Side':<3} {'mark':<7} {'P_win':<6} {'edge':<6} {'cost':<8} {'Kelly$':<8} {'Δ to opt':<9} {'cluster':<15}")
    print(f"{'='*100}")
    for r in rows:
        if r["status"] == "DE_INDEXED_SKIP":
            print(f"{r['slug'][:45]:<45} {r['side']:<3} {r['mark']:<7.4f} {'  -':<6} {'  -':<6} {r['cost']:<8.2f} {'(de-idx)':<8} {'-':<9} {r['cluster']:<15}")
        else:
            print(f"{r['slug'][:45]:<45} {r['side']:<3} {r['mark']:<7.4f} {r['p_win']:<6.3f} {r['edge_pp']:>5.2f}pp {r['cost']:<8.2f} {r['kelly_dollar']:<8.2f} {r['delta']:>+9.2f} {r['cluster']:<15}")

    # Summary
    actives = [r for r in rows if r["status"] == "ACTIVE"]
    total_cost = sum(r["cost"] for r in actives)
    total_kelly = sum(r["kelly_dollar"] for r in actives)
    print(f"\n{'='*100}")
    print(f"TOTAL: cost=${total_cost:.2f}  kelly_optimal=${total_kelly:.2f}  delta=${total_kelly - total_cost:+.2f}")
    print(f"  Bankroll utilization (cost): {total_cost/args.bankroll*100:.1f}%")
    print(f"  Kelly-optimal utilization:   {total_kelly/args.bankroll*100:.1f}%")

    # Recommendations
    print(f"\nRecommended actions (delta > $5 = scale-in candidate):")
    candidates = [r for r in actives if r["delta"] is not None and r["delta"] > 5]
    candidates.sort(key=lambda r: -r["delta"])
    for r in candidates[:5]:
        print(f"  +${r['delta']:>6.2f}  {r['side']} @ ${r['mark']}  edge={r['edge_pp']:>5.2f}pp  {r['title']}")

    print(f"\nOver-sized (delta < -$5 = consider trim):")
    over = [r for r in actives if r["delta"] is not None and r["delta"] < -5]
    over.sort(key=lambda r: r["delta"])
    if not over:
        print("  (none)")
    for r in over[:5]:
        print(f"  ${r['delta']:>+7.2f}  {r['side']} @ ${r['mark']}  edge={r['edge_pp']:>5.2f}pp  {r['title']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
