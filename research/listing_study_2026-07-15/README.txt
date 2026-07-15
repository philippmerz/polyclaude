NEW-LISTING MISPRICING STUDY — 2026-07-15 (data + scripts; memo delivered in agent output)

Scripts (run with /home/polyclaude/polyclaude/.venv/bin/python3):
  crawl_keyset.py    — gamma /markets/keyset crawler (after_cursor pagination; offset endpoint caps at ~2000)
  pull_cohort.py     — first-pass offset puller (superseded by crawl_keyset.py)
  fetch_paths.py     — CLOB prices-history anchored at acceptingOrdersTimestamp; snapshots at fixed ages + life fractions
  analyze.py         — calibration by age, drift, divergence, hindsight winner cost, family/volume slices
  exec_check.py      — data-api /trades early-window taker fills for mid-priced listings

Data:
  cohort_apr_may.jsonl   — 200k closed vol>=1k markets listed 2026-04-01..05-26 (keyset crawl, capped)
  paths.jsonl            — 1100 sampled price paths (833 usable non-series life>=120h + 170 series + rest)
  exec_trades.jsonl      — 260 mid-priced (p6h in [.25,.75]) listings with early-window taker trades
  census_jul_open/closed.jsonl — ALL 97,356 markets listed Jul 8-15 (12,170/day)
  census_all.jsonl / census_apr_closed.jsonl — ALL 61,708 markets listed Apr 1-7 (survivorship)
  live_book_check.json   — live CLOB books on 60 one-off listings <=72h old
  analysis_main.txt      — full analyzer output (N=833)

Key facts (see agent memo for full verdict):
  - prices-history = sampled QUOTE MIDPOINTS, not trades (>=718 points on a $297-volume market)
  - one-off Yes/No listings resolve YES ~23% (<=34% survivorship bound) while books open at mid~0.5
  - ECE on mids: 22.4pp (T+1h) -> 9.0pp (72h); matched diff +13.3pp CI [9.4,16.9] — REAL ON MIDS
  - BUT 95% of mid-priced listings have ZERO trades in hour 1; 82% zero in 6h (exec sample N=260)
  - early YES takers: -16.8c/share (N=58 mkts); early cheap-NO fills adversely selected (-EV 0-6h)
  - fees on new listings 2026: taker-only, rate x min(p,1-p): politics 4% / sports 5% / crypto 7%
  - feed: 12,170 listings/day; ~237 one-off/day; ~25% of young one-offs have spread<=5c & $15 depth
