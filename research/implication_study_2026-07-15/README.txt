Cross-event implication study 2026-07-15 (research agent, ~40min)
QUESTION: do logically-related markets in DIFFERENT events show executable
consistency violations (new scanner class), or is it midpoint artifact again?
VERDICT: ARTIFACT/EMPTY — do not build the scanner. Full memo in the orchestrator
transcript (2026-07-15); numbers reproducible from these files.

Pipeline: crawl_open.py (gamma keyset, closed=false, vol>=500 -> 12,773 mkts, ~50s)
  -> discover_pairs.py (4 template classes + dup/complement, polarity-aware; 4,575 pairs)
  -> walk_books.py (live CLOB walk on all 160 mid/quote-flagged pairs; fee-aware
     box economics, takerBaseFee bps x min(p,1-p))
  -> persistence.py (30d hourly mid history on liquid TRUE pairs)

Key result: 160 pairs walked -> 136 dead on book, 17 dust, 6 mechanical "executable"
of which 4 semantically FALSE (Emmy category-name "or"; Sao Tome runoff; leader-out
event EDITIONS with different lists), 2 true but 0.11%/0.26% ROI dust locks.
True liquid families (31 nom/pres + 30 WS=>LCS + 34 win=>ballot) never violate >0.5pp.
True dup pairs (15) diverge on MIDS persistently (Maxwell 73% of hours >1pp, episodes
up to 298h) but books were dead at every live check. 93% of universe carries
takerBaseFee=1000 (10% x min(p,1-p)) — kills sub-3pp gaps structurally.
NEW failure mode catalogued: same question text != same proposition (event editions,
criteria deltas: IPO-definition, listed-leader sets). Verify description before any
cross-event "arb".
Files: pairs_violating.jsonl (162 flagged pairs), book_results.jsonl (walked economics),
persistence.json. Bulk crawl (13MB) + full pair file (5.5MB) were /tmp-ephemeral.
