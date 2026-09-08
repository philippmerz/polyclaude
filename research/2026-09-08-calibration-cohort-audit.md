# Calibration review: reconcile coverage before counting evidence

Reviewed 2026-09-08 UTC. Research only; no probability, sizing, or hold/exit
policy change. This audit supersedes treating the legacy scorer's N as a count
of independent instance theses, or deferring reconciliation solely until December.

## What the current scorer actually measures

`scripts/ledger_calibration.py score` reports 15 scored rows, 11 pending and 25
excluded/study rows. Its Brier score is 0.1374 versus 0.1626 for its ask-derived
market baseline. These are decision-row statistics, not independent experiments.
Keeping the earliest dated forecast for each exact question removes two later
GPT-6 forecasts and two later Prime Video decisions: **11 distinct questions**.
Their Brier score is **0.1822071**. Dates within these duplicate groups distinguish
the initial forecast; this is a fixed initial-forecast convention, not selecting
the most successful update after the result.

The old July grades are read from the existing ledger, not freshly revalidated
against every market in this audit. Some older rows lack stable market identifiers.
The scorer also treats `PENDING-NO*` as NO; that must not establish finality. The
one such current row has no numeric central prior, so excluding it leaves today's
15-row score unchanged. Do not use the fuzzy-question `resolve` path to establish
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
the desired policy result. This research table preserves the three omissions without
silently rewriting the archival ledger or changing its existing score semantics.
