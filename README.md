# polyclaude

Autonomous agent-driven trading project. Mandate: **maximize return**. Two on-chain sleeves. Fully decentralized — no CEX, no KYC.

**Last updated:** 2026-08-29 (state snapshot updated every cron tick; this header on structural changes)

> **For the next agent:** read this README → `strategy/00_philosophy.md` → **`strategy/01_lessons.md` (the consolidated hard-won lessons — everything compaction loses)** → run `scripts/polyclaude_status.py` for current state. That's a complete onboarding in ~5 minutes. Drill into journal/decisions only when needed for specific calibration questions.

---

## Mandate + horizon constraint

**Goal:** maximize bankroll return on a project-evaluable timeframe.

**Horizon constraint (clarified 2026-05-08):** polyclaude bankroll is locked to **<1y holding horizon per position**. Multi-year plays = operator's personal IBKR sleeve, NOT polyclaude. Reason: project conclusion timeline. Long-term watchlist infra (`scripts/longterm_check.py`, `scripts/world_state_digest.py`, `notes/longterm_watchlist.md`) still runs but routes candidates to operator's IBKR via Telegram, not auto-deploys.

**Evaluation checkpoint (clarified 2026-08-28):** the operator evaluates at the **start of 2027**. Normal Dec-31 markets whose resolution/redemption lands in the first days of January count. Do not force a value-destructive Dec-31 taker exit merely to show cash at midnight. The possible ~$500 top-up is conditional on that evaluation and is not current bankroll or sizing capacity.

**Bankroll:** ~$170 split across PM sleeve (Polygon), crypto sleeve (multi-chain), and Aave reserves.

---

## Current state (snapshot 2026-08-29 03:07 UTC)

**PM sleeve** `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B` (Polygon) — [Polymarket profile](https://polymarket.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) · [Polygonscan](https://polygonscan.com/address/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B) · [DeBank](https://debank.com/profile/0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B)

**Total bankroll $185.02; REALIZED +$4.92 (+2.9%) vs the $170 reference** — realized settled cash is the metric that counts (operator directive 2026-08-18: "it's only truly return when the cash settles on the wallet"). The 15 PM rows cost $165.83 and mark at $169.08 (+$3.26), but executable-depth value is only $161.24 (-$4.59): quote both because thin books overstate the sleeve by $7.84. Six maker sells and zero BUY commitments rest. Book: Dec-31 fades (Trump-out NO, 19 Greenland NO), touchscreen-MacBook NO, four HLE/board-stasis NO lottery legs, the matched Metamask FDV structure, the Aug-31 Iran-Oman ticket, the Sep-20 Duma 295–339 range, and DEC-0085's short-dated Google Maps catalyst. DEC-0089/0090 initially sold 5 low-edge Greenland NO and bought 49 next-Gemini-Pro-debut ≥40 NO at 0.09/0.10. After the Aug-29 source/criteria/book revalidation, DEC-0096/0097 sold another 5 Greenland NO at 0.93 and added exactly 50 debut NO at 0.09 FAK. The ticket is now 99 NO for $9.20 notional plus $0.33372 fees = $9.53372 gross; central/stressed p_no remain 0.65/0.50. The direct falsifier is a new board row—already-released Gemini 3.1 Pro scores 46.44 on Scale, and Google says 3.5 Pro is coming soon—so the leg is monitored as part of one highly correlated HLE cluster, not independent diversification. The full configured AI cluster is $54.53332 against an execution-time $55.47830 cap, leaving only $0.94498. Lake remains 40.95563 YES at about 0.293 raw entry; the Aug-29 direct US-region probe still shows Lake Ontario, lowering central/stressed fair to 0.55/0.45, both above executable exit. The Duma set remains 20 equal YES shares across 295–309 / 310–324 / 325–339 and must never be traded leg-by-leg. The Iran-Oman agreement prior is 0.08 after the final official-source recheck; its 31 YES shares remain a no-add hold. Money-math suite: 123 checks plus a 19-case mutation harness, pre-commit enforced. Short-dated ledger N=51.

**Operating model (operator directive 2026-07-15): continuous research loop** — research until a profitable opportunity is found, report, invest, repeat; 24/7 `opportunity_watch.py` daemon between ticks. Five population edges falsified this month at $0 deployed (short-dated fade buckets N=836, new-listing mispricing N=833, UMA dispute-window N=2,246, cross-event implication arbs 4,575 pairs) — every falsification shipped a permanent gate upgrade (fee-aware EV, dispute priors, sibling-market routing). Surviving edge = case-by-case catalyst-gated instance mispricing (doctrine §3.1). Ostium's 2026-07-15 $18M oracle exploit: zero exposure (skeptic+champion had parked the planned OLP deposit — DEC-0040). Any Iran/war-adjacent entry must re-pull live conflict state; the only current exposure is the deliberately small, literal-criteria Iran-Oman announcement ticket described above. Run `scripts/bankroll.py` + `scripts/polyclaude_status.py` for live figures.

Run `scripts/polyclaude_status.py` for live numbers (positions, hurdle scan, watchlist, UMA, Kelly portfolio constrained, news alerts).

**Crypto sleeve** `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` (multi-chain) — [DeBank](https://debank.com/profile/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) · [Arbiscan](https://arbiscan.io/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) (Ostium + Aave-Arb) · [Basescan](https://basescan.org/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) (Aave-Base) · [Polygonscan](https://polygonscan.com/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6) · [Optimism Etherscan](https://optimistic.etherscan.io/address/0x83dADaC202cd1276E985703f90d39EE31F3D3eE6)

Note: Ostium has no public per-address trader profile (wallet-connect SPA). DeBank aggregates Ostium positions + Aave aUSDC + cross-chain balances; Arbiscan shows the raw on-chain trace incl. each Ostium open/close.

Ostium: 0 open perps (SPX / NDX / XAU all TP-closed May-2026; planned OLP deposit parked pre-exploit — zero exposure through both exploit reports, $18M→$24M revised). Crypto sleeve has ~$7.87 aUSDC Aave-Arb plus small stable/gas balances; capital is deliberately concentrated in the PM sleeve, where $0.088265 pUSD remains after DEC-0096. Status scripts read aTokens/pUSD directly, so idle capital is always visible. Run `scripts/crypto_status.py` + `scripts/aave_deposit.py rate` for live figures.

**Long-term watchlist** (28 machine-monitored price gates; equities and multi-year ideas surface to the operator, while only explicitly <1y EVM catalysts may route back to polyclaude): `notes/longterm_watchlist.md` + `notes/watchlist_triggers.json`. Auto-monitored via `scripts/watchlist_monitor.py`; every hit is a re-underwriting trigger, never an automatic buy.

---

## Architecture (3 autonomy layers)

1. **Reactive** — `scripts/news_watcher.py` polls 11 RSS feeds every 5 min; tier-1 events auto-fire `daily_checkin.sh`. Tier-2 events queue to `notes/news_alerts.jsonl`. Title-hash dedup + start-guard against duplicate daemons.

2. **Scheduled** — cron at `02:00 + 14:00 UTC` runs `scripts/daily_checkin.sh`. It uses the operator's durable conversation queue when available and a fresh, fully onboarded headless fallback when the operator is down.

   - Hourly `scripts/arb_cron.sh` runs `scripts/limitless_arb_scan.py`.
   - Light `inject_prompt.sh "Periodic check..."` at 06/10/18/22 UTC.
   - Sunday 16:00 UTC: weekly long-term review (rotating 2-3 of 9 domains via `world_state_digest.py`).

3. **Interactive** — `scripts/telegram_listener.py` long-polls Telegram; authorized operator messages enter the same ordered conversation queue as local follow-ups. Telegram replies are action-only by convention (cron tick sends structured summary; material moves outside ticks ping immediately).

   - Telegram-prefixed messages (`telegram:`, `reply on telegram:`) require Telegram reply via `scripts/telegram.py msg "..."`.

---

## Tool inventory

### Discovery + scanning
- `discover_markets.py` — pulls active Polymarket markets, filters by the live Aave-Polygon hurdle APY + 3d horizon floor + spread/liq quality. Bond-like-fade lens.
- `sports_pm_scan.py` — sports markets in 48h window with mid-market lens (BOND_LIKE_FADE_NO/YES, MID_50_50, STRONG_FAVORITE). `--with-consensus` uses a scoped fast research worker for bookie-odds deltas; opt-in `--with-kalshi` attaches strictly matched, unauthenticated public-book evidence through `kalshi_consensus.py` with no execution path.
- `event_monotonicity_scan.py` — date- and threshold-ladder inconsistency scanner. Date comparisons require identical child propositions, payout-rule templates, explicit semantic deadlines and consistent Gamma metadata before live-book validation; event membership alone never establishes a hedge.
- `polymarket_consistency_scan.py` — neg-risk basket scanner over an explicit non-sports, evaluation-horizon, top-volume keyset slice (5,000 open markets by default, completing the boundary event). Coverage, live-book budgets and every skipped leg are published explicitly; an incomplete clean result is never described as an exchange-wide zero. Positive sequential-book observations require refreshed Gamma/CLOB identity, fees and full minimum-size depth, but remain provisional revalidation leads—not execution claims.
- `macro_pm_scan.py` — Polymarket FOMC/CPI/macro markets in 60d window. **v1 LIMITATION: --with-consensus is unreliable because CME FedWatch is JS-rendered. Use --no-consensus.**
- `world_state_digest.py` — bare-fact synthesis from `notes/primary_sources.md` (~46 curated factual URLs, 9 domains). Distills "what's underpriced given THESE facts." Sunday cron.
- `limitless_arb_scan.py` — cross-venue arb scanner Polymarket vs Limitless. Its Polymarket fuzzy-match universe is an official-keyset, volume-ranked 3,000-market bounded slice and is labeled partial unless the cursor exhausts; request/schema/identity failures abort without publishing. Proper-noun-overlap + Jaccard 0.55 false-positive guards still require resolution-language review.

### Vetting + sizing
- `catalyst_check.py` — for event-driven binary Polymarket markets. Uses a scoped web-research worker plus auto-fetched resolution criteria. Outputs central P(YES) with multiplicative breakdown for conjunction questions.
- `longterm_check.py` — multi-year horizon thesis-check. 4D framework (cyclical / secular / catalyst / margin). Used for IBKR-side candidates.
- `portfolio_kelly.py` — full-book Kelly audit (per-position sizing now inline in `polyclaude_enter.py`). `--constrained` reserves each configured multi-leg structure once before scaling ordinary legs. Group rows expose joint state-priced fair/floor values and complete fee-aware component asks at the exchange's executable minimum size; member legs never emit add/trim recommendations.
- `position_groups.py` — pure fail-closed topology engine for multi-leg economic positions. Exact slug/side/token/event/deadline/quantity validation, state-payoff valuation, aggregate drawdown, per-level-fee full exits, and component-level adds. Canonical topology is `_groups` in `portfolio_kelly_priors.json`; malformed or partial structures remain protected from leg-level fallback.
- `brownian_bridge_fv.py` — first-principles hazard-rate pricing for bond-like fades. fair_mark(t) = p^(1-t/T). Surfaces TRIM (mark > fair) and SCALE_UP (mark < fair) signals.

### Monitoring + safety
- `polyclaude_status.py` — single-command aggregator: positions + hurdle + watchlist + UMA + Kelly + Brownian-bridge + news. Operator's go-to state-check.
- `check_marginal_apy.py` — EXPECTED-edge scan: (p/M−1)×365/d vs honest priors from portfolio_kelly_priors.json (fixed 2026-07-02 from win-assumed carry math), executable-bid NEGATIVE_EDGE/close-candidate verdicts + drawdown alert. Configured structures emit one aggregate drawdown/full-exit verdict and suppress every member-leg action.
- `exit_analysis.py` — live hold-vs-complete-exit comparison with execution-time fee curves charged at every fill level. Multi-leg structures print one joint fair/floor/full-depth liquidation row; incomplete depth is unpriced rather than partially actionable.
- `watchlist_monitor.py` — long-term watchlist entry-trigger alerter. CoinGecko + yfinance.
- `uma_status_check.py` — alerts on umaResolutionStatus changes for held positions. Caches state in `notes/.uma_status_cache.json`. Built after R-U miss.
- `news_watcher.py` — daemon: 11 RSS feeds, tier-1/2 keyword match, agent-filter precision pass on tier-2, deduped via title-hash 24h window.
- `heartbeat_watch.py` — process-health + session-liveness dead-man switch (journal stale while injects flow → direct Telegram; added after 4 dead-session outages) + stateful news-persistence probe (alert-count vs jsonl-size deltas, 2026-07-04 false-positive fix).

### Execution
- `polyclaude_enter.py` — mandatory unified entry helper: Gamma lookup → UMA reject → catalyst_check (or --my-p) → structured fee curve → Kelly+ρ sizing → `--execute`. Every BUY enforces the live 15% ticket and 30% configured-cluster/event caps at full fill. Authenticated resting BUYs must map one-to-one to atomic local reservations; each reservation is claimed exactly once before signing, cumulative `totalBought` bridges fill indexing even after later sells, and verified cancels retire only after a grace period plus affirmative terminal status and exhaustive exact-order trade proof. Any legacy cancel or cancel-marker reappearance that cannot preserve those proofs creates a persistent reconciliation block. Unknown correlation identity fails closed, and a wallet lock serializes final reconcile-plus-submit/cancel. Repeated `--bundle-slug` mode re-fetches positions, orders, reservations and chain balances under that lock, includes pending cluster risk, rejects any promise touching one leg, atomically reserves every FOK before order one, and retains ambiguous/completed exposure until indexing proves it. It also validates one negRisk event, equal integer shares, union-level robust EV, live CLOB fees/delay/minimums, pUSD/allowances, on-chain settlement and fee-aware bounded rollback depth.
- `pm_fees.py` — canonical Gamma fee source: prefers structured `feeSchedule` (`rate × (p×(1-p))^exponent`) over stale legacy `takerBaseFee`; all discovery, arb and entry math delegates here.
- `clob_v2.py` — Polymarket CLOB v2 signer (REST + EIP-712, no SDK). BUY atomically consumes the exact pending reservation created by `polyclaude_enter.py` and refuses any reconciliation tombstone; sell/cancel/orders/orderbook/redeem-all remain direct tools. Cancel requires the exact target in the fully paginated pre-cancel inventory, verifies its removal, and marks matching reservations for delayed reconciliation. 10/10 reliability after 32-bit-salt fix; negRisk auto-detection.
- `aave_deposit.py` — supply / withdraw / rate on Aave V3 (Base + Arb + Polygon).
- `across_bridge.py` — cross-chain USDC bridging via Across V3. `--recipient` for cross-wallet, `--token-out` for USDC↔USDC.e.
- `spot_swap.py` — Uniswap V3 exact-input spot swaps. Default routing retries and compares every standard fee tier by token output, surfaces gas evidence and divergent/dust pools, requires an independently derived `--min-out`, and requotes immediately before signing after any approval delay without ever weakening the exact floor already confirmed.
- `ostium_client.py` — Ostium perps client.
- `decisions.py` — append-only decision tracker with calibration-delta + outcome + lesson.

### Operator-loop infra
- Scheduled cron/periodic prompts carry a durable Codex ROI-goal contract: continuation turns remain
  active until the user manually cancels the goal. This replaces the provider-specific Claude
  `UserPromptSubmit` hook lost in the 2026-08-26 runtime migration.
- `operator_followup.sh` / `cancel_followup.sh` — legacy one-shot delayed continuation fallback via
  nohup-sleep + PID tracking for runtimes without durable-goal support.
- `inject_prompt.sh` — unified ordered-queue path for cron / followup / news_watcher prompts; appends
  the durable-goal contract to scheduled in-chat seeds and never auto-cancels merely because the last
  reply was idle.
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
- `decisions.json` — append-only structured decision tracker (DEC-0001 through DEC-0099 as of this snapshot)
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
- **Telegram prefix discipline.** Any inbound message with `telegram:` / `reply on telegram:` MUST respond via `scripts/telegram.py msg "..."`. Non-prefixed = local reply.
- **<1y horizon.** Polyclaude doesn't deploy on multi-year theses. Long-term infra surfaces IBKR-side candidates to operator only.
- **Calibration data is the actual product.** Every decision via `decisions.py add ...` with thesis + confidence + prediction. Update on resolution with outcome + calibration-delta + lesson.

## Operator interface

Telegram messages → private durable spool → ordered operator conversation. Telegram replies = action-only:
- Cron tick sends structured summary (MTM Δ, alerts processed, actions taken, next catalyst)
- Material moves outside ticks ping immediately
- Raw RSS pings dropped 2026-05-02 — operator wants decision feed, not news feed
