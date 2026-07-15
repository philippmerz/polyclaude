Instance-mispricing sweep 2026-07-15 (strict/loose criteria vs colloquial pricing).
Pipeline: crawl_sweep.py (gamma keyset, 7761 seen -> 3324 kept: vol>=3k, 20-300dte, binary, non-sports, uma clean)
 -> score_pass1.py (marker scoring, 2243 scored; 1081 auto-killed p<=0.03/>=0.97)
 -> manual judgment pass over top-150 + directional scans (~190 reviewed, 44 full-description reads, 10 web checks)
 -> walk_books.py (live CLOB both sides, 14 finalists) -> shortlist.jsonl (11 reportable).
Full universe/scored jsonl left in /tmp/instance_sweep/ (6MB+, not copied). top150.txt = mechanical triage view.
