"""Public-read Limitless/Polymarket arb quote inspector.

Execution is permanently disabled.  The inspector validates exact market
identities, reads public books, and calls ``limitless_quote_math.quote_pair``
for both complementary directions.  Results are conditional screening only;
fees, rounding, minimums, freshness, and resolution equivalence are not an
executable guarantee.

The per-level Polymarket fee source remains ``pm_fees.py`` through the pure
quote helper; this wrapper does not estimate fees from an average fill.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import httpx

try:
    from .limitless_quote_math import quote_pair
except ImportError:
    from limitless_quote_math import quote_pair  # type: ignore


_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
SCAN_OUTPUT = _REPO_ROOT / "logs" / "limitless_arb_latest.json"
STATE_PATH = Path.home() / ".polyclaude_arb_state.json"
PER_ARB_CAP_USDC = 3.00
PER_ARB_FIRST_TRADE_CAP_USDC = 1.00
TOTAL_OPEN_ARB_CAP_USDC = 20.00
MIN_NET_EDGE = 0.015
LIMITLESS_API_BASE = "https://api.limitless.exchange"
POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"
POLYMARKET_CLOB = "https://clob.polymarket.com/book"
LIMITLESS_FEE_BOUND = 0.03
PM_BOOK_MAX_AGE_SECONDS = 120.0
SCAN_MAX_AGE_SECONDS = 2 * 60 * 60
BASE_NATIVE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
_DRY_RUN = False  # compatibility only; there is no alert/order path

_ASSUMPTIONS = (
    "Limitless buy fee is bounded at 3% from public documentation, not an exact pre-trade quote.",
    "Limitless fee asset/rounding and Polymarket execution rounding remain unverified.",
    "Displayed-book freshness, minimum-order rules, and resolution-rule equivalence remain unverified.",
    "Screening math only; execution_ready is always false and no order is submitted.",
)


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"open_arbs": [], "resolved_arbs": [], "last_run_at": 0,
                "first_trade_completed": False}
    try:
        value = json.loads(STATE_PATH.read_text())
        return value if isinstance(value, dict) else {}
    except Exception:
        return {"open_arbs": [], "resolved_arbs": [], "last_run_at": 0,
                "first_trade_completed": False}


def _read_scan() -> dict:
    if not SCAN_OUTPUT.exists():
        return {}
    try:
        value = json.loads(SCAN_OUTPUT.read_text())
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _select_candidate(scan: dict, state: dict) -> dict | None:
    identical = scan.get("verified_identical") or []
    open_ids = {str(a.get("lim_id")) for a in state.get("open_arbs", [])}
    eligible = [c for c in identical if isinstance(c, dict)
                and (c.get("net_edge") or 0) >= MIN_NET_EDGE
                and str(c.get("lim_id")) not in open_ids
                and c.get("lim_chainlink_enabled")]
    eligible.sort(key=lambda c: -(c.get("net_edge") or 0))
    return eligible[0] if eligible else None


def _open_capital_used(state: dict) -> float:
    return sum(float(a.get("capital_per_side") or 0) * 2
               for a in state.get("open_arbs", []))


def _unpriced(reason: str, **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "unpriced", "ok": False, "screening_only": True,
        "execution_ready": False, "reason": f"unpriced: {reason}",
        "assumptions": list(_ASSUMPTIONS),
    }
    result.update(extra)
    return result


def _json_get(url: str, *, params: Mapping[str, Any] | None = None,
              get: Callable[..., Any] | None = None) -> Any:
    request = get or httpx.get
    response = request(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _same_id(a: Any, b: Any) -> bool:
    return bool(_text(a)) and _text(a).casefold() == _text(b).casefold()


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _timestamp(value: Any) -> float | None:
    number = _number(value)
    if number is not None:
        return number / 1000.0 if number > 10_000_000_000 else number
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _expiry(market: Mapping[str, Any]) -> float | None:
    for key in ("expirationTimestamp", "expiration_timestamp", "expirationDate",
                "expiration_date", "endDate", "end_date"):
        if key in market and market[key] not in (None, ""):
            return _timestamp(market[key])
    return None


def _limitless_market_ok(market: Any, candidate: Mapping[str, Any], now: float) -> str | None:
    if not isinstance(market, Mapping):
        return "Limitless market response is not an object"
    if not _same_id(market.get("id"), candidate.get("lim_id")):
        return "Limitless response id does not match candidate lim_id"
    if not _same_id(market.get("slug"), candidate.get("lim_slug")):
        return "Limitless response slug does not match candidate lim_slug"
    status = _text(market.get("status")).casefold()
    if status not in {"created", "funded"}:
        return f"Limitless market is not active CLOB status CREATED/FUNDED ({status or 'missing'})"
    trade_type = _text(market.get("tradeType") or market.get("trade_type")).casefold()
    if trade_type != "clob":
        return "Limitless market is not CLOB"
    market_type = _text(market.get("marketType") or market.get("market_type")).casefold()
    child_values = [market.get(key) for key in
                    ("children", "markets", "subMarkets", "submarkets")]
    if any(value for value in child_values):
        return "Limitless group has children; an exact leaf is required"
    expiry = _expiry(market)
    if expiry is None:
        return "Limitless market has no verifiable expiry"
    if expiry <= now:
        return "Limitless market is expired"
    tokens = market.get("tokens")
    yes = tokens.get("yes") if isinstance(tokens, Mapping) else None
    no = tokens.get("no") if isinstance(tokens, Mapping) else None
    if not _same_id(yes, candidate.get("lim_yes_token")):
        return "Limitless YES token does not match candidate"
    if not _same_id(no, candidate.get("lim_no_token")):
        return "Limitless NO token does not match candidate"
    if not yes or not no or _same_id(yes, no):
        return "Limitless tokens are missing or not distinct"
    collateral = market.get("collateralToken")
    if isinstance(collateral, Mapping):
        address = collateral.get("address") or collateral.get("token")
        decimals = collateral.get("decimals")
    else:
        address = collateral
        decimals = market.get("collateralDecimals")
    if not _same_id(address, BASE_NATIVE_USDC):
        return "Limitless collateral is not Base native USDC"
    if _number(decimals) != 6:
        return "Limitless collateral decimals are not 6"
    return None


def _parse_list(value: Any) -> list[Any] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return None
    return list(value) if isinstance(value, (list, tuple)) else None


def _pm_market_tokens(market: Mapping[str, Any]) -> tuple[str, str] | None:
    outcomes = _parse_list(market.get("outcomes"))
    token_ids = _parse_list(market.get("clobTokenIds") or market.get("clob_token_ids"))
    if not outcomes or not token_ids or len(outcomes) != 2 or len(token_ids) != 2:
        return None
    found: dict[str, str] = {}
    for label, token in zip(outcomes, token_ids):
        key = _text(label).casefold()
        if key in {"yes", "no"} and _text(token):
            if key in found:
                return None
            found[key] = _text(token)
    yes, no = found.get("yes"), found.get("no")
    return (yes, no) if yes and no and not _same_id(yes, no) else None


def _pm_fee_metadata_ok(market: Mapping[str, Any]) -> str | None:
    """Require explicit fee evidence before presenting a priced quote."""
    if market.get("feesEnabled") is False:
        return None
    schedule = market.get("feeSchedule")
    if not isinstance(schedule, Mapping):
        return "Polymarket fee metadata is missing a structured feeSchedule"
    rate = _number(schedule.get("rate"))
    exponent = _number(schedule.get("exponent"))
    if rate is None or rate < 0 or exponent is None or exponent < 0:
        return "Polymarket feeSchedule rate/exponent is invalid"
    return None


def _pm_market_ok(market: Any, candidate: Mapping[str, Any]) -> tuple[str | None, tuple[str, str] | None]:
    if not isinstance(market, Mapping):
        return "Polymarket Gamma response is not an object", None
    if not _same_id(market.get("slug"), candidate.get("pm_slug")):
        return "Polymarket response slug does not match candidate pm_slug", None
    if market.get("active") is not True:
        return "Polymarket market is inactive", None
    if market.get("closed") is True or market.get("resolved") is True:
        return "Polymarket market is resolved/closed", None
    if market.get("proposed") is True or market.get("disputed") is True:
        return "Polymarket market is proposed/disputed", None
    for key in ("umaResolutionStatus", "umaResolutionStatuses"):
        value = market.get(key)
        parsed = _parse_list(value) if isinstance(value, str) else None
        values = parsed if parsed is not None else (
            value if isinstance(value, (list, tuple)) else [value])
        for item in values:
            state = _text(item).casefold()
            if state in {"resolved", "proposed", "disputed", "inactive", "closed"}:
                return f"Polymarket UMA resolution status is {state}", None
    status = _text(market.get("status")).casefold()
    if status in {"resolved", "proposed", "disputed", "inactive", "closed"}:
        return f"Polymarket market status is {status}", None
    if market.get("acceptingOrders") is False or market.get("enableOrderBook") is False:
        return "Polymarket market is not accepting CLOB orders", None
    fee_reason = _pm_fee_metadata_ok(market)
    if fee_reason:
        return fee_reason, None
    tokens = _pm_market_tokens(market)
    if tokens is None:
        return "Polymarket outcomes/tokens are not a distinct Yes/No mapping", None
    condition = market.get("conditionId") or market.get("condition_id")
    if not _text(condition):
        return "Polymarket conditionId is missing", None
    return None, tokens


def _pm_book_ok(book: Any, token: str, condition: str, now: float) -> str | None:
    if not isinstance(book, Mapping):
        return "Polymarket book is not an object"
    book_token = book.get("asset_id") or book.get("token_id") or book.get("tokenId")
    if not _same_id(book_token, token):
        return "Polymarket book token identity mismatch"
    book_condition = book.get("market") or book.get("conditionId") or book.get("condition_id")
    if not _same_id(book_condition, condition):
        return "Polymarket book condition identity mismatch"
    stamp = _timestamp(book.get("timestamp"))
    if stamp is None:
        return "Polymarket book timestamp is missing or invalid"
    age = now - stamp
    if age < 0 or age > PM_BOOK_MAX_AGE_SECONDS:
        return f"Polymarket book timestamp age {age:.1f}s exceeds {PM_BOOK_MAX_AGE_SECONDS:.0f}s"
    minimum = _number(book.get("min_order_size"))
    if minimum is None or minimum <= 0:
        return "Polymarket minimum order size is missing or invalid"
    return None


def _direction_result(raw: dict[str, Any], direction: str, lim_outcome: str,
                      pm_outcome: str, lim_token: str, pm_token: str,
                      pm_minimum: float, cap_usdc: float) -> dict[str, Any]:
    result = dict(raw)
    result.update({"direction": direction, "screening_only": True,
                   "execution_ready": False, "lim_outcome": lim_outcome,
                   "pm_outcome": pm_outcome, "pm_min_order_size": pm_minimum,
                   "assumptions": list(_ASSUMPTIONS),
                   "cash_cap_usdc": cap_usdc})
    result["lim"]["buy_token"] = lim_outcome
    result["lim"]["token_id"] = lim_token
    result["pm"]["buy_token"] = pm_outcome
    result["pm"]["token_id"] = pm_token
    result["pm"]["min_order_size"] = pm_minimum
    matched = float(result["matched_net_shares"])
    if matched < pm_minimum:
        result["ok"] = False
        result["reason"] = f"PM minimum order size {pm_minimum:g} exceeds matched {matched:g}"
    else:
        floor = result["conditional_profit_floor_usdc"]
        total = result["total_cash_usdc"]
        edge = floor / total if total else 0
        result["conditional_net_edge_frac"] = edge
        result["ok"] = bool(floor > 0 and edge >= MIN_NET_EDGE)
        result["reason"] = ("passes conditional screening" if result["ok"] else
                             f"conditional floor edge {edge * 100:.2f}% below {MIN_NET_EDGE * 100:.1f}%")
    return result


def _live_arb_quote(candidate: dict, usdc_per_side: float, *, now: float | None = None,
                    get: Callable[..., Any] | None = None) -> dict[str, Any]:
    """Fetch and validate public data, returning both conditional directions."""
    base: dict[str, Any] = {"screening_only": True, "execution_ready": False,
                            "assumptions": list(_ASSUMPTIONS), "directions": {}}
    if not isinstance(candidate, Mapping):
        return _unpriced("candidate is not an object", **base)
    required = ("lim_id", "lim_slug", "lim_yes_token", "lim_no_token", "pm_slug")
    missing = [key for key in required if not _text(candidate.get(key))]
    if missing:
        return _unpriced(f"candidate missing {', '.join(missing)}", **base)
    current = time.time() if now is None else float(now)
    try:
        lim_market = _json_get(f"{LIMITLESS_API_BASE}/markets/{candidate['lim_slug']}", get=get)
    except Exception as exc:
        return _unpriced(f"Limitless market fetch failed: {str(exc)[:120]}", **base)
    reason = _limitless_market_ok(lim_market, candidate, current)
    if reason:
        return _unpriced(reason, **base)
    try:
        lim_book = _json_get(f"{LIMITLESS_API_BASE}/markets/{candidate['lim_slug']}/orderbook", get=get)
    except Exception as exc:
        return _unpriced(f"Limitless YES orderbook fetch failed: {str(exc)[:120]}", **base)
    if not isinstance(lim_book, Mapping) or not _same_id(lim_book.get("tokenId"), candidate["lim_yes_token"]):
        return _unpriced("Limitless orderbook is not the exact YES book", **base)
    try:
        gamma = _json_get(f"{POLYMARKET_GAMMA}/markets", params={"slug": candidate["pm_slug"]}, get=get)
    except Exception as exc:
        return _unpriced(f"Polymarket Gamma fetch failed: {str(exc)[:120]}", **base)
    if not isinstance(gamma, list) or len(gamma) != 1:
        return _unpriced("Polymarket Gamma exact slug did not return one market", **base)
    pm_market = gamma[0]
    reason, pm_tokens = _pm_market_ok(pm_market, candidate)
    if reason or pm_tokens is None:
        return _unpriced(reason or "Polymarket token mapping failed", **base)
    pm_yes, pm_no = pm_tokens
    condition = _text(pm_market.get("conditionId") or pm_market.get("condition_id"))
    books: dict[str, dict] = {}
    minima: dict[str, float] = {}
    for token, label in ((pm_yes, "YES"), (pm_no, "NO")):
        try:
            book = _json_get(POLYMARKET_CLOB, params={"token_id": token}, get=get)
        except Exception as exc:
            return _unpriced(f"Polymarket {label} orderbook fetch failed: {str(exc)[:120]}", **base)
        books[label] = book
    validation_now = current if now is not None else time.time()
    # Recheck the Limitless expiry after all network reads; a short-lived
    # market must not be treated as fresh based only on the initial timestamp.
    reason = _limitless_market_ok(lim_market, candidate, validation_now)
    if reason:
        return _unpriced(reason, **base)
    for token, label in ((pm_yes, "YES"), (pm_no, "NO")):
        reason = _pm_book_ok(books[label], token, condition, validation_now)
        if reason:
            return _unpriced(f"Polymarket {label} book: {reason}", **base)
        minima[label] = float(books[label]["min_order_size"])

    specs = (("lim_yes_pm_no", "YES", "NO", pm_no, "NO"),
             ("lim_no_pm_yes", "NO", "YES", pm_yes, "YES"))
    for direction, lim_outcome, pm_outcome, pm_token, pm_label in specs:
        try:
            raw = quote_pair(lim_book, str(candidate["lim_yes_token"]), lim_outcome,
                             books[pm_label], pm_market, usdc_per_side,
                             lim_fee_bound=LIMITLESS_FEE_BOUND)
            result = _direction_result(raw, direction, lim_outcome, pm_outcome,
                                       str(candidate[f"lim_{lim_outcome.lower()}_token"]),
                                       pm_token, minima[pm_label], float(usdc_per_side))
        except Exception as exc:
            result = _unpriced(f"{direction} quote unavailable: {str(exc)[:120]}")
            result.update({"direction": direction, "screening_only": True,
                           "execution_ready": False})
        base["directions"][direction] = result
    priced = [q for q in base["directions"].values() if q.get("status") == "screening_quote_only"]
    if not priced:
        return _unpriced("both complementary directions are unpriced", **base)
    eligible = [q for q in priced if q.get("ok")]
    best = max(eligible or priced, key=lambda q: q["conditional_profit_floor_usdc"])
    base.update({"status": "screening_quote_only", "best_direction": best["direction"],
                 "selected": best, "ok": bool(best.get("ok")),
                 "reason": ("passes conditional screening" if best.get("ok") else
                            "no direction clears the conditional profit/edge screen")})
    # Legacy result names remain available, but values are explicitly screening
    # floors and are never called executable/locked.
    for key in ("lim", "pm", "total_cash_usdc", "conditional_payout_floor_usdc",
                "conditional_profit_floor_usdc"):
        base[key] = best[key]
    base["direction"] = best["direction"]
    base["net_profit"] = best["conditional_profit_floor_usdc"]
    base["net_edge_frac"] = best.get("conditional_net_edge_frac", 0)
    base["fees_usdc"] = best["pm"].get("fee_usdc")
    return base


def cmd_status(_args: argparse.Namespace) -> int:
    state = _load_state()
    print("limitless arb quote inspector (execution disabled)")
    print(f"  state file: {STATE_PATH} ({'exists' if STATE_PATH.exists() else 'fresh'})")
    print(f"  open arbs:  {len(state.get('open_arbs', []))}")
    print(f"  resolved:   {len(state.get('resolved_arbs', []))}")
    print(f"  last run:   {state.get('last_run_at', 'never')}")
    print(f"  scan file:  {SCAN_OUTPUT} ({'exists' if SCAN_OUTPUT.exists() else 'missing'})")
    print("  credentials: not required (public reads only)")
    return 0


def _candidate_is_mechanical(scan_record: dict) -> bool:
    return bool((scan_record.get("lim_metadata") or {})
                .get("chainlinkDataStream", {}).get("enabled"))


def _scan_is_fresh(scan: Mapping[str, Any], now: float | None = None) -> tuple[bool, str]:
    stamp = _timestamp(scan.get("generated_at"))
    if stamp is None:
        return False, "scan snapshot has no verifiable generated_at"
    current = time.time() if now is None else float(now)
    age = current - stamp
    if age < 0 or age > SCAN_MAX_AGE_SECONDS:
        return False, f"scan snapshot age {age:.0f}s exceeds {SCAN_MAX_AGE_SECONDS}s"
    return True, ""


def cmd_run(args: argparse.Namespace) -> int:
    """Inspect one candidate.  This command has no order or alert path."""
    state = _load_state()
    scan = _read_scan()
    if not scan:
        print("no scan output; run scripts/limitless_arb_scan.py first")
        return 1
    fresh, freshness_reason = _scan_is_fresh(scan)
    if not fresh:
        print(f"stale/unverifiable scan; {freshness_reason}")
        return 0
    used = _open_capital_used(state)
    if used >= TOTAL_OPEN_ARB_CAP_USDC:
        print(f"open arb capital ${used:.2f} at cap; skipping")
        return 0
    candidate = _select_candidate(scan, state)
    if not candidate:
        print("no eligible IDENTICAL candidate above net-edge threshold")
        return 0
    cap = (PER_ARB_FIRST_TRADE_CAP_USDC
           if not state.get("first_trade_completed") else PER_ARB_CAP_USDC)
    print(f"selected: {candidate.get('lim_title', '')[:80]}")
    print(f"  conditional screening cap per leg: ${cap:.2f}")
    quote = _live_arb_quote(candidate, cap)
    if quote.get("ok"):
        print(f"SCREENING QUOTE ONLY — conditional floor edge {float(quote.get('net_edge_frac', 0))*100:+.2f}%")
        print(f"  direction: {quote.get('direction')}")
    else:
        print(f"screening quote unavailable/rejected: {quote.get('reason', 'unknown')}")
    print("  execution_ready=False; no order submitted")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    run = sub.add_parser("run", help="compute a public-read screening quote (never submits)")
    run.add_argument("--dry-run", action="store_true", help="kept for compatibility")
    sub.add_parser("dry-run", help="compatibility alias for run --dry-run").set_defaults(
        fn=cmd_run, dry_run=True)
    run.set_defaults(fn=cmd_run)
    args = parser.parse_args()
    global _DRY_RUN
    _DRY_RUN = bool(getattr(args, "dry_run", False))
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
