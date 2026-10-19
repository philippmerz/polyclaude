# Market context batches

> **Context-only warning:** Context grouping uses exact Gamma event IDs among rows present in this snapshot. The snapshot may omit event siblings, and shared event membership does not prove proposition, criteria, outcome, or settlement equivalence.

Scan kind: `thin_tail`  
Current proof: `5634a493680e34bf8424c370167298f19bd9b491ed5d72ca541f08da1e8f857e`  
Source integrity verified: `True`  
Prior proof: `dcc5f67880e1d702bd7b067833854b72eaefb839459c858e1ff0880e6dfcf0fa`

Upstream discovery coverage: `{"fetch": {"duplicate_market_rows": 451, "endpoint": "events", "fetched_market_rows": 38055, "malformed_rows": 0, "max_pages": 20, "pages_attempted": 20, "pages_succeeded": 20, "pagination_complete": false, "response_rows": 2000, "stop_reason": "page_cap"}, "filters": {"eligible_before_top": 3213, "filter_accounting_complete": true, "filter_rejections": {"horizon": 315, "liquidity": 14846, "missing_deadline": 25, "not_tradable": 5342, "past_deadline": 880, "spread": 822, "volume": 9698, "win_assumed_hurdle": 2914}, "input_markets": 38055, "selected": 3000, "selection_complete": false, "top_omitted": 213}}`
Minimum order size is in shares; legacy `min_size_usd` is a share-count alias.

Warnings:
- 454 prior market(s) are absent from the current filtered shortlist; omission is not evidence of closure or resolution
- upstream discovery pagination is incomplete: page_cap
- upstream output cap omitted 213 eligible rows

