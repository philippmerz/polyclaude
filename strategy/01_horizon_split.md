# Two-sleeve architecture — 2026-04-25 (sizing rules superseded 2026-05-09)

> **MAJOR UPDATE 2026-05-09:** the per-sleeve $-caps below are SUPERSEDED by Kelly+ρ-adjusted constrained portfolio math. Use `scripts/portfolio_kelly.py --constrained` for sizing decisions. The naive cluster $-cap (30% × sleeve target) was found to double-count risk in clusters with anti-correlated tail paths (Iran peace-deal vs Iran regime-fall scenarios are MUTUALLY EXCLUSIVE — naive single-ρ analysis was wrong). Full reasoning in journal 2026-05-09 entries.
>
> **Horizon constraint (clarified 2026-05-08):** polyclaude bankroll is locked to **<1y holding horizon per position**. Multi-year plays = operator's IBKR sleeve. The "1-year long sleeve" framing below is preserved for historical reference; in practice the entire polyclaude book holds <1y.
>
> **Bankroll growth (2026-05-09):** ~$170 (was $70 at kickoff). Sizing math updated accordingly via portfolio_kelly + brownian_bridge_fv.

The bankroll is partitioned into two evaluation sleeves with different time horizons. Each sleeve is sized, researched, and reported independently, but they share the same operational tooling, philosophy, and risk caps from `00_philosophy.md`.

## Allocation

| Sleeve | Eval window | Capital target | % of bankroll | Trade duration |
|---|---|---|---|---|
| Long-horizon | 1 year (2026-04-25 → 2027-04-25) | $46.67 | 2/3 | up to ~12 months; carry / longer-thesis |
| Short-horizon | 1 month (2026-04-25 → 2026-05-25) | $23.33 | 1/3 | trades resolve within ~30 days |
| Flex / cash | n/a | residual | ~5% | unallocated buffer |

## Why split

A single eval horizon mixes apples and oranges:
- 1-year-only would mean very few signal events to evaluate forecasting accuracy until late in the year.
- 1-month-only forces high-turnover trades that compete with retail dayflow on highly efficient short-dated contracts.

A split lets me run two distinct strategies and get two clean sets of feedback: a fast pulse on calibration (short sleeve) and a slow pulse on big-thesis quality (long sleeve).

## Per-sleeve risk caps

The 15% per-ticket and 30% per-cluster caps from `00_philosophy.md` apply **within each sleeve**, computed against the sleeve target — not the full bankroll. So:

- Long sleeve cap per ticket: 15% × $46.67 ≈ **$7.00**
- Long sleeve cap per cluster: 30% × $46.67 ≈ **$14.00**
- Short sleeve cap per ticket: 15% × $23.33 ≈ **$3.50**  → *floored to Polymarket's $5 min order*, so the practical min size is the cap. **Short sleeve runs 4–6 positions max.**
- Short sleeve cap per cluster: 30% × $23.33 ≈ **$7.00**

Note: the long sleeve's existing 5 positions were sized against a bankroll-relative cap of $10.50 (15% of full $70) before this split was introduced. They're now slightly *over* the new per-ticket cap (largest ticket is $10 on Jesus and Pahlavi). Going forward I will size new long-sleeve trades against the $7 cap; the existing $10 tickets are grandfathered with the rationale that (a) they were within risk policy at the time of placement, (b) they have very low expected loss given the longshot fade thesis, and (c) closing/resizing now would lock in 1¢ of round-trip cost without a corresponding edge improvement.

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
