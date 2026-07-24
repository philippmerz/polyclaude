# Standing resting orders (GTC maker take-profits)

Auto-execute the consumed-edge exit (doctrine §5) at fair, fee-free, no spread — the
operator's 2026-07-24 "automatic sale at your prior" idea. Placed via
`clob_v2.py sell <token> <price> <shares> --order-type GTC --post-only`.

**IMPORTANT management rules:**
- These fill ONLY on an UP-move to fair (market agreeing with me → take profit). They do
  NOT handle thesis-BREAK exits (price dropping) — those still need the active judgment
  path (news → catalyst_check → active sell).
- If a fade's FAIR changes on news, CANCEL/re-price the resting order (`clob_v2.py orders`
  to list, cancel via the order id). Check these each tick.
- `clob_v2.py orders` shows live ones; reconcile against this file.

| Placed | Position | Shares | Rest SELL @ | Fair | Note |
|---|---|---|---|---|---|
| 2026-07-24 | Greenland NO | 29 | 0.98 | 0.975 | Dec-31 fade; consumed-edge auto-exit |
| 2026-07-24 | Trump-out NO | 28 | 0.97 | 0.97 | Dec-31 fade; us-politics |
| 2026-07-24 | Satoshi NO | 6 | 0.99 | 0.99 | Dec-31 fade |

(GPT-6/SpaceX/Marvel NOT rested: GPT-6+SpaceX have live edge below fair (want to hold/add,
not take-profit); Marvel near-locked, settles at par ~Jul-27, deep book — no spread to avoid.)
