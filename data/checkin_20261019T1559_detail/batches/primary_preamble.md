# Market context batches

> **Context-only warning:** Context grouping uses exact Gamma event IDs among rows present in this snapshot. The snapshot may omit event siblings, and shared event membership does not prove proposition, criteria, outcome, or settlement equivalence.

Scan kind: `primary`  
Current proof: `c9876622d6a63a7dd8bce735e004e3b13f78195d9fb40ba02e6a1059e387566b`  
Source integrity verified: `True`  
Prior proof: `65e619085754e6193766d730934ec69189a7903ae4745a7967778202b7c20dcb`

Upstream discovery coverage: `{"fetch": {"duplicate_market_rows": 37, "endpoint": "markets", "fetched_market_rows": 963, "malformed_rows": 0, "max_pages": 10, "pages_attempted": 10, "pages_succeeded": 10, "pagination_complete": false, "response_rows": 1000, "stop_reason": "page_cap"}, "filters": {"eligible_before_top": 590, "filter_accounting_complete": true, "filter_rejections": {"horizon": 47, "liquidity": 257, "missing_deadline": 2, "past_deadline": 65, "spread": 2}, "input_markets": 963, "selected": 80, "selection_complete": false, "top_omitted": 510}}`
Minimum order size is in shares; legacy `min_size_usd` is a share-count alias.

Warnings:
- 21 prior market(s) are absent from the current filtered shortlist; omission is not evidence of closure or resolution
- upstream discovery pagination is incomplete: page_cap
- upstream output cap omitted 510 eligible rows

