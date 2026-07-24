#!/usr/bin/env python3
"""Brier/log-loss calibration over notes/shortdated_ledger.json.

THE calibration measure (operator 2026-07-21: a single binary settling 1-or-0
is NOT a calibration test — the ledger of many scored calls is). Two modes:

  resolve  — backfill `outcome` for records whose market has resolved on gamma
             (match by normalized question text; only fills nulls; ambiguous or
             unresolved stay null and are reported).
  score    — Brier + log-loss of catalyst_p_yes_central vs realized outcome,
             against the MARKET baseline implied by (side, ask) at record time.
             Positive skill (market_brier − my_brier) = beating the market.

Records without catalyst_p_yes_central or a clean YES/NO outcome are excluded
from scoring (studies, pre-gate skips) and counted separately.
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import sys
from pathlib import Path

import httpx

LEDGER = Path(__file__).resolve().parent.parent / "notes" / "shortdated_ledger.json"
GAMMA = "https://gamma-api.polymarket.com/markets"


def _norm(q: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (q or "").lower()).strip()


def _load() -> list:
    data = json.loads(LEDGER.read_text())
    return data if isinstance(data, list) else data.get("records", [])


def _market_p_yes(rec: dict) -> float | None:
    """Market-implied P(YES) at record time from (side, ask)."""
    ask, side = rec.get("ask"), rec.get("side")
    if ask is None or side not in ("YES", "NO"):
        return None
    return float(ask) if side == "YES" else 1.0 - float(ask)


def cmd_resolve(args) -> int:
    recs = _load()
    filled = ambiguous = unresolved = 0
    for r in recs:
        if r.get("outcome") is not None or not r.get("question"):
            continue
        if r.get("side") not in ("YES", "NO"):
            continue  # study rows
        try:
            sr = httpx.get("https://gamma-api.polymarket.com/public-search",
                           params={"q": r["question"], "limit_per_type": 10},
                           timeout=20).json()
            cands = [m for e in (sr.get("events") or []) for m in (e.get("markets") or [])]
        except Exception as e:
            print(f"  fetch failed for {r['question'][:50]!r}: {e}", file=sys.stderr)
            continue
        best, best_ratio = None, 0.0
        for m in cands:
            ratio = difflib.SequenceMatcher(
                None, _norm(r["question"]), _norm(m.get("question", ""))).ratio()
            if ratio > best_ratio:
                best, best_ratio = m, ratio
        # By-date siblings ("by August 31" vs "by August 21") differ by ONE char
        # (ratio ~0.98) — similarity alone WILL mis-match them. Require the
        # date-ish tokens (numbers + month names) to be exactly equal too.
        def _datetoks(q: str) -> list:
            return sorted(re.findall(
                r"\b(?:\d+|january|february|march|april|may|june|july|august|"
                r"september|october|november|december)\b", _norm(q)))
        if (not best or best_ratio < 0.88
                or _datetoks(r["question"]) != _datetoks(best.get("question", ""))):
            ambiguous += 1
            print(f"  no confident match ({best_ratio:.2f}): {r['question'][:60]}")
            continue
        try:
            prices = json.loads(best.get("outcomePrices") or "[]")
            p_yes_final = float(prices[0])
        except Exception:
            unresolved += 1
            continue
        if p_yes_final not in (0.0, 1.0):
            unresolved += 1
            print(f"  matched but not settled ({p_yes_final}): {r['question'][:60]}")
            continue
        r["outcome"] = "YES" if p_yes_final == 1.0 else "NO"
        filled += 1
        print(f"  RESOLVED {r['outcome']}: {r['question'][:60]}")
    if filled and not args.dry_run:
        LEDGER.write_text(json.dumps(recs, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {LEDGER.name}")
    print(f"resolve: {filled} filled, {ambiguous} no-match, {unresolved} not-settled")
    return 0


def cmd_score(_args) -> int:
    recs = _load()
    rows, excluded, pending = [], 0, 0
    for r in recs:
        p = r.get("catalyst_p_yes_central")
        out = r.get("outcome")
        out_clean = out if out in ("YES", "NO") else (
            "NO" if isinstance(out, str) and out.startswith("PENDING-NO") else None)
        if p is None or _market_p_yes(r) is None:
            excluded += 1
            continue
        if out_clean is None:
            pending += 1
            continue
        y = 1.0 if out_clean == "YES" else 0.0
        mp = _market_p_yes(r)
        eps = 1e-6
        rows.append({
            "q": r["question"][:48], "date": r["date"], "my_p": p, "mkt_p": mp, "y": y,
            "brier_my": (p - y) ** 2, "brier_mkt": (mp - y) ** 2,
            "ll_my": -(y * math.log(max(p, eps)) + (1 - y) * math.log(max(1 - p, eps))),
            "ll_mkt": -(y * math.log(max(mp, eps)) + (1 - y) * math.log(max(1 - mp, eps))),
        })
    if not rows:
        print(f"scored 0 (pending {pending}, excluded {excluded}) — nothing resolvable yet")
        return 0
    n = len(rows)
    print(f"{'date':<11}{'my_p':>6}{'mkt_p':>7}{'out':>4}{'Bmy':>7}{'Bmkt':>7}  question")
    for r in rows:
        print(f"{r['date']:<11}{r['my_p']:>6.2f}{r['mkt_p']:>7.2f}{int(r['y']):>4}"
              f"{r['brier_my']:>7.3f}{r['brier_mkt']:>7.3f}  {r['q']}")
    bm = sum(r["brier_my"] for r in rows) / n
    bk = sum(r["brier_mkt"] for r in rows) / n
    lm = sum(r["ll_my"] for r in rows) / n
    lk = sum(r["ll_mkt"] for r in rows) / n
    print(f"\nN={n} scored ({pending} pending, {excluded} excluded/study)")
    print(f"Brier    mine {bm:.4f}  vs market {bk:.4f}  → skill {bk - bm:+.4f} "
          f"({'BEATING' if bk > bm else 'LOSING TO'} market)")
    print(f"Log-loss mine {lm:.4f}  vs market {lk:.4f}  → skill {lk - lm:+.4f}")
    print("NOTE: N < ~30 is too small for a verdict — this is the accumulating measure, "
          "not a proof either way.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve", help="backfill outcomes from gamma for resolved markets")
    r.add_argument("--dry-run", action="store_true")
    sub.add_parser("score", help="Brier/log-loss vs market baseline")
    args = ap.parse_args()
    return cmd_resolve(args) if args.cmd == "resolve" else cmd_score(args)


if __name__ == "__main__":
    sys.exit(main())
