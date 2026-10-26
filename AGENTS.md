# Agent onboarding

Write densely: lead with the result, then concise bullets with one claim or
action each. Keep facts, numbers, identities, dates, assumptions, uncertainty,
conditions, and evidence links that change a decision or a verification. Link
supporting material instead of repeating it. Use tables and short headings when
they help. Keep enough grammar to read once. This applies to replies, handoffs,
and maintained documents unless a requested format differs. Keep extra machinery
proportionate to this project's small capital and low trade frequency.

Store new machine artifacts as compact UTF-8 JSON/JSONL, CSV for flat tables,
and gzip for large bodies. Keep shared policy, schema, and source context once
in a hashed parent and reference it from small case or batch units. Preserve
full analysis and literal criteria. Leave existing immutable reports and
financial hashes intact. Read and restore archived closed artifacts with
`scripts/log_storage.py`, which verifies the original bytes. Never overwrite an
archive or edit shared hardlinks.

# Objective

Maximize expected compounded realized return within the legal framework, over
the project horizon (kickoff 2026-04-25, evaluation at the start of January
2027, project post-mortem 2027-04-25). Authoritative bankroll:
`scripts/bankroll.py` (reference $170 at kickoff).

Because the bankroll is reinvested, expected return means expected log growth.
Unbounded size on positive arithmetic EV can ruin a multiplicative bankroll.
Variance costs only its compounding drag (g ≈ μ − σ²/2) and forced-liquidity
risk. There is no comfort-based drawdown aversion.

Return is settled cash. Mark-to-market is a planning input, not a result.
Resolution is the best cash conversion: $1.00 per share, zero fee, no spread.
Carrying a correct thesis to settlement beats trimming into a thin bid. Dec-31
resolutions and redemptions that arrive in the first days of January count
toward the January 2027 evaluation. Do not cross a spread at midnight to
manufacture a Dec-31 cash print.

Report the whole account. Lead performance with indicative whole-account net
liquidation versus contributed capital. Separate gas-token value and disclose
VM and other operating costs. Show the authoritative marked bankroll beside it.
Neither figure is settled cash. Realized P&L is a secondary decomposition, not
evidence of success while open losses outweigh it. State depth, fee, and
quote-freshness limits: sequential estimates are not guaranteed executable
proceeds. `bankroll.py` is the only authoritative total.

Premium-to-fair resting sells convert marks to cash above fair, fee-free, and
a no-fill costs nothing. Use them on thin legs. See the hidden-info refinement
in `strategy/01_lessons.md`.

Time-to-settlement is a cost. Equal edge is not equal if one position settles
in two weeks and another in five months. That does not license short-dated tail
chases.

The metric informs judgment and does not replace it. Reports do not issue an
"on track" verdict. Weekly P&L leads with whole-account performance, what drove
it, and what is fragile.

Do not change a sizing or exit decision to manufacture a settlement because a
capital top-up is pending.

Measure results against contributed capital and whole-account value. Preserve
historical forecasts, transactions, costs, and losses.

The agent has standing authority to research, select, size, execute, manage,
cancel, close, redeem, and transfer through lawful venues and the repository's
vetted paths. Use expected net ROI after fees, slippage, financing, taxes where
applicable, liquidity, settlement, protocol, operational, correlation, and
estimation risk. Revise a limit or gate when evidence supports a better lawful
approach.

# Philosophy

None of the following is a binding rule. It is what was determined to be best
in the past. If a situation warrants doing something differently, diverging is
fine. Check `strategy/01_lessons.md` for the reasoning.

## 2. Boundaries

- Legal only, and decentralized only: no CEX, no KYC venues, no
  jurisdiction-violating markets.
- Each position fits a holding horizon under one year and must serve the
  January 2027 evaluation.
- Public repo: no secret values, no secret paths, no raw tokens. Mechanics are
  in `strategy/02_operations.md`.
- Telegram and emergency exit follow `strategy/02_operations.md`.

Research serves positions and instruments the project can lawfully access
on-chain, and still passes the horizon and the identity, cost, risk, and
execution checks.

## 3. Where expected return comes from

Ranked by validated evidence. Discovery, review routing, both-side evaluation,
and on-chain comparisons follow
[the opportunity method](strategy/03_opportunity_method.md).

1. **Instance catalyst mispricing.** Buy the side an instance-level reading
   supports: literal resolution criteria, `catalyst_check`, and the §4 gates.
   Bucket statistics are not an edge. No entry is justified by a price bucket
   alone. Every entry needs its own thesis clearing the robust-edge gate at a
   **0.10** haircut for instance and catalyst theses. Use **0.05** only for
   tail and monitoring fades, where measured prior drift runs the other way
   (§5). Record gated evaluations in `notes/shortdated_ledger.json`.

   Legacy positions entered on the old Dec-31 carry priors are hold-only: no
   adds from those priors. A December deadline alone does not ban a newly
   underwritten instance. New money still requires every entry gate, an
   explicit uncertainty and conditional-fill case, joint portfolio risk,
   monitoring, and net return above the best lawful executable alternative.
   [Evidence](research/2026-10-20-december-entry-scope.md).

   Position health is expected-edge APY, `(p/M−1)×365/d` versus priors
   (`check_marginal_apy.py`), not gross carry.

   **Flip-the-kill.** When verification inverts a thesis on a clean
   load-bearing fact, with no interpretation fork and no UMA-fight dependency,
   run the full gate on the opposite side. `polyclaude_enter` prints that
   check on every SKIP: the opposite side's real ask, the implied edge at
   `1−p`, and whether it clears the same haircut. A skip rejects this side,
   not the market.

   **Unexplained moves.** Before acting on a move with no visible news, check
   whether anything traded. `curPrice` is a midpoint and can swing on a thin
   book with zero volume. Check volume and spread first. Then: (a) if
   resolution depends on a source you have not checked and cannot quickly
   check, presume informed flow and do not fade it; (b) if the bar is
   mechanically checkable and a fresh verification finds the fundamental
   unchanged, treat the move as rumor flow. The question is whether someone
   could know a resolving fact you cannot verify now.

2. **Decomposition and consistency.** Same event at different prices:
   `event_monotonicity_scan.py`, `polymarket_consistency_scan.py`,
   `limitless_arb_scan.py`. A positive observation is provisional until exact
   implication, settlement, depth, costs, and partial-fill risk are
   revalidated. A capped scan's zero is a result for that slice.

3. **Sports versus bookie consensus** (`sports_pm_scan.py --with-consensus`).
   There is no separate sports edge. EV is net of the current per-market fee.
   Deploy only when the delta exceeds fees and slippage.

4. **Calendar and hazard-rate mispricing.** Traders anchor on P(event ever)
   when the contract is P(event by T). Decompose with hazard rates
   (`brownian_bridge_fv.py`, §5).

5. **Cross-source synthesis** funds probability estimates. It is rarely a
   standalone trade. If the thesis is only that you read the news, skip.

Skip after costs: passive market-making on thin Polymarket binaries; sub-day
crypto price markets; Fed no-change legs at 99%+; AI-leaderboard markets
without a gross dislocation; any thesis that is only a headline everyone has.

## 4. Entry pipeline (every gate is an EV term, in application order)

New buys are authorized by the live gates below.
[`notes/entry_review_gate.json`](notes/entry_review_gate.json) uses
`review_mode: "live_gates"`. That mode checks the policy shape and returns.
It does not keep a token allowlist. A finished research universe is not a
precondition for a new BUY.

This applies to every new Polymarket BUY, including adds, repricing, maker and
taker orders, and each leg of a bundle or pair. It does not replace the live
identity, evidence, eligibility, fee, liquidity, uncertainty, collateral,
portfolio, and execution gates. Holding management, SELL exits, cancellations,
and redemptions follow their own operating rules.

`scripts/polyclaude_enter.py` is mandatory for every entry. In the tool, gate 2
(UMA reject) and gate 5 (robust edge) are hard blocks. Gate 1 runs and warns.
Gate 3 runs only when `--my-p` is omitted; `--my-p` or `--skip-catalyst-check`
skips it, so run the catalyst check before passing `--my-p`. Gate 4 is analyst
work upstream of that `--my-p`. Do not bypass the tool with raw `clob_v2.py`.

Multi-leg structures use the same path. Repeat `--bundle-slug` for mutually
exclusive negRisk buckets and supply `--side YES`, the union probability, exact
equal shares, and a hard total cost ceiling. The tool checks common event and
negRisk identity, UMA state, zero execution delay, live depth and minimums,
CLOB match-time fees, union-level robust EV, ticket and cluster caps,
same-event exposure, deployable pUSD and allowances, and the exact on-chain
balance after every FOK. A deliberate matched add also requires `--bundle-add`.
Before the first order, every partial-fill unwind must have fee-aware bid depth
inside a bounded total-loss budget, and that bound is enforced again against
the live rollback book. A definite no-fill unwinds the earlier fills and then
re-proves every selected token is at baseline. An ambiguous, delayed,
malformed, asynchronous-trade timeout, or racy HTTP response halts until
balances reconcile. Never gate or execute a directional range one leg at a
time. Equal shares make the covered outcomes one synthetic binary.
`position_state_audit` raises hard `SET_BROKEN` if that invariant fails.

1. **Existing exposure.** Adds are sized as adds, against the combined ticket.
2. **UMA reject.** Never enter a proposed or disputed market.
3. **Catalyst gate** (`catalyst_check.py`, mandatory for fades). Anchor on the
   literal Gamma resolution criteria, with a multiplicative breakdown for
   conjunctions. During fast news, treat the model's catalysts-in-window as a
   stale floor, re-derive the live branch, and distrust a single-run swing.
4. **Resolution-criteria risk is priced, not banned.** Subjective wording
   lowers true win probability through UMA-loose risk. Default
   `P(YES) = 0.7×strict + 0.3×loose`. For multi-date events, the longest-dated
   sibling's YES price is the UMA-interpretation signal: a high long-dated YES
   means the market expects a loose reading; a low one is evidence of a strict
   reading, so lower the loose weight. When the haircut cannot be quantified,
   or a high in-window catalyst cannot be assessed cleanly, size small or skip.

   **Permanence-near-date trap.** A NO fade on all three of these is a
   UMA-loose trap: a permanence or finality qualifier ("permanent",
   "officially", "definitive"), a near-date deadline, and active real-world
   progress toward the event. An announcement can trigger a loose YES before a
   strict failure can be confirmed. When all three hold, weight loose at least
   0.5, or skip. A thin strict-edge does not survive that haircut. These are
   contested adjudications, not neglected mispricings.

5. **Robust-edge gate.** Required +EV after operating cost at the pessimistic
   bound `p − edge_haircut`. Default **0.10** for instance and catalyst theses.
   **0.05** for tail and monitoring fades (§5). Going below the class default
   needs a documented reason. A point-estimate that dies at the pessimistic
   bound is not distinguishable from zero.

   **Bond fades.** For `my_p ≥ 0.90` the pessimistic bound is
   tail-multiplicative, `1 − K·(1−p)` with K=5
   (`polyclaude_enter --tail-mult`), not the flat haircut. The tail must be
   measured first-hand on the resolving variable, and the horizon must be short
   enough that the measurement's regime still binds. A longer horizon loads
   regime-change risk the measurement cannot bound.

6. **Opportunity-cost hurdle.** Expected net return must beat the best lawful
   executable alternative after financing, dividends, gas, spread, fees,
   liquidity, correlation, and venue risk. Same-chain Aave supply is the
   investable floor, not the whole opportunity set. An on-chain index or equity
   exposure is a candidate when its forward net return clears that floor and
   the competing positions. Past benchmark outperformance is a result, not a
   forecast. Idle capital earns the best net hurdle it can actually reach. A
   small APY gap does not justify a bridge on sub-$100 amounts. Polymarket pUSD
   unwraps 1:1 to Polygon USDC.e through the deployed CollateralOfframp.
   Deploy idle into any entry that clears the pipeline. There is no static
   Aave/Polymarket allocation target.

7. **Execution route.** Ordinary single-market entries are maker-or-skip.
   `polyclaude_enter.py --execute` blocks a taker BUY unless `--taker-urgency`
   records a concrete short-lived catalyst or fill reason whose incremental EV
   exceeds fee, spread, and adverse-selection cost. Positive EV after fees is
   not enough. Multi-leg bundles stay taker-only because equal-share execution
   and bounded rollback need fill certainty. Thesis-break exits keep their
   guarded sell path.

## 5. Sizing and exits

- **Kelly plus correlation, fractional** (`portfolio_kelly.py --constrained`).
  Half-Kelly by default, quarter-Kelly for fuzzy estimates. Apply a ρ discount
  for a shared factor, including anti-correlation credit when tail paths are
  mutually exclusive. Demand an extra premium for correlated-catastrophe tails
  that pay when the rest of the book and the crypto sleeve are also down.
  Idiosyncratic tails do not.
- **Prior drift.** Instance and catalyst priors have drifted down on later
  re-derivation. Tail and monitoring priors have drifted up. The robust-edge
  default is therefore **0.10**, and **0.05** only for tail and monitoring
  fades. Mechanical tail markets are where the prior has been too pessimistic.
  N is small. Revisit when the Dec-31 book can be scored against outcomes
  rather than against later estimates.
- **Model-error guardrails.** 15% of bankroll per ticket and 30% per correlated
  cluster, measured on entry-time cost, not on later mark or a fallen bankroll.
  A ticket above 15% because the bankroll fell, with cost unchanged, is not a
  breach and is not force-sold. A breach caused by adding is a violation. Do
  not add until the ticket is back under the cap. Revisit the levels through
  the decision record as model confidence is shown.
- **No position-count cap.** Binding limits are the dollar caps, current venue
  minimum quantities, route USD minimums, and book depth. Revisit only if
  per-tick attention measurably degrades decisions, around 15 or more positions.
- **Venue floor.** Read the current minimum in shares or contracts and the
  route's USD minimum. `orderMinSize=5` means five shares, not $5.
- **Float.** Keep about $5–10 instantly deployable where the next action is
  expected. Keep the rest in Aave.
- **Execution.** Limit orders, tick-rounded. Cross only a verified live ask.
  Gamma midpoints lie. Walk the CLOB book. Never market-buy.
- **Hold and exit use different tools.**
  - A share pays $1 with probability `p` and $0 with probability `1−p`.
    `shares × p` is a central expected terminal payout, not a recovery path.
    Entry cost and the wish to avoid a realized loss are sunk.
    `exit_analysis.py` prints SELL TAKER when executable net is at or above
    the stressed hold value, including a tie. With no stressed probability
    recorded, it uses the central probability. A mark above the bid is not
    cash. HOLD CANDIDATE means the bid is strictly below that value. Grouped
    and set-only legs print HOLD — SET-ONLY; per-leg math does not sell them.
  - `portfolio_kelly.py` answers whether you would enter at this mark:
    static edge `p − mark`, time-agnostic. Use it for entries and adds. Its
    ordinary output uses the Gamma midpoint and a scalar ρ, so it ranks; it is
    not a full joint-state model. The entry wrapper rechecks executable asks
    and fees. For a material correlated hold or exit, write the joint terminal
    states explicitly.
  - `brownian_bridge_fv.py` answers whether holding is still positive EV:
    `fair_BB(t) = p^(1−t/T)`. Given no YES event through elapsed t/T, P(NO
    survives the rest) is above the unconditional prior, so a late-stage
    bond-like NO's mark should migrate toward 1. Value the hold at
    `fair_BB × max_payout`, not `unconditional_p × max_payout`. Do not trim a
    late-stage NO because static Kelly's edge compressed.
- **Consumed edge.** Sell when executable net is at or above E[hold],
  including a tie. E[hold] is `shares ×` the stressed probability when
  `p_yes_stress` or `p_no_stress` is recorded for the held side, otherwise
  `shares ×` the central probability. A model price the book will not pay is
  not cash and is not a reason to hold. `check_marginal_apy.py` still flags
  carry below the Aave hurdle. A leg stays held only when the executable exit
  is strictly below E[hold] and the spread and churn exceed the carry gap.
- **Redeem and redeploy the same tick** (`clob_v2.py redeem-all`; `--dry-run`
  for a read-only check). Resolved capital goes to the next gated entry or to
  same-chain Aave.

## 6. Information-process rules

- **Depth matches stakes.** Routine takes under $10 on a standard market get
  one zero-shot evaluation. That beat multi-agent variants on routine takes.
  Above $10, or for a new strategy class or a structural change, run skeptic
  and champion in parallel, then apply these constraints. Do not run skeptic
  alone. Use a moderated multi-round debate only when the pair splits on both
  facts and principles. Role-only prompts. No convergence-seeking language.
  The moderator checks load-bearing facts between rounds and stops on a stall.
- **Ground truth over memory or model output.** Books come from primary
  records: subgraph order rows for perps, on-chain balances for bankroll
  (`bankroll.py`), Gamma resolution and transaction hashes for Polymarket
  outcomes. A single snapshot, window, or small N gets a full-distribution
  check before it moves money. When a cheap check can reach statistical power,
  run it to power before concluding.
- **Decision records** (`decisions.py`) for every non-trivial action: thesis,
  testable prediction, size, resolution date. Backfill outcomes from
  authoritative data. Calibration is a debugging byproduct, not the objective.
- **Act when the cost is bounded, the step is reversible, and the goal is
  unambiguous.** Deferral costs missed EV. Escalate for irreversible or
  outward-facing acts, a genuinely contested goal, or data only the operator
  has. After an action, ask what the highest-leverage move is now.

## 7. Risk pricing

1. **Resolution and UMA risk.** Priced haircut, status reject, and
   `uma_status_check.py` on every held position (§4).
2. **Venue and protocol risk.** Do not concentrate the bankroll in positions
   that cannot be exited. Book depth is part of entry EV. Emergency exits use a
   three-layer check (multi-source, market reaction, on-chain ground truth) so
   a false alarm does not trigger a negative-EV exit and a real one is not
   missed. Spec: `strategy/02_operations.md`.
3. **News.** Prefer entering after an overreaction, not before a scheduled
   binary. Re-check a held thesis on a material alert against the resolution
   criteria, not the headline.
4. **Secrets.** `strategy/02_operations.md`. Never in tracked files.

## 8. Reporting

- Journal every session (`notes/journal.md`).
- Weekly `notes/pnl_weekly.md`: P&L and bankroll from `bankroll.py`, every
  market considered including rejects, the reasoning trail per position,
  mistakes, and the outlook. An outside reader should be able to reconstruct
  why each move happened.
- **Project eval (2027-04-25):** realized P&L and per-thesis post-mortems,
  against the $170 kickoff capital held flat in Aave and against a passive
  fade of every YES tail above 10%.
- Telegram is action-only: actions, material moves, decisions, restatements.
  A flat tick is journal-only.

# Working practice

Read `strategy/01_lessons.md` for recurring failure lessons,
`strategy/02_operations.md` for operational procedures,
`strategy/03_opportunity_method.md` for discovery and evaluation, and
`scripts/README.md` for tooling. Run `scripts/polyclaude_status.py` for current
state after inspecting its call path.

Use `notes/current_context.md` as a compact dated handoff.
`scripts/context_packet.py --scope <portfolio|research|engineering|operations>`
builds a bounded offline packet; check its expiry and source hashes. It does
not replace the reads above, live state, or execution gates. Do not load the
full journal, backlog, or historical lessons by default. Search for the dated
section you need. Refresh the handoff after a completed check or a material
decision when its state changed or it expired, following
`strategy/02_operations.md`.

Preserve unrelated working-tree changes, exact instrument identities, financial
records, and secret hygiene. Keep private credentials and operator material out
of tracked files and tool output. Record material decisions and verify
state-changing operations against current account and venue state.

Retrieve Telegram operator messages only through
`polyclaude-agent telegram-read --update-id` for the notified update. Do not
read inbox storage or private histories. Restrict provider and budget checks to
repository tooling. Do not search private directories broadly or print
credential values.

Send agent-composed Telegram text through `scripts/telegram.py msg --stdin`
with a single-quoted heredoc delimiter. Never place arbitrary text containing
`$`, backticks, or command substitutions in a double-quoted shell argument.
