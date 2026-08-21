"""Mutation-test the money-math suite: does it actually discriminate?

Reintroduces each historical money bug and asserts the suite goes RED. Run after
touching any pricing code, and add a mutant whenever a new class of bug is fixed.

WHY (2026-08-20): a passing suite proves nothing about the bugs it cannot see.
First run, three of six mutants SURVIVED — including the gas-as-profit bug fixed
an hour earlier, whose regression guard I had just written. Causes, all invisible
to a green run: (a) the whole realized-split block sat BELOW the sys.exit verdict,
so its checks ran and were never evaluated (twice — same cat >> mistake); (b) every
numeric fee case used bps=1000, so hardcoding 0.10 passed; (c) the unsorted-book
test consumed both levels, and a full sweep totals the same in any order.
Fixes: verdict moved to an atexit hook so it cannot be stranded by an append, plus
discriminating cases. Restoring the file is in a finally block — a crash mid-run
must not leave a mutated script on disk.
"""
import subprocess, pathlib, shutil, sys

REPO = pathlib.Path("/home/polyclaude/polyclaude")
MUTS = [
    ("pm_fees.py",  'return float(bps) / 10000.0',        'return 0.10'),                    # ignore per-market fee
    ("pm_fees.py",  'return fee_rate(market) * min(price, 1.0 - price)',
                    'return fee_rate(market) * price'),                                       # drop edge-awareness
    ("book_walk.py",'levels = sorted(bids or [], key=lambda x: -float(x["price"]))',
                    'levels = bids or []'),                                                   # trust input order
    ("book_walk.py",'fee = fee_per_share(market, avg_fill) * float(size) if gross > 0 else 0.0',
                    'fee = 0.0'),                                                             # the fee-free walk bug
    ("discover_markets.py",'cost = p_buy + pm_fees.fee_per_share(market, p_buy)',
                    'cost = p_buy * (1 + pm_fees.fee_per_share(market, p_buy))'),             # multiplicative fee
    ("bankroll.py", '"realized": (total - gas_usd - ref) - unreal_mid',
                    '"realized": (total - ref) - unreal_mid'),                                # gas booked as profit
    ("book_walk.py",'if maker_px is not None:\n        return maker_px, 0.0',
                    'if False:\n        return maker_px, 0.0'),                               # maker judged on taker cost (2026-08-18 gap)
]
results = []
for fname, old, new in MUTS:
    f = REPO / "scripts" / fname
    orig = f.read_text()
    if orig.count(old) != 1:
        results.append((fname, old[:38], "ANCHOR-MISS")); continue
    try:
        f.write_text(orig.replace(old, new))
        r = subprocess.run([str(REPO/".venv/bin/python"), str(REPO/"tests/test_money_math.py")],
                           capture_output=True, text=True, timeout=120, cwd=str(REPO))
        results.append((fname, old[:38], "CAUGHT" if r.returncode != 0 else "*** SURVIVED ***"))
    finally:
        f.write_text(orig)
for fn, snip, verdict in results:
    print(f"  {verdict:18} {fn:22} {snip}")
print("\nSURVIVED = the suite cannot detect that bug.")
