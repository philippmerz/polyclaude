# ECB October 2026 hold model: skeptical review

**Scope:** frozen case 272, market `3081965`, condition `0xf97e2e2b845a3e5ce0646ce7563cca294f58b1c23affc38010386c08627075ac`, criteria SHA-256 `68ca4cf2a11da0a01938d1478c36976d22fe8e760429758d60ed0f455087390a`. The operative event is the DFR change caused by the Oct 28–29 meeting, relative to its pre-meeting level; unrelated emergency action and MRO/marginal-lending rates do not count. This audits the probability bridge, not an adopted alternative probability or trade.

## Main challenge

A plausible **hold-dominant countermodel** could put 90–97% on no change: the Sep 10 +25bp increase was implemented Sep 16; the ECB says policy is meeting-by-meeting and not pre-committed; Lagarde’s Oct 17 statement describes stable underlying inflation and a “measured response,” while the headline acceleration is energy-led and not by itself evidence that the Council will hike again immediately. September HICP was 3.8% y/y (0.6% m/m), but the next October flash was scheduled Nov 4—after the meeting. That leaves a short window for confirming persistence before the Oct 29 decision. This countermodel is a stress case, not a calibrated estimate: the same energy shock and upward inflation-risk language can support a near-term hike.

The primary model’s 65/25/10 regime weights and within-regime outcome splits are explicitly judgmental, without historical estimation or a documented likelihood update from observations to regime membership. Its “energy broadening” branch assigns 64.5% to a hike, but the evidence cited establishes higher energy/headline inflation and risk direction, not that wages, services, expectations, or second-round effects have broadened enough by this meeting. Conversely, 65% weight on “measured pause” is also an unsupported prior. The 15pp reserve acknowledges this uncertainty but does not fix the bridge.

## Survey and arithmetic checks

The September ECB SMA October row is correctly labeled for the **October meeting**, with 68 responses: average probabilities 81.3% hold, 18.2% +25bp, 0.3% −25bp, 0.2% +50bp. But it was fielded Aug 24–26, before the Sep 10 hike and before the current energy/inflation information. It is not a post-September-hike conditional forecast. The same survey’s 84.8% +25bp September row was also pre-meeting and cannot be treated as an independent second likelihood after the September hike. The October-round questionnaire closed Oct 14, but its aggregate was scheduled Nov 2, after this contract resolves; there is no current survey result to validate the regime bridge. Cross-sectional DFR level expectations (Oct median 2.50%) are not meeting-outcome probabilities.

The saved raw probabilities reproduce when the documented 0.5% fallback-to-hold branch is applied: the regime mixture (69.500% hold, 26.050% hike, 4.450% cut) becomes 69.6525%, 25.91975%, 4.42775%. The arithmetic is consistent. The fallback weight itself is explicitly a judgment, not estimated or supported by the cited data, and should remain part of sensitivity analysis.

## Evidence that would discriminate

- Current, meeting-specific policy-path expectations or a documented forecast distribution; the stale SMA cannot provide this.
- September/October euro-area wage, negotiated-pay, services/core inflation, inflation expectations and credit/transmission observations published before Oct 29.
- A decomposition of the energy shock and evidence on persistence/second-round pass-through, rather than headline HICP alone.
- A clear conditional-update method linking those inputs and prior rate changes to outcome probabilities, plus calibration or sensitivity for the three regime weights and conditional splits.
- Preserve the reproducible raw-vector calculation, including its consistent 0.5% fallback-to-hold branch; separately test the judgmental cancellation/postponement weight (the frozen rule maps no decision by the next scheduled meeting to “No Change”).

## Source basis (captured by Oct 18, 2026)

- Frozen rule and identity: `data/deep_review_20261017/work/0272_facts.json`.
- ECB Sep 10 decision: https://www.ecb.europa.eu/press/pr/date/2026/html/ecb.mp260910~314e508016.en.html (captured Oct 18); official calendar: https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html (captured Oct 18).
- Eurostat Sep HICP, released Oct 16: `data/deep_review_20261017/work/0272_facts_expansion_20261018.json`; source archive hash `d1d077e6326329355034f2d4be4cc4a1be68cd9d977c50d44d29ed47ccb3e088`.
- Lagarde IMFC statement, Oct 17: same fact unit; archive hash `358524c157c9751e724c9d06a018e0124acd97bce298f64ba48bff8695810bce`.
- SMA semantics/distribution: `data/deep_review_20261017/work/0272_sma_second_table_audit.json`; questionnaire https://www.ecb.europa.eu/stats/ecb_surveys/sma/shared/pdf/ecb.sma260824_questionnaire.en.pdf?1fa8cb52541c36c1a8ec28eb9e2e0b7e and aggregate https://www.ecb.europa.eu/stats/ecb_surveys/sma/shared/pdf/ecb.smar260911_september.en.pdf.
- Primary model audited: `research/2026-10-17-deep-review/models/ecb272_primary_2105.json`.
