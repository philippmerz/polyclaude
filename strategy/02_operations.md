# Operations

Single canonical home for the project's operational infrastructure. Other docs reference this file rather than restate it.

## Cron — autonomous check-in driver

- **Schedule (UTC):** `0 2 * * *` and `0 14 * * *` — symmetric 12h spacing. The 14:00 anchor catches the US-morning news cycle; 02:00 fills the otherwise-quiet window and catches Asia-morning + late-US news.
- **Driver:** `scripts/daily_checkin.sh`. Resolves repo root from `${BASH_SOURCE[0]}`, sources `~/.polyclaude/env` for secret paths, forks the operator's interactive Claude session via `claude -p --resume <id> --fork-session --model opus --effort max --permission-mode acceptEdits`.
- **Per-tick token cap:** ~100K (the prompt itself caps).
- **Logs:** `polyclaude/logs/cron/checkin_<UTC ts>.log` (gitignored, auto-pruned at 30d).
- **What each tick does:** load context (memory, journal tail, strategy, questions), mark portfolio + wallet state via `scripts/positions.py` and `scripts/wallet_status.py`, scan WebSearch for active-position catalysts, decide hold/adjust/add/close, journal it, write a weekly report if ≥7d since last, commit + push (audit diff for secrets first), Telegram-alert if anything material moved.

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
