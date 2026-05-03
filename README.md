# polyclaude

Autonomous, Claude-managed trading project. Mandate: maximize return. Two sleeves, fully decentralized, no CEX, no KYC.

**Last updated:** 2026-05-03 ~14:00 UTC (cron tick)

---

## Portfolio summary

### Polymarket sleeve — `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B` (Polygon)

Public views: [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) · [Polygonscan](https://polygonscan.com/address/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) · [DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)

Bankroll $70, two-horizon split per [`strategy/01_horizon_split.md`](strategy/01_horizon_split.md). 9 positions filled 2026-04-25, all carry / longshot-fade theses.

| Market | Side | Cost | MTM | P&L |
|---|---|---:|---:|---:|
| Pahlavi leads Iran 2026 | NO | $10.00 | $9.99 | −$0.01 |
| Jesus returns by 2027 | NO | $10.00 | $10.15 | +$0.15 |
| US confirms aliens by 2027 | NO | $9.00 | $9.28 | +$0.28 |
| **US-Iran peace deal by May 31** | NO | $6.99 | $8.61 | **+$1.62** |
| Iranian regime falls by 2027 | NO | $7.00 | $7.13 | +$0.13 |
| Trump out before 2027 | NO | $7.00 | $7.21 | +$0.21 |
| Amy Acton — 2026 Ohio Gov | YES | $4.99 | $5.03 | +$0.04 |
| Latvia top 10 — Eurovision | NO | $5.00 | $4.97 | −$0.03 |
| Atletico Madrid top 4 — La Liga | YES | $4.97 | $4.96 | −$0.01 |
| **Total** | | **$64.95** | **$67.32** | **+$2.38** |

Cash buffer: $5.05 USDC.e + 53.81 POL gas reserve. Initial-portfolio reasoning: [`research/_long_initial.md`](research/_long_initial.md), [`research/_short_initial.md`](research/_short_initial.md).

### Crypto sleeve — `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` (multi-chain)

Public views: [DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) · [Arbiscan](https://arbiscan.io/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) (Ostium + Aave-Arb) · [Basescan](https://basescan.org/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) (Aave-Base) · [Polygonscan](https://polygonscan.com/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) · [Optimism](https://optimistic.etherscan.io/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)

Note: Ostium has no public per-address trader profile (wallet-connect SPA). DeBank aggregates Ostium positions + Aave aUSDC + cross-chain balances in one view; Arbiscan shows the raw on-chain trace including each Ostium open/close.

Bankroll $100. Funded 2026-04-29. Strategy + tier-ranked plays in [`research/_crypto_landscape_2026-04-27.md`](research/_crypto_landscape_2026-04-27.md).

**Default split (deployment in progress):**
- $50 → Ostium points-farming + RWA-perp directional (Arbitrum)
- $30 → Limitless ↔ Polymarket prediction-market arb (Base)
- $10 → PLUME directional buy (Plume Network)
- $10 → reserve / gas

**Current state:** 3 active Ostium positions ($14.67 collateral). Idle USDC parked in Aave V3: **$55 on Arbitrum @ 4.152% APY** (deposited 2026-04-30) + **$29.50 on Base @ 3.375% APY** (deposited 2026-04-29). Withdrawable in <1 min for any opportunity. $35 of the Ostium budget still pending operator greenlight.

**Open Ostium positions:**

| Pair | Side | Lev | Net collateral | Notional | Entry | Mark | P&L |
|---|---|---:|---:|---:|---:|---:|---:|
| XAU/USD (gold) | LONG | 5x | $4.89 | $24.46 | $4,543.48 | $4,581.24 | +$0.20 |
| SPX/USD | LONG | 5x | $4.89 | $24.46 | $7,167.41 | $7,172.61 | +$0.02 |
| NDX/USD | SHORT | 5x | $4.89 | $24.46 | $27,368.69 | $27,460.68 | −$0.08 |
| **Total** | | | **$14.67** | **$73.39** | | | **+$0.14** |

Pair-trade structure (long SPX + short NDX) keeps the equity exposure roughly delta-neutral; XAU long is a separate macro bet. A first crypto-pair Ostium attempt (long ETH 5x) on April 29 sat in Stork-oracle queue ~56 min and was force-resolved via `openTradeMarketTimeout` (collateral refunded). Crypto-pair opens were degraded that day; non-crypto opens filled in seconds. Pivoted to gold/indices/equities going forward.

Skipped/dropped: pump.fun retail sniping, HLP vault, funding-rate basis trade, LRTs (post-Kelp DAO hack April 19), MOVE, Plasma pre-July, inscriptions, Resolv, Bittensor/TAO (CEX-required, dropped permanently under decentralization constraint).

---

## Architecture

Three independent autonomy layers (full spec: [`strategy/02_operations.md`](strategy/02_operations.md)):

1. **Reactive** — `scripts/news_watcher.py` polls 11 RSS feeds every 5 min; tier-1 events auto-fire a max-effort cron tick.
2. **Scheduled** — `cron 02:00 + 14:00 UTC` runs `scripts/daily_checkin.sh`, forking the operator's interactive Claude session for context.
3. **Interactive** — `scripts/telegram_listener.py` long-polls Telegram; operator messages land directly in the running tmux pane.

Strategy: [`strategy/00_philosophy.md`](strategy/00_philosophy.md) — sizing rules, risk controls, restrictions.

## Repo map

```
strategy/   — philosophy, sleeve allocation, operations spec
research/   — per-question audit memos (yield, algo trading, crypto landscape, initial portfolios)
scripts/    — runnable Python tooling (clob client, ostium client, news watcher, telegram, bridges, status readers)
notes/      — chronological journal + weekly P&L reports
```

## Operator interface

Operator messages via Telegram → land in the live Claude tmux pane. Cron Claude updates this README each tick with current portfolio state. Blocking questions surfaced via Telegram from the live session.
