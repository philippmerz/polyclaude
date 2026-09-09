# polyclaude

Agent-assisted trading research and monitoring. Objective: maximize expected ROI within a <1-year holding horizon; evaluation at the start of 2027. Ordinary Dec-31 resolutions redeeming in early January count. A possible ~$500 top-up is conditional, not sizing capacity.

**Start here:** [agent entry point](docs/START.md) · [knowledge map](docs/INDEX.md) · [due work](notes/backlog.md) · [11-step check-in](docs/checkin.md) · [tools](scripts/README.md).

## Portfolio dashboard

Snapshot **2026-09-09 14:19 UTC**, not a live quote. No position/order change this tick.

| Metric | Value |
|---|---:|
| Whole-account indicative net liquidation | ~$176.63 |
| Less included gas-token value | $6.26 |
| Trading net liquidation vs $170 contributions | ~$170.37; +$0.37 / +0.22%, **before VM/other costs** |
| Authoritative marked bankroll, 14:19:23 UTC | $182.20 |
| PM midpoint / fee-and-depth estimate | $148.69 / $143.12 |
| Settled realized / open liquidation P&L | +$14.44 / −$14.07 |

Net liquidation replaces the PM midpoint in `bankroll.py`'s total with indicative bid-depth proceeds. It is sequential, excludes withdrawal/transfer costs, and is **not synchronized or freshness-verified executable cash**. The aggregate output does not certify full coverage for every book; targeted checks found older timestamps on four books. See [reporting definitions](docs/reference/reporting.md) and the [HLE risk review](research/2026-09-09-hle-uma-proposal-review.md).

- 13 active PM positions, $157.20 cost. Authenticated orders checked around 14:18: five LIVE SELLs with matched size zero; no BUYs or Apple orders.
- Approximate reserves: $2.12 pUSD, $16.11 Polygon Aave, $7.87 Arbitrum Aave; Ostium has no open position. Tiny Hormuz claim dust is not economic exposure.
- **HLE risk exception:** OpenAI ≥50 is now UMA `proposed`, YES/NO .997/.003, despite an unchanged named board. Proposal is not finality. Old automated HOLD conclusions are not a current underwrite of this event; no add/flip, fresh underwriting required. OpenAI ≥55 fresh 19-share NO bid-depth estimate fell to $2.57. Duma/MetaMask remain protected complete groups; HLE is correlated, not atomic. [Priors](notes/portfolio_kelly_priors.json) retain original numeric assessments pending verified resolution evidence.
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
