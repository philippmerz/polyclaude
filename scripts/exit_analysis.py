#!/usr/bin/env python3
"""Hold vs sell, computed on the LIVE book, for every open position.

Every exit is three options, not two, and the fee makes the route decisive:
  HOLD            -> EV = shares x fair            (resolution is FEE-FREE)
  SELL TAKER now  -> walk the real BID book, minus the execution-time V2 taker
                     curve at each level (`pm_fees`, including its exponent)
  REST MAKER sell -> post-only, fee-free, so the breakeven price IS `fair`;
                     the order only fills if someone pays >= fair.

Lesson sources: the Prime-SDCC exit (2026-07-24) sold taker into a thin book at
the midpoint's flattering price and gave up ~$2 of EV vs holding; the Fed
position (2026-07-28) showed taker breakeven 0.2778 vs maker breakeven 0.2500 —
a 2.8pp gap that decides the trade. Doctrine (notes/resting_orders.md): when
hold and sell are close, DON'T CHOOSE — rest a maker sell at the strictly-better
price and let the market decide.

Reads fair values from notes/portfolio_kelly_priors.json (side-aware, and it
respects the `verified` staleness convention by WARNING on priors > 14d).

CLI: exit_analysis.py [--slug-filter TEXT]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

import httpx

from pm_fees import fee_per_share, fee_schedule
import position_groups

REPO = Path(__file__).resolve().parent.parent
PRIORS = REPO / "notes" / "portfolio_kelly_priors.json"
ADDR = "0x9032ad983ee5a22bfd078ecc4fd3d4d69e57267b"


def _fair(slug: str, side: str, priors: dict):
    for k, v in priors.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        if k in slug or slug in k:
            p = v.get("p_no") if side == "No" else v.get("p_yes")
            return (float(p) if p is not None else None), v.get("verified")
    return None, None


def _execution_fee_market(condition_id: str) -> dict | None:
    """Return the execution-time CLOB fee curve in ``pm_fees`` form.

    The full CLOB market's ``taker_base_fee`` is a stale compatibility field:
    live fee-bearing markets can all say 1000 there while the compact V2
    descriptor carries the actual category rate and exponent as ``fd={r,e,to}``.
    Trust only that compact descriptor for a positive curve.  If compact says
    no descriptor exists, retain the full endpoint solely as an explicit-zero
    compatibility fallback.  Every missing, malformed, contradictory, or
    unreachable state returns ``None``, which is deliberately charged at
    ``pm_fees``' conservative fallback rather than silently becoming fee-free.
    """
    try:
        compact_r = httpx.get(
            f"https://clob.polymarket.com/clob-markets/{condition_id}",
            timeout=15,
        )
        compact_r.raise_for_status()
        compact = compact_r.json()
    except Exception:
        return None
    if not isinstance(compact, dict):
        return None
    if str(compact.get("c") or "").lower() != condition_id.lower():
        return None

    descriptor = compact.get("fd")
    if isinstance(descriptor, dict):
        # Preserve the whole structured curve. pm_fees validates all numerical
        # fields and fails closed if the descriptor itself is malformed.
        return {
            "feesEnabled": True,
            "feeSchedule": {
                "rate": descriptor.get("r"),
                "exponent": descriptor.get("e"),
                "takerOnly": descriptor.get("to", True),
            },
        }
    if descriptor is not None:
        return None

    # Compact explicitly has no V2 descriptor. The old endpoint may establish
    # only the unambiguous fee-free case; a positive legacy 1000 must never
    # override a missing execution-time schedule.
    try:
        full_r = httpx.get(
            f"https://clob.polymarket.com/markets/{condition_id}", timeout=15
        )
        full_r.raise_for_status()
        full = full_r.json()
    except Exception:
        return None
    if not isinstance(full, dict):
        return None
    if str(full.get("condition_id") or "").lower() != condition_id.lower():
        return None
    try:
        legacy_rate = float(full["taker_base_fee"])
    except (KeyError, TypeError, ValueError):
        return None
    if math.isfinite(legacy_rate) and legacy_rate == 0.0:
        return {"takerBaseFee": 0}
    return None


def _walk_bids(token: str, shares: float,
               fee_market: dict | None) -> tuple[float, float, float]:
    """Return gross, filled shares, and exact fee walking the real bid side.

    Fees are calculated at every fill level. Applying a non-linear V2 curve to
    the volume-weighted average price is not equivalent when a sale crosses
    multiple levels, particularly when ``feeSchedule.exponent != 1``.
    """
    b = httpx.get("https://clob.polymarket.com/book",
                  params={"token_id": token}, timeout=15).json()
    bids = sorted(b.get("bids", []), key=lambda x: -float(x["price"]))
    rem, gross, fees = shares, 0.0, 0.0
    for lvl in bids:
        px, sz = float(lvl["price"]), float(lvl["size"])
        if (not math.isfinite(px) or not 0.0 <= px <= 1.0
                or not math.isfinite(sz) or sz < 0.0):
            raise ValueError("malformed binary bid level")
        take = min(rem, sz)
        gross += take * px
        fees += take * fee_per_share(fee_market, px)
        rem -= take
        if rem <= 0:
            break
    return gross, shares - rem, fees


def _curve_is_monotone_from(fair: float, rate: float, exponent: float) -> bool:
    """Whether taker net proceeds are non-decreasing on ``[fair, 1]``.

    This lets the breakeven solver fail explicitly instead of returning an
    arbitrary root for a hypothetical extreme schedule with several roots.
    All observed V2 schedules clear this condition comfortably.
    """
    if rate <= 0.0 or exponent == 0.0 or fair >= 0.5:
        return True
    if exponent < 1.0:
        if fair <= 0.0:
            return False
        max_fee_slope = (
            exponent
            * (fair * (1.0 - fair)) ** (exponent - 1.0)
            * (1.0 - 2.0 * fair)
        )
    elif exponent == 1.0:
        max_fee_slope = 1.0 - 2.0 * fair
    else:
        peak = (1.0 - 1.0 / math.sqrt(2.0 * exponent - 1.0)) / 2.0
        p = peak if fair <= peak else fair
        max_fee_slope = (
            exponent
            * (p * (1.0 - p)) ** (exponent - 1.0)
            * (1.0 - 2.0 * p)
        )
    return rate * max_fee_slope <= 1.0 + 1e-12


def _taker_breakeven(fair: float, fee_market: dict | None) -> float | None:
    """Lowest safely defined bid whose taker net/share reaches ``fair``.

    Solves ``p - rate*[p*(1-p)]**exponent = fair`` by bisection. ``None``
    means there is no in-range solution or the supplied curve is not monotone
    over the relevant interval, in which case displaying a scalar threshold
    would be operationally unsafe.
    """
    if not 0.0 <= fair <= 1.0:
        raise ValueError("fair must be between 0 and 1")
    curve = fee_schedule(fee_market)
    if curve.rate == 0.0:
        return fair
    if not _curve_is_monotone_from(fair, curve.rate, curve.exponent):
        return None

    def surplus(price: float) -> float:
        return price - fee_per_share(fee_market, price) - fair

    lo, hi = fair, 1.0
    if surplus(hi) < -1e-12:
        return None
    if surplus(lo) >= -1e-15:
        return lo
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if surplus(mid) >= 0.0:
            hi = mid
        else:
            lo = mid
    return hi


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug-filter", default=None)
    args = ap.parse_args()

    priors = json.loads(PRIORS.read_text())
    pos = httpx.get("https://data-api.polymarket.com/positions",
                    params={"user": ADDR, "limit": "100"}, timeout=25).json()
    group_book = position_groups.evaluate_groups(priors, pos)
    selected_group_ids = {
        group_id
        for group_id, group in group_book.groups.items()
        if not args.slug_filter
        or args.slug_filter in group_id
        or args.slug_filter.lower() in str(group.get("label", "")).lower()
        or any(args.slug_filter in slug for slug in group.get("slugs", []))
    }
    selected_group_slugs = {
        slug
        for slug, group_id in group_book.by_slug.items()
        if group_id in selected_group_ids
    }
    today = dt.date.today()
    rows = []
    quotes_by_slug: dict[str, dict] = {}
    for p in pos:
        slug = str(p.get("slug", ""))
        protected_group_id = group_book.by_slug.get(slug)
        if (protected_group_id is not None
                and group_book.groups.get(protected_group_id, {}).get("status") != "OK"):
            continue
        try:
            shares = float(p.get("size", 0))
        except (TypeError, ValueError):
            print(f"  [UNPRICED] malformed size on {slug[:52]}", file=sys.stderr)
            continue
        if not math.isfinite(shares) or shares < 0.5:
            continue
        if (args.slug_filter and args.slug_filter not in slug
                and slug not in selected_group_slugs):
            continue
        side = p["outcome"]
        fair, verified = _fair(slug, side, priors)
        if fair is None:
            print(f"  [NO PRIOR] {slug[:52]} — add one to price the exit", file=sys.stderr)
            continue
        # Execution-time compact V2 schedule. Missing or malformed metadata is
        # deliberately represented as None so pm_fees charges its conservative
        # fallback; only an explicit legacy zero can establish fee-free status.
        try:
            fee_market = _execution_fee_market(str(p.get("conditionId")))
            gross, filled, taker_fee = _walk_bids(p["asset"], shares, fee_market)
        except Exception as exc:
            print(
                f"  [UNPRICED] exit book unavailable for {slug[:52]} "
                f"({type(exc).__name__})",
                file=sys.stderr,
            )
            # For a group, the absent quote is consumed below as one explicit
            # GROUP_UNPRICED result. Never abort or fall back to member math.
            continue
        avg_fill = (gross / filled) if filled else 0.0
        taker_net = gross - taker_fee
        quotes_by_slug[slug] = {
            "gross": gross,
            "fee": taker_fee,
            "net": taker_net,
            "filled": filled,
            "unfilled": max(0.0, shares - filled),
        }
        hold_ev = shares * fair
        taker_be = _taker_breakeven(fair, fee_market)
        taker_be_text = (
            f"{taker_be:.3f}" if taker_be is not None
            else "unavailable (no safe scalar for this fee curve)"
        )
        stale = ""
        try:
            if verified and (today - dt.date.fromisoformat(str(verified))).days > 14:
                stale = " [PRIOR-STALE]"
        except Exception:
            stale = " [PRIOR-UNDATED]"
        hidden, set_only = False, None
        for kk, vv in priors.items():
            if isinstance(vv, dict) and (kk in slug or slug in kk):
                hidden = bool(vv.get("hidden_info"))
                # `arb_paired` is the original riskless-pair marker. `set_only`
                # generalizes the same operational invariant to directional
                # equal-share structures (for example a contiguous range):
                # per-leg exit math is still meaningless and potentially harmful.
                set_only = vv.get("set_only") or vv.get("arb_paired")
                break
        grouped = slug in group_book.by_slug
        if set_only or grouped:
            # SET-ONLY legs are priced per-leg but only mean anything as a set.
            # For riskless pairs, closing one leg creates naked exposure; for a
            # range bundle, it destroys the equal covered-state payout. Either
            # way the per-leg sell comparison must never drive execution.
            # Added 2026-08-25 the moment this tool printed "SELL TAKER NOW
            # (+$0.36)" on the Metamask 700M leg — a verdict a headless fallback
            # tick (one ran two days earlier, with no conversation context) could
            # have executed mechanically. The doctrine note lived in the priors
            # file and the tool printed the sell anyway: a rule written down is
            # not a rule enforced.
            gap = taker_net - hold_ev
            marker = set_only or f"group {group_book.by_slug[slug]}"
            verdict = (f"HOLD — SET-ONLY ({marker}); per-leg math says "
                       f"{'SELL +' if gap > 0 else 'hold '}${abs(gap):.2f} but that number is "
                       f"MEANINGLESS ALONE. Re-underwrite and transact the complete set, or let it resolve.")
        elif taker_net > hold_ev:
            verdict = f"SELL TAKER NOW (+${taker_net - hold_ev:.2f} vs hold)"
            if hidden:
                verdict += " [hidden-info: VERIFY the move first]"
        elif hidden:
            # Hidden-info doctrine, REFINED 2026-08-18 and reflected here
            # 2026-08-25: resting AT or BELOW fair is banned (an informed lift
            # means fair jumped, and the stale-fair sell donates the news), but
            # resting ABOVE fair is PERMITTED — the premium is the compensation
            # for jump risk. This text still imposed the superseded blanket ban while the
            # book carried four permitted premium rests (Gemini 0.60 vs fair
            # 0.54, OpenAI 0.70/0.45, MacBook 0.69), i.e. the tool contradicted
            # both the doctrine and the live book. The lesson sitting next to
            # the refinement says it: when practice diverges from a written
            # rule, the expensive outcome is leaving both on the page.
            verdict = (f"HOLD (+${hold_ev - taker_net:.2f}); HIDDEN-INFO: rest maker sell only "
                       f"ABOVE fair {fair:.3f} (premium = jump-risk pay; at/below fair is BANNED "
                       f"— donates the news). Taker breakeven {taker_be_text}")
        else:
            verdict = (f"HOLD (+${hold_ev - taker_net:.2f}); rest maker sell >= "
                       f"{fair:.3f} (taker would need {taker_be_text})")
        rows.append((slug, side, shares, fair, avg_fill, hold_ev, taker_net, verdict, stale))

    if not rows and not selected_group_ids and not group_book.issues:
        print("no priced positions")
        return 0
    print(f"{'position':<44}{'side':>5}{'sh':>7}{'fair':>7}{'bid~':>7}{'hold$':>8}{'sell$':>8}  verdict")
    for slug, side, sh, fair, bid, hold_ev, taker_net, verdict, stale in rows:
        if slug in group_book.by_slug:
            continue
        print(f"{slug[:44]:<44}{side:>5}{sh:>7.1f}{fair:>7.3f}{bid:>7.3f}"
              f"{hold_ev:>8.2f}{taker_net:>8.2f}  {verdict}{stale}")
    if selected_group_ids:
        print("\nGROUP STRUCTURES (member-leg actions suppressed)")
        for group_id in sorted(selected_group_ids):
            group = group_book.groups[group_id]
            quote = position_groups.quote_group_exit(group, quotes_by_slug)
            verdict = position_groups.group_exit_verdict(
                group, quote, as_of=today
            )
            print("  " + position_groups.format_group_summary(group, quote, verdict))
    if group_book.issues:
        represented = {
            issue
            for group in group_book.groups.values()
            for issue in group.get("issues", [])
        }
        extra_issues = [issue for issue in group_book.issues if issue not in represented]
        if extra_issues:
            print("\nGROUP CONFIGURATION ISSUES (all member-leg actions suppressed)")
            for issue in extra_issues:
                print(f"  {issue}")
    print("\nresolution is fee-free; maker sells are fee-free; taker sells pay "
          "rate x [p x (1-p)]^exponent/share at each fill level (V2 curve) — "
          "that gap is usually the whole decision.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
