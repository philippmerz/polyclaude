# Macro scan receipt — tick 104103

Command: `.venv/bin/python scripts/macro_pm_scan.py --no-consensus --days 60`

Terminal observations: 8 markets passed the $30,000 24h-volume threshold. The displayed rows were the four October Fed outcome contracts (Oct 2026 meeting, 8.7 days in the captured output), two December Fed outcomes (50.5 days), and two Bank of Canada outcomes (7.5 days). No derivatives consensus was requested. The scanner uses up to eight pages and its stdout did not report page counts or failures, so coverage beyond these results is unknown.

This receipt summarizes captured stdout; it is not a raw API response. Carry fields are not probability or edge estimates.
