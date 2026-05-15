# Two-sleeve architecture — 2026-04-25 (sizing rules superseded 2026-05-09)

> **MAJOR UPDATE 2026-05-09:** the per-sleeve $-caps below are SUPERSEDED by Kelly+ρ-adjusted constrained portfolio math. Use `scripts/portfolio_kelly.py --constrained` for sizing decisions. The naive cluster $-cap (30% × sleeve target) was found to double-count risk in clusters with anti-correlated tail paths (Iran peace-deal vs Iran regime-fall scenarios are MUTUALLY EXCLUSIVE — naive single-ρ analysis was wrong). Full reasoning in journal 2026-05-09 entries.
>
> **Horizon constraint (clarified 2026-05-08):** polyclaude bankroll is locked to **<1y holding horizon per position**. Multi-year plays = operator's IBKR sleeve. The "1-year long sleeve" framing below is preserved for historical reference; in practice the entire polyclaude book holds <1y.
>
> **Bankroll growth (2026-05-09):** ~$170 (was $70 at kickoff). Sizing math updated accordingly via portfolio_kelly + brownian_bridge_fv.

## Current operating model (2026-05-13+)

Single sleeve, <1y horizon, Kelly+ρ-adjusted sizing via `scripts/portfolio_kelly.py --constrained`. The historical two-sleeve split below is preserved for reference but not in active use.

**Filters (effective post-R-U strategy pivot, 2026-05-11):**
- Mechanical-resolution markets only — skip subjective "permanent peace deal / ceasefire / qualifies-as-X" markets
- 10pp+ edge bar at entry (was 5pp)
- `scripts/polyclaude_enter.py` mandatory for every entry — enforces umaResolutionStatus check + Kelly sizing
- Max 5 concurrent active positions

**Target allocation:** 60% Aave reserve (hurdle floor 3.4-3.8% APY) / 40% PM selective.

## Historical reference (April 2026 architecture)

The original framing partitioned a $70 bankroll into two sleeves:
- Long-horizon ($46.67, 2/3): 1-year eval, ~12-month trade duration, carry/longer-thesis
- Short-horizon ($23.33, 1/3): 1-month eval, ~30-day trade duration
- Flex/cash: residual

Per-sleeve caps were 15% per-ticket / 30% per-cluster against sleeve target. This was REPLACED 2026-05-09 by Kelly+ρ math after anti-correlation insight on Iran cluster (peace-deal scenario and regime-fall scenario are mutually exclusive tail paths; naive single-ρ analysis double-counted risk).

## File layout

- `strategy/00_philosophy.md` — overall philosophy (sleeve-agnostic).
- `strategy/01_horizon_split.md` — this file.
- `research/_long_*.md` — long-sleeve research notes.
- `research/_short_*.md` — short-sleeve research notes.
- `research/<slug>.md` — single-market research notes (frontmatter declares the sleeve).
- `notes/journal.md` — chronological log, both sleeves, latest at bottom.
- `notes/pnl_weekly.md` — weekly report; per-sleeve P&L and per-sleeve commentary.

## Eval criteria

At the 1-month checkpoint (2026-05-25):
- Short sleeve: realised P&L on resolved markets, plus mark-to-market on unresolved. Brier score on each prediction (calibration).
- Long sleeve: mark-to-market only; no realised resolutions expected this early.

At the 1-year checkpoint (2027-04-25):
- Both sleeves: realised P&L; calibration; per-thesis post-mortems.
- Comparison vs. baselines: a $70 USDC held flat (0% return), and a hypothetical "buy NO on every >10% YES tail market" passive strategy.
