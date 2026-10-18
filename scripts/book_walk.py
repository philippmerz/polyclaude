#!/usr/bin/env python3
"""Indicative position proceeds at supplied bid depth with conservative fees.

WHY THIS EXISTS (2026-08-14). "Realizable value" was computed in four places
with three different answers:

  * positions.py  — walked the book, NO fee subtracted
  * bankroll.py   — same walk, same omission
  * check_marginal_apy._exit_net — walk + per-market fee (correct)
  * exit_analysis — walk + per-market fee (correct)

The two that skipped fees produce the headline number. Measured on the live
book that night: gross walk $145.12 vs net $140.55 — a $4.57 gap, 3.9pp of
reported return, on the figure quoted to the operator in the weekly P&L.

That is the THIRD instance of one failure: a single number standing in for an
executable path. First the MIDPOINT stood in for a tradeable price; then
BEST-BID stood in for depth (fixed by walking the book); now the depth-walk
itself stood in for proceeds by ignoring the fee that gets deducted on the way
out. Each fix was real and each left the next layer of the same error intact.
The pattern to notice: every one of them flattered the number.

Pure functions — no network, no wallet, no clock — so tests/test_money_math.py
can assert on them directly. That is deliberate: the previous versions were
untestable because the walk was welded to an httpx call inside a display loop,
which is how two of them silently drifted from the two that were right.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from decimal import Decimal, ROUND_CEILING

from pm_fees import fee_per_share, fee_per_share_at

_FEE_QUOTE_QUANTUM = Decimal("0.00001")
_FEE_FLOAT_GUARD = 1e-12


def _ceil_fee_quote(value: float) -> float:
    """Round a nonnegative quote fee up to the observed five-decimal precision."""
    if value == 0:
        return 0.0
    # Values are accumulated in binary floats. Nudge only sub-picodollar
    # representation noise below a decimal boundary before strict ceiling.
    adjusted = max(0.0, value - _FEE_FLOAT_GUARD)
    return float(Decimal(str(adjusted)).quantize(
        _FEE_QUOTE_QUANTUM, rounding=ROUND_CEILING
    ))


def _finite_nonnegative(value: object, name: str) -> float:
    """Reject unknown/non-numeric quantities, including bool's numeric alias."""
    if isinstance(value, bool):
        raise ValueError(f"invalid {name}: expected a finite nonnegative number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"invalid {name}: expected a finite nonnegative number") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"invalid {name}: expected a finite nonnegative number")
    return number


def _bid_fills(bids: list[dict], size: float) -> Iterator[tuple[float, float]]:
    """Yield hypothetical (shares, price) fills from a fully validated bid side.

    Bad depth must not become a real-valued exit estimate. Validate even levels
    below the requested fill before yielding; otherwise changing the requested
    size can make the same malformed payload appear safe. This pure arithmetic
    check does not verify market identity, timestamps, or execution availability.
    A zero requested size is a no-op and does not inspect the unused bid side.
    """
    left = _finite_nonnegative(size, "requested size")
    if left == 0:
        return
    if not isinstance(bids, list):
        raise ValueError("invalid bid side: expected a list")
    levels = []
    for lvl in bids:
        if not isinstance(lvl, dict) or "price" not in lvl or "size" not in lvl:
            raise ValueError("invalid bid level: price and size are required")
        price = _finite_nonnegative(lvl["price"], "bid price")
        quantity = _finite_nonnegative(lvl["size"], "bid size")
        if price > 1:
            raise ValueError("invalid bid price: binary price exceeds 1")
        levels.append((price, quantity))
    for price, quantity in sorted(levels, key=lambda level: -level[0]):
        if left <= 0:
            break
        if quantity == 0:
            continue
        take = min(left, quantity)
        yield take, price
        left -= take


def walk_bids(bids: list[dict], size: float) -> tuple[float, float, float]:
    """Walk the bid book selling `size` shares. Returns (proceeds, avg_fill, unfilled).

    Levels are sorted here rather than assumed sorted — a caller passing an
    API's raw order is otherwise silently mispriced, and the CLOB does not
    guarantee ordering.

    UNFILLED REMAINDER IS NOT PRICED. If the book cannot absorb the whole
    position, the leftover contributes $0 to proceeds and is reported
    separately. Pricing it at the last touched level would assume depth that
    demonstrably is not there — which is the exact assumption best-bid pricing
    made and that walking the book exists to kill. `avg_fill` is proceeds over
    the FULL requested size, so a half-filled walk shows a visibly poor average
    rather than a flattering one computed over just the filled part.
    """
    size = _finite_nonnegative(size, "requested size")
    if size == 0:
        return 0.0, 0.0, 0.0
    left, proceeds = float(size), 0.0
    for take, price in _bid_fills(bids, size):
        proceeds += take * price
        left -= take
    return proceeds, proceeds / float(size), max(0.0, left)


def conservative_sell_fee(
    gross: float, filled: float, level_fee: float, market: dict | None
) -> float:
    """Conservative quote across observed per-level and aggregate-fee models.

    A confirmed multi-price SELL receipt reconciled more closely to the fee
    curve applied at the execution's aggregate price (gross / actually filled)
    than to a sum charged independently at each maker price. The grouping rule
    is not established universally, so quote at least the existing level-wise
    amount and take the greater of the two, rounded upward at observed
    five-decimal fee precision. Do not divide by requested shares: unfilled
    depth incurs no fee and would bias the executed average down.
    """
    gross = _finite_nonnegative(gross, "gross proceeds")
    filled = _finite_nonnegative(filled, "filled shares")
    level_fee = _finite_nonnegative(level_fee, "level fee")
    if filled == 0:
        if gross != 0 or level_fee != 0:
            raise ValueError("zero filled shares cannot have proceeds or fees")
        return 0.0
    if gross > filled:
        raise ValueError("gross proceeds exceed binary share payout")
    aggregate_price = gross / filled
    aggregate_fee = filled * fee_per_share(market, aggregate_price)
    if not math.isfinite(aggregate_fee) or aggregate_fee < 0:
        raise ValueError("invalid aggregate sell fee")
    return _ceil_fee_quote(max(level_fee, aggregate_fee))


def maker_rest_price(best_bid: float, best_ask: float | None, tick: float) -> float:
    """Return the best valid passive maker BUY price on both venue grids.

    CLOB prices must respect the market tick and the signed USD amount's
    two-decimal precision. Their common grid is the integer LCM of those two
    increments. Use ``Decimal(str(...))`` so a decimal boundary such as
    ``.009 + .001 == .01`` is not turned into a false strict inequality by
    binary floating-point arithmetic.

    Prefer one tick above the best bid when that common-grid price is strictly
    below the ask. If that cannot fit, use the highest positive common-grid
    price strictly below the ask. With no ask, use the first common-grid price
    at/above bid+tick, capped below the binary payout of $1. Raise when no
    positive valid passive price exists; callers must fail closed before
    reserving or signing an order.
    """

    def decimal_value(value: object, name: str, *, optional: bool = False) -> Decimal | None:
        if optional and value is None:
            return None
        if isinstance(value, bool):
            raise ValueError(f"invalid {name}: expected a finite decimal")
        try:
            number = Decimal(str(value))
        except Exception as exc:
            raise ValueError(f"invalid {name}: expected a finite decimal") from exc
        if not number.is_finite():
            raise ValueError(f"invalid {name}: expected a finite decimal")
        return number

    bid_d = decimal_value(best_bid, "best bid")
    ask_d = decimal_value(best_ask, "best ask", optional=True)
    tick_d = decimal_value(tick, "tick")
    assert bid_d is not None and tick_d is not None
    if not Decimal("0") <= bid_d < Decimal("1"):
        raise ValueError("invalid best bid: must be in [0, 1)")
    if ask_d is not None and not Decimal("0") < ask_d <= Decimal("1"):
        raise ValueError("invalid best ask: must be in (0, 1]")
    if not Decimal("0") < tick_d <= Decimal("1"):
        raise ValueError("invalid tick: must be in (0, 1]")

    # Scale all finite decimals to exact integer units. At least two decimal
    # places are required for the cash grid; additional places come from the
    # observed tick and book prices.
    decimals = [bid_d, tick_d] + ([] if ask_d is None else [ask_d])
    places = max(2, *(max(0, -value.as_tuple().exponent) for value in decimals))
    scale = 10 ** places

    def units(value: Decimal) -> int:
        sign, digits, exponent = value.as_tuple()
        coefficient = int("".join(map(str, digits)) or "0")
        shift = exponent + places
        if shift < 0:  # guarded by `places`, retained as a fail-closed invariant
            raise ValueError("price precision exceeds the common decimal scale")
        return (-coefficient if sign else coefficient) * (10 ** shift)

    bid_units = units(bid_d)
    tick_units = units(tick_d)
    ask_units = None if ask_d is None else units(ask_d)
    cent_units = scale // 100
    if tick_units <= 0 or cent_units <= 0:
        raise ValueError("invalid tick: no representable positive price grid")
    if bid_units % tick_units:
        raise ValueError("invalid best bid: price is not aligned to the market tick")
    if ask_units is not None and ask_units % tick_units:
        raise ValueError("invalid best ask: price is not aligned to the market tick")

    # A common-grid price is simultaneously a multiple of the venue tick and
    # one cent. All quantities are integers at the exact decimal scale above.
    grid_units = math.lcm(tick_units, cent_units)

    def ceil_grid(value_units: int) -> int:
        return ((value_units + grid_units - 1) // grid_units) * grid_units

    desired_units = bid_units + tick_units
    candidate_units = ceil_grid(desired_units)
    if ask_units is None:
        if candidate_units < scale:
            rest_units = candidate_units
        else:
            # The common grid may place bid+tick exactly at $1. A valid binary
            # maker price must remain below $1, so use the highest grid point
            # below the payout boundary instead.
            rest_units = ((scale - 1) // grid_units) * grid_units
    else:
        max_passive_units = ((ask_units - 1) // grid_units) * grid_units
        if candidate_units <= max_passive_units:
            rest_units = candidate_units
        else:
            # This also preserves bb when bb+tick equals ask, while staying
            # strictly passive when the ask is between tick/cent grid points.
            rest_units = max_passive_units

    if rest_units <= 0:
        raise ValueError("no positive price on both grids is strictly below the ask/payout")
    if rest_units >= scale:
        raise ValueError("no valid binary maker price below $1")
    if rest_units % tick_units or rest_units % cent_units:
        raise ValueError("internal error: maker price is not on both venue grids")
    if ask_units is not None and rest_units >= ask_units:
        raise ValueError("no valid maker price strictly below the best ask")
    return float(Decimal(rest_units) / Decimal(scale))


def effective_entry_cost(mark: float, taker_bps: int, maker_px: float | None = None
                         ) -> tuple[float, float]:
    """Per-share (cost, fee) the entry gate and Kelly must judge.

    WHY (2026-08-18 gap, fixed 2026-08-21): --maker changed only the EXECUTION
    price, so the robust gate judged maker entries on ask + taker fee —
    economics a post-only order never pays — and spuriously SKIPped MacBook at
    an effective 0.55 when the intended rest at 0.45 cleared by +10pp. The gate
    question for a maker entry is "IF this bid fills at the posted price, is it
    +EV"; whether it fills is governed by the resting-order rules, not here.

    Taker: mark (the live ask) + the TRUE quadratic fee (pm_fees, wallet-
    verified 2026-08-22). Maker: the posted rest price, fee $0.
    """
    if maker_px is not None:
        return maker_px, 0.0
    fee = fee_per_share_at(taker_bps / 10000.0, mark) if taker_bps > 0 else 0.0
    return mark + fee, fee


def realizable(bids: list[dict], size: float, market: dict | None) -> dict:
    """Indicative proceeds at supplied depth, after the market's own taker fee.

    Returns gross / fee / net / avg_fill / unfilled. `market` is the gamma dict
    (feeSchedule, with legacy takerBaseFee fallback); pass None only when it
    genuinely could not be fetched, which charges the conservative fallback
    rate rather than assuming free.

    The per-level fee sum remains a conservative floor. A confirmed multi-price
    SELL reconciled to the fee curve evaluated at aggregate executed price;
    because universal fee grouping is unproven, use the greater estimate.
    Unfilled shares have neither proceeds nor fees.
    """
    size = _finite_nonnegative(size, "requested size")
    gross, level_fee = 0.0, 0.0
    left = size
    for take, price in _bid_fills(bids, size):
        gross += take * price
        level_fee += take * fee_per_share(market, price)
        left -= take
    filled = size - max(0.0, left)
    fee = conservative_sell_fee(gross, filled, level_fee, market)
    avg_fill = gross / float(size) if size > 0 else 0.0
    unfilled = max(0.0, left)
    return {
        "gross": gross,
        "fee": fee,
        "net": gross - fee,
        "avg_fill": avg_fill,
        "unfilled": unfilled,
    }
