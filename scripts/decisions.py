"""Decision-quality tracker for polyclaude.

Records every non-trivial decision (trade open/close, strategy-class change,
scaffolding choice) as a structured entry. Outcomes get filled in
retrospectively. Aggregated calibration data tells us where reasoning is
weak — overconfident on which market types, underconfident on which
catalysts, etc.

Calibration is a DEBUGGING BYPRODUCT, not the objective (operator directive
2026-05-14: the only goal is ROI; treating calibration as the product is
Goodhart's law). Record deltas; use them only when they reveal a systematic
bias worth fixing. P&L — not calibration — is the scorecard.

Storage: `notes/decisions.json` (structured, machine-readable). The cron
tick reads this file to (a) propose retrospective updates on resolved
decisions and (b) flag patterns of mis-calibration in the weekly report.

CLI:
    python scripts/decisions.py add --type open_position --thesis "..." --confidence high --prediction "..." --size 7
    python scripts/decisions.py list [--unresolved] [--type open_position]
    python scripts/decisions.py update <id> --outcome "..." --calibration-delta "..." [--lesson "..."]
    python scripts/decisions.py summary
    python scripts/decisions.py pending  # list decisions whose resolution date has passed without an outcome
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import _paths as _secrets

_secrets.install_scrubbing_excepthook()


_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
DECISIONS_PATH = _REPO_ROOT / "notes" / "decisions.json"


VALID_TYPES = {
    "open_position",     # opening any new position (Polymarket/Ostium/etc.)
    "close_position",    # closing an existing position
    "size_change",       # adjusting an existing position's size
    "strategy_change",   # entering / exiting a strategy class (e.g., "started Ostium")
    "scaffolding",       # building a system capability (a script, an audit, a process change)
    "skip",              # explicitly NOT taking an action that was considered
}

VALID_CONFIDENCE = {"low", "medium", "high"}


def _load() -> dict:
    if not DECISIONS_PATH.exists():
        return {"next_id": 1, "decisions": []}
    return json.loads(DECISIONS_PATH.read_text())


def _save(d: dict) -> None:
    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECISIONS_PATH.write_text(json.dumps(d, indent=2, default=str))


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cmd_add(args: argparse.Namespace) -> int:
    if args.type not in VALID_TYPES:
        print(f"invalid --type {args.type!r}; valid: {sorted(VALID_TYPES)}")
        return 2
    if args.confidence not in VALID_CONFIDENCE:
        print(f"invalid --confidence {args.confidence!r}; valid: {sorted(VALID_CONFIDENCE)}")
        return 2

    store = _load()
    rows = store.get("decisions")
    if not isinstance(rows, list):
        print("invalid decision store: 'decisions' must be a list")
        return 2
    if any(not isinstance(row, dict) for row in rows):
        print("invalid decision store: every decision must be an object")
        return 2
    ids = [row.get("id") for row in rows]
    if any(type(decision_id) is not int for decision_id in ids):
        print("invalid decision store: every decision must have an integer id")
        return 2
    if len(ids) != len(set(ids)):
        print("invalid decision store: duplicate decision ids; refusing to append")
        return 2
    # `next_id` is a cache, not authority.  Auto-logged decisions can land
    # without advancing it, so trusting the cached value reused DEC-0095 on
    # 2026-08-29.  Derive a monotone floor from the actual ledger every time.
    cached_next = store.get("next_id", 1)
    if type(cached_next) is not int:
        print("invalid decision store: next_id must be an integer")
        return 2
    next_id = max(cached_next, max(ids, default=0) + 1)
    decision = {
        "id": next_id,
        "timestamp": _now_utc(),
        "type": args.type,
        "thesis": args.thesis,
        "confidence": args.confidence,
        "prediction": args.prediction,
        "size_usd": args.size,
        "resolution_at": args.resolution_at,
        "tags": args.tags or [],
        "slug": getattr(args, "slug", None),
        "outcome": None,
        "calibration_delta": None,
        "lesson": None,
    }
    TRADE_TYPES = {"open_position", "size_change", "close_position"}
    if args.type in TRADE_TYPES and not decision["slug"]:
        print("WARNING: no --slug on a trade decision. It will need manual identification "
              "to grade; see notes/shortdated_ledger.json's _schema for why that fails.")
    rows.append(decision)
    store["next_id"] = next_id + 1
    _save(store)
    print(f"DEC-{decision['id']:04d} added")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = _load()
    rows = store["decisions"]
    if args.type:
        rows = [r for r in rows if r["type"] == args.type]
    if args.unresolved:
        rows = [r for r in rows if r.get("outcome") is None]
    if args.tag:
        rows = [r for r in rows if args.tag in (r.get("tags") or [])]

    if not rows:
        print("(none)")
        return 0
    for r in rows[-args.limit:]:
        status = "PENDING" if r.get("outcome") is None else "RESOLVED"
        # confidence/prediction are absent on auto-logged records (polyclaude_enter /
        # infra path) and size lives under 'usd' there, not 'size_usd'. Guard all of
        # them so `list` never dies mid-review (summary was fixed 2026-06-05; list
        # had the same KeyError until 2026-06-23).
        conf = r.get("confidence") or "unknown"
        size = r.get("size_usd") or r.get("usd") or 0
        print(f"DEC-{r['id']:04d}  {r['timestamp'][:10]}  {r['type']:18s}  {conf:6s}  ${size:>6.2f}  [{status}]")
        if r.get("thesis"):
            print(f"  thesis:     {r['thesis']}")
        if r.get("prediction"):
            print(f"  prediction: {r['prediction']}")
        if r.get("outcome"):
            print(f"  outcome:    {r['outcome']}")
        if r.get("calibration_delta"):
            print(f"  delta:      {r['calibration_delta']}")
        if r.get("lesson"):
            print(f"  lesson:     {r['lesson']}")
        print()
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    store = _load()
    target = next((r for r in store["decisions"] if r["id"] == args.id), None)
    if not target:
        print(f"DEC-{args.id:04d} not found")
        return 2
    if args.outcome is not None:
        target["outcome"] = args.outcome
        target["resolved_at"] = _now_utc()
    if args.calibration_delta is not None:
        target["calibration_delta"] = args.calibration_delta
    if args.lesson is not None:
        target["lesson"] = args.lesson
    _save(store)
    print(f"DEC-{args.id:04d} updated")
    return 0


def cmd_summary(_args: argparse.Namespace) -> int:
    store = _load()
    rows = store["decisions"]
    total = len(rows)
    resolved = [r for r in rows if r.get("outcome")]
    pending = [r for r in rows if not r.get("outcome")]

    print(f"decisions total={total}  resolved={len(resolved)}  pending={len(pending)}")

    # by type
    print("\nby type:")
    by_type: dict[str, list] = {}
    for r in rows:
        by_type.setdefault(r.get("type") or "unknown", []).append(r)
    for t, lst in sorted(by_type.items(), key=lambda x: -len(x[1])):
        n_res = sum(1 for r in lst if r.get("outcome"))
        print(f"  {t:18s}  total={len(lst):3d}  resolved={n_res:3d}")

    # by confidence
    print("\nby confidence:")
    by_conf: dict[str, list] = {}
    for r in rows:
        by_conf.setdefault(r.get("confidence") or "unknown", []).append(r)
    order = ["high", "medium", "low"] + sorted(k for k in by_conf if k not in ("high", "medium", "low"))
    for c in order:
        lst = by_conf.get(c, [])
        n_res = sum(1 for r in lst if r.get("outcome"))
        print(f"  {c:8s}  total={len(lst):3d}  resolved={n_res:3d}")

    # capital-weighted exposure of pending decisions
    pending_capital = sum((r.get("size_usd") or 0) for r in pending)
    print(f"\npending capital (sum of sizes): ${pending_capital:.2f}")

    # lessons recorded
    lessons = [r["lesson"] for r in rows if r.get("lesson")]
    if lessons:
        print(f"\nlessons recorded: {len(lessons)}")
        for l in lessons[-5:]:
            print(f"  • {l}")

    return 0


def cmd_pending(_args: argparse.Namespace) -> int:
    """List decisions whose stated resolution date has passed without an outcome."""
    store = _load()
    today = dt.datetime.now(dt.timezone.utc).date()
    overdue = []
    for r in store["decisions"]:
        if r.get("outcome"):
            continue
        rd = r.get("resolution_at")
        if not rd:
            continue
        try:
            rd_date = dt.datetime.fromisoformat(rd).date()
        except ValueError:
            continue
        if rd_date < today:
            overdue.append((r, (today - rd_date).days))
    if not overdue:
        print("(no overdue decisions)")
        return 0
    overdue.sort(key=lambda x: -x[1])
    for r, days in overdue:
        print(f"DEC-{r['id']:04d}  resolution_at={r.get('resolution_at')}  ({days} days overdue)")
        print(f"  {r.get('thesis') or '(no thesis recorded)'}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add", help="record a new decision")
    s.add_argument("--type", required=True, help=f"one of: {sorted(VALID_TYPES)}")
    s.add_argument("--thesis", required=True, help="one-paragraph rationale")
    s.add_argument("--confidence", required=True, choices=sorted(VALID_CONFIDENCE))
    s.add_argument("--prediction", required=True,
                   help="testable prediction; what should be true if the thesis holds")
    s.add_argument("--size", type=float, default=0.0,
                   help="capital at risk in USD (0 for non-trade decisions)")
    s.add_argument("--resolution-at", default=None,
                   help="ISO date when outcome should be evaluable (YYYY-MM-DD)")
    s.add_argument("--tags", nargs="*", default=None)
    # MARKET IDENTIFIER (2026-08-13). Trade decisions carried no reliable way to
    # name the market: only 2 of 60 had a token_id and none had a slug. That is
    # the same defect that left shortdated_ledger two-thirds ungraded for months
    # — grading requires identifying the market, and attempting it from prose
    # produced FALSE resolutions (a market that had not reached its date came
    # back "resolved"). It has not bitten here yet only because nothing is
    # overdue; 29 ungraded decisions resolve around Dec-31 and ARE the evidence
    # for the operator's January review. Cheap now, painful in January.
    s.add_argument("--slug", default=None,
                   help="Polymarket market slug — REQUIRED for trade types "
                        "(open_position/size_change/close_position) so the outcome can be "
                        "graded later without guessing which market it was.")
    s.set_defaults(fn=cmd_add)

    s = sub.add_parser("list", help="show decisions")
    s.add_argument("--type", default=None)
    s.add_argument("--unresolved", action="store_true")
    s.add_argument("--tag", default=None)
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_list)

    s = sub.add_parser("update", help="fill in outcome / calibration / lesson")
    s.add_argument("id", type=int)
    s.add_argument("--outcome", default=None)
    s.add_argument("--calibration-delta", default=None,
                   help="how prediction vs outcome diverged (e.g., 'overconfident; price moved 4%% not 1%%')")
    s.add_argument("--lesson", default=None)
    s.set_defaults(fn=cmd_update)

    s = sub.add_parser("summary", help="aggregate stats")
    s.set_defaults(fn=cmd_summary)

    s = sub.add_parser("pending", help="list decisions overdue for outcome")
    s.set_defaults(fn=cmd_pending)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
