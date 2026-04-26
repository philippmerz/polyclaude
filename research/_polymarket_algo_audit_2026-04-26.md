# Polymarket algorithmic-trading feasibility audit (2026-04-26)

> Operator asked whether automated/algorithmic strategies on Polymarket — particularly the much-discussed BTC 5-minute Up/Down markets — could be profitable on our 2-CPU / 2-GB / 15-GB Polygon-only setup with a $70 bankroll. Honest answer below; verdict is *no, not at this scale*, with the specific reasons captured so future ticks (or future-me at higher bankroll) can re-evaluate cleanly.

## What the markets actually look like

**Polymarket has three relevant short-tenor crypto product families:**
1. **5-minute Bitcoin Up/Down** (`/crypto/5M`). Each market resolves whether BTC's Binance close at the end of a fixed 5-minute window is ≥ open. New markets fire every 5 minutes around the clock.
2. **Hourly BTC Up/Down**. Same mechanic on the BTC/USDT 1H candle (currently ~$40k volume per market for active ones).
3. **Daily BTC level ladders** (`Bitcoin above $XXk on April 26`). Twelve-strike ladder on 24-hour-ahead settlement, ~$100k–280k volume per strike, very tight prices near expiry.

**Resolution source for all three: Binance BTC/USDT** spot, deterministically read from a specific candle. No oracle ambiguity.

## Fee structure (the decisive number)

Pulled live from gamma-api on the BTC > $76k April-26 market and the Hourly Up/Down — both fire the same fee schedule:

```
{ exponent: 1, rate: 0.072, takerOnly: True, rebateRate: 0.2 }
```

That's an **edge-aware** fee: `fee_per_trade = rate × min(p, 1−p) × notional`. So:
- At **p = 0.50** (the fair-coin-flip case), takers pay **3.6%** per side → 7.2% round-trip.
- At **p = 0.95** (a near-certain "yes"), takers pay **0.36%** per side.
- At **p = 0.99**, takers pay **0.072%** per side.

**Maker rebate** is 20% of the same edge-aware amount — so a maker resting an order *inside* the spread *and* getting hit pays a much smaller effective fee. **Critically**, rewards programs (`rewardsMinSize: 50`, `rewardsMaxSpread: 4.5`) only pay rebates to makers placing orders **≥ $50** within 4.5¢ of the mid. Our $5 minimum tickets are an order of magnitude below that.

So the fee picture for our setup:
- **Taking 5-min markets at p ≈ 0.5**: round-trip fee 7.2%. Need a > 7.2% edge per trade just to break even.
- **Taking daily ladder markets at p ≈ 0.99**: round-trip fee 0.14%. Tractable but only worth ~1% per bet.
- **Maker quoting**: gas-cheap on Polygon (zero fees on filled orders for makers in rewards-eligible markets), but our $5 size is too small to qualify for rebates.

## What public bot strategies actually achieve

I cross-checked the cottage industry of Polymarket BTC bots (CoinDesk Feb 2026 piece, Medium write-ups by Liu and Benjamin-Cup, Archetapp's gist, ThinkEnigmatic's bot-arena repo). The honest summary:

| Strategy | Mechanism | Achievable edge | Compatible with our setup? |
|---|---|---|---|
| Last-second TA at T-10s | Read Binance spot, fire trade right before window close | Live win rate **25–27%** vs ~53% breakeven | **No** — markets are efficient at short horizons; fees dominate |
| YES+NO ≠ $1 cross-leg arbitrage | Fire when the two sides briefly mis-sum | 1.5–3% per trade across many trades | **No** — opportunities last milliseconds; loses the latency race to AWS/dedicated infra bots |
| Market-making (passive maker) | Quote both sides around mid; collect spread + rebates | Variable, often 5–15% APY for serious participants | **No** — rebate floor is $50/order, our $5 min disqualifies us |
| Adaptive bot arena (4 competing strategies) | Toy / educational rather than production-profitable | n/a | **No** |

The 53% breakeven on a 50/50 binary is the dispositive number: it's *below* the fees-and-spread headwind, which is why every retail TA-bot that's been honestly benchmarked underperforms it.

## Where my time would *not* be better spent here

- **No GPU**: rules out any latency-critical inference; even small transformers on CPU are 100–1000× slower than the median Polymarket bot's reaction time.
- **Polygon RPC latency**: 100–300 ms round-trip to gamma/CLOB. A 5-min market starts pricing the resolution within seconds of the open; by the time we've fetched + signed + posted an order, the edge is gone.
- **$5 ticket vs $50 rewards floor**: even in a fee-friendly market we don't qualify for the rebates that turn maker quoting into a positive-EV strategy.
- **Bankroll variance**: a $5 stake at 50% probability with 7.2% drag has a one-trade variance of ~$5; ten consecutive losers wipes out 70% of the bankroll. We're not capitalised for HFT-style law-of-large-numbers strategies.

## Where there *might* be edge that survives our constraints

Honest list, even given the verdict:

1. **Daily BTC ladder fades on extreme strikes** (e.g., BTC > $80k YES at 0.0105 with current spot ~$77k) — basically the longshot tail-fade pattern we already use on Polymarket-non-crypto. Buy NO at 0.99 → +1% if BTC stays under $80k for a day. Edge ≈ comparable to Atletico-top-4 carry. **Already in the playbook.** Not a new strategy.
2. **Maker-quoting in long-tenor liquid markets** when bankroll ≥ $250 (so a $50 quote is < 20% of bankroll). Polymarket's liquidity-rewards program is real for traders at that scale.
3. **Cross-venue arbitrage**: Polymarket vs. Kalshi for same-event contracts. Killed by US-bank-account requirement on Kalshi for now.
4. **Latency-insensitive reflexivity**: pre-positioning for known catalysts (Fed announcements, earnings, sports starts) — already what we do with the discretionary book.

## Verdict

**No automated trading deployment recommended at the current $70 bankroll and 2 CPU / 2 GB / Polygon-only compute envelope.** The fee structure and rebate floors make all the "obvious" Polymarket bot strategies negative-expected-value at our scale, and faster competitors (with dedicated infra and 100x our capital) have already arbed the obvious mispricings.

The bot the operator vaguely remembered ("insane returns on BTC 5-min bets") is most likely either: (a) a viral lucky-streak post that wasn't representative, (b) a maker-quoting bot operating well above the $50 rewards floor, or (c) backtested-not-live numbers that didn't survive paper-to-production.

**Update (2026-04-26 ~08:30 UTC) — operator forwarded the actual account they remembered**: `0xde17f7144fbd0eddb2679132c10ff5e74b120988` (35.6k profile views on Polymarket). It is **not a profitable bot**. It is **a -$727,450.80 lifetime P&L cautionary tale** — 1,168 predictions, all on the daily/weekly BTC range markets that this audit predicted would lose money under the 7.2% taker fee. The "biggest win: $195k" headline is the lottery-winner story that propagates online; the matching $922k of losses around it is what doesn't. Direct empirical confirmation that the strategy described in the rumour is a *known capital-destroyer*, not a hidden edge. This is what survivorship bias on social media looks like in practice.

## Trigger conditions for revisiting

- **Bankroll ≥ $250–500** → maker quoting in rewards-eligible markets becomes viable; revisit Polymarket LP strategies.
- **Polymarket changes fee/rebate structure on short-tenor crypto markets** (specifically: removes the $50 rewards floor or drops the 7.2% taker rate).
- **Operator forwards a specific bot/article with a verifiable edge** I haven't accounted for here.
- **Compute upgrade** that closes the latency gap to ≤ 50 ms RTT to Polygon CLOB — at current cloud pricing that's a $50–100/month VM. Trigger when bankroll covers it from yield, not when we'd be paying out of principal.

## Sources
- [Polymarket 5-minute crypto bucket](https://polymarket.com/crypto/5M)
- [Polymarket markets API (gamma)](https://gamma-api.polymarket.com/markets)
- [How AI is helping retail traders exploit prediction-market 'glitches' (CoinDesk, Feb 2026)](https://www.coindesk.com/markets/2026/02/21/how-ai-is-helping-retail-traders-exploit-prediction-market-glitches-to-make-easy-money)
- [AI-Augmented Arbitrage in Short-Duration Prediction Markets (Liu, Mar 2026)](https://medium.com/@gwrx2005/ai-augmented-arbitrage-in-short-duration-prediction-markets-live-trading-analysis-of-polymarkets-8ce1b8c5f362)
- [Unlocking Edges in Polymarket's 5-Minute Crypto Markets (Benjamin-Cup)](https://medium.com/@benjamin.bigdev/unlocking-edges-in-polymarkets-5-minute-crypto-markets-last-second-dynamics-bot-strategies-and-db8efcb5c196)
- [Adaptive trading-bot arena for Polymarket BTC 5-min (ThinkEnigmatic, GitHub)](https://github.com/ThinkEnigmatic/polymarket-bot-arena)
- [Polymarket BTC 5-Minute Up/Down Trading Bot (Archetapp gist)](https://gist.github.com/Archetapp/7680adabc48f812a561ca79d73cbac69)
