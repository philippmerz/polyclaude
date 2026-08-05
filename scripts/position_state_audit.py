#!/usr/bin/env python3
"""Audit every position-referencing state file against the LIVE book.

Motivation (2026-07-28): a price trigger left armed after its position was sold
fired every 5 minutes for hours — telegramming the operator and burning ticks on
an add I'd already decided against. Root class: **state files drift out of sync
with the book when positions open/close/resize**, and nothing checks. Files:

  notes/opportunity_triggers.json    armed price triggers (the ARB failure)
  notes/position_condition_ids.json  redemption claim-insurance snapshot
  notes/portfolio_kelly_priors.json  per-position P(win) priors
  notes/acknowledged_holds.json      deliberate hold acknowledgements (expiring)
  notes/resting_orders.md            resting-order tracker (line-count sanity only)

`--fix` refreshes the conditionId snapshot and drops expired acked-holds; the
judgment items (orphan priors, armed triggers) are REPORTED, never auto-removed —
an orphan prior may be a re-entry candidate worth keeping.

CLI: position_state_audit.py [--fix]   (exit 1 if any issue found)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
NOTES = REPO / "notes"
ADDR = "0x9032ad983ee5a22bfd078ecc4fd3d4d69e57267b"


def _live_positions() -> list[dict]:
    r = httpx.get("https://data-api.polymarket.com/positions",
                  params={"user": ADDR, "limit": "100"}, timeout=25)
    return [p for p in r.json() if float(p.get("size", 0)) > 0.5]


def _load(name: str, default):
    try:
        return json.loads((NOTES / name).read_text())
    except Exception:
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true",
                    help="refresh conditionId snapshot + drop expired acked-holds")
    args = ap.parse_args()

    pos = _live_positions()
    live = {p["slug"]: float(p["size"]) for p in pos}
    issues: list[str] = []

    # 1. conditionId snapshot (claim insurance — must cover every open position)
    snap = _load("position_condition_ids.json", {"positions": []})
    snapmap = {r["slug"]: float(r.get("size", 0)) for r in snap.get("positions", [])}
    for s in snapmap:
        if s not in live:
            issues.append(f"SNAPSHOT stale (position closed): {s[:52]}")
    for s in live:
        if s not in snapmap:
            issues.append(f"SNAPSHOT missing (no claim insurance!): {s[:52]}")
        elif abs(snapmap[s] - live[s]) > 0.5:
            issues.append(f"SNAPSHOT size drift: {s[:44]} {snapmap[s]:g} vs live {live[s]:g}")

    # 2. armed triggers referencing closed positions (the ARB failure class)
    for t in _load("opportunity_triggers.json", []):
        if not t.get("actionable"):
            continue
        note = (t.get("note") or "").lower()
        key = t.get("key", "")
        # heuristic: an ACTIONABLE trigger whose note names no live slug and
        # says "add"/"re-entry" deserves a human look each audit
        if any(w in (key + note) for w in ("add", "re-entry", "reentry")):
            issues.append(f"TRIGGER armed+actionable — confirm still wanted: {key} "
                          f"({t.get('kind')} {t.get('op')} {t.get('level')})")

    # 3. orphan priors (position gone — keep only if a deliberate re-entry candidate)
    for k, v in _load("portfolio_kelly_priors.json", {}).items():
        if k.startswith("_"):
            continue
        if not any(k in s or s in k for s in live):
            note = (v.get("note", "") if isinstance(v, dict) else "")
            if "closed" not in note.lower() and "re-entry" not in note.lower():
                issues.append(f"PRIOR orphan (no live position, no closure note): {k[:52]}")

    # 3b. CRITERIA RE-READ rotation (2026-08-05). Staleness guards watch the
    # `verified` DATE, not whether the recorded thesis is still CORRECT — and
    # an audit that day found 2 of 8 positions running on wrong/stale facts
    # (SpaceX's prior carried a "$2.1T day-one bar" when the IPO had already
    # happened at ~$1.75T; GPT-6's thesis assumed a naming crux the criteria
    # do not require). Neither was flagged by anything automated. So: surface
    # the LIVE position whose criteria were read longest ago, one per tick —
    # round-robin means every position gets re-read within ~a week.
    priors_raw = _load("portfolio_kelly_priors.json", {})
    oldest_key, oldest_date = None, None
    for k, v in priors_raw.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        if not any(k in s or s in k for s in live):
            continue
        cr = v.get("criteria_read") or "1970-01-01"
        if oldest_date is None or cr < oldest_date:
            oldest_key, oldest_date = k, cr
    # Threshold, not just "oldest" (2026-08-05): flagging the oldest EVERY tick
    # makes the flag wallpaper once all positions are current — the same
    # reporting-vs-action gap that made the Kelly over-sized flag ignorable.
    # Only surface a genuinely stale one (>7d), so the flag always means act.
    CRITERIA_STALE_DAYS = 7
    if oldest_key:
        never = oldest_date == "1970-01-01"
        try:
            age_days = (dt.date.today() - dt.date.fromisoformat(oldest_date)).days
        except Exception:
            age_days = 9999
        if never or age_days > CRITERIA_STALE_DAYS:
            age = "NEVER" if never else f"{age_days}d ago"
            issues.append(
                f"CRITERIA RE-READ due (read {age}): {oldest_key[:52]} — "
                f"pull the market description, confirm the recorded thesis still matches "
                f"the actual bar, then set criteria_read to today")

    # 4. expired acked-holds
    today = dt.date.today().isoformat()
    acks = _load("acknowledged_holds.json", [])
    fresh_acks = []
    for a in acks:
        expired = str(a.get("until", "")) < today
        gone = not any(a.get("slug", "") in s or s in a.get("slug", "") for s in live)
        if expired or gone:
            issues.append(f"ACKED-HOLD stale ({'expired' if expired else 'position gone'}): "
                          f"{a.get('slug','')[:48]}")
        else:
            fresh_acks.append(a)

    if args.fix:
        rows = [{"slug": p["slug"], "outcome": p["outcome"], "size": p["size"],
                 "conditionId": p.get("conditionId"), "asset": p.get("asset"),
                 "negativeRisk": p.get("negativeRisk")} for p in pos]
        (NOTES / "position_condition_ids.json").write_text(json.dumps(
            {"_purpose": "Claim insurance: de-index-during-resolution is a known failure "
                         "(Mojtaba, Marvel) — redemption must never depend on data-api indexing. "
                         "Refreshed by position_state_audit.py --fix.",
             "_refreshed": today, "positions": rows}, indent=1) + "\n")
        (NOTES / "acknowledged_holds.json").write_text(json.dumps(fresh_acks, indent=1) + "\n")
        print(f"FIXED: snapshot refreshed ({len(rows)} positions), "
              f"acked-holds pruned ({len(acks) - len(fresh_acks)} dropped)")

    if issues:
        print(f"\n{len(issues)} state issue(s):")
        for i in issues:
            print(f"  - {i}")
        print("\n(judgment items — triggers/priors — are reported, never auto-removed)")
        return 1
    print(f"position state CLEAN ({len(live)} live positions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
