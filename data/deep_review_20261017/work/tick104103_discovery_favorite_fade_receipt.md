# Favorite-fade scan receipt — tick 104103

Command: `.venv/bin/python scripts/favorite_fade_scan.py`

Terminal coverage: 1,000 active markets fetched across 10/10 pages; stop reason `max_pages`, incomplete. Rough survivors before the book-walk cap: 59; 40 selected for walks; 19 omitted by the cap. All 40 selected had valid books; 12 valid-book favorites fell outside the 0.90–0.98 profile; 28 rows emitted. No missing/invalid favorite books; no batch error. These are only live favorite-price profile candidates at 2–14 days, with no probability, edge, or APY inference. The historical population edge is falsified per scanner documentation.

This receipt summarizes captured stdout; the scanner did not persist a standalone raw result file.
