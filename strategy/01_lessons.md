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
- **Check the live number before trading any headline.** Three saves in one week:
  NVDA-largest ("Apple overtakes" headline was 7 days stale, live caps said otherwise),
  BTC threshold (my own price prior was wrong — this timeline's BTC ≈ $64k), WTI $100
  (Brent headline ≠ WTI reality). The market usually knew better than the news.
- **N=1 resolutions are NOT calibration** (operator, 2026-07-21). The Brier/log-loss
  ledger over many scored calls is (`ledger_calibration.py`; score EVERY judged skip
  with a prior so misses become datapoints — the DC/Lucasfilm wrong-skips were captured
  only because skips were scored).
- **War-adjacent gates re-pull live conflict state at decision time** — never from
  memory. Tier-2 keyword demotion (right for an Iran-free book) let the ambient
  world-model go stale; the Kuwait fade was gated on peacetime logic during an active
  missile war on Kuwait (killed at deploy-time re-verify, 2026-07-26 — the re-verify
  condition attached at queue time is what saved it).

## Edges that survived (and their fine print)

- **Case-by-case instance mispricing is the surviving PM edge** (§3.1). Five population
  patterns falsified at $0 deployed. High-APY candidates are questions, not answers.
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

## Sizing & risk

- **Scale-invariance cuts BOTH ways** (operator): no "it's small" risk-crutch, AND no
  filtering thin books — capacity is a January problem, not a filter. Maximize
  expected COMPOUNDED return; variance reduction only when the Kelly/log-utility CE
  says so (the Prime sell failed this check; the Fed hold passed it).
- **Anti-correlation is real sizing relief:** Trump-out NO and Greenland NO share the
  Trump-continuity factor with OPPOSITE signs — the pair is safer than either alone.
  Conversely cluster caps bind on genuinely shared tails (SDCC family window).
- **Trump-out is ~2/3 actuarial:** age-80 mortality (~5.5-6%/yr, presidential-care
  discounted) dominates the 3% out-probability; the market's 7.5% overprices the drama
  paths. Priors file carries the decomposition.

## Ops (the failure classes that actually happened)

- **NEVER pkill/pgrep with the pattern anywhere else in the command line** — killed the
  shell THREE times (exit 144). Use `scripts/daemonctl.sh {status|stop|restart}` —
  structurally immune. Restart daemons via daemonctl/keepalive only; a bare nohup races
  the keepalive into DUPLICATE daemons (= double alerts, double tick-fires).
- **State files drift when positions change.** Closing a position must disarm its
  triggers (stale ARB trigger fired every 5min for hours, telegramming the operator);
  `position_state_audit.py --fix` reconciles triggers/priors/claim-snapshot/acked-holds
  against the live book each tick (step 3b).
- **Markets DE-INDEX mid-resolution** (Mojtaba, Marvel): data-api drops the row, slug
  404s, redeem-all goes blind. conditionIds are snapshotted per position
  (notes/position_condition_ids.json) and `clob_v2 redeem-one <conditionId>` claims
  without indexing. (Whether v2 redemption wants pUSD or USDC.e collateral is
  UNVERIFIED — first real redemption should test and note it.)
- **data-api /activity is ground truth** for fills/redemptions; /trades lags and MISSED
  a fill outright (Marvel 0.98, 2026-07-26). Wallet-balance arithmetic with resting
  orders is unreliable — don't reconcile by inference, pull the activity feed.
- **VM = 1.9GB. ONE background agent max, ever** (3 OOM crashes). Check MemAvailable
  >500MB before any spawn.
- **Daemon-fired ticks must carry their reason** (else they read as scheduled noise and
  the alert gets answered "nothing happened" — 2026-07-28). daily_checkin passes $1
  through to the prompt.
- **Session marathons hang** (2× ~4h in one day, 2026-07-27). Sentinels (TICK-EATEN,
  session-dead) cover the gap; resting orders live server-side; recommend a fresh
  session to the operator rather than pushing through — everything durable is in the
  repo precisely so context is disposable.

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
