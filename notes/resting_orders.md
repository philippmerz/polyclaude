# Standing resting orders (GTC post-only makers)

Maker orders are a default tool, not an exception (operator 2026-07-24: "limit orders
are standard... part of your everyday repertoire"). Two uses:
- **SELLS** — consumed-edge take-profits (doctrine §5) at/above fair, fee-free, no spread.
- **BIDS** — patient entries/adds at the bid side. Saves the taker fee (1000bps markets
  charge takers 10%×min(p,1−p)/share — 3.9c at 0.61 = ~8% of cost basis) and the spread.
  `polyclaude_enter.py --maker` does this; raw: `clob_v2.py buy <tok> <px> <usd> --post-only`.

**Management rules (checked EVERY tick — reconcile `clob_v2.py orders` vs this file):**
- SELLS fill only on UP-moves (market agreeing with me). They do NOT handle thesis-break
  exits — those still need the active judgment path (news → catalyst_check → active sell).
- BIDS fill under FUTURE information: every tick, re-verify the thesis fundamental is
  unchanged (for GPT-6: no release/announcement). If state changed or in doubt → CANCEL
  FIRST, think second. Pull bids before known catalyst windows (events, earnings, panels).
- Resting bids are only allowed on markets whose hidden-info channel is covered by
  news_watcher keywords (GPT-6: gpt/openai tier-1 ✓). No coverage → no blind bid
  (MacBook rejected 2026-07-24: Gurman/supply-chain channel unwatched).
- If fair changes on news, cancel/re-price the affected order.

| Placed | Position | Side | Shares | Price | Fair | Note |
|---|---|---|---|---|---|---|
| 2026-07-24 | Greenland NO | SELL | 29 | 0.98 | 0.975 | Dec-31 fade; consumed-edge auto-exit |
| 2026-07-24 | Trump-out NO | SELL | 28 | 0.97 | 0.97 | Dec-31 fade; us-politics |
| 2026-07-24 | Satoshi NO | SELL | 6 | 0.99 | 0.99 | Dec-31 fade |
| 2026-07-24 | Marvel-SDCC YES | SELL | 7 | 0.98 | 0.93 | Book 0.887/0.99 pre-panel; 0.98 certain > 0.93 EV, exits before resolution risk. If unfilled → redeem ~Jul-27 |
| 2026-07-24 | GPT-6 NO | BID | 20 | 0.60 | 0.82 | Add at bid (taker would cost 0.649 eff). Joins 60sh queue. Rewards-band order (see below). Cap: cluster ≤ half-K $47; this takes it to ~$33 |

## Liquidity rewards (first checked 2026-07-24 — previously unused income stream)

Polymarket pays daily USDC to makers resting within `max_spread` of mid, size ≥ `min_size`
(config per market via `clob.polymarket.com/markets/<cond>` → `rewards`). Current book:
- **GPT-6: $50/day pool, min 20sh, 4.5c band** → the 20sh bid @0.60 qualifies (one-sided
  scores at reduced weight). Empirically check accrual after ~1 day (rewards dashboard /
  data-api) before counting it as real carry.
- Trump-out $10/d min50, Satoshi $2/d min50, SpaceX $30/d min200 — min_size above our
  position sizes; do NOT deepen positions just to farm rewards (classifier/cluster rules
  outrank reward income; Trump-out add rejected on thin edge + politics-ρ).
- Two-sided quoting scores higher but is off-limits where it conflicts with alpha
  (selling GPT-6 at 0.65 against a 0.82 fair = donating 17pp — never).
