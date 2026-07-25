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
| 2026-07-24 | Marvel-SDCC YES | SELL | 7 | 0.98 | 0.93→locked | Panel Sat Jul-25; ~0.95 pre-panel. Unfilled → redeem ~Jul-27 |
| 2026-07-24 | Apple-TV-SDCC YES | BID | 13 | 0.80 | 0.95 | Panel Sat 2-4pm PT; mid 0.905 — fills only on panic dump |
| 2026-07-24 | Prime-SDCC YES | BID | 11 | 0.78 | 0.95 | Carrie panel Sat; re-entry below fair |
| 2026-07-25 | GPT-6 NO | BID | 10 | 0.67 | 0.82 | Re-priced from 20@0.60 (flow ran to 0.765, 0 news); dip-catcher |

SDCC cluster cap: Marvel 7sh + both bids if filled ≈ $25 ≈ 15% bankroll — no adds.
Expected releases: SDCC resolves ~Jul-26/27 → unfilled Apple/Prime bids free ~$19; Marvel
redeems ~$7 if YES. Deploy queue in notes/backlog.md (Fed add #0, then MacBook/SpaceX/Kuwait).

## Liquidity rewards (first checked 2026-07-24)

Polymarket pays daily USDC to makers within `max_spread` of mid, size ≥ `min_size`
(config via `clob.polymarket.com/markets/<cond>` → `rewards`). GPT-6: $50/day pool, min
20sh, 4.5c band — NOTE current bid is 10sh (below min) AND mid (0.765) moved outside the
band of my 0.67 bid → rewards qualification currently DEAD; revives only if mid ≤0.715
and size ≥20. Verify any past accrual as pUSD credits in the daily balance sweep.
Do NOT deepen positions to farm rewards; two-sided quoting banned where it fights alpha
(Trump-out $10/d min50, Satoshi $2/d min50, SpaceX $30/d min200 all below-min anyway).
