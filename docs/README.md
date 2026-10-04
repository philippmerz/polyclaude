# Performance chart

Static HTML, CSS and JavaScript. No build, framework, external fonts, tracking,
chart library or paid service. The chart reads the two CSVs in this directory.
Only this directory is intended for GitHub Pages publication.

## View and publish

Local preview from the repository root:

```bash
python3 -m http.server 8765 --directory docs
```

Open `http://localhost:8765`. In GitHub repository **Settings → Pages**, use
**Deploy from a branch → main → /docs**. Then each push to main publishes the
updated CSV and site at `https://philippmerz.github.io/polyclaude/`.
GitHub API/administration authentication is needed to change that setting;
the VM's existing Git SSH access alone does not supply it.

## Append an observation

Append one row to `performance.csv` after an existing portfolio check, using
its recorded values. Keep rows in increasing UTC time order; preserve the
historical rows. No extra market requests are needed to maintain the chart.

| Column | Meaning |
|---|---|
| `timestamp_utc` | ISO UTC time, e.g. `2026-10-04T18:07:00Z` |
| `timestamp_kind` | `second`, `minute`, `check_window`, or `day` |
| `trading_capital_usd` | Cumulative external trading contributions from the capital ledger |
| `total_mark_usd` | Authoritative whole-account marked bankroll |
| `gas_usd` | Separately funded gas-token value in that same snapshot |
| `pm_mark_usd` | PM midpoint value used in the account snapshot |
| `pm_depth_usd` | PM recorded bid-depth value after trading fees |
| `settled_pnl_usd` | Reported cumulative accounting residual; not an independently audited cash-profit series |
| `source` | Public financial record path and start line, e.g. `notes/journal.md:23522` |
| `source_commit` | Optional full commit SHA for an older README/source version |
| `note` | Precision, quote timing, provenance and accounting limitations |

Minute timestamps use `:00` seconds as a plotting anchor. Scheduled windows
use their documented start time and `check_window`; the UI labels them with
`~`. Date-only reports use midnight with `day`, visibly labeled as date only.
These anchors are not invented exact quote times. The 27 initial observations
cover Sep 8–Oct 4; 17 have all fields needed for the ex-gas depth calculation.
Ten gas values are absent from the public records and remain blank. Two
missing daily snapshots were replaced with complete same-day observations.

Use blank cells for unavailable figures, never zero or a different-time quote.
Do not mix balances from different snapshots to manufacture a full valuation.
The graph computes:

```text
trading midpoint = total mark − funded gas
trading depth = total mark − funded gas − PM midpoint + PM depth
return % = (trading value / external trading contributions − 1) × 100
```

This captures reserves and open losses along with gains. Sequential depth
estimates are not guaranteed liquidation proceeds and omit routing/withdrawal
costs. VM/API costs remain unreconciled and excluded. Returns are contribution
ratios, not time-weighted or money-weighted returns. The retained interval has
no external trading capital flows. Future contributions must update the ledger
and CSV together; raw value changes then include those flows.

`benchmarks.csv` contains validated contribution-timed SPY observations only.
Use the market session's date, not retrieval date. Current close anchors are
20:00 UTC for the documented regular US sessions. The Sep 24 diagnostic
reconstruction is deliberately absent because the strict run failed. CSV source
links identify the actual records. No missing daily benchmark prices are filled.

Run the focused checks with:

```bash
node --test tests/performance_chart.test.mjs
```
