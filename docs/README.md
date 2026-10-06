# Performance chart

Static HTML, CSS and JavaScript. No build, framework, external fonts, tracking,
chart library or paid service. The chart reads the three CSVs in this directory.
Only this directory is intended for GitHub Pages publication.

## View and publish

Live chart: [philippmerz.github.io/polyclaude](https://philippmerz.github.io/polyclaude/).
GitHub Pages publishes `main /docs`; each normal push to main updates the
site and CSVs. The Oct-6 history publication was verified at 09:19 UTC:
all six site/data files returned HTTP 200 and matched the repository byte
for byte. When changing JavaScript or CSS compatibility, update their version
query in `index.html` so a browser uses the matching assets.

Local preview from the repository root:

```bash
python3 -m http.server 8765 --directory docs
```

Open `http://localhost:8765`.

## Append an observation

Append one row to `performance.csv` after an existing portfolio check, using
its recorded values. Keep rows in increasing UTC time order; preserve the
historical rows. No extra market requests are needed to maintain the chart.
Use the current CSV header when writing a row, including blank optional cells.

| Column | Meaning |
|---|---|
| `timestamp_utc` | ISO UTC time, e.g. `2026-10-04T18:07:00Z` |
| `timestamp_kind` | `second`, `minute`, `check_window`, or `day` |
| `trading_capital_usd` | Cumulative external trading contributions from the capital ledger |
| `total_mark_usd` | Recorded gas-inclusive account aggregate; blank for early trading-only observations |
| `gas_usd` | Separately funded gas-token value in that same snapshot |
| `pm_mark_usd` | PM midpoint value used in the account snapshot |
| `pm_depth_usd` | PM recorded bid-depth value after trading fees |
| `settled_pnl_usd` | Reported cumulative accounting residual; not an independently audited cash-profit series |
| `source` | Public financial record path and start line, e.g. `notes/journal.md:23522` |
| `source_commit` | Optional full commit SHA for an older README/source version |
| `note` | Precision, quote timing, provenance and accounting limitations |
| `reported_trading_mark_usd` | Optional complete non-gas trading subtotal from the same observation; never a PM-only subtotal once both sleeves were funded |
| `gas_kind` | `recorded`, `rounded_identity`, or `missing` |
| `gas_rounding_bound_usd` | Rounding-only bound for reconstructed gas; not a bound on provider, timing or accounting uncertainty |

Minute timestamps use `:00` seconds as a plotting anchor. Scheduled windows
use their documented start time and `check_window`; the UI labels them with
`~`. Date-only reports use midnight with `day`, visibly labeled as date only.
These anchors are not invented exact quote times. The Oct-6 archive review
expanded 36 observations to **130**, spanning Apr 25–Oct 6 and 118 of 165
calendar dates. There are 123 recorded account marks, 50 trading midpoints
and 43 indicative trading-depth estimates. Seven Apr 25–29 values sum
contemporaneous PM positions and cash while the crypto sleeve was unfunded;
their gas-inclusive totals remain unknown. Account aggregates begin Jun 10.

Sixteen gas values are explicitly marked `rounded_identity`, including the
ten previously blank September gas cells. The historical accounting function
and each snapshot's published inputs support the reconstruction:

```text
gas = total − trading contributions − reported accounting residual
      − marked unrealized P&L
marked unrealized P&L = PM midpoint − PM cost
```

These are estimates, visibly prefixed with `~`; rounding alone contributes
up to ±$0.02, or ±$0.015 for the Sep-4 three-input identity. No gas price is
borrowed from another observation. The residual is not an audited cash ledger;
this algebra does not make it one. The input table, historical function
revisions and immutable source hashes are in the
[archive audit](../research/2026-10-06-performance-history.json).

Apr 30–Jun 9 and six later dates lack a supported complete account valuation.
Early manual totals with unclear sleeve/gas scope are excluded. Cache-only
records preserve reported aggregate values and timestamps, but not component
breakdowns or valuation warnings, so their completeness cannot be independently
established. Known failed captures were excluded or replaced with a separately
dated later observation. Connected points are observations, not reconstructed
daily quotes or certified historical NAV.

Use blank cells for unavailable figures, never zero or a different-time quote.
Do not mix balances from different snapshots to manufacture a full valuation.
The graph computes:

```text
trading midpoint = total mark − funded gas
                   OR a documented complete non-gas trading subtotal
trading depth = total mark − funded gas − PM midpoint + PM depth
return % = (trading value / external trading contributions − 1) × 100
```

This captures reserves and open losses along with gains. Sequential depth
estimates are not guaranteed liquidation proceeds and omit routing/withdrawal
costs. VM/API costs remain unreconciled and excluded. Returns are contribution
ratios, not time-weighted or money-weighted returns. The gas-inclusive account
series is available in USD only and is never divided by trading capital to
claim a return.

`contributions.csv` records $70 on Apr 25 and a further $100 on Apr 29. The
first uses a date-only anchor; the second uses the archive's approximate
19:55 UTC funding acknowledgment, not an exact on-chain transfer time. The
Apr-29 02:00 and 14:00 observations still use $70. Internal bridges, Aave
moves and sleeve transfers are not contributions. Future external flows must
update the capital ledger, contribution CSV and observation denominator
together; raw value changes then include those flows. The viewer checks that
observations agree with the contribution steps.

`benchmarks.csv` contains validated contribution-timed SPY observations only.
Use the market session's date, not retrieval date. Current close anchors are
20:00 UTC for the documented regular US sessions. The Sep 24 diagnostic
reconstruction is deliberately absent because the strict run failed. CSV source
links identify the actual records. No missing daily benchmark prices are filled.

Run the focused checks with:

```bash
node --test tests/performance_chart.test.mjs
```
