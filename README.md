# polyclaude

Autonomous agent-driven trading project. Mandate: **maximize return**. Two on-chain sleeves. Fully decentralized — no CEX, no KYC.

**Last updated:** 2026-09-11 (state snapshot updated every cron tick; this header on structural changes)

> **For the next agent:** read [`MANDATE.md`](MANDATE.md) → this README → `strategy/00_philosophy.md` → **`strategy/01_lessons.md` (the consolidated hard-won lessons — everything compaction loses)** → run `scripts/polyclaude_status.py` for current state. That's a complete onboarding in ~5 minutes. Drill into journal/decisions only when needed for specific calibration questions.

---

## Mandate + horizon constraint

**Goal:** maximize bankroll return on a project-evaluable timeframe.

**Horizon constraint (clarified 2026-05-08):** polyclaude bankroll is locked to **<1y holding horizon per position**. Multi-year plays = operator's personal IBKR sleeve, NOT polyclaude. Reason: project conclusion timeline. Long-term watchlist infra (`scripts/longterm_check.py`, `scripts/world_state_digest.py`, `notes/longterm_watchlist.md`) still runs but routes candidates to operator's IBKR via Telegram, not auto-deploys.

**Evaluation checkpoint (clarified 2026-08-28):** the operator evaluates at the **start of 2027**. Normal Dec-31 markets whose resolution/redemption lands in the first days of January count. Do not force a value-destructive Dec-31 taker exit merely to show cash at midnight. The possible ~$500 top-up is conditional on that evaluation and is not current bankroll or sizing capacity.

**Reference capital:** $170, with holdings across the PM sleeve (Polygon), crypto sleeve (multi-chain), and Aave reserves; current marked bankroll is below.

---

## Latest update — 2026-09-11 02:06 UTC

**Comparable performance:** authoritative marked whole-account bankroll is **$185.61**, including **$6.03 of separately contributed gas tokens**. PM midpoint is $154.78, while the complete depth/fee estimate is $146.23. Replacing the midpoint with that estimate gives about **$177.06 including gas**, or **$171.03 of trading value against $170 contributed: +$1.03 / +0.61%**, before VM/other costs. The reads are sequential, stablecoins and aTokens are treated at par, and the liquidation estimate is indicative rather than a synchronized executable quote. There are 12 unresolved PM positions, $147.12 reported cost, and two live zero-fill SELL orders: Greenland 19 @ .98 and Trump-out 28 @ .97. The [Sep-11 weekly report](notes/pnl_weekly.md) records the comparable Sep-4 baseline and accounting limits.

**HLE source correction and current review:** the resolving “AI Progress on Humanity's Last Exam” chart is populated by `dashboard.safe.ai/api/models`; the ten-row server-rendered table previously parsed by `source_freeze_check.py` is a different stale surface. The actual chart API grew from 44 rows on Jul-3 to 52 on Aug-4, 58 on Sep-10, and **59 on Sep-11**. The new observed row is Grok 4.6 at **39.72**. It is not Gemini Pro and does not move any held threshold: Gemini still tops at **46.2**, and GPT-6 Astra remains **53.6**. Active maintenance was already incorporated in central `p_no` values of next-Gemini-Pro debut ≥40 **0.20**, Gemini ≥50 **0.35**, and OpenAI ≥55 **0.30**, so those estimates remain unchanged. Fresh complete net exits are $16.678960/$9.594373/$2.384044 versus central hold payouts $33.80/$20.553192/$5.70. Hold all three; no enlargement, taker exit, or new maker order. The Sep-10 erroneous exit/re-entry remains a **$2.442466 cash loss**, despite positive re-entry EV.

**Passive benchmark:** the same $70/$100 contribution schedule, entered at the first completed trading session strictly after each ledger date, is worth **$179.32 in VT (+5.48%)**, **$180.01 in VTI (+5.89%)**, or **$180.09 in SPY (+5.93%)** at the Sep-10 completed close. Against the current $171.03 depth-based trading value, the pilot trails those asynchronous comparators by about **$8.29–$9.06**, or roughly 4.9–5.3 percentage points of capital. The reproducible policy and script exclude gas and model ideal fractional shares, reinvested distributions and zero trading/tax friction.

**Index allocation review:** broad equities are now an explicit investable outside option, but no purchase clears the net-return gate today. A +2.25% modeled SPX price return through Dec-31 loses at 1x to Ostium's current 5.805% annualized long carry, Aave opportunity cost and legal/venue risk; its $0.10 oracle reserve is refunded after a successful full close and is not counted as a lifecycle cost. Spot SPYx through Jupiter is the best alternative found, but its estimated $0.45-$0.85 one-off bridge/setup/exit cost erases the edge on the current $23.49 reserve. Current full-position exit quotes also lose to their recorded central hold values after the actual index route cost. The stale legacy Ostium approval was revoked after proving zero open trades and limits. Full arithmetic, route evidence and reopening gates are in the [Sep-10 index allocation review](research/2026-09-10-index-allocation-review.md).

**Other current decisions:** VCIOM's Sep-10 list forecast supports the protected Duma 295–339 union's existing **0.72** estimate but supplies no independent district forecast. Hold all three equal legs; do not add because the probability gate (≥.75) and price ceiling (≤.57 per covered payout dollar) both fail. The direct MetaMask token-launch sibling fell to a **0.07** midpoint; updated conditional priors strengthen the protected group, whose $44.75 rule floor and $45.99 central fair remain above its $43.29 complete exit. Hormuz-normal finalized **NO**; the four linked decisions are graded, and its remaining 0.003571 winning dust is below redemption gas. Apple NO remains **0.55 / HOLD / NO ADD**. Full HLE recovery reasoning and transaction evidence remain in the [Sep-10 autonomy review](research/2026-09-10-frontier-model-autonomy-review.md).

## Earlier update — 2026-09-09 14:19 UTC

This later snapshot supersedes the 02:01 figures and blanket HLE HOLD assessment below. Indicative whole-account net liquidation ~$176.63, including $6.26 gas; trading net ~$170.37 against $170 contributed (+$0.37/+0.22%, before VM/other costs). Marked bankroll $182.20 at 14:19:23 UTC; PM midpoint $148.69, indicative fee/depth proceeds $143.12. Settled realized P&L +$14.44; open liquidation P&L −$14.07. Sequential estimates, not synchronized executable cash; four targeted books had older timestamps.

Thirteen active PM positions ($157.20 cost) and five LIVE SELL orders with zero matched size; no BUY/Apple orders or position/order changes. Reserves approximately $2.12 pUSD, $16.11 Polygon Aave and $7.87 Arbitrum Aave; Ostium has no open position.

**HLE proposal exception:** OpenAI ≥50 is UMA `proposed`, YES/NO .997/.003 despite an unchanged named board. Proposal is not finality; old automatic HOLD output needs fresh underwriting. OpenAI ≥55's fresh 19-share NO depth estimate fell to $2.57. Numeric priors remain unchanged pending verified evidence. See the [preserved Sep-9 risk review](research/2026-09-09-hle-uma-proposal-review.md) and [journal](notes/journal.md). Apple review remains Sep-9 18:30 UTC and AVAV 22:00 UTC.

## Earlier state (snapshot 2026-09-09 02:01 UTC; superseded where noted above)

**PM sleeve** `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B` (Polygon) — [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) · [Polygonscan](https://polygonscan.com/address/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) · [DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)

**Whole-account performance:** indicative net liquidation **~$177.47**, including **$6.22 gas-token value**; excluding gas, **~$171.25 versus $170 contributed: +$1.25 (+0.74%) before VM/other operating costs**. Authoritative marked bankroll is **$184.49 at 02:01:44 UTC**, up $4.25 from Sep-8 14:01. PM midpoint **$151.03**, indicative fee/depth net **$144.0099083** (gap ~$7.02). Net liquidation replaces only the PM midpoint in the authoritative total and uses rounded non-PM outputs; it is sequential, not synchronized or freshness-verified executable cash, and excludes withdrawal/transfer costs. Settled P&L **+$14.44** remains secondary to whole-account performance; unrealized liquidation **−$13.19**, marked **−$6.16**. Thirteen active quantities match the pre-tick committed claims within 1e-6; cost $157.20. All 13 bankroll walks covered their full quantity. Authenticated orders at 02:01:06: five LIVE SELLs, each matched size zero, no BUYs/Apple orders. No trade/order change. Earlier drawdown evidence: [Sep-8 review](research/2026-09-08-1000-portfolio-depth-check.md).

**Holds and gates:** unchanged priors: Gemini ≥50/debut ≥40 **0.55/0.60**, OpenAI ≥50/≥55 **0.35/0.40**, Apple **0.65**, Trump-out/Greenland **0.97/0.95**. UMA flagged Apple YES **.855→.720** and OpenAI ≥55 YES **.725→.775**; no new finality alert. Apple remains HOLD / NO ADD ahead of today's event, without treating lack of an announcement yet as year-end absence. Duma's daily source review retains **0.18/0.31/0.19**, union **0.68** below the ≥0.75 add gate; equal quantities stay protected. Duma/MetaMask indicative exits **$11.86/$43.50** versus raw fair $13.60/$46.80; MetaMask's $44.751 rule-based minimum payout is before time/resolver risk, not a stop price. All exit verdicts HOLD; stored priors are unproven estimates. The HLE table still matches Jan-15 across ten model rows and both scores. Both OpenAI criteria were re-read; the named-source/unavailability condition is unchanged. See [backlog](notes/backlog.md) and [journal](notes/journal.md).

Official tool-enabled OpenAI and Google results already clear the held HLE thresholds: the remaining thesis rests on the named board's reporting and resolver interpretation, not an absence of demonstrated capability.

**Separate price-alert verification, 02:03:32 UTC:** exact Gamma/CLOB identities matched for Apple and OpenAI ≥55. Apple NO book **.26/.30**, age **12.0s**, covers 49.005 shares for **$11.69761952 net**; OpenAI ≥55 NO **.22/.23**, age **1.7s**, covers 19 shares for **$4.049584 net**. Neither is guaranteed executable later or part of a synchronized portfolio quote. These remain below 10pp-stressed hold estimates of $26.95/$5.70; that comparison depends on uncertain priors, not proven calibrated fair values. The portfolio-wide pass did not independently validate every book's identity/age.

**Reminders and balances:** Apple’s official keynote is Sep 9 at 17:00 UTC, with the one-shot review armed for 18:30; AVAV research is scheduled for Sep 9 at 22:00 UTC per the backlog. There is no economic Hormuz exposure beyond **0.003571** dust; Iran–Oman is closed at a $5.03 loss already reflected in settled P&L. The Sep-9 02:01 balances round to **$2.12 pUSD**, **$16.11 Polygon aUSDC.e**, and **$7.87 Arbitrum aUSDC**. The ledger has 54 records (22 scored forecast rows, 16 matched-baseline rows after the 06:08 exact-identity Kuwait NO grade; neither count represents independent outcomes). First forecasts cover 16 distinct questions, with shared-event dependence still material. No original forecast or price changed. Tests last passed at **643 total / 156 money-math checks**, including 38 isolated calibration tests and three missing-quote watchlist-reporting regressions; this update changes no code. The earlier disk-full ledger truncation was fully recovered and field-verified. With VM expansion explicitly rejected, authorized manual housekeeping on Sep 8 removed seven obsolete user-owned artifacts (the two superseded Claude native versions and five study JSONL files), **692,874,130 bytes** total; free space rose from **516,726,784** to **1,209,585,664 bytes** (~**1.126 GiB**) at 10:23 UTC. No archives were made; scripts and small results were preserved, the current CLI `--version` passed, all four daemon PIDs remained unchanged/live, and key state JSONs were valid. Private histories/inbox/credentials and active logs were untouched. The old active operator log (~115.7 MB) is non-O_APPEND and must not be copy-truncated or rotated while live; no log policy or restart was implemented. The hourly heartbeat guard remains warning below 512 MiB and critical below 128 MiB; future cleanup is manual and narrowly scoped.

**Operating model (operator-authorized update 2026-09-08): bounded, event-driven work** — cron and 24/7 news/opportunity/health daemons trigger concrete reviews; complete the due work and verification, then stop. No indefinite ROI goal, idle LLM polling or self-perpetuating "anything else?" loop. This supersedes the July continuous-research and August automatic-goal-continuation instructions without changing the ROI mandate or safety checks. Five population edges falsified this month at $0 deployed (short-dated fade buckets N=836, new-listing mispricing N=833, UMA dispute-window N=2,246, cross-event implication arbs 4,575 pairs) — every falsification shipped a permanent gate upgrade (fee-aware EV, dispute priors, sibling-market routing). Surviving edge = case-by-case catalyst-gated instance mispricing (doctrine §3.1). Ostium's 2026-07-15 $18M oracle exploit: zero exposure (skeptic+champion had parked the planned OLP deposit — DEC-0040). Any Iran/war-adjacent entry must re-pull live conflict state; there is currently no economic Iran/Hormuz exposure beyond 0.003571 claim dust. Run `scripts/bankroll.py` + `scripts/polyclaude_status.py` for live figures.

Run `scripts/polyclaude_status.py` for live numbers (positions, hurdle scan, watchlist, UMA, Kelly portfolio constrained, news alerts).

**Crypto sleeve** `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` (multi-chain) — [DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) · [Arbiscan](https://arbiscan.io/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) (Ostium + Aave-Arb) · [Basescan](https://basescan.org/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) (Aave-Base) · [Polygonscan](https://polygonscan.com/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) · [Optimism Etherscan](https://optimistic.etherscan.io/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)

Note: Ostium has no public per-address trader profile (wallet-connect SPA). DeBank aggregates Ostium positions + Aave aUSDC + cross-chain balances; Arbiscan shows the raw on-chain trace incl. each Ostium open/close.

Ostium: 0 open perps (SPX / NDX / XAU all TP-closed May-2026; planned OLP deposit parked pre-exploit — zero exposure through both exploit reports, $18M→$24M revised). Crypto sleeve has ~$7.87 aUSDC Aave-Arb plus small stable/gas balances. The PM wallet holds about 16.11 aUSDC.e on Polygon, $2.115500 pUSD operational float, and small raw stable/gas balances after closing DEC-0114. Status scripts read aTokens/pUSD directly, so idle capital is always visible. Run `scripts/crypto_status.py` + `scripts/aave_deposit.py rate` for live figures.

**Long-term watchlist** (31 machine-monitored price gates; equities and multi-year ideas surface to the operator, while only explicitly <1y EVM catalysts may route back to polyclaude): `notes/longterm_watchlist.md` + `notes/watchlist_triggers.json`. Auto-monitored via `scripts/watchlist_monitor.py`; every hit is a re-underwriting trigger, never an automatic buy. LRCX's stale $280 gate fired Sep-3, but a fresh 2/4 check rejected entry near 50x trailing earnings and tightened the research gate to $190.

---

## Architecture (3 autonomy layers)

1. **Reactive** — `scripts/news_watcher.py` polls 11 RSS feeds every 5 min; tier-1 events auto-fire `daily_checkin.sh`. Tier-2 events queue to `notes/news_alerts.jsonl`. Title-hash dedup + start-guard against duplicate daemons.

2. **Scheduled** — cron at `02:00 + 14:00 UTC` runs `scripts/daily_checkin.sh`. It uses the operator's durable conversation queue when available and a fresh, fully onboarded headless fallback when the operator is down.

   - Hourly `scripts/arb_cron.sh` runs `scripts/limitless_arb_scan.py`.
   - Light `inject_prompt.sh "Periodic check..."` at 06/10/18/22 UTC.
   - Sunday 16:00 UTC: weekly long-term review (rotating 2-3 of 9 domains via `world_state_digest.py`).

3. **Interactive** — `scripts/telegram_listener.py` long-polls Telegram; authorized operator messages enter the same ordered conversation queue as local follow-ups. Telegram replies are action-only by convention (cron tick sends structured summary; material moves outside ticks ping immediately).

   - Reply to new authenticated Telegram operator messages through `scripts/telegram.py msg "..."`, honoring the private one-time-reader contract: `ALREADY_CLAIMED` means no action or duplicate reply; `EXPIRED` means only a generic fresh-resend request.

---

## Tool inventory

### Discovery + scanning
- `discover_markets.py` — pulls active Polymarket markets, filters by the live Aave-Polygon hurdle APY + 3d horizon floor + spread/liq quality. Bond-like-fade lens.
- `sports_pm_scan.py` — sports markets in 48h window with mid-market lens (BOND_LIKE_FADE_NO/YES, MID_50_50, STRONG_FAVORITE). `--with-consensus` uses a scoped fast research worker for bookie-odds deltas; opt-in `--with-kalshi` attaches strictly matched, unauthenticated public-book evidence through `kalshi_consensus.py` with no execution path.
- `event_monotonicity_scan.py` — date- and threshold-ladder inconsistency scanner. Date comparisons require identical child propositions, payout-rule templates, explicit semantic deadlines and consistent Gamma metadata before live-book validation; event membership alone never establishes a hedge.
- `polymarket_consistency_scan.py` — neg-risk basket scanner over an explicit non-sports, evaluation-horizon, top-volume keyset slice (5,000 open markets by default, completing the boundary event). Coverage, live-book budgets and every skipped leg are published explicitly; an incomplete clean result is never described as an exchange-wide zero. Positive sequential-book observations require refreshed Gamma/CLOB identity, fees and full minimum-size depth, but remain provisional revalidation leads—not execution claims.
- `macro_pm_scan.py` — Polymarket FOMC/CPI/macro markets in 60d window. **v1 LIMITATION: --with-consensus is unreliable because CME FedWatch is JS-rendered. Use --no-consensus.**
- `world_state_digest.py` — bare-fact synthesis from `notes/primary_sources.md` (~46 curated factual URLs, 9 domains). Distills "what's underpriced given THESE facts." Sunday cron.
- `limitless_arb_scan.py` — conditional cross-venue screen. Expands Limitless groups into exact priced leaves (never invented 50c parents); uses net-contract fee accounting and full PM fee schedules. Its Polymarket match universe is an official-keyset, volume-ranked 3,000-market bounded slice, labeled partial unless exhausted. Request/schema/identity failures abort without publishing. Proper-noun/Jaccard guards and agent criteria review prioritize leads, not trades. `limitless_arb_executor.py` is a public-read, execution-disabled inspector: validates identities/freshness, mirrors NO from the YES book, and delegates both-leg depth/cap/per-fill fee arithmetic to `limitless_quote_math.py`. Unknown exact fees/rounding, Limitless minimums/freshness and rule equivalence remain explicit gates.

### Vetting + sizing
- `catalyst_check.py` — for event-driven binary Polymarket markets. Uses a scoped web-research worker only after an exact Gamma identity supplies literal resolution criteria; missing, ambiguous, or partially covered lookups stop before analysis. Outputs central P(YES) with multiplicative breakdown for conjunction questions.
- `longterm_check.py` — multi-year horizon thesis-check. 4D framework (cyclical / secular / catalyst / margin). Used for IBKR-side candidates.
- `portfolio_kelly.py` — full-book Kelly audit (per-position sizing now inline in `polyclaude_enter.py`). `--constrained` reserves each configured multi-leg structure once before scaling ordinary legs. Group rows expose joint state-priced fair/floor values and complete fee-aware component asks at the exchange's executable minimum size; member legs never emit add/trim recommendations. Ordinary scale-in suggestions are suppressed when either live fee-inclusive ticket cost leaves insufficient 15% headroom or aggregate cluster cost leaves insufficient shared 30% headroom; `polyclaude_enter.py` remains the final commitment-aware gate.
- `position_groups.py` — pure fail-closed topology engine for multi-leg economic positions. Exact slug/side/token/event/deadline/quantity validation, state-payoff valuation, aggregate drawdown, per-level-fee full exits, and component-level adds. Canonical topology is `_groups` in `portfolio_kelly_priors.json`; malformed or partial structures remain protected from leg-level fallback.
- `brownian_bridge_fv.py` — first-principles hazard-rate pricing for bond-like fades. fair_mark(t) = p^(1-t/T). Surfaces TRIM (mark > fair) and SCALE_UP (mark < fair) signals.

### Monitoring + safety
- `polyclaude_status.py` — single-command aggregator: positions + hurdle + watchlist + UMA + Kelly + Brownian-bridge + news. Operator's go-to state-check.
- `check_marginal_apy.py` — EXPECTED-edge scan: (p/M−1)×365/d vs honest priors from portfolio_kelly_priors.json (fixed 2026-07-02 from win-assumed carry math), executable-bid NEGATIVE_EDGE/close-candidate verdicts + drawdown alert. Configured structures emit one aggregate drawdown/full-exit verdict and suppress every member-leg action.
- `exit_analysis.py` — live hold-vs-complete-exit comparison with execution-time fee curves charged at every fill level. Multi-leg structures print one joint fair/floor/full-depth liquidation row; incomplete depth is unpriced rather than partially actionable.
- `book_walk.py` — pure depth/fee valuation shared by positions, bankroll and marginal-exit reporting. Rejects malformed, negative or nonfinite quantities and out-of-range binary prices before calculating proceeds; preserves zero/partial-depth semantics. This numerical validation does not establish quote identity, freshness or synchronized execution. Portfolio reports explicitly label their depth estimates as indicative.
- `watchlist_monitor.py` — long-term watchlist entry-trigger alerter. CoinGecko + yfinance.
- `index_benchmark.py` — read-only contribution-timed VT/VTI/SPY total-return comparator. Policy pins the $70/$100 capital dates, first-completed-session entry rule, adjusted-close method, idealized execution assumptions and Jan-1 evaluation behavior; malformed, stale or in-progress price data fail closed.
- `source_freeze_check.py` — validated archive comparison. On agi.safe.ai, the default follows the chart's real `dashboard.safe.ai/api/models` data path and compares raw archived/live model rows and HLE scores. The old server-rendered table is not the resolving chart. Malformed/ambiguous API rows fail closed; other sources or non-default regexes explicitly report token-only coverage, not whole-page stasis.
- `uma_status_check.py` — alerts on umaResolutionStatus changes and signed price moves for held positions. Failed, malformed or capped position-inventory reads report unknown coverage, not an empty wallet; cached Gamma identities continue to be checked without inventing disappearance. Reports tracked rows separately from refreshed markets. Caches state in `notes/.uma_status_cache.json`. Built after R-U miss.
- `news_watcher.py` — daemon: 11 RSS feeds, tier-1/2 keyword match, agent-filter precision pass on tier-2, deduped via title-hash 24h window.
- `heartbeat_watch.py` — process-health + session-liveness dead-man switch (journal stale while injects flow → direct Telegram; added after 4 dead-session outages) + stateful news-persistence probe (alert-count vs jsonl-size deltas, 2026-07-04 false-positive fix). Its hourly poll also warns below 512 MiB available on the repository filesystem, escalates below 128 MiB with a separate cooldown, and reports failed probes as unknown. It does not delete files.

### Execution
- `polyclaude_enter.py` — mandatory unified entry helper: exact Gamma slug/question identity → UMA reject → catalyst_check (or --my-p) → structured fee curve → Kelly+ρ sizing → `--execute`. Question lookup uses exact public search plus an exhaustive official-keyset fallback and canonical ID refetch; incomplete/ambiguous coverage aborts. Every BUY enforces the live 15% ticket and 30% configured-cluster/event caps at full fill. Authenticated resting BUYs must map one-to-one to atomic local reservations; each reservation is claimed exactly once before signing, cumulative `totalBought` bridges fill indexing even after later sells, and verified cancels retire only after a grace period plus affirmative terminal status and exhaustive exact-order trade proof. Any legacy cancel or cancel-marker reappearance that cannot preserve those proofs creates a persistent reconciliation block. Unknown correlation identity fails closed, and a wallet lock serializes final reconcile-plus-submit/cancel. Repeated `--bundle-slug` mode re-fetches positions, orders, reservations and chain balances under that lock, includes pending cluster risk, rejects any promise touching one leg, atomically reserves every FOK before order one, and retains ambiguous/completed exposure until indexing proves it. It also validates one negRisk event, equal integer shares, union-level robust EV, live CLOB fees/delay/minimums, pUSD/allowances, on-chain settlement and fee-aware bounded rollback depth.
- `pm_fees.py` — canonical Gamma fee source: prefers structured `feeSchedule` (`rate × (p×(1-p))^exponent`) over stale legacy `takerBaseFee`; all discovery, arb and entry math delegates here.
- `clob_v2.py` — Polymarket CLOB v2 signer (REST + EIP-712, no SDK). BUY atomically consumes the exact pending reservation created by `polyclaude_enter.py` and refuses any reconciliation tombstone; sell/cancel/orders/orderbook/redeem-all remain direct tools. Cancel requires the exact target in the fully paginated pre-cancel inventory, verifies its removal, and marks matching reservations for delayed reconciliation. 10/10 reliability after 32-bit-salt fix; negRisk auto-detection.
- `aave_deposit.py` — supply / withdraw / rate on Aave V3 (Base + Arb + Polygon).
- `across_bridge.py` — cross-chain USDC bridging via Across V3. `--recipient` for cross-wallet, `--token-out` for USDC↔USDC.e.
- `spot_swap.py` — Uniswap V3 exact-input spot swaps. Default routing retries and compares every standard fee tier by token output, surfaces gas evidence and divergent/dust pools, requires an independently derived `--min-out`, and requotes immediately before signing after any approval delay without ever weakening the exact floor already confirmed.
- `ostium_client.py` — Ostium perps client.
- `decisions.py` — append-only decision tracker with calibration-delta + outcome + lesson.
- `ledger_calibration.py` — exact-identity/final-outcome ledger grading; own forecast scores and matched market-baseline scores have separate counts. Missing quotes stay missing, and row counts are not independent-sample counts. Saves write/fsync a same-directory temporary file before atomic replacement, preserving the previous ledger on pre-replacement failures; this is not concurrent-writer locking or a directory-fsync durability guarantee.

### Operator-loop infra
- Scheduled cron/periodic prompts carry a bounded-run contract: finish the due checks and concrete
  follow-up, then end. The operator authorized clearing the indefinite ROI goal on 2026-09-08;
  scheduled prompts must not recreate it. Cron and event daemons handle waiting between runs.
- `check_usage.sh` / `codex_usage.py` — read main-Codex and model-specific quota headroom directly
  through the supported, read-only app-server account RPC. Scheduled prompts run this before
  discretionary research; it never injects `/usage` or consumes a conversational turn merely to
  inspect quota. Keep the primary model for portfolio/risk judgment and use cheaper subagents for
  bounded routine work; quota pressure never overrides safety checks or a thesis-break exit.
- `operator_followup.sh` / `cancel_followup.sh` — one-shot delayed reminder via nohup-sleep + PID
  tracking, only for a concrete time-bound pending task not covered by an existing reminder; never
  an idle research-loop fallback.
- `inject_prompt.sh` — unified ordered-queue path for cron / followup / news_watcher prompts; appends
  the bounded-run and quota-headroom contracts to scheduled in-chat seeds. A quiet previous reply
  does not suppress a newly due check or alert.
- `operator_start.sh` — idempotent starter for the single long-lived operator session.
- `telegram.py` / `telegram_listener.py` — operator interface.

### Emergency
- `emergency_bridge_to_safety.py` / `emergency_exit_ostium.py` / `emergency_exit_polymarket.py` / `emergency_swap_usdc_to_eth.py` — circuit-breakers for catastrophic events. Per `strategy/02_operations.md` 3-layer-sanity-check protocol before invoking.

---

## Repo map

```
PRIMER.md          — original session-launch primer (2026-04-25)
README.md          — this file (entry point)
strategy/          — philosophy, sleeve allocation, operations spec
scripts/           — Python tooling + bash drivers
research/          — per-question audit memos (PM v2 write-path schema, algo-trading audit)
notes/             — chronological journal + weekly P&L + structured news_alerts.jsonl + decisions.json + priors + watchlist
data/              — gitignored: methodology snapshots, market discovery snapshots
logs/              — gitignored: cron + news daemon logs
```

### Key notes/ files
- `journal.md` — chronological narrative log (recent ~2 weeks kept; older history in git)
- `decisions.json` — append-only structured decision tracker (DEC-0001 through DEC-0133 as of this snapshot)
- `backlog.md` — operator-maintained pending-items list, reviewed each cron tick
- `recoup_campaign.md` — 2026-05-09 multi-stage engineering campaign log
- `longterm_watchlist.md` — multi-year IBKR-side candidate doc with verdict table
- `portfolio_kelly_priors.json` — per-position P(win) priors + cluster + ρ_within + canonical `_groups` component topology
- `watchlist_triggers.json` — entry-trigger config for `watchlist_monitor.py` (12 candidates, all `route=ibkr_surface`)
- `primary_sources.md` — curated factual URLs for `world_state_digest.py`
- `pnl_weekly.md` — weekly P&L reports
- `capital_ledger.md` — authoritative record of operator deposits in/out ($170 trading capital + gas). Log every external flow here immediately.
- `catalyst_log.md` / `longterm_log.md` / `world_state_log.md` — append-only outputs from per-script analyses (recent tail kept; history in git)

---

## Recent calibration milestone: R-U loss + recoup campaign (2026-05-09)

**The R-U miss.** DEC-0018 (Russia-Ukraine ceasefire by May 31 NO) opened May 8 at $0.768, scaled in at $0.5208 during Trump's 3-day-ceasefire announcement spike. 25 NO shares / $16.73 cost. Then market entered UMA dispute (umaResolutionStatus="disputed") on May 8/9 after a YES proposal claimed Trump's 3-day ceasefire qualifies under loose criteria language ("regardless of whether ceasefire officially starts afterward"). Market priced UMA-resolves-YES at 99.95%. Position effectively lost.

**Three mistakes documented:**
1. **Scale-in error.** Mark crashed 0.768 → 0.456 on Trump announcement; I read as overreaction and scaled in. Should have read as new info.
2. **Investigation gap.** Position de-indexed from data-api at ~19:45 UTC May 8; I checked on-chain balance + activity but did NOT fetch `gamma-api/markets/{id}` for `umaResolutionStatus`. 18+ hours assuming benign UI lag.
3. **Resolution-criteria interpretation.** Operating under "strict permanent-deal" framing while actual criteria explicitly say "regardless of whether ceasefire officially starts afterward" — a loose bar Trump's announcement satisfies.

**Recoup campaign 2026-05-09 17:00-21:30 UTC.** Operator authorized aggressive engineering. Shipped:
- 4 new trades / scale-ins ($48.02 total deployment)
- 10 tools (kelly_size, portfolio_kelly + constrained, sports_pm_scan + bookie consensus, macro_pm_scan v1, limitless_arb_scan fixes, news_watcher start-guard, drawdown_guard, uma_status_check, polyclaude_enter, polyclaude_status, brownian_bridge_fv)
- 5 cron wirings into daily_checkin.sh
- Theoretical depth: Kelly+ρ → constrained portfolio Kelly → Brownian-bridge hazard-rate pricing

**Recoup math:** Iran cluster +$2.67 unrealized today + $11-15 expected EV from new positions resolving = $14-18 over 22d ≥ R-U $16.73 effective loss. The systematic infrastructure was the actual product — captures alpha autonomously going forward.

---

## Key context for next agent

- **Default to action.** Bounded cost + reversible + unambiguous goal → just execute. Don't ask for permission. (`feedback_default_to_action.md` memory)
- **Stepwise compounding.** Small bounded improvements (one CLI flag, one hook line) compound across every future action. Prefer over multi-hour structural projects unless explicitly authorized.
- **Skeptic+champion pairing.** For trades > $10 OR new strategy class OR sizable structural change: spawn skeptic + champion in parallel. Routine prospecting (single trade < $10): zero-shot evaluation per 2026-05-02 stress-test data.
- **Telegram prefix discipline.** Reply to new authenticated `telegram:` / `reply on telegram:` operator messages via `scripts/telegram.py msg "..."`. Honor the private one-time reader first: no action/reply for `ALREADY_CLAIMED`; only a generic resend request for `EXPIRED`. Non-prefixed = local reply.
- **<1y horizon.** Polyclaude doesn't deploy on multi-year theses. Long-term infra surfaces IBKR-side candidates to operator only.
- **ROI is the product; calibration is a debugging instrument.** Log every material decision via `decisions.py add ...`, then update its outcome/delta/lesson so systematic errors can be removed without Goodharting the project around a score.

## Operator interface

Telegram messages → private durable spool → ordered operator conversation. Telegram replies = action-only:
- Cron tick sends structured summary (MTM Δ, alerts processed, actions taken, next catalyst)
- Material moves outside ticks ping immediately
- Raw RSS pings dropped 2026-05-02 — operator wants decision feed, not news feed
