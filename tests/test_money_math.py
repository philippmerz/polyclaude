#!/usr/bin/env python3
"""Regression tests for the arithmetic that decides what a trade costs.

WHY THIS EXISTS (2026-08-14). This repo had NO tests. In a single 24h window it
shipped and then caught three independent errors in cost/fee math:

  * the fee RATE hard-coded at 0.072 across seven scripts, when the live modal
    rate is 0.10 and 16% of markets charge nothing,
  * the fee applied MULTIPLICATIVELY (`p*(1+f)`) in the entry filter when the
    charge is dollars per share (`p+f`) — 3.2pp of understated cost at p=0.50,
  * an exit-cost gate charging a fee to a market whose takerBaseFee is None.

Every one understated cost, i.e. made trades look better than they are, and
every one was found by hand. The 21 adversarial parse_threshold cases written
after the six phantom-arb incident were run ad-hoc in a shell and never
persisted, so the exact bug that manufactured those arbs had no guard at all.

SCOPE: pure functions only — no network, no wallet, no clock. Fast enough to
run before every commit that touches pricing. Deliberately narrow: this is not
coverage for its own sake, it is a net under the specific arithmetic where a
silent wrong answer spends money.

Run:  .venv/bin/python tests/test_money_math.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import discover_markets as dm  # noqa: E402
import event_monotonicity_scan as ems  # noqa: E402
import pm_fees  # noqa: E402

FAILS: list[str] = []


def check(label: str, got, want, tol: float = 1e-9) -> None:
    ok = (abs(got - want) <= tol) if isinstance(want, (int, float)) and isinstance(got, (int, float)) else (got == want)
    if not ok:
        FAILS.append(f"{label}: got {got!r}, want {want!r}")


# ---------------------------------------------------------------- pm_fees
# The field is per-market and BOTH extremes are real: 84% of live markets carry
# 1000bps, 16% carry None. A None must mean zero, NOT "missing, use fallback" —
# conflating those is what charged Greenland a fee it does not have.
check("rate 1000bps", pm_fees.fee_rate({"takerBaseFee": 1000}), 0.10)
check("rate string bps", pm_fees.fee_rate({"takerBaseFee": "1000"}), 0.10)
check("rate None = genuinely zero", pm_fees.fee_rate({"takerBaseFee": None}), 0.0)
check("rate 'None' string", pm_fees.fee_rate({"takerBaseFee": "None"}), 0.0)
check("rate absent field", pm_fees.fee_rate({}), 0.0)
check("rate unfetchable market", pm_fees.fee_rate(None), pm_fees.FEE_RATE_FALLBACK)
check("rate garbage falls back", pm_fees.fee_rate({"takerBaseFee": "abc"}), pm_fees.FEE_RATE_FALLBACK)

# Edge-aware: rate x min(p, 1-p). Peaks at 0.50, vanishes at the extremes —
# this book is mostly long-tail NOs, where a rate-x-notional estimate is wildly
# wrong (0.945 pays on 0.055, not on 0.945).
m10 = {"takerBaseFee": 1000}
check("fee at 0.50", pm_fees.fee_per_share(m10, 0.50), 0.05)
check("fee at 0.945 pays on the short side", pm_fees.fee_per_share(m10, 0.945), 0.10 * 0.055)
check("fee symmetric", pm_fees.fee_per_share(m10, 0.30), pm_fees.fee_per_share(m10, 0.70))
check("zero-fee market costs nothing", pm_fees.fee_per_share({"takerBaseFee": None}, 0.50), 0.0)

# ------------------------------------------------- discover_markets cost math
# THE multiplicative-vs-additive regression. p*(1+f) returned 0.518 here; the
# true cost is 0.550. Anchored on exact numbers so the bug cannot creep back.
def cost_of(p, market):
    """Recover implied cost from the APY the filter computes."""
    apy = dm.annualized_yield_after_fee(p, 365.0, market)
    return 1.0 / (1.0 + apy)          # 365d => gross = (1-c)/c, so c = 1/(1+gross)


check("cost additive at p=0.50", cost_of(0.50, m10), 0.550, tol=1e-6)
check("cost additive at p=0.90", cost_of(0.90, m10), 0.910, tol=1e-6)
check("cost zero-fee market", cost_of(0.50, {"takerBaseFee": None}), 0.500, tol=1e-6)
# The old bug in explicit form: multiplicative would have given 0.5*1.05=0.525.
if abs(cost_of(0.50, m10) - 0.525) < 1e-6:
    FAILS.append("cost math regressed to MULTIPLICATIVE fee (p*(1+f))")
check("degenerate p>=0.999 rejected", dm.annualized_yield_after_fee(0.9995, 30, m10), None)
check("degenerate days<1 rejected", dm.annualized_yield_after_fee(0.5, 0.5, m10), None)

# ------------------------------------------- monotonicity arb breakeven
# Understating this LOWERS the bar a violation must clear, which manufactures
# arbs that lose money on execution. Legs can carry different rates.
check("breakeven both legs 10%", ems.fee_aware_breakeven(0.50, 0.50, 1000, 1000), 0.10)
check("breakeven both legs free", ems.fee_aware_breakeven(0.50, 0.50, None, None), 0.0)
check("breakeven mixed rates", ems.fee_aware_breakeven(0.50, 0.50, 1000, None), 0.05)
check("breakeven edge-aware at tails", ems.fee_aware_breakeven(0.95, 0.90, 1000, 1000),
      0.10 * 0.05 + 0.10 * 0.10)
# Unknown bps must NOT silently become free — that is the dangerous direction.
check("breakeven unknown bps uses fallback",
      ems.fee_aware_breakeven(0.50, 0.50), 2 * pm_fees.FEE_RATE_FALLBACK * 0.5)

# ------------------------------------------------- parse_threshold regression
# The six phantom "REAL ARB" fires: "$1B" parsed as 1.0 and "$50M" as 50.0,
# inverting a correctly-priced FDV ladder. The prices were real; the ORDERING
# was fabricated, and a live-CLOB walk cannot rescue a bad parse.
def val(q):
    r = ems.parse_threshold(q)
    return r[0] if r else None


check("$1B scales", val("Will FDV be above $1B?"), 1e9)
check("$50M scales", val("Will FDV be above $50M?"), 50e6)
check("ladder ordering preserved", val("Will FDV be above $1B?") > val("Will FDV be above $50M?"), True)
check("trailing-word form scales", val("Will revenue be $2 billion or higher?"), 2e9)
check("plain percent unscaled", val("Will the score be 50% or higher?"), 50.0)
# Must NOT grab the year from a question whose bar is stated separately.
check("year not mistaken for bar", val("Will the highest score on HLE in 2026 be 50% or higher?"), 50.0)
# Exact-value buckets are a PARTITION — no monotone constraint, must be rejected.
check("exact-value bucket rejected", ems.parse_threshold("Will the party win 3 seats?"), None)
check("no-comparator rejected", ems.parse_threshold("Will Apple release a laptop in 2026?"), None)
# Direction: "or higher" = harder bar as value rises.
check("direction up", ems.parse_threshold("Will it be 50 or higher?")[1], 1)
check("direction down", ems.parse_threshold("Will it be 50 or lower?")[1], -1)



# ------------------------------------------------------------- book_walk
# The depth-walk was duplicated four ways and two copies omitted the fee,
# overstating "realizable" by $4.57 (3.9pp of reported return) on the live book.
import book_walk  # noqa: E402

BIDS = [{"price": "0.60", "size": "10"}, {"price": "0.50", "size": "10"}]

g, avg, un = book_walk.walk_bids(BIDS, 10)
check("walk single level", g, 6.0)
check("walk single level avg", avg, 0.60)
check("walk no remainder", un, 0.0)

g, avg, un = book_walk.walk_bids(BIDS, 20)
check("walk two levels", g, 11.0)
check("walk blended avg", avg, 0.55)

# Partial fill: the unfilled remainder must NOT be priced at the last level,
# and avg_fill is over the FULL size so a thin book looks thin.
g, avg, un = book_walk.walk_bids(BIDS, 30)
check("walk partial gross", g, 11.0)
check("walk reports unfilled", un, 10.0)
check("walk avg over full size", avg, 11.0 / 30)

# Unsorted input must not be trusted as sorted.
g2, _, _ = book_walk.walk_bids(list(reversed(BIDS)), 20)
check("walk sorts input", g2, 11.0)
check("walk empty book", book_walk.walk_bids([], 10)[0], 0.0)
check("walk zero size", book_walk.walk_bids(BIDS, 0)[0], 0.0)

r = book_walk.realizable(BIDS, 20, {"takerBaseFee": 1000})
check("realizable gross", r["gross"], 11.0)
check("realizable fee edge-aware", r["fee"], 0.10 * min(0.55, 0.45) * 20)
check("realizable net", r["net"], 11.0 - 0.10 * 0.45 * 20)
check("realizable zero-fee market", book_walk.realizable(BIDS, 20, {"takerBaseFee": None})["net"], 11.0)
check("realizable unknown market uses fallback",
      book_walk.realizable(BIDS, 20, None)["fee"], pm_fees.FEE_RATE_FALLBACK * 0.45 * 20)
check("realizable empty book charges no fee", book_walk.realizable([], 20, {"takerBaseFee": 1000})["fee"], 0.0)


if FAILS:
    print(f"FAIL ({len(FAILS)}):")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print("OK — money-math regression suite passed")
