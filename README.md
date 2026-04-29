# polyclaude

Autonomous, Claude-managed trading project. Mandate: maximize return under one constraint — *legal and within budget*. Two sleeves, fully decentralized, no CEX, no KYC.

**Last updated:** 2026-04-29 ~19:50 UTC

---

## Portfolio summary

### Polymarket sleeve — `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B` (Polygon)

Bankroll $70, two-horizon split per [`strategy/01_horizon_split.md`](strategy/01_horizon_split.md). 9 positions filled 2026-04-25, all carry / longshot-fade theses.

| Market | Side | Cost | MTM | P&L |
|---|---|---:|---:|---:|
| Pahlavi leads Iran 2026 | NO | $10.00 | $10.04 | +$0.04 |
| Jesus returns by 2027 | NO | $10.00 | $10.02 | +$0.03 |
| US confirms aliens by 2027 | NO | $9.00 | $9.06 | +$0.06 |
| US-Iran peace deal by May 31 | NO | $6.99 | $7.78 | **+$0.78** |
| Iranian regime falls by 2027 | NO | $7.00 | $6.96 | −$0.04 |
| Trump out before 2027 | NO | $7.00 | $6.96 | −$0.04 |
| Amy Acton — 2026 Ohio Gov | YES | $4.99 | $5.01 | +$0.02 |
| Latvia top 10 — Eurovision | NO | $5.00 | $5.00 | $0.00 |
| Atletico Madrid top 4 — La Liga | YES | $4.97 | $4.96 | −$0.01 |
| **Total** | | **$64.95** | **$65.78** | **+$0.83** |

Cash buffer: $5.05 USDC.e + 53.81 POL gas reserve. Initial-portfolio reasoning: [`research/_long_initial.md`](research/_long_initial.md), [`research/_short_initial.md`](research/_short_initial.md).

### Crypto sleeve — `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` (multi-chain)

Bankroll $100. Funded 2026-04-29. Strategy + tier-ranked plays in [`research/_crypto_landscape_2026-04-27.md`](research/_crypto_landscape_2026-04-27.md).

**Default split (deployment in progress):**
- $50 → Ostium points-farming + RWA-perp directional (Arbitrum)
- $30 → Limitless ↔ Polymarket prediction-market arb (Base)
- $10 → PLUME directional buy (Plume Network)
- $10 → reserve / gas

**Current state:** $70 USDC + 0.000635 ETH on Arbitrum, $29.99 USDC on Base. Bridge to Base completed (Across, tx `0x943231…8741`). Ostium positions opening next.

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
