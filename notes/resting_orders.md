# Standing resting orders (GTC post-only makers)

This is the compact current policy. It is not a live-order inventory; the full
dated policy and execution history is preserved in
[resting_orders-2026-09-09.md](../docs/archive/resting_orders-2026-09-09.md).

## Live source and default

Run `.venv/bin/python scripts/clob_v2.py orders` for the authoritative live order set and reconcile it against positions and current priors every tick and
after every place/cancel. Never infer current orders from this file. Maker
orders are a default tool: post-only SELLS for consumed-edge take-profits and
BIDS for patient entries/adds, subject to the gates below. Raw CLOB BUYs remain
blocked because they bypass full-fill ticket/cluster and indexing-lag reserves.

Charge each actual PM fill at the level where it occurs using
`rate × [p × (1−p)]^exponent` per share. `scripts/pm_fees.py` reads the
authoritative structured `feeSchedule`; the **0.07 cap retained only for legacy compatibility**. Do not apply the curve at an average fill price or charge
unfilled shares.

## Mandatory management rules

- A SELL is for an up-move/take-profit, not a thesis-break exit. Thesis-break
  exits require active judgment and current depth.
- Re-verify the thesis and hidden-information coverage before every resting
  BID. If state changes or is uncertain, CANCEL FIRST. Pull bids before known
  catalyst windows and cancel/re-price when fair changes. After every cancel,
  verify the order is absent from the fully paginated authoritative inventory.
- Announce-market asymmetry: informed flow generally BUYS YES / SELLS NO.
  Resting YES bids may be benign without hidden-channel coverage; resting NO
  bids require it. Pull announce-market YES bids at the event/window end.
- For hidden-info-class positions, never rest a sell **at or below fair**:
  informed flow can mean fair jumped. A **premium-to-fair** sell **strictly above fair** is allowed only when its premium explicitly compensates jump
  risk. Thesis-break exits remain active judgments.
- Pull every order on a scheduled-catalyst market before the release moment;
  do not rely on the next periodic tick. A stale sell can donate the post-event
  tail and a stale bid can fill under information.

## Group and authority guard

Duma and MetaMask monotonicity are protected `_groups` where applicable: do not
independently add, trim, or exit a leg. HLE is a correlated exposure for
caps/sizing, not an atomic `_groups` topology; retain its current HOLD / NO ADD
/ NO FLIP assessment and correlation limits, but do not apply the Duma/MetaMask
leg prohibition by analogy. Check
[backlog.md](backlog.md) for current clocks (Apple Sep-9, AVAV Sep-9, the
Sep-12 drill, and USGS Sep-13). Preserve the existing drill procedure and
execution gates; documentation consolidation does not alter the operator's
mandate or create a new recurring task.
