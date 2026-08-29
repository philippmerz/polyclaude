# Standing resting orders (GTC post-only makers)

Maker orders are a default tool, not an exception (operator 2026-07-24: "limit orders
are standard... part of your everyday repertoire"). Two uses:
- **SELLS** — consumed-edge take-profits (doctrine §5) at/above fair, fee-free, no spread.
- **BIDS** — patient entries/adds at the bid side. Saves the per-market taker fee and the
  spread. The true fee curve is `rate × p × (1−p)` per share (current category cap 0.07;
  ~1.67c at p=0.61 at that cap); `scripts/pm_fees.py` is authoritative for the market's
  actual rate.
  `polyclaude_enter.py --maker` does this. Raw CLOB BUYs are now deliberately
  blocked because they bypass full-fill ticket/cluster and indexing-lag reservations.

**Management rules (checked EVERY tick — treat `.venv/bin/python scripts/clob_v2.py orders`
as the authoritative live inventory and reconcile it against positions and current priors):**
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
- Hidden-info-class positions: never rest a sell at or below fair, because an informed
  up-spike can mean fair jumped. A premium-to-fair sell (strictly above fair) is allowed
  when that premium explicitly compensates the jump risk; thesis-break exits still use
  active judgment, and scheduled-catalyst pull rules still apply.

## Live-order source of truth

Run `.venv/bin/python scripts/clob_v2.py orders` for the authoritative live order set.
Do not use this file as a current-order inventory: the entries below are a dated policy and
execution log only. Reconcile the command output on every tick and after every place/cancel.

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
The current cancel helper now refuses to send DELETE unless the exact target and side appear in a
fully paginated pre-cancel inventory; an unreserved BUY or a reappeared cancel marker leaves a
persistent manual-reconciliation block rather than letting an indexing race authorize new risk.
Historical snapshot at that fill: Trump-out SELL 28@0.97, Greenland SELL 29@0.98,
Fed-hike YES SELL 41@0.26,
SpaceX YES SELL 34@0.96.

**Maker-sell-at-fair policy (2026-07-28, corrected for hidden information):** for an ordinary
public-information position, a resting post-only sell AT FAIR is fee-free, fills only if someone
pays >= my own fair value, and frees capital early at no EV cost. For hidden-info-class positions
(GPT-6, MacBook), sells at or below fair are banned because an informed up-move can mean fair
JUMPED. A premium-to-fair sell (strictly above fair) is allowed when its premium explicitly pays
for that jump risk. SpaceX qualified (mechanical, public-fact resolution) -> 34@0.96 rested.

**Fed maker-sell (2026-07-28, operator Q "lowest sell price that beats holding?"):** taker breakeven
is ~0.2636 at the current 0.07 cap because taker net is `p − rate × p × (1−p)`; MAKER
breakeven = fair 0.25 exactly (fee-free). The actual per-market rate comes from
`scripts/pm_fees.py`. Rested 41@0.26
— above both, ask was 0.218, so it fills only if the market pays above my fair. Free option; resolves
Wed 18:00 UTC otherwise. GENERAL RULE: when hold-vs-sell is close, don't choose — rest a post-only
sell at the price that makes selling strictly better and let the market decide.

## Scheduled-catalyst pull rule (2026-07-29, generalized from the announce-window rule)

ALL resting orders on a market with a SCHEDULED binary catalyst (FOMC, earnings, court ruling,
launch date) must be PULLED before the release moment — not at the next tick after it. A resting
sell left through the release is a free option against us: if the catalyst lands our way, bots
lift the stale offer at pre-catalyst prices and capture the entire tail (Fed 0.26 sell vs ~1.00
post-hike would have donated ~$24). Pre-catalyst fills remain benign (that IS the free option
working — Fed 32.78sh filled at 0.26 three hours before a decision that zeroed YES).
Mechanically: when a position has a known catalyst datetime, note the pull deadline in the
position entry AND arm a pre-catalyst reminder; do not rely on a periodic check coinciding
with the release (today it did, 18:00:05, and the order had already filled — luck, not process).

## PLACED: Gemini-HLE-50+ NO maker BUY (2026-08-10 22:30 UTC, DEC-0065)

60 shares NO @ **0.100**, post-only GTC, $6.00, order `0x257e1b10…31e7`. Fee-free by construction;
at the current 0.07 cap, the taker path was 0.103 ask + 0.65c/share
(`rate × p × (1−p)`) = 0.1095 effective, so resting saved ~0.95c/share versus crossing on a
leg with 4.7 months to run and no scheduled catalyst — exactly the case the maker-first default
was written for. The actual per-market rate comes from `scripts/pm_fees.py`. It sat one tick above
the 1615-share 0.099 wall.

NOT subject to the scheduled-catalyst pull rule: there is no dated release that flips this market.
The thing that would kill the thesis (agi.safe.ai publishing a 2026 Gemini row >=50) is unscheduled
and would move the price against me instantly — so if the board updates, PULL this bid before
re-underwriting, don't let it fill into news.

Re-verify at each tick: if unfilled after ~7 days, either re-price to the then-best bid or drop it —
a stale resting bid at a price the market has left behind is a free option written to the market.

## REPLACED: Greenland NO maker SELL after DEC-0090 trim (2026-08-28 20:36 UTC)

Cancelled the original 29sh @ 0.98 order `0x5c542a6b…352f5`, verified it was absent, sold 5sh
actively at 0.93 to fund DEC-0089, then restored the take-profit for the exact remaining balance:
24sh NO @ **0.98**, post-only GTC, order `0xbbf11df8…e2373`. The 0.98 rest is above the unchanged
0.95 fair; the active trim changed quantity, not thesis. Live `clob_v2.py orders` remains the source
of truth.

## FILLED: touchscreen-MacBook-2026 NO maker BUY (placed 2026-08-11 10:15, filled by 18:00 UTC, DEC-0067)

6 shares NO @ **0.59** — FILLED, fee-free. Position now 66sh at 0.412 avg, cost $27.19 (14.6% of a
$186 bankroll, inside the 15% single-ticket cap the size was set by). The maker route worked exactly
as intended: rested at the bid rather than crossing, so neither the spread nor the quadratic taker
fee was paid.

Original placement rationale: post-only GTC, $3.54, order `0x5d4f7e42…2b86`. Rested at the bid because the
book was 0.59/0.60 and the helper caps a maker bid one tick under the ask. At p=0.60 and the current
0.07 cap, `rate × p × (1−p)` is 1.68c/share, so the maker route avoided both that fee and the 1pp
spread to skip a queue on a position with 4.7 months to run. Use `scripts/pm_fees.py` for the
market's actual rate.

Size is set by the 15% single-ticket cap, not by conviction: position cost $23.65 against a $27.03
ceiling. Kelly at p_no 0.80 wanted $36. If the cap ceiling rises with bankroll, this is the first
position to top up.

NOT catalyst-gated in the near term (Apple's September event is the next scheduled mover, ~Sep 8-10).
PULL this bid before that event per the scheduled-catalyst rule — a resting bid through an unveiling
is a free option written to whoever sees the ship date first.


## CANCELLED: Gemini-HLE-50 NO maker BUY (placed 2026-08-10 22:30, cancelled 2026-08-12 22:05, DEC-0071)

60sh @ 0.100 never filled beyond a 0.01sh dust match. Cancelled because the market moved 2.5x away
(NO 0.102 -> 0.249 in ~30h), which converts a cheap option into ADVERSE SELECTION: filling now needs
a ~60% collapse, and a move that size on a hidden-info market is information — the board posting a
2026 Gemini row, or Google announcing a >=50 score — not noise. A bid that can only fill once its own
thesis has broken is a negative-EV standing order however cheap the price looks.

Held the position itself (36.01sh, +211%, prior 0.56 vs 0.249 mark). The claim is still cheap; what
expired was the case for paying collateral to sit 15pp under the market.

GENERAL RULE this instance sharpens: a resting bid's worth is not its price versus your fair, it is
P(fill | noise) versus P(fill | information). As the market walks away from a bid, that ratio decays
even though the nominal edge at the bid price looks better than ever.
