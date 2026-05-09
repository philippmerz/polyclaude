# polyclaude

Autonomous Claude-driven trading project. Mandate: **maximize return**. Two on-chain sleeves. Fully decentralized — no CEX, no KYC.

**Last updated:** 2026-05-09 ~21:30 UTC

> **For the next agent:** read this README → `strategy/00_philosophy.md` → run `scripts/polyclaude_status.py` for current state. That's a complete onboarding in ~5 minutes. Drill into journal/decisions only when needed for specific calibration questions.

---

## Mandate + horizon constraint

**Goal:** maximize bankroll return on a project-evaluable timeframe.

**Horizon constraint (clarified 2026-05-08):** polyclaude bankroll is locked to **<1y holding horizon per position**. Multi-year plays = operator's personal IBKR sleeve, NOT polyclaude. Reason: project conclusion timeline. Long-term watchlist infra (`scripts/longterm_check.py`, `scripts/world_state_digest.py`, `notes/longterm_watchlist.md`) still runs but routes candidates to operator's IBKR via Telegram, not auto-deploys.

**Bankroll:** ~$170 split across PM sleeve (Polygon), crypto sleeve (multi-chain), and Aave reserves.

---

## Current state (snapshot 2026-05-09 21:30 UTC)

**PM sleeve** `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B` (Polygon)

10 positions visible to data-api: cost $116.79, MTM $119.46, +$2.67 / +2.28% unrealized. R-U position de-indexed from data-api but on-chain at 25 NO shares — UMA dispute resolution underway, expected loss ~$16.73 (effectively lost capital). All 10 visible positions clear marginal-APY hurdle.

Iran cluster (May-11/15/31 + regime-fall + Pahlavi) is the dominant book by exposure.

Run `scripts/polyclaude_status.py` for live numbers (positions, hurdle scan, watchlist, UMA, Kelly portfolio constrained, news alerts).

**Crypto sleeve** `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` (multi-chain)

Aave V3 USDC reserves: ~$5 Base + $0 Arb (drained $25 to PM sleeve 2026-05-09). Ostium 3 perp positions ($14.67 collateral). Dust on Optimism.

**Long-term watchlist** (12 candidates, all `route=ibkr_surface` per <1y constraint): `notes/longterm_watchlist.md`. Auto-monitored via `scripts/watchlist_monitor.py` with entry-trigger price alerts.

---

## Architecture (3 autonomy layers)

1. **Reactive** — `scripts/news_watcher.py` polls 11 RSS feeds every 5 min; tier-1 events auto-fire `daily_checkin.sh`. Tier-2 events queue to `notes/news_alerts.jsonl`. Title-hash dedup + start-guard against duplicate daemons.

2. **Scheduled** — cron at `02:00 + 14:00 UTC` runs `scripts/daily_checkin.sh`. Bash-level pre-check dispatches to operator tmux pane via `tmux send-keys` if alive; falls back to forked `claude -p --resume <session> --fork-session` if pane is down.

   - Hourly `scripts/arb_cron.sh` runs `scripts/limitless_arb_scan.py`.
   - Light `inject_prompt.sh "Periodic check..."` at 06/10/18/22 UTC.
   - Sunday 16:00 UTC: weekly long-term review (rotating 2-3 of 9 domains via `world_state_digest.py`).

3. **Interactive** — `scripts/telegram_listener.py` long-polls Telegram; operator messages land in operator tmux pane. Telegram replies are action-only by convention (cron tick sends structured summary; material moves outside ticks ping immediately).

   - Telegram-prefixed messages (`telegram:`, `reply on telegram:`) require Telegram reply via `scripts/telegram.py msg "..."`.

---

## Tool inventory

### Discovery + scanning
- `discover_markets.py` — pulls active Polymarket markets, filters by hurdle APY (3.4% Aave Base) + 3d horizon floor + spread/liq quality. Bond-like-fade lens.
- `sports_pm_scan.py` — sports markets in 48h window with mid-market lens (BOND_LIKE_FADE_NO/YES, MID_50_50, STRONG_FAVORITE). `--with-consensus` fetches bookie odds via haiku for delta computation.
- `macro_pm_scan.py` — Polymarket FOMC/CPI/macro markets in 60d window. **v1 LIMITATION: --with-consensus is unreliable (CME FedWatch is JS-rendered → haiku hallucinates). Use --no-consensus.**
- `world_state_digest.py` — bare-fact synthesis from `notes/primary_sources.md` (~46 curated factual URLs, 9 domains). Distills "what's underpriced given THESE facts." Sunday cron.
- `limitless_arb_scan.py` — cross-venue arb scanner Polymarket vs Limitless. Proper-noun-overlap + Jaccard 0.55 false-positive guards. Mostly surfaces subjective-resolution arbs (token launches by date).

### Vetting + sizing
- `catalyst_check.py` — for event-driven binary Polymarket markets. Spawns `claude -p haiku` with WebSearch + WebFetch + auto-fetched resolution criteria. Outputs central P(YES) with multiplicative breakdown for conjunction questions.
- `longterm_check.py` — multi-year horizon thesis-check. 4D framework (cyclical / secular / catalyst / margin). Used for IBKR-side candidates.
- `kelly_size.py` — per-position Kelly + ρ-adjusted + sensitivity to ±5%/±10% p-misestimate.
- `portfolio_kelly.py` — full-book Kelly audit. `--constrained` flag scales by (bankroll/sum_kelly) when total > 100% bankroll. Surfaces deficit ranking.
- `brownian_bridge_fv.py` — first-principles hazard-rate pricing for bond-like fades. fair_mark(t) = p^(1-t/T). Surfaces TRIM (mark > fair) and SCALE_UP (mark < fair) signals.

### Monitoring + safety
- `polyclaude_status.py` — single-command aggregator: positions + hurdle + watchlist + UMA + Kelly + Brownian-bridge + news. Operator's go-to state-check.
- `check_marginal_apy.py` — hurdle scan + drawdown alert (with de-indexed-market guard at mark ≤ 0.005).
- `watchlist_monitor.py` — long-term watchlist entry-trigger alerter. CoinGecko + yfinance.
- `uma_status_check.py` — alerts on umaResolutionStatus changes for held positions. Caches state in `notes/.uma_status_cache.json`. Built after R-U miss.
- `news_watcher.py` — daemon: 11 RSS feeds, tier-1/2 keyword match, agent-filter precision pass on tier-2, deduped via title-hash 24h window.
- `heartbeat_watch.py` — process-health monitor.

### Execution
- `polyclaude_enter.py` — unified entry helper: gamma lookup → UMA reject → catalyst_check (or --my-p) → Kelly+ρ sizing → `--execute` → clob_v2.py buy with clean integer-share math.
- `clob_v2.py` — Polymarket CLOB v2 signer (REST + EIP-712, no SDK). buy/sell/cancel/orders/orderbook/redeem-all. 10/10 reliability after 32-bit-salt fix. negRisk auto-detection.
- `aave_deposit.py` — supply / withdraw / rate on Aave V3 (Base + Arb + Polygon).
- `across_bridge.py` — cross-chain USDC bridging via Across V3. `--recipient` for cross-wallet, `--token-out` for USDC↔USDC.e.
- `ostium_client.py` — Ostium perps client.
- `decisions.py` — append-only decision tracker with calibration-delta + outcome + lesson.

### Operator-loop infra
- `operator_followup.sh` / `cancel_followup.sh` — self-injected continuation prompts via nohup-sleep + PID tracking.
- `inject_prompt.sh` — unified tmux send-keys path for cron / followup / news_watcher prompts to operator pane.
- `~/.claude/hooks/inject_context_and_schedule.sh` — UserPromptSubmit hook: injects current UTC + queues 20-min self-followup.
- `telegram.py` / `telegram_listener.py` — operator interface.

### Emergency
- `emergency_bridge_to_safety.py` / `emergency_exit_ostium.py` / `emergency_exit_polymarket.py` / `emergency_swap_usdc_to_eth.py` — circuit-breakers for catastrophic events. Per `strategy/02_operations.md` 3-layer-sanity-check protocol before invoking.

### Scaffolding (deprecated)
- `prompter_start.sh` / `prompter_send.sh` — prompter-architecture launcher; deprecated 2026-05-08, kept for recoverability.

---

## Repo map

```
PRIMER.md          — original session-launch primer (2026-04-25)
README.md          — this file (entry point)
strategy/          — philosophy, sleeve allocation, operations spec, deprecated prompter role
scripts/           — Python tooling + bash drivers (50 files)
research/          — per-question audit memos (yield, algo trading, crypto landscape, initial portfolios, PM v2 schema)
notes/             — chronological journal + weekly P&L + structured news_alerts.jsonl + decisions.json + priors + watchlist
data/              — gitignored: methodology snapshots, market discovery snapshots
logs/              — gitignored: cron + news daemon logs
```

### Key notes/ files
- `journal.md` — chronological narrative log (~2000 lines as of 2026-05-09; archive split monthly)
- `decisions.json` — append-only structured decision tracker (DEC-0001 through DEC-0022 as of session)
- `backlog.md` — operator-maintained pending-items list, reviewed each cron tick
- `recoup_campaign.md` — 2026-05-09 multi-stage engineering campaign log
- `longterm_watchlist.md` — multi-year IBKR-side candidate doc with verdict table
- `portfolio_kelly_priors.json` — per-position P(win) priors + cluster + ρ_within
- `watchlist_triggers.json` — entry-trigger config for `watchlist_monitor.py` (12 candidates, all `route=ibkr_surface`)
- `primary_sources.md` — curated factual URLs for `world_state_digest.py`
- `pnl_weekly.md` — weekly P&L reports
- `catalyst_log.md` / `longterm_log.md` / `world_state_log.md` — append-only outputs from per-script analyses
- `prompter_primer.md` — DEPRECATED architecture, kept for recoverability

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

Telegram messages → `telegram_listener.py` → operator tmux pane. Telegram replies = action-only:
- Cron tick sends structured summary (MTM Δ, alerts processed, actions taken, next catalyst)
- Material moves outside ticks ping immediately
- Raw RSS pings dropped 2026-05-02 — operator wants decision feed, not news feed
