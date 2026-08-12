# Polyclaude — Trading Doctrine

> Rewritten 2026-06-10 on operator directive: **the only objective is expected-return
> maximization; every rule below is derived from it** (given estimation error, venue
> facts, and the operator's boundary conditions). A rule with no derivation is a bug.
> Prior doc (rules-list era) in git history. Where this doc and live tooling disagree,
> fix one of them — don't improvise a third behavior.
>
> **Fresh session / post-compaction: read `strategy/01_lessons.md` FIRST** — the
> consolidated hard-won idiosyncrasies (execution mechanics, prior hygiene, failure
> classes) that context compaction otherwise loses.

## 1. Objective

Maximize expected compounded return on the bankroll over the project horizon
(kickoff 2026-04-25, ~1y). Authoritative bankroll number: `scripts/bankroll.py`
(reference $170 at kickoff).

Because the bankroll is repeatedly reinvested, "expected return" operationally means
**expected log growth** (Kelly): maximizing per-bet arithmetic EV with unbounded size
ruins a multiplicative bankroll even when every bet is +EV. This single fact derives
most of the sizing discipline below. Variance has no cost beyond its compounding drag
(g ≈ μ − σ²/2) and forced-liquidity risk — there is no comfort-based drawdown
aversion. Precedent: held May-31 Iran-peace NO through a −47pp mark crash on explicit
conditional-fair-value logic; resolved +47.5%.

## 2. Operator boundary conditions (the feasible set — not mine to optimize away)

- **Legal only; decentralized only** — no CEX, no KYC venues, no jurisdiction-violating
  markets.
- **<1y holding horizon per position.** Multi-year theses route to the operator's IBKR
  sleeve via Telegram (watchlist infra: `longterm_check.py`, `watchlist_monitor.py`).
- **Public repo** — no secret values, no secret paths, no raw tokens (mechanics in
  `strategy/02_operations.md`).
- **Telegram protocols + emergency-exit procedure** per `strategy/02_operations.md`.

## 3. Where expected return comes from (live edge sources)

Ranked by validated evidence, not aspiration:

1. **Case-by-case catalyst-gated mispricing (the surviving core trade).** Buying NO
   (or YES) where an INSTANCE-level analysis — strict resolution-criteria reading +
   catalyst_check + the §4 gates — shows the market materially mispricing a specific
   event (the realized-win class: the Iran calendar fades, Latvia, aliens-close).
   **Population-bucket fade harvesting is DEAD as an edge source (2026-07-03).** The
   original localization (`longshot_calibration_backtest.py`, N=1513, 2026-06-02:
   0.90–0.95 +4.8pp/3.2σ, 0.95–0.98 +2.8pp/4.7σ at ~7d) FAILED REPLICATION on 836
   fresh resolved markets with the same methodology: 0.90–0.95 −0.5pp ±2.9, 0.95–0.98
   −0.5pp ±1.9 — calibrated at mid, NEGATIVE at executable asks (+1c: −1.4/−1.7pp;
   study: logs/backtest_askadjust_v3_20260703.log). Either arbed away since June or
   the original was window-specific; both readings forbid population harvesting NOW.
   Practical rules: no entry justified by bucket statistics alone; every entry needs
   its own instance thesis clearing the robust-edge gate at the FLAT 0.05 haircut
   (the 2026-07-03 design review kept it; the gate's skips were vindicated the same
   night); `notes/shortdated_ledger.json` continues recording gated evaluations as
   the ongoing falsification record. Long-dated entries (Dec-31 book) remain
   HOLD-ONLY: held where exit-spread > negative carry, no new entries, no adds —
   expectation math at own priors puts the book at ~Aave-grade carry wearing tail
   risk. Position health = EXPECTED-edge APY ((p/M−1)×365/d vs priors,
   `check_marginal_apy.py`, fixed 2026-07-02), never gross carry.

   Two instance-pipeline rules added 2026-07-17/19 (both validated live the same week):

   **FLIP-THE-KILL.** When candidate verification INVERTS a thesis on a clean
   load-bearing fact (no interpretation fork, no UMA-fight dependency), run the
   full gate on the OPPOSITE side instead of skip-only — the kill pipeline finds
   these for free. Evidence: Bears-leave-Illinois (agent said NO; the Jun-5
   Indiana board vote implied YES cheap at 0.33; +12pp in 48h, untraded because
   the rule didn't exist yet). N=1 clean + 1 boundary exclusion (Hormuz
   interpretation fork) — treat first applications as small-sized tests.

   **UNEXPLAINED-MOVE CLASSIFICATION.** When a market moves hard without visible
   news, classify before acting: (a) if the resolution depends on a data source
   or state you have NOT checked and CANNOT quickly check (a hidden-information
   channel — e.g. Stripe-3rd's NPM valuation ladder), presume INFORMED FLOW and
   never fade it; (b) if the resolution bar is mechanically checkable and a
   fresh verification finds the fundamental unchanged (e.g. GPT-6-by-Aug-31:
   YES requires a PUBLIC release — no hidden channel exists), the move is RUMOR
   FLOW and fading it is the week's best entry class (bought the 0.68→0.61 dip).
   The classification question is always: "could someone know something that
   resolves this market, that I cannot verify right now?"
2. **Decomposition / consistency arbitrage.** Same event expressed at different prices:
   date-monotonicity violations (`event_monotonicity_scan.py`), multi-leg sum≠1
   (`polymarket_consistency_scan.py`, live-CLOB-validated), cross-venue
   (`limitless_arb_scan.py`). Persistently ~0 hits at our scale — scans stay because
   they cost nothing and a hit is near-riskless return.
3. **Mid-market sports vs bookie consensus** (`sports_pm_scan.py --with-consensus`).
   We have no sports edge; the bookie consensus is the model. EV is computed net of
   Polymarket's 3% sports taker fee like any other op-cost. Validated signal source
   (Latvia Eurovision); deploy only on delta > fees + slippage.
4. **Calendar / hazard-rate mispricing.** Traders anchor on P(event ever) when pricing
   P(event by T); decompose with hazard rates (the Brownian-bridge machinery, §5).
5. **Cross-source synthesis speed.** Primary sources read faster and wider than retail
   narrative. This funds the p estimates everywhere else; it is rarely a standalone
   trade ("no info edge over headline-watchers" — if the thesis is just "I read the
   news," skip).

Anti-edges (negative expected return after costs — skip): **passive market-making on thin Polymarket binaries** (NO-GO, DD 2026-06-17: at our scale + no latency edge, captured spread < adverse-selection + binary-resolution cost; the liquidity-rewards subsidy rounds to $0 below the $1 payout floor in crowded markets and only pays on stale wide-spread markets where you'd be the sole picked-off quote — three converging evidence streams, thread closed); sub-day crypto price
markets, Fed no-change legs at 99%+, AI-leaderboard markets absent gross dislocation
(no private edge; COI restriction lifted 2026-06-01, judged on EV like anything else),
anything whose only thesis is a headline everyone has.

## 4. Entry pipeline (every gate is an EV term, in application order)

`scripts/polyclaude_enter.py` is mandatory for every entry. Honest enforcement map:
#2 (UMA reject) and #5 (robust-edge gate) are HARD BLOCKS in the tool; #1 auto-runs
but warns rather than blocks; #3 auto-runs ONLY when `--my-p` is omitted — supplying
`--my-p` or `--skip-catalyst-check` skips it, so running the catalyst check first
stays on the analyst; #4 is analyst process upstream of the `--my-p` you pass.
Manual bypass via raw `clob_v2.py` cost real EV twice (DEC-0029).

1. **Existing-exposure check** (auto): adds are sized as adds, against the combined
   ticket.
2. **UMA status reject** (auto): never enter proposed/disputed markets — the R-U
   dispute realized −$16.73.
3. **Catalyst gate** (`catalyst_check.py`, mandatory for fades): cheap purchased
   information (~5-10K tokens) that corrects p before money moves. Anchors haiku on
   LITERAL gamma resolution criteria with a multiplicative breakdown. Lesson sources:
   DEC-0016 (missed same-day Pentagon UAP program; market was right), US-invade-Iran
   (98%→2.2% swing once criteria-anchored), peace-deal-Jun-15 2026-06-10 (scanner said
   +3.4pp, gate said −8pp; gate killed a scanner artifact). **Breaking-news caveat
   (2026-06-11):** during fast-moving windows the haiku's websearch lags by
   minutes-to-hours (one check said "neither is scheduled" mid-strikes) — treat its
   catalysts-in-window as a stale floor, re-derive the live branch yourself, and
   distrust single-run swings in its central (5.5%→18% overnight was part real,
   part run-to-run variance; the corrected synthesis sat between).
4. **Resolution-criteria risk is PRICED, not banned.** Subjective wording ("permanent
   deal", "identity revealed", "widely reported") lowers true p_win via UMA-loose
   risk. Quantify: weight `P(YES) = 0.7×strict + 0.3×loose`; for multi-date events the
   longest-dated sibling's YES price is the best UMA-interpretation signal (Dec-31
   priced 73% while strict said 30-40% → market expected loose; conversely a LOW
   long-dated YES is evidence of strict, so modulate the loose weight down). When the
   haircut is unquantifiable — or a HIGH in-window catalyst can't be cleanly
   assessed — size small (Satoshi NO at $5.64, no adds) or skip. [Replaces the
   2026-05-11 "mechanical-resolution ONLY" hard filter — a ban forfeits +EV that
   survives the haircut, and the book already rationally held priced exceptions.]
   **The permanence-near-date trap (two losses, one signature — codified 2026-06-15):**
   a NO fade on `(permanence/finality qualifier: "permanent", "officially", "definitive")
   × (near-date deadline) × (active real-world progress toward the event: live
   negotiations, an announced framework)` is a UMA-LOOSE TRAP — an *announcement* can
   trigger loose-YES in days, faster than a strict failure can be confirmed, so the
   strict reading that looks cheap is the wrong base. Burned twice: R-U "permanent
   ceasefire by May 31" (−$16.73, UMA ruled loose) and DEC-0038 "permanent peace deal
   by June 15" (−$10, disputed→leaning YES — a "permanent"-labeled but unsigned/interim
   MOU). When all three conditions hold, weight loose ≥0.5 (not 0.3) OR skip; a thin
   strict-edge does not survive that haircut. The favorite-longshot edge does NOT apply
   to these — they are not neglected mispricings, they are contested adjudications where
   resolution-arb specialists set the price.
5. **Robust-edge gate**: required +EV after op-cost at the PESSIMISTIC bound
   `p − edge_haircut` (default 0.05; smaller only for genuinely tight estimates —
   document why). Derivation: estimated edges are noisy and Kelly punishes overbetting
   a believed-but-wrong edge far more than underbetting a true one. A point-estimate
   +EV that dies at the pessimistic bound is statistically indistinguishable from
   zero — the op-cost is not.
6. **Op-cost hurdle**: annualized return must beat the riskless alternative (Aave
   supply APY, currently ~3-4%) plus friction (gas, wrap, spread, fees). Idle capital
   is never "doing nothing" — it earns the hurdle in Aave **on the chain it already
   sits on** (a ~0.5pp APY gap never justifies a bridge on sub-$100 amounts).
   Deploy idle into any entry that clears the pipeline, without an allocation-ratio
   target; discipline lives in these gates, not in a static Aave/PM split.

## 5. Sizing and exits

- **Kelly+ρ, fractional** (`portfolio_kelly.py --constrained`): half-Kelly default,
  quarter for fuzzy estimates. Fractional because input error is certain and the
  growth penalty is asymmetric. ρ-discount because correlated positions share a
  hidden factor — including ANTI-correlation credit where tail paths are mutually
  exclusive (Iran peace vs regime-fall). Correlated-catastrophe tails (pandemic,
  Taiwan, NK) deserve an extra premium demand: they pay out when the rest of the
  book and the crypto sleeve are also down, maximizing σ² exactly where compounding
  is hurt most; idiosyncratic tails (aliens, Greenland) don't.
- **Model-error guardrails** (parameters, not principles — current settings):
  **15% of bankroll per ticket; 30% per correlated cluster.** These bound the damage
  when p or ρ is simply wrong (the failure Kelly can't see). They bound 2026-06-10's
  Trump-out add at $14.40 against Kelly's $25.63 — working as intended. Revisit the
  levels as model confidence is demonstrated, via decision record.
  **Semantics (clarified 2026-08-12): these are ENTRY-TIME constraints on cost, not
  continuous constraints on holdings.** They bound what I DEPLOY against a possibly-wrong
  p or ρ, which is a decision; they do not bound where the ratio drifts afterwards, which
  is not. So a ticket sitting above 15% because the BANKROLL fell (SpaceX at 15.9% on
  2026-08-12: unchanged $29.42 cost against a bankroll that moved) is NOT a breach and
  must not trigger a forced sale — reading it as continuous would mandate liquidating into
  weakness, selling exactly when the denominator is smallest, which inverts the guardrail's
  purpose. A breach caused by ADDING is a real violation. The live consequence of drift is
  narrower and still binding: no further adds to that ticket until it is back under, which
  is what capped the 2026-08-11 MacBook add at $3.38 when conviction wanted far more.
- **No position-count cap.** [Deleted 2026-06-10: no ER derivation. Diversification
  across independent gated edges raises expected log growth; monitoring is automated
  (per-position marginal cost ≈ a UMA row + a news keyword). Binding limits are the
  $-caps, the venue's $5 `orderMinSize` floor, and book depth. Re-derive only if the
  book grows past the point where per-tick attention measurably degrades decisions
  (~15+ positions).]
- **Venue floor:** $5/ticket (`orderMinSize`). **Operational float:** keep ~$5-10
  instantly deployable on the venue where the next action is expected; rest in Aave
  (<3min withdrawable).
- **Execution:** limit orders on-grid (tick-rounded), cross only a verified live ask
  (gamma midpoints lie — stub bids vs real asks; walk the CLOB book). Never
  market-buy.
- **Hold/exit — use the right tool** (mixing them produces false signals):
  - `portfolio_kelly.py` answers "would I ENTER at this mark?" — static edge
    `p − mark`, time-agnostic. Use for entries and adds.
  - `brownian_bridge_fv.py` answers "is HOLDING still +EV?" — conditional fair value
    `fair_BB(t) = p^(1−t/T)`: given no YES event through elapsed t/T, P(NO survives
    the remainder) is strictly above the unconditional prior, so a late-stage
    bond-like NO's mark *should* migrate toward 1.0. EV(hold) at intermediate t uses
    `fair_BB × max_payout`, never `unconditional_p × max_payout`. Don't trim a
    late-stage NO because static Kelly's edge compressed — that signal is an artifact
    (standing example: aliens-NO "trim" flag = HOLD).
- **Consumed-edge exit (2026-07-04, codifying DEC-0042/0043):** when a held leg's
  MARK reaches or overtakes its HONEST prior (`check_marginal_apy.py` NEGATIVE_EDGE
  at a hygienic central — priors are honest beliefs, pessimism lives in entry gates
  only), the edge is consumed: sell into the bid whenever bid ≥ E[hold]/share — that
  realizes expectation with zero remaining variance, sheds the tail, and frees
  capital. Positive-but-sub-hurdle legs stay held (exit-spread + churn > the carry
  gap). This is pull-to-par harvesting of the Dec-31 book: exits into strength,
  never panic-trims (contrast DEC-0036). Both week-one realized gains came from
  this rule (+$0.65 hantavirus, +$1.93 regime-fall).
- **Redeem and redeploy immediately** (no-deferral): resolved capital goes to the
  next gated entry or same-chain Aave the same tick (`clob_v2.py redeem-all`;
  `--dry-run` for read-only checks).

## 6. Information-process rules (derived from cost-of-error × cost-of-compute)

- **Reasoning depth matches stakes.** Routine takes (<$10, standard market): single
  zero-shot evaluation. Empirical: N=30 retrospective shows zero-shot beats
  multi-agent on routine takes (+$0.04/$ vs −$0.04 to −$0.22), and the ground-truth-
  blind prospective N=20 confirms at interim 13/20 (final readout ~2026-06-30) —
  depth talks itself into outsmarting prices that were simply right.
  High stakes (>$10, new strategy class, structural change): spawn **skeptic +
  champion in parallel** — never skeptic alone (lone skeptics ratchet toward
  inaction), synthesize honestly, then apply this doc's constraints AFTER the debate
  (agents miss hard caps). The pair pays: it caught the haiku death-tail error and
  the 15%-cap breach on the 2026-06-10 Trump-out add. Escalate to moderated
  multi-round debate only when the pair splits on both facts and principles
  (role-only prompts — NO convergence-seeking language, it manufactures artifact
  consensus; moderator grounds load-bearing factual claims between rounds; stop on
  stall).
- **Trust ground truth over memory or model output.** Books are written from primary
  records only: subgraph order rows for perps (DEC-0026: a close booked from a
  count-diff + assumed direction sat sign-flipped 3 weeks), on-chain balances for
  bankroll (`bankroll.py` — twice hand-assembled aggregates misreported), gamma
  resolution + tx hashes for PM outcomes. Single-point signals (one snapshot, one
  window, small N) get the full-distribution check before they move money — when a
  cheap check can reach statistical power, run it to power before concluding.
- **Decision records** (`decisions.py`) for every non-trivial action: thesis,
  testable prediction, size, resolution date; outcomes backfilled from authoritative
  data. Purpose: catch systematic biases that cost return. Calibration is a debugging
  byproduct, NOT the objective (operator 2026-05-14 — optimizing calibration directly
  is Goodhart's law).
- **Default to action.** Bounded cost + reversible + unambiguous goal → decide and
  execute; deferral is a cost (missed EV + operator attention), not safety. Escalate
  only for irreversible/outward-facing acts, genuinely contested goals, or
  operator-only data. Operate as chief executive: after every action, re-ask "what's
  the highest-leverage move now?" — many small compounding state changes beat one
  polished deliverable.

## 7. Risk pricing (all expressed as EV terms, none as vibes)

1. **Resolution/UMA risk** → priced haircut + status reject + `uma_status_check.py`
   observability on every held position (§4).
2. **Venue/protocol risk** → don't concentrate the bankroll in positions that can't
   be exited (book depth is part of entry EV); pre-built emergency exits with a
   3-layer sanity check (multi-source, market-reaction, on-chain ground truth) so a
   false alarm doesn't trigger a −EV panic exit and a real one isn't missed — spec
   in `02_operations.md`.
3. **News/reflexivity risk** → prefer entering after overreactions, not before
   scheduled binaries; re-check held theses on MATERIAL alerts against resolution
   criteria, not headlines (helicopter-downing 2026-06-09: marks unmoved, catalyst
   re-check 5.5% vs 12.5% mark → hold was right).
4. **Operational/key risk** → secrets discipline per `02_operations.md`; never in
   tracked files.

## 8. Reporting (the operator's visibility is a hard deliverable)

- Journal every session (`notes/journal.md`); README refreshed as the public
  dashboard.
- Weekly `notes/pnl_weekly.md`: P&L + bankroll trajectory (from `bankroll.py`),
  every market considered incl. rejects, reasoning trail per position, honest
  mistakes list, outlook. An outside reader should reconstruct *why* every move
  happened.
- **Project eval (2027-04-25):** realised P&L + per-thesis post-mortems, benchmarked
  against (a) the $170 kickoff capital held flat in Aave and (b) a passive
  "fade every >10% YES tail" strategy.
- Telegram: action-only cadence — actions, material moves, decisions, restatements;
  flat ticks journal-only.
