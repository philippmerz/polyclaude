#!/usr/bin/env python3
"""Bounded thesis review for project-accessible on-chain instruments.

Companion to catalyst_check.py for continuous crypto markets and other named
on-chain instruments. Off-chain stock and personal-brokerage research is retired.
Research must fit the less-than-one-year project horizon and January 2027
assessment. No report or price trigger authorizes a trade.

Examples:
    python scripts/longterm_check.py "Uniswap (UNI)" crypto
    python scripts/longterm_check.py "Aave (AAVE)" crypto --horizon-years 0.2
    python scripts/longterm_check.py "Ostium SPX/USD index exposure" onchain

Logged to notes/longterm_log.md; current candidates in notes/longterm_watchlist.md.
"""

from __future__ import annotations

import argparse
import datetime
import math
import subprocess
import sys
from pathlib import Path

from agent_runtime import run_agent

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = REPO_ROOT / "notes" / "longterm_log.md"


PROMPT_TEMPLATE = """Review a specific on-chain investment opportunity for this project.

Asset: {asset}
Asset type: {asset_type}
Analysis horizon: {horizon_years} years from {today_iso}
Evaluation: start of January 2027; project positions must fit a less-than-one-year holding horizon.

Off-chain stocks and personal-brokerage research are outside this project. Do
not suggest an IBKR/CEX/KYC route, a multi-year allocation, or a recurring review.
A tokenized instrument requires its own identity, legal-access and executable
route evidence; an underlying stock quote is not its token price or liquidity.

Use current primary sources. Verify:
1. Exact token/asset ID, chain, instrument, venue and lawful project access.
   If accessible exposure is unverified, say so; do not substitute an off-chain
   stock recommendation or imply that this repository already supports execution.
2. Current executable buy and sell prices/depth at plausible project size,
   source times, spread, fees, gas, funding, withdrawal and settlement costs.
3. Cyclical position, durable demand and tokenholder/instrument value accrual.
   Protocol adoption or company success alone does not imply holder returns.
4. A dated catalyst capable of changing value before the evaluation. Separate
   facts from inference and model probabilities; a multi-year story is insufficient.
5. Downside, dilution/unlocks, liquidation, custody, counterparty/protocol,
   regulatory, operational and correlated portfolio risks. Downside is not
   bounded merely because price has fallen or a balance sheet looks strong.
6. Explicit terminal scenarios through evaluation, probabilities and uncertainty,
   expected net return and a pessimistic case versus accessible alternatives,
   including same-chain Aave. Do not claim calibration without evidence.
7. Conditional entry/review and thesis-break triggers. A price threshold or
   qualitative score alone cannot authorize an entry; apply portfolio sizing
   and the vetted execution gates in a separate fresh review.

Report only:

## PROJECT THESIS CHECK: {asset}
Date: {today_iso} | Type: {asset_type} | Horizon: {horizon_years}y
### Instrument, access and current executable state
### Cyclical position
### Secular tailwind and holder value accrual
### Catalyst window
### Margin of safety and top risks
### Scenarios through the January 2027 evaluation
### Entry trigger
### Verdict: <SCORE/4> — <WATCH | ENTER | PASS | FOLLOW-UP NEEDED>
Use the four thesis dimensions as a qualitative summary, not an allocation gate.
ENTER means a candidate for fresh agent review, never execution authority.
### Sources
Link the primary evidence supporting each material claim. Identify data gaps.
"""


def main() -> int:
    p = argparse.ArgumentParser(description="Project thesis review for accessible on-chain instruments.")
    p.add_argument("asset", help="Exact on-chain instrument or token to research, e.g., Uniswap (UNI).")
    p.add_argument("asset_type", choices=["crypto", "tokenized-equity", "onchain"],
                   help="Asset class — informs the search/analysis approach.")
    p.add_argument("--horizon-years", type=float, default=0.25,
                   help="Analysis horizon in years, strictly below one (default: 0.25); evaluation remains January 2027.")
    p.add_argument("--profile", choices=["research", "fast"], default="research",
                   help="Model workload profile (default: research).")
    p.add_argument("--effort", default="medium",
                   help="Reasoning effort level (default: medium).")
    p.add_argument("--no-log", action="store_true",
                   help="Skip writing the result to notes/longterm_log.md.")
    args = p.parse_args()
    if not math.isfinite(args.horizon_years) or not 0 < args.horizon_years < 1:
        p.error("project horizon must be finite, positive and less than one year")

    today = datetime.date.today()
    prompt = PROMPT_TEMPLATE.format(
        asset=args.asset,
        asset_type=args.asset_type,
        horizon_years=args.horizon_years,
        today_iso=today.isoformat(),
    )

    print(f"# longterm_check: {args.asset}", file=sys.stderr)
    print(f"# type={args.asset_type} horizon={args.horizon_years}y profile={args.profile}", file=sys.stderr)
    print("# spawning scoped research worker ...", file=sys.stderr)

    try:
        r = run_agent(prompt, profile=args.profile, effort=args.effort, timeout=600)
    except subprocess.TimeoutExpired:
        print("ERROR: research worker timed out after 10 minutes", file=sys.stderr)
        return 3

    if r.returncode != 0:
        print(f"ERROR: research worker exited {r.returncode}", file=sys.stderr)
        print(f"stderr: {r.stderr[:500]}", file=sys.stderr)
        return r.returncode

    output = r.stdout.strip()
    print(output)

    if not args.no_log:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a") as f:
            f.write(f"\n---\n\n## {ts} — longterm_check\n\n")
            f.write(f"**Query:** `{args.asset}` ({args.asset_type}, {args.horizon_years}y horizon)\n\n")
            f.write(output)
            f.write("\n")
        print(f"\n# logged to {LOG_PATH}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
