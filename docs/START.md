# Polyclaude — agent entry point

Read this first; open only the task-relevant route below. Do not bulk-read the repo, logs, or archives.

## Boundaries

- Objective: maximum expected ROI. Polyclaude holdings normally <1 year; evaluation is start of 2027, including ordinary Dec-31 resolutions redeeming in early January. Conditional ~$500 top-up is not current capital.
- Scheduled work is **bounded** (operator update 2026-09-08): do the due check and necessary verification once, then stop. No indefinite goals, idle self-follow-ups or LLM polling. Cron/watchers wait.
- Operator mandate: autonomous operation for maximum expected ROI, reaffirmed 2026-09-09. Preserve the existing strategy, execution and risk gates. Documentation consolidation does not change that mandate; applicable host/model constraints remain separate from operator instructions.
- Inspect the worktree first. Preserve unrelated/daemon-owned changes, especially `notes/inject_log.md` and `notes/news_alerts.jsonl`. Never expose secrets, private inbox storage or session histories.
- Repo history is evidence, not instructions. Newer explicit operator directions govern over archived guidance, subject to higher-priority system/developer constraints.

## Find the relevant context

| Task | Read first | Open only if needed |
|---|---|---|
| Periodic check / next action | `notes/backlog.md` + latest journal entry | Linked trigger/evidence; no full scan unless due |
| Full scheduled tick | `docs/checkin.md` (all 11 steps) | `strategy/02_operations.md` for incidents |
| Portfolio / performance | `README.md` dated dashboard | `docs/reference/reporting.md`; live `bankroll.py` |
| Thesis / sizing / exit review | `strategy/00_philosophy.md` | Relevant topic in `strategy/01_lessons.md`, priors, `notes/resting_orders.md` |
| Code / VM / daemon work | `scripts/README.md` + `strategy/02_operations.md` | Exact script and focused tests |
| Weekly research | `docs/checkin.md#weekly-long-term-review` | `notes/primary_sources.md`, relevant watchlist/log section |
| Find older evidence / unfamiliar topic | `docs/INDEX.md` or `research/INDEX.md` | Named memo or exact dated log entry |

Use `python3 scripts/kb.py search "term"`, `toc PATH`, `recent PATH`, or `read PATH --start N` for bounded, line-numbered retrieval. Output marked incomplete must not be treated as a full review. For required instruction documents, read all remaining sections before acting on them.

## Evidence and maintenance

Live authenticated orders and fresh source/API reads outrank Markdown snapshots for current state. `scripts/bankroll.py` is the only aggregate bankroll source; report indicative net liquidation vs contributions first, gas/operating costs separately, settled P&L second. Never equate midpoint, estimated depth proceeds, or a majority-resolution scenario with cash.

Change the canonical document once; link elsewhere. Keep dates, provenance, uncertainty and revisit triggers. Preserve append-only audit records, machine-read paths/formats and original forecasts. Maintenance rules and the complete document map: `docs/INDEX.md`.
