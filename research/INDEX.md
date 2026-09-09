# Research map

Updated 2026-09-09. This is a routing index, not a trade list. Dated scans are snapshots; historical quotes, APYs, population counts, and BUY language are noncurrent unless independently re-vetted against a current primary source and fee-aware executable depth.

## Current/recent evidence

| Memo | Status and revisit trigger |
|---|---|
| [`2026-09-08-1000-portfolio-depth-check.md`](2026-09-08-1000-portfolio-depth-check.md) | Sep 8 depth snapshot; no action. Recheck only with a synchronized executable quote and current positions. |
| [`2026-09-08-arena-source-gate-review.md`](2026-09-08-arena-source-gate-review.md) | Arena exact-contract/source gate; watch-only. Revisit on a fresh authoritative source and criteria match. |
| [`2026-09-08-calibration-cohort-audit.md`](2026-09-08-calibration-cohort-audit.md) | Ledger identity/quote reconciliation snapshot; not independent evidence or a policy change. Revisit with a new cohort or corrected provenance. |
| [`2026-09-08-hip4-metadata-gate.md`](2026-09-08-hip4-metadata-gate.md) | HIP-4 metadata gate only; no resolver formula/tradeability. Revisit when exact outcome metadata and execution gates are available. |
| [`2026-09-08-limitless-quote-audit.md`](2026-09-08-limitless-quote-audit.md) | Screening-only quote audit; identity, fees, and freshness were not execution-verified. Revisit only with fresh exact leaf books. |
| [`2026-09-08-thin-market-source-triage.md`](2026-09-08-thin-market-source-triage.md) | No qualified entry; HIP-3/source and thin-book gates incomplete. Revisit only on a measurable primary source plus executable depth. |
| [`2026-09-08-usgs-weekly-count-review.md`](2026-09-08-usgs-weekly-count-review.md) | USGS window/source-sensitive review; no entry or calibrated forecast. Revisit on the next exact release/window. |

## Stable/reference material

| Memo | Use |
|---|---|
| [`_polymarket_v2_schema_2026-05-03.md`](_polymarket_v2_schema_2026-05-03.md) | Historical v2 schema rationale. Current `scripts/clob_v2.py` is authoritative; preserve this for field/address context. |
| [`_venue_dd_drift_kalshi_2026-08-28.md`](_venue_dd_drift_kalshi_2026-08-28.md) | Venue boundary: Drift/Velocity non-deployable and Kalshi no-KYC boundary. Revisit only if policy/access changes. |
| [`_polymarket_algo_audit_2026-04-26.md`](_polymarket_algo_audit_2026-04-26.md) | Historical feasibility audit; no small-bankroll HFT/maker/BTC deployment. Revisit only with materially changed bankroll or infrastructure. |

## Historical studies and sweeps

These are preserved for methodology and negative results, not current candidates.

- [`implication_study_2026-07-15/README.txt`](implication_study_2026-07-15/README.txt) — artifact/empty; same text is not the same proposition; do not build a scanner from it.
- [`instance_sweep_2026-07-15/README.txt`](instance_sweep_2026-07-15/README.txt) and [`top150.txt`](instance_sweep_2026-07-15/top150.txt) — historical mechanical screening; no current authority.
- [`listing_study_2026-07-15/MEMO.md`](listing_study_2026-07-15/MEMO.md), [`README.txt`](listing_study_2026-07-15/README.txt), and [`analysis_main.txt`](listing_study_2026-07-15/analysis_main.txt) — mids/population did not establish a taker-entry edge; reopen only with forward paper ledger, maker pilot, or real depth.
- [`redeploy_sweep_2026-07-20/README.txt`](redeploy_sweep_2026-07-20/README.txt) — stale finalists; no current trade authority.
- [`shortdated_sweep_2026-07-15/README.txt`](shortdated_sweep_2026-07-15/README.txt) — historical near-miss sweep; no current trade authority.
- [`uma_study_2026-07-15/MEMO.md`](uma_study_2026-07-15/MEMO.md) — population study killed/no entry rule; current defensive status checks remain the operational path.

## Kimi evaluation archive

All files in [`kimi_eval_2026-07-19/`](kimi_eval_2026-07-19/) are model-evaluation artifacts, not live recommendations: [`MEMO.md`](kimi_eval_2026-07-19/MEMO.md), [`kimi_advisor_first_use_gpt6.md`](kimi_eval_2026-07-19/kimi_advisor_first_use_gpt6.md), [`kimi_advisor_marvel_sdcc_2026-07-20.txt`](kimi_eval_2026-07-19/kimi_advisor_marvel_sdcc_2026-07-20.txt), [`kimi_eval_result.md`](kimi_eval_2026-07-19/kimi_eval_result.md), [`kimi_eval_task.md`](kimi_eval_2026-07-19/kimi_eval_task.md), [`kimi_open_discovery.md`](kimi_eval_2026-07-19/kimi_open_discovery.md), and [`kimi_rebuttal.md`](kimi_eval_2026-07-19/kimi_rebuttal.md). The individual BUY/ape recommendations are withdrawn or stale; the rebuttal records the correction of equal-split/pro-rata errors.

Document ownership and machine-read contracts live in [the knowledge map](../docs/INDEX.md); source/code is authoritative for current implementation.

## Current interpretation

The operating gate is conservative: exact market identity and criteria, current primary-source evidence, time-window alignment, fee-aware depth, and risk approval are all required. “Watch,” “screening,” and historical “BUY” text are not executable state. For current operational truth, prefer the latest dated journal/check-in plus structured state files and live script output; use this catalog to find the supporting memo and its revisit condition.
