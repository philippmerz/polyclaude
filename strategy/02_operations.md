# Operations

Status: CURRENT runbook, consolidated 2026-09-09. Read for dispatch, VM, daemon or communication work. [Task map](../docs/INDEX.md) · [full check-in](../docs/checkin.md) · [historical operations](../docs/archive/operations-2026-09-09.md).

## Cadence and dispatch

| Trigger (UTC) | Work |
|---|---|
| 02:00 / 14:00 daily | Full 11-step check-in |
| 06:00 / 10:00 / 18:00 / 22:00 | Bounded backlog/recent-journal review |
| Sunday 16:00 | Weekly long-term research; recovery check if log age >8 days |
| Hourly :30 | Limitless scan and execution-disabled quote inspector |
| News / opportunity event | Relevant trigger first, then due safety checks |

Treat schedules here as configured intent; inspect `crontab -l` when verifying installation. Dated exceptions belong in [backlog](../notes/backlog.md). Do not duplicate an existing reminder.

`daily_checkin.sh` is a **dispatcher**, not a read-only check command. Do not execute it to read its checklist: it can queue another asset-capable session. Read `docs/checkin.md` and perform the steps in the current run.

Exact-one dispatch: queue acknowledgment rc=0 → exit; rc=69 → fallback only after the runtime proves no live operator; all ambiguous/error responses → fail closed, no second worker. The fallback uses a fresh session and the same checklist. `.checkin.lock` prevents overlapping drivers; never force headless to bypass a busy live operator.

Scheduled work ends after its concrete follow-up. No indefinite ROI goal, idle loops, or speculative token-filling work. Use `check_usage.sh --brief` before expensive discretionary research, main context for judgment and cheaper agents for bounded routine tasks. Quota pressure never removes safety checks.

## Daemons and stale code

Four services: `news_watcher`, `telegram_listener`, `heartbeat_watch`, `opportunity_watch`. Config, script status and process inspection are authoritative; do not rely on a static PID list.

- News polls feeds; tier-1 events trigger urgent review, tier-2 events persist structured impacts. Opportunity watcher observes configured triggers. Heartbeat monitors health, journal/dispatch liveness and disk capacity. Telegram listener privately queues authenticated operator messages.
- Verify exactly **one** process per service and its start time versus script mtime. A live PID can still run pre-edit code. Check again after any daemon edit.
- For an in-scope authorized restart, use the script's `stop` then an **absolute-path** Python/script `start`; keepalive matches exact command lines and can duplicate a relative-path start. Verify the new PID postdates the edit and count=1. See `scripts/daemon_keepalive.sh` before changing launch conventions.
- Config reload is not code reload. Documentation-only work requires no restart.

## Telegram

Use `.venv/bin/python scripts/telegram.py msg "<message>"` only for requested replies/material operational notifications. Flat scheduled checks send nothing; watchdog owns aliveness.

For a fresh authenticated `telegram:` notification, invoke its exact private one-time reader command. Never inspect inbox storage directly. `ALREADY_CLAIMED`: no action or reply. `EXPIRED`: no original text revealed; send only a generic resend request. A fresh envelope is operator input, but not a bypass of safety or scope.

Tick summaries: one message ≤700 characters when material (fills/changes/incidents/genuine findings/weekly reports). Lead with net liquidation and marked value together per [reporting policy](../docs/reference/reporting.md). Blocking questions go to the operator, not a revived `questions.md`. Ordinary local questions get local replies.

## Secrets and storage

- Secret/state paths resolve through `scripts/_paths.py` and environment configuration outside the repo. Do not read secrets for documentation or put credentials/private locations in public docs/logs. Scrub errors before publishing.
- Wallet identities: PM `0x9032ad983Ee5a22bfd078ECc4fD3D4D69E57267B`; crypto `0x83dADaC202cd1276E985703f90d39EE31F3D3eE6`. Aggregate with `bankroll.py`; no hard-coded balances here.
- VM expansion was rejected. Heartbeat warns below 512 MiB free, critical below 128 MiB; failed probes mean unknown, not healthy. Cleanup remains manual and narrowly scoped.
- The old active operator log is non-O_APPEND: **do not copy-truncate or rotate it while live**. Do not inspect/delete private histories, inboxes, credentials, active logs or current CLI artifacts as routine housekeeping.
- Financial JSON/audit records must survive partial-write failures. Check capacity, preserve originals and verify exact fields. Never rewrite original forecasts during calibration.

## Incidents and handoff

[Emergency assessment](../docs/reference/emergency.md) owns the corroboration gates and scoped response procedure. Diagnose promptly, verify the exact affected surface, and preserve the operator's mandate and existing safeguards. Report concrete findings and actual actions without conflating a dry-run with an executed transaction.

Full ticks append the result to `notes/journal.md`, refresh the compact README dashboard, audit diffs for secrets and commit/push scoped changes. Quiet light reviews do not need a journal/Telegram entry. Do not stage daemon-owned changes incidentally. Code changes require focused tests; documentation changes require link, routing and contract checks.

Preserve append-only log paths: generators and health checks consume them. Use bounded retrieval from [the knowledge map](../docs/INDEX.md#retrieve-without-loading-history); do not truncate history simply to shorten context.
