# Operations

Single canonical home for the project's operational infrastructure. Other docs reference this file rather than restate it.

## Cron — autonomous check-in driver

- **Schedule (UTC):** `0 2 * * *` and `0 14 * * *` — symmetric 12h spacing. The 14:00 anchor catches the US-morning news cycle; 02:00 fills the otherwise-quiet window and catches Asia-morning + late-US news.
- **Driver:** `scripts/daily_checkin.sh`. Resolves repo root from `${BASH_SOURCE[0]}`, sources `~/.polyclaude/env` for secret paths, forks the operator's interactive Claude session via `claude -p --resume <id> --fork-session --model opus --effort max --permission-mode acceptEdits`.
- **Per-tick token cap:** ~100K (the prompt itself caps).
- **Logs:** `polyclaude/logs/cron/checkin_<UTC ts>.log` (gitignored, auto-pruned at 30d).
- **What each tick does:** load context (memory, journal tail, strategy), mark portfolio + wallet state via `scripts/positions.py` and `scripts/wallet_status.py`, scan WebSearch for active-position catalysts, decide hold/adjust/add/close, journal it, write a weekly report if ≥7d since last, commit + push (audit diff for secrets first), Telegram-alert if anything material moved.

## News watcher — 24/7 reactive layer

- **Daemon:** `scripts/news_watcher.py` (subcommands `start | status | stop | once`). Restarts on reboot via `@reboot` crontab.
- **Feeds:** 11 RSS sources (BBC World/Politics/ME, Al Jazeera, NPR World/Politics, Guardian World/US, France24, CBS, Fox World). Polled every 300s.
- **Config:** `scripts/news_watcher_config.json` — feeds + tiered keyword lists, editable; daemon re-reads each poll.
- **Tier 1** (book-resolving): Trump dies / 25A-removed, Iranian regime falls / Khamenei dies, US-Iran permanent peace deal, Pahlavi takes power, aliens confirmed, Jesus returns, Iran missile-strikes a European city. → `[URGENT]` Telegram **and** auto-spawns `daily_checkin.sh` for max-effort response. 30-min rate limit between auto-fires.
- **Tier 2** (notable): Trump health/security, Hormuz blockade ops, US-Iran talks state, Khamenei health, UAP/AARO reports, Eurovision rehearsals, Ohio primary, La Liga title race. → `[NEWS]` Telegram only. Per-keyword 30-min cooldown.

## Telegram bridge

- **Bot:** `@philipp_claudBot`.
- **Outbound:** `scripts/telegram.py {setup,msg,file,md}`.
- **Inbound:** `scripts/telegram_listener.py start` long-polls and pipes incoming text into the operator's interactive Claude tmux pane via `tmux send-keys -l <text>` then Enter. Detects busy pane via Braille-spinner heuristic in `pane_title`; advances the update cursor only on successful inject so a missed message is retried next poll.

## Secrets — path-leak hygiene

- **Path resolution:** scripts read all secret/state file locations from env vars resolved through `scripts/_paths.py`, which auto-loads `~/.polyclaude/env` (gitignored, 0o600, outside the repo) on import. Public source contains env-var names only — never absolute filesystem paths.
- **Stored files** (all in the gitignored secrets directory, mode 0o600): two wallet keyfiles (Polymarket sleeve + crypto sleeve), Polymarket API creds, Telegram bot token, Polymarket session id, news-watcher state.
- **Adding a new secret:** declare it in `~/.polyclaude/env`, then read via `_paths.path("VAR_NAME")` in script. Never hardcode a path.

## Wallets

| Sleeve | Address | Funded | Strategy spec |
|---|---|---|---|
| Polymarket | `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B` | ~$70 USDC.e on Polygon | Two-horizon split per `strategy/01_horizon_split.md`; positions in `research/_long_initial.md` + `research/_short_initial.md` |
| Crypto | `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` | (pending operator $50 fund) | Default split per `research/_crypto_landscape_2026-04-27.md` §7 |

Both wallets resolved via the same `_paths.py` mechanism (`POLYCLAUDE_WALLET`, `POLYCLAUDE_WALLET_CRYPTO`).

## Daemons currently running

- `scripts/news_watcher.py start` — PID in `~/.polyclaude_news_watcher.pid`
- `scripts/telegram_listener.py start` — PID in `~/.polyclaude_telegram_listener.pid`
- Both restart on reboot via `@reboot` crontab entries.

## README.md as living portfolio dashboard

Each cron tick (and any other meaningful state change) refreshes `README.md` at the repo root with: current portfolio across both sleeves, MTM, recent decisions, links to the canonical strategy/research docs. GitHub renders this on the front of the repo so the operator can see project state at a glance without reading the journal. Treat it as a public face — concise, link-heavy, no operational secrets.

## Operator-blocking questions

Surface via Telegram (`scripts/telegram.py msg "..."`) rather than a tracked file. The previous `questions.md` was retired 2026-04-29 in favor of the live channel — operator wants questions to interrupt them in real time, not pile up in a file.

## Heartbeat watchdog

`scripts/heartbeat_watch.py` runs as its own daemon (PID file `~/.polyclaude_heartbeat.pid`, restarts on reboot via `@reboot` crontab). Hourly probe — checks news_watcher and telegram_listener PIDs are alive, news_watcher's state file is fresh (< 30 min), and no `claude -p` cron fork has been running > 60 min. Telegram-alerts on anomaly with a 1-hour per-anomaly cooldown. Was added 2026-04-29 after a 3-day deadlocked cron tick from the prior week; this layer would have caught it within an hour.

## Emergency-exit protocol

When a Tier-1 news_watcher alert indicates a real exploit / depeg / chain halt affecting our positions, the cron tick that gets auto-fired runs a 3-layer sanity check, then invokes a pre-built `scripts/emergency_exit_*.py` script. The scripts are dumb executors; the *intelligence* (deciding whether to call them) is in the cron tick.

### Three-layer sanity check (all must pass before invoking any emergency script)

1. **Multi-source corroboration.** WebFetch ≥ 3 independent crypto-news sources. Require ≥ 2 to confirm the same event. If only 1 source mentions it, especially a low-reputation feed → HOLD + Telegram operator. (This alone catches the substring-regex false positive that hit on 2026-04-29 — only one feed had the keyword, others would not corroborate.)
2. **Market-reaction consistency.** The market should already be reacting if the event is real:
   - *USDC/USDT depeg*: actual price on Coingecko's multi-exchange aggregate. Must be < $0.98 to confirm.
   - *Ostium / Across hack*: TVL via DefiLlama or directly from the contract balance. Sudden drawdown > 10% in last 1h = real signal.
   - *Polymarket halt*: try fetching a market via gamma-api. If responsive, protocol is operational.
   - *Sequencer halt*: issue an `eth_chainId` RPC to that chain. If responsive, no halt.
3. **On-chain ground truth.** Read the at-risk contract's relevant balance directly. Authoritative, overrides news source claims. Blockchain state is what an attacker can't fake.

**Decision tree:**
- All 3 PASS → invoke the script. Telegram an "executed emergency exit" notice.
- Any FAIL → abort, Telegram operator with the discrepancy. Wait 10 min for operator decision; default to inaction on timeout.
- Layers 1+2 PASS but 3 uncertain (RPC slow/unreachable) → Telegram with all data, wait 5 min for operator response, proceed if no objection.

### Script catalog

| Script | Trigger keywords (Tier-1) | What it does |
|---|---|---|
| `emergency_exit_ostium.py` | `ostium hack`, `ostium exploit`, `ostium drained`, `ostium rugged` | Reads all open Ostium positions via SDK, market-closes 100% each, aborts after 3 retries on any single fail. |
| `emergency_exit_polymarket.py` | `polymarket halted`, `polymarket banned`, `polymarket sec lawsuit`, `polymarket frozen` | Cancels open orders, places SELL at best_bid for every position, 10% slippage cap. |
| `emergency_bridge_to_safety.py` | `arbitrum sequencer halt`, `base sequencer halt`, `arbitrum exploit`, `base exploit` | Reads full USDC balance on at-risk chain, bridges to Polygon (or specified safe chain) via Across. |
| `emergency_swap_usdc_to_eth.py` | `usdc depeg`, `usdc breaks peg`, `tether depeg` | Swaps full USDC balance to WETH via Uniswap V3 on the chain, 5% slippage cap. |

The operator can also invoke any of these manually via Telegram (the listener pipes the message into the live tmux pane and I execute on their behalf — no sanity check, operator override is trusted).

### What NOT to do under panic

- Don't write new emergency code under time pressure — the scripts are pre-built for exactly this. If the situation requires something not pre-built, Telegram the operator and let them decide.
- Don't escalate sizing (e.g., "since this is bad, sell *more* of the safe sleeve too"). Each script handles its scoped at-risk surface; cross-contamination of scope is a recipe for loss.
- Don't panic-bridge through a bridge that's the at-risk component (e.g., if Across is exploited, do not use `emergency_bridge_to_safety.py` since it uses Across).
