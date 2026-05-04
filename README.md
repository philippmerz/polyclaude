# polyclaude

Autonomous, Claude-managed trading project. Mandate: maximize return. Two sleeves, fully decentralized, no CEX, no KYC.

**Last updated:** 2026-05-04 14:00 UTC (cron tick)

---

## Portfolio summary

### Polymarket sleeve — `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B` (Polygon)

Public views: [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) · [Polygonscan](https://polygonscan.com/address/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) · [DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)

Bankroll $70, two-horizon split per [`strategy/01_horizon_split.md`](strategy/01_horizon_split.md). 9 positions filled 2026-04-25, all carry / longshot-fade theses.

| Market | Side | Cost | MTM | P&L |
|---|---|---:|---:|---:|
| Pahlavi leads Iran 2026 | NO | $10.00 | $10.02 | +$0.02 |
| Jesus returns by 2027 | NO | $10.00 | $10.14 | +$0.14 |
| US confirms aliens by 2027 | NO | $9.00 | $9.28 | +$0.28 |
| **US-Iran peace deal by May 31** | NO | $6.99 | $8.72 | **+$1.73** |
| Iranian regime falls by 2027 | NO | $7.00 | $7.22 | +$0.22 |
| Trump out before 2027 | NO | $7.00 | $7.21 | +$0.21 |
| Amy Acton — 2026 Ohio Gov | YES | $4.99 | $5.04 | +$0.05 |
| Latvia top 10 — Eurovision | NO | $5.00 | $5.27 | +$0.27 |
| Atletico Madrid top 4 — La Liga | YES | $4.97 | $4.96 | −$0.01 |
| **Total** | | **$64.95** | **$67.85** | **+$2.90** |

Venue-specific buffer: $5.05 USDC.e + 53.81 POL gas reserve. Project-wide buffer is implicitly satisfied by Aave deposits below (withdrawable + bridgeable in <3 min). Initial-portfolio reasoning: [`research/_long_initial.md`](research/_long_initial.md), [`research/_short_initial.md`](research/_short_initial.md).

> **Operational note (2026-05-04)**: Polymarket migrated to CLOB v2 + a new collateral token pUSD on Apr 28, 2026 (per their [help docs](https://help.polymarket.com/en/articles/14762452)). Both first-party SDKs are still on v1 schemas and get rejected. Polyclaude ships its own v2 signer ([`scripts/clob_v2.py`](scripts/clob_v2.py)) — direct REST + EIP-712, no SDK dependency. Verified end-to-end 2026-05-04 (place + cancel both 200 OK on a test order). Onramp set: 5 USDC.e wrapped to pUSD via [CollateralOnramp](https://polygonscan.com/address/0x93070a847efEf7F70739046A929D47a521F5B8ee), pUSD approved to both v2 exchanges. Existing 9 v1 positions resolve naturally on the v1 stack (USDC.e settlement). Schema details: [`research/_polymarket_v2_schema_2026-05-03.md`](research/_polymarket_v2_schema_2026-05-03.md).

### Crypto sleeve — `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` (multi-chain)

Public views: [DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) · [Arbiscan](https://arbiscan.io/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) (Ostium + Aave-Arb) · [Basescan](https://basescan.org/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) (Aave-Base) · [Polygonscan](https://polygonscan.com/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) · [Optimism](https://optimistic.etherscan.io/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)

Note: Ostium has no public per-address trader profile (wallet-connect SPA). DeBank aggregates Ostium positions + Aave aUSDC + cross-chain balances in one view; Arbiscan shows the raw on-chain trace including each Ostium open/close.

Bankroll $100. Funded 2026-04-29. Strategy + tier-ranked plays in [`research/_crypto_landscape_2026-04-27.md`](research/_crypto_landscape_2026-04-27.md).

**Original allocation plan (2026-04-29):** $50 Ostium / $30 Limitless arb / $10 PLUME / $10 reserve. Deployed differently after live diligence:
- **Ostium**: 3 active positions ($14.67 collateral). Remaining budget held back; volume rotation as positions close.
- **Limitless ↔ Polymarket arb**: scanner shipped (`scripts/limitless_arb_scan.py`), live-quote auto-executor downgraded to inspector-only after EV analysis showed expected value goes negative at our size given resolution-divergence risk on subjective markets. Capital re-routed to Aave.
- **PLUME**: directional buy parked indefinitely; no entry placed.
- **Aave V3 (idle yield)**: **$55.02 on Arbitrum @ 3.14% APY** (deposited 2026-04-30) + **$29.51 on Base @ 3.42% APY** (deposited 2026-04-29). Withdrawable + bridgeable in <3 min. Sets the *hurdle rate* for any new bond-like NO buy on Polymarket.

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
research/   — per-question audit memos (yield, algo trading, crypto landscape, initial portfolios, PM v2 schema)
scripts/    — Python tooling: CLOB + Ostium clients, news watcher, telegram, bridges, Aave deposits,
              decision tracker, methodology stress-test harness, status readers, emergency exits.
              clob_node/ holds a TS clob-client probe used for SDK-version diagnosis.
notes/      — chronological journal + weekly P&L reports + structured news_alerts.jsonl + decisions.json
data/       — gitignored: methodology snapshots, market discovery snapshots
```

## Operator interface

Operator messages via Telegram → `scripts/telegram_listener.py` injects them into the live Claude tmux pane. Telegram replies are **action-only** by convention: cron tick sends a structured summary (MTM Δ, material news alerts processed, actions/inactions taken, next catalyst), and material moves outside the tick window get an immediate ping. Raw RSS pings were dropped 2026-05-02 — the operator wanted decision feed, not news feed.

Convention for inbound Telegram messages: prefixing with `telegram:` or `reply on telegram:` signals the operator is on phone and a Telegram reply is required. Non-prefixed messages = at the laptop, local reply suffices.
