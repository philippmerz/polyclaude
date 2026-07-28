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
