# scripts/

Quick map for any agent (or human) reading the repo cold. For deeper context: [`../README.md`](../README.md), [`../strategy/02_operations.md`](../strategy/02_operations.md), [`../notes/journal.md`](../notes/journal.md).

`operator_start.sh` starts the interactive runtime directly in tmux, retaining
the blank-session prompt gate. Codex owns session history; the launcher creates
no duplicate terminal transcript.

## Daemons (long-running; restarted on reboot via `@reboot` crontab)

- `news_watcher.py` — polls configured RSS feeds; validates classifier impacts against live exposure IDs. Research-only topics stay internal; material/critical and explicit unknown/safety cases qualify for review. Pending alert IDs persist until dispatch acknowledgment; queued does not mean reviewed. No raw RSS Telegram messages. Config: `news_watcher_config.json`.
- `telegram_listener.py` — long-polls Telegram, durably spools authorized messages, and submits them to the live operator's ordered conversation queue.
- `heartbeat_watch.py` — hourly probe; alerts if any daemon stalls > 30 min or any headless model worker runs > 60 min.

## Scheduled (crontab)

The former Sunday stock/brokerage review and missed-week catch-up are retired.
`watchlist_monitor.py` checks only project-routed crypto candidates.
`world_state_digest.py` and `longterm_check.py` remain tools for bounded,
on-demand research supporting accessible on-chain opportunities and held
positions; they do not create a recurring stock or brokerage workflow.

- `daily_checkin.sh` — main cron tick at `02:00` + `14:00` UTC. Queues to the live operator, or runs a fresh onboarded fallback, then follows the standard portfolio + prospecting + journal flow. Optional `POLYCLAUDE_DISPATCH_RECEIPT` records the actual lock/queue/fallback boundary; no receipt claims review completion.
- `arb_cron.sh` — hourly arb scan + executor at `30 * * * *`.

`inject_prompt.sh` keeps the historical Markdown bytes in `notes/inject_log.md`
and appends one compact JSON metadata line per queue attempt. New lines record
UTC time, status/return code, queued-payload UTF-8 byte count and SHA-256, and
whether the bounded contract was appended; they omit prompt and quota text. The
heartbeat uses only the file modification time, so this preserves its liveness
signal without duplicating prompt bodies.

## Sleeve clients (libraries imported by other scripts)

- `polyclaude_client.py` — Polymarket CLOB wrapper. EOA signing (`signature_type=0`). `place_limit_buy/sell`, `orderbook`, allowance setup, position queries.
- `ostium_client.py` — legacy Ostium reader/guarded-close client plus allowance revocation. New entries are blocked while this execution environment fails Ostium's current eligibility terms; a future entry also requires a current writer with exact allowance, bounded slippage and final oracle-fill verification.
- `_paths.py` — secret/state file resolution from `~/.polyclaude/env` (canonical), plus `~/secrets/limitless_creds.json`. Provides `path()` and `scrub()` + `install_scrubbing_excepthook()` so secrets never reach logs.

## Decision-quality tracking

- `decisions.py` — record/list/update/summarize structured decision entries. Stored in `notes/decisions.json`. Foundation for evaluating reasoning quality at scale; spec in `strategy/00_philosophy.md`.
- `jev_shadow.py` — standalone, capped System One research client. It is shadow-only: no watcher, probability, order, or trade path calls it. `models` is read-only; `ask` accepts typed state plus an ID-keyed `{type, instructions, criteria}` question map, pins `jev-1.13.0` by default, and records only metering metadata plus a state hash in private local usage history. It enforces input, timeout, repeat, and $0.50 calendar-month caps.
- `case_memory.py` — offline SQLite shadow store for exact case versions, source/configuration receipts, quote context and dependency-pinned assessments. `init`, `import-snapshot`, `observe`, `import-assessment`, `packet`, `bundle`, `status` use explicit paths/timestamps. Bundles losslessly share identical rule fields; stale/unknown cases remain visible. Use one coherent snapshot scope per DB; a different filter/profile is not complete observation of earlier cases. No network/model/execution/financial-record integration.
- `case_distribution.py` — pure shadow projection of reviewer-supplied joint scenarios onto explicitly bound exact market predicates. `--model MODEL.json --bindings BINDINGS.json --packets PACKETS.json` requires provided literal criteria with matching hashes and outcome-token mappings; completeness of live terms remains uncertified. Unknown mass remains in bounds; supplied weights are not calibrated forecasts, and freshness/economics remain separate checks. See [the architecture and measured replay](../research/2026-10-12-finite-context-architecture.md).

## Status / inspection (read-only)

- `context_packet.py` — offline, bounded orientation from allowlisted Git-tracked public docs. `--scope portfolio|research|engineering|operations`, optional `--query "heading words"`, `--format json|markdown`, default `--max-bytes 12000`. Uses notes/current_context.md review/expiry and source hashes; no live state, private history, model call or execution approval. Queries only current strategies and the lesson archive; current matches come first and archive excerpts carry historical labels, line bounds and hashes. No title match is explicit; optional sections are omitted whole on overflow, while an oversized essential packet fails. Required primary reads remain mandatory. Refresh the handoff through the existing record workflow, not by regenerating the packet.

- `public_source_archive.py` — reversible archive for explicitly allowlisted,
  receipt-linked public HTML in completed Oct 1–16 runs. `verify`, `restore` and
  `roundtrip` check manifest, raw/gzip hashes, source receipt and file metadata;
  this is not a general log cleaner.
- `public_source_archive_extra.py` — isolated `prior36` and `more-html` profiles.
  Choose `--profile prior36` or `--profile more-html` for verification/restoration;
  each profile has its own immutable manifest and rejects out-of-scope paths. Together with the base manifest, the verified set covers 307 receipt-linked
  public HTML bodies; this is scoped evidence archiving, not general cleanup.
- `public_snapshot_archive.py` — exact allowlist archive for nine completed Oct 13–16 thin-tail discovery snapshots. `verify` checks the manifest and gzip identities; `restore ORIGINAL_PATH` restores one original without overwriting changed bytes; `read_verified_path()` can verify/read original or archived bytes. Existing `shortlist_latest.json` symlinks are preserved, but direct JSON reads through them require restore while the target is archived. The manifest does not assert original HTTP receipt binding. Completion: `data/deep_review_20261017/public_discovery_archive_completed_0318.json` (two restore/recompress roundtrips; 68,669,172 bytes reclaimed).
- `public_snapshot_archive_data.py` — separate exact48-file archive for public thin-tail snapshots in `data/snapshots/` dated beforeOct13. `verify`, `restore ORIGINAL_PATH` and `read_verified_path()` check original/gzip and sidecar identities, preserving bytes/mode/mtime. Current/latest targets are excluded; the shared latest symlink remains mutable and untouched. Direct historical JSON reads require restore; ledger links use the verified reader. The immutable manifest records legacy sidecar versions without claiming HTTP receipt binding. Completion: `data/deep_review_20261017/work/storage_safety_120928/verified.json` (161,010,084 bytes reclaimed; live restore/recompression checked).
- `deep_review_ledger.py` — persist one frozen-universe research case at a time and rebuild its effective index/checkpoint. `start --index N` permits resuming the same unfinished case and rejects a different case until active work has a completed record; a failed record cannot advance the queue. `revise --input CASE.json --prior-report-sha256 SHA256 --reason "specific change"` appends a dated immutable report/JSON plus `revisions.jsonl`; it never overwrites the base case or `evaluations.jsonl`. Rebuild verifies revision identity, predecessor report SHA, revision JSON SHA and Markdown SHA. The live index/counts use the newest verified revision per condition once; `evaluations_written` remains the base-record count, with revision count/hash separate. Revisions change research status only, never authorize a trade. Base/revision reports validate local Markdown links before any immutable write, using the actual report directory and existing hash-verified archive readers; broken or escaping paths fail without changing the ledger. New standard economics check exact outcome labels, reference probabilities, complements and selected stresses against the current forecast before any immutable write; historical rebuild remains unchanged.
- `deep_review_resume.py` — read-only, byte-bounded packet for one active or pending frozen case (`--index N` to select explicitly). It verifies the selected case/revision report chain and emits checkpoint hashes plus exact full rules; oversized packets fail without truncation. Entire revision history is verified; long-chain emitted metadata keeps base plus latest two artifacts, with omitted count and full-list digest. It does not rebuild, record, call a model, or access network/accounts.
- `deep_review_terminal_status.py` — public Gamma status for at most30 explicit frozen indices; exact identity, full rules and tokens must match. Only closed/nonaccepting/UMA-resolved/binary-terminal cases become review leads. Root reads each full rule before recording an objective exclusion; other results remain unvalued. Private raw/gzip receipts bind hashes, HTTP status and clocks; sanitized units omit numeric prices. No CLOB, account, forecast or ledger writes.
- `read_capture.py` — private durable receipts around an existing vetted read call: persist intent first, then supplied bytes and receipt before parsing. Atomic no-overwrite publication; failures and parser crashes retain evidence. Declare body representation explicitly (`http_body`, SDK serialization or provider result); hashes bind supplied bytes, and call-window timestamps do not claim wire timing. It adds no transport, authentication or financial writer.
- `deep_review_economics.py` — offline `economics(index, p_yes, quote_path, reserve=..., days=..., quantity=...)`; quote path is required. Checks actual frozen/Gamma fields and outcome tokens, binds Gamma and books to saved response hashes/receipts, assigns probabilities by Yes/No label and computes age from the matching book response. Legacy packet provenance remains limited to its preserved body/hash/global time. Named binary outcomes require `reference_outcome="EXACT LABEL"`; forecasts declare the same `probability_reference_outcome`. Defaults remain Yes/No by label, never book order. Half-payout/void branches belong in the forecast expectation explicitly. Hypothetical fees/depth/carry only; no execution authority. [Clock audit](../research/2026-10-17-deep-review/quote_clock_audit_2145.md); [Gamma binding audit](../research/2026-10-17-deep-review/gamma_binding_audit_2226.md).
- `deep_review_public_snapshot.py` — `--indices CSV --output NEW_REPO_REL_JSON --log-dir NEW_REPO_REL_DIR`; capture public Gamma, compact fees, books and geoblock with actual HTTP status/receipt clocks and raw/gzip hashes. Verify frozen identity/rules/tokens, use `fd` fees (top-level `r` is rebates), distinguish missing books from HTTP failure, and fail with explicit gaps. Fee-disabled markets without `fd` require exact full CLOB numeric-zero corroboration; record that evidence separately without inventing a descriptor/parity. [Validation](../research/2026-10-20-fee-disabled-research-capture.md). Gzip evidence only; raw geoblock body stays private0600. No accounts, forecasts or writers.
- `wallet_status.py` — Polymarket-sleeve MATIC + USDC balance on Polygon.
- `exit_analysis.py` — held-position/group sale planning. Taker candidates meet the same book’s live `min_order_size`, including the minimum crossing inside a bid level; missing/invalid minimum leaves the book unpriced. Quotes still need all current execution gates before an order.
- `positions.py` — Polymarket open positions with mark-to-market P&L.
- `book_walk.py` — indicative bid proceeds. SELL fees use the greater of per-level and aggregate executed-price estimates, rounded upward to five decimals; partial fills use filled shares. This conservative convention follows one reconciled receipt and does not prove universal exchange fee grouping or executable depth.
- `crypto_status.py` — multi-chain balance reader for either sleeve. Subcommand: `crypto` (default) or `polymarket`.
- `discover_markets.py` — paginated Gamma discovery. Default snapshots are compact UTF-8 `.json.gz`, with raw-content SHA, gzip SHA, byte counts and coverage sidecar; both latest aliases point to that file. Use the compression-aware loader, or `--plain-snapshot`/`write_snapshot(compressed=False)` for direct JSON compatibility. Fetch/filter/top omissions, literal criteria and every row remain intact; liquidity/volume are not executable depth.
- `market_context_batches.py` — deterministic offline organizer with exact event grouping, coverage warnings and proof hashes. Save one `--format compact-json --output FILE.json.gz` parent per scan; `--input FILE.json.gz --batch-index N` resumes one batch without rereading sources. `--reference-only` saves a small parent-hash reference plus selected batch. Source/criteria/economics and offline/no-execution semantics remain required. Plain/pretty JSON and Markdown stay available.
- `log_storage.py` — lossless closed-artifact archive. `plan` inventories eligible untracked files; `maintain` verifies exact gzip roundtrips before removing raw copies; `verify` checks every mapping; `restore PATH` restores original bytes/mode/mtime. `read_verified_bytes(PATH)` handles plain, gzip, and hash-verified missing legacy paths. Index: local `logs/storage_archive/index.jsonl`; private/open/tracked files, existing hardlinks, receipts and current aliases are excluded. Scheduled check-ins maintain at most128files/64MiB input/30s; event-triggered checks skip maintenance. No evidence expiry or financial writer.
- `clob_books.py` — strict read-only Polymarket `POST /books` transport. It chunks requests at 500 unique token IDs, maps responses only by `asset_id`, preserves omitted requested IDs as missing, and rejects malformed, duplicate, or unexpected rows.
- `favorite_fade_scan.py` — short-horizon favorite-price profile only: exact identities and both-side context, no population probability, edge or APY. Deprecated `--min-edge-pp` warns and is ignored.
- `event_monotonicity_scan.py` — reports page failures/caps and incomplete fetch coverage; fetch failures exit nonzero while preserving observations for review.
- `polymarket_consistency_scan.py` — bounded basket quotes default to balanced midpoint-priority plus least-recently-attempted exact groups; `--live-selection midpoint` retains the diagnostic legacy order. Coverage, failures and quote lanes remain explicit.

The [opportunity method](../strategy/03_opportunity_method.md) distinguishes
discovery profiles, evidence, probability judgment and guarded execution. Offline
batches do not use a model. Cheap workers perform bounded triage/source collection;
the primary agent owns the portfolio decision.

`event_monotonicity_scan.py`, `polymarket_consistency_scan.py`,
`favorite_fade_scan.py`, and `cross_event_bound_scan.py` use that transport for
broad discovery walks while retaining their own identity, freshness, fee, and
depth validation. A batch is not an atomic execution quote: positive output is
provisional and requires an independent fresh rewalk before any action.

## On-chain operations

- `entry_review_gate.py` — offline operator restriction on all new Polymarket
  BUY bids:600 unique completed valuations plus a primary comparative selection
  of exact winner tokens. It cross-checks canonical checkpoint/index counts and
  a hashed research report; reaching600 alone does not release the pause.
  Missing, malformed or inconsistent authority fails closed. The execution
  CLIs and BUY writers enforce it; research previews and SELL/cancel/redemption
  management remain available. Policy: `notes/entry_review_gate.json`.
- `polyclaude_enter.py` — mandatory guarded Polymarket entry path. Single-market
  execution defaults to maker-or-skip: `--execute` with a taker route requires a
  logged `--taker-urgency` naming the short-lived reason that justifies fee and
  slippage. Multi-leg bundles retain their separately guarded taker-only path.
  Optional `--maker --maker-price PRICE` preserves an explicit fine-tick limit:
  both book reads must match the asset/condition, be at most180s old, and keep
  the price strictly below the ask. Integer-share lots must produce exact cent
  cash within budget, meet live share minima and the1USD cash floor. Preview,
  cap checks, reservation and post-only writer use that same price/size/cash;
  the default maker cent grid remains. No bundle or routine-taker bypass.
  [Precision repair and validation](../research/2026-10-19-fine-tick-maker-repair.md).
  Cancellation reconciliation binds complementary fills to the reserved maker's
  own asset/BUY row and parent condition; outer trade assets can differ. Terminal
  cancellation, exhaustive fills and indexed cumulative purchases still gate
  reservation retirement. [Verified repair](../research/2026-10-19-2232-periodic-check.md).
- `catalyst_check.py --facts-only --slug EXACT_SLUG` — collect dated source
  evidence while the primary analyst owns probabilities and selection. Feed
  title matches remain unverified leads in both modes; missing bodies are gaps.
  Pass a separately reviewed `--my-p` to the entry tool; this mode provides no
  automatic forecast or execution authority.
- `clob_v2.py` — authenticated order, cancel, sell and redemption client. Its
  read-only `orders` display adds a canonical slug only after an exact
  condition-ID plus token-ID match against `notes/position_condition_ids.json`;
  unknown or duplicate identities are labeled explicitly rather than guessed.
  `redeem-all` still skips losing/uncertain rows. Explicit requested cleanup uses
  `redeem-one CONDITION --token-id ASSET --outcome Yes|No --burn-losing`
  (add `--neg-risk` when applicable; rehearse with `--dry-run`). It proves exact
  identity and final zero payout, burns only that side, and verifies zero
  post-balance. This spends gas; it neither recovers stakes nor erases history.
- `across_bridge.py` — Across V3 bridge for USDC and native ETH across Arbitrum / Base / Polygon / Optimism.
- `aave_deposit.py` — Aave V3 `supply` / `withdraw` / `rate` across the same chains; new supply fails closed on inactive, paused, frozen, or simulation-reverting reserves.
- `spot_swap.py` — guarded Uniswap V3 exact-input swaps with independent output floors, signing-time requotes, chain-aware gas, and pre-sign simulation.
- `wrap_pusd.py` — exact 1:1 Polygon conversion in both directions: USDC.e → pUSD through CollateralOnramp and pUSD → USDC.e (or native USDC when that asset is unpaused) through CollateralOfframp. Write paths validate the deployment and simulate before broadcast.
- `monotonicity_pair.py` — guarded equal-share execution for a revalidated
  sibling implication pair. It defaults to dry-run and requires exact shared
  criteria/event identity, fresh CLOB books, fee/route parity, portfolio caps,
  route-specific approvals, persistent correlation/group topology, FOK balance
  reconciliation, and bounded rollback.
- `limitless_arb_scan.py` — paginates Limitless `isPolyArbitrage:true` markets, fuzzy-matches Polymarket counterparts, uses a scoped fast worker to verify resolution-language equivalence, and tags Chainlink-Data-Stream-backed markets as mechanical resolution. Output: `logs/limitless_arb_<ts>.md` + `logs/limitless_arb_latest.json`.
- `limitless_arb_executor.py` — live-quote inspector. Reads scan output, recomputes net edge after real orderbook slippage. **Does not submit orders** — the auto-execution path was removed after honest EV analysis showed expected value goes negative at our size given resolution-divergence risk on subjective markets.

## Emergency exits (3-layer sanity check spec in `strategy/02_operations.md`)

- `emergency_exit_ostium.py` — close all open Ostium positions at market.
- `emergency_exit_polymarket.py` — sell every Polymarket position at best_bid (10% slippage cap).
- `emergency_bridge_to_safety.py` — bridge full USDC off an at-risk chain via Across.
- `emergency_swap_usdc_to_eth.py` — Uniswap V3 USDC → WETH on a chain (5% slippage cap, validated CoinGecko quote with fresh DefiLlama fallback; aborts if neither is available).

## Telegram interface

- `telegram.py` — outbound. Subcommands: `setup --expected-chat-id`, `msg`,
  `file`, `md`. Shell-composed messages should use `msg --stdin` with a
  single-quoted heredoc (or `msg --input-file PATH`) so currency `$`,
  backticks, and command substitutions remain literal. Positional `msg TEXT`
  remains available for subprocess argv callers.

## Conventions

- All paths to secret-bearing files come from `_paths.path("ENV_VAR")`. No absolute paths in source.
- Telegram-related code passes through `_paths.scrub()` before logging to strip bot tokens.
- Network calls have explicit timeouts; failures fall through to "fail-open" defaults (e.g., agent eval errors → SEND, executor errors → no-trade).
- Emergency scripts are dumb executors; the smart "should we?" sanity check lives in the cron tick that invokes them.

- `position_state_audit.py` — malformed criteria-read dates are flagged as unknown/stale; they cannot abort claim-insurance checks.
