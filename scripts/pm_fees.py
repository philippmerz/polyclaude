#!/usr/bin/env python3
"""Single source of truth for Polymarket trading fees.

WHY THIS EXISTS (2026-08-14 meta-reflection). The codebase carried THREE
different answers to "what does a Polymarket trade cost":

  * `POLYMARKET_FEE_RATE = 0.072` hard-coded in SEVEN scripts (discover_markets,
    event_monotonicity_scan, polymarket_consistency_scan, sports_pm_scan,
    limitless_arb_scan, limitless_arb_executor, and a default arg in
    sports_pm_scan.annualized_apy)
  * `TAKER_FEE_RATE = 0.10` in check_marginal_apy
  * a LIVE read of `takerBaseFee` in polyclaude_enter — the only one that was right

Measured against 100 active markets sorted by 24h volume: 84 carry
takerBaseFee=1000 bps (10%) and 16 carry None (no fee at all). So the fee is
not a constant in the first place — it is a per-market field, and any single
hard-coded number is wrong in BOTH directions at once. The dominant error is
the dangerous one: 0.072 understates a real 10% fee by 28%, and it was sitting
inside the arb scanners and the discovery filter, i.e. exactly the places where
understating cost manufactures an opportunity that is not there. Six phantom
"REAL ARB" fires had already come out of that machinery this week from an
unrelated parsing bug; this was a second, independent generator of the same
failure waiting behind it.

The 16% zero-fee case matters too, in the opposite direction: Greenland carries
takerBaseFee=None, and the exit-cost gate shipped earlier the same day charged
it a fee that does not exist, reporting "closing costs $0.17" against a true
cost of zero. That biased toward holding.

USAGE — prefer passing the gamma market dict you already fetched:

    from pm_fees import fee_per_share, fee_rate

    f = fee_per_share(market_dict, price)     # dollars per share
    r = fee_rate(market_dict)                 # fraction, e.g. 0.10 or 0.0

When you only have a slug, `fee_rate_for_slug` fetches and caches per-process.

FALLBACK POLICY: unknown/unfetchable markets return FEE_RATE_FALLBACK (0.10),
the modal live value. Deliberately the HIGH end — an overstated fee kills a
marginal trade, while an understated one books a loss as a win. For arb and
discovery paths that asymmetry is the whole ballgame.
"""

from __future__ import annotations

import httpx

# Modal live value (84/100 active markets, measured 2026-08-14). Used only when
# the market's own field is unavailable. See FALLBACK POLICY above for why this
# is the high end rather than a blend.
FEE_RATE_FALLBACK = 0.10

# TRUE FEE CURVE (corrected 2026-08-22). The charge is QUADRATIC, not min():
#     fee = shares x rate x p x (1-p)        [docs.polymarket.com fees page]
# and the EFFECTIVE rate is category-capped at 0.07 (docs: category rates run
# 0.04-0.07), NOT takerBaseFee/10000. Established by invariance-chasing two
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


def fee_rate(market: dict | None) -> float:
    """Taker fee RATE as a fraction, read from the market's own takerBaseFee.

    Returns 0.0 when the market explicitly carries no fee (None/0/absent-but-
    fetched), which is 16% of live markets — NOT a missing value to be filled
    with the fallback. Callers that genuinely could not fetch the market should
    pass None to get the conservative fallback instead.
    """
    if market is None:
        return FEE_RATE_FALLBACK
    bps = market.get("takerBaseFee")
    if bps in (None, "", "None"):
        return 0.0
    try:
        return float(bps) / 10000.0
    except (TypeError, ValueError):
        return FEE_RATE_FALLBACK


def effective_rate(raw_rate: float) -> float:
    """Cap a field-derived rate at the documented category maximum (0.07).

    takerBaseFee=1000 does NOT mean a 10% charge — the wallet-verified fills
    above pin the effective rate at 0.07 for these markets, and the docs cap
    category rates there. A field rate BELOW the cap (e.g. 250bps) is kept.
    """
    return min(raw_rate, CATEGORY_RATE_CAP)


def fee_per_share_at(raw_rate: float, price: float) -> float:
    """Dollars of fee per share at `price` for a given field rate.

    TRUE curve (see header): rate x p x (1-p), quadratic — largest at 0.50
    ($0.0175/share at the 0.07 cap) and vanishing at BOTH extremes faster than
    the old min() model assumed. Verified exact against two wallet-reconciled
    fill sets on 2026-08-22.
    """
    return effective_rate(raw_rate) * price * (1.0 - price)


def fee_per_share(market: dict | None, price: float) -> float:
    """Dollars of fee per share at `price` for this market."""
    return fee_per_share_at(fee_rate(market), price)


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
    dist = Counter(fee_rate(m) for m in ms)
    print(f"sampled {len(ms)} active markets by 24h volume")
    for r, n in dist.most_common():
        print(f"  fee_rate {r:.4f}  x{n}  ({n/len(ms)*100:.0f}%)")
    modal = dist.most_common(1)[0][0]
    if abs(modal - FEE_RATE_FALLBACK) > 1e-9:
        print(f"!! FEE_RATE_FALLBACK={FEE_RATE_FALLBACK} but modal live rate is {modal} "
              f"— update the fallback and re-check the scripts that rely on it.")
        sys.exit(1)
    print(f"OK: FEE_RATE_FALLBACK={FEE_RATE_FALLBACK} matches the modal live rate.")
