# Resume protocol and operator scope

Operator authorized a continuous, finite in-depth review of all but clearly irrelevant conditions in the frozen 3,000-market universe on October 17. First 100 completed valuations is the inspection milestone; blocked cases and exclusions remain separate. Continue useful research through compaction; do not stop after building tracking. No token scarcity shortcut. Do not create an indefinite goal, new watcher, or idle continuation.

1. Read `notes/deep_review_checkpoint.json`, this protocol, `progress.json`, and the active case files/drafts. The original diagnostic's `completed` status is distinct from this active new review.
2. All 3,000 exact conditions start pending. Ignore old model screening verdicts for exclusion. Preserve exact condition, market, outcome-token IDs and full criteria hash. Use original index ordering; grouping common sources is permitted, with each affected condition indexed explicitly. Do not restrict research to the previous 255 flags.
3. Exclude only a documented, factual reason (e.g. completed/closed event with no live position route; an already certain event priced near 99.8% at current relevant quotes; inaccessible or beyond-project-horizon cases only after reading exact rules). Record exclusions separately; never count them toward 100 substantive reviews. A title, cheap-model interpretation, liquidity or favorite-price screen cannot reject a case.
4. Primary operator reads the complete literal rules and owns evidence interpretation, forecasts and valuation. Cheap agents may retrieve bounded factual sources/quotes, but cannot weed out candidates or supply authoritative investment judgments. Share a source model across exact related instruments only where the relation is proved. Do not count one family as many independent forecasts.
5. An in-depth case must explain rule/settlement forks, dated load-bearing sources, an independently reasoned probability/range, both sides' intended-size book/fee economics or explicit quote failure, relevant catalysts, uncertainty, source/adjudication/correlation risk, January horizon and comparison with the best accessible alternative. Give maker entry triggers, net-price break-even and sizing where supported; no artificial precision or certainty requirement. Apply existing execution doctrine before money moves.
6. `valued` means a defensible primary probability/range and both-side economics are complete. `blocked_after_review` needs actual in-depth investigation and a specific unresolved load-bearing fact; report it separately from completed valuations and do not count it toward the first 100. Broad unpriced triage is still pending. `excluded_factual` is separate and does not count at the milestone. Never manufacture a forecast to hit 100.
7. Before starting each case, use `python3 scripts/deep_review_ledger.py start --index N`. Before beginning another evaluation, write the primary-authored case JSON to a local work file and call `record --input path`. This immediately saves the immutable structured case, readable Markdown, append-only ledger, full CSV index, progress and tracked checkpoint. Update after EACH evaluation, not after a family/batch of evaluations. Files, not the chat summary, are the resume authority.
8. Save partial work/source receipts under `logs/deep_review_20261017/` and `data/deep_review_20261017/`; do not mark drafts complete. Verify a saved final record/index after compaction. Rebuild indexes from case JSON if a crash interrupted an update; do not rerun an already completed case blindly. Keep revisions linked, dated and separate; earlier observations remain evidence at their own time.
9. At the first 100 completed valuations, report valued/blocked/excluded separately, top candidates, evidence, entry thresholds, risks and missed coverage. Notify the operator in this chat and through the previously authorized Telegram route. Continue the authorized remaining queue after that notification unless the operator steers or asks to pause. Research records alone do not authorize a later execution; revalidate all current gates for any trade.
10. Latest money and management are in `notes/resting_orders.md` and
    `notes/current_context.md`; research quotes are not current execution checks.
    The separate October18 fallback completed after 10:00 UTC; its account reading
    was 09:36 UTC and remains a dated observation, not live state. This research audit
    made no account call or financial action.

    Current checkpoint (10:39 UTC): 213 valued, 3 blocked, 328 factual exclusions,
    2,456 pending across 544 records; active 113 is included in pending. Five rows
    append after pushed HEAD `33e9fac`: 96, 101, 106, 112 valued; 97 factually excluded
    after official final MLB verification. See [audit 1039](../../data/deep_review_20261017/ledger_audit_1039.json),
    [checkpoint](../../notes/deep_review_checkpoint.json), and [index](INDEX.md).
    Case 92 remains blocked: its post-creation CME active-month High history is
    incomplete. Resume active 113 first.

    Case 112 is priority research only: 9% YES, 0.5–80% range after the post-quote
    concentrated countermodel, with a 15-point reserve that is not an entry floor.
    No entry is approved. The OpenRouter public `period=week` endpoint returns one
    rolling-week row per model variant, not a daily panel. case 35's required fixed
    UTC Monday–Sunday history remains missing, not zero; see the [source correction]
    (../../data/deep_review_20261017/openrouter112_source_followup_1030.json).

    The Oct 16 preliminary CME CL DEC26 option crosscheck uses American put premiums
    and derived sensitivities. It challenges the prior low-oil mass but is not a
    physical forecast or ICE Europe WTI/Pyth CLL observation; it does not replace
    the dated compound cases. See [crosscheck](models/oil_option_proxy_crosscheck_0325.md).

    The milestone-200 precision caveat remains: case 270's rounded p = .05 EV is
    +$0.10537, versus raw normalized-payout EV +$0.058553 per ten shares. Reserve
    files postdate the older quote batch; timestamp metadata alone does not attest
    forecast-before-own-price ordering. Do not invent or backdate such attestation.

Current corrections: read [CURRENT_REVISIONS.md](CURRENT_REVISIONS.md) and [candidate_followup.md](candidate_followup.md) alongside canonical reports. Older immutable scenario ranges/quotes do not overwrite these dated corrections.


## Current review resume — October 18, 10:39 UTC

The checkpoint has 544 records: 213 valued, 3 blocked, 328 factual exclusions and 2,456 pending, including active 113. Five appended rows after pushed HEAD `33e9fac` pass the identity/hash audit at [1039](../../data/deep_review_20261017/ledger_audit_1039.json). Case 92 remains blocked on incomplete post-creation CME active-month High history; case 35 remains blocked on missing historical fixed-week OpenRouter totals. Resume active 113 first and preserve every saved case; this is progress, not a milestone.
