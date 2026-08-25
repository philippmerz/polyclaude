# Lessons ledger — hard-won idiosyncrasies, single source

> Purpose: a fresh session (or one recovering from context compaction) reads THIS to
> inherit everything the journal taught the hard way, without replaying 3 months of it.
> One line of origin per lesson so it can be trusted/traced. Update IN THE SAME TURN a
> new lesson lands; prune only when a lesson is superseded (note by what).
> Doctrine lives in 00_philosophy.md; ops mechanics in 02_operations.md; this file is
> the connective "why we do it that way" layer.

## Map (read this first; dive selectively)

| Section | What lives there |
|---|---|
| Execution mechanics | fees, maker-vs-taker, resting-order selection, slippage |
| Priors & calibration | how p estimates are built, revised, and mis-set |
| Edges that survived | the live edge sources and their fine print |
| Sizing & risk | caps, Kelly, cluster correlation, liquidity |
| **Ops** (largest) | the failure classes that actually happened, in seven sub-sections: **Daemons, resources & liveness** (pkill, VM=1.9GB, fallbacks, dark panes) · **Write paths, drills & outward side effects** (dry-run traps, operator-facing alarms) · **Parsing, venue data & verifying my own output** (empty-list bugs, de-indexing, detector validation) · **Prior & fact hygiene (2026-08-10→12)** on stale/inverted priors and source-diffing · **Self-flattering numbers & display honesty (2026-08-13→20)** on midpoints, self-marking and un-applied corrections · **Stale constants & the test suite (2026-08-14→22, incl. the fee-formula ground-truth correction)** · **Verified mechanics & regime judgment (2026-08-16→20)** (regime-bounded data, measurable-interim sources, thesis-worked exits) |
| Process & operator covenant | Telegram protocol, weekly P&L, reporting discipline |

Recurring meta-shapes, if you read nothing else: *fix the CLASS not the instance* (a break
usually has a second half); *a rule written down is not a rule enforced* (make the tool print
the gap); *verify against a known truth* (absent output and failed output look identical); and
*the number that flatters you arrives with a plausible justification attached*.

## Execution mechanics (the fee decides almost everything)

- **Maker-first, always consider three exits.** Taker fee on fee-bearing markets =
  0.07 × p × (1−p) per share — QUADRATIC, wallet-verified 2026-08-22 (the long-quoted
  "10% × min(p,1−p)" was the FIELD rate on the WRONG curve: ~40% high at the tails, ~3×
  high at 0.50 — see pm_fees.py header for the two reconciled fills). Maker pays $0;
  RESOLUTION pays $0. So every exit is hold vs taker-net vs maker-at-fair, and
  `exit_analysis.py` computes all three on the LIVE book with the true curve. (Prime exit gave up ~$2 crossing a thin book, 2026-07-24; Fed
  taker-vs-maker gap 2.8pp, 2026-07-28.)
- **When hold-vs-sell is close, don't choose.** Rest a post-only sell AT fair (fee-free
  breakeven IS fair) and let the market decide. Validated live: Fed 8.22sh filled at
  0.26 vs 0.25 fair, 2026-07-29 — someone paid above fair, variance retired for free.
- **Hidden-info exception (both directions).** Positions whose market has an insider
  channel (GPT-6, MacBook) get NO resting take-profit sells AT FAIR — an informed up-move means
  fair JUMPED and the old-fair sell donates the news.
  **REFINED 2026-08-18 after four days of running the opposite in practice.** The rule as written
  reads as a blanket ban and named the two markets I then rested sells on (GPT-6 0.94, MacBook
  0.69) — doctrine and practice had diverged unreconciled, which a future session would have read
  as contradiction. The ban is correct for resting AT fair and wrong for resting ABOVE it, because
  the premium IS the compensation for jump risk. GPT-6 made the arithmetic explicit: hold-to-
  resolution at my own 0.912 is $31.01, a 0.94 fill is $31.96 certain, so resting beats holding by
  +$0.48 to +$0.90 across any plausible fill probability. The donate-the-news case is real but is
  measured against a fair I do not hold more confidently than the market does. So: **premium-to-
  fair resting sells are permitted on hidden-info markets; at-or-below-fair ones remain banned**,
  and the premium must be sized to the jump — which is exactly why MacBook (largest leg, hard
  Sep 8-10 catalyst) was rested at HALF size while GPT-6 (no edge left, 12d, liquid) went full.
  The generic form: when practice has quietly diverged from a written rule, one of them is wrong
  and finding out which is cheap — the expensive outcome is leaving both on the page. Same logic blocks resting NO bids
  on announce-markets (embargoed reveals hit NO bids). Resting YES bids on
  announce-markets are benign PRE-catalyst (informed flow lifts asks, doesn't hit bids)
  and become ADVERSE the moment the window closes — pull them at window end
  (SDCC pull, 2026-07-26: post-panel fill = "nothing announced" = adverse).
- **Resting bids fill under FUTURE information.** Allowed only with per-tick fundamental
  re-verification AND news_watcher coverage of the market's info channel; pull before
  catalyst windows. Re-verify BEFORE re-placing after any unexplained move
  (cancel-first-verify-second, GPT-6 2026-07-26).
- **Pull ALL resting orders before a SCHEDULED binary catalyst** (FOMC, earnings, ruling)
  — a sell left through the release donates the tail to whoever lifts it first
  post-print (Fed 0.26 offer vs ~1.00 post-hike ≈ $24 at risk); note the pull deadline
  at entry, don't rely on a check coinciding with the release (2026-07-29: it did,
  by luck — the offer had already filled pre-catalyst, which is the benign direction).
- **Midpoints are mirages.** Gamma mids sit between stub bids and real asks (DC "0.395"
  = 0.20/0.59 book; Prime "0.865 mark" = 0.77 real bid). Walk the live CLOB before
  believing ANY price, especially "arb" signals. Applies to our own backtests too.
- **Verify cancels against the order book, not the API response.** A "canceled"
  response raced a fill and lost 5.4sh (2026-07-28); clob_v2 cancel now re-checks and
  exits 3 if the order survives.
- **Amount precision:** integer shares × 2-dec price; on fine-tick markets round the
  price to 2 decimals (up for taker buys, down for maker bids) or the CLOB 400s.
- **Rewards program:** makers within `max_spread` of mid, size ≥ `min_size`, earn daily
  USDC (config per market at clob /markets/<cond>). Never deepen a position to farm
  rewards; never quote two-sided against your own alpha.

## Priors & calibration

- **When a market is CONDITIONAL, look for the sibling that prices the condition — do not invent
  the term someone else quotes.** 2026-08-25, pricing three Metamask FDV legs: each resolves YES
  only if MetaMask launches a token by Dec-31 AND the FDV clears a bar, so
  p_yes = P(launch) x P(FDV > bar | launch). P(launch) is a question I have no special insight
  into — and a separate market prices exactly it ("Will MetaMask launch a token by December 31,
  2026", YES 0.085). Taking that number instead of inventing one does three things: it removes my
  worst-estimated term, it forces honesty about WHERE my edge actually lives (only in the
  conditional term, if anywhere), and it hands me a free consistency check, because the conditional
  market must price at or below the condition market. That check immediately paid: FDV>700M was
  quoted 0.092 against a 0.085 precondition — logically impossible, and now an armed cross-event
  trigger. CAVEATS: a thin sibling (here $61 of 24h volume) is an anchor, not gospel — quote the
  volume next to the number; and accepting the market's term means you have explicitly declined to
  have an edge there, which is a decision to make consciously rather than by default.


- **Verify evidence AGE before acting on any prior.** kimi went 3-for-3 catching stale
  evidence under my priors in one week (GPT-6 down, MacBook down, SpaceX UP — direction
  unpredictable). Priors carry `verified:` dates; >14d flags in both Kelly consumers.
  The world can move while the prior stands still (Satoshi: the Murphy-FOIA suit
  matured into the window; exit at fair, 2026-07-26).
  **Now 4-for-4, and the missing piece was WHEN to call it (added 2026-08-18).** The fourth was a
  CONFIRMATION rather than a catch: MacBook fell 18pp on ~$162 of volume, kimi's 25-round search
  found no development justifying it, and it independently derived p_no ~0.68 against my 0.65 — so
  the move was a liquidity sweep and the right action was to hold 49 shares with confidence, not to
  trade. Note that a confirmation is as valuable as a catch: without it I was holding my largest
  position through an unexplained 18pp move, which is the state I had just described to the operator
  as my biggest fragility. THE TRIGGER, which is what was actually absent: an UNEXPLAINED move ≥15pp
  on a held position — meaning it survived step (0) as real book movement, has no news-watcher hit,
  and has no sibling to cross-check — earns one kimi call. I only ran it today because I happened to
  think of it, which is the same failure shape as the news-coverage gaps found one at a time. Cheap
  (one agent slot, ~4 min), and its output feeds the prior either way. Cross-check the reverse
  direction too: it does NOT license buying every noise dip — the same day, the resulting add still
  failed the robust-edge gate at the executable ask, and I declined it.
- **A prior CUT triggers an immediate re-size check.** portfolio_kelly's over-sized
  flag fired for 3 days after the Fed prior cut and I read it as informational because
  it lacked a HOW (fixed: it now prints the fee-free maker route). Kelly at the NEW
  prior is the position size the current you would choose; the delta is legacy.
- **Ask what a consensus number MEASURES before anchoring.** CME FedWatch's implied
  30-38% embedded an inflation-tail RISK PREMIUM (hedging price ≠ probability);
  economists were unanimously opposite. Cost: entered a ~zero-edge position believing
  10-12pp of edge (2026-07-25→26). Same family: verify-full-distribution.
- **The weekly digest's own "bare facts" need verification too.** world_state_digest is an
  LLM synthesis of curated sources, not ground truth: on 2026-08-10 it framed a biotech
  theme around a Uganda outbreak at "378 cases and growing" when Uganda's outbreak had
  ENDED on Jul-28 at 20 cases, while missing that the real epidemic (DRC, 4,053 cases) had
  already exported a case to France — the single fact that killed the trade I was building.
  Treat digest numbers as leads to check, exactly like headlines.
- **Check the live number before trading any headline.** Three saves in one week:
  NVDA-largest ("Apple overtakes" headline was 7 days stale, live caps said otherwise),
  BTC threshold (my own price prior was wrong — this timeline's BTC ≈ $64k), WTI $100
  (Brent headline ≠ WTI reality). The market usually knew better than the news.
- **N=1 resolutions are NOT calibration** (operator, 2026-07-21). The Brier/log-loss
  ledger over many scored calls is (`ledger_calibration.py`; score EVERY judged skip
  with a prior so misses become datapoints — the DC/Lucasfilm wrong-skips were captured
  only because skips were scored).
- **Check a market's IMPLICATION SIBLINGS before believing its move.** When GPT-6 NO
  dipped to 0.70 and fired the judgment trigger, the sibling Astra-timing market still
  priced the underlying event at 0.235 — implying the GPT-6 move was inconsistent with
  its own family, i.e. noise, not information. Held; the move fully mean-reverted
  overnight (2026-08-05→06). A price move that its logical siblings don't echo is a thin
  order, not news — and conversely, sibling-confirmed moves deserve the full re-eval.
  BOTH branches now validated live: the 0.65 fire on 2026-08-06 WAS real (whole Astra
  family exploded on volume) and the sibling check identified it as information within
  minutes — prior cut to market, no thesis-defense. The technique works in both
  directions, which is what makes it a test rather than a rationalization.
  Cheap check (one API call), applicable to any market with date-series or
  implication-linked siblings.
- **War-adjacent gates re-pull live conflict state at decision time** — never from
  memory. Tier-2 keyword demotion (right for an Iran-free book) let the ambient
  world-model go stale; the Kuwait fade was gated on peacetime logic during an active
  missile war on Kuwait (killed at deploy-time re-verify, 2026-07-26 — the re-verify
  condition attached at queue time is what saved it).

- **RE-READ the criteria when the world moves — reading them once at entry is not enough.**
  Twice in one week a re-read of criteria I had already "read" changed a position: the HLE
  legs (the named source is frozen, and the fallback clause triggers on "unavailable", not
  "stale") and GPT-6 (YES does NOT require the name — "recognized as a successor to GPT-5"
  also counts, which killed ~45% of my thesis's edge). Entry-time reading answers "is there
  an edge?"; the world then moves and the SAME text can answer differently. Trigger a
  re-read on: any adverse move >5pp, any real-world event in the market's domain, and at
  any prior revision. (2026-08-04/05)

## Edges that survived (and their fine print)

- **Case-by-case instance mispricing is the surviving PM edge** (§3.1). Five population
  patterns falsified at $0 deployed. High-APY candidates are questions, not answers.
- **Thin markets are where mispricings persist longest** — sharps can't size, so nobody
  corrects the price. The discovery scanner's $20k liquidity floor hid the HLE
  legs ($775-2k/leg) until the OPERATOR browsed into them (2026-08-01).
  [STATUS NOTE so this doesn't read as a win: the HLE trade itself is DOWN — see the
  fact-vs-interpretation lesson above. What this lesson validates is the FUNNEL fix
  (thin markets are worth SEEING), not that particular thesis.] Doctrine changes (scale-invariance: capacity is not a filter) must be
  AUDITED INTO scanner configs, not just applied at evaluation — the funnel decides
  what you never see. Thin-tail pass now in step 6; hits get criteria READS, not
  auto-entries.
- **Announce-at-event template:** criteria are LOOSE (any new project/season/casting via
  ANY official channel over a multi-day window; already-announced content excluded).
  SDCC went 4-FOR-4 YES including no-panel studios — the official-channels backdoor
  makes P(YES) ≈ 0.85-0.95 for ANY active entity; panel logic only picks WHERE reveals
  land. Buy active-entity YES ≤~0.80 after reading the criteria text; the cheap legs
  are the biggest edge (my 0.22/0.15 skips on DC/Lucasfilm missed +69% each). Pull
  unfilled bids at window end. Realized: Prime +59%, Marvel +43.9%.
- **Verified rumor-churn fading:** GPT-6 had 4+ rumor waves in 10 days; each verified
  no-announcement dip was buyable (0.59/0.61/0.67 all profitable). Classifier: fade
  ONLY when the bar is mechanically checkable AND verified unchanged NOW; a sustained
  MONOTONIC move (vs spike-fade) earns fair-shading and a hard judgment trigger, not
  more size.
- **Consensus-anchor trades** (PM vs external consensus: bookies, rates markets) are
  real but the anchor must be interrogated (see FedWatch above). Bookie consensus for
  sports; no scrapeable FedWatch source exists (all JS-hydrated — WebSearch daily).
- **Mechanism, not headline** (ARB): "fees to tokenholders" was relabeled TREASURY
  flow; a derived number (VELO ratio from committed terms) can close a "wait for
  publication" gate early. Read what actually accrues to whom.

- **SELF-REFERENTIAL MARKETS ARE A CONFLICT ZONE** (2026-08-03). Markets on "does
  Anthropic/Claude stay #1" put me — a Claude model — in the position of pricing my own
  maker's success. The arena.ai WebDev leg looked ~4pp cheap after fees (Anthropic #1 by
  29 Elo, 6 of top 10, yet priced 0.79 vs 0.945 for the structurally identical Text
  Arena). DECLINED anyway: I cannot audit my own optimism on that question, so the
  discrepancy is as likely to be my bias as their mispricing. Rule: on any market whose
  subject is Anthropic/Claude, apply a bias haircut that zeroes a thin edge, and NEVER
  size up on one. Adjacent-but-fine: markets about OTHER labs judged on a mechanical
  leaderboard (the HLE/Gemini legs) — the conflict is about the SUBJECT, not the domain.

- **Separate FACT bets from INTERPRETATION bets, and size them differently.** My edge is
  verifying facts the crowd hasn't checked (repeatedly proven). It does NOT extend to
  predicting how a UMA voter will READ ambiguous criteria — Polymarket has no meta-rule for
  a stale/non-reporting source, so those go to a 48h token-holder vote, i.e. a judgment call
  where the crowd's read aggregates better than mine. The HLE legs looked like criteria-
  mechanics edge but were really resolver-behaviour bets; the market moved 20pp against me
  with the source verifiably unchanged (2026-08-04), and cutting was correct. Rule: if the
  edge rests on how someone will READ something rather than on a checkable fact, size it as
  a lottery ticket, not an edge trade.

## Sizing & risk

- **Scale-invariance cuts BOTH ways** (operator): no "it's small" risk-crutch, AND no
  filtering thin books — capacity is a January problem, not a filter. Maximize
  expected COMPOUNDED return; variance reduction only when the Kelly/log-utility CE
  says so (the Prime sell failed this check; the Fed hold passed it).
- **Anti-correlation is real sizing relief:** Trump-out NO and Greenland NO share the
  Trump-continuity factor with OPPOSITE signs — the pair is safer than either alone.
  Conversely cluster caps bind on genuinely shared tails (SDCC family window).
- **A risk limit that depends on untagged data does not exist.** The 30% cluster cap
  never fired on the OpenAI cluster (~27% at entry, four positions short the same
  "AI-ships-fast" factor) because grouping was by EVENT-FAMILY and the priors carried no
  cluster tags — one Astra event hit all four at once (2026-08-06). The kelly machinery
  had cluster+rho support all along; the data wasn't there. Entry checklist now includes
  "which FACTOR cluster?" — event-family is not the unit of correlation.
- **Trump-out is ~2/3 actuarial:** age-80 mortality (~5.5-6%/yr, presidential-care
  discounted) dominates the 3% out-probability; the market's 7.5% overprices the drama
  paths. Priors file carries the decomposition.

## Ops (the failure classes that actually happened)

### Daemons, resources & liveness

- **A conversation rewind is a FILE operation — diff the worktree against HEAD before you write
  anything.** 2026-08-25: the operator rewound the session (Fable quota hit, switched to Opus) and
  said only that they had gone "a bit too far". The rewind also reverted WORKING-TREE FILES to the
  rewind point, while git history kept the real commits — so `git log` showed six commits through
  Aug-25 04:25 while `notes/journal.md` on disk ended Aug-23. The trap is that everything LOOKS
  normal: no error, no conflict, just an older file. My habitual next move is `git add -A &&
  commit`, which would have made the reverted state the new truth and silently destroyed two days
  of work (a Sunday review, two ticks, a fallback tick, a divergence ack, and priors whose
  criteria_read dates rolled back 12 days). PROCEDURE, in order: (1) `git status` — files you did
  not touch showing as modified is the tell; (2) `git diff --stat` and count +/- lines to establish
  DIRECTION per file — behind HEAD (deletions only) vs genuinely ahead; (3) copy the stale versions
  aside before restoring, so the recovery is itself reversible; (4) `git checkout --` only the files
  that are behind. Do NOT blanket-restore: `notes/inject_log.md` was legitimately AHEAD (a live
  daemon appends to it between commits), and a blanket checkout would have destroyed real state to
  fix the opposite problem. The general shape is the empty-list bug wearing new clothes — an older
  file and a current one look identical until you check the count against a known truth.


- **NEVER pkill/pgrep with the pattern anywhere else in the command line** — killed the
  shell THREE times (exit 144). Use `scripts/daemonctl.sh {status|stop|restart}` —
  structurally immune. Restart daemons via daemonctl/keepalive only; a bare nohup races
  the keepalive into DUPLICATE daemons (= double alerts, double tick-fires). The
  keepalive recognizes ONLY the exact cmdline form `<python3> <ABS-path> start` — any
  restart path that launches with a relative script path spawns a keepalive-invisible
  daemon that gets duplicated within 10 min (daemonctl itself did this, 2026-07-29,
  7.5h dual-run; fixed to absolute). After ANY daemon restart, verify `status` shows
  ONE pid ~10+ min later, not just immediately.

- **State files drift when positions change.** Closing a position must disarm its
  triggers (stale ARB trigger fired every 5min for hours, telegramming the operator);
  `position_state_audit.py --fix` reconciles triggers/priors/claim-snapshot/acked-holds
  against the live book each tick (step 3b). The drift runs BOTH directions: a judgment
  trigger written into a priors note is NOT armed until it exists in
  opportunity_triggers.json (GPT-6 NO<0.60 sat note-only while the bid touched 0.60,
  2026-07-29 — armed via new `clob_bid` kind).

- **VM = 1.9GB. ONE background agent max, ever** (3 OOM crashes). Check MemAvailable
  >500MB before any spawn — AND check no other claude-spawning script is still running
  (watchlist --auto-revet, sports --with-consensus, catalyst_check all spawn `claude -p`
  AFTER launch, so MemAvailable at launch time under-counts; 2026-07-30: 3 concurrent
  haikus at 548MB from exactly this stack-up — killed one, no OOM).

- **Daemon-fired ticks must carry their reason** (else they read as scheduled noise and
  the alert gets answered "nothing happened" — 2026-07-28). daily_checkin passes $1
  through to the prompt.

- **A fallback that never runs is indistinguishable from one that works.** daily_checkin's
  headless fallback died on `claude: command not found` (hardcoded cron PATH omitted
  ~/.local/bin) — for MONTHS, invisibly, because the normal path dispatches to the pane
  and exits before reaching it. Only building the tick-eaten RECOVERY (which forces the
  headless path) exercised it (2026-08-03). Force every emergency path at least once,
  or assume it is broken. Forcing it TWICE found two more breaks the same day: probes
  must replicate the script's `cd` (claude's session scope is cwd-derived), and
  `--resume --fork-session` on the 121MB operator transcript timed out past 4 MINUTES.
  Recovery therefore runs a FRESH session + primer (README -> 01_lessons.md -> status),
  not a fork: 7.7s vs 4min+, size-independent, and conservatism-instructed because a cold
  session lacks conversation context. Corollary: THIS FILE is the context a cold fallback
  inherits — that is what it is for, so keep it current.

- **The fallback's OWN peer check self-matches.** `pgrep -cf 'claude -p'` counts the bash
  SUBSHELL running it (its argv carries the literal pattern), so the count is +1: a LONE
  fallback sees count=2 and, under the prompt's "2+ = defer" rule, false-defers and eats the
  tick — same outage class as 2026-07-16, opposite cause from the documented `$$` trap.
  ENUMERATE with `pgrep -af 'claude -p'`, drop the `bash -c … pgrep …` line, and count the
  genuine `claude -p` PIDs (cross-check `ps … | grep -v grep`). Count OUT the pattern-bearing
  subshell, never your own claude PID. (2026-08-09: caught by verifying instead of trusting the
  raw count — cost nothing, but the "count==1 → proceed" rule as written is wrong for the
  fallback path; harden daily_checkin's prompt to say "enumerate, don't count".)

- **Liveness ≠ progress — monitor OUTPUT, not PIDs.** Three instances: news_watcher
  logged alerts but never persisted them 30h (2026-06-11); send-keys into a dead pane
  ate a tick (2026-07-16); a wedged tmux send-keys child blocked the telegram listener
  in do_wait for 27 HOURS with its PID happily alive — every operator message queued
  undelivered and the OPERATOR was the detection layer (2026-07-30). Every subprocess
  call in a daemon needs a timeout=; every daemon check needs a progress signal (child
  age, output growth, state mtime), not just pid-alive. Also: tmux clients exit 0 on
  SIGTERM — a killed send may be logged "delivered" without the text landing.

- **A dark pane has TWO causes that look identical: session hang and MODEL QUOTA
  exhaustion.** Same symptoms from inside (ticks eaten, journal stale, sentinels fire),
  opposite fixes. 2026-08-02: I diagnosed a 16h gap as the marathon-hang pattern and
  recommended a restart; the operator's actual cause was Fable quota — they fixed it by
  switching model. Check quota FIRST (cheapest, and only the operator can see it), then
  session age. Sentinel text now names quota first. Marathon hangs ARE real too (2× ~4h,
  2026-07-27), and the response is the same either way: nothing is lost — resting orders
  live server-side, everything durable is in the repo precisely so context is disposable.

### Write paths, drills & outward side effects

- **A fallback that never runs is indistinguishable from one that works — and DRY-RUN mode
  can hide the exact half that is broken.** 2026-08-12, drilling the emergency exit: it read
  all 8 positions, walked real bids and correctly slippage-aborted the illiquid leg, so the
  dry-run looked healthy. But dry-run returns before the write, and the write called
  `pc.place_limit_sell()` — the py_clob_client v1 path that has been BROKEN against v2 since
  the 2026-05-05 migration (order_version_mismatch). Written 2026-04-29, never once executed,
  so it sat broken for three months: it would have enumerated correctly, guarded correctly,
  and then failed every sell in precisely the exploit/depeg scenario it exists for. Rewired to
  clob_v2 and LIVE-FIRED with an unfillable FOK, which returned an orderID plus "FOK orders are
  fully filled or killed" — a semantic rejection, proving signing and posting work, at zero cost
  and with nothing left resting. Drill the write path, not the dry-run; an unfillable order at an
  impossible price is the free way to do it.

- **After fixing a broken path, grep for the CLASS — the same break usually has a second half.**
  2026-08-12: rewiring the emergency exit's SELL to clob_v2 left `pc.cancel()` sitting on the dead
  v1 client three lines away. That half was load-bearing, not incidental: resting sells lock the
  very shares an emergency sell needs, so a silently-failing cancel does not just leave clutter,
  it can BLOCK the exit entirely. One grep for every v1 write call across scripts/ found it in
  seconds. (positions.py and polyclaude_enter.py import the v1 client too, but make no write
  calls — checked, not assumed.)

- **Gate a side effect at the FUNCTION, not at each call site.** 2026-08-12, sweeping the
  drill-alert leak: FIVE scripts paired a --dry-run with Telegram (both emergency exits, the
  bridge, the swap, the Limitless executor) across ~11 call sites. Patching each site invites
  exactly the miss that caused the bug. Gating inside `_telegram()` itself covers every existing
  site AND every future one, since a new caller cannot forget a check it never writes. Then wire
  the flag from argparse — I gated three files and left the flag unset in all three, so the guard
  was inert: the same half-fix shape as leaving `pc.cancel()` on the dead client after fixing the
  sell beside it. A guard plus no wiring reads exactly like a guard.

- **A drill must not be indistinguishable from the real event ON THE OPERATOR'S SCREEN.**
  2026-08-12: five --dry-run drills of the emergency exit each Telegrammed a summary reading
  "submitted: 7/8", because the send was never gated on dry_run. Nothing was sold, but the
  operator saw five messages that looked like the book had just been liquidated and asked
  "Whats that". Dry-run correctly suppressed the ORDERS and completely failed to suppress the
  ALARM. When adding a test mode, enumerate every outward-facing side effect — telegrams,
  webhooks, logs the operator reads — not just the money-moving one; and make the wording
  differ ("WOULD SUBMIT" vs "submitted") so a message cannot be misread even if it does escape.
  The cost of getting this wrong is not money, it is the operator's trust in every future alert.

- **A function whose only mode is SEND will eventually be called by someone who thinks they
  are testing.** 2026-08-12: probing the redemption wiring, I called `redeem_one()` believing
  it had a dry path. It did not — it broadcast a real transaction, which reverted (correctly,
  the condition was unresolved) for 0.00808 MATIC / $0.0006. The money is nothing; the shape
  is the lesson, and it is the mirror of the emergency-exit bug found the same morning. There
  the dry-run hid the write path; here the absence of a dry-run turned a test into a write.
  Every write function needs a simulate mode, and on-chain that is free: `eth_call` executes
  against current state and reverts WITHOUT broadcasting. Added to redeem_one, it now returns
  "would REVERT: result for condition not received yet" — a semantic revert proving ABI,
  contract and signing are all correct, at zero cost, and letting resolution day be rehearsed.

- **An emergency exit should take partial fills, not refuse them.** The live-fire also exposed
  that FOK was wrong for this job: all-or-nothing at one price means any thinning between the
  bid you read and the order you post kills the sell and exits NOTHING — in the one situation
  where the book is guaranteed to be moving. Switched to a GTC limit at the same bid: it takes
  whatever depth exists and rests the remainder, price still protected by the slippage cap. A
  partial exit in an emergency strictly beats a clean refusal.

### Parsing, venue data & verifying my own output

- **Markets DE-INDEX mid-resolution** (Mojtaba, Marvel): data-api drops the row, slug
  404s, redeem-all goes blind. conditionIds are snapshotted per position
  (notes/position_condition_ids.json) and `clob_v2 redeem-one <conditionId>` claims
  without indexing. (Whether v2 redemption wants pUSD or USDC.e collateral is
  UNVERIFIED — first real redemption should test and note it.)

- **data-api /activity is ground truth** for fills/redemptions; /trades lags and MISSED
  a fill outright (Marvel 0.98, 2026-07-26). Wallet-balance arithmetic with resting
  orders is unreliable — don't reconcile by inference, pull the activity feed.

- **A bulk string-replace with count=1 silently patches the WRONG call site.** Adding that dry
  path, my `t.replace(old, new, 1)` anchored on a `send_raw_transaction` line that appears in
  BOTH redeem_all and redeem_one — and redeem_all comes first, so the patch landed in the wrong
  function and corrupted it. An IndentationError on import caught it; `git checkout` restored it
  in seconds. Prefer the Edit tool for surgical patches precisely because it FAILS on a
  non-unique match instead of guessing, and keep the working tree committed so revert is cheap.

- **I re-committed the empty-list bug ONE DAY after banking it — because I wrote the parse
  from MEMORY instead of reading the shape.** 2026-08-13: adding a "deployable cash" figure to
  wallet_status, I parsed the orders response as data["data"]["data"] when it is
  data["body"]["data"], and it printed "committed to resting BUYs: 0.000000" against a live
  $5.06 bid — a confident, wrong, load-bearing number. Identical to the run_pair_arb bug from
  2026-08-12. Knowing the lesson did not prevent it; only CHECKING the output against a known
  truth did (I knew there was exactly one bid). So the operational rule is not "remember that
  empty lists look like success" — it is: print the shape before parsing it, and assert the
  result against a number you already know. Recall is where this bug lives.

- **A loop over an empty list looks exactly like success.** My first cancel-path parse guessed the
  response shape and produced [] against 4 live orders; it printed nothing and the run looked
  clean. Only the DRILL caught it, because the drill asserts against a known truth (I knew there
  were 4). Whenever code iterates a fetched collection, the test must check the COUNT against
  something independently known — "no errors" is not evidence the collection was non-empty.
  Verify write paths the free way: an order that cannot fill (FOK at an impossible price) and a
  cancel of an id that cannot exist both return SEMANTIC errors, which proves signing, auth and
  endpoint while touching nothing.

- **A signal that fires on 100% of the book is not a signal.** The Brownian-bridge pass listed
  all 8 positions as SCALE_UP candidates. That is a tell about the tool's calibration, not an
  instruction — but the biggest outlier in it (69pp) was still worth chasing, and was where the
  stale prior was hiding. Read blanket-fire output for OUTLIERS, never for its verdict.

- **A validation layer only protects against the failure it was built for — a NEW
  detector class walks straight past it.** 2026-08-10: the monotonicity scanner's
  phantom-arb defence is a live-CLOB walk, built after mid-price artifacts (stub bids)
  produced fake edges. The first run of the new THRESHOLD pass produced six "REAL ARB"
  fires that sailed through that walk, because the books were genuinely real — what was
  fabricated was the ORDERING ("$1B" parsed as 1.0, "$50M" as 50.0, inverting a
  correctly-priced FDV ladder). Prices were validated; the STRUCTURAL claim was not.
  When adding a detector, ask which layer validates its specific claim, and if the
  answer is "none", that claim carries the whole safety burden and must be unit-tested
  against adversarial inputs BEFORE the daemon can fire on it.

- **Threshold ladders are as monotone as date ladders** (and the scanner was blind to
  them for months, having dismissed same-date families as "categorical"). Any family of
  the form ">= k" over rising k obeys P(X>=k2) <= P(X>=k1) for k1<k2. Watch for the two
  traps: an EXACT-value bucket ("wins exactly 3 seats") is a partition with NO monotone
  constraint, and a magnitude suffix must be APPLIED, not skipped.

### Prior & fact hygiene — the 2026-08-10→12 cluster
*(two valuation lessons from 08-10, then three inverted revisions inside twelve hours,
then an 18pp miss from a source that was faithfully quoted but four months stale.
Read this before touching any prior.)*

- **"Unexitable" and "worthless" are different questions — do not merge them.** 2026-08-10:
  I called the OpenAI-HLE-50 leg "moot" to the operator because it marked 0.07 with 47 shares
  of bid. But the plan for it was hold-to-resolution, which needs no bid at all, and the honest
  p_no was 0.50 — the largest edge in the book. What actually drove the word "moot" was the
  -81% P&L column. Exit liquidity governs whether I can CHANGE my mind cheaply; it says nothing
  about the value of the claim. Ask them separately, in that order.

- **A prior you would never trade on is not a prior — it is an unbooked disagreement with
  yourself.** Same day: the Gemini-HLE prior said p_no 0.70 while the market offered NO at 0.10,
  a 60pp edge I had been carrying for 8 days without buying a share. Either the number was
  fantasy or I was ignoring the best trade available; both cannot hold. The fix is not to mark
  to market — it is to decompose (P(board posts a qualifying row) + P(no row) × w_spirit ×
  P(capability)), because a decomposed prior can be checked against the world, and a vibes prior
  cannot. Audit trigger: any live position whose prior differs from mark by >25pp.

- **The mechanism: a revision FEELS like verification, so it never gets re-verified — and
  re-reading it reproduces the error perfectly.** Evidence, all found on 2026-08-11:
  (a) MacBook — my 08-08 edit cut the prior 0.70 -> 0.58 citing "Gurman anchor moved to
  late-2026/early-2027", but that phrase was the ORIGINAL window; the actual revision said
  "early 2027 is now more likely than late 2026" and that the machines would not be
  purchasable in 2026. 12pp the wrong way on the second-largest position, then defended
  TWICE with "no new information" because each re-check re-read my own note.
  (b) SpaceX — my 08-05 "correction" replaced a "$2.1T day-one bar" with "~$1.75T" and called
  the $2.1T figure wrong; SPCX in fact closed day one at $160.95, a cap above $2.1T. The fix
  was the error. So: "I corrected this on <date>" is a claim to check, not a reason to skip
  checking.
  (c) HLE — a DIFFERENT sub-type worth naming: the recorded FACTS were right (board top 38.3,
  OpenAI 25.3) but the recorded INFERENCE was wrong ("frozen since Apr-2025" — that stamp is the
  DATASET date, and the board had added GPT-5, Grok 4, Claude 4.5 and Gemini 3 Pro after it; slow,
  not dead). Wrong inferences off right facts are harder to catch, because every fact-check passes.

- **A dated primary source is not a CURRENT one — source-diffing checks FIDELITY, not
  RECENCY.** 2026-08-12: the MacBook prior was rebuilt the day before from a fetched, dated,
  correctly-quoted MacRumors/Gurman piece — and I treated "I verified against a primary source"
  as "my facts are current". The piece was from APRIL, in a supply-chain story that had moved
  three times since. Only when the market ran 10pp against me over twelve hours did I look for
  NEWER reporting, and found July supply-chain coverage (2.5M Samsung panels, shipments
  spanning late-2026 AND early-2027) that was materially less committed to 2027 than Gurman's
  April read. The verification question is therefore TWO questions: does the source say what my
  note claims (fidelity), AND is there a newer source that supersedes it (recency)? I had built
  a discipline for the first and none for the second. Practical form: when a key_fact's source
  date is old relative to the story's clock speed, searching for a NEWER source is the check —
  not re-reading the one you have.

- **The market moving hard against you IS a source-recency signal on hidden-info positions.**
  Same episode: a sustained one-directional 10pp move with no headline is exactly what informed
  supply-chain flow looks like, and the doctrine already said so for these markets. I had been
  reading each leg of that move as "flow against a freshly-sourced thesis" and acking it. Treat
  a sustained adverse move on a hidden-info position as a prompt to hunt for a NEWER source,
  not as noise to be acknowledged.

- **Only a source-diff against a genuinely FETCHABLE artifact counts as verification — and a
  URL that 403s is not one.** The audit tags a key_fact UNVERIFIED when its source is not a URL,
  but congress.gov returns 403 to WebFetch, so that link PASSES the tag while being exactly as
  unverifiable as the prose "coverage sweep" it replaced: the tag tests source SHAPE, not ACCESS.
  Where a source cannot actually be fetched, say so inline and name the independent falsifier used
  instead. On 2026-08-12 that falsifier was the market itself — an aggregated summary claimed
  Senate removal proceedings had "already concluded earlier in 2026" (conflating the 2020 and 2021
  impeachments) and what refuted it was Trump-out NO trading at 0.935, since a resolved removal
  prices near zero. Position prices are a free, always-available consistency check on any claim
  that an event has already resolved. Fetching the
  primary source and comparing its ACTUAL words to what the note CLAIMS it says is what caught
  both errors; every position "verified" by search-sweep found nothing, which is what a
  confirmation process produces. When I first populated `key_facts` I wrote 3 of 8 with sources
  like "coverage sweep" — unfetchable, so a verification against them is my memory agreeing with
  itself. The audit now tags non-URL sources UNVERIFIED. Writing the discipline down did not
  enforce it; making the tool print the gap did. Corollary: a revision must record what the
  source said BEFORE and what it says NOW — "the anchor moved to X" is an ambiguous fragment
  that encodes no direction.

- **An error's DIRECTION predicts whether it costs money.** Self-flattering errors get executed:
  the bad MacBook 0.58 made the mark reaching 0.59 read as "at fair", which under trim-at-fair
  actively invites selling a 21pp edge. Self-deprecating ones just sit: the SpaceX error
  understated the bar a rival must clear, so it made me UNDERRATE my own position and went
  unnoticed for six days. Same root cause, wildly different expected cost — so log the direction
  of every error found, and audit priors hardest when the mark is CONVERGING on them.

- **Mid-tick prior edits are drafts, not revisions; and label which clock a field is on.** Both
  inverted edits were written during routine ticks (many things updated fast) and both were
  caught during deep single-topic dives — 2-for-2 on WHEN bad edits happen. A number changed
  mid-tick carries a citation obligation until source-diffed. Relatedly, `rationale` is the
  ENTRY-TIME record and `note` is current state; reading the former as the latter is what hid a
  27pp internal contradiction for three days, so entry-time fields now say so explicitly.

- **A detector needs an ECONOMICS spec, not just a correctness spec — and the gap only
  shows up once the phantoms are gone.** 2026-08-11 produced two daemon-fired ticks, neither
  about the market: a false positive from a two-leg trigger whose level encoded the unwatched
  leg's price at arming time, and a TRUE positive worth +0.37pp that was still not worth
  waking for. Last week's bugs were phantom arbs (detector wrong); this week's are real arbs
  below the threshold of mattering (detector right, economics unspecified). Every alerting
  check now needs a floor, and the floor's justification must be MODEL ERROR, not bankroll
  size: 0.37% is 0.37% at any scale, but a sub-2pp edge sits inside my own fee/slippage
  uncertainty (the same pair measured +0.37pp and +0.59pp eight minutes apart) and a two-leg
  structure goes directional the instant one leg fills alone.

- **When you fix an instance, grep for the class in your own recent code.** The monotonicity
  floor was added at 18:28; `run_pair_arb`, which I had written four hours earlier, had the
  identical `> 0` gate and would have repeated the failure. Both scanners now take the floor
  as a parameter. The habit that catches this is asking "which OTHER call sites did I write
  with the same assumption?" immediately after any fix — not at the next reflection.

- **You do not have to trade an inconsistency to be paid by it — you have to be on the right
  side of it.** 2026-08-05 through 08-12: GPT-6-by-Aug-31 YES was priced ABOVE its own
  precondition (Astra-by-Aug-31 YES), a logical impossibility. The ARB was never executable —
  ~1pp of gross against ~5pp of taker fees, checked repeatedly — so the pair-trade bar was
  never met and I never traded it. The market corrected anyway, and because I already held the
  leg the structure said was overpriced, the entire correction accrued to me fee-free (+8.5pp
  in a day). Refines the DEC-0069 rule: an inversion identifies an inconsistent PAIR rather
  than a wrong LEG, but if you hold an INDEPENDENT view on which leg is wrong, the cheapest
  expression is simply owning that leg and waiting — no legging risk, no fees, no execution.
  Check inconsistencies for which leg you already have a thesis on BEFORE pricing the arb.

- **On a BY-DATE market, a prior that does not decay is a prior going stale on a clock.**
  2026-08-12: exit_analysis printed my first-ever "SELL TAKER NOW" on GPT-6-by-Aug-31. Verified
  instead of executing (hidden-info rule) and the verdict was an artifact of MY number, not a
  real signal — the market at 0.88 was ahead of my 0.85, which I had set the previous day with
  20 days on the clock. With 19 days left and still no waitlist, beta or early-access programme
  of any kind open, P(YES) falls mechanically every day that passes without the qualifying event,
  because the remaining window to stand up open access keeps shrinking. Raised to 0.90 and the
  sell verdict correctly vanished. Generalisation: for "will X happen by DATE" positions, the
  passage of time is itself evidence, and a prior held flat across days is drifting relative to
  reality even when no news arrives. Re-derive by-date priors on elapsed time, not just on news.

- **Check that your alerting actually covers the CRUX of each position, not just its topic.**
  2026-08-12: three HLE positions (~10% of bankroll) plus a resting bid rest entirely on whether
  agi.safe.ai posts a 2026 model row — and ZERO of the 217 news_watcher keywords across both
  tiers touched that. The thesis-break event for the whole cluster would have arrived with no
  alerting at all. It surfaced sideways, from checking whether a stale resting bid still met its
  own precondition ("resting bids allowed only with news coverage of the market's info channel"),
  which is a rule I wrote and had never actually audited against the config. The general form: a
  position's alerting requirement is not "do I watch this topic" but "would I be told if the
  specific thing that RESOLVES it happened". Audit the two against each other whenever a cluster
  grows past a few percent of bankroll.

### Self-flattering numbers & display honesty — the 2026-08-13→20 cluster
*(three instances in one day, all pointing the same way: the number that favours you is
the one that arrives with a plausible justification attached. Audit those hardest.)*

- **The HEADLINE number must walk real bids, not midpoints.** I was one step from reporting
  +19.5% when +13.7% was realizable. One leg printed mark 0.685 and +66% — the MIDDLE of a
  0.57/0.76 spread on a book with ZERO 24h volume and no bid depth above 0.60 — inflating it
  by $7.59 and the book by $8.64. Every other position's bid sat within 0.5-1.5pp of its mark,
  so it was one illiquid leg dragging the total. exit_analysis had always walked real bids, but
  that is not what I quote: a correct number in a tool you don't cite is not a correct report.
  positions.py, bankroll.py, the status telegram, the tick template and README now all carry
  REALIZABLE alongside marked. Third midpoint artifact in three days (phantom FDV ladder,
  phantom cross-event arb, then my own P&L) — the first two cost nothing because I distrust
  TOOL output by reflex; this one nearly cost an inflated report because I don't distrust MY
  OWN performance number with the same reflex.

- **Valuing the book at YOUR OWN PRIORS is not a performance number — it converts a bet into a
  claimed gain.** Deciding whether to re-base the bankroll after that finding, I computed three
  valuations of the same book: mid +18.2%, best-bid +14.1%, my-priors +30.6%. The prior-based
  figure is HIGHEST precisely BECAUSE it encodes my belief that positions are underpriced, so
  the more wrong I am the better it looks. Kept mid (conventional, market-based, right for a
  hold-to-resolution book where bid understates because I am not liquidating). Prior-based
  valuation belongs only in hold-vs-sell math, where "what do I think this is worth" is the
  question actually being asked.

- **A calibration correction you apply only to FUTURE entries and never to your live convictions
  is a ritual, not a correction.** Measured that my instance-thesis priors run 6-23pp
  overconfident (N=5, all one direction), raised the entry haircut 0.05 -> 0.10 on that
  evidence, reconciled three doctrine passages — and moved on without applying it to the thesis
  I am MOST confident about, which is exactly where a systematic overconfidence correction has
  the most work to do. Applied it: HLE board-failure input 0.85 -> 0.72, taking OpenAI>=50 p_no
  0.50 -> 0.41 and Gemini>=50 0.56 -> 0.54. No action followed — all held, lottery-sized, marks
  far below even the haircut numbers — which is precisely why it was easy to skip. The test of a
  calibration finding is whether you turn it on your strongest belief, not on the next trade.

- **A close signal is not a close DECISION until it is priced against the cost of closing.**
  2026-08-14 the hurdle scan flagged 2 CLOSE_CANDIDATEs after I cut priors — the first non-empty
  flag list all week, so it read as newly actionable. It was not. MacBook's mark had converged
  exactly onto my own fair (expected edge +0.00%), but exiting meant walking 66 shares down a
  book with 5 at the touch: $39.23 net versus $42.90 held to prior. Paying $2.92 to escape $0.00
  of negative edge is value destruction wearing the costume of discipline. Greenland "cleared"
  by $0.05 — a sixth of one $0.01 tick across 29 shares, i.e. inside the measurement error of
  the very snapshot that produced it. Same error class as marking at mid or at best-bid: a
  single number standing in for an executable path. Gate now compares exit-now-then-redeploy-at-
  hurdle against hold-to-resolution-at-own-prior, with a materiality floor of one tick x size.
  Two dependencies this creates, named now rather than rediscovered: (1) the gate is only as
  honest as the PRIOR, since an inflated prior inflates hold-value and manufactures a "hold" —
  which makes the divergence and source-staleness checks load-bearing for it, not merely
  hygienic; (2) a truly dead book fails the gate FOREVER, so the gate will correctly counsel
  holding a rotting position indefinitely. That is not a flaw in the gate — it relocates the
  error to entry time, where exit liquidity must be priced BEFORE committing, because afterwards
  the arithmetic will always tell you that you are stuck.

- **The metric you build to be honest is where the next flattering error hides — and the tell is a
  number moving when nothing happened.** 2026-08-20: two days after building the REALIZED line
  precisely because marked gains were overstating performance, the realized figure ticked +$10.57 ->
  +$10.76 overnight with ZERO settlements. That is impossible if the label is accurate, and chasing
  it found the operator's GAS DEPOSIT booked as trading profit: capital_ledger records $170 trading
  capital and ~53.8 POL gas as SEPARATE deposits, but bankroll.py counts POL/ETH market value inside
  `total` while comparing against 170. So ~$5.45 of gas the operator sent was being reported as
  return — realized was 2x too high (+$10.77 vs +$5.32, +6.3% vs +3.1%), in the one number the
  operator had just said they would judge on, inside the metric I had built to be the honest one.
  Two transferable pieces: (1) an asset that appears in the numerator must appear in the baseline,
  or its whole value reads as profit — check deposit COMPOSITION against what the total counts, not
  just the deposit total; (2) the diagnostic that works is INVARIANCE — ask what should be constant
  (realized cannot move without a settlement), then watch whether it is. Price-drift noise in a line
  labelled "settled" is a category error the arithmetic will not catch on its own.

- **"Fix it at the display layer" is incomplete until you ENUMERATE the display layers.**
  2026-08-13, in one morning, the same scope error three times: found midpoints inflating the
  book, fixed positions.py, then wrote a reasoned defence of NOT touching bankroll.py — which
  is the number I quote — then fixed that, and still left polyclaude_status's Telegram line
  grepping `mtm` alone, which is the number the operator actually READS. The principle was
  right each time and the scope was wrong each time. When a fix is "report X alongside Y",
  the very next step is to list every place X is emitted: script output, aggregator, alert,
  weekly report, README. Enumerate before patching, not after each miss.

- **Liquidity is a MEASUREMENT with a short shelf life, not a property of the market.** Same
  leg, same day: at 10:00 MacBook showed a 20pp spread, ZERO 24h volume and no bid within 5% of
  mark (exit effectively impossible); by 22:00 it showed a 1.0pp spread with $2,543 traded, but
  only 5 shares at the touch before a gap — so a full exit costs ~6.5pp rather than being
  unavailable. The correct instruction changed from "treat as unmanageable, entry size is your
  only control" to "act on a genuine break and pay 6.5pp". Both readings were right when taken.
  Re-measure before relying on either, and note that SPREAD and DEPTH move independently: a book
  can become quotable without becoming exitable.

- **A thesis-break EXIT plan on an illiquid leg is fiction — the only real lever was entry
  sizing.** 2026-08-13, first measurement of exitable depth across the book: 6 of 8 positions
  are tight (1pp spreads, 100% of the holding sellable within 5% of mark), but two are not —
  MacBook (20pp spread, ZERO shares bid within 5% of mark) and OpenAI-HLE-50 — together 22% of
  book by cost. I had written careful thesis-break rules for MacBook ("Apple announces with a
  2026 ship → re-underwrite") that quietly assume I can act on them. If that break arrives the
  market gaps and there is no bid to hit. For illiquid legs the honest rule is "hold and accept
  the outcome; re-underwrite for INFORMATION value, not for exit" — and the decision that
  actually controls the loss is the entry size, made before any of it. Measure exitable depth
  BEFORE writing an exit plan, or the plan is a comfort rather than a control.

- **Grepping for the SUCCESS string hides the failure string.** 2026-08-13: verifying the new
  flip check, I ran the entry helper and grepped for "FLIP-THE-KILL". Nothing came back, which I
  read as "the block did not run" — correct by luck. It HAD run, hit a NameError, and printed
  "(flip check unavailable: ...)" through its own except handler, which my grep filtered out.
  The diagnosis was right for the wrong reason, and had the failure string been closer to the
  success string I would have concluded the opposite. When verifying new output, grep for BOTH
  the success and failure markers, or read the full output — a filter tuned to what you hope to
  see cannot distinguish "absent" from "failed".

- **A broad `except` around code whose purpose is to BE NOTICED is self-defeating.** Same
  episode: the mechanisation of FLIP-THE-KILL — a rule that exists precisely because failures
  go unnoticed — was wrapped in try/except and would have failed silently on a variable-name
  slip. The handler printing something saved it. Guard new instrumentation with handlers that
  are LOUDER than the thing they guard, never quieter.

- **Re-reading the CRITERIA is not re-verifying the FACTS, and only one of them was gated.**
  2026-08-13: SpaceX cost the project its largest prior correction (0.95 -> 0.68) on an Anthropic
  valuation wrong by ~15x, while its criteria_read was TWO DAYS old — so no age-based rotation
  could ever have surfaced it. Measuring the book found 3 of 8 positions with a fresh check
  sitting on a source older than 60 days (Greenland 203d, MacBook 116d, SpaceX 66d). The audit
  now fires on EITHER stale criteria or a stale source. Note the fix I first proposed
  (size-weight the rotation) would NOT have caught it — worth working a fix through against the
  actual failure before building it, because the plausible one and the correct one differed.

- **An alert that CANNOT be cleared becomes wallpaper and takes the useful fires with it.**
  Greenland's freshest available source is ~200 days old because the story has not moved, not
  because I stopped looking — so the new stale-source check would have screamed forever on a
  position doing nothing wrong. Gave it a dated, expiring `source_ack` (21 days), the same shape
  as `divergence_ack`: the ack records "I looked and nothing newer exists" WITH a date, so the
  claim expires and gets re-tested instead of calcifying. Any always-on alert needs a way to say
  "acknowledged, and here is when to ask again".

- **Verification FREQUENCY does not protect you; verification COVERAGE does.** 2026-08-13,
  after SpaceX cost the largest prior correction of the project, I hypothesised that my big
  "settled" positions get less scrutiny than my small contested ones — and MEASURED it instead
  of banking it. The hypothesis was WRONG: distinct verified-dates run GPT-6 11, MacBook 7,
  SpaceX 5, Trump 4, and the three small HLE legs 3 each. Effort tracks size positively; my
  impression of obsessively checking HLE was recency bias from a few days. The real defect is
  that SpaceX was verified FIVE TIMES and still carried a fact wrong by 15x, because each pass
  re-checked whatever was salient (the IPO happening, the $2.1T bar, OpenAI's timing) and none
  ever asked about Anthropic's valuation. Re-verifying often is not re-verifying widely.

- **Write key_facts as ATOMIC claims, not bundled narratives — a bundle hides the fact you
  never checked.** The killer entry read "No plausible 2026 rival: OpenAI pushed to 2027, and a
  >$2.1T first-day close would need an S-1 already public". That is TWO independent facts wearing
  one sentence: OpenAI's timing (which I checked, twice) and every other rival's size (which I
  never checked, because the bundle's headline asserted the conclusion). One checkable assertion
  per entry, each with its own source and date, so an unchecked fact cannot hide inside a checked
  one's sentence.

- **Never move a prior on a claim you have not pinned to a dated artifact — and the tell is
  that you cannot name the source.** 2026-08-13: an aggregated search summary said Apple's M5
  chip reshuffle was "in an effort to ACCELERATE" the touchscreen line. I moved MacBook's prior
  0.62 -> 0.58 partly on that. Hours later, writing key_facts atomically forced me to admit the
  claim had no dated source — I labelled it "search sweep, not yet pinned" rather than faking a
  URL — and pinning it REFUTED it: dated coverage says Apple is "sticking with" M5 Pro/Max
  (neutral), and Gurman's own trajectory runs February "back half of 2026" -> "early 2027 now
  more likely", which is a SLIP. Reverted to 0.65. Two habits saved this: writing the weak
  source honestly instead of tidily, and treating a load-bearing unsourced claim as a task
  rather than a footnote. A summary is a lead; only a dated artifact moves a number.

- **A point estimate in a slow document describing a fast quantity is a lie with a timestamp.**
  2026-08-13 produced two instances inside an hour. MacBook's exit cost read "impossible" at
  10:00, ~6.5% at 22:00 and 9.6% at 22:40 — so the CORRECTION I wrote at 22:20 was stale by
  22:40. And a GPT-6 key_fact pinned the Astra sibling ladder at "Aug-31 ~0.22, Sep-15 ~0.54",
  which read 0.165 / 0.40 a day later: 5.5pp and 14pp of drift in a fact that exists to
  CORROBORATE a live position. Rule: when a quantity moves faster than the cadence at which the
  note gets re-read, the note carries a RANGE plus a re-measure instruction, or a pointer to the
  live source — never a value. Record instead what is STABLE about it (the Astra ladder stays
  monotone with September modal and the Aug-31 leg drifting down; MacBook's spread is reliably
  tight while depth stays thin), because the durable claim is the shape, not the number.

### Stale constants & the birth of the test suite — the 2026-08-14→22 cluster

- **The FORMULA can be wrong, not just the constant — and only a cash reconciliation
  can tell you.** 2026-08-22: the fee model (takerBaseFee/10000 x min(p,1-p)) had survived
  the stale-constant sweep, the test suite, and the mutation harness, because every guard
  validated the code against the MODEL, not the model against the WORLD. What broke it was
  the invariance rule doing its job twice in one day: realized dipped by odd amounts after
  each arb entry, and chasing those dips against wallet pUSD deltas produced two exact
  cash fees ($0.182, $0.435) that the model missed by ~40%. The true formula (docs +
  reconciliation): fee = shares x rate x p x (1-p), QUADRATIC, rate category-capped at
  0.07 — wrong CURVE and wrong RATE, ~3x overstated at p=0.50. The error direction was
  "safe" (killed marginal trades) which is exactly why nothing ever surfaced it: an
  overstatement in a gate never books a loss, it silently forgoes wins — the arb daemon's
  floor was rejecting REAL arbs. Two durable rules: (a) any formula that prices a real
  venue charge gets a GROUND-TRUTH pin in the suite (a wallet-reconciled observed value a
  future change must reproduce), not just internal-consistency cases; (b) when a metric
  built to be honest moves oddly, the reconciliation that explains it is worth more than
  the explanation — chase it to the cent, because the residual is where the next model
  error lives.

- **On a stub book, the displayed top-of-book is the STALE part — size an arb so the
  MARGINAL level clears the floor standalone.** 2026-08-22, first real monotonicity arb:
  walked +2.71pp at top-of-book, fired ~8min later, and the pretty 5+7.6sh levels were
  gone — fill came level-3-heavy at +1.42pp, under the 2pp floor I sized against. The $1
  CLOB minimum forced blending the marginal level in, and the blend assumption ("the
  cheap levels exist") is precisely what stub quotes break. Hours later the same ladder
  re-crossed with real depth and the rule made it safe to size: every level cleared
  standalone, executed inside the minute, and slippage ran POSITIVE (+3.53 walked,
  +4.75 filled). Both directions of walk-to-fire drift observed in one day; the rule,
  not the average, is what makes stub-book arbs takeable.


- **A hand-maintained constant that tracks the outside world will be stale every time you look
  at it; the fix is a fetch, not a better number.** 2026-08-14 the hold/close hurdle read 5.00%,
  documented as "≈ current Aave USDC supply APY". Live rates that morning: Polygon 2.88, Base
  3.59, Arbitrum 2.38 — the threshold governing the whole book sat 1.4pp above the best rate
  available ANYWHERE. This was the constant's SECOND staleness: 3.4% was already wrong when the
  2026-07-02 audit replaced it. Editing it a third time would have been choosing to be wrong
  again by October. Note the direction of the damage — an inflated hurdle overstates what freed
  capital earns, so exiting looks better than it is: Greenland read "exit clears by $0.05" at
  5% and "closing costs $0.17" at the true 2.88%. The stale number was arguing to liquidate.
  Retired to a fallback (kept HIGH deliberately: if the fetch dies, over-flagging costs one
  gate check while under-flagging costs real carry), with a live read, a 24h cache, a sanity
  bound, and all four failure modes tested — fallback, recovery, TTL expiry, corrupt cache.
  The class: any constant whose comment contains the word "current" is a bug with a timer on it.

- **When one stale constant turns up, the finding is the CLASS — go sweep, the same night.** The
  hurdle fix on 2026-08-14 came with a tidy sentence ("any constant whose comment contains the
  word 'current' is a bug with a timer on it"). Treating that as a claim to TEST rather than a
  line to admire found, within the hour: `POLYMARKET_FEE_RATE = 0.072` hard-coded in SEVEN
  scripts, `TAKER_FEE_RATE = 0.10` in an eighth, and a correct live read in a ninth — three
  answers to "what does a trade cost". Measured against 100 live markets the fee is not a
  constant at all: 84 charge 1000bps, 16 charge zero. It is a per-market FIELD, and both
  constants were wrong in both directions at once. The dominant error ran the dangerous way —
  0.072 understates a real 10% fee by 28%, and it sat inside the arb scanners and the entry
  filter, exactly where understating cost manufactures an opportunity that is not there. Two
  further errors fell out of the same sweep: the entry filter applied the fee MULTIPLICATIVELY
  (`p*(1+f)` for a charge that is dollars per share, understating cost 3.2pp at p=0.50) and its
  own hurdle was a 3-month-old snapshot sitting under a comment instructing periodic refresh.
  A constant nobody re-measures is not a value, it is a decaying assumption; the durable fix is
  a fetch plus a self-check that FAILS when reality moves, not a fresher number.

- **Writing the lesson does not inoculate you against the lesson.** Within the same hour as
  authoring the stale-constant rule, I shipped an exit-cost gate with a flat 0.10 fee — which
  charged Greenland (takerBaseFee=None) $0.17 of fee that does not exist and printed it as the
  REASON TO HOLD. The verdict survived on corrected math by $0.01 against a $0.29 noise floor,
  i.e. right by luck. The gap between "I know this failure mode" and "my next commit is free of
  it" is not closed by understanding; it is closed by a mechanism that re-measures. Hence the
  self-check in pm_fees rather than a comment saying to keep the number current.
  TWICE IN ONE NIGHT, which is what makes this a rule and not an anecdote. Writing
  tests/test_money_math.py I put a comment in it warning that `takerBaseFee=None` means THIS
  MARKET CHARGES NO FEE and must never be conflated with "value missing, use the fallback" —
  and the suite's first run caught me doing exactly that in fee_aware_breakeven, in code I had
  written twenty minutes earlier. Zero-fee legs (16% of markets) were charged a phantom 10%,
  overstating the arb breakeven and suppressing real opportunities. The lesson was in my head,
  then on the page, and still in the code; what removed it was an assertion that RAN. Corollary
  for this repo, which had no tests at all until 2026-08-14: the suite is not overhead, it is
  the only thing that has ever caught one of these before the money moved. Any change to code
  deciding what a trade COSTS ships with a test in the same commit.

### Verified mechanics & regime judgment — 2026-08-16→20

- **A position whose legs are only meaningful as a SET will be advised on leg-by-leg by every
  tool you own — put the pairing in the TOOL, not in a note.** 2026-08-25, minutes after adding
  honest priors to the three Metamask arb legs, both advisory tools pointed at the same leg:
  exit_analysis printed "SELL TAKER NOW (+$0.36 vs hold)" and check_marginal_apy printed
  NEGATIVE_EDGE, saved from EXIT only by the tick-noise floor and self-labelled "flips to EXIT at
  a 0.05 prior haircut". Both were arithmetically right and economically catastrophic: closing one
  leg of a matched pair converts riskless carry into a naked directional bet on a pre-launch token.
  I had written "DO NOT EXIT INDEPENDENTLY" into the priors note first — and the tools printed the
  sell anyway, because prose in a data file is not a mechanism. The fix is an `arb_paired` marker
  both tools read, which converts the verdict instead of decorating it. Note WHO the reader is: a
  headless fallback tick had run two days earlier with no conversation context, and a fallback
  follows tool verdicts mechanically — the guard exists for the session that cannot know better.

- **A display ALLOWLIST silently drops exactly the thing you just added.** Same hour: the new
  ARB-PAIRED verdict rendered as a BARE clean hold, because the holds printer showed the verdict
  only for a hardcoded prefix list (`ACKED_HOLD`, `HOLD (exit-cost gate)`). The comment directly
  above that line warned that printing a gated hold bare "is how a low-context tick concludes all
  fine about a leg that is dead money" — i.e. the code documented the failure it was committing.
  A guard that does not render is not a guard, and I would have shipped it believing it worked had
  I not re-read the output. Fixed structurally rather than by extending the list: print ANY
  non-empty verdict (clean holds carry none), so no future verdict type can be dropped. Same shape
  as the validation-layer lesson: an allowlist enumerates what you thought of, and the next thing
  you add is by definition not in it.


- **A "never observed in the data" fact has TIME-DEPENDENT strength — check what regime produced
  the observations before exporting it down the ladder.** 2026-08-19, holding the Hormuz Aug-31 NO,
  I pulled 150 prints and found the peak SINGLE DAY was 44 against a bar needing a 7-day AVERAGE of
  60 — i.e. YES requires a level never once observed. That is near-dispositive at 12 days and it is
  tempting to carry straight to the Sep-30 and Dec-31 legs of the same monotone ladder. It does not
  carry, and the reason is the regime: EVERY observation is from during the conflict. June's best
  episode (mean 10.7, peak 44) was a partial de-escalation, not a post-ceasefire recovery, so the
  series bounds conflict-period traffic and says nothing about how fast ships return once insurance
  re-rates. Decomposing Dec-31 honestly — P(ceasefire) x P(recovery | ceasefire) — spans 0.32-0.52
  around the market's 0.445, i.e. no differentiated edge, and the 44.5% that looked absurd against
  "never observed 60" is defensible. The generic error to avoid: treating a historical range as a
  bound on the FUTURE when every sample was drawn from one regime and the question is whether the
  regime ends. The same dataset that makes a 12-day fade verified-impossibility makes a 134-day one
  a geopolitical forecast.

- **Split "named resolution source" into MEASURABLE-INTERIM vs TERMINAL-ONLY — my edge only exists
  in the first.** 2026-08-18, gate-checking the Spotify "top artist 2026" family (named source,
  mechanical resolution, Dec-31 measurement, $10-25k books — superficially the exact shape that has
  worked). It fails on one structural property: Spotify publishes the resolving variable ONCE, at
  Wrapped, and no public source tracks calendar-year global streams mid-year (Kworb carries
  all-time totals and chart appearances, neither of which is the resolving quantity). Contrast the
  markets where this class HAS paid: PortWatch publishes the Hormuz 7-day MA continuously, so I
  measured 4.4-vs-60 before committing and the same measurement killed the Bab el-Mandeb sibling at
  25.1-vs-10; agi.safe.ai publishes the HLE board continuously, so "has a qualifying row appeared"
  is checkable any day. **The test is not "is the source named and mechanical" — it is "can I read
  the variable TODAY."** If the answer is no, there is no fact to verify until resolution, my stated
  edge (verifying facts the crowd has not checked) is structurally unavailable, and what remains is
  a popularity forecast against fans who follow it more closely than I do. Cheap filter, applies
  before any pricing work: find the source, try to read the CURRENT value, and skip the family if
  you cannot.

- **A rule inferred from a neighbouring case is not a verified rule — and the neighbour can point
  the wrong way.** 2026-08-12's drill established that a resting sell BLOCKS an emergency taker
  exit: it locks the very shares that path needs. On 2026-08-18, with a full-size exit resting on
  a leg that resolves in 12 days, the obvious inference was that those shares would equally block
  REDEMPTION. Measured it instead: CTF balanceOf returned the full balance with the order live —
  CLOB orders are allowance-based and never escrow. Same order, same shares, OPPOSITE conclusions,
  because one path must TRANSFER the tokens and the other BURNS them from a balance that never
  left the wallet. Had the inference stood, resolution day (the runbook's first live use) would
  have carried an invented cancel-then-redeem step: extra transactions, extra failure modes, under
  time pressure, to solve a problem that did not exist. The tell is generic — when a new situation
  resembles a case you already paid for, the resemblance is a HYPOTHESIS about a shared mechanism,
  and the cheap move is to check whether the mechanism is actually shared before importing the
  conclusion.

- **"The thesis worked and the price now reflects it" is a complete exit condition — it needs no
  thesis break.** GPT-6 NO, entered at 0.645, sat at 0.93 with the criteria re-read that morning
  confirming the bar intact and the sibling ladder confirming the thesis. Nothing was wrong; there
  was simply no edge left, and holding a zero-edge position is carrying variance for no
  compensation. The instinct to keep a winner because the reasoning still holds is the mirror of
  refusing to cut a loser because the reasoning still holds — both substitute "am I right?" for
  "am I paid?". Two mechanical guards made it actionable rather than a judgment call: the
  both-measures test SPLIT for the first time (exit +$0.39 at my prior, hold +$0.04 at the
  market's — the latter inside noise), and the measured one-directional overconfidence broke the
  tie toward exiting, which it does whenever my prior already sits below the market's.

- **Idle capital is not automatically mis-parked — price the move before making it.** The $28.12
  PM float sits in pUSD at 0%, which repeatedly LOOKS like a standing violation of "deploy idle
  same-chain capital immediately". Priced honestly it is not: Aave-Polygon pays 2.88%, so a
  realistic 2-3 week idle window is worth ~$0.05, and even 139 days of never trading is $0.31.
  Against that, `wrap_pusd.py` is one-way BY DESIGN (no pUSD->USDC.e unwrap exists), so
  capturing it means building a fresh on-chain write path against the collateral that funds all
  trading — and parking the float adds withdraw+wrap latency to entries whose edge is largest in
  the HOURS after listing (the announce template's realized record is +59% and +43.9%). Paying
  execution speed and new-write-path risk for five cents is a bad trade. Recorded because the
  question re-arises every tick and the arithmetic, not the instinct, is the answer.

## Process & operator covenant

- **Default to action; verify before state-changing commands; report failures plainly.**
  Scored skips, falsifiers, and honest re-grades (Prime, Fed) are deliverables, not
  embarrassments — the operator consistently rewards the honest number over the
  flattering one.
- **Telegram:** "telegram:"-prefixed → reply via scripts/telegram.py, always. Heartbeat
  EVERY tick. Idle replies start with "Idle".
- **Weekly P&L vs the $170 reference, grade-inflation stop on** (bankroll.py is the
  only total). Brier ledger + shortdated ledger + clean ops = the January-decision
  evidence stream. Dec-31 is the accountability date.
