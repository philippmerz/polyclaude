# Operations

Single canonical home for the project's operational infrastructure. Other docs reference this file rather than restate it.

## Operator session history

`pc-attach` attaches to the interactive operator. That session is the Grok
CLI on grok-4.7. `scripts/operator_start.sh` does not launch a model runtime.
Scheduled work queues through the private adapter, which runs a separate
headless grok process and does not resume the interactive session. Operator
directive 2026-10-19: do not reintroduce `script`, `tee`, or tmux output
capture for the interactive session, or create `logs/operator/` transcripts.

## Cron — autonomous check-in driver

- **Schedule (UTC):** `0 */3 * * *` — eight equispaced check-ins at 00, 03, 06, 09, 12, 15, 18, and 21. A wake that still has a fresh page-capped discovery reports that stop and does not launch another full scan.
- **Finite goal:** `scripts/goal_inject.sh set "<objective>"` queues one `/goal` line into the live session. `scripts/goal_inject.sh clear` removes it when the work is done. A goal is not a waiting loop and does not replace the 3-hour ticks.
- **Driver:** `scripts/daily_checkin.sh`. Resolves repo root from `${BASH_SOURCE[0]}`, sources `~/.polyclaude/env` for secret paths, queues to the long-lived operator when available, and otherwise starts a fresh fully onboarded headless fallback.
- **Per-tick token cap:** ~100K (the prompt itself caps).
- **Logs:** `polyclaude/logs/cron/checkin_<UTC ts>.log` (gitignored; closed artifacts enter the bounded lossless archive described below).
- **What each tick does:** load context (memory, journal tail, strategy), mark portfolio + bankroll via `scripts/positions.py` + `scripts/bankroll.py` (authoritative total), scan WebSearch for active-position catalysts, decide hold/adjust/add/close, journal it, write a weekly report if ≥7d since last, commit + push (audit diff for secrets first), Telegram-alert if anything material moved.

Weekly portfolio P&L and passive index comparisons remain part of account evaluation.

## News watcher — 24/7 reactive layer

- **Daemon:** `scripts/news_watcher.py` (subcommands `start | status | stop | once`). Restarts on reboot via `@reboot` crontab.
- **Feeds:** configured public RSS sources, polled every 300s; the current list is in the config.
- **Config:** `scripts/news_watcher_config.json` — feeds + tiered keyword lists, editable; daemon re-reads each poll.
- **Relevance:** both keyword tiers use the scoped classifier against current held positions and authenticated live BUY commitments (five-minute inventory cache). Impact keys must match actual condition IDs; an Ostium key requires verified open trades. Research-only/minor mentions do not qualify as portfolio alerts. Zero quantity and settled claims are excluded; an unresolved zero-priced holding remains exposure. This classification neither values nor rejects research candidates.
- **Review routing:** material/critical current-exposure impacts qualify for an internal review. Inventory/classifier failures and possible infrastructure incidents remain explicitly unknown safety/review cases. Tier1 research leads remain available internally. Classify before the routine headline cooldown so an earlier generic article cannot mask a critical update.
- **Dispatch evidence:** ordinary reviews stay in `notes/news_alerts.jsonl` for the next 3-hour tick and do not spawn one. Critical and safety leads request a tick immediately; those pending IDs survive deferral and retry on existing polls. Journal recency does not prove an alert was read. `daily_checkin.sh` acknowledges `queued`, `deferred`, `failed` or `fallback_starting` through a local receipt; a missing acknowledgment is `unconfirmed`. Queued means accepted for delivery, never reviewed or completed. Logs: `logs/news_dispatch.jsonl` and its related alert IDs. Unconfirmed critical requests are checked for late acknowledgment without blindly resending them.
- **Outbound policy (October 18):** the news watcher sends no raw headlines to Telegram, including Tier 1. The reviewing agent sends material findings, verified actions or decisions through the documented sender; routine mentions, research candidates and unfilled bids do not justify standalone headline pings. Internal detection, critical-impact records, review triggers and operational incident warnings remain active.

## Telegram bridge

- **Bot:** `@<bot-handle>`.
- **Outbound:** `scripts/telegram.py {setup --expected-chat-id,msg,file,md}`.
  For agent-composed shell messages, pass the body through literal stdin with a
  single-quoted heredoc delimiter; never put arbitrary text containing `$`,
  backticks, or `$()` in a double-quoted shell argument:

  ```bash
  .venv/bin/python scripts/telegram.py msg --stdin <<'TELEGRAM'
  Portfolio value is $164.65.
  TELEGRAM
  ```

  `msg --input-file PATH` is the equivalent safe route for an existing UTF-8
  file. Python callers already pass message bodies as argv list elements and
  do not invoke a shell.
- **Inbound:** `scripts/telegram_listener.py start` long-polls, enforces the configured private chat ID, writes authorized text to a private ordered spool, then submits it through the operator's durable conversation queue. The Telegram cursor advances only after durable local spooling; delivery retries preserve order without terminal keystrokes. Message text is not written to the listener log.

## Secrets — path-leak hygiene

- **Path resolution:** scripts read all secret/state file locations from env vars resolved through `scripts/_paths.py`, which auto-loads `~/.polyclaude/env` (gitignored, 0o600, outside the repo) on import. Public source contains env-var names only — never absolute filesystem paths.
- **Stored files** (all in the gitignored secrets directory, mode 0o600): two wallet keyfiles (Polymarket sleeve + crypto sleeve), Polymarket API creds, Telegram bot token, private agent state, and watcher state.
- **Adding a new secret:** declare it in `~/.polyclaude/env`, then read via `_paths.path("VAR_NAME")` in script. Never hardcode a path.

## Wallets

| Sleeve | Address | Holds | Strategy spec |
|---|---|---|---|
| Polymarket | `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B` | PM positions + Aave Polygon idle + pUSD + POL gas | `AGENTS.md`; live positions via `scripts/positions.py`, decisions in `notes/decisions.json` |
| Crypto | `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6` | Aave Arb/Base idle + dust (Ostium venue wallet) | Same doctrine; aggregate via `scripts/bankroll.py` |

Both wallets resolved via the same `_paths.py` mechanism (`POLYCLAUDE_WALLET`, `POLYCLAUDE_WALLET_CRYPTO`).

## Daemons currently running

- `scripts/news_watcher.py start` — PID in `~/.polyclaude_news_watcher.pid`
- `scripts/telegram_listener.py start` — PID in `~/.polyclaude_telegram_listener.pid`
- Both restart on reboot via `@reboot` crontab entries.

## Performance chart

The static performance chart is in `docs/`. After an already-required complete
portfolio snapshot, manually append its recorded totals to
`docs/performance.csv` with a public financial source reference. Use values from
the same check and retain blank fields and timestamp precision; do not make
extra market requests or infer missing gas from another date. The graph derives
whole-account trading depth excluding separately funded gas and keeps midpoint
value alongside it. Archive account totals without a gas split appear only as
gas-inclusive USD marks; documented trading-only sums and rounded accounting
reconstructions retain their provenance and approximation labels. External
trading contributions also update `docs/contributions.csv`; internal transfers
are not flows. See `docs/README.md` for the CSV columns and Pages setting.
Push the CSV with the existing record update; this adds no watcher,
timer or trading authority.

## Compact working context

Keep notes/current_context.md as a short public handoff: active work, blockers,
the last completed check's dated evidence pointers, material unknowns and the
next already-scheduled boundary. Target 6 KB; never copy private operator text,
credentials or a stale probability as fresh authority. Original financial
records and the full journal remain unchanged by condensation.

After an existing check or material decision, refresh it when state changed or
it expired. Review relevant current documents and records first. Set reviewed_at
to that actual editorial review, valid_until to the next due check/catalyst,
and source_hashes to raw-file SHA-256 values for every allowlisted public
document used for curation. Financial/source observations retain their separate
as-of times and original evidence; hashing a guide does not refresh them.
Compute hashes after updating source documents. Do not roll expiry forward by
copying the old summary; explicitly retain dates and unknowns when no fresh
financial/source check was performed.

Keep completed case reports and source/model units independently addressable;
target2–5KB per unit and link large arrays/raw receipts separately. Store a small
hashed index for scanner batches so resumption needs only the selected unit.
Before formatting read evidence, persist it through the existing vetted reader;
`scripts/read_capture.py` provides private durable intent/body/receipt storage.
Label SDK serialization and call-window timing honestly; they are not raw HTTP
or wire timestamps. The helper changes no financial execution path.

For tool-orchestrated web reads, store the returned string or object before any
formatting or serialization. Use JSON and the proven writer; do not assume `btoa`
or `Buffer` exists. If saving fails, retain the stored result and repair the writer
without repeating the request. Mark any missing response or timing explicitly.

Storage: prefer compact JSON/JSONL or CSV, with one shared policy/source parent
and small indexed units. Large captures and discovery snapshots use gzip;
retain raw-content hashes, timestamps, criteria and complete analysis. Do not
save repeated Markdown wrappers or duplicate uncompressed bodies. Existing
case/financial records retain their original bytes and hashes. `log_storage.py`
archives closed, untracked artifacts older than24h, verifies gzip roundtrips,
and preserves a local path/hash index. It excludes open files, current aliases,
hardlinks, receipts and private operator paths. Read archived bytes with
`read_verified_bytes`; `restore PATH` recreates an exact legacy file. Scheduled
check-ins reuse a bounded maintenance pass; event-triggered checks skip it.

For CLI checks, persist each completed command's stdout, stderr, return code and
invocation bounds before optional receipt conversion or another command. Two
October20 wrappers lost return codes by keeping them only in memory until a
later adapter failed; preserved output does not establish a zero return code.
`Capture.write_response` requires both `started_utc` and `received_utc`, matched
to the durable intent. For API reads, use the existing
`capture_readonly_call` adapter when suitable; its response is saved before parsing.

scripts/context_packet.py emits a bounded orientation packet for portfolio,
research, engineering or operations from allowlisted Git-tracked public files.
Its default cap is 12,000 UTF-8 bytes, not a model token budget. Expired, future
or hash-mismatched handoffs remain visibly stale/invalid. Optional matched
sections are dropped whole on overflow; required reads and the handoff are
never silently cut. No live/account/model data or execution approval is inferred.

During the already-due weekly P&L review, review strategy/01_lessons.md for
duplicates and superseded examples, preserving current gates and linked dated
evidence. The byte-identical pre-condensation ledger is in strategy/archive/.
Use targeted searches for relevant history; do not load the full journal or
archive as default onboarding. This adds no timer, watcher or durable goal.

## Operator-blocking questions

Surface via Telegram using the literal `msg --stdin` form above rather than a
tracked file. The previous `questions.md` was retired 2026-04-29 in favor of
the live channel — operator wants questions to interrupt them in real time,
not pile up in a file.

## Heartbeat watchdog

`scripts/heartbeat_watch.py` runs as its own daemon (PID file `~/.polyclaude_heartbeat.pid`, restarts on reboot via `@reboot` crontab). Hourly probe — checks news_watcher and telegram_listener PIDs are alive, news_watcher's state file is fresh (< 30 min), and no headless model worker has been running > 60 min. Alerts have separate cooldowns. Routine disk warnings below 512 MiB repeat at most once every 24 hours; critical space below 128 MiB and disk-probe failures retain hourly cooldowns. A recent warning never suppresses a critical alert. Was added 2026-04-29 after a 3-day deadlocked cron tick from the prior week; this layer would have caught it within an hour.

## Emergency-exit protocol

When a Tier-1 news_watcher alert indicates a real exploit / depeg / chain halt affecting our positions, the cron tick that gets auto-fired runs a 3-layer sanity check, then invokes a pre-built `scripts/emergency_exit_*.py` script. The scripts are dumb executors; the *intelligence* (deciding whether to call them) is in the cron tick.

### Three-layer sanity check (all must pass before invoking any emergency script)

1. **Multi-source corroboration.** WebFetch ≥ 3 independent crypto-news sources. Require ≥ 2 to confirm the same event. If only 1 source mentions it, especially a low-reputation feed → HOLD + Telegram operator. (This alone catches the substring-regex false positive that hit on 2026-04-29 — only one feed had the keyword, others would not corroborate.)
2. **Market-reaction consistency.** The market should already be reacting if the event is real:
   - *USDC/USDT depeg*: actual price from a validated CoinGecko quote with fresh DefiLlama fallback. Must be < $0.98 to confirm.
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

The operator can also invoke any of these manually via Telegram. Explicit authenticated operator authority is trusted, but the agent still revalidates message freshness, current live state, and the hard execution gates immediately before acting; a stale consequential message requires reconfirmation.

### What NOT to do under panic

- Don't write new emergency code under time pressure — the scripts are pre-built for exactly this. If the situation requires something not pre-built, Telegram the operator and let them decide.
- Don't escalate sizing (e.g., "since this is bad, sell *more* of the safe sleeve too"). Each script handles its scoped at-risk surface; cross-contamination of scope is a recipe for loss.
- Don't panic-bridge through a bridge that's the at-risk component (e.g., if Across is exploited, do not use `emergency_bridge_to_safety.py` since it uses Across).
