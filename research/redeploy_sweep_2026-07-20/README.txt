Redeploy sweep 2026-07-20 (~$17 pUSD to deploy; SDCC Jul 22-26 = 2d out).
Scripts (reuse of 2026-07-15 crawlers, adapted):
  crawl_short.py  - gamma keyset, closed=false, vol>=1000, binary, dte 3-45d, excl sports/crypto/weather/election-day. -> universe_short.jsonl (805 rows)
  score_pass1.py  - strict/loose marker scoring -> scored_short.jsonl (406 scored)
  fetch_sdcc.py   - targeted SDCC satellite fetch (ignores vol floor) -> sdcc_finalists.jsonl (36 SDCC markets)
  walk_sdcc.py    - live CLOB book walk, $8 fill, fee-adjusted -> sdcc_books.jsonl
Outputs:
  shortlist.jsonl     - ranked finalists w/ criteria-gap, facts, fair-p, edge, kill-risk
  sdcc_finalists.jsonl- all 36 SDCC markets w/ prices+descriptions
  sdcc_books.jsonl    - live books for top-3 SDCC finalists
Top edge: Marvel-Studios-announce YES @0.67 (net 0.703, depth $384) - confirmed Sat Hall H 'what's next' Feige panel vs loose new-project criteria, ~20pp.
Held (NOT re-surfaced): Prime-Video-SDCC YES, SpaceX-IPO YES, MacBook-2026 NO, GPT-6 NO, Greenland NO, Satoshi NO.
