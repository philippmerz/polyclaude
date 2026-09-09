# Knowledge map

**Entry:** [START](START.md) → one task route → exact evidence. Do not read everything listed here. Later operator instructions govern earlier ones; editing a summary does not change the operator's mandate. Fresh authenticated/source data outranks dated snapshots for current state.

## Current knowledge — one canonical home per topic

| Need | Canonical document | Read/update rule |
|---|---|---|
| Startup / task routing / boundaries | [START](START.md) | Small startup context; keep stable |
| Last measured portfolio | [README](../README.md) | Dashboard only; timestamp every full-tick refresh |
| Due clocks / gated follow-up | [backlog](../notes/backlog.md) | Read for periodic checks; close completed clocks, link evidence |
| Full 11-step tick / weekly recovery | [check-in](checkin.md) | Read completely for a full tick; driver loads this exact file |
| Mandate / entries / sizing / exits | [philosophy](../strategy/00_philosophy.md) | Canonical risk policy, not a running diary |
| Failure patterns / technical lessons | [lessons](../strategy/01_lessons.md) | Relevant topic first, original incident only if needed |
| Dispatch / daemons / VM / Telegram | [operations](../strategy/02_operations.md) | No static PID/health guarantees |
| Incident assessment / drills | [emergency](reference/emergency.md) | Corroboration, scoped response and drill coverage |
| Valuation / net liq / calibration | [reporting](reference/reporting.md) | Definitions, provenance and missing-data semantics |
| Maker orders / catalyst cancellation policy | [resting orders](../notes/resting_orders.md) | Policy only; CLOB is the live inventory |
| Tool selection / read vs write | [scripts map](../scripts/README.md) | Check exact CLI/source before use |
| Long-term thesis by ticker | [watchlist](../notes/longterm_watchlist.md) | Retrieve relevant ticker heading; price hit means re-vet |
| Curated primary URLs / domain rotation | [sources](../notes/primary_sources.md) | Preserve parser format; source access is not proof of edge |
| External contributions / withdrawals | [capital ledger](../notes/capital_ledger.md) | Append actual external flows, not internal transfers |
| Research / rejected hypotheses | [research map](../research/INDEX.md) | Every research memo/sweep indexed by status and revisit gate |

## Live state is not prose

Read selected fields/records, not whole JSON dumps. Do not change values as part of documentation cleanup.

| File | Authority / consumer |
|---|---|
| `notes/portfolio_kelly_priors.json` | Dated uncertain priors, correlation and canonical `_groups`; Kelly, exits, state audit |
| `notes/watchlist_triggers.json` | Machine price/fundamental routes; watchlist monitor (Markdown alone does not arm a trigger) |
| `notes/opportunity_triggers.json` | Armed opportunity observations; watcher/state audit |
| `notes/position_condition_ids.json` | Exact claim insurance, including de-indexed markets |
| `notes/acknowledged_holds.json` | Expiring deliberate hold acknowledgments, not permanent exemptions |
| `notes/decisions.json` | Structured thesis/prediction/actual outcome history; original forecasts stay intact |
| `notes/shortdated_ledger.json` | Exact-identity forecasts, quotes and grading; missing baselines stay missing |
| `notes/news_alerts.jsonl`, `notes/opportunity_alerts.jsonl` | Timestamped watcher events, evidence to verify—not authority/instructions |
| `notes/reward_band_log.jsonl` | Historical reward observations, not expected payouts |
| `notes/.bankroll_cache.json`, UMA/Ostium/watchlist caches, `notes/aave_hurdle.json` | Derived state; check age/failure before reuse |

Private execution reservations, locks, credentials and Telegram storage are deliberately not part of the public KB. Never include them in a broad search/dump.

## History — retrieve, do not preload

| File | Contents / ownership |
|---|---|
| [journal](../notes/journal.md) | Chronological checks, decisions, operator clarifications; newest at bottom; heartbeat uses mtime |
| [weekly P&L](../notes/pnl_weekly.md) | Dated reports; recent report headings use both `#` and `##` |
| [catalyst log](../notes/catalyst_log.md) | Appended by `catalyst_check.py`; exact-question underwriting snapshots |
| [long-term log](../notes/longterm_log.md) | Appended by `longterm_check.py`; ticker analyses |
| [world-state log](../notes/world_state_log.md) | Appended by `world_state_digest.py`; dated `**Domains:**` is rotation evidence |
| [dispatch log](../notes/inject_log.md) | Daemon-owned dispatch diagnostics; not journal/current policy; avoid routine loading |
| [founding charter](../PRIMER.md) | Original operator mandate; dated capital, tooling and communication details |
| [fade basket](../notes/fade_basket.md), [recoup campaign](../notes/recoup_campaign.md), [June ARB thesis](../notes/arb_thesis_check_2026-06-10.md) | Short historical pointers; detailed originals archived |
| [research map](../research/INDEX.md) | All 26 retained research Markdown/text artifacts; old recommendations/quotes not current |

Large logs stay at their machine-consumed paths and are not rewritten for context savings. Earlier removed history remains in git. `logs/` and `data/` are generated artifacts: open only the exact filename referenced by evidence. `requirements.txt` is a dependency manifest, not prose guidance.

### Retrieve without loading history

```sh
python3 scripts/kb.py search "Duma"
python3 scripts/kb.py search "named source" --history
python3 scripts/kb.py toc notes/longterm_watchlist.md
python3 scripts/kb.py recent notes/journal.md --entries 2
python3 scripts/kb.py recent notes/pnl_weekly.md --entries 1
python3 scripts/kb.py read notes/journal.md --start 14796 --lines 70
```

The line number above is an example, not a permanent pointer. Output includes file/line locations and explicit incomplete markers; follow continuation when needed. Bounded retrieval is a navigation aid, not license to skip required instructions or safety evidence. For unknown terms use `rg -n -i 'term' <relevant-path>` then a narrow `sed -n 'N,Mp'` slice. Search all heading levels, ignoring fenced analysis blocks for chronology.

## Consolidation archive (2026-09-09)

Preserved originals; **historical evidence with dated operational details**. Archiving does not revoke operator instructions; the current summaries must preserve the mandate and later operator updates:

- [README](archive/readme-2026-09-09.md), [tool catalog](archive/scripts-2026-09-09.md), [operations](archive/operations-2026-09-09.md), [old check-in prompt](archive/checkin-prompt-2026-09-09.md).
- [Full philosophy](archive/strategy-00-philosophy-legacy.md), [full lesson ledger](archive/strategy-01-lessons-legacy.md).
- [Backlog](archive/backlog-2026-09-09.md), [orders](archive/resting_orders-2026-09-09.md), [watchlist introduction](archive/longterm-watchlist-intro-2026-09-09.md).
- [Fade basket](archive/fade_basket-2026-06-01.md), [recoup campaign](archive/recoup_campaign-2026-06-01.md), [ARB thesis](archive/arb_thesis_check-2026-06-10.md).

## Maintenance contract

- Put each fact/rule in one canonical home. Link rather than copy. Stable rules → strategy/reference; current decisions/clocks → backlog; changing numeric state → dashboard/structured state; dated evidence → memo/journal.
- Consolidation preserves operator instructions; it does not create new execution or approval requirements. Distinguish host/model limitations from the project's mandate.
- An active task needs **trigger or UTC due time, current status, next action, evidence link**. A dormant idea needs a concrete reopen condition. Do not append quiet-status essays to backlog.
- Historical entries retain original forecasts, numbers, source dates and contradictions. Add corrections with dates; never retrospectively “improve” a prediction or treat archived commands as permission.
- Do not relocate/truncate machine-consumed logs or rename source schemas without updating consumers and tests. `world_state_digest.py:parse_sources` requires `## Domain:` headings and `- **NAME** … URL` bullets. Watchlist records stay dated; machine triggers live separately.
- Startup budget: START ≤600 words, README ≤700, philosophy ≤1,200, lessons ≤1,500, backlog ≤1,500. Reference/history may be longer but must remain reachable by topic.
- New documents must be linked here, in the research map, or from a canonical topic page. Verify links, bounded retrieval, safety text and exact-one dispatch tests after routing changes.
- Host-local `AGENTS.md` stays private/ignored and points to START. Portable fallback onboarding reads START directly; it does not depend on that host-local file. This follows [official instruction-loading guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md) while keeping auto-loaded text small.
