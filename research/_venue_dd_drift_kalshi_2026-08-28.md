# Drift / Kalshi venue diligence — 2026-08-28

## Decision

- **Drift / Velocity: close as non-deployable for prediction-market arbitrage.** The old
  Drift BET route now redirects to Velocity. Velocity is a new Solana program, the legacy
  Drift deployment is paused, and Velocity explicitly removed prediction-market
  initialization and deprecated the prediction contract type. Its live market surface is
  perpetuals, not event binaries, so it has no payoff-identical Polymarket intersection.
- **Kalshi execution: no build and no funding.** The old April finding that Kalshi required
  a US bank account is stale: Kalshi now admits eligible users in many countries and offers
  international debit, wire, and crypto rails. It still requires identity/residence
  verification, however, which conflicts with this repo's explicit "fully decentralized —
  no CEX, no KYC" boundary. No account was created and no eligibility assumption was made
  from the VM's location.
- **Kalshi public data: useful read-only input.** Its unauthenticated REST market and book
  endpoints are a large, current consensus surface. A bounded, fail-closed adapter for
  already-shortlisted Polymarket sports markets is worth keeping; it is an evidence source,
  not an execution path.

## Drift / Velocity evidence

`https://app.drift.trade/bet` redirects to `https://velocity.exchange/bet`. The official
Velocity migration guide says the new deployment has a new program ID, no Drift state
carries over, `initialize_prediction_market` was removed, and
`ContractType.PREDICTION` became `DEPRECATED_PREDICTION`.

A live read-only query to `https://data.velocity.exchange/stats/markets` exposed SOL, BTC,
ETH, and HYPE perpetuals and no event/outcome symbols. At the snapshot, only SOL-PERP had
nonzero reported 24-hour quote volume (about $93); the other three reported zero. Event-like
prediction queries failed as unknown/invalid symbols. This is enough to establish zero
current Polymarket overlap even without relying on the thin-volume observation.

Velocity's public DLOB/REST documentation is perps-only. A separate perps strategy could fit
under $200 mechanically, but it would require a new Solana account, USDT collateral, SOL gas,
explicit jurisdiction eligibility, a published/acceptable final post-fork audit, and a
measured funding/basis edge. None of those turns a perpetual into a hedge for a binary
Polymarket contract.

## Kalshi evidence

### Access and scale

The official Quick Start documents unauthenticated REST access to markets, events, and
orderbooks; WebSockets and trading require an API key. A complete live pagination at
21:4x UTC returned **52,000 open non-MVE contracts**, of which **33,501** had nonzero bids
and asks. That count is dominated by sports derivatives and micro-markets and must not be
mistaken for 52,000 independent opportunities.

In a bounded first-20,000-contract sample:

- 14,086 had two-sided prices;
- 6,378 had spreads at or below 5 cents;
- 4,809 had spreads at or below 3 cents;
- 722 had at least 1,000 contracts of 24-hour volume; and
- 649 combined a spread at or below 5 cents, at least 1,000 contracts of 24-hour volume,
  and at least five contracts at the touch.

The API eventually rate-limited a broad crawl, so any durable integration must shortlist on
Polymarket first, cache mappings, back off on 429, and fail closed on stale data.

### Fees and small-bankroll mechanics

The July 7 fee schedule gives the general taker formula as
`0.07 * contracts * price * (1-price)`. The newer fixed-point rounding specification
separately ceilings the model fee to $0.000001, aligns direct-member balances to $0.0001
and non-direct balances to $0.01, and carries rounding overpayment through a per-order
accumulator. With no authorized account/member type, read-only comparisons conservatively use
the cent-aligned debit and do not assume future rebates.
Applicable maker fees use a lower `0.0175` coefficient; many series have no maker fee and a
few named series have zero taker fees. There is no settlement or membership fee. Kalshi now
supports fractional quantities, so contract granularity is not the binding constraint at a
$188 bankroll.

The real constraints are account/KYC eligibility, capital fragmentation across two venues,
funding/withdrawal friction, non-atomic legging, and settlement-language basis risk. The
international wire minimum is $1,000; other rails can fit this bankroll, but their actual
crypto provider/network path is exposed only after account onboarding and cannot be assumed
to accept the repo's Polygon assets.

### Live overlap test

A bounded join of the first 20,000 open non-combo Kalshi contracts against the top 1,000
Polymarket markets produced 20 high-confidence participant/name near-overlaps. Manual rule
and live-book checks on three representative pairs—Buse/Bonzi tennis, NRG/LOUD Valorant, and
Astros/Mets totals—confirmed **zero strictly rule-identical pairs and zero fee-positive
trades**.

The Buse/Bonzi check also caught a critical data trap. Gamma still suggested Buse near 0.77,
but the immediate Polymarket CLOB ask was 0.89, matching Kalshi's 0.89 ask. The cheapest
cross-side pair summed to 1.01 before fees; at the five-share Polymarket minimum it lost about
2.3 percentage points after both venues' taker fees. The other checked pairs summed to
1.00–1.01 before fees. Any comparator that uses Gamma midpoint rather than current CLOB
depth would manufacture false edge.

The held Greenland contract is an instructive non-sports false arb:

- Kalshi `KXGREENLAND-29-27`: YES 0.041 / 0.043, requiring the United States to
  **purchase** at least part of Greenland from Denmark before Jan 1, 2027.
- Polymarket `will-the-us-acquire-any-part-of-greenland-in-2026`: YES 0.06 / 0.07,
  also counting a qualifying binding sovereignty/control instrument (even if effective
  later), primary/exclusive jurisdiction acquired by force, and other broader paths.

Kalshi YES at 0.043 plus Polymarket NO near 0.94 appears to cost only 0.983, but both legs
can lose if a Polymarket-only qualifying control path occurs. It is basis risk, not a 1.7%
arbitrage. Kalshi's narrower market is still useful context and is consistent with the held
Greenland NO prior; it does not change the HOLD decision.

## Operating decision and revisit gates

1. Do not create, KYC, or fund a Kalshi account under the current mandate.
2. Do not build a Velocity or Kalshi execution adapter.
3. Permit a read-only Kalshi consensus adapter only when it:
   - starts from already-shortlisted Polymarket sports candidates;
   - matches exact participants, event time, market type, side, and numeric line;
   - reads both settlement rules and fails closed on void/postponement/cancellation mismatch;
   - uses live Polymarket CLOB depth, never Gamma midpoint, for executable comparisons;
   - includes both venues' fees at the actual minimum size; and
   - emits evidence only, with no account, funding, or order path.
4. Revisit executable Kalshi arbitrage only if the operator explicitly relaxes the no-KYC
   boundary and confirms jurisdiction **and** the read-only log shows recurrent, strict-rule,
   live-depth gaps above roughly 3 percentage points after fees, transfer cost, and legging
   buffer.
5. Revisit Velocity only if prediction contracts are officially reintroduced, live outcome
   books exist, a final post-fork audit is published and acceptable, and exact Polymarket
   settlement equivalence can be established.

### Read-only implementation shipped

`scripts/kalshi_consensus.py` now implements that narrow evidence path behind the explicit
`sports_pm_scan.py --with-kalshi` flag. The normal scanner does not import the adapter or emit
Kalshi fields. An enabled run makes a single capped milestone request per shortlisted candidate,
requires exact event/series/child lineage plus participant, start-time, predicate and exceptional-
settlement equivalence, and then walks fresh public books at one shared minimum size. It has no
credential, funding, or order method. Because the two REST snapshots are sequential, its output is
labelled a fee-only non-atomic snapshot spread rather than an arbitrage or executable quote.

The final live five-candidate smoke emitted no spread: three UFC candidates had no exact
participant/time/lineage match, while both Coventry candidates failed the supported full-event
scope gate. A separate exact PIT–STL 8.5-run lookup reached the rule comparison and was rejected
before either book was read: Polymarket explicitly uses a half payout on cancellation and keeps a
postponed game open, while the available Kalshi child text did not prove the same exception set.
This is the intended fail-closed result, not a missing-data workaround.

## Primary sources

- Velocity migration: https://docs.velocity.exchange/developers/migrate-from-drift
- Velocity orderbook / WebSocket: https://docs.velocity.exchange/developers/ecosystem-builders/orderbook-and-ws
- Velocity fees: https://docs.velocity.exchange/protocol/trading/trading-fees
- Velocity audits: https://docs.velocity.exchange/protocol/risk-and-safety/audits
- Kalshi public market-data quick start: https://docs.kalshi.com/getting_started/quick_start_market_data
- Kalshi orderbook semantics: https://docs.kalshi.com/getting_started/orderbook_responses
- Kalshi signup / identity requirements: https://help.kalshi.com/en/articles/13823778-signing-up-as-an-individual
- Kalshi international access: https://help.kalshi.com/en/articles/14026044-can-i-trade-on-kalshi-from-outside-the-united-states
- Kalshi transfer methods: https://help.kalshi.com/en/articles/13823791-transfers-faq
- Kalshi crypto deposits: https://help.kalshi.com/en/articles/13823799-crypto-deposits
- Kalshi fixed-point / fractional migration: https://docs.kalshi.com/getting_started/fixed_point_migration
- Kalshi fee and balance rounding: https://docs.kalshi.com/getting_started/fee_rounding
- Kalshi July 7, 2026 fee schedule: https://kalshi.com/docs/kalshi-fee-schedule.pdf
