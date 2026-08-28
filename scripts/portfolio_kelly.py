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
import datetime as dt
import json
import math
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as _secrets
import exit_analysis as exact_exit
import position_groups

REPO_ROOT = Path(__file__).resolve().parent.parent
PRIORS_PATH = REPO_ROOT / "notes" / "portfolio_kelly_priors.json"
MIN_POSITION_SHARES = 0.5



def _bankroll_default() -> float:
    """Live bankroll from bankroll.py's cache when fresh (<24h); else 170 + warn."""
    import datetime as _dt
    try:
        cache = Path(__file__).resolve().parent.parent / "notes" / ".bankroll_cache.json"
        d = json.loads(cache.read_text())
        age_h = (_dt.datetime.now(_dt.timezone.utc)
                 - _dt.datetime.fromisoformat(d["at"])).total_seconds() / 3600
        if age_h < 24:
            print(f"# bankroll ${d['total']:.2f} from cache (age {age_h:.1f}h)", file=sys.stderr)
            return float(d["total"])
        print(f"# WARNING: bankroll cache stale ({age_h:.0f}h) — run scripts/bankroll.py; using $170 fallback", file=sys.stderr)
    except Exception:
        print("# WARNING: no bankroll cache — run scripts/bankroll.py; using $170 fallback", file=sys.stderr)
    return 170.0


def load_priors() -> dict:
    if not PRIORS_PATH.exists():
        return {}
    return json.loads(PRIORS_PATH.read_text())


def filter_operational_positions(positions: list[dict]) -> list[dict]:
    """Exclude sub-0.5-share remnants that have no operational value."""
    kept = []
    for pos in positions:
        try:
            size = float(pos.get("size", 0) or 0)
        except (TypeError, ValueError):
            continue
        if size > MIN_POSITION_SHARES:
            kept.append(pos)
    return kept


def fetch_positions(addr: str) -> list[dict]:
    with httpx.Client(timeout=15) as c:
        r = c.get("https://data-api.polymarket.com/positions",
                  params={"user": addr.lower(), "limit": 100,
                          "sizeThreshold": MIN_POSITION_SHARES})
        r.raise_for_status()
        payload = r.json() or []
        if not isinstance(payload, list):
            raise ValueError("positions payload is not a list")
        for index, position in enumerate(payload):
            if not isinstance(position, dict):
                raise ValueError(f"position row {index} is not an object")
            try:
                size = float(position.get("size", 0) or 0)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"position row {index} has malformed size") from exc
            if not math.isfinite(size) or size < 0:
                raise ValueError(f"position row {index} has invalid size")
        # Defend locally too: the headline and allocation set must remain clean
        # if data-api ever ignores or changes sizeThreshold semantics.
        return filter_operational_positions(payload)


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


def set_only_label(prior: dict | None) -> str | None:
    """Return the generic set-only marker, including legacy arb pairs."""
    if not isinstance(prior, dict):
        return None
    return prior.get("set_only") or prior.get("arb_paired")


def _broken_group_reserve(
    member_rows: list[dict], bankroll: float
) -> tuple[float, float]:
    """Reserve known cost, or the full bankroll when member data is malformed."""
    total_cost = 0.0
    total_size = 0.0
    degraded = False
    for member in member_rows:
        try:
            size = float(member.get("size", 0) or 0)
            if not math.isfinite(size) or size < 0:
                raise ValueError("invalid size")
            total_size += size
        except (TypeError, ValueError):
            degraded = True
        try:
            total_cost += position_groups.position_cost(member)
        except Exception:
            degraded = True
    if degraded:
        total_cost = max(total_cost, float(bankroll))
    return total_cost, total_size


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--bankroll", type=float, default=None,
                   help="default: live total from bankroll.py cache (<24h), else 170")
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
    if args.bankroll is None:
        args.bankroll = _bankroll_default()

    wallet_addr = json.load(open(args.wallet))["address"]
    priors = load_priors()
    if not priors:
        print(f"WARN: no priors at {PRIORS_PATH} — using defaults (P(win)=mark+0.05)", file=sys.stderr)

    try:
        positions = fetch_positions(wallet_addr)
    except Exception as exc:
        print(
            f"ERROR: live positions unavailable/malformed ({type(exc).__name__}: {exc}); "
            "Kelly actions suppressed",
            file=sys.stderr,
        )
        return 2
    group_book = position_groups.evaluate_groups(priors, positions)
    grouped_slugs = set(group_book.by_slug)
    group_add_quotes: dict[str, list[tuple[str, dict, dict]]] = {}
    for group_id, group in group_book.groups.items():
        if group.get("status") != "OK":
            continue
        asks_by_leg: dict[str, list[dict]] = {}
        minimum_order_by_leg: dict[str, object] = {}
        fees_by_leg: dict[str, dict | None] = {}
        for leg_id, member in group["positions"].items():
            try:
                response = httpx.get(
                    "https://clob.polymarket.com/book",
                    params={"token_id": member["asset"]},
                    timeout=15,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or not isinstance(payload.get("asks"), list):
                    raise ValueError("malformed ask book")
                asks_by_leg[leg_id] = payload["asks"]
                if "min_order_size" not in payload:
                    raise ValueError("ask book lacks minimum order size")
                minimum_order_by_leg[leg_id] = payload["min_order_size"]
                fees_by_leg[leg_id] = exact_exit._execution_fee_market(
                    str(member.get("conditionId"))
                )
            except Exception:
                # Component quote below remains explicitly unpriced.
                continue
        alternatives: list[tuple[str, dict, dict]] = []
        for component in group["components"]:
            try:
                component_delta = position_groups.minimum_executable_component_delta(
                    component, minimum_order_by_leg
                )
            except Exception as exc:
                add_quote = {
                    "status": "GROUP_UNPRICED",
                    "actionable": False,
                    "issues": [
                        f"GROUP_UNPRICED {group_id}/{component['id']}: {exc}"
                    ],
                }
                alternatives.append(
                    (
                        component["id"],
                        add_quote,
                        position_groups.group_add_verdict(
                            group, add_quote, as_of=dt.date.today()
                        ),
                    )
                )
                continue
            leg_quotes: dict[str, dict] = {}
            minimum_order_by_slug: dict[str, object] = {}
            for leg_id, weight in component["weights"].items():
                if leg_id not in asks_by_leg:
                    continue
                member = group["positions"][leg_id]
                try:
                    leg_quotes[str(member["slug"])] = position_groups.walk_asks(
                        asks_by_leg[leg_id],
                        component_delta * float(weight),
                        fees_by_leg.get(leg_id),
                    )
                    minimum_order_by_slug[str(member["slug"])] = minimum_order_by_leg[
                        leg_id
                    ]
                except Exception:
                    # Missing/invalid leg quote makes the component explicitly
                    # ADD_UNPRICED below; it must not abort the whole audit.
                    continue
            add_quote = position_groups.quote_group_add(
                group,
                {component["id"]: component_delta},
                leg_quotes,
                minimum_order_by_slug=minimum_order_by_slug,
            )
            alternatives.append(
                (
                    component["id"],
                    add_quote,
                    position_groups.group_add_verdict(
                        group, add_quote, as_of=dt.date.today()
                    ),
                )
            )
        group_add_quotes[group_id] = alternatives
    print(f"# portfolio_kelly: {len(positions)} held rows, "
          f"{len(group_book.groups)} protected group(s), bankroll=${args.bankroll}, "
          f"kelly_frac={args.kelly_frac}", file=sys.stderr)

    rows = []
    for pos in positions:
        slug = pos.get("slug", "?")
        if slug in grouped_slugs:
            # Never let a broken/missing group prior fall into mark+5pp or a
            # per-leg Kelly delta. One economic row is appended below.
            continue
        size = float(pos.get("size", 0) or 0)
        if size <= MIN_POSITION_SHARES:
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
        set_only = set_only_label(prior)
        # Prior-staleness tag (2026-07-25): kimi verification went 3-for-3
        # catching priors resting on stale evidence this week (GPT-6, MacBook,
        # SpaceX). Any recommendation driven by a prior not re-verified within
        # 14d carries a visible warning — re-verify before acting on the flag.
        stale_tag = ""
        ver = prior.get("verified")
        try:
            age_d = (dt.date.today() - dt.date.fromisoformat(str(ver))).days if ver else None
        except Exception:
            age_d = None
        if prior and (age_d is None or age_d > 14):
            stale_tag = f"  [PRIOR-STALE: verified {'never-dated' if age_d is None else f'{age_d}d ago'} — re-verify before acting]"

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

        if set_only:
            # A per-leg Kelly delta is not an actionable quantity for matched
            # pairs or equal-share range bundles. Treat current deployment as a
            # fixed portfolio allocation and surface the invariant explicitly;
            # sizing changes must be re-run on the synthetic set economics.
            rows.append({
                "slug": slug,
                "side": side,
                "size": size,
                "mark": round(mark, 4),
                "p_win": p_win,
                "cost": round(cost, 2),
                "kelly_dollar": round(cost, 2),
                "delta": 0.0,
                "status": "SET_ONLY",
                "cluster": cluster,
                "title": title[:50],
                "edge_pp": round((p_win - mark) * 100, 2),
                "stale": stale_tag,
                "set_only": set_only,
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
            "stale": stale_tag,
        })

    # One row per economic structure. Point-estimate binary Kelly is valid for
    # Duma's covered union but not for MetaMask's variable multi-state payoff;
    # neither becomes an add instruction without a complete executable ask.
    # Reserve current cost once and expose component fairs for underwriting.
    for group_id, group in group_book.groups.items():
        if group.get("status") != "OK":
            member_rows = [
                position for position in positions
                if group_book.by_slug.get(str(position.get("slug"))) == group_id
            ]
            protected_cost, protected_size = _broken_group_reserve(
                member_rows, args.bankroll
            )
            rows.append({
                "slug": group_id,
                "side": "SET",
                "size": protected_size,
                "mark": 0.0,
                "p_win": 0.0,
                "cost": round(protected_cost, 2),
                "kelly_dollar": round(protected_cost, 2),
                "delta": 0.0,
                "status": "GROUP_BROKEN",
                "cluster": "group-structure",
                "title": group.get("label", group_id),
                "issues": group.get("issues", []),
            })
            continue
        component_text = ", ".join(
            f"{component['id']} fair/unit={component['fair_per_unit']:.3f}"
            for component in group["components"]
        )
        add_text_parts = []
        for component_id, add_quote, add_verdict in group_add_quotes.get(group_id, []):
            if add_quote.get("status") == "OK":
                delta = float(add_quote["component_deltas"][component_id])
                add_text_parts.append(
                    f"{component_id}: executable +{delta:g}; all-in/unit "
                    f"${add_quote['total'] / delta:.3f} vs fair/unit "
                    f"${add_quote['fair_value'] / delta:.3f} "
                    f"({add_verdict['verdict']})"
                )
            else:
                detail = "; ".join(add_quote.get("issues", []))
                suffix = f" ({detail})" if detail else ""
                add_text_parts.append(f"{component_id}: ADD_UNPRICED{suffix}")
        rows.append({
            "slug": group_id,
            "side": "SET",
            "size": group["total_shares"],
            "mark": (
                round(group["mark_value"], 4)
                if group["mark_value"] is not None else None
            ),
            "p_win": None,
            "cost": round(group["cost_basis"], 2),
            "kelly_dollar": round(group["cost_basis"], 2),
            "delta": 0.0,
            "status": "GROUP",
            "cluster": "group-structure",
            "title": group["label"],
            "edge_pp": None,
            "fair_value": group["fair_value"],
            "mark_value": group["mark_value"],
            "mark_status": group["mark_status"],
            "guaranteed_floor": group["guaranteed_floor"],
            "components": component_text,
            "add_components": "; ".join(add_text_parts),
            "add_gate": group["add_gate"],
        })

    # A global parse error leaves no strict group object, but the best-effort
    # suppression map still identifies protected members. Emit/reserve them as
    # one broken economic row per raw group rather than silently omitting cost.
    missing_group_ids = set(group_book.by_slug.values()) - set(group_book.groups)
    for group_id in sorted(missing_group_ids):
        member_rows = [
            position for position in positions
            if group_book.by_slug.get(str(position.get("slug"))) == group_id
        ]
        protected_cost, protected_size = _broken_group_reserve(
            member_rows, args.bankroll
        )
        rows.append({
            "slug": group_id,
            "side": "SET",
            "size": protected_size,
            "mark": 0.0,
            "p_win": 0.0,
            "cost": round(protected_cost, 2),
            "kelly_dollar": round(protected_cost, 2),
            "delta": 0.0,
            "status": "GROUP_BROKEN",
            "cluster": "group-structure",
            "title": group_id,
            "issues": group_book.issues,
        })

    # If --constrained, rescale per-position Kelly$ so total <= bankroll.
    # Closed-form portfolio Kelly under budget constraint when correlations are
    # already absorbed via per-position rho-discount: scale each position's
    # absolute Kelly$ by ratio (bankroll / total_kelly) when total > bankroll.
    if args.constrained:
        actives_pre = [r for r in rows if r["status"] == "ACTIVE" and r["kelly_dollar"] is not None]
        total_unconstrained = sum(r["kelly_dollar"] for r in actives_pre)
        fixed_set_cost = sum(
            r["cost"] for r in rows
            if r["status"] in ("SET_ONLY", "GROUP", "GROUP_BROKEN")
        )
        allocatable = max(0.0, args.bankroll - fixed_set_cost)
        if total_unconstrained > allocatable:
            scale = allocatable / total_unconstrained if total_unconstrained else 0.0
            for r in rows:
                if r["status"] == "ACTIVE" and r["kelly_dollar"] is not None:
                    r["kelly_dollar"] = round(r["kelly_dollar"] * scale, 2)
                    r["delta"] = round(r["kelly_dollar"] - r["cost"], 2)
            print(f"# constrained: scaled active legs by {scale:.4f} "
                  f"((${args.bankroll:.2f} - ${fixed_set_cost:.2f} fixed set-only) / "
                  f"${total_unconstrained:.2f})", file=sys.stderr)

    rows.sort(key=lambda r: r.get("delta") or -9e9, reverse=True)

    print(f"\n{'='*100}")
    print(f"{'Slug':<45} {'Side':<3} {'mark':<7} {'P_win':<6} {'edge':<6} {'cost':<8} {'Kelly$':<8} {'Δ to opt':<9} {'cluster':<15}")
    print(f"{'='*100}")
    for r in rows:
        if r["status"] == "DE_INDEXED_SKIP":
            print(f"{r['slug'][:45]:<45} {r['side']:<3} {r['mark']:<7.4f} {'  -':<6} {'  -':<6} {r['cost']:<8.2f} {'(de-idx)':<8} {'-':<9} {r['cluster']:<15}")
        elif r["status"] == "SET_ONLY":
            print(f"{r['slug'][:45]:<45} {r['side']:<3} {r['mark']:<7.4f} {r['p_win']:<6.3f} "
                  f"{r['edge_pp']:>5.2f}pp {r['cost']:<8.2f} {'(set)':<8} {'0.00':>9} {r['cluster']:<15}")
            print(f"    SET-ONLY: {r['set_only']}")
        elif r["status"] == "GROUP":
            print(f"{r['slug'][:45]:<45} {'SET':<3} {'  -':<7} {'  -':<6} {'  -':<6} "
                  f"{r['cost']:<8.2f} {'(group)':<8} {'0.00':>9} {r['cluster']:<15}")
            mark_text = (
                f"${r['mark_value']:.2f}"
                if r["mark_status"] == "OK" else "UNPRICED (de-indexed member)"
            )
            print(f"    GROUP: mark={mark_text} fair=${r['fair_value']:.2f} "
                  f"floor=${r['guaranteed_floor']:.2f}; {r['components']}; "
                  f"{r['add_components']}")
            print(f"    {r['add_gate']}")
        elif r["status"] == "GROUP_BROKEN":
            print(f"{r['slug'][:45]:<45} {'SET':<3} {'  -':<7} {'  -':<6} {'  -':<6} "
                  f"{r['cost']:<8.2f} {'BROKEN':<8} {'-':>9} {r['cluster']:<15}")
            print("    " + "; ".join(r.get("issues", [])))
        else:
            print(f"{r['slug'][:45]:<45} {r['side']:<3} {r['mark']:<7.4f} {r['p_win']:<6.3f} {r['edge_pp']:>5.2f}pp {r['cost']:<8.2f} {r['kelly_dollar']:<8.2f} {r['delta']:>+9.2f} {r['cluster']:<15}")

    # Summary
    actives = [r for r in rows if r["status"] == "ACTIVE"]
    fixed_sets = [
        r for r in rows if r["status"] in ("SET_ONLY", "GROUP", "GROUP_BROKEN")
    ]
    total_cost = sum(r["cost"] for r in actives + fixed_sets)
    total_kelly = (sum(r["kelly_dollar"] for r in actives)
                   + sum(r["cost"] for r in fixed_sets))
    print(f"\n{'='*100}")
    print(f"TOTAL: cost=${total_cost:.2f}  kelly_optimal=${total_kelly:.2f}  delta=${total_kelly - total_cost:+.2f}")
    print(f"  Bankroll utilization (cost): {total_cost/args.bankroll*100:.1f}%")
    print(f"  Kelly-optimal utilization:   {total_kelly/args.bankroll*100:.1f}%")

    # Recommendations
    print(f"\nRecommended actions (delta > $5 = scale-in candidate):")
    candidates = [r for r in actives if r["delta"] is not None and r["delta"] > 5]
    candidates.sort(key=lambda r: -r["delta"])
    for r in candidates[:5]:
        print(f"  +${r['delta']:>6.2f}  {r['side']} @ ${r['mark']}  edge={r['edge_pp']:>5.2f}pp  {r['title']}{r.get('stale','')}")

    # 2026-07-29: this section flagged the Fed position as over-sized for THREE
    # DAYS after I cut its prior 0.36->0.25, and I read it as informational —
    # because "consider trim" doesn't say HOW, and a taker trim usually loses to
    # holding once the fee is counted. Every over-sized line now prints the
    # fee-free route for public-information positions: rest a post-only sell AT
    # FAIR. Hidden-info positions need a premium above fair that explicitly pays
    # for jump risk; at/below-fair resting sells donate informed up-moves.
    print(f"\nOver-sized (delta < -$5) — choose the maker route by information class:")
    over = [r for r in actives if r["delta"] is not None and r["delta"] < -5]
    over.sort(key=lambda r: r["delta"])
    if not over:
        print("  (none)")
    for r in over[:5]:
        print(f"  ${r['delta']:>+7.2f}  {r['side']} @ ${r['mark']}  edge={r['edge_pp']:>5.2f}pp  {r['title']}{r.get('stale','')}")
        print(f"           -> PUBLIC-INFO: rest post-only SELL at {r['p_win']:.3f} "
              f"(= fair; fee-free). HIDDEN-INFO: sells at or below fair are banned because an "
              f"informed up-move can mean fair jumped; a premium-to-fair sell "
              f"(strictly above fair) is allowed when the premium compensates jump risk. "
              f"Thesis-break exits "
              f"remain active judgment. See notes/resting_orders.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
