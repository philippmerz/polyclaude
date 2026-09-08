# Calibration review: reconcile coverage before counting evidence

Reviewed 2026-09-08 UTC. Research only; no probability, sizing, or hold/exit
policy change. This audit supersedes treating the legacy scorer's N as a count
of independent instance theses, or deferring reconciliation solely until December.

## Audit-start snapshot (before reconciliation)

`scripts/ledger_calibration.py score` reported 15 scored rows, 11 pending and 25
excluded/study rows. Its Brier score is 0.1374 versus 0.1626 for its ask-derived
market baseline. These are decision-row statistics, not independent experiments.
Keeping the earliest dated forecast for each exact question removes two later
GPT-6 forecasts and two later Prime Video decisions: **11 distinct questions**.
Their Brier score is **0.1822071**. Dates within these duplicate groups distinguish
the initial forecast; this is a fixed initial-forecast convention, not selecting
the most successful update after the result.

The old July grades are read from the existing ledger, not freshly revalidated
against every market in this audit. Some older rows lack stable market identifiers.
The old scorer also treated `PENDING-NO*` as NO; that must not establish finality. The
one such current row has no numeric central prior, so excluding it leaves today's
15-row score unchanged. Do not use fuzzy-question matching to establish
future grades: the ledger's own schema requires exact market identity.

Do not exclude the Wimbledon forecasts merely because population screening found
the candidates: the records contain explicit instance probability judgments. Also
do not silently call all question rows independent. Five SDCC brand contracts
share a major event and the same permissive online-announcement mechanism.

## Three missing August initial-entry forecasts

All three are absent from the short-dated ledger. Main independently read their
first-entry versions from git, where the outcome was still null, then fetched
their exact Gamma market IDs. Each returned the recorded slug, closed=true,
umaResolutionStatus=resolved, and the labelled binary payout shown below.

| Initial decision | Forecast convention | Market YES probability | Final YES payout | Brier | Pre-outcome commit |
| --- | --- | ---: | ---: | ---: | --- |
| DEC-0082, Aug-26, Iran–Oman agreement | Initial YES entry | 0.55 | 0 | 0.3025 | `b310ef0` |
| DEC-0085, Aug-28, Lake America | Initial YES entry | 0.60 | 1 | 0.1600 | `348ea87` |
| DEC-0107, Aug-31, GTA below 20M | Initial NO entry: P(at least 20M)=0.45, hence P(market YES)=0.55 | 0.55 | 0 | 0.3025 | `768eaa3` |

Exact outcomes/identities checked through [Iran–Oman market 3348048](https://gamma-api.polymarket.com/markets/3348048),
[Lake America market 3943918](https://gamma-api.polymarket.com/markets/3943918),
and [GTA market 3962583](https://gamma-api.polymarket.com/markets/3962583).
The initial slug-list fetch did not establish all three identities; direct ID
reads resolved that diagnostic failure. No outcome was inferred from a title.

DEC-0108/0110/0114/0115 are subsequent decisions on the same GTA market, not four
additional independent samples. They remain essential path evidence: the later
0.92 under-20M forecast and reversal were wrong even though the initial >=20M
direction was right. A terminal initial-forecast score does not measure that
sequence's realized loss or validate the update/exit process.

## Interpretation and next review

Combining the 11 legacy question-level grades with these three verified omissions
gives a **14-question candidate cohort**, Brier **0.1978056**. The mean selected-side
probability minus selected-side outcome is **-1.7857pp**, versus **+1.3636pp** on the
11-question cohort alone. These descriptive means are sensitive to cohort choice,
include skips and heterogeneous thesis classes, and are not a calibrated adjustment
for current holdings. No contemporaneous market-baseline score is asserted for the
expanded cohort: executed averages and order limits are not interchangeable with
the decision-time executable ask.

The backlog's >10 review threshold is crossed under a distinct-question convention,
so this reassessment is due now rather than automatically waiting for Dec-31.
Collapsing the five SDCC questions into one shared-event unit gives only **10 units**;
that illustrative grouping does not prove independence between the other units or
define an effective statistical sample size. There is no robust evidence here for
a uniform 10pp overconfidence correction on holds. Retain existing entry stress
tests, explicit hold sensitivity and portfolio limits; do not infer that raw hold
priors are thereby proven calibrated either.

Before the next policy-changing calculation: reconcile the missing initial-entry
records into a single auditable cohort, preserve exact side/probability orientation
and pre-outcome provenance, mark genuinely unavailable baseline quotes as missing,
exclude pending outcomes, and report event dependence separately from row count.
Reassess with new independently settling theses and the named December cohort;
never count repeated updates as additional outcomes or choose a grouping to obtain
the desired policy result. The initial audit preserved the three omissions here;
the following implementation records the subsequent explicit ledger reconciliation.

## Implementation follow-up, same day

Appended DEC-0082/0085/0107 to `notes/shortdated_ledger.json`, with the exact IDs,
initial forecast timestamps, full pre-outcome commit hashes, labelled outcomes and
source URLs. All 51 older records remain unchanged. Iran–Oman and Lake America
have `ask: null` because no separate historical baseline quote was established;
GTA retains the explicit initial raw NO ask of 0.27. No baseline was backfilled
from a cap, average fill, midpoint or a current quote.

The corrected scorer reports **18 own forecast rows**, Brier **0.1569654**, and a
**16-row market-matched subset**. Within that same subset, own Brier is **0.1476799**
versus **0.1857395** for the raw-ask-implied market baseline. These are row-level
descriptions, not the 14-question initial-forecast cohort above or an independent
sample. The positive matched-subset score difference is not a demonstrated ROI
edge, and cannot validate a portfolio-policy change.

The resolver now uses exact [market-ID](https://docs.polymarket.com/api-reference/markets/get-market-by-id)
or [market-slug](https://docs.polymarket.com/api-reference/markets/get-market-by-slug)
endpoints and checks every supplied identity. It requires closed=true, UMA status
resolved, exact YES/NO labels and complementary 0/1 payouts. Pending labels never
score as final; uncertain/unidentified rows stay ungraded. Missing baseline asks
do not erase a valid own-forecast/outcome observation, and market comparisons use
only matched rows. Dry-run preserved the ledger and reported **13 no-identifier
rows**, rather than guessing their market from titles. Legacy identity repair and
explicit first-forecast/event-group reporting remain separate work before any
policy-changing inference.

Implementation incident: an initial test mocked loaded rows but not the output
path, briefly replacing the working ledger with a one-row fixture. Main stopped
the worker, restored all 51 committed rows and the three known additions, and
verified the original records unchanged. Tests now automatically redirect to a
temporary ledger, confine writes, deny live network access and assert the real
ledger's bytes are unchanged. No order or funds were touched. A separate output
regression caught in main review (valid baselines displayed as n/a) is also tested.
