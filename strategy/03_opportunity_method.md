# Opportunity discovery and evaluation

Use this with [the entry pipeline](../AGENTS.md#4-entry-pipeline-every-gate-is-an-ev-term-in-application-order).
New buys are authorized by the live entry gates. A finished valuation list is
not a token allowlist. Discovery or one attractive case does not replace those
gates.
The objective is net compounded return through the January evaluation. Number of
markets read, number of trades and a quiet scanner are not success measures.

## Coverage before conclusions

Every scan should identify its endpoint/universe, filters, page/byte/time limits,
stop reason, fetched rows, filter exclusions, output omissions, requested quotes,
valid quotes and failures. Report a zero within that scope. Unknown, failed,
filtered, truncated and unreviewed are different states; none means no opportunity.
Integrity hashes establish what was read, not that the input covered the venue.

Primary and thin-tail discovery are volume-ranked profiles. A dominant-side
win-assumed carry filter cannot assess the opposite side, sub-three-day events or
true expected return. Keep its exclusions visible. Broaden a profile in a bounded
diagnostic when the measured exclusions justify it; use matched inputs to compare
selection policies rather than attribute a different market state to a code fix.
Do not repeatedly expand the crawl merely because the tick was quiet.

Consistency quotes default to a balanced budget: roughly half for midpoint rank,
the rest for least-recently-attempted exact baskets. Member/criteria changes reset
recency. Priority and exploration share the existing group/leg/time limits; unused
capacity can be backfilled. A failed quote is an observation about that attempt,
not a permanent rejection. Sequential positive books remain provisional.

## Organize cases, then purchase information

The review unit is an exact instrument or a proven economic structure. For PM,
retain market, condition and outcome-token IDs, outcome order, literal criteria
hash and observed event membership. For another venue, retain chain, contract or
asset ID, product, oracle and wallet route. A shared title/event is context, not
proof of equivalence, mutual exclusion or identical settlement.

Use cheap reviewers for bounded factual triage and source collection, with an
explicit list of rows covered and rows still unreviewed. For a bounded news feed,
return all titles or an explicit unreviewed list; a literal-name mismatch does not
establish irrelevance. The primary reviewer verifies load-bearing speaker,
comparator and change-direction claims against the original body. The offline context
batcher neither calls a model nor supplies a probability. It is a delta queue:
unchanged prices can become interesting when a source, catalyst, cost, eligibility
or horizon changes. Read the complete scanner output as well as emitted batches.
Group common text to reduce repetition while preserving each distinct clause.

For each serious case, leave a compact disposition in its dated research/journal
record: exact identity and criteria/source version; sides considered; evidence;
economics at intended size; verdict; unresolved blocker; and the concrete condition
that would change the verdict. Refer back to that record on a repeat review instead
of reconstructing a thesis from old prose. Source/criteria/cost changes invalidate
the relevant disposition. Filtered disappearance is not closure. No review record
authorizes a later order or creates an idle scheduled follow-up.

Save results during the work, before beginning the next batch or case. Append each
completed screen batch to the run's JSONL ledger and refresh its progress file;
append deeper case findings to a separate follow-up ledger. Keep a tracked
checkpoint with exact ledger paths, counts, hashes, completed coverage and the
remaining queue. Preserve prior valid observations and append dated revisions.
After compaction, resume from those files and their exact instrument bindings.
A final CSV export supplements these live records. Label any retrospective
backfill explicitly, and keep checkpoint time separate from evidence freshness.
The [current review checkpoint](../notes/market_review_checkpoint.json) indexes
the completed Oct 17 diagnostic and its unresolved source flags.

Triage first by whether a fact can change the decision:

1. Can the project lawfully access the instrument, fund and exit it through a
   vetted route? Venue eligibility and personal eligibility are separate facts;
   moving a VM does not establish either. A listing can remain a research case
   while a writer is unavailable, with that blocker explicit.
2. Does settlement fit January, including normal year-end redemption in early
   January? A later expiry needs a substantiated early-settlement or January-exit
   thesis with its costs and risks. A remote target or annualized return is not
   that thesis. Metadata end dates are not verified settlement dates.
3. What independent information could make the price wrong? Prefer a named
   resolving measurement, a verifiable catalyst or a tested external consensus.
   First establish endpoint/configuration identity, then fidelity and recency.
   A blocked source is unobserved; re-reading a stale one proves no absence.
4. Does the economics have enough potential to justify the next research cost?
   Use an optimistic *bound* only to reject mathematically impossible cases;
   never promote that bound to a forecast. Do not manufacture confidence to fill
   an allocation or treat generic liquidity/volume as intended-size depth.

Routine instance research uses one evaluation; the prospective reasoning-depth
experiment did not justify debating every small trade. Escalate material sizing,
new strategy classes and structural ambiguity as specified in doctrine. Separate
fact collection from the primary agent's probability and portfolio judgment.
More model calls are useful when they can resolve a load-bearing uncertainty.

The [finite-context architecture](../research/2026-10-12-finite-context-architecture.md)
proposes reviewing a source family once and projecting explicitly supplied joint
scenarios through exact per-contract rule bindings. Its offline case memory and
projection tools are a shadow prototype. Byte-identical prose may be shared;
unknown branches, distinct thresholds, source configurations and correlation
must remain explicit. Dependency versions and expiry check declared assumptions,
not their completeness or the accuracy of a forecast. This does not introduce a
standing probability signal or a new execution/attention schedule.

## Forecast and compare both sides

A probability needs dated evidence, explicit assumptions, a falsifiable crux and
downside alternatives. Search for already-existing qualifying evidence before
forecasting future catalysts. Benchmark configurations and named resolution
surfaces cannot be substituted for one another. Quantify strict/loose adjudication
branches rather than silently call an interpretation bet a measured fact.

Evaluate both sides when a verified fact kills a thesis. Do not assume their
executable asks sum to one. Apply the current class-specific pessimistic bound:
the ordinary instance/catalyst default is a 0.10 haircut; measured short-horizon
bond tails can use the documented multiplicative stress. No general 1pp edge
floor exists. The favorite-price profile has no population-derived p, edge or APY;
the old curve failed replication and is no longer an attention-ranking signal.

Compare at the actual proposed dollars and holding window. Include both-side
book walks, nonlinear fees via `pm_fees.py`, spread/slippage, gas, funding,
bridge/on-offramp costs, settlement delay, issuer/protocol/oracle risks and exit
liquidity. A quote's timestamp is not the collection timestamp; rewalk before
action. Venue minimum quantities are shares/contracts, separate from applicable
route USD minimums. Do not turn Gamma `orderMinSize=5` into a universal $5 floor.
The venue's [current order documentation](https://docs.polymarket.com/trading/place-orders)
defines the CLOB minimum as a share quantity.

Use the best lawful executable alternative, including same-chain Aave, after
actual funding costs. Variable carry held constant is a sensitivity, not a
forecast. Total bankroll is not free cash. For material shared risks, compare
joint terminal wealth/log growth across explicit states; midpoint Kelly and a
scalar correlation discount remain advisory. Entry cost is sunk in an exit call.

The guarded entry tools enforce important identity, cost, cap and transaction
checks. They do not independently certify the truth/recency of a supplied p,
personal eligibility, every horizon assumption or the best alternative. Those
remain analyst responsibilities before invoking the vetted writer. Preserve
15% ticket/30% factor-cluster caps, complete-set invariants, reservations, final
current-state checks and balance/fill reconciliation.

## All on-chain candidates use the same comparison

PM is the most developed discovery path, not the whole opportunity set. Compare
spot exposures, lending, tokenized assets and lawful derivatives by forward net
return into January, actual reachable size, correlation and route risk. A future
writer is worth building only when an accessible thesis survives its all-in cost;
adding a venue or a leverage product is not itself an edge. Keep current manual
candidates and route blockers in [the project watchlist](../notes/longterm_watchlist.md).

## Measure decisions, not reading volume

For a material evaluation, record the forecast and executable quote before the
outcome in the existing decision/skip records. Retain skips and opposite-side
checks as well as entries; distinguish no-edge, missing evidence, inaccessible,
unquoted and unreviewed. Grade at net executable economics, not hit rate or a
winning subset. Collapse duplicate/event-dependent forecasts before claiming
calibration sample size; do not fit a new probability curve to a few wins.

The useful funnel is: fetched scope → triaged cases → independently verified
cases → both-side economic evaluations → robust approved entries → actual fills
→ net outcomes. A stage count is an audit measure, not a target. Evaluate a
method change by matched-input coverage, validation yield, failures and later
outcomes; an increased row count or passing tests is not proof of improved ROI.
