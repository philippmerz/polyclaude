# Limitless quote audit — 2026-09-07/08 UTC

Status: **screening only; no execution enabled or transaction submitted.**

## Primary-source contract

- [Current fee guide](https://docs.limitless.exchange/user-guide/fees): CLOB BUY
  charges are deductions from received outcome contracts, with a stated
  0.40–3.00% range. The buy curve is asymmetric, not a symmetric surcharge on
  USDC. Its exact formula is unpublished; execution responses disclose actual
  charges afterward. The inspector uses 3% as an explicit screening assumption,
  not a verified account-specific pre-trade quote. Per-maker rounding, rebates
  and market applicability remain unverified.
- [Orderbook reference](https://docs.limitless.exchange/api-reference/trading/orderbook):
  the exact active CLOB leaf slug returns a YES-side book. NO asks derive from
  YES bids at `1 - price`, with unchanged quantity. A `tokenId=NO` query is not
  a documented alternate-book selector. `minSize` participates in adjusted
  midpoint/reward filtering; it is not established here as a hard order minimum.
  Receipt time alone does not prove venue book freshness.
- [Official Python SDK market types](https://raw.githubusercontent.com/limitless-labs-group/limitless-sdk/main/limitless_sdk/types/markets.py):
  orderbook sizes are integer shares scaled by 1e6. Thus size 20,000,000 is
  20 contracts, whose cash cost depends on price—not $20 of depth. The installed
  Python SDK agrees. The TypeScript documentation is less explicit about the
  raw REST scale, so this unit assumption needs revalidation after API changes.
- The [whitepaper](https://limitless.exchange/whitepaper.pdf), page 3, gives an
  older price-dependent fee formula that does not reproduce the current guide's
  representative values. Do not mix the older formula with the current table
  or invent an interpolated exact curve.

## Measurements and corrections

At approximately 23:43, an ETH five-minute market returned the same YES token
and levels both with no query and with a NO-token query. Its 20,000,000 raw
ask quantity was 20 contracts. That market subsequently expired; this is
schema evidence, not a live opportunity.

A 23-page survey retrieved 556 advertised active rows: 161 had the discovery
flag, including 101 parent groups without prices/tokens. The old scanner
invented `[0.5, 0.5]` for these parents and spent its verification budget on
misidentified comparisons. The revised normalizer expands to exact priced
children and preserves child IDs, slugs and tokens, while retaining parent
title/rule context only for matching. A later live refresh returned **162
flagged parents and 714 priced leaves**, including 656 leaves whose own
`marketType` remains `group`. A group label alone must not exclude a valid
tokenized leaf. These rolling pagination observations are not atomic censuses.
After the pagination safeguards were added, a final public read completed
23 pages / 557 advertised rows, yielding 161 flagged parents and **709 priced
leaves** (651 group-labeled children). The changing totals are separate live
snapshots. This run invoked no language-model verification, Telegram or order.

The pure quote module now mirrors the correct side, converts depth units,
charges each PM level's full structured fee curve, and matches conservative
NET shares under both independent cash caps and displayed depth. Gross
Limitless quantity is floored once to a micro-contract. Additional contracts
if the actual fee is below the assumed bound are contingent upside, not floor
payout. Decimal arithmetic does not establish venue execution rounding.

Counterexample (PM fees zero): $10 buys 20 gross Limitless contracts at 0.50,
but a 3% deduction leaves 19.4. Buying 20 complementary PM shares at 0.49
costs $9.80: total $19.80 versus $19.40 floor, a **$0.40 loss**. The old
formula instead reported $0.16 profit. Matching only 19.4 PM shares costs
$9.506, leaving a smaller but still negative **$0.106** conditional profit.

## Remaining gates

Exact current leaf/Gamma identity, token/outcome mapping, active status and
known PM minimums are checked by the public-read wrapper. Stale or missing
data is unpriced, never a plausible zero-cost quote. Both orientations are
screened; the old credential reminder/order scaffolding is unnecessary for
public reads. Neither an LLM `IDENTICAL` label nor positive conditional math
establishes legally or operationally identical resolution, synchronized fills,
Limitless freshness/minimums, final fee rounding, gas/bridge/settlement costs or
stablecoin redemption parity. Every output retains `execution_ready=False`.
