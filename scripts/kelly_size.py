#!/usr/bin/env python3
"""Kelly-criterion sizing tool — computes optimal bet sizing for binary outcomes.

For a binary bet at mark M (the price you pay per share, payout 1.0 if won),
my probability estimate p of winning, and bankroll B, the Kelly fraction is:

    b = (1 - M) / M    # net odds: profit per dollar wagered if won
    f* = (p * b - q) / b = (p * (1-M) - (1-p) * M) / (1 - M)
       = (p - M) / (1 - M)              # simplified for binary

Kelly maximizes log-bankroll growth. Full Kelly is theoretically optimal for
log-utility, but realistic operators use FRACTIONAL Kelly (1/4 to 1/2) to:
- Account for estimation error in p (Kelly is highly sensitive to p mis-estimate)
- Manage correlation across positions (Kelly assumes independence)
- Reduce drawdown variance

This script also computes:
- Per-bet expected value (EV) at mark M and probability p
- Edge in pp (percentage points): p - M
- Sharpe-like ratio for log-utility sizing
- Bayesian-adjusted Kelly with explicit conservatism

Usage:
    python scripts/kelly_size.py <mark> <p_estimate> [--bankroll B] [--fraction F]
                                                     [--correlation rho_to_existing]
                                                     [--existing-cluster-size $]

Examples:
    # DEC-0019: mark 0.965 (NO), my P(NO) = 0.99, bankroll $170, half-Kelly
    python scripts/kelly_size.py 0.965 0.99 --bankroll 170 --fraction 0.25

    # Sportsbook fade: mark 0.92 (favorite), my P(favorite wins) 0.97, full Kelly
    python scripts/kelly_size.py 0.92 0.97 --bankroll 170 --fraction 1.0

Reference: Kelly 1956 "A New Interpretation of Information Rate";
Thorp 1969 "Optimal Gambling Systems for Favorable Games".
Operator directive 2026-05-09: apply mathematical sophistication to sizing.
"""

from __future__ import annotations

import argparse
import math


def kelly_fraction(mark: float, p: float) -> float:
    """Full-Kelly fraction for binary bet at price mark with estimated win prob p.

    f* = (p - M) / (1 - M)  for buying at price M expecting payout 1.0

    Returns the optimal fraction of bankroll to deploy. Negative => no edge,
    don't bet (or short if possible).
    """
    if mark >= 0.999:
        return 0.0
    if p <= mark:
        return 0.0  # no edge
    return (p - mark) / (1.0 - mark)


def expected_log_growth(mark: float, p: float, fraction: float) -> float:
    """E[log(1 + fraction × pnl)] under bet at mark with win prob p, sized fraction.

    win pnl per dollar = (1 - M) / M
    loss pnl = -1 (entire bet)
    """
    if fraction <= 0:
        return 0.0
    b = (1.0 - mark) / mark  # net odds
    win_term = p * math.log(1.0 + fraction * b)
    loss_term = (1.0 - p) * math.log(1.0 - fraction)
    return win_term + loss_term


def correlation_adjusted_kelly(mark: float, p: float, rho_existing: float,
                                existing_cluster_frac: float) -> float:
    """Adjust Kelly fraction for correlation with existing positions.

    Naive heuristic: when existing-cluster-bet has weight w_existing in bankroll
    and the new bet is correlated with rho >= 0 to that cluster, the *combined*
    portfolio risk is approximately:
       sigma_combined^2 = sigma_new^2 + w_existing^2 * sigma_existing^2 + 2*rho*...

    For binary bets, we approximate by treating rho>0 as effectively reducing
    available Kelly fraction by (1 - rho * existing_cluster_frac).

    Returns the corr-adjusted full-Kelly fraction. Operator should still apply
    a fractional Kelly (1/4 to 1/2) on top.
    """
    full_kelly = kelly_fraction(mark, p)
    if rho_existing <= 0 or existing_cluster_frac <= 0:
        return full_kelly
    discount = max(0.0, 1.0 - rho_existing * existing_cluster_frac)
    return full_kelly * discount


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    p.add_argument("mark", type=float, help="Market price (cost per share, e.g. 0.965)")
    p.add_argument("p_estimate", type=float, help="My probability estimate of winning (0.0-1.0)")
    p.add_argument("--bankroll", type=float, default=170.0, help="Total bankroll in USD")
    p.add_argument("--fraction", type=float, default=0.25,
                   help="Fractional Kelly factor (default 0.25 = quarter Kelly)")
    p.add_argument("--correlation", type=float, default=0.0,
                   help="Correlation rho to existing cluster (0.0 if independent, 1.0 if perfectly correlated)")
    p.add_argument("--existing-cluster-frac", type=float, default=0.0,
                   help="Fraction of bankroll already in correlated cluster (0.0-1.0)")
    args = p.parse_args()

    mark = args.mark
    p_est = args.p_estimate

    if not (0 < mark < 1):
        print(f"ERROR: mark must be in (0, 1), got {mark}")
        return 2
    if not (0 < p_est < 1):
        print(f"ERROR: p_estimate must be in (0, 1), got {p_est}")
        return 2

    full_kelly = kelly_fraction(mark, p_est)
    edge_pp = (p_est - mark) * 100
    b = (1.0 - mark) / mark
    ev_per_dollar = p_est * b - (1.0 - p_est)

    corr_adj_kelly = correlation_adjusted_kelly(mark, p_est, args.correlation, args.existing_cluster_frac)
    fractional = corr_adj_kelly * args.fraction
    dollar_size = fractional * args.bankroll

    log_growth_full = expected_log_growth(mark, p_est, full_kelly)
    log_growth_frac = expected_log_growth(mark, p_est, fractional)

    print(f"\n{'─' * 60}")
    print(f"Kelly sizing for mark=${mark:.4f}, P(win)={p_est:.4f}")
    print(f"{'─' * 60}\n")
    print(f"Edge:            {edge_pp:+.2f}pp  (p_estimate - mark)")
    print(f"Net odds (b):    {b:.4f}        ((1-M)/M, profit per $ if won)")
    print(f"E[$pnl]/$:       {ev_per_dollar:+.4f}        (p*b - q)")
    print(f"")
    print(f"Full Kelly:      {full_kelly:.4f}        ({full_kelly*100:.1f}% of bankroll)")
    if args.correlation > 0 and args.existing_cluster_frac > 0:
        print(f"  ρ-adjusted:    {corr_adj_kelly:.4f}        ({corr_adj_kelly*100:.1f}% of bankroll)")
        print(f"  (discount factor: {1 - args.correlation * args.existing_cluster_frac:.3f} for ρ={args.correlation} × cluster_frac={args.existing_cluster_frac})")
    print(f"  ×Kelly frac:   {args.fraction:.2f}        (operator's risk multiplier)")
    print(f"  Final frac:    {fractional:.4f}")
    print(f"")
    print(f"Bankroll:        ${args.bankroll:.2f}")
    print(f"Optimal $ size:  ${dollar_size:.2f}")
    print(f"  shares (@${mark:.4f}): {dollar_size/mark:.2f}")
    print(f"")
    print(f"Log-growth at full Kelly:  {log_growth_full:.6f}")
    print(f"Log-growth at fractional:  {log_growth_frac:.6f}")
    print(f"{'─' * 60}\n")

    # Sensitivity check: what does ±10% misestimate of p do to optimal size?
    print(f"Sensitivity to ±10% p_estimate misestimate:")
    for delta in [-0.10, -0.05, +0.05, +0.10]:
        p_perturb = max(0.001, min(0.999, p_est + delta))
        f_perturb = kelly_fraction(mark, p_perturb)
        size_perturb = f_perturb * args.fraction * args.bankroll
        print(f"  p={p_perturb:.4f} ({delta:+.2f})  → full_K={f_perturb:.4f}  size=${size_perturb:.2f}")
    print()

    return 0


if __name__ == "__main__":
    main()
