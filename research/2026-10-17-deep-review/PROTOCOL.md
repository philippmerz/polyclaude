# Resume protocol and operator scope

Operator authorized a continuous, finite in-depth review of all but clearly irrelevant conditions in the frozen 3,000-market universe on October 17. First 100 completed valuations is the inspection milestone; blocked cases and exclusions remain separate. Continue useful research through compaction; do not stop after building tracking. No token scarcity shortcut. Do not create an indefinite goal, new watcher, or idle continuation.

1. Read `notes/deep_review_checkpoint.json`, this protocol, `progress.json`, and the active case files/drafts. The original diagnostic's `completed` status is distinct from this active new review.
2. All 3,000 exact conditions start pending. Ignore old model screening verdicts for exclusion. Preserve exact condition, market, outcome-token IDs and full criteria hash. Use original index ordering; grouping common sources is permitted, with each affected condition indexed explicitly. Do not restrict research to the previous 255 flags.
3. Exclude only a documented, factual reason (e.g. completed/closed event with no live position route; an already certain event priced near 99.8% at current relevant quotes; inaccessible or beyond-project-horizon cases only after reading exact rules). Record exclusions separately; never count them toward 100 substantive reviews. A title, cheap-model interpretation, liquidity or favorite-price screen cannot reject a case.
4. Primary operator reads the complete literal rules and owns evidence interpretation, forecasts and valuation. Cheap agents may retrieve bounded factual sources/quotes, but cannot weed out candidates or supply authoritative investment judgments. Share a source model across exact related instruments only where the relation is proved. Do not count one family as many independent forecasts.
5. An in-depth case must explain rule/settlement forks, dated load-bearing sources, an independently reasoned probability/range, both sides' intended-size book/fee economics or explicit quote failure, relevant catalysts, uncertainty, source/adjudication/correlation risk, January horizon and comparison with the best accessible alternative. Give maker entry triggers, net-price break-even and sizing where supported; no artificial precision or certainty requirement. Apply existing execution doctrine before money moves.
6. `valued` means a defensible primary probability/range and both-side economics are complete. `blocked_after_review` needs actual in-depth investigation and a specific unresolved load-bearing fact; report it separately from completed valuations and do not count it toward the first 100. Broad unpriced triage is still pending. `excluded_factual` is separate and does not count at the milestone. Never manufacture a forecast to hit 100.
7. Before starting each case, use `python3 scripts/deep_review_ledger.py start --index N`. Before beginning another evaluation, write the primary-authored case JSON to a local work file and call `record --input path`. This immediately saves the immutable structured case, readable Markdown, append-only ledger, full CSV index, progress and tracked checkpoint. Update after EACH evaluation, not after a family/batch of evaluations. Files, not the chat summary, are the resume authority. For a material change to an already saved case, use `revise --input path --prior-report-sha256 SHA256 --reason "specific change"`; the input must repeat the exact frozen index, market, condition and criteria identity. This appends timestamped JSON/Markdown under `revisions/` and an append-only `revisions.jsonl` entry; never overwrite the base case or base ledger.
8. Save partial work/source receipts under `logs/deep_review_20261017/` and `data/deep_review_20261017/`; do not mark drafts complete. Verify a saved final record/index after compaction. Rebuild the effective index from base JSON plus the verified revision ledger if a crash interrupted an update; do not rerun an already completed case blindly. Base records/counts remain accessible, while current counts and links use the newest verified revision per condition exactly once. `evaluations_written` remains the base-record count; revision count/hash are separate. Keep revisions linked, dated and separate; earlier observations remain evidence at their own time.
9. At the first 100 completed valuations, report valued/blocked/excluded separately, top candidates, evidence, entry thresholds, risks and missed coverage. Notify the operator in this chat and through the previously authorized Telegram route. Continue the authorized remaining queue after that notification unless the operator steers or asks to pause. Research records alone do not authorize a later execution; revalidate all current gates for any trade.
10. Latest money and management are in `notes/resting_orders.md` and
    `notes/current_context.md`; research quotes are not current execution checks.
    The separate October18 fallback completed after 10:00 UTC; its account reading
    was 09:36 UTC and remains a dated observation, not live state. This research audit
    made no account call or financial action.

    Current checkpoint at 12:15 UTC: 230 valued, 2 blocked, 328 factual exclusions
    and 2,440 pending; case 133 is active and included in pending. There are 560
    immutable base records and 15 revisions. [Audit 1215](../../data/deep_review_20261017/ledger_audit_1215.json),
    [checkpoint](../../notes/deep_review_checkpoint.json), and [index](INDEX.md)
    govern; the index has 2,439 pending rows plus one active row. Cases 124, 130
    and 131 are valued at 7%, 59% and 21% YES; no orders were added. Case 35 is valued at 60% YES ([revision](revisions/0035_20261018T111634872634Z.md)); its 53-point Top Models token chart includes Others, distinct from the R2 request-share chart’s 52-week series through partial Oct. 12. Case 92 remains
    blocked on incomplete post-creation CME active-month High history.

    All 12 exact OpenRouter R2 cases share the [daily-text revision model](models/openrouter_lab_rank2_daily_revision_1215.md):
    Google 90%, OpenAI 7.67%, DeepSeek 1.03%, ZAI 0.4%, residual 0.9%, in dependent
    subjective branches. The 406-row Oct. 17 endpoint has no exhaustion/cutoff
    guarantee. Revision followed the 11:45 quotes, not price-blind; Case 112 DEC-0214 is LIVE
    and unfilled NO 5 at 65¢ ($3.25), last verified in the 11:50 snapshot; eight
    bids then totaled $16.42. Review/pull at the existing 22:00 UTC check or earlier
    on uncertainty; cancel first. That account proof is dated, not a live check.

    Case 119’s request-share chart differs from the default token-share API. Its
    11:45 book was already ~65 minutes old; the helper computes a passive 1¢ price
    on that stale capture, not a fresh underwritten quote; selected NO is 0% after
    reserve. Case 358’s 1¢ ask has no positive cent-grid passive maker price. No
    R2 order was added.

Current corrections: read [CURRENT_REVISIONS.md](CURRENT_REVISIONS.md) and [candidate_followup.md](candidate_followup.md) alongside canonical reports. Older immutable scenario ranges/quotes do not overwrite these dated corrections.


## Current review resume — October 18, 12:15 UTC

The effective checkpoint has 230 valued, 2 blocked, 328 factual exclusions and
2,440 pending; case 133 is active and included in pending. It contains 560 immutable
base evaluations plus 15 revisions, counted once. [Audit 1215](../../data/deep_review_20261017/ledger_audit_1215.json)
validates identities, report/revision hashes, effective index and checkpoint.
Resume case 133 from the checkpoint; case 92 remains blocked on incomplete
post-creation CME active-month High history. Cases 124/130/131 are valued at
7%/59%/21% YES with no new orders.

All 12 exact R2 lab cases use [the daily-text primary revision](models/openrouter_lab_rank2_daily_revision_1215.md),
made after the 11:45 quotes were seen. Google 90%, OpenAI 7.67%, DeepSeek 1.03%,
ZAI 0.4%, residual 0.9%; the 406-row daily endpoint is not proven exhaustive or
cutoff-complete. Case 112 DEC-0214 is LIVE/unfilled NO 5 at 65¢ ($3.25), last verified in
the 11:50 snapshot with eight bids/$16.42; that proof is dated. Pull at the existing
22:00 UTC check or earlier on uncertainty; cancel first. Case 119’s 11:45 book was
already ~65 minutes old; helper computes passive 1¢ on that stale capture, not a
fresh underwritten quote; selected NO is 0% after reserve. Case 358’s 1¢ ask has no
positive cent-grid maker price. No R2 order was added. Next research boundary is
14:00 UTC.
