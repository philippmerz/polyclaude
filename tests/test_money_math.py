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

import atexit
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import discover_markets as dm  # noqa: E402
import event_monotonicity_scan as ems  # noqa: E402
import pm_fees  # noqa: E402

FAILS: list[str] = []


def _report() -> None:
    """Registered with atexit so it ALWAYS runs after every check, wherever the
    check was appended. 2026-08-20: the pass/fail block used to sit inline, and
    twice I appended a new section BELOW it with `cat >>` — the checks executed,
    appended to FAILS, and nothing ever looked at FAILS again. Both times the
    suite printed OK while containing dead assertions, including the regression
    guard for a 2x error in the operator's headline metric. A test file whose
    verdict is positional is one append away from lying."""
    if FAILS:
        print(f"FAIL ({len(FAILS)}):", flush=True)
        for f in FAILS:
            print("  -", f, flush=True)
        sys.stdout.flush()
        os._exit(1)      # _exit skips flushing, hence the explicit flushes above
    print(f"OK — money-math regression suite passed ({CHECKS[0]} checks)", flush=True)


atexit.register(_report)


CHECKS = [0]


def check(label: str, got, want, tol: float = 1e-9) -> None:
    CHECKS[0] += 1
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



# ------------------------------------------------- realized/unrealized split
# 2026-08-20: the inline version booked the operator's GAS DEPOSIT as trading
# profit for two days — +$10.77 reported vs +$5.32 true, 2x, on the one number
# the operator said they would judge on. The arithmetic was never wrong; an
# INPUT was. These pin the gas case so it cannot silently return on a refactor.
import bankroll  # noqa: E402

# The live numbers from the day the bug was found.
s = bankroll.realized_split(total=193.06, ref=170.0, gas_usd=5.44,
                            pm_mid=134.52, pm_cost=122.23, pm_realizable=124.46)
check("realized excludes gas", s["realized"], 5.33, tol=0.02)
check("unrealized marked", s["unrealized_marked"], 12.29, tol=0.01)
check("unrealized realizable", s["unrealized_realizable"], 2.23, tol=0.01)
check("gas reported separately", s["gas_excluded"], 5.44)
# THE REGRESSION GUARD — a SENSITIVITY test, not a value test. The first draft
# of this called realized_split with gas_usd=0.0 and compared to the true figure,
# which can never fire: a function that IGNORES gas returns the same thing whether
# you pass 0 or 5.44, so the check passes under both the correct and the broken
# implementation. Caught by simulating the bug and watching the guard stay silent.
# The real test is that varying gas MOVES the answer by exactly that amount.
_g0 = bankroll.realized_split(193.06, 170.0, 0.0, 134.52, 122.23)["realized"]
_g5 = bankroll.realized_split(193.06, 170.0, 5.44, 134.52, 122.23)["realized"]
check("realized is sensitive to gas (2026-08-20 regression)", _g0 - _g5, 5.44, tol=1e-9)

# Invariance: realized must NOT move when only marks move (nothing settled).
a = bankroll.realized_split(190.0, 170.0, 5.0, 130.0, 122.0)["realized"]
b = bankroll.realized_split(195.0, 170.0, 5.0, 135.0, 122.0)["realized"]
check("realized invariant to pure mark moves", a, b, tol=1e-9)
# ...but DOES move when settled cash moves with marks held constant.
cash_up = bankroll.realized_split(195.0, 170.0, 5.0, 130.0, 122.0)["realized"]
check("realized moves on settlement", cash_up - a, 5.0, tol=1e-9)
# Gas APPRECIATION lifts total and gas by the SAME amount, so realized is
# unchanged. (First draft bumped total by 6 while gas rose 1 — not gas drift at
# all, but a $5 settlement with extra gas. It was stranded below the verdict and
# so never ran; the atexit restructure surfaced it immediately.)
check("gas drift does not move realized",
      bankroll.realized_split(191.0, 170.0, 6.0, 130.0, 122.0)["realized"], a, tol=1e-9)

# --------------------------------------------- discriminating cases (mutation-driven)
# Added 2026-08-20 after mutation testing showed the suite could NOT detect two
# real bugs. Each of these exists to kill a specific surviving mutant.
# MUTANT 1: `return float(bps)/10000.0` -> `return 0.10`. Every prior numeric case
# used bps=1000, which IS 0.10, so hardcoding the modal rate passed. A second,
# different rate is what discriminates.
check("rate 500bps (kills hardcoded-0.10 mutant)", pm_fees.fee_rate({"takerBaseFee": 500}), 0.05)
check("rate 250bps", pm_fees.fee_rate({"takerBaseFee": 250}), 0.025)
# MUTANT 2: `sorted(bids, ...)` -> `bids`. The prior unsorted test consumed BOTH
# levels, and a full sweep totals the same in any order. Order only matters on a
# PARTIAL fill, where the walk must take the best price first.
_unsorted = [{"price": "0.50", "size": "10"}, {"price": "0.60", "size": "10"}]
check("partial fill takes BEST price first (kills unsorted mutant)",
      book_walk.walk_bids(_unsorted, 10)[0], 6.0)
check("partial fill avg is the best level", book_walk.walk_bids(_unsorted, 10)[1], 0.60)

# --------------------------------------------- maker gate economics (2026-08-21)
# The --maker gap: the robust gate judged maker entries on ask + taker fee,
# economics a post-only order never pays. These pin the fix: the gate must see
# the POSTED rest price with zero fee, and the rest price must stay passive.

# maker_rest_price: bb+tick when room exists under the ask
check("rest = bb+tick under the ask", book_walk.maker_rest_price(0.44, 0.50, 0.01), 0.45)
# bb+tick would EQUAL the ask -> not strictly under -> stay at bb
check("bb+tick == ask stays at bb", book_walk.maker_rest_price(0.44, 0.45, 0.01), 0.44)
# empty ask side -> bb+tick unconstrained
check("no ask -> bb+tick", book_walk.maker_rest_price(0.44, None, 0.01), 0.45)
# fine-tick market: 0.441+0.001=0.442 must FLOOR to the 2-dec grid (0.44), never
# ceil (0.45 could cross a 0.445 ask and turn the order taker)
check("fine tick floors to 2-dec grid", book_walk.maker_rest_price(0.441, 0.445, 0.001), 0.44)

# effective_entry_cost: the MacBook 2026-08-18 numbers. Ask 0.50 on a 1000bps
# market = 0.55 effective taker; the intended rest at 0.45 pays no fee.
_tc, _tf = book_walk.effective_entry_cost(0.50, 1000)
check("taker cost = ask + fee", _tc, 0.55)
check("taker fee at p=0.50", _tf, 0.05)
_mc, _mf = book_walk.effective_entry_cost(0.50, 1000, maker_px=0.45)
check("maker cost = posted price", _mc, 0.45)
check("maker fee is zero even on 1000bps market", _mf, 0.0)
# The regression itself: at p_robust=0.55 the taker cost shows ZERO edge (the
# spurious SKIP) while the maker cost clears by 10pp — the trade that was lost.
check("taker economics showed no edge", 0.55 - _tc, 0.0)
check("maker economics cleared by 10pp", 0.55 - _mc, 0.10)
# zero-fee market: taker cost is just the ask (no phantom fallback fee)
check("zero-fee taker cost = ask", book_walk.effective_entry_cost(0.50, 0)[0], 0.50)
