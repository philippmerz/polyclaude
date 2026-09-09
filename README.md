# polyclaude

Agent-assisted trading research and monitoring. Objective: maximize expected ROI within a <1-year holding horizon; evaluation at the start of 2027. Ordinary Dec-31 resolutions redeeming in early January count. A possible ~$500 top-up is conditional, not sizing capacity.

**Start here:** [agent entry point](docs/START.md) · [knowledge map](docs/INDEX.md) · [due work](notes/backlog.md) · [11-step check-in](docs/checkin.md) · [tools](scripts/README.md).

## Portfolio dashboard

Snapshot **2026-09-09 02:01 UTC**, not a live quote. This documentation cleanup did not refresh balances or change positions.

| Metric | Value |
|---|---:|
| Whole-account indicative net liquidation | ~$177.47 |
| Less included gas-token value | $6.22 |
| Trading net liquidation vs $170 contributions | ~$171.25; +$1.25 / +0.74%, **before VM/other costs** |
| Authoritative marked bankroll, 02:01:44 UTC | $184.49 |
| PM midpoint / fee-and-depth estimate | $151.03 / $144.0099083 |
| Settled realized / open liquidation P&L | +$14.44 / −$13.19 |

Net liquidation replaces the PM midpoint in `bankroll.py`'s total with indicative bid-depth proceeds. It is sequential, excludes withdrawal/transfer costs, and is **not synchronized or freshness-verified executable cash**. All 13 position walks covered their quantities, but not every book's identity/age was independently verified. See [reporting definitions](docs/reference/reporting.md) and the [Sep-9 journal entry](notes/journal.md#2026-09-09-0200-utc--bounded-full-check-bid-recovery-no-trade).

- 13 active PM positions, $157.20 cost. Authenticated orders at 02:01:06: five LIVE SELLs with matched size zero; no BUYs or Apple orders. No order change this tick.
- Approximate reserves: $2.12 pUSD, $16.11 Polygon Aave, $7.87 Arbitrum Aave; Ostium has no open position. Tiny Hormuz claim dust is not economic exposure.
- Thesis summary: HOLD / no add pending evidence. Official OpenAI/Google tool-enabled HLE results already exceed held thresholds; the remaining thesis is **named-board/resolver behavior**, not lack of capability. Duma and MetaMask must be assessed as protected complete groups. Current assumptions live in [priors](notes/portfolio_kelly_priors.json), not this dashboard.
- Next dated reviews: **Sep-9 Apple 18:30 UTC**, **AVAV 22:00 UTC**. Exact triggers, sources and reminder handling: [backlog](notes/backlog.md).

## How the project runs

Bounded scheduled checks at 02:00/14:00 UTC; light reviews at 06:00/10:00/18:00/22:00; Sunday long-term research at 16:00. News, opportunity and health watchers handle waiting. No perpetual agent goal or idle continuation loop.

The [operations runbook](strategy/02_operations.md) owns dispatch, daemon, incident and Telegram procedures. The operator's mandate is autonomous operation for maximum expected ROI, subject to the existing strategy and execution gates. Equities and multi-year candidates remain research surfaces for the operator's personal IBKR sleeve.

Telegram uses the **private one-time** reader: `ALREADY_CLAIMED` means no action/reply; `EXPIRED` means only a generic request to resend. Scheduled Telegram summaries are material-only.

## Knowledge layout

- [Strategy](strategy/00_philosophy.md): mandate, entry gates, sizing and exit policy.
- [Lessons](strategy/01_lessons.md): distilled topic guide; details only on demand.
- [Research index](research/INDEX.md): dated findings, rejected hypotheses, revisit gates.
- [Knowledge map](docs/INDEX.md): canonical files, machine state, history retrieval and maintenance.
- [Founding charter](PRIMER.md): historical operator message, not current instructions.

`notes/` retains audit history and machine state; `data/` and `logs/` hold generated artifacts, not onboarding material.
