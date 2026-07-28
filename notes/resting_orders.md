# Standing resting orders (GTC post-only makers)

Maker orders are a default tool, not an exception (operator 2026-07-24: "limit orders
are standard... part of your everyday repertoire"). Two uses:
- **SELLS** — consumed-edge take-profits (doctrine §5) at/above fair, fee-free, no spread.
- **BIDS** — patient entries/adds at the bid side. Saves the taker fee (1000bps markets
  charge takers 10%×min(p,1−p)/share — 3.9c at 0.61 = ~8% of cost basis) and the spread.
  `polyclaude_enter.py --maker` does this (NOTE: flag shipped 2026-07-24, not yet
  exercised live); raw: `clob_v2.py buy <tok> <px> <usd> --post-only`.

**Management rules (checked EVERY tick — reconcile `clob_v2.py orders` vs this table):**
- SELLS fill only on UP-moves. They do NOT handle thesis-break exits — those need the
  active judgment path (news → catalyst_check → active sell).
- BIDS fill under FUTURE information: every tick re-verify the thesis fundamental is
  unchanged. If state changed or in doubt → CANCEL FIRST. Pull bids before known
  catalyst windows. Resting bids require news_watcher coverage of the market's
  hidden-info channel — EXCEPT announce-market YES bids (see asymmetry below).
- If fair changes on news, cancel/re-price the affected order.
- **Announce-market bid asymmetry:** on "<entity> announce at <event>?" markets,
  informed flow (embargoed reveals) BUYS YES / SELLS NO — resting YES bids have benign
  adverse selection (fills = impatient exits); resting NO bids are the embargo's victim
  (YES bids OK without coverage; NO bids need it — DC/Lucasfilm skipped on exactly this).
- Hidden-info-class positions (GPT-6) get NO resting take-profit sells — an informed
  up-spike means fair jumped; sell only via active judgment.

## Live orders (all 7 — single source of truth; updated 2026-07-25 14:30)

| Placed | Position | Side | Shares | Price | Fair | Note |
|---|---|---|---|---|---|---|
| 2026-07-24 | Greenland NO | SELL | 29 | 0.98 | 0.975 | Dec-31 fade; consumed-edge auto-exit |
| 2026-07-24 | Trump-out NO | SELL | 28 | 0.97 | 0.97 | Dec-31 fade; us-politics |
| 2026-07-24 | Satoshi NO | SELL | 6 | 0.99 | 0.99 | Dec-31 fade |
| 2026-07-25 | GPT-6 NO | BID | 10 | 0.67 | 0.82 | Dip-catcher (mark eased to 0.725) |

**CANCELLED 2026-07-26 02:20 (post-panel rule):** Apple 13@0.80 + Prime 11@0.78 — panels passed
without confirmed qualifying announcements; benign-adverse-selection logic is DEAD once the
catalyst window closes (a post-panel fill = "nothing announced" = adverse). Released $18.98.
DOCTRINE ADDITION: announce-market YES bids must be pulled AT panel/window END, not just before
known catalysts — the asymmetry inverts the moment the catalyst passes.

FILLED 2026-07-26 02:11: Marvel-SDCC SELL 7@0.98 = $6.86 (+43.9% realized; market resolved
YES 1h later — the fill cost $0.14 vs redemption for a day-earlier fee-free exit). SDCC over.
Remaining queue item: Kuwait NO (~$10 from the freed cash, conditions in backlog).

## Liquidity rewards (first checked 2026-07-24)

Polymarket pays daily USDC to makers within `max_spread` of mid, size ≥ `min_size`
(config via `clob.polymarket.com/markets/<cond>` → `rewards`). GPT-6: $50/day pool, min
20sh, 4.5c band — NOTE current bid is 10sh (below min) AND mid (0.765) moved outside the
band of my 0.67 bid → rewards qualification currently DEAD; revives only if mid ≤0.715
and size ≥20. Verify any past accrual as pUSD credits in the daily balance sweep.
Do NOT deepen positions to farm rewards; two-sided quoting banned where it fights alpha
(Trump-out $10/d min50, Satoshi $2/d min50, SpaceX $30/d min200 all below-min anyway).

**FILLED 2026-07-28 02:54:** MacBook NO bid 25@0.40 (benign dip, no news; position 60sh @0.394 avg
vs 0.73 fair). **CANCEL-RACE LESSON (02:56 audit):** the GPT-6 10sh order's 5.4sh remainder FILLED
Jul-27 01:05 DESPITE the Jul-26 22:10 cancel command returning "canceled" — the grep of response
text never verified removal. True GPT-6 position: 50sh @0.645 (cap overshoot +5.4sh, profitable but
unintended). RULE: after every cancel, VERIFY via `clob_v2.py orders` that the id is gone.
Live: Trump-out SELL 28@0.97, Greenland SELL 29@0.98, Fed-hike YES SELL 41@0.26.

**Fed maker-sell (2026-07-28, operator Q "lowest sell price that beats holding?"):** taker breakeven
0.2778 (fee eats 10% of min(p,1-p)); MAKER breakeven = fair 0.25 exactly (fee-free). Rested 41@0.26
— above both, ask was 0.218, so it fills only if the market pays above my fair. Free option; resolves
Wed 18:00 UTC otherwise. GENERAL RULE: when hold-vs-sell is close, don't choose — rest a post-only
sell at the price that makes selling strictly better and let the market decide.
