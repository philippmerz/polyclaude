# Finite deep-review protocol

Read [RESUME.md](RESUME.md), then `.venv/bin/python scripts/deep_review_resume.py --index N` for the selected case. The packet orients; full rules, source/model review, current state and execution gates remain required. Current state is in [current context](../../notes/current_context.md), [resting orders](../../notes/resting_orders.md), and the [checkpoint](../../notes/deep_review_checkpoint.json). Dated counts and financial instructions belong in dated records. The prior version is preserved [byte-for-byte](archive/PROTOCOL_before_20261018T2100.md).

## Scope and selection

**Operator direction, October 21:** the broad review experiment ended after 422
completed unique `valued` cases. Case 529 remains unfinished and is excluded
from the count. The 600-case waiting milestone is retired. New investment may
be selected autonomously for EV from the completed valued universe after a
primary comparison using fresh source/criteria checks, both-side executable
economics, uncertainty, settlement horizon, maker-fill risk, and the current
portfolio. The v2 [entry policy](../../notes/entry_review_gate.json) uses
`review_mode: "completed_universe"` and
`minimum_completed_valuations: 422`; record exact condition/token identities
and a hashed research report there before any new BUY. All current execution
gates still apply. A completed comparison is not itself an order or fill.

Selection may conclude that no bid is justified. The policy's `selection` uses:

```json
{"reviewed_utc":"<actual aware UTC time>","completed_valuations":422,
 "report":"research/<comparative-report>.md","report_sha256":"<SHA256>",
 "targets":[{"condition_id":"<exact valued condition>","token_id":"<selected outcome token>"}]}
```

The offline gate verifies configured count consistency, report hash and selected
token membership; it cannot certify comparison quality or live eligibility.

The October17 broad review authorization covered the frozen 3,000-condition universe and ended after 422 completed valuations. The remaining queue is not a current entry barrier or an instruction to resume that experiment; case 529 is unfinished. Preserve exact frozen identities and criteria in any future authorized case work. All cases remain eligible for research regardless of title, old model labels, price, liquidity, or cheap-model output. Small models and factual collectors cannot reject, rank, set probabilities, or choose investments. Primary review owns interpretation, forecasts, and investment conclusions.

Read the complete rule before analysis. Copy case identities programmatically from the frozen universe; check complete token strings, not shortened or manually transcribed IDs. Preserve an erroneous source unit and append a correction before relying on it. Exclude only for an objective fact that makes the exact contract ineligible or unreachable within the project horizon, such as a resolved/closed event with no remaining route. Record the exact reason and source. A high price, thin book, research difficulty, or related market result is not sufficient. Inaccessible evidence is a gap unless the contract itself is objectively impossible to evaluate. Shared family research is permitted only when the relationship is demonstrated; index each condition and do not count shared evidence as independent forecasts.

## Evidence and analysis

Bind sources to the exact claim, entity, geography, metric, date, and contract wording. Prefer dated primary sources; preserve URL, publication/event time, retrieval status, body hash, and bounded raw receipt. Distinguish source bodies from snippets, directories, model outputs, and failed requests. A failed or missing retrieval is not evidence of absence. For a forecast update, compare the new observation with that forecast’s fielding date, baseline, units and horizon. An already-anticipated high level or risk is not automatically new evidence; document the surprise bridge before adding another regime penalty. Keep per-case source units small and readable; store raw arrays/captures separately. Never put credentials, private operator material, or authenticated payloads in tracked research.

Use compact JSON/JSONL for machine units and CSV for flat data; gzip large arrays/body captures. Keep protocol, schema and shared source context once in a hashed parent, with indexed case/batch references. Preserve full reasoning and literal criteria; omit repeated Markdown preambles and duplicate raw/pretty body dumps. Existing immutable case reports and hash chains are unchanged. Archived legacy paths read through `log_storage.read_verified_bytes` or `scripts/log_storage.py restore PATH`. Save one `market_context_batches --format compact-json --output FILE.json.gz` parent per scan; resume with `--input FILE.json.gz --batch-index N`. Persist `--reference-only` slices only when needed.

A complete valuation explains resolution rules and timing/fallback/rounding, cites load-bearing evidence, and gives an independently reasoned probability and range with competing scenarios and calibration limits. Compare both outcomes at intended size after fees, spread, depth, fill selection, funding, carry, and operational costs. State adjudication/source uncertainty, cross-case and portfolio dependence, catalysts/deadlines, and the best accessible alternative. Do not treat prices, point forecasts, rankings, or a small hit-rate sample as calibrated outcome probabilities. A transparent forecast bridge may use them with its assumptions, dependence and uncertainty stated. Avoid false precision, but do not demand certainty or require arbitrary scenario endpoints to pass a hurdle. Apply existing risk and execution doctrine.

Research records do not authorize execution. Any later action needs current exact venue identity, fresh eligible books and fee data, current bankroll and open commitments, portfolio/correlation limits, and the vetted execution path. Revalidate at decision time; dated quotes and account snapshots are not live gates.

For saved-quote math use `scripts/deep_review_economics.py` with an explicit packet path. Gamma economics fields and books must bind to hash-verified raw receipts; [binding audit](gamma_binding_audit_2226.md). Book age uses its matching CLOB response, never Gamma time. [Clock erratum](quote_clock_audit_2145.md) covers older helper output; prices/probabilities stay unchanged and material corrections append.

When computed projections carry a forecast, save the small generator with source/configuration hashes and any seed. Parameters and a seed alone do not establish the draw order or an exact replay. Distinguish computational error from model uncertainty; preserve prior results when a new projection uses newly specified draws. [Joint-yield example](models/0481_joint_projection_1634.json).

Generate intended-ticket prose from its saved depth walk, including every consumed level and fee. A best ask times a larger quantity is not a ticket quote. [Append-only DOGE correction](revisions/0482_20261020T164413862661Z.md) preserves the original report and already-correct walk.

## Records and progress

Every case starts pending. Use `scripts/deep_review_ledger.py start --index N` before work. The start guard permits resuming the same unfinished case and rejects a different case until active work has a completed record; a failed record call does not permit advancing. After each finished case—not a batch—save the primary-authored input and run `record --input PATH`. This writes immutable base JSON/Markdown, append-only ledger, effective index, progress, and checkpoint. Partial work stays in bounded work/source directories. Verify saved identity, hashes, status, and checkpoint before moving on.

Target2–5KB per source/model unit; keep large arrays and raw receipts separate. Use a small hash-linked index rather than reopening batch monoliths. `deep_review_terminal_status.py` supplies at most30 exact-ID status leads per explicit request; the primary still reads each full rule before recording objective ineligibility. Nonterminal, missing or failed responses stay pending, without a probability or rejection. `scripts/read_capture.py` can persist read evidence before parsing; supplied SDK/provider bytes and call-window clocks must retain those representation limits.

Use `valued`, `blocked_after_review`, or `excluded_factual`. `valued` requires a defensible primary probability/range and both-side economics. `blocked_after_review` requires substantive review and a named unresolved load-bearing fact; it is separate from completed valuations. `excluded_factual` requires objective ineligibility and is also not a valuation. Unreviewed/partial cases remain pending. Never manufacture a forecast to hit a milestone.

For material correction, run `revise --input PATH --prior-report-sha256 SHA256 --reason "specific change"`, preserving exact frozen identity. Revisions append timestamped JSON/Markdown and a hash-linked ledger entry; never overwrite base records or older observations. Use verified revision logic for effective state. Count each condition once using its latest verified revision; retain base counts and `evaluations_written` separately from revision counts. If saving/rebuilding is interrupted, audit existing files before retrying; never repeat a completed case blindly.

At each authorized milestone, report valued, blocked, excluded, and pending counts separately, plus coverage, evidence, risks, and supported entry conditions. Notify in chat and through the already-authorized Telegram route when applicable. Continue a queue only while that research authorization is active. The Oct21 direction ended the broad pass at 422 and the native goal is inactive; do not resume the remaining queue without renewed authorization. A milestone count does not prove opportunity or full coverage.

## Resume and safety

Scheduled check-ins do not reactivate a paused native goal or the ended broad-review authorization. A blocked individual case is saved and the next pending case remains eligible only under active research authorization. A global block requires a shared obstacle that prevents meaningful progress, not a completed cron tick, a milestone, or one missing source for an individual case. Do not fake completion or create a replacement goal. Resume native automatic continuation only through the user/system goal control.

After interruption or compaction, read the checkpoint and resume packet, then inspect the selected case and latest verified revision. Refresh the compact handoff after material checks or decisions. Historical notes/archive are evidence only; do not replay old trades, snapshots, deadlines, or instructions. Preserve unrelated changes and immutable financial records. This protocol creates no indefinite goal, timer, watcher, or idle continuation.
Provider captures must preserve the exact returned tool object/string before selection, parsing or paraphrase. Hashing reconstructed excerpts or agent-written source notes does not verify publisher content; label them as notes and retain an explicit source gap until the actual response is captured. A failed independent source read does not corroborate a collector's paraphrase.

Geometry checks bind coordinate reference system and explicit distance units; verify meters versus kilometers with an independent scale calculation. Center-point containment does not prove an any-part intersection condition, and two nonconsecutive map snapshots do not prove next-cycle persistence or full historical coverage. Preserve erroneous units and append a verified correction before forecasting.

Sourceorigination matters: directmanagement interviews carried by crediblepublishers are primaryevidence; issuer-domain-only searches can miss them. An emptynewsroom/filingsearch is boundedcoverage, not proof ofabsence.

Creation-date clauses require a verified creation timestamp; do not assume a title or effective date defines the full event window.
