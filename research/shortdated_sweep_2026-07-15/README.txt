Short-dated (5-20 dte) instance-mispricing sweep, run 2026-07-15/16 UTC night.
Complement to instance_sweep_2026-07-15 (which covered 20-300 dte).
Pipeline: crawl_short.py (gamma keyset, 10,794 seen -> 376 kept: vol>=1k, 5-20dte,
binary, uma-clean, excl sports/series/up-down/crypto-price/weather/election-day)
 -> score_pass1.py (198 scored; 178 auto-killed p<=0.03/>=0.97)
 -> full triage of all 198 + 28 full-description reads
 -> 12 web checks (16 thesis-relevant stories verified, 2 gamma-mid artifacts exposed)
 -> walk_books.py (13 finalists, live CLOB) -> shortlist.jsonl (10 reportable).
Near-miss: moscow-air-traffic-suspended-by-july-31 YES (fair ~0.90, taker net 0.84,
+6pp < 8pp bar; maker at 0.80-0.81 would clear).
Universe/scored jsonl in /tmp/shortdated_sweep/ (not copied, ~1.5MB).
