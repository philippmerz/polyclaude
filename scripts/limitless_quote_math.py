"""Pure, conservative Limitless/Polymarket complementary-book math.

This module deliberately has no network, SDK, credentials, order, or metadata
logic.  Callers must validate market identity, resolution equivalence, fresh
books, minimums, ticks, and venue rules before calling it.

Limitless order-book sizes are raw integer micro-contracts.  The supplied
Limitless YES book is used for YES asks directly, or mirrored YES bids are
turned into NO asks at ``1 - price``.  Limitless' fee is modeled only as a
deduction from received contracts, bounded by ``lim_fee_bound``; it is never
added to USDC cash cost.  PM fees are charged per share, at every PM fill
level, through :func:`pm_fees.fee_per_share`.

All numeric outputs are :class:`decimal.Decimal`.  The quote is a screening
calculation conditional on the stated fee bound and whatever rounding the
maker applies.  It must not be described as executable, locked, or guaranteed.
Only gross Limitless fills are floored to the feed's 1e-6 contract unit; no
common PM precision or minimum is inferred here.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
import re
from typing import Any, Mapping, Sequence

try:  # Package import (``from scripts...``).
    from .pm_fees import fee_per_share
except ImportError:  # Direct import when scripts is placed on sys.path.
    from pm_fees import fee_per_share  # type: ignore


_MICRO = Decimal("1000000")
_MICRO_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0")
_ONE = Decimal("1")
_INTEGER = re.compile(r"^[0-9]+$")


@dataclass(frozen=True)
class BookLevel:
    """A normalized ask level, sorted by increasing price."""

    price: Decimal
    size: Decimal
    source_index: int


def _decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be finite numeric")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{name} must be finite numeric") from None
    if not parsed.is_finite():
        raise ValueError(f"{name} must be finite numeric")
    return parsed


def _price(value: Any, name: str = "price") -> Decimal:
    p = _decimal(value, name)
    if not _ZERO < p < _ONE:
        raise ValueError(f"{name} must be strictly between 0 and 1")
    return p


def _raw_micro_size(value: Any, name: str) -> Decimal:
    """Parse raw Limitless integer micro-contract size exactly."""
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a nonnegative integer micro-size")
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{name} must be nonnegative")
        return Decimal(value) / _MICRO
    if isinstance(value, str) and _INTEGER.fullmatch(value.strip()):
        return Decimal(value.strip()) / _MICRO
    raise ValueError(f"{name} must be a nonnegative integer micro-size")


def _share_size(value: Any, name: str) -> Decimal:
    size = _decimal(value, name)
    if size < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return size


def _floor_limitless_contracts(value: Decimal) -> Decimal:
    """Floor a gross Limitless quantity to the feed's 1e-6 contract unit."""
    return value.quantize(_MICRO_QUANTUM, rounding=ROUND_FLOOR)


def _book_levels(book: Mapping[str, Any], side: str, *, limitless: bool) -> list[BookLevel]:
    if not isinstance(book, Mapping):
        raise ValueError("book must be a mapping")
    raw_levels = book.get(side)
    if not isinstance(raw_levels, Sequence) or isinstance(raw_levels, (str, bytes)):
        raise ValueError(f"book.{side} must be a sequence")
    out: list[BookLevel] = []
    for i, level in enumerate(raw_levels):
        if not isinstance(level, Mapping):
            raise ValueError(f"book.{side}[{i}] must be a mapping")
        if "price" not in level or "size" not in level:
            raise ValueError(f"book.{side}[{i}] needs price and size")
        price = _price(level["price"], f"book.{side}[{i}].price")
        size = (
            _raw_micro_size(level["size"], f"book.{side}[{i}].size")
            if limitless
            else _share_size(level["size"], f"book.{side}[{i}].size")
        )
        if size > _ZERO:
            out.append(BookLevel(price, size, i))
    out.sort(key=lambda x: x.price)
    return out


def normalize_limitless_book(
    book: Mapping[str, Any], yes_token: str, outcome: str
) -> tuple[BookLevel, ...]:
    """Normalize the requested Limitless outcome's asks.

    ``book`` must be the YES-side book and must contain ``tokenId`` equal to
    ``yes_token``.  For NO, YES bids are mirrored to asks at ``1 - p``.  Raw
    sizes are integer micro-contracts and become contract quantities by exact
    division by 1e6.
    """
    if not isinstance(yes_token, str) or not yes_token:
        raise ValueError("yes_token must be a nonempty string")
    if not isinstance(book, Mapping) or book.get("tokenId") != yes_token:
        raise ValueError("Limitless book tokenId does not match supplied YES token")
    side = str(outcome).upper() if isinstance(outcome, str) else ""
    if side not in {"YES", "NO"}:
        raise ValueError("lim_outcome must be YES or NO")
    if side == "YES":
        return tuple(_book_levels(book, "asks", limitless=True))

    mirrored: list[BookLevel] = []
    for level in _book_levels(book, "bids", limitless=True):
        mirrored.append(BookLevel(_ONE - level.price, level.size, level.source_index))
    mirrored.sort(key=lambda x: x.price)
    return tuple(mirrored)


def normalize_pm_book(book: Mapping[str, Any]) -> tuple[BookLevel, ...]:
    """Normalize a PM ask book whose sizes are already shares."""
    return tuple(_book_levels(book, "asks", limitless=False))


def _walk_limitless(
    levels: Sequence[BookLevel], target_net: Decimal, fee_bound: Decimal
) -> tuple[Decimal, Decimal, tuple[dict[str, Decimal], ...]]:
    gross_target = _floor_limitless_contracts(target_net / (_ONE - fee_bound))
    remaining = gross_target
    gross = cost = _ZERO
    fills: list[dict[str, Decimal]] = []
    for level in levels:
        if remaining <= _ZERO:
            break
        take = min(level.size, _floor_limitless_contracts(remaining))
        gross += take
        cost += take * level.price
        fills.append({"price": level.price, "gross_contracts": take})
        remaining -= take
    if remaining > Decimal("1e-24"):
        raise ValueError("insufficient Limitless depth for requested match")
    return gross, cost, tuple(fills)


def _pm_fee(market: Mapping[str, Any], price: Decimal) -> Decimal:
    try:
        value = fee_per_share(dict(market), float(price))
    except Exception as exc:
        raise ValueError(f"invalid PM fee market: {exc}") from None
    # pm_fees is intentionally the source of the curve but returns a float.
    # Strip binary-representation noise without inventing venue precision.
    fee = _decimal(format(value, ".15g"), "PM fee per share")
    if fee < _ZERO:
        raise ValueError("PM fee per share must be nonnegative")
    return fee


def _walk_pm(
    levels: Sequence[BookLevel], target: Decimal, market: Mapping[str, Any]
) -> tuple[Decimal, Decimal, tuple[dict[str, Decimal], ...]]:
    remaining = target
    shares = cost = fees = _ZERO
    fills: list[dict[str, Decimal]] = []
    for level in levels:
        if remaining <= _ZERO:
            break
        take = min(level.size, remaining)
        fee_share = _pm_fee(market, level.price)
        notional = take * level.price
        fee = take * fee_share
        shares += take
        cost += notional + fee
        fees += fee
        fills.append({
            "price": level.price,
            "shares": take,
            "notional_usdc": notional,
            "fee_per_share_usdc": fee_share,
            "fee_usdc": fee,
        })
        remaining -= take
    if remaining > Decimal("1e-24"):
        raise ValueError("insufficient PM depth for requested match")
    return shares, cost, tuple(fills)


def _limitless_capacity(
    levels: Sequence[BookLevel], cap: Decimal, fee_bound: Decimal
) -> tuple[Decimal, Decimal, Decimal]:
    remaining_cash = cap
    gross = cost = _ZERO
    for level in levels:
        if remaining_cash <= _ZERO:
            break
        take = min(level.size, _floor_limitless_contracts(remaining_cash / level.price))
        gross += take
        cost += take * level.price
        remaining_cash -= take * level.price
    return gross * (_ONE - fee_bound), gross, cost


def _pm_capacity(
    levels: Sequence[BookLevel], cap: Decimal, market: Mapping[str, Any]
) -> tuple[Decimal, Decimal, Decimal]:
    remaining_cash = cap
    shares = cost = fees = _ZERO
    for level in levels:
        if remaining_cash <= _ZERO:
            break
        fee_share = _pm_fee(market, level.price)
        all_in = level.price + fee_share
        take = min(level.size, remaining_cash / all_in)
        shares += take
        fee = take * fee_share
        cost += take * all_in
        fees += fee
        remaining_cash -= take * all_in
    return shares, cost, fees


def quote_pair(
    lim_book: Mapping[str, Any],
    lim_yes_token: str,
    lim_outcome: str,
    pm_book: Mapping[str, Any],
    pm_market: Mapping[str, Any],
    cap_usdc: Any,
    lim_fee_bound: Any = Decimal("0.03"),
) -> dict[str, Any]:
    """Return a conservative, non-executable complementary-book quote.

    The same lower-bound net quantity is bought on both legs.  Quantity is
    maximized subject to displayed depth and each leg's cash outlay being at
    most ``cap_usdc``.  Partial depth is reported as ``unfilled``; empty or
    zero-capacity books raise ``ValueError``.
    """
    cap = _decimal(cap_usdc, "cap_usdc")
    bound = _decimal(lim_fee_bound, "lim_fee_bound")
    if cap <= _ZERO:
        raise ValueError("cap_usdc must be positive")
    if not _ZERO <= bound < _ONE:
        raise ValueError("lim_fee_bound must be in [0, 1)")
    if not isinstance(pm_market, Mapping):
        raise ValueError("pm_market must be a mapping")

    lim = normalize_limitless_book(lim_book, lim_yes_token, lim_outcome)
    pm = normalize_pm_book(pm_book)
    if not lim or not pm:
        raise ValueError("insufficient displayed depth")

    lim_depth_net = sum((x.size for x in lim), _ZERO) * (_ONE - bound)
    lim_budget_net, _, _ = _limitless_capacity(lim, cap, bound)
    pm_depth = sum((x.size for x in pm), _ZERO)
    pm_budget, _, _ = _pm_capacity(pm, cap, pm_market)
    capacity_match = min(lim_depth_net, lim_budget_net, pm_depth, pm_budget)
    matched = capacity_match
    if matched <= _ZERO:
        raise ValueError("insufficient depth or budget for positive match")

    # A PM-capacity match may not map exactly to a Limitless micro-contract
    # quantity. Reduce the common match to the actual lower net quantity. Do
    # not rewalk Limitless: doing so can floor a second time at a level
    # boundary and lose another micro-contract.
    lim_gross, lim_cost, lim_fills = _walk_limitless(lim, matched, bound)
    lim_net_lower = lim_gross * (_ONE - bound)
    if lim_net_lower < matched:
        matched = lim_net_lower
    pm_shares, pm_cost, pm_fills = _walk_pm(pm, matched, pm_market)
    # Re-walks should agree exactly; retain this guard against future changes
    # to a fee helper or level representation.
    if pm_shares != matched:
        raise ValueError("PM re-walk did not produce the matched quantity")
    lim_net_lower = lim_gross * (_ONE - bound)
    if lim_net_lower < matched:
        raise ValueError("Limitless lower-bound net quantity underfilled")

    fee_bound_contracts = lim_gross * bound
    lim_unfilled_net = max(_ZERO, lim_depth_net - matched)
    pm_unfilled = max(_ZERO, pm_depth - matched)
    lim_actual_fee_upside_max = fee_bound_contracts
    total_cash = lim_cost + pm_cost
    floor = min(lim_net_lower, pm_shares)
    caps: list[str] = []
    # A budget is binding only when it cuts below displayed depth and is the
    # minimum capacity. Equality with depth is depth-limited, not budget-
    # limited.
    if lim_budget_net < lim_depth_net and lim_budget_net <= capacity_match:
        caps.append("limitless")
    if pm_budget < pm_depth and pm_budget <= capacity_match:
        caps.append("pm")
    lim_result = {
        "gross_contracts": lim_gross,
        "net_contracts_lower": lim_net_lower,
        "cost_usdc": lim_cost,
        "fee_bound": bound,
        "fee_bound_contracts": fee_bound_contracts,
        "unmatched_fee_upside_max_contracts": lim_actual_fee_upside_max,
        "unfilled_net_contracts_lower": lim_unfilled_net,
        "fills": lim_fills,
    }
    pm_result = {
        "shares": pm_shares,
        "cost_usdc": pm_cost,
        "fee_usdc": sum((x["fee_usdc"] for x in pm_fills), _ZERO),
        "unfilled_shares": pm_unfilled,
        "fills": pm_fills,
    }
    result = {
        "status": "screening_quote_only",
        "matched_net_shares": matched,
        "limitless": lim_result,
        # Short aliases match the vocabulary used by the existing inspector.
        "lim": lim_result,
        "pm": pm_result,
        "total_cash_usdc": total_cash,
        "conditional_payout_floor_usdc": floor,
        "conditional_profit_floor_usdc": floor - total_cash,
        "budget_limit": bool(caps),
        "budget_limited": bool(caps),
        "budget_limited_legs": tuple(caps),
        "unfilled": bool(lim_unfilled_net > _ZERO or pm_unfilled > _ZERO),
        "fee_bound_conditional": True,
        "disclaimer": (
            "Screening math only; conditional on Limitless fee <= bound and fee "
            "rounding. Not executable, locked, or guaranteed."
        ),
    }
    return result
