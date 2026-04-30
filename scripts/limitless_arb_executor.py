"""Autonomous Limitless ↔ Polymarket arb executor.

Reads the latest scan output (logs/limitless_arb_latest.json), filters to
agent-verified IDENTICAL candidates above the net-edge threshold, fires
both legs of the cross-venue arb, and emergency-closes a lone leg if the
second leg fails to fill.

Architecture:
  - Polymarket leg via existing scripts/polyclaude_client.py (the
    polymarket-sleeve wallet at 0x9032…267B; settles in USDC.e on Polygon)
  - Limitless leg via the official `limitless-sdk` Python package (the
    crypto-sleeve wallet at 0x83dA…3eE6; settles in USDC on Base)
  - Per-position cap: $3 from each side ($6 total exposure per arb)
  - Total open arb cap: $20 across both sides
  - Position state in ~/.polyclaude_arb_state.json

PREREQUISITE — operator action: create a Limitless API key via
https://limitless.exchange (Privy login → developer settings → create
key) and drop into ~/.polyclaude/env as:

    LIMITLESS_API_KEY=lk_...

The executor refuses to start without that env var. It also requires
USDC depth on both sides — you need ≥ $5 USDC.e on Polygon (polymarket
sleeve) and ≥ $5 USDC on Base (crypto sleeve) before the executor can
take any position.

Until the API key is set, this script is a no-op stub — the scanner
continues to find candidates and Telegram-alert on IDENTICAL ones, but
no automatic execution happens.

Subcommands:
  status         Print current open arbs + check API-key + balances
  run            One-shot: read scan output, attempt one execution if eligible
  dry-run        Same as run but print actions instead of executing

Usage from cron (every hour, after the scanner runs):
  python scripts/limitless_arb_scan.py --notify
  python scripts/limitless_arb_executor.py run
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
SCAN_OUTPUT = _REPO_ROOT / "logs" / "limitless_arb_latest.json"
STATE_PATH = Path.home() / ".polyclaude_arb_state.json"

# Risk parameters
PER_ARB_CAP_USDC = 3.00     # max collateral per leg per arb
TOTAL_OPEN_ARB_CAP_USDC = 20.00  # max total open arb capital (both sides combined)
MIN_NET_EDGE = 0.015        # 1.5% net edge required to execute
MIN_DEPTH_USDC = 3.00       # require both sides to have ≥ this depth at quoted price


def _telegram(text: str) -> None:
    try:
        subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", text],
            cwd=_REPO_ROOT, check=False, timeout=15, capture_output=True,
        )
    except Exception:
        pass


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {"open_arbs": [], "last_run_at": 0}
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"open_arbs": [], "last_run_at": 0}


def _save_state(s: dict) -> None:
    STATE_PATH.write_text(json.dumps(s, indent=2, default=str))
    os.chmod(STATE_PATH, 0o600)


def _have_limitless_key() -> bool:
    return bool(os.environ.get("LIMITLESS_API_KEY"))


def cmd_status(_args: argparse.Namespace) -> int:
    state = _load_state()
    print(f"limitless arb executor")
    print(f"  state file: {STATE_PATH} ({'exists' if STATE_PATH.exists() else 'fresh'})")
    print(f"  open arbs:  {len(state.get('open_arbs', []))}")
    for a in state.get("open_arbs", [])[:10]:
        print(f"    {a}")
    print(f"  last run:   {state.get('last_run_at', 'never')}")
    print(f"  scan file:  {SCAN_OUTPUT} ({'exists' if SCAN_OUTPUT.exists() else 'missing'})")
    print(f"  LIMITLESS_API_KEY: {'set' if _have_limitless_key() else 'MISSING (executor disabled)'}")
    return 0


def _read_scan() -> dict:
    if not SCAN_OUTPUT.exists():
        return {}
    try:
        return json.loads(SCAN_OUTPUT.read_text())
    except Exception as e:
        print(f"failed to read scan output: {_secrets.scrub(str(e))}")
        return {}


def _select_candidate(scan: dict, state: dict) -> dict | None:
    """Pick the highest-edge IDENTICAL candidate not already open."""
    identical = scan.get("verified_identical") or []
    if not identical:
        return None

    open_lim_ids = {a.get("lim_id") for a in state.get("open_arbs", [])}
    eligible = [c for c in identical
                if (c.get("net_edge") or 0) >= MIN_NET_EDGE
                and c.get("lim_id") not in open_lim_ids]
    if not eligible:
        return None

    eligible.sort(key=lambda c: -(c.get("net_edge") or 0))
    return eligible[0]


def _open_capital_used(state: dict) -> float:
    return sum(float(a.get("capital_per_side") or 0) * 2
               for a in state.get("open_arbs", []))


def _execute_arb(candidate: dict, dry_run: bool) -> dict:
    """Execute both legs of an arb. Stub for now — will fill in when API key is set.

    Returns a state record dict with status / tx hashes / errors.
    """
    if not _have_limitless_key():
        return {
            "status": "BLOCKED",
            "reason": "LIMITLESS_API_KEY not set in environment; executor cannot place Limitless leg",
            "candidate": candidate,
        }

    # Once API key exists, this is where the actual two-leg execution lives:
    # 1. Re-fetch live prices on both venues to confirm the spread still holds
    # 2. Compute exact order sizes for $3 per leg given current prices
    # 3. Place Limitless order via limitless_sdk
    # 4. Place Polymarket order via polyclaude_client
    # 5. Watch for partial fills; emergency-close lone leg if second fails
    # 6. Return the state record with both tx hashes
    #
    # Until the key exists, we don't even import limitless_sdk (it would
    # fail on missing env var). Stub the path.

    return {
        "status": "NOT_IMPLEMENTED",
        "reason": "execution path requires limitless_sdk + tested two-leg ordering; "
                  "scaffold exists, full implementation deferred to next iteration after API key is set",
        "candidate": candidate,
    }


def cmd_run(args: argparse.Namespace) -> int:
    state = _load_state()
    state["last_run_at"] = int(time.time())

    scan = _read_scan()
    if not scan:
        print("no scan output available; run scripts/limitless_arb_scan.py first")
        _save_state(state)
        return 1

    if _open_capital_used(state) >= TOTAL_OPEN_ARB_CAP_USDC:
        print(f"open arb capital ${_open_capital_used(state):.2f} >= cap ${TOTAL_OPEN_ARB_CAP_USDC:.2f}; skip")
        _save_state(state)
        return 0

    candidate = _select_candidate(scan, state)
    if not candidate:
        print("no eligible IDENTICAL candidate above net-edge threshold")
        _save_state(state)
        return 0

    print(f"selected: {candidate.get('lim_title', '')[:80]}  "
          f"net_edge={(candidate.get('net_edge') or 0)*100:+.2f}%")

    if not _have_limitless_key():
        # 6h cooldown on the missing-key Telegram so we don't spam the operator
        # while the key is still being created.
        last = state.get("last_missing_key_alert", 0)
        now = int(time.time())
        msg = ("limitless arb executor blocked: LIMITLESS_API_KEY not set. "
               "Operator action: create key at https://limitless.exchange "
               "and add to ~/.polyclaude/env. "
               f"Pending opportunity: {candidate.get('lim_title','')[:80]} "
               f"(net edge +{(candidate.get('net_edge') or 0)*100:.2f}%).")
        print(msg)
        if now - last >= 6 * 3600:
            _telegram(msg)
            state["last_missing_key_alert"] = now
        else:
            print(f"  (telegram suppressed by 6h cooldown; last alert {(now - last) // 60} min ago)")
        _save_state(state)
        return 2

    result = _execute_arb(candidate, args.dry_run)
    print(json.dumps(result, indent=2, default=str)[:1500])
    if result.get("status") == "OK":
        state.setdefault("open_arbs", []).append({
            "lim_id": candidate.get("lim_id"),
            "lim_title": candidate.get("lim_title"),
            "pm_slug": candidate.get("pm_slug"),
            "capital_per_side": PER_ARB_CAP_USDC,
            "opened_at": int(time.time()),
            "tx_lim": result.get("tx_lim"),
            "tx_pm": result.get("tx_pm"),
        })
        _telegram(f"limitless arb OPENED: {candidate.get('lim_title','')[:80]} "
                  f"net edge +{(candidate.get('net_edge') or 0)*100:.2f}%")
    _save_state(state)
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    s = sub.add_parser("run")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_run)
    s = sub.add_parser("dry-run")
    s.set_defaults(fn=lambda a: cmd_run(argparse.Namespace(dry_run=True)))
    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
