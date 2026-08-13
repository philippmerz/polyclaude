#!/usr/bin/env python3
"""Aggregator command — runs all polyclaude tick-checks in one invocation.

Bundles into a single status summary:
1. Positions (data-api + on-chain) + sleeve balances
2. Hurdle scan (check_marginal_apy with drawdown guard)
3. Watchlist trigger check (watchlist_monitor --hits-only)
4. UMA status check (uma_status_check)
5. Kelly portfolio audit (portfolio_kelly --constrained)
6. Recent news alerts (last 6h)

Output: structured markdown summary + Telegram-friendly tick line.

Usage:
    python scripts/polyclaude_status.py             # full report
    python scripts/polyclaude_status.py --quick     # skip slow checks (UMA, Kelly)
    python scripts/polyclaude_status.py --telegram  # send summary to Telegram

Operator directive 2026-05-09: this is the single-command operator state-check.
Each polyclaude check-in (cron or ad-hoc) can invoke this to get full visibility
without manually orchestrating individual scripts.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_script(args: list[str], timeout: int = 60) -> str:
    """Run a polyclaude script, return stdout (or stderr-prefixed error)."""
    try:
        r = subprocess.run(
            [".venv/bin/python"] + args,
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout,
        )
        if r.returncode != 0:
            return f"[ERR exit {r.returncode}] {r.stderr.strip()[:300]}"
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT after {timeout}s]"
    except Exception as e:
        return f"[EXCEPTION] {e}"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("--quick", action="store_true", help="Skip slow checks (UMA, full Kelly).")
    p.add_argument("--telegram", action="store_true", help="Send compact summary to Telegram.")
    p.add_argument("--md", action="store_true", help="Markdown-format output (default plain).")
    args = p.parse_args()

    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M UTC")

    # Header
    print(f"\n{'='*80}")
    print(f"# POLYCLAUDE STATUS — {ts}")
    print(f"{'='*80}\n")

    # 1. Positions
    print("## Positions (PM sleeve)")
    print(run_script(["scripts/positions.py"], timeout=30))

    # 2. Hurdle scan + drawdown
    print("\n## Hurdle scan (marginal APY + drawdown guard)")
    out = run_script(["scripts/check_marginal_apy.py"], timeout=30)
    # Show only header + drawdown alerts + close candidates
    lines = out.split("\n")
    summary_lines = []
    in_drawdown = False
    for line in lines:
        if "DRAWDOWN ALERT" in line or "below hurdle" in line or "clear hurdle" in line:
            summary_lines.append(line)
        elif "Will" in line and "%" in line[:20]:  # data row
            pass  # skip individual hold rows here
    print("\n".join(summary_lines) if summary_lines else "(see full check_marginal_apy.py output)")

    # 3. Watchlist
    print("\n## Watchlist hits (12 candidates)")
    out = run_script(["scripts/watchlist_monitor.py", "--hits-only"], timeout=30)
    print(out if out.strip() else "(no triggers hit)")

    if not args.quick:
        # 4. UMA
        print("\n## UMA status check")
        print(run_script(["scripts/uma_status_check.py"], timeout=120))

        # 5. Kelly portfolio
        print("\n## Kelly portfolio (constrained)")
        out = run_script(["scripts/portfolio_kelly.py", "--constrained"], timeout=30)
        # Show summary lines only
        lines = out.split("\n")
        summary = []
        capture = False
        for line in lines:
            if "TOTAL:" in line or "Bankroll utilization" in line or "Recommended actions" in line:
                capture = True
            if capture:
                summary.append(line)
        print("\n".join(summary) if summary else out[-1500:])

        # 5b. Brownian-bridge fair-value
        print("\n## Brownian-bridge fair-value (time-decay-adjusted)")
        out = run_script(["scripts/brownian_bridge_fv.py"], timeout=30)
        # Show only TRIM/SCALE_UP summary
        lines = out.split("\n")
        summary = []
        capture = False
        for line in lines:
            if "TRIM candidates" in line or "SCALE_UP candidates" in line or "(no TRIM" in line or "(no SCALE_UP" in line:
                capture = True
            if capture:
                summary.append(line)
        print("\n".join(summary) if summary else "(see brownian_bridge_fv.py for details)")

    # 6. News alerts (last 6h)
    print("\n## News alerts (last 6h)")
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(hours=6)).isoformat()
    alerts_path = REPO_ROOT / "notes" / "news_alerts.jsonl"
    if alerts_path.exists():
        try:
            recent = []
            for line in alerts_path.read_text().splitlines():
                try:
                    d = json.loads(line)
                    if d.get("ts", "") > cutoff:
                        recent.append(d)
                except Exception:
                    continue
            if not recent:
                print("(no alerts in last 6h)")
            else:
                for d in recent[-10:]:
                    levels = [i.get("level") for i in d.get("impacts", [])]
                    has_critical = any(lv in ("CRITICAL", "MATERIAL") for lv in levels)
                    flag = " [⚠]" if has_critical else ""
                    print(f"  {d.get('ts')[:16]} t{d.get('tier','?')} {d.get('matched','?')}: "
                          f"{d.get('title','?')[:70]}{flag}")
        except Exception as e:
            print(f"(error reading alerts: {e})")
    else:
        print("(no alerts file)")

    print(f"\n{'='*80}\n")

    # Optionally send Telegram summary
    if args.telegram:
        try:
            # Compact line for tick summary
            r = subprocess.run([".venv/bin/python", "scripts/positions.py"],
                               cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)
            pos_out = r.stdout
            mtm_match = re.search(r"mtm\s+\$([\d.-]+)", pos_out)
            cost_match = re.search(r"cost\s+\$([\d.-]+)", pos_out)
            mtm = mtm_match.group(1) if mtm_match else "?"
            cost = cost_match.group(1) if cost_match else "?"
            # Carry the REALIZABLE figure into the operator-facing line when
            # positions.py reports one (2026-08-13). This was the last display
            # layer still quoting the midpoint alone: the fix went into
            # positions.py, then bankroll.py, and this telegram — the number the
            # operator actually READS — was still grepping `mtm` only. Same
            # scope error twice in one morning, which is why the rule is now
            # "enumerate every display layer", not "fix the display layer".
            real_match = re.search(r"REALIZABLE \(best bids\): \$([\d.-]+)", pos_out)
            real_line = f"realizable ${real_match.group(1)} (best bids)\n" if real_match else ""

            tg_msg = (f"polyclaude status {ts}\n"
                      f"PM cost ${cost} mtm ${mtm}\n"
                      f"{real_line}"
                      f"(full report via scripts/polyclaude_status.py)")
            subprocess.run([".venv/bin/python", "scripts/telegram.py", "msg", tg_msg],
                           cwd=REPO_ROOT, timeout=15)
            print("(Telegram summary sent)")
        except Exception as e:
            print(f"(Telegram send failed: {e})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
