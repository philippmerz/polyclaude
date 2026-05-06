# Operator-Agent Log

Append-only log of every operator decision. Format per `notes/operator_primer.md`:

```
## YYYY-MM-DD HH:MM UTC
- trigger: <user-typed | cron | news-alert | morning-ping | self-burst>
- assessment: <one line — what's the state?>
- action: <spawned worker with task X | passed | proposed strategic pivot to user>
- outcome: <one line — what happened, token cost rough>
```

---

## 2026-05-06 (initial setup, not yet started)
Operator agent infrastructure shipped by the worker (me) per user request to automate user's manual continuation-pressure role. User to start the session via `scripts/operator_agent.sh` when ready, then attach via `tmux attach -t operator` to observe.
