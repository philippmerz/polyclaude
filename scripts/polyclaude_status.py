#!/usr/bin/env python3
"""Aggregator command — runs all polyclaude tick-checks in one invocation.

Bundles into a single status summary:
1. Positions (data-api + on-chain) + sleeve balances
2. Hurdle scan (check_marginal_apy with drawdown guard)
3. Watchlist trigger check (watchlist_monitor --hits-only)
4. UMA status check (uma_status_check)
5. Kelly portfolio audit (portfolio_kelly --constrained)
6. HLE resolving-chart source check (full report only)
7. Recent news alerts (last 6h)

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
        stdout = r.stdout.strip()
        stderr = " ".join(r.stderr.split())[:300]
        if stderr:
            diagnostic = f"[stderr] {stderr}"
            return f"{stdout}\n{diagnostic}" if stdout else diagnostic
        return stdout
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT after {timeout}s]"
    except Exception as e:
        return f"[EXCEPTION] {e}"


_OPEN_TOTAL_RE = re.compile(
    r"^OPEN TOTAL\s+cost\s+\$([\d.-]+)\s+mtm\s+\$([\d.-]+)",
    re.MULTILINE,
)
_REALIZABLE_RE = re.compile(
    r"^REALIZABLE \(depth-walked, NET of taker fees\):\s*\$([\d.-]+)",
    re.MULTILINE,
)


def summarize_hurdle_output(output: str) -> str:
    """Keep actionable hurdle diagnostics while omitting routine hold rows."""
    summary: list[str] = []
    capture_flagged = False
    capture_drawdowns = False
    diagnostics = ("[ERR", "[TIMEOUT", "[EXCEPTION", "[stderr]")
    markers = (
        "DRAWDOWN ALERT",
        "NEGATIVE_EDGE",
        "CLOSE_CANDIDATE",
        "below hurdle",
        "below-hurdle",
        "clear hurdle",
    )

    for line in output.splitlines():
        stripped = line.strip()
        if line.startswith("=== FLAGGED"):
            capture_flagged = True
            summary.append(line)
            continue
        if capture_flagged and line.startswith("==="):
            capture_flagged = False
        if line.startswith("!!! DRAWDOWN ALERTS"):
            capture_drawdowns = True
            summary.append(line)
            continue
        if capture_drawdowns and not stripped:
            capture_drawdowns = False
        if capture_flagged or capture_drawdowns:
            if stripped:
                summary.append(line)
            continue
        if stripped.startswith(diagnostics) or any(marker in line for marker in markers):
            summary.append(line)

    return "\n".join(summary) if summary else "(see full check_marginal_apy.py output)"


def format_telegram_summary(
    pos_out: str,
    ts: str,
    *,
    positions_returncode: int = 0,
) -> str:
    """Format the compact operator summary from a positions.py result.

    The depth-walked line is intentionally optional: positions.py suppresses
    it when the book is tight, so absence is not an unavailable-check error.
    A failed positions subprocess is handled first and never gets a financial
    cost/MTM summary, even if it happened to emit partial stdout.
    """
    if positions_returncode != 0:
        return (
            f"polyclaude status {ts}\n"
            f"PM position check failed: exit {positions_returncode}\n"
            "realizable unavailable (positions check failed)\n"
            "(full report via scripts/polyclaude_status.py)"
        )
    if pos_out.lstrip().startswith(("[ERR", "[TIMEOUT", "[EXCEPTION")):
        return (
            f"polyclaude status {ts}\n"
            "PM position check failed: positions script error\n"
            "realizable unavailable (positions check failed)\n"
            "(full report via scripts/polyclaude_status.py)"
        )

    total_match = _OPEN_TOTAL_RE.search(pos_out)
    if total_match:
        lines = [
            f"polyclaude status {ts}",
            f"PM cost ${total_match.group(1)} mtm ${total_match.group(2)}",
        ]
    elif pos_out.strip() == "(no open positions)":
        lines = [f"polyclaude status {ts}", "PM positions: no open positions"]
    else:
        lines = [
            f"polyclaude status {ts}",
            "PM cost/mtm unavailable (positions output missing OPEN TOTAL)",
        ]
    real_match = _REALIZABLE_RE.search(pos_out)
    if real_match:
        lines.append(
            f"realizable ${real_match.group(1)} "
            "(depth-walked, NET of taker fees)"
        )
    else:
        unavailable = re.search(
            r"^\(realizable check unavailable:[^\n]+\)$", pos_out, re.MULTILINE
        )
        if unavailable:
            lines.append(unavailable.group(0))
    lines.append("(full report via scripts/polyclaude_status.py)")
    return "\n".join(lines)


def send_telegram_message(message: str) -> tuple[bool, str]:
    """Send one Telegram message and return success plus a failure detail."""
    try:
        result = subprocess.run(
            [".venv/bin/python", "scripts/telegram.py", "msg", message],
            cwd=REPO_ROOT, timeout=15,
        )
    except Exception as e:
        return False, str(e)
    returncode = result.returncode
    if returncode:
        return False, f"exit {returncode}"
    return True, ""


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
    print(summarize_hurdle_output(out))

    # 3. Watchlist
    print("\n## Watchlist hits (12 candidates)")
    out = run_script(["scripts/watchlist_monitor.py", "--hits-only"], timeout=30)
    print(out if out.strip() else "(no triggers hit)")

    if not args.quick:
        # 4. HLE resolving source. The public page's server-rendered table is
        # stale; source_freeze_check reads the API that populates the actual
        # resolving chart and compares it with a pre-market raw archive.
        print("\n## HLE resolving chart (live API vs Jul-3 pre-market archive)")
        print(run_script([
            "scripts/source_freeze_check.py",
            "--url", "https://agi.safe.ai/",
            "--since", "20260703",
            "--expect", "gpt-6,gemini",
            "--brief",
        ], timeout=90))

        # 5. UMA
        print("\n## UMA status check")
        print(run_script(["scripts/uma_status_check.py"], timeout=120))

        # 6. Kelly portfolio
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

        # 6b. Brownian-bridge fair-value
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

    # 7. News alerts (last 6h)
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
        positions_ok = True
        try:
            # Compact line for tick summary
            try:
                r = subprocess.run([".venv/bin/python", "scripts/positions.py"],
                                   cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)
                positions_ok = r.returncode == 0 and not r.stdout.lstrip().startswith(
                    ("[ERR", "[TIMEOUT", "[EXCEPTION")
                )
                tg_msg = format_telegram_summary(
                    r.stdout,
                    ts,
                    positions_returncode=r.returncode,
                )
            except subprocess.TimeoutExpired:
                positions_ok = False
                tg_msg = format_telegram_summary("", ts, positions_returncode=124)
            except Exception:
                positions_ok = False
                tg_msg = format_telegram_summary("", ts, positions_returncode=1)
            sent, detail = send_telegram_message(tg_msg)
            if sent:
                print("(Telegram summary sent)")
            else:
                print(f"(Telegram send failed: {detail})")
                return 1
            if not positions_ok:
                return 1
        except Exception as e:
            print(f"(Telegram send failed: {e})")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
