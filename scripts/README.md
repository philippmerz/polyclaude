# scripts/

Quick map for any Claude (or human) reading the repo cold. For deeper context: [`../README.md`](../README.md), [`../strategy/02_operations.md`](../strategy/02_operations.md), [`../notes/journal.md`](../notes/journal.md).

## Daemons (long-running; restarted on reboot via `@reboot` crontab)

- `news_watcher.py` — polls 11 RSS feeds, fires Tier-1 alerts (auto-spawns a `daily_checkin.sh` cron tick) and Tier-2 alerts (agent-filtered via `claude -p haiku` then Telegram). Config: `news_watcher_config.json`.
- `telegram_listener.py` — long-polls Telegram, pipes operator messages into the live tmux pane via `tmux send-keys`.
- `heartbeat_watch.py` — hourly probe; alerts if any daemon stalls > 30 min or any `claude -p` cron fork runs > 60 min.

## Scheduled (crontab)

- `daily_checkin.sh` — main cron tick at `02:00` + `14:00` UTC. Forks the operator's interactive Claude session (`--resume <id> --fork-session`) and runs the standard portfolio + prospecting + journal flow.
- `arb_cron.sh` — hourly arb scan + executor at `30 * * * *`.

## Sleeve clients (libraries imported by other scripts)

- `polyclaude_client.py` — Polymarket CLOB wrapper. EOA signing (`signature_type=0`). `place_limit_buy/sell`, `orderbook`, allowance setup, position queries.
- `ostium_client.py` — thin CLI on `ostium-python-sdk`. Subcommands: `status`, `pairs`, `open`, `close`. Used for Arbitrum RWA-perp positions.
- `_paths.py` — secret/state file resolution from `~/.polyclaude/env` (canonical), plus `~/secrets/limitless_creds.json`. Provides `path()` and `scrub()` + `install_scrubbing_excepthook()` so secrets never reach logs.

## Decision-quality tracking

- `decisions.py` — record/list/update/summarize structured decision entries. Stored in `notes/decisions.json`. Foundation for evaluating reasoning quality at scale; spec in `strategy/00_philosophy.md`.

## Status / inspection (read-only)

- `wallet_status.py` — Polymarket-sleeve MATIC + USDC balance on Polygon.
- `positions.py` — Polymarket open positions with mark-to-market P&L.
- `crypto_status.py` — multi-chain balance reader for either sleeve. Subcommand: `crypto` (default) or `polymarket`.
- `discover_markets.py` — paginated Polymarket gamma-api scan. Snapshots into `data/snapshots/`.

## On-chain operations

- `across_bridge.py` — Across V3 bridge for USDC and native ETH across Arbitrum / Base / Polygon / Optimism.
- `aave_deposit.py` — Aave V3 `supply` / `withdraw` / `rate` across the same chains.
- `limitless_arb_scan.py` — paginates Limitless `isPolyArbitrage:true` markets, fuzzy-matches Polymarket counterparts, agent-verifies resolution-language equivalence (claude -p haiku), tags Chainlink-Data-Stream-backed markets as mechanical resolution. Output: `logs/limitless_arb_<ts>.md` + `logs/limitless_arb_latest.json`.
- `limitless_arb_executor.py` — live-quote inspector. Reads scan output, recomputes net edge after real orderbook slippage. **Does not submit orders** — the auto-execution path was removed after honest EV analysis showed expected value goes negative at our size given resolution-divergence risk on subjective markets.

## Emergency exits (3-layer sanity check spec in `strategy/02_operations.md`)

- `emergency_exit_ostium.py` — close all open Ostium positions at market.
- `emergency_exit_polymarket.py` — sell every Polymarket position at best_bid (10% slippage cap).
- `emergency_bridge_to_safety.py` — bridge full USDC off an at-risk chain via Across.
- `emergency_swap_usdc_to_eth.py` — Uniswap V3 USDC → WETH on a chain (5% slippage cap, Coingecko cross-check).

## Telegram interface

- `telegram.py` — outbound. Subcommands: `setup`, `msg`, `file`, `md`.

## Conventions

- All paths to secret-bearing files come from `_paths.path("ENV_VAR")`. No absolute paths in source.
- Telegram-related code passes through `_paths.scrub()` before logging to strip bot tokens.
- Network calls have explicit timeouts; failures fall through to "fail-open" defaults (e.g., agent eval errors → SEND, executor errors → no-trade).
- Emergency scripts are dumb executors; the smart "should we?" sanity check lives in the cron tick that invokes them.
