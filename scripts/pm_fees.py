#!/usr/bin/env python3
"""Single source of truth for Polymarket trading fees.

WHY THIS EXISTS (2026-08-14 meta-reflection). The codebase carried THREE
different answers to "what does a Polymarket trade cost":

  * `POLYMARKET_FEE_RATE = 0.072` hard-coded in SEVEN scripts (discover_markets,
    event_monotonicity_scan, polymarket_consistency_scan, sports_pm_scan,
    limitless_arb_scan, limitless_arb_executor, and a default arg in
    sports_pm_scan.annualized_apy)
  * `TAKER_FEE_RATE = 0.10` in check_marginal_apy
  * a LIVE read of `takerBaseFee` in polyclaude_enter — the closest available
    source at the time, before Gamma exposed the structured V2 schedule

The legacy Gamma field ``takerBaseFee`` is now only a compatibility fallback.
Live Gamma markets expose the actual V2 curve under::

    feeSchedule = {"rate": 0.04, "exponent": 1, "takerOnly": True}

As of 2026-08-28, ``takerBaseFee`` is still 1000 on every fee-bearing market
sampled even though ``feeSchedule.rate`` varies by category (0.03/0.04/0.05/
0.07). Treating 1000 bps as the rate therefore overstates most fees and can
silently reject good trades. ``feeSchedule`` wins whenever it is present.
Legacy behavior is retained only for old/cached payloads without a schedule,
and ambiguous fetched payloads fail closed to the conservative fallback
instead of silently becoming fee-free.

The historical zero-fee case matters too, in the opposite direction: Greenland carries
takerBaseFee=None, and the exit-cost gate shipped earlier the same day charged
it a fee that does not exist, reporting "closing costs $0.17" against a true
cost of zero. That biased toward holding.

USAGE — prefer passing the Gamma market dict you already fetched:

    from pm_fees import fee_per_share, fee_rate

    f = fee_per_share(market_dict, price)     # dollars per share
    r = fee_rate(market_dict)                 # fraction, e.g. 0.04 or 0.0

When you only have a slug, `fee_rate_for_slug` fetches and caches per-process.

FALLBACK POLICY: unknown/unfetchable markets retain the legacy conservative
FEE_RATE_FALLBACK (0.10), capped to 0.07 by the old-path compatibility rule.
An overstated fee kills a marginal trade, while an understated one books a
loss as a win. For arb and discovery paths that asymmetry is the whole ballgame.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import httpx

# Legacy modal value (84/100 active markets, measured 2026-08-14 before the
# structured schedule became authoritative). Used when the market payload is
# unavailable or legacy metadata is malformed. See FALLBACK POLICY above.
FEE_RATE_FALLBACK = 0.10

# All legacy fee curves in this repository used exponent 1. Gamma's structured
# feeSchedule now carries this explicitly. Keep 1 as the conservative/default
# value for old/unknown payloads. Malformed structured schedules use the
# separate maximal fail-closed value below because their exponent is unbounded.
FEE_EXPONENT_FALLBACK = 1.0

# A present but malformed structured curve has no defensible numerical bound
# (the schema's exponent lower bound is not documented). Advisory/scanner paths
# therefore price it at the full $1 payout per share; live execution paths
# reject the descriptor before reaching this fallback.
MALFORMED_FEE_PER_SHARE = 1.0

# TRUE FEE CURVE (corrected 2026-08-22). The charge is QUADRATIC, not min():
#     fee = shares x rate x p x (1-p)        [docs.polymarket.com fees page]
# and the legacy EFFECTIVE rate is category-capped at 0.07 (current structured
# category rates run 0.03-0.07), NOT takerBaseFee/10000. Established by
# invariance-chasing two
# same-day arb entries and reconciling against wallet pUSD deltas:
#   fill set 1: 15.25sh@0.0787 + 15.03sh@0.888 -> TRUE fee $0.182
#   fill set 2: 32.47sh@0.0804 + 29.72sh@0.849 -> TRUE fee $0.435
# rate=0.07 quadratic predicts $0.182 / $0.435 — both EXACT. The old
# rate=0.10 x min(p,1-p) predicted $0.29 / $0.71 — ~40% high at the tails and
# ~3x high at p=0.50 (0.050 vs 0.0175/share). Direction of the old error was
# safe (killed marginal trades) but it distorted arb floors and breakevens.
# Markets whose field is a lower rate (e.g. 500bps) keep their own lower rate.
CATEGORY_RATE_CAP = 0.07

GAMMA = "https://gamma-api.polymarket.com/markets"

_SLUG_CACHE: dict[str, float] = {}


@dataclass(frozen=True)
class FeeCurve:
    """Normalized per-market fee parameters.

    ``authoritative`` distinguishes Gamma's V2 ``feeSchedule.rate`` from the
    legacy ``takerBaseFee`` field. The old field needs the historical 0.07 cap;
    the structured schedule is already the protocol rate and must not be
    altered (important for curves such as rate=0.25, exponent=2).
    """

    rate: float
    exponent: float
    taker_only: bool
    authoritative: bool


def _nonnegative_finite(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) and parsed >= 0.0 else None


def fee_schedule(market: dict | None) -> FeeCurve:
    """Return normalized fee parameters, preferring Gamma ``feeSchedule``.

    A present, valid structured schedule is the source of truth even when its
    rate conflicts with ``takerBaseFee``. ``takerOnly`` does not remove the fee
    from taker calculations: false means makers may also be charged, while a
    taker still pays. Maker economics remain handled by execution-role callers.

    ``market=None`` means the fetch failed and receives the conservative legacy
    fallback. Explicit ``feesEnabled=False`` and explicit zero-valued schedules
    are fee-free. For old payloads without a ``feesEnabled`` field, an
    explicitly present null/zero ``takerBaseFee`` also retains the historical
    fee-free meaning. Missing fee fields are ambiguous and therefore fall back.
    Most importantly, ``feesEnabled=True`` can never become fee-free merely
    because ``feeSchedule`` and ``takerBaseFee`` are absent or null. A present
    malformed structured schedule is harsher: advisory math charges the full
    $1 payout/share, while live execution callers reject it outright.
    """
    if market is None:
        return FeeCurve(FEE_RATE_FALLBACK, FEE_EXPONENT_FALLBACK, True, False)

    # Gamma's explicit market-level disable flag is sufficient evidence of a
    # free market. Use identity checks: malformed/truthy strings must not be
    # interpreted as authoritative booleans in either direction.
    fee_flag_present = "feesEnabled" in market
    fee_flag = market.get("feesEnabled")
    if fee_flag is False:
        return FeeCurve(0.0, FEE_EXPONENT_FALLBACK, True, False)

    fees_enabled = fee_flag is True
    fee_flag_ambiguous = fee_flag_present and not isinstance(fee_flag, bool)

    # A mapping, including a malformed one, means Gamma attempted to provide
    # the V2 source of truth; do not silently trust a conflicting legacy field
    # when the structured rate cannot be parsed. A non-null, non-mapping value
    # is malformed too and fails closed rather than falling through.
    schedule = market.get("feeSchedule")
    if isinstance(schedule, dict):
        rate = _nonnegative_finite(schedule.get("rate"))
        exponent = _nonnegative_finite(schedule.get("exponent"))
        if rate is None or exponent is None:
            return FeeCurve(MALFORMED_FEE_PER_SHARE, 0.0, True, True)
        return FeeCurve(
            rate=rate,
            exponent=exponent,
            taker_only=bool(schedule.get("takerOnly", True)),
            authoritative=True,
        )
    if schedule is not None:
        return FeeCurve(MALFORMED_FEE_PER_SHARE, 0.0, True, True)

    legacy_present = "takerBaseFee" in market
    bps = market.get("takerBaseFee")
    if bps in (None, "", "None"):
        # Null is evidence of a legacy fee-free market only when the field was
        # actually supplied and the newer market flag is absent.
        if not legacy_present or fees_enabled or fee_flag_ambiguous:
            return FeeCurve(FEE_RATE_FALLBACK, FEE_EXPONENT_FALLBACK, True, False)
        return FeeCurve(0.0, FEE_EXPONENT_FALLBACK, True, False)
    parsed_bps = _nonnegative_finite(bps)
    if parsed_bps is None:
        return FeeCurve(FEE_RATE_FALLBACK, FEE_EXPONENT_FALLBACK, True, False)
    # An enabled-fee payload carrying legacy zero is internally inconsistent;
    # charge the fallback rather than let the weaker legacy field disable fees.
    if parsed_bps == 0.0 and (fees_enabled or fee_flag_ambiguous):
        return FeeCurve(FEE_RATE_FALLBACK, FEE_EXPONENT_FALLBACK, True, False)
    return FeeCurve(parsed_bps / 10000.0, FEE_EXPONENT_FALLBACK, True, False)


def fee_rate(market: dict | None) -> float:
    """Taker fee rate, preferring the market's structured Gamma schedule.

    Returns 0.0 only for explicit evidence of no fees: ``feesEnabled=False``, a
    valid structured zero rate, or an explicitly present legacy null/zero on an
    old payload without a ``feesEnabled`` field. Missing or contradictory fields
    receive the conservative fallback.
    """
    return fee_schedule(market).rate


def fee_exponent(market: dict | None) -> float:
    """Gamma exponent; 1 for legacy/unknown, 0 for maximal malformed fallback."""
    return fee_schedule(market).exponent


def effective_rate(raw_rate: float) -> float:
    """Cap a field-derived rate at the documented category maximum (0.07).

    takerBaseFee=1000 does NOT mean a 10% charge — the wallet-verified fills
    above pin the effective rate at 0.07 for these markets, and the docs cap
    category rates there. A field rate BELOW the cap (e.g. 250bps) is kept.
    """
    return min(raw_rate, CATEGORY_RATE_CAP)


def fee_per_share_at(raw_rate: float, price: float,
                     exponent: float = FEE_EXPONENT_FALLBACK, *,
                     authoritative: bool = False) -> float:
    """Dollars of fee per share for explicit curve parameters.

    V2 curve: ``rate * (p * (1-p)) ** exponent``. Current Gamma schedules use
    exponent 1, which is the wallet-verified ``rate * p * (1-p)`` curve. The
    default keeps all legacy callers byte-for-byte equivalent. Set
    ``authoritative=True`` only for a structured schedule rate; legacy raw bps
    rates still receive the historical 0.07 compatibility cap.
    """
    rate = float(raw_rate) if authoritative else effective_rate(float(raw_rate))
    return rate * (price * (1.0 - price)) ** float(exponent)


def fee_per_share(market: dict | None, price: float) -> float:
    """Dollars of fee per share at `price` for this market."""
    curve = fee_schedule(market)
    return fee_per_share_at(
        curve.rate,
        price,
        curve.exponent,
        authoritative=curve.authoritative,
    )


def max_taker_buy_cost_through(market: dict | None, limit_price: float) -> float:
    """Worst all-in BUY cost/share for any fill at or below ``limit_price``.

    ``price + fee(price)`` is increasing for every observed V2 curve, even
    though the fee component alone peaks at 0.50. Validate that monotonicity
    analytically for the supplied nonnegative-exponent curve; an unfamiliar
    curve that could be non-monotone is rejected instead of under-reserved.
    """
    price = float(limit_price)
    if not math.isfinite(price) or not 0.0 < price < 1.0:
        raise ValueError("limit price must be finite and between 0 and 1")
    curve = fee_schedule(market)
    rate = curve.rate if curve.authoritative else effective_rate(curve.rate)
    exponent = curve.exponent
    if rate > 0.0 and exponent > 0.0 and price > 0.5:
        max_t = 2.0 * price - 1.0
        if exponent > 1.0:
            max_t = min(max_t, 1.0 / math.sqrt(2.0 * exponent - 1.0))
        x = (1.0 - max_t * max_t) / 4.0
        negative_fee_slope = rate * exponent * max_t * x ** (exponent - 1.0)
        if not math.isfinite(negative_fee_slope) or negative_fee_slope > 1.0 + 1e-12:
            raise ValueError("taker BUY all-in cost is non-monotone below the limit")
    return price + fee_per_share(market, price)


def fee_rate_for_slug(slug: str, client: httpx.Client | None = None) -> float:
    """fee_rate() for a slug, cached per-process. Falls back on any failure."""
    if slug in _SLUG_CACHE:
        return _SLUG_CACHE[slug]
    try:
        c = client or httpx.Client(timeout=20.0)
        m = c.get(GAMMA, params={"slug": slug}).json()[0]
        rate = fee_rate(m)
    except Exception:
        rate = FEE_RATE_FALLBACK
    _SLUG_CACHE[slug] = rate
    return rate


if __name__ == "__main__":
    import sys
    from collections import Counter
    # Self-check: re-measure the live distribution the module's defaults rest on.
    with httpx.Client(timeout=30.0) as c:
        ms = c.get(GAMMA, params={"closed": "false", "limit": "500",
                                  "order": "volume24hr", "ascending": "false"}).json()
    dist = Counter((fee_rate(m), fee_exponent(m)) for m in ms)
    print(f"sampled {len(ms)} active markets by 24h volume")
    for (r, e), n in dist.most_common():
        print(f"  fee curve rate={r:.4f} exponent={e:g}  x{n}  ({n/len(ms)*100:.0f}%)")
    fallback_peak = fee_per_share(None, 0.50)
    max_live_peak = max((fee_per_share(m, 0.50) for m in ms), default=0.0)
    if fallback_peak + 1e-12 < max_live_peak:
        print(f"!! fallback peak fee/share={fallback_peak:.6f} is below live max "
              f"{max_live_peak:.6f} — unknown markets are no longer conservative.")
        sys.exit(1)
    print(f"OK: fallback peak fee/share={fallback_peak:.6f} covers live max "
          f"{max_live_peak:.6f}.")
