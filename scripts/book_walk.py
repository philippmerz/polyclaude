#!/usr/bin/env python3
"""What a position is actually worth if you sell it right now.

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

from pm_fees import fee_per_share


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
    if size <= 0:
        return 0.0, 0.0, 0.0
    levels = sorted(bids or [], key=lambda x: -float(x["price"]))
    left, proceeds = float(size), 0.0
    for lvl in levels:
        if left <= 0:
            break
        take = min(left, float(lvl["size"]))
        proceeds += take * float(lvl["price"])
        left -= take
    return proceeds, proceeds / float(size), max(0.0, left)


def realizable(bids: list[dict], size: float, market: dict | None) -> dict:
    """Net proceeds of exiting `size` NOW, after the market's own taker fee.

    Returns gross / fee / net / avg_fill / unfilled. `market` is the gamma dict
    (for takerBaseFee); pass None only when it genuinely could not be fetched,
    which charges the conservative fallback rate rather than assuming free.
    """
    gross, avg_fill, unfilled = walk_bids(bids, size)
    fee = fee_per_share(market, avg_fill) * float(size) if gross > 0 else 0.0
    return {
        "gross": gross,
        "fee": fee,
        "net": gross - fee,
        "avg_fill": avg_fill,
        "unfilled": unfilled,
    }
