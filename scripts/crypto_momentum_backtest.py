#!/usr/bin/env python3
"""Time-series momentum backtest for crypto — is there a systematic DIRECTIONAL edge?

Operator asked (2026-06-02) about directional crypto/tokenized-asset bets. Discretionary
directional VIEWS aren't an edge (liquid crypto is efficient). The one directional approach
with a documented historical crypto edge is time-series momentum / trend-following. This tests
it honestly (per the favorite-fade lesson: don't dismiss on prior, check cheaply).

Signal: SMA crossover — long when close > N-day SMA, else flat (long-only; shorting crypto is
riskier and borrow/funding isn't free). Lookahead-safe: position is set from data up to t-1 and
earns return t. Costs: --cost bps charged on each position flip. Compares strategy CAGR / Sharpe /
maxDD / trade-count vs buy-and-hold.

CLI: crypto_momentum_backtest.py [--coins bitcoin,ethereum] [--days 1095] [--cost-bps 10]
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta

import httpx


def fetch_daily(coin: str, days: int) -> list[float]:
    """Daily closes from Hyperliquid candleSnapshot (reliable, no auth). coin = HL symbol (BTC/ETH/SOL)."""
    start = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp() * 1000)
    r = httpx.post("https://api.hyperliquid.xyz/info",
                   json={"type": "candleSnapshot", "req": {"coin": coin, "interval": "1d", "startTime": start}},
                   timeout=30).json()
    if not isinstance(r, list):
        return []
    return [float(c["c"]) for c in r]


def stats(daily_rets: list[float]) -> tuple[float, float, float]:
    """CAGR, annualized Sharpe, max drawdown from a list of daily simple returns."""
    if not daily_rets:
        return 0.0, 0.0, 0.0
    import statistics as st
    eq = 1.0
    peak = 1.0
    mdd = 0.0
    for r in daily_rets:
        eq *= (1 + r)
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    yrs = len(daily_rets) / 365.0
    cagr = eq ** (1 / yrs) - 1 if yrs > 0 and eq > 0 else -1.0
    mean = st.mean(daily_rets)
    sd = st.pstdev(daily_rets) or 1e-9
    sharpe = (mean / sd) * (365 ** 0.5)
    return cagr, sharpe, mdd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coins", default="bitcoin,ethereum")
    ap.add_argument("--days", type=int, default=1095)
    ap.add_argument("--cost-bps", type=float, default=10.0)
    ap.add_argument("--lookbacks", default="20,50,100")
    args = ap.parse_args()
    cost = args.cost_bps / 10000.0
    lbs = [int(x) for x in args.lookbacks.split(",")]

    for coin in args.coins.split(","):
        px = fetch_daily(coin.strip(), args.days)
        if len(px) < max(lbs) + 30:
            print(f"{coin}: insufficient data ({len(px)})", file=sys.stderr)
            continue
        rets = [(px[i] / px[i - 1] - 1) for i in range(1, len(px))]
        # buy & hold
        bh = stats(rets)
        print(f"\n=== {coin} ({len(px)}d) ===")
        print(f"{'strategy':>16} {'CAGR':>8} {'Sharpe':>7} {'maxDD':>7} {'trades':>7}")
        print(f"{'buy&hold':>16} {bh[0]*100:>7.0f}% {bh[1]:>7.2f} {bh[2]*100:>6.0f}% {'-':>7}")
        for lb in lbs:
            pos = []  # position for day i (0/1), set from prices up to i-1
            for i in range(1, len(px)):
                if i < lb:
                    pos.append(0)
                    continue
                sma = sum(px[i - lb:i]) / lb  # uses px[i-1] as latest, no lookahead on ret[i]
                pos.append(1 if px[i - 1] > sma else 0)
            strat = []
            trades = 0
            for k in range(len(rets)):
                p = pos[k]
                r = p * rets[k]
                if k > 0 and pos[k] != pos[k - 1]:
                    r -= cost
                    trades += 1
                strat.append(r)
            cg, sh, dd = stats(strat)
            print(f"{'SMA-' + str(lb) + ' long/flat':>16} {cg*100:>7.0f}% {sh:>7.2f} {dd*100:>6.0f}% {trades:>7}")
    print("\n# long/flat SMA crossover; cost charged per flip. Compare Sharpe + maxDD vs buy&hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
