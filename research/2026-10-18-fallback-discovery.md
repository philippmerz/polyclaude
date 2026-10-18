# Fallback discovery — 2026-10-18

Bounded public-market scan for the 09:34 UTC fallback tick. Fact collection only; no priors, probability estimates, portfolio judgment, or trade authorization were produced.

## Capture and coverage

| Profile | Fetched scope and stop | Filtering / output |
|---|---|---|
| Primary | Gamma `/markets`: 1,000 rows, 10/10 pages, `page_cap`; incomplete. | 603 eligible before rank cap; 80 retained; 523 omitted by top-80. Rejections: 319 liquidity, 38 horizon, 36 past deadline, 3 spread, 1 missing deadline. |
| Thin tail | Gamma `/events`: 2,000 event rows, 50,165 unique member markets, 139 duplicate member rows, 20/20 pages, `page_cap`; incomplete. | 2,648 passed filters and retained; top omission 0. Rejections: 15,761 liquidity, 13,556 volume, 13,251 not tradable, 3,788 win-assumed hurdle, 303 horizon, 287 past deadline, 531 spread, 40 missing deadline. The 3.0544% hurdle and 3-day floor are a dominant-side win-assumed carry screen, not expected return; it may omit opposite-side cases. |

Both snapshot hashes match their sidecars and the context-batch current proofs. Primary proof: `c9bb6467b40d862b89e4607a0cedbd8483f3a337cf76f778e95d58b795a4388a`; thin-tail proof: `76090619b7df91c8e3d002538fa31c9e3d0af05cfac571ddf0bbdcbecb849e4f`. The primary context comparison has 71 prior rows absent from the filtered shortlist and 523 eligible top omissions. Thin-tail has 1,884 prior rows absent and a changed `hurdle_apy` parameter; these are cohort/filter differences, not closures. All four primary and 137 thin-tail emitted Markdown batches were parsed; declared batch sizes matched parsed rows. Primary batches contain 72 entries; 8 of 80 current primary rows did not enter the delta queue. Thin-tail batches contain 2,404 entries (1,532 new to this filtered snapshot, not necessarily new listings; 450 changed, 422 event context); 244 of 2,648 current rows did not enter the delta queue and remain unreviewed. Parser and integrity counts are distinct from factual/semantic triage: all four primary batches (72 entries) and thin-tail batches 1–46 (774 entries) have now received row-by-row semantic triage, documented in [batch review A](2026-10-18-fallback-batch-review-a.md). That review did not assign probabilities or establish executable value. Thin-tail batches 47–137 (1,630 entries) remain assigned to the other reviewers; rows outside each delta queue (8 primary, 244 thin-tail) also remain unreviewed.

## Material observed price changes

Four exact thin-tail markets moved at least 3pp with 24h volume above $50,000 between the Oct 15 and Oct 18 snapshots. These are quote changes only; no cause, fair value, or side was assessed. Criteria hashes and execution identities did not change for the matched markets.

| Market ID / condition ID | YES price, prior → current | 24h volume | Outcome token IDs (YES, NO) |
|---|---:|---:|---|
| `3120760` / `0x2a4fcda5c1598fc8621cf96cabc410f9f23a2d0336c3bff5070a37a663d39e94` — NATO x Russia clash by Oct 31 | 0.060 → 0.095 (+3.5pp) | $123,738 | `90103249718343334756773580827701144244122903469501608441410963092372041632343`, `66797176836865406644675050248194264952001579179703527537658211196864343226792` |
| `5697539` / `0x1175651306e9ae39991642dcff3fd96778ae0301fc44c7f5565251fc2bb68d31` — Israel x Iran ceasefire through Oct 21 | 0.915 → 0.958 (+4.3pp) | $70,315 | `24399767988117113521472412724678339180207513110495231843644050348352296275787`, `95621696205739201037602073257017921677890684949833910344379917839419913867662` |
| `5686979` / `0x04fb634139d4654febf4b62c425b209806e06d9eff93ac2e7c5301ecdaf5e4ca` — US x Iran ceasefire through Oct 22 | 0.870 → 0.945 (+7.5pp) | $61,151 | `11703355753646866721510451780813586747644200170798817311988936815535980370261`, `65420996630654354480054098878673482065505905636022385586010587347634944011067` |
| `2589812` / `0xdf9bf27ee5757c55b44b8b9826ddc9ec3a8809aa3278634c45edbb7fc8f1a3e3` — no Fed rate change after Oct meeting | 0.735 → 0.865 (+13.0pp) | $54,238 | `111061902544814266207267295505639408607400625795891618462682726460921782993748`, `42038775866198212615491650114881818219665139981763207699110491615333273795415` |

These identities and full public criteria are in [the thin-tail snapshot](../data/snapshots/shortlist_20261018T093711188860Z_thin_tail.json); current/prior selection and hashes are in its adjacent sidecars.

## Structural, sports, and other unreviewed cases

- **Sports consensus:** 85 sports markets passed the 36-hour scanner filters; 20 were displayed, with consensus attempted for the top three pregame rows. Karmine Corp vs MVK Esports (`5838886`, condition `0xde91800e376946d961489798727a683e032fc5eae108a3a4f902a3a3a44fbbe5`) matched Sportsbet at 0.900 versus PM 0.885 (−1.6pp, $198,415 volume), below the 3pp threshold. Packers −7.5 (`5130152`, condition `0x97848a7498bccc1fc83899dc3cfa5544f94780bb1a88c24cc7fd3c12e0d79962`) failed exact ordered-outcome matching. “Will Coventry City FC win on 2026-10-19?” had no matched opponent in the question/rules; text output did not provide its market ID. The other 17 displayed markets received no consensus lookup; none was independently verified as a >3pp case. One in-play row was explicitly skipped. Consensus failures and unlooked rows remain unreviewed. The scanner is capped at 6 pages, but does not report pages fetched or its pagination stop reason; coverage is unknown.
- **Macro, no consensus by request:** five markets passed the scanner's $30,000 volume filter. They remain without independent benchmarks: market IDs `2589814` (Fed +50bp Oct, $244,545 vol), `3215006` (−25bp Dec, $62,417), `2589811` (−25bp Oct, $61,085), `2589812` (no change Oct, $54,238; also in the changed-price table), and `2589810` (−50bp Oct, $47,196). No probability judgment was made. Its 8-page cap and actual pagination stop are not reported, so universe coverage is unknown.
- **Favorite-price profile:** 40 of 46 rough survivors received live book walks; 6 were omitted by the walk cap, 40 favorite books validated, 0 missing/invalid favorite books, and 27 candidate-only rows were emitted. The profile supplies no population probability or edge. All six emitted markets above $50,000 volume remain unreviewed: `5697539` Israel x Iran Oct 21 ($70,315), `5686979` US x Iran Oct 22 ($61,151), `5340069` Flávio Bolsonaro margin 8–12% ($140,822), `3128888` US ends Iranian blockade by Oct 31 ($57,906), `3758964` Bab el-Mandeb effectively closed by Oct 31 ($91,836), and `3120760` NATO x Russia clash by Oct 31 ($123,738). Every row is `candidate_only`, `execution_ready=false`, and requires a fresh rewalk.
- **Consistency baskets:** 5,001 open markets across 656 events/33 pages reached the 5,000-market soft cap (`market_cap`), so coverage is incomplete. The scanner found 292 midpoint deviations above 0.5%; 200 structural groups were in the live-relevant queue, 20 requested (10 priority, 10 exploration), 144 legs attempted, 8 groups validated, 12 quote-failed, and 180 unquoted. No provisional positive survived. The 12 failed member IDs were stale books: `5766588` (1,059s), `5766654` (1,592s), `5767427` (3,248s), `5766520` (1,025s), `5769423` (760s), `5479332` (313s), `5616751` (663s), `5648377` (626s); and no asks: `5767449`, `5766643`, `5818521`, `5766432`. Remaining structural rows are unreviewed in the bounded queue; a midpoint deviation is not an executable candidate.
- **Event monotonicity:** 1,388 events fetched, 1,104 multi-market events inspected, 15/15 pages, `max_pages`, no fetch failures, and no violations. Coverage is incomplete at the cap, so this is not a venue-wide zero.

## Receipts

All seven complete raw scanner stdout/stderr outputs were read; each required command completed with return code 0. The sports, macro, favorite-price, and consistency results still have explicit lookup/quote limitations above; no independent probabilities or fresh execution-ready books were established. Timed command receipts and stdout/stderr SHA-256 values are in [run_receipts.jsonl](../logs/checkin_20261018T0934_fallback/discovery/run_receipts.jsonl); snapshot and output hashes are in [artifact_manifest.json](../logs/checkin_20261018T0934_fallback/discovery/artifact_manifest.json). Complete scanner outputs, all context batches, consistency JSON/Markdown, and prior quote-history baseline are in [the run directory](../logs/checkin_20261018T0934_fallback/discovery/). `data/snapshots/shortlist_latest.json` now points to the thin-tail capture; the prior target and target hash are recorded in the alias baseline receipt.


## Completed fallback batch coverage

All **4 primary and 137 thin-tail batches** subsequently received bounded offline
factual/semantic row review: [A](2026-10-18-fallback-batch-review-a.md) covers
primary1–4/thin-tail1–46, [B](2026-10-18-fallback-batch-review-b.md) covers47–92,
and [C](2026-10-18-fallback-batch-review-c.md) covers93–137. Root reviewed the
reports and corrected category/horizon overstatements. All cases remain unvalued;
full captured criteria/source checks cover flagged clusters only, and no new
external facts, probabilities or executable edge were established by this pass.
Underlying equity/company subject alone does not exclude an on-chain PM contract;
retired brokerage research was not revived. Exact dates and lawful eligibility
remain per-instrument questions. The252 current rows outside the delta queues
(8primary+244thin-tail) and all upstream omissions remain unreviewed.
