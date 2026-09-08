#!/usr/bin/env python3
"""Indicative position proceeds at supplied bid depth, including per-fill fees.

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

from pm_fees import fee_per_share, fee_per_share_at


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


def maker_rest_price(best_bid: float, best_ask: float | None, tick: float) -> float:
    """Where a passive maker BUY actually rests: best_bid+tick, capped one tick
    under the ask, floored to the 2-dec amount grid (CLOB maker-USD precision —
    flooring keeps the bid passive; ceiling could cross and turn it taker).
    """
    px = best_bid + tick if (best_ask is None or best_bid + tick < best_ask) else best_bid
    return round(math.floor(round(px * 100, 6)) / 100, 2)


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

    Curved fees must be charged at each actual fill price. Charging the curve
    at avg_fill is not equivalent, and partial-depth averages also include
    unsold shares. Those unsold shares have neither proceeds nor fees here.
    """
    size = _finite_nonnegative(size, "requested size")
    gross, fee = 0.0, 0.0
    left = size
    for take, price in _bid_fills(bids, size):
        gross += take * price
        fee += take * fee_per_share(market, price)
        left -= take
    avg_fill = gross / float(size) if size > 0 else 0.0
    unfilled = max(0.0, left)
    return {
        "gross": gross,
        "fee": fee,
        "net": gross - fee,
        "avg_fill": avg_fill,
        "unfilled": unfilled,
    }
