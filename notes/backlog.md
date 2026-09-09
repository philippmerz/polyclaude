# Polyclaude backlog — canonical action register

Reviewed during scheduled checks and only for a concrete due trigger. This
file is intentionally short. Long evidence and superseded prose are preserved
in [the dated backlog archive](../docs/archive/backlog-2026-09-09.md) and the
linked research notes. Preserve the operator mandate, existing strategy gates,
and the bounded-run contract when working through this register.

Unless a newer dated entry says otherwise, observations and no-trade
assumptions below are as of **2026-09-09 02:00 UTC**.

## Operating guard

The 2026-09-08 bounded-run instruction is current: execute one due checklist
or event review, perform necessary verification, then stop. Do not poll, sleep,
revive the old durable ROI goal, or use `operator_followup.sh` for idle work.
Existing cron/news/opportunity/health schedules handle waiting. Disk cleanup
is manual and narrowly scoped; do not rotate the live non-O_APPEND operator
log or auto-delete files. Heartbeat warning/critical thresholds remain
<512 MiB/<128 MiB.

## Active clocks

- **2026-09-09 17:00 UTC Apple keynote; 18:30 one-shot postreview.** Market
  1499672 asks whether a touchscreen product explicitly branded MacBook is
  available for general-public purchase by Dec-31 23:59 ET. Re-read exact
  criteria, inspect credible availability evidence, and check the absent-
  announcement case. An unveiling alone is insufficient; preorders remain an
  interpretation question. Current assessment: p_no .65, HOLD / NO ADD / NO
  FLIP, zero Apple resting orders. Quotes are timestamped indicative depth,
  never guaranteed. See the dated Apple entry in the
  [backlog archive](../docs/archive/backlog-2026-09-09.md) and the
  [resting-order policy](resting_orders.md). Remove the one-shot tag
  `polyclaude-once-apple-20260909` only after the postreview fires; no replacement schedule is implied.
- **2026-09-09 20:30 AVAV call / 22:00 periodic review.** Record FY27 Q1
  disclosure even if price is unchanged. Re-vet only if **price <= $110 AND
  FY27 guidance is maintained or raised AND company-reported funded backlog is
  >= $1.2B**. Contract headlines do not establish funded backlog. This is an
  operator IBKR watchlist item, not a polyclaude equity entry.
- **2026-09-12 emergency-path drill.** Retain the existing monthly procedure
  and [emergency reference](../docs/reference/emergency.md), including explicit
  dry-run versus write-path coverage. Verify exact expected semantic results
  and actual effects on orders/balances; an empty loop is not a passing test.
- **2026-09-13 22:00 UTC USGS.** Market 4223844: recount worldwide M>=5.5
  earthquakes Sep-7 00:00 through Sep-13 23:59 ET,
  inspect late revisions and fresh depth, and form a new uncertainty-aware
  assessment only if warranted. No standing order or entry; provisional
  catalog counts are not finality. See [research](../research/2026-09-08-usgs-weekly-count-review.md).

## Protected active holdings

- **Duma 295–339 equal-share set through Sep-20:** 20 YES shares in each of
  295–309, 310–324, and 325–339. Keep the group intact: HOLD / NO ADD; never
  add, trim, or exit one leg. Current stored distribution is .18/.31/.19,
  union .68, below the .75 add gate. A new add requires **both union >= .75
  and whole-set cost <= .57**. Do not replace these stored priors from
  this register. Re-read the named primary assessments daily through Sep-20;
  stale or unchanged evidence is not a new forecast. Canonical topology is in
  [`portfolio_kelly_priors.json`](portfolio_kelly_priors.json).
- **MetaMask FDV monotonicity group through Dec-31:** treat the 700M/3B/4B
  legs and launch precondition as one protected structure; never act on a leg
  independently. Paired-payout and unpaired-crumb details remain in the
  canonical JSON and [archived fade scan](../docs/archive/fade_basket-2026-06-01.md).
- **HLE board-stasis cluster through Dec-31:** HOLD / NO ADD / NO FLIP under
  current correlation caps. This is correlated exposure, not an atomic `_groups`
  topology; re-run the exact board diff only on a board-row, criteria, or
  on-point UMA change. Do not treat capability news alone as a literal
  resolution fact. See the dated HLE entry in the [backlog archive](../docs/archive/backlog-2026-09-09.md).
- **Hormuz-normal:** economically closed after the Aug-28 sale; retain only
  claim-insurance/UMA and grading checks, and do not spend gas on dust.

## Conditional or dormant gates

- **Arena Text Overall through Sep-30 12:00 ET:** exact market 3008499 is
  valid only under `arena.ai/leaderboard/text/overall-no-style-control`, Models,
  Adjustments None, rank-first rules. Re-underwrite only on a verified Astra
  top-five result in that exact view at effective YES <= .20, or effective
  price < .04 without thesis erosion; no midpoint-only entry. See the
  [source-gate review](../research/2026-09-08-arena-source-gate-review.md).
- **HIP-4 / HIP-3:** metadata or a client shell is not a rule-identical,
  tradeable source. Revisit only with exact settlement identity, active status,
  dated source/finalization evidence, fresh depth, and verified economics; do
  not build infrastructure or fund a lead from labels/mids.
- **Limitless cross-venue inspector:** screening only. The <=3% received-
  contract fee is a bound, not a verified exact curve. Applicability, maker
  rounding, minimums, synchronized books, rule equivalence, bridge/gas and
  settlement costs remain open gates; execution stays disabled.
- **Long-term watchlist:** AVAV's gate is above. All other seed names remain
  watch-only until their stored price plus fundamental gates fire; equity
  actions route to the operator's IBKR. Do not infer a trade from a price hit
  alone. The full per-name gates remain in
  [`longterm_watchlist.md`](longterm_watchlist.md).
- **Arbitrum DRIP:** revisit only on a verifiable funded active epoch/campaign,
  exact asset/action eligibility, and conservative incentive cash proceeds
  exceeding claim/conversion/exit costs plus foregone reserve yield; no reserve
  migration or leverage from an announcement.
- **Named-source/HLE lag scanner:** build/reopen only after an HLE grade is
  positive **or a second independent instance appears**; source measurement may
  continue defensively, but no scale-up follows from an ungraded freeze thesis.
- **Stale-prior rotation:** build only if a live `verified` prior exceeds 21
  days stale or a headless fallback prints the stale tag without acting.
  **Tick cooldown:** revisit only if logs show a genuinely time-critical second
  trigger masked by the global cooldown, or two actionable armed triggers both
  have minute-scale windows. **Capital velocity:** build only after
  a second held position becomes converged yet unexitable, or one such leg
  locks >15% of bankroll.
- **Prior calibration:** no blanket haircut; policy-changing work requires
  exact identities, initial-forecast provenance, finality, missing-baseline
  disclosure and event grouping. The current skip ledger has remaining
  Dec-31 grades; re-run after those resolve, not on repeated updates.
- **Maker rewards / monotonicity:** no reward scaling or maker-arb build until
  capital, half-fill handling, actual payout, and fee/depth evidence clear the
  existing gates. Fold the monthly `pm_fees.py` distribution self-check into
  the **Sep-12** drill; do not create another schedule.
- **NYCC/SDCC playbook:** dormant until an actual listing alert. First classify
  loose online-release versus strict at-event-only wording, then re-underwrite;
  the old <=.80 template does not transfer automatically. Netflix remains a
  standing pass unless a thin-release-slate exception is independently shown.
- **US–Iran effective-ceasefire family:** watch only on a signed deal/visible
  pause or qualifying terrestrial strike. The named date is the last eligible
  START/reset date, not the 14-day completion deadline; maritime/proxy actions
  are excluded. Re-read the exact live leg and conflict state; do not repeat
  the false deadline-only NO arbitrage. Full criteria: dated backlog archive.
- **Resolution-day:** confirm final winning outcome, exact token balance, and
  successful dry-run before any operator-authorized redemption. A data-api
  `redeemable` flag alone is insufficient; losing/dust/de-indexed rows require
  the archived identity path.

- **2026-11-03 US midterms:** retain as a dated catalyst for the Trump-out
  position; no interim trade follows from the calendar reminder.

The Sep-9 AVAV and Sep-13 USGS reminders are removed after their respective
reviews; no replacement cron or standing order is created.

## Historical note map

- [resting_orders.md](resting_orders.md): compact current maker/catalyst policy;
  full dated order history is [archived](../docs/archive/resting_orders-2026-09-09.md).
- [fade_basket.md](fade_basket.md): historical/gated June scan;
  [full archive](../docs/archive/fade_basket-2026-06-01.md).
- [recoup_campaign.md](recoup_campaign.md): closed May campaign;
  [full archive](../docs/archive/recoup_campaign-2026-06-01.md).
- [arb_thesis_check_2026-06-10.md](arb_thesis_check_2026-06-10.md): expired
  June catalyst thesis; [full archive](../docs/archive/arb_thesis_check-2026-06-10.md).
