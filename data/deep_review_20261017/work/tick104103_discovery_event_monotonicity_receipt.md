# Event monotonicity scan receipt — tick 104103

Command: `.venv/bin/python scripts/event_monotonicity_scan.py`

Terminal observations: 1,397 events fetched; 1,097 multi-market events inspected; zero midpoint violations ≥1.0 percentage point and zero provisional candidates after the batched CLOB walk. Pagination attempted/succeeded 15/15, no failures, stop reason `max_pages`; coverage is explicitly incomplete. This zero applies only to the scanned slice and default filters (event volume ≥$1,000; both legs ≥$500 24h volume).

This receipt summarizes captured stdout; the scanner did not persist a standalone raw result file.
