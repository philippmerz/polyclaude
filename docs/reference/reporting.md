# Portfolio reporting

Status: CURRENT policy, consolidated 2026-09-09. Open for performance, P&L or valuation questions; current numbers belong in the README dashboard, not here.

## Source hierarchy

1. `scripts/bankroll.py`: **only** authoritative aggregate marked total across both wallets, PM positions, Aave aTokens, pUSD, raw stables and gas tokens. Preserve unvalued/error warnings. Never assemble a competing total by hand.
2. `scripts/positions.py`: PM quantities, cost, midpoint and indicative fee/depth proceeds. `clob_v2.py orders`: authenticated order inventory; it is not a historical-fill ledger.
3. `notes/capital_ledger.md`: external contributions/withdrawals; reference trading capital $170, gas separately.
4. README: dated last-check summary, not an oracle. Journal contains evidence, times and limitations. Cache freshness is not guaranteed by its existence.

## Headline order

- Whole-account indicative net liquidation versus contributed capital.
- Gas-token value separately; trading comparison excluding gas. Deduct VM/other operating costs only if measured, otherwise explicitly say **before operating costs**. No VM expansion assumed.
- Authoritative marked bankroll alongside, explaining the midpoint-to-bid gap.
- Settled realized P&L and open P&L as components, never a substitute for the whole-account result.

For a consistent snapshot:
`indicative whole-account net liq = bankroll TOTAL − its PM midpoint component + PM fee/depth proceeds`.

This replaces one component, not a new independently assembled bankroll. Disclose sequential timing, rounding, partial/zero depth, unavailable components, transfer/withdrawal costs and any unverified book identity/freshness. A full numerical walk does not prove simultaneous execution. Do not silently value missing depth at zero or at midpoint.

## Comparisons that are not account value

- Raw fair value depends on uncertain priors; even pessimistic-bound stress tests do not establish calibration.
- Win-assumed carry/gross APY ignores losing outcomes; use honest probabilities for expected return and compare with live Aave yield.
- “Resolve every market in its current majority direction” is a **scenario**, not expected value or net liquidation. It jumps discontinuously at 50%, assumes every favored outcome wins and ignores dependence. If requested, label the rule (including ties) and keep it separate from the headline.
- Grouped positions require joint state payouts and complete fee-aware exits; never sum independent action recommendations for protected member legs.
- Entry-cost cap breaches caused only by mark/bankroll drift do not automatically require a forced exit.

## Weekly and decision reporting

`notes/pnl_weekly.md` is append-only, newest report at the bottom. Its historical date headings use both `#` and `##`; do not declare it stale by searching only one heading level. Include marked and indicative liquidation values, external flows/costs, material decisions, forecast errors and the next catalyst.

Preserve original forecasts, timestamps and entry prices in `notes/decisions.json` / `notes/shortdated_ledger.json`; add actual outcomes rather than rewriting predictions. Forecast rows, matched-price rows and independent resolved events are distinct sample counts. Missing quotes remain missing; software tests passing does not validate the empirical thesis.

Read-only grading diagnostics: `.venv/bin/python scripts/decisions.py pending` and `summary`; inspect `ledger_calibration.py --help` before selecting a mode that can write.
