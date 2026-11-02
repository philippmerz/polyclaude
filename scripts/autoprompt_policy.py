#!/usr/bin/env python3
"""Operator auto-prompt policy gate (notes/operator_autoprompt.json).

Usage: autoprompt_policy.py <source>   -> exit 0 allowed, exit 1 suppressed.
Sources and the key that governs them:
  scheduled_tick -> scheduled_ticks   (3-hourly daily_checkin cron tick, also when run by hand)
  event_wake     -> event_wakes       (news_watcher / opportunity_watch review requests)
  self_followup  -> self_followups    (operator_followup.sh delayed self-prompts)
  goal_set       -> goal_set          (goal_inject.sh set; "/goal clear" is never gated)
Anything else is allowed. Absent file or key = allowed (pre-2026-11-02 behaviour).
Legacy {"enabled": false} suppresses every gated source. An unreadable file
fails safe: only event_wake passes (urgent news must still wake the operator).
"""
import json
import sys
from pathlib import Path

KEYS = {"scheduled_tick": "scheduled_ticks", "event_wake": "event_wakes",
        "self_followup": "self_followups", "goal_set": "goal_set"}


def allowed(source: str, path: Path) -> bool:
    key = KEYS.get(source)
    if key is None:
        return True
    if not path.exists():
        return True
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise ValueError("not an object")
    except (OSError, ValueError):
        return source == "event_wake"
    if data.get("enabled") is False:
        return False
    return data.get(key, True) is not False


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[1]
    src = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.exit(0 if allowed(src, repo / "notes" / "operator_autoprompt.json") else 1)
