# Current lessons — compact onboarding

Reviewed 2026-10-16. Read README, then the current philosophy and this guide.
[MANDATE.md](../MANDATE.md), [00_philosophy.md](00_philosophy.md) and
[02_operations.md](02_operations.md) remain the authorities for scope, judgment
and procedures. This guide preserves recurring failure lessons; it does not
replace live checks or set new priors.

The [full pre-condensation ledger](archive/01_lessons_2026-10-12.md) is preserved
byte for byte. Its dated numbers, platform assumptions, experiments and retired
procedures are historical evidence. Read selected sections when a task needs
that evidence; do not restore an old instruction simply because it is archived.

## Evidence, identity and resolving sources

- Bind every claim to the exact condition, ordered outcome tokens, literal
  criteria, resolving source, source configuration, dates and instrument.
  Similar titles and shared events do not establish equivalent settlement.
  Contracts involving “by,” “before,” first qualifying events, rounding,
  cutoffs and fallback sources require their own interpretation.
- Fetch the data the live interface actually uses. Static HTML, yesterday's
  chart, cached screenshots and old API schemas can all look plausible while
  missing the current values. A mounted chart API is evidence only for its
  actual fields and observed version; record response cache age as well.
- Separate observation time, source publication time, cache age and event
  cutoff. A successful fresh HTTP request does not prove fresh publication.
  A digest or hash proves consistency with captured bytes, not that coverage
  was complete or the source was correct.
- Blocked, absent, malformed, stale or partial evidence is unknown. Never turn
  a failed fetch, incomplete pagination, empty parsed table or missing model
  into a confident “nothing changed.” Check controls, counts and the live
  interface before declaring a complete source sweep.
- Read shared source material once for a family, but compare every contract's
  exact dates, thresholds, units, rules and fallback behavior. Joint source
  analysis cannot erase a differing settlement condition. Changing criteria,
  evidence or model configuration invalidates the affected case conclusions.
- Re-read criteria and the resolving source at a material event, an adverse
  move or a prior change. Case memory is a map to evidence; old assessments
  and cached quotations cannot authorize a current action.

Origins: archive “Prior & fact hygiene,” “Parsing, venue data & verifying my own
output,” “Priors & calibration,” and dated source/version incidents in the
journal. Current method: [03_opportunity_method.md](03_opportunity_method.md).

## Forecasts, calibration and hidden information

- Binary terminal loss has no recovery story. Separate observed facts,
  resolution interpretation and probabilistic judgment; document what would
  break the thesis and when it must be checked.
- Write probabilities for this exact contract, regime and horizon. Historical
  lesson examples, a vendor's ranking, market midpoint and favorite-population
  curves are not standing priors. Record central, downside and other justified
  cases, with their assumptions and evidence dates.
- Shared sources and mutually exclusive or nested outcomes need a joint
  scenario view. Do not assign independent high probabilities to every
  sibling, count the same information twice or disguise unresolved mass.
  A scenario projection with supplied weights is uncalibrated until tested.
- Price changes matter only after checking actual trades, executable depth,
  spread and timing. Quiet volume or a noisy book alone does not prove informed
  trading. A large unexplained move or a genuine thesis break needs prompt
  reassessment; do not preserve a flattering prior to avoid realizing loss.
- Use the current philosophy's uncertainty rules: ordinarily a 0.10 absolute
  haircut, with exceptions only where the documented tail treatment applies.
  Do not resurrect the old universal 0.05 haircut or copy a historical
  0.85–0.95 estimate into a new market.
  High-confidence bond fades use the documented multiplicative tail stress
  only when the tail was measured first-hand and the horizon keeps that regime
  relevant. A short measurement cannot certify a much longer sibling.
- Routine factual triage can use a cheaper worker; primary judgment retains
  portfolio, eligibility, correlation, economics and uncertainty decisions.
  Escalate independent evidence review for material or disputed assumptions,
  with bounded scope and explicit files. More agents do not manufacture facts.
- Evaluate prospective entries, skips and the opposite side after actual
  fees, depth and timing. Correlated contracts are not independent successes.
  One winning settlement, a small replay or a narrower packet establishes
  neither forecasting skill nor a repeatable profit edge.

Origins: archive “Priors & calibration,” “Edges that survived,” “Verified
mechanics & regime judgment,” and the self-flattering-numbers cluster. Current
risk and counterfactual procedure: [00_philosophy.md](00_philosophy.md).

## Execution, fees and incomplete fills

- Use the vetted call path. New Polymarket buys go through
  scripts/polyclaude_enter.py; existing-position sells and verified cancels use
  scripts/clob_v2.py. A dry run validates only the branches it actually exercises.
  Do not bypass entry gates with a raw writer or assume a legacy writer's
  signature covers the current venue and deployed contracts.
  Test modes must suppress or clearly label every outward side effect,
  including Telegram messages; never announce a simulated order as submitted.
  Ordinary single-market entries are maker-or-skip. A taker entry needs the
  documented concrete urgency and incremental EV required by the philosophy;
  positive fee-net EV alone is insufficient. Multi-leg synchronization and
  thesis-break exits follow their distinct vetted routes.
- Quote lifetimes need an economic or risk reason (October19). A scheduled
  review is not an automatic expiry. Recheck conditional fill economics,
  source validity, caps and monitoring; keep a still-justified quote. Resolve
  or price known load-bearing gaps before posting. A hard expiry needs a
  named catalyst, source-staleness or operational-risk reason, while new
  unassessed material evidence still warrants the required cancel-first
  response. Never automatically repost a canceled quote or extend an existing
  explicit pull without fresh underwriting. Details: [resting orders](../notes/resting_orders.md).
- Fees must come from the current authoritative schedule and actual per-fill
  economics. An old 7% parameter is not a universal fee. Account for fees paid
  in shares, net received hedge units, rounding and exact-price depth; check
  gas, funding and withdrawal costs when changing venue or collateral.
- Dollars and shares have different minima. Check the current tick size,
  order-size units, lot precision and rounding before signing. Historical
  $5-ticket, five-share and decimal examples describe different constraints.
  Missing asks, nonfinite inputs and ambiguous identities must fail closed.
- Final action checks use current token/condition identity, full criteria,
  account and venue state, fee schedule, fresh book rewalk, available collateral,
  allowances, ticket/factor caps and pending-order reservations. A scanner
  trigger or an old quote is an observation, never execution approval.
- Reconcile resting orders against the authenticated venue every check.
  Ordinary public-information maker sells may rest at or above fair;
  hidden-information positions require a documented premium strictly above
  fair. Pull scheduled-catalyst orders before the event. Fee-net maker, taker
  and hold alternatives can change the preferred action.
- An acknowledgement, submitted transaction or cancel response does not prove
  completion. Verify trades, cumulative fills, remaining orders and actual
  account balances. Ambiguous cancellation/fill state retains its reservation
  and blocks conflicting spend until reconciled.
- Manage protected structures as complete economic positions, using canonical
  group topology and actual held units. Sequential multi-leg quotes are not
  atomic fills. Explicitly assess partial fills, residual exposures and the
  unwind before breaking a hedge; a floor alone omits its settlement option.
- Transfers and redemptions require the deployed contract, correct chain,
  recipient and collateral denomination, live pause/eligibility state,
  simulation and post-action balances/events. A successful unrelated supply
  simulation does not unblock a paused conversion route. Dust and gas can
  dominate small nominal profits.

Origins: archive “Execution mechanics,” “Write paths, drills & outward side
effects,” instrument/guard incidents and stale-constants/test-suite incidents.
Current tool contracts: [scripts/README.md](../scripts/README.md).

## Portfolio decisions and accounting

- Compare hold, trim, close, add, both outcomes and the best lawful executable
  alternative at our actual size and project horizon. Include spread, fees,
  variable carry, opportunity cost, liquidity, eligibility and operational risk.
  A constant-rate carry calculation is a sensitivity, not a guaranteed payoff.
- Current ticket and correlated-factor caps come from the philosophy and
  guarded entry path. The 15% new-ticket and 30% factor limits are not a fixed
  maximum position count; passive drift alone does not mandate a costly sale.
  Reservations and shared drivers still count before new exposure.
- Kelly/rho displays are advisory. Check joint terminal wealth, constrained
  alternatives and partial-fill paths before action. Evaluate each additional
  unit at current value: sunk entry price, an allegedly “free” carry and a
  house-money label do not make remaining risk free.
- A complete hedged pair can contain a guaranteed floor plus an option on a
  middle outcome or early resolution. Compare that complete economic position
  with a realizable alternative, including any blocked collateral conversion,
  before paying the spread to exit it.
- scripts/bankroll.py is the aggregate account reference across both wallets.
  Keep gas contributions separate from trading capital and disclose VM/API
  costs that remain unreconciled. Publish midpoint and fee-net depth together;
  sequential books are indicative estimates, not synchronized NAV or promises.
- A rounded “settled P&L” residual can change through marks or accounting.
  Do not describe it as new audited cash profit or invent a fill/settlement.
  Preserve original contributions, losses, external flows and approximation
  labels. Internal transfers are not returns or contributions.
- Normal December 31 resolutions redeemed in the first days of January count
  in the start-of-2027 evaluation. Do not cross an uneconomic spread solely
  to print cash before midnight. Evaluate the project on honest net return,
  rather than attention, activity or attracting additional capital.

Origins: archive “Sizing & risk,” “Self-flattering numbers & display honesty,”
and “Process & operator covenant.” Canonical records remain in notes/;
[performance methodology](../docs/README.md) governs the chart.

## Operations, scope and private information

- The mandate is legal expected compounded ROI. Project positions must fit a
  less-than-one-year horizon through the January evaluation. Off-chain stocks,
  personal brokerage, retired Sunday rotations and missed-week catch-ups are
  outside current scope. Historical queue text does not revive them.
- Scheduled runs execute the due check or trigger once, finish bounded safety
  follow-up and end. Cron and event watchers handle waiting. Do not create an
  indefinite goal, idle follow-up or extra timer because a check was quiet.
- Inspect call paths before running tooling. For bounded probes, resolve and
  verify the interpreter and intended parent with a harmless local round-trip,
  then create a fresh capture directory with
  `exist_ok=False` before requests; keep writes within it. If post-probe
  processing fails, preserve receipts and mark lost metadata unknown instead
  of rerunning completed probes or reconstructing it. Preserve unrelated
  worktree changes and financial records. Stage owned changes explicitly;
  never reset or restore a dirty tree wholesale to make an audit easier.
- Manage each canonical daemon through its current control procedure and
  verify one process, resolved command/path, code version and progress. A
  stale PID, old command or superficial liveness signal is not a healthy
  service. Avoid broad process killing and repeated competing workers.
- Keep local heavy work within actual VM memory/disk limits; use bounded
  independent delegation where authorized, with explicit ownership.
  On this constrained VM, enumerate local model workers and require more than
  500 MB MemAvailable before starting one; allow at most one local background
  model worker. Cloud delegation is a separate resource path.
  Budget probes use scripts/check_usage.sh --brief directly. Never inject /usage
  into a conversation or save quota by skipping a necessary safety exit.
- Read secrets through scripts/_paths.py and configured environment names.
  Never put credentials, secret paths or private operator material in tracked
  files, generated public packets or tool output. No broad searches of private
  directories, inboxes or provider histories.
- Retrieve notified Telegram text only through its private one-time reader.
  ALREADY_CLAIMED means no action or duplicate reply. EXPIRED means only a
  generic request for a fresh resend. Outbound agent text uses the documented
  msg --stdin path with a single-quoted heredoc delimiter.
- Keep Telegram summaries material-only. Raw RSS keyword matches stay in the
  internal review queue, including Tier 1; research candidates and unfilled
  bids do not justify standalone headline pings. Preserve review wakeups and
  report material findings, actions, decisions and operational incidents.
- Reconcile triggered alerts with actual current holdings and orders; stale
  keywords or a dropped position must not perpetuate fictional exposure.
  Emergency exploit/depeg/chain-halt action follows the exact corroboration,
  market-reaction and on-chain-ground-truth protocol in current operations.
  A real thesis break still receives prompt ordinary vetted exit analysis.

Origins: archive “Ops,” “Daemons, resources & liveness,” and “Process & operator
covenant.” All live procedures and drills: [02_operations.md](02_operations.md).

## Keeping memory useful

Use [notes/current_context.md](../notes/current_context.md) as a short dated
index to current work, blockers and evidence. Its review/expiry times are
editorial metadata, not refreshed quote or account timestamps. Required primary
reads, current records and execution checks remain mandatory.

After an existing completed check or material decision, update that handoff if
its state changed or validity expired; record the actual review time, next due
boundary and hashes of the public sources used. Do not extend freshness merely
by regenerating a packet. Review this guide for duplication and superseded
instructions during the already-due weekly P&L review, with no new schedule.
Fold a durable new failure lesson into the relevant paragraph and retain dated
evidence in the journal or archive. Old numbers and examples belong behind
links, while gates and unresolved failure classes stay in the active guide.

Target about 16 KB for this guide and 6 KB for the handoff. These are maintenance
budgets, not permission to cut a safety requirement. If space becomes tight,
move redundant examples to dated evidence and preserve essential controls.
Task-specific packets from scripts/context_packet.py default to a 12 KB cap,
include hashes and freshness status, and omit whole optional sections rather
than truncate rules. They read allowlisted Git-tracked public documents only;
no private histories, account state, live quotes or model calls are loaded.

Focused relevant context can improve attention and tool reliability; it does
not establish that every extra token always worsens a response. Summarization
can also drop constraints or carry an error forward. Preserve original evidence
and explicit unknowns, and judge any benefit with task outcomes rather than
packet size alone. See OpenAI's
[session-memory guidance](https://developers.openai.com/cookbook/examples/agents_sdk/session_memory).
