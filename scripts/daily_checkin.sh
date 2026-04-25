#!/bin/bash
# Polyclaude daily check-in.
# Invoked by cron. Each run is a fresh headless Claude session that loads context
# from polyclaude/ + memory, monitors positions, scans news, journals, and trades
# if conviction warrants it.

set -euo pipefail

POLYCLAUDE_DIR="<PROJECT>"
LOG_DIR="${POLYCLAUDE_DIR}/logs/cron"
mkdir -p "${LOG_DIR}"

TS=$(date -u +%Y%m%dT%H%M%SZ)
LOG_FILE="${LOG_DIR}/checkin_${TS}.log"

# Ensure we have a working PATH for cron (cron runs with minimal env)
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export HOME="<HOME>"

# A self-contained prompt the headless agent will operate on.
# Keep it tight: it gets read into context every run.
read -r -d '' PROMPT <<'EOF' || true
You are continuing the polyclaude project — an autonomous Polymarket trading experiment.
The operator may not check in for several days; you are running on cron.

# Setup (read these first)
- Working dir: <PROJECT> (you should `cd` here)
- Wallet (PRIVATE, never commit): <SECRETS>/wallet.json
- Memory index: <HOME>/.claude/projects/-home-philipp/memory/MEMORY.md (load all linked files)
- Python venv: <PROJECT>/.venv (use .venv/bin/python)
- Repo is public github (philippmerz/polyclaude); audit every commit for secrets

Read in order before deciding anything:
1. <HOME>/.claude/projects/-home-philipp/memory/MEMORY.md (and the files it links)
2. polyclaude/strategy/00_philosophy.md and 01_horizon_split.md
3. tail -200 polyclaude/notes/journal.md
4. polyclaude/research/_long_initial.md and _short_initial.md (or any newer research notes)
5. polyclaude/questions.md (operator may have answered something or asked a new question)

# Today's task
1. Mark current state:
     cd <PROJECT>
     .venv/bin/python scripts/wallet_status.py
     .venv/bin/python scripts/positions.py
2. News scan via WebSearch / WebFetch — only the catalysts that move active positions:
     - Iran-US conflict / Hormuz blockade / any peace deal language (moves S1, Iran-regime, Pahlavi)
     - Trump health, security incidents, 25th-amendment chatter (moves Trump-out)
     - UAP/UFO disclosure, AARO press releases, Pentagon/NASA UAP statements (moves Aliens)
     - Eurovision 2026 build-up if today is on or before 2026-05-16 (moves Latvia)
     - Ohio Dem gubernatorial primary if on or before 2026-05-05 (moves Acton)
     - La Liga title race / top-4 standings if on or before 2026-05-30 (moves Atletico)
     - Any of the long-sleeve themes if a major event broke
3. Decide: hold / adjust / close any position. If a position MTM has moved >5% from entry: explain the move; decide whether to add/trim/exit. Document reasoning in notes/journal.md.
4. If new high-EV markets surfaced and pass the philosophy/checklist (Kelly/4 sizing, sleeve caps from strategy/01_horizon_split.md, no AI-model markets): consider exploratory orders. Cap any new ticket at $5 unless justified in the journal entry.
5. Weekly report: if today is Saturday OR pnl_weekly.md hasn't been written in ≥7 days, generate a new entry in notes/pnl_weekly.md per the verbose-decision-log spec in strategy/00_philosophy.md (full reasoning trail, every market considered including rejections, mistakes list, next-week outlook, sources).
6. Commit + push. Audit the diff for secrets (`grep -E '0x[0-9a-fA-F]{64}|private_key|mnemonic'`) before `git push`.
7. End with one paragraph summarizing what changed today.

# Constraints
- Token budget: aim for ≤ 100K tokens this run. Skip lengthy explorations if positions look stable.
- Honor sleeve caps from strategy/01_horizon_split.md.
- Don't trade AI-model leaderboard markets (self-conflict of interest).
- If you're genuinely blocked on an operator decision: append to questions.md (don't email; operator reads the file).
- Do NOT remove or rewrite earlier journal entries; append-only.
- Do not invoke /loop or /schedule from inside this run — cron handles cadence.

If positions are stable and there's no news worth journaling, write a one-line "stable, no action" entry and exit cleanly. Brevity is a virtue when nothing happened.
EOF

cd "${POLYCLAUDE_DIR}"

{
  echo "=== polyclaude daily check-in ${TS} ==="
  echo "$ pwd"
  pwd
  echo "$ claude -p (headless)"
  echo "${PROMPT}" | claude -p \
    --model opus \
    --effort max \
    --permission-mode acceptEdits \
    --allowed-tools "Bash,Read,Write,Edit,Grep,Glob,WebSearch,WebFetch,TaskCreate,TaskUpdate,TaskList" \
    2>&1
  echo
  echo "=== exit $? at $(date -u) ==="
} >> "${LOG_FILE}" 2>&1

# Keep last 30 days of logs only
find "${LOG_DIR}" -name "checkin_*.log" -mtime +30 -delete 2>/dev/null || true
