# Lessons ledger — hard-won idiosyncrasies, single source

> Purpose: a fresh session (or one recovering from context compaction) reads THIS to
> inherit everything the journal taught the hard way, without replaying 3 months of it.
> One line of origin per lesson so it can be trusted/traced. Update IN THE SAME TURN a
> new lesson lands; prune only when a lesson is superseded (note by what).
> Doctrine lives in 00_philosophy.md; ops mechanics in 02_operations.md; this file is
> the connective "why we do it that way" layer.

## Execution mechanics (the fee decides almost everything)

- **Maker-first, always consider three exits.** Taker fee on fee-bearing markets =
  10% × min(p, 1−p) per share; maker pays $0; RESOLUTION pays $0. So every exit is
  hold vs taker-net vs maker-at-fair, and `exit_analysis.py` computes all three on the
  LIVE book. Taker breakeven = fair/(1−fee) — on SpaceX that's 1.067, i.e. taker exit
  can NEVER win there. (Prime exit gave up ~$2 crossing a thin book, 2026-07-24; Fed
  taker-vs-maker gap 2.8pp, 2026-07-28.)
- **When hold-vs-sell is close, don't choose.** Rest a post-only sell AT fair (fee-free
  breakeven IS fair) and let the market decide. Validated live: Fed 8.22sh filled at
  0.26 vs 0.25 fair, 2026-07-29 — someone paid above fair, variance retired for free.
- **Hidden-info exception (both directions).** Positions whose market has an insider
  channel (GPT-6, MacBook) get NO resting take-profit sells — an informed up-move means
  fair JUMPED and the old-fair sell donates the news. Same logic blocks resting NO bids
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

- **Verify evidence AGE before acting on any prior.** kimi went 3-for-3 catching stale
  evidence under my priors in one week (GPT-6 down, MacBook down, SpaceX UP — direction
  unpredictable). Priors carry `verified:` dates; >14d flags in both Kelly consumers.
  The world can move while the prior stands still (Satoshi: the Murphy-FOIA suit
  matured into the window; exit at fair, 2026-07-26).
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
- **Markets DE-INDEX mid-resolution** (Mojtaba, Marvel): data-api drops the row, slug
  404s, redeem-all goes blind. conditionIds are snapshotted per position
  (notes/position_condition_ids.json) and `clob_v2 redeem-one <conditionId>` claims
  without indexing. (Whether v2 redemption wants pUSD or USDC.e collateral is
  UNVERIFIED — first real redemption should test and note it.)
- **data-api /activity is ground truth** for fills/redemptions; /trades lags and MISSED
  a fill outright (Marvel 0.98, 2026-07-26). Wallet-balance arithmetic with resting
  orders is unreliable — don't reconcile by inference, pull the activity feed.
- **VM = 1.9GB. ONE background agent max, ever** (3 OOM crashes). Check MemAvailable
  >500MB before any spawn — AND check no other claude-spawning script is still running
  (watchlist --auto-revet, sports --with-consensus, catalyst_check all spawn `claude -p`
  AFTER launch, so MemAvailable at launch time under-counts; 2026-07-30: 3 concurrent
  haikus at 548MB from exactly this stack-up — killed one, no OOM).
- **Daemon-fired ticks must carry their reason** (else they read as scheduled noise and
  the alert gets answered "nothing happened" — 2026-07-28). daily_checkin passes $1
  through to the prompt.
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

- **A bulk string-replace with count=1 silently patches the WRONG call site.** Adding that dry
  path, my `t.replace(old, new, 1)` anchored on a `send_raw_transaction` line that appears in
  BOTH redeem_all and redeem_one — and redeem_all comes first, so the patch landed in the wrong
  function and corrupted it. An IndentationError on import caught it; `git checkout` restored it
  in seconds. Prefer the Edit tool for surgical patches precisely because it FAILS on a
  non-unique match instead of guessing, and keep the working tree committed so revert is cheap.

- **A loop over an empty list looks exactly like success.** My first cancel-path parse guessed the
  response shape and produced [] against 4 live orders; it printed nothing and the run looked
  clean. Only the DRILL caught it, because the drill asserts against a known truth (I knew there
  were 4). Whenever code iterates a fetched collection, the test must check the COUNT against
  something independently known — "no errors" is not evidence the collection was non-empty.
  Verify write paths the free way: an order that cannot fill (FOK at an impossible price) and a
  cancel of an id that cannot exist both return SEMANTIC errors, which proves signing, auth and
  endpoint while touching nothing.

- **An emergency exit should take partial fills, not refuse them.** The live-fire also exposed
  that FOK was wrong for this job: all-or-nothing at one price means any thinning between the
  bid you read and the order you post kills the sell and exits NOTHING — in the one situation
  where the book is guaranteed to be moving. Switched to a GTC limit at the same bid: it takes
  whatever depth exists and rests the remainder, price still protected by the slippage cap. A
  partial exit in an emergency strictly beats a clean refusal.

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

### Prior & fact hygiene — the 2026-08-11/12 cluster
*(three inverted revisions inside twelve hours, then an 18pp miss from a source that was faithfully
quoted but four months stale. Read this before touching any prior.)*

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
