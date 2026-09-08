# HIP-4 metadata check — watch only

One public mainnet request to `https://api.hyperliquid.xyz/info`, body
`{"type":"outcomeMeta"}`, ran at **09:41:15.102324–09:41:15.544150 UTC** on
2026-09-08 and returned HTTP 200. No wallet/account request, order book,
Polymarket search, funding, trading or infrastructure change was made.

The Aug-28 journal records eight then-active IDs and a sampled BTC book, not
a complete historical family/underlying inventory. Current visible recurring
`priceBinary` descriptors include BTC, ETH, SOL and HYPE, fixed target prices,
one-day periods and 06:00 expiries. That alone does not prove newly added
underlyings or active trading status. Registered touch, policy-rate and sports
templates are likewise not evidence of active markets.

## Captured price-bucket question

These objects are copied from the worker's captured response output. The full
response was not retained, output was truncated, and total outcome/question
counts are unknown. This is an extracted-object record, not a full raw snapshot.

```json
{
  "description": "class:priceBucket|underlying:BTC|expiry:20260909-0600|priceThresholds:76964,80105|period:1d",
  "fallbackOutcome": 1997,
  "name": "Recurring",
  "namedOutcomes": [1998, 1999, 2000],
  "question": 227,
  "settledNamedOutcomes": []
}
```

Associated outcome objects:

```json
[
  {"description":"other","name":"Recurring Fallback","outcome":1997,"quoteToken":"USDC","sideSpecs":[{"name":"Yes"},{"name":"No"}]},
  {"description":"index:0","name":"Recurring Named Outcome","outcome":1998,"quoteToken":"USDC","sideSpecs":[{"name":"Yes"},{"name":"No"}]},
  {"description":"index:1","name":"Recurring Named Outcome","outcome":1999,"quoteToken":"USDC","sideSpecs":[{"name":"Yes"},{"name":"No"}]},
  {"description":"index:2","name":"Recurring Named Outcome","outcome":2000,"quoteToken":"USDC","sideSpecs":[{"name":"Yes"},{"name":"No"}]}
]
```

This is a family not detailed in the old note, not proof that it launched after
Aug-28. No active-status field was observed. A future expiry or an empty settled
list does not establish tradeability. Do not infer boundary inclusivity, index
mapping, fallback payout or the complete oracle/averaging rule from these labels.

## Documentation and decision

Main independently read the current [official spot info documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot):
it documents `outcomeMeta` at the mainnet endpoint and does **not** label it
testnet-only. An initial worker statement to that effect was unsupported and
was corrected before recording this assessment. The [asset-ID documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids)
describes separate binary sides per outcome; it does not supply this question's
complete resolver formula. Do not label the whole endpoint undocumented on
the basis of the discarded testnet-only claim.

**Watch only.** The visible bucket structure justifies preserving exact evidence,
not funding a venue or building the full scanner. Entry still requires actual
trading status, complete resolver/oracle rules, an exactly equivalent counterleg,
fresh synchronized depth, applicable fees/minimums and all operational costs.
The old HyperCore-mark versus Binance/window mismatch remains a warning, not a
fresh comparison of every current contract. No rule-identical hedge or economic
edge was established here. No probabilities or portfolio decisions changed.
