"""Autonomous Limitless ↔ Polymarket arb executor.

Reads the latest scan output, picks the highest-net-edge IDENTICAL
candidate, re-fetches both venues' orderbooks for actual fillable prices
(not midpoints — the scanner overestimates because it uses displayed
midpoint, real fills happen at the orderbook spread), recomputes net
edge after slippage + fees, and if the post-slippage edge still clears
the threshold, fires both legs.

Two-leg execution:
  1. Place Limitless leg as FOK (fill-or-kill) — atomic, guaranteed
     to either fill at the requested price or cancel cleanly.
  2. If Lim fills, immediately place Polymarket leg.
  3. If PM leg fails to fill, market-close the Lim leg at best bid
     (emergency exit, accept slippage to avoid one-sided exposure).

Per-arb cap: $3/leg ($6 total exposure). Total open arb cap: $20.
Net-edge threshold (post-slippage): 1.5%.
First-trade self-throttle: $1/leg until at least one arb resolves cleanly.

Subcommands:
  status       Read-only: print state, balances, latest candidate
  run          Attempt one execution if eligible
  dry-run      Compute the trade but don't submit
  resolve      Mark closed/resolved arbs, tally realized P&L
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
from eth_account import Account

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
SCAN_OUTPUT = _REPO_ROOT / "logs" / "limitless_arb_latest.json"
STATE_PATH = Path.home() / ".polyclaude_arb_state.json"

# Risk parameters
PER_ARB_CAP_USDC = 3.00
PER_ARB_FIRST_TRADE_CAP_USDC = 1.00  # used until first arb resolves cleanly
TOTAL_OPEN_ARB_CAP_USDC = 20.00
MIN_NET_EDGE = 0.015
LIMITLESS_API_BASE = "https://api.limitless.exchange"
POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"
POLYMARKET_FEE_RATE = 0.072


# ---- helpers ---------------------------------------------------------------


_DRY_RUN = False   # set from --dry-run in main(); gates all operator alerts


def _telegram(text: str) -> None:
    """Best-effort Telegram; never raise.

    DRY-RUN GATE (2026-08-12): gated at the FUNCTION, not per call site, so a
    new call site cannot forget it. Origin: five --dry-run drills of the
    Polymarket exit each Telegrammed "submitted: 7/8" — indistinguishable from
    a real liquidation on the operator's screen. Dry-run suppressed the ORDERS
    and did nothing about the ALARM; with a monthly drill scheduled that would
    have become a recurring false emergency.
    """
    if _DRY_RUN:
        print(f"  (dry run — operator NOT telegrammed: {text.splitlines()[0][:70]})")
        return
    try:
        subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            cwd=_REPO_ROOT, check=False, timeout=15, capture_output=True,
        )
    except Exception:
        pass


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"open_arbs": [], "resolved_arbs": [], "last_run_at": 0,
                "first_trade_completed": False}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"open_arbs": [], "resolved_arbs": [], "last_run_at": 0,
                "first_trade_completed": False}


def _save_state(s: dict) -> None:
    STATE_PATH.write_text(json.dumps(s, indent=2, default=str))
    os.chmod(STATE_PATH, 0o600)


def _have_limitless_creds() -> bool:
    return bool(os.environ.get("LIMITLESS_API_KEY") and
                os.environ.get("LIMITLESS_API_SECRET"))


def _read_scan() -> dict:
    if not SCAN_OUTPUT.exists():
        return {}
    try:
        return json.loads(SCAN_OUTPUT.read_text())
    except Exception:
        return {}


def _select_candidate(scan: dict, state: dict) -> dict | None:
    """Highest-net-edge IDENTICAL candidate not already open AND with
    mechanical/oracle resolution (Limitless Chainlink Data Stream enabled).
    Subjective-resolution markets (FDV / launch / sports props) are excluded
    even if the agent verified them as IDENTICAL — single resolution-language
    disagreement can wipe ~25 successful arbs at our size.
    """
    identical = scan.get("verified_identical") or []
    open_lim_ids = {a.get("lim_id") for a in state.get("open_arbs", [])}
    eligible = [c for c in identical
                if (c.get("net_edge") or 0) >= MIN_NET_EDGE
                and c.get("lim_id") not in open_lim_ids
                and c.get("lim_chainlink_enabled")]
    if not eligible:
        return None
    eligible.sort(key=lambda c: -(c.get("net_edge") or 0))
    return eligible[0]


def _open_capital_used(state: dict) -> float:
    return sum(float(a.get("capital_per_side") or 0) * 2
               for a in state.get("open_arbs", []))


# ---- orderbook walking ----------------------------------------------------


def _walk_book_buy_ask(asks: list[dict], usdc_target: float) -> tuple[float, float] | None:
    """Walk an ask-side book, computing avg fill price for `usdc_target` of buys.

    Returns (avg_price, tokens_received) or None if depth is insufficient.

    Each ask entry: {'price': float, 'size': int (microUSDC of size at that price)}
    For Limitless: size is in 6-decimal USDC units (microUSDC). We treat it as
    USDC-equivalent of token-quantity at that price: tokens = size / 1e6 / price.
    """
    target_usdc = float(usdc_target)
    spent_usdc = 0.0
    tokens = 0.0
    for ask in asks:
        if spent_usdc >= target_usdc - 1e-9:
            break
        p = float(ask["price"])
        size_usdc = float(ask["size"]) / 1_000_000  # microUSDC -> USDC
        # USDC needed to clear this level
        room = target_usdc - spent_usdc
        take_usdc = min(room, size_usdc)
        spent_usdc += take_usdc
        tokens += take_usdc / p
    if spent_usdc < target_usdc - 1e-6:
        return None  # insufficient depth
    avg_price = spent_usdc / tokens if tokens > 0 else 0
    return (avg_price, tokens)


# ---- Polymarket orderbook fetch -------------------------------------------


def _polymarket_token_orderbook(token_id: str) -> dict | None:
    """Fetch Polymarket orderbook for a token via the public CLOB endpoint."""
    try:
        r = httpx.get(f"https://clob.polymarket.com/book",
                      params={"token_id": token_id}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _polymarket_walk_book_buy(book: dict, usdc_target: float) -> tuple[float, float] | None:
    """Walk Polymarket orderbook (asks). Returns (avg_price, tokens) or None.

    Polymarket book shape: {'bids': [{'price': '0.14', 'size': '12.5'}, ...], 'asks': ...}
    Sizes are in tokens (shares), not USDC. To buy `usdc_target` USDC worth, we
    walk asks ascending.
    """
    asks = book.get("asks") or []
    # Asks come sorted descending by price typically; ensure ascending
    parsed = sorted([(float(a["price"]), float(a["size"])) for a in asks
                     if float(a.get("size", 0)) > 0], key=lambda x: x[0])
    spent_usdc = 0.0
    tokens = 0.0
    for price, size in parsed:
        if spent_usdc >= usdc_target - 1e-9:
            break
        room = usdc_target - spent_usdc
        max_tokens_here = size
        max_usdc_here = max_tokens_here * price
        take_usdc = min(room, max_usdc_here)
        spent_usdc += take_usdc
        tokens += take_usdc / price
    if spent_usdc < usdc_target - 1e-6:
        return None
    avg_price = spent_usdc / tokens if tokens > 0 else 0
    return (avg_price, tokens)


# ---- live arb evaluation --------------------------------------------------


async def _live_arb_quote(candidate: dict, usdc_per_side: float) -> dict:
    """Fetch live orderbooks on both venues, compute actual fill prices,
    and return a rich quote dict with net edge after real slippage.

    Decision is symmetric: if Lim YES < PM YES → buy Lim YES + buy PM NO.
    Else → buy PM YES + buy Lim NO.
    """
    from limitless_sdk import HMACCredentials
    from limitless_sdk.api import HttpClient

    key = os.environ["LIMITLESS_API_KEY"]
    sec = os.environ["LIMITLESS_API_SECRET"]
    creds = HMACCredentials(token_id=key, secret=sec)
    http = HttpClient(hmac_credentials=creds)

    # Determine direction by the scan's last-seen prices
    lim_yes_scan = float(candidate["lim_yes_price"])
    pm_yes_scan = float(candidate["pm_yes_price"])
    direction = "lim_yes_pm_no" if lim_yes_scan < pm_yes_scan else "pm_yes_lim_no"

    quote = {"direction": direction, "ok": False, "reason": "", "lim": {}, "pm": {}}

    try:
        # Limitless market data fresh — find current slug by id (slugs rotate)
        all_pages = []
        page = 1
        while True:
            r = await http.get(f"/markets/active?page={page}")
            all_pages.extend(r.get("data") or [])
            if not r.get("data") or len(all_pages) >= (r.get("totalMarketsCount") or 0):
                break
            page += 1
            if page > 50:
                break
        lim_market = next((m for m in all_pages if m["id"] == candidate["lim_id"]), None)
        if not lim_market:
            quote["reason"] = "limitless market not found in active set"
            return quote
        slug = lim_market["slug"]

        # Limitless orderbook — note: SDK returns one tokenId at a time. Choose
        # the side we're buying.
        if direction == "lim_yes_pm_no":
            lim_token = lim_market["tokens"]["yes"]
        else:
            lim_token = lim_market["tokens"]["no"]
        # The /markets/{slug}/orderbook endpoint returns the YES book by default.
        # For NO, need /markets/{slug}/orderbook?tokenId={no_token}
        ob_path = f"/markets/{slug}/orderbook"
        if direction == "pm_yes_lim_no":
            ob_path += f"?tokenId={lim_token}"
        try:
            lim_book = await http.get(ob_path)
        except Exception as e:
            quote["reason"] = f"limitless orderbook fetch failed: {str(e)[:120]}"
            return quote

        lim_walk = _walk_book_buy_ask(lim_book.get("asks") or [], usdc_per_side)
        if not lim_walk:
            quote["reason"] = f"limitless insufficient depth at ${usdc_per_side}"
            return quote
        lim_fill_price, lim_tokens = lim_walk
        quote["lim"] = {
            "slug": slug,
            "token_id": lim_token,
            "buy_token": "YES" if direction == "lim_yes_pm_no" else "NO",
            "fill_price": lim_fill_price,
            "tokens": lim_tokens,
            "usdc": usdc_per_side,
        }
    finally:
        await http.close()

    # Polymarket orderbook lookup. We need the token_id for the side we buy.
    pm_slug = candidate["pm_slug"]
    pm_market = httpx.get(f"{POLYMARKET_GAMMA}/markets",
                           params={"slug": pm_slug}, timeout=10).json()
    if not pm_market or not (isinstance(pm_market, list) and len(pm_market)):
        # Try direct fetch path
        pm_market_data = httpx.get(f"{POLYMARKET_GAMMA}/markets/{pm_slug}",
                                    timeout=10).json()
        if isinstance(pm_market_data, dict):
            pm_market = [pm_market_data]
        else:
            quote["reason"] = "polymarket market not found"
            return quote
    pm = pm_market[0]
    pm_clob_tokens = pm.get("clobTokenIds") or "[]"
    if isinstance(pm_clob_tokens, str):
        pm_clob_tokens = json.loads(pm_clob_tokens)
    if not pm_clob_tokens or len(pm_clob_tokens) < 2:
        quote["reason"] = "polymarket missing clob tokens"
        return quote

    # Polymarket outcome ordering is ["Yes", "No"] (verified via gamma).
    pm_yes_token = pm_clob_tokens[0]
    pm_no_token = pm_clob_tokens[1]
    pm_buy_token = pm_no_token if direction == "lim_yes_pm_no" else pm_yes_token

    pm_book = _polymarket_token_orderbook(pm_buy_token)
    if not pm_book:
        quote["reason"] = "polymarket orderbook fetch failed"
        return quote
    pm_walk = _polymarket_walk_book_buy(pm_book, usdc_per_side * (1 - lim_yes_scan if direction == "lim_yes_pm_no" else lim_yes_scan))
    # Actually we want SAME tokens on each side, not same USDC. Recompute.
    # But for now, simpler: target the matching token quantity, not USDC.
    # We bought lim_tokens above; need lim_tokens on PM side too.
    target_pm_tokens = quote["lim"]["tokens"]

    # Re-walk for token-quantity targeting on PM side
    asks = pm_book.get("asks") or []
    parsed = sorted([(float(a["price"]), float(a["size"])) for a in asks
                     if float(a.get("size", 0)) > 0], key=lambda x: x[0])
    spent_usdc = 0.0
    tokens_bought = 0.0
    for price, size in parsed:
        if tokens_bought >= target_pm_tokens - 1e-6:
            break
        take_tokens = min(size, target_pm_tokens - tokens_bought)
        spent_usdc += take_tokens * price
        tokens_bought += take_tokens
    if tokens_bought < target_pm_tokens - 1e-3:
        quote["reason"] = (f"polymarket insufficient depth: have {tokens_bought:.3f} "
                           f"tokens, need {target_pm_tokens:.3f}")
        return quote
    pm_fill_price = spent_usdc / tokens_bought if tokens_bought > 0 else 0

    quote["pm"] = {
        "slug": pm_slug,
        "token_id": pm_buy_token,
        "buy_token": "NO" if direction == "lim_yes_pm_no" else "YES",
        "fill_price": pm_fill_price,
        "tokens": tokens_bought,
        "usdc": spent_usdc,
    }

    # Net edge: each side bought ~`target_pm_tokens` shares; total cost is
    # lim_usdc + pm_spent_usdc; payout at resolution is target_pm_tokens × $1.
    total_cost = quote["lim"]["usdc"] + quote["pm"]["usdc"]
    payout = target_pm_tokens
    gross_profit = payout - total_cost
    # Fees
    lim_fee_frac = 0.004 + (0.030 - 0.004) * abs(lim_fill_price - 0.5) * 2
    pm_fee_frac = POLYMARKET_FEE_RATE * min(pm_fill_price, 1 - pm_fill_price)
    fees_usdc = quote["lim"]["usdc"] * lim_fee_frac + quote["pm"]["usdc"] * pm_fee_frac
    net_profit = gross_profit - fees_usdc

    quote["total_cost"] = total_cost
    quote["payout_if_resolves"] = payout
    quote["gross_profit"] = gross_profit
    quote["fees_usdc"] = fees_usdc
    quote["net_profit"] = net_profit
    quote["net_edge_frac"] = net_profit / total_cost if total_cost > 0 else 0
    quote["ok"] = net_profit > 0 and quote["net_edge_frac"] >= MIN_NET_EDGE
    quote["reason"] = "ok" if quote["ok"] else f"net edge {quote['net_edge_frac']*100:.2f}% < threshold {MIN_NET_EDGE*100:.1f}%"
    return quote


# ---- subcommands -----------------------------------------------------------


def cmd_status(_args: argparse.Namespace) -> int:
    state = _load_state()
    print("limitless arb executor")
    print(f"  state file: {STATE_PATH} ({'exists' if STATE_PATH.exists() else 'fresh'})")
    print(f"  open arbs:  {len(state.get('open_arbs', []))}")
    for a in state.get("open_arbs", [])[:10]:
        print(f"    {json.dumps(a, default=str)[:200]}")
    print(f"  resolved:   {len(state.get('resolved_arbs', []))}")
    print(f"  last run:   {state.get('last_run_at', 'never')}")
    print(f"  scan file:  {SCAN_OUTPUT} ({'exists' if SCAN_OUTPUT.exists() else 'missing'})")
    print(f"  creds:      {'set' if _have_limitless_creds() else 'MISSING'}")
    print(f"  first trade completed: {state.get('first_trade_completed', False)}")
    return 0


def _candidate_is_mechanical(scan_record: dict) -> bool:
    """Filter for candidates where resolution is a mechanical/oracle event.

    Limitless side: market metadata must have `chainlinkDataStream.enabled`.
    These are crypto-price-at-time markets — objective, hard for the two
    venues' oracles to disagree on. Excludes FDV/launch/sports/props markets
    where resolution language is subjective and divergence risk is real.
    """
    return bool((scan_record.get("lim_metadata") or {})
                .get("chainlinkDataStream", {}).get("enabled"))


def cmd_run(args: argparse.Namespace) -> int:
    state = _load_state()
    state["last_run_at"] = int(time.time())

    if not _have_limitless_creds():
        msg = ("limitless arb executor blocked: credentials not set in env. "
               "Drop ~/secrets/limitless_creds.json with key+secret, or populate "
               "~/.polyclaude/env with LIMITLESS_API_KEY + LIMITLESS_API_SECRET.")
        print(msg)
        last = state.get("last_missing_key_alert", 0)
        now = int(time.time())
        if now - last >= 6 * 3600:
            _telegram(msg)
            state["last_missing_key_alert"] = now
        _save_state(state)
        return 2

    scan = _read_scan()
    if not scan:
        print("no scan output; run scripts/limitless_arb_scan.py first")
        _save_state(state)
        return 1

    if _open_capital_used(state) >= TOTAL_OPEN_ARB_CAP_USDC:
        print(f"open arb capital ${_open_capital_used(state):.2f} at cap; skipping")
        _save_state(state)
        return 0

    candidate = _select_candidate(scan, state)
    if not candidate:
        print("no eligible IDENTICAL candidate above net-edge threshold")
        _save_state(state)
        return 0

    print(f"selected: {candidate.get('lim_title','')[:80]}")
    print(f"  scan net edge: {(candidate.get('net_edge') or 0)*100:+.2f}% "
          f"(midpoint-based; will recompute on real orderbook)")

    # First-trade self-throttle: $1/leg until the first arb resolves cleanly.
    cap = (PER_ARB_FIRST_TRADE_CAP_USDC
           if not state.get("first_trade_completed") else PER_ARB_CAP_USDC)
    print(f"  position size per leg: ${cap}")

    quote = asyncio.run(_live_arb_quote(candidate, cap))
    if not quote.get("ok"):
        msg = f"arb quote rejected: {quote.get('reason', 'unknown')}"
        print(msg)
        if quote.get("lim", {}).get("fill_price") and quote.get("pm", {}).get("fill_price"):
            print(f"  Lim fill: {quote['lim']['fill_price']:.4f}  PM fill: {quote['pm']['fill_price']:.4f}")
            print(f"  net edge after slippage: {quote.get('net_edge_frac', 0)*100:+.2f}%")
        _save_state(state)
        return 0

    print(f"\nLIVE QUOTE — net edge {quote['net_edge_frac']*100:+.2f}% after slippage:")
    print(f"  {quote['direction']}")
    print(f"  Lim {quote['lim']['buy_token']}: {quote['lim']['tokens']:.4f} tokens @ {quote['lim']['fill_price']:.4f}  cost ${quote['lim']['usdc']:.4f}")
    print(f"  PM  {quote['pm']['buy_token']}: {quote['pm']['tokens']:.4f} tokens @ {quote['pm']['fill_price']:.4f}  cost ${quote['pm']['usdc']:.4f}")
    print(f"  total cost: ${quote['total_cost']:.4f}  payout if resolves: ${quote['payout_if_resolves']:.4f}")
    print(f"  fees: ${quote['fees_usdc']:.4f}  net profit (locked): ${quote['net_profit']:.4f}")

    # Auto-execution is intentionally disabled. Pre-execution analysis
    # (2026-04-30) showed that even on agent-verified IDENTICAL pairs, the
    # post-slippage net edge is small enough that a single resolution-language
    # disagreement on a subjective market (FDV/launch/sports props) wipes
    # ~25 successful arbs. At our $1-3/leg size with ~80-90% verifier accuracy
    # on subtle edge cases, expected value goes negative. This script now
    # functions as a live-quote inspector: it tells us what the real
    # post-slippage edge would have been if we'd executed, but does not
    # fire orders. Use the data to decide manually whether a specific
    # candidate is worth a manual trade.
    _save_state(state)
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    s = sub.add_parser("run", help="compute live post-slippage quote (no live execution)")
    s.add_argument("--dry-run", action="store_true",
                   help="kept for compat; the executor never submits live orders")
    s.set_defaults(fn=cmd_run)
    args = p.parse_args()
    # Gate operator alerts on dry-run (2026-08-12). Setting the module flag
    # here covers EVERY _telegram call site in the file at once — the gate
    # without this wiring is inert, which is exactly the half-fix that let the
    # same bug survive one round of repair earlier today.
    global _DRY_RUN
    _DRY_RUN = bool(getattr(args, "dry_run", False))
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
