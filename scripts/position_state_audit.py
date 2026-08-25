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
import re
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

    # NOTE THE SHAPE: this file is a DICT {_purpose, _refreshed, positions:[...]},
    # not a list. The first version of this line iterated it directly, walked the
    # KEY STRINGS, filtered them all out and produced an EMPTY set — which made
    # every price trigger look orphaned. It was caught only because one of the two
    # flagged triggers (hormuz) was obviously live; had both been genuinely stale
    # the broken check would have printed the right answer by luck. Empty-collection
    # bug, fifth instance in this repo. Assert non-empty rather than trusting it.
    _snap = _load("position_condition_ids.json", {})
    _rows = _snap.get("positions", []) if isinstance(_snap, dict) else _snap
    live_assets = {str(p.get("asset")) for p in _rows
                   if isinstance(p, dict) and p.get("asset")}
    if not live_assets:
        issues.append("AUDIT DEGRADED — no live assets parsed from position_condition_ids.json; "
                      "orphan-trigger check SKIPPED (do not read its silence as clean)")

    # 2. armed triggers referencing closed positions (the ARB failure class)
    for t in _load("opportunity_triggers.json", []):
        if not t.get("actionable"):
            continue
        note = (t.get("note") or "").lower()
        key = t.get("key", "")
        # heuristic: an ACTIONABLE trigger whose note names no live slug and
        # says "add"/"re-entry" deserves a human look each audit
        # Word-boundary match (2026-08-10): the bare substring "add" also fires
        # on "added"/"address", so a trigger whose note merely NARRATES fee math
        # ("taker fees added 8.4pp") got flagged every tick. A recurring false
        # flag is worse than no flag — it trains me to skim the audit, which is
        # the wallpaper failure the criteria rotation was designed to avoid.
        if re.search(r"\b(add|adds|re-?entry|re-?enter)\b", key + " " + note):
            issues.append(f"TRIGGER armed+actionable — confirm still wanted: {key} "
                          f"({t.get('kind')} {t.get('op')} {t.get('level')})")
            continue
        # ORPHANED PRICE TRIGGER (2026-08-25). The check above matches triggers
        # whose TEXT says add/re-entry — which is NOT this file's stated
        # motivation ("a price trigger left armed after its position was sold").
        # Found the gap the honest way: gpt6-no-judgment sat armed and actionable
        # on a token whose position was exited 2026-08-18, and every audit since
        # printed CLEAN. A price trigger watches ONE token, so it is orphaned the
        # moment that token leaves the book; watch-class kinds (new_listing,
        # pair_arb, coingecko) are deliberately position-free and exempt.
        if live_assets and t.get("kind") in ("clob_bid", "clob_ask", "clob_no_ask"):
            tok = str(t.get("id") or "")
            if tok and tok not in live_assets:
                issues.append(f"TRIGGER ORPHANED — armed on a token with no live position "
                              f"(exited?): {key} ({t.get('kind')} {t.get('op')} "
                              f"{t.get('level')}) — disarm or document why it stays")

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
    # SECOND TRIGGER: STALE SOURCE behind a FRESH check (2026-08-13). The
    # rotation gated only on criteria_read age, and that is not where the risk
    # lives. SpaceX cost the project its largest prior correction today (p_yes
    # 0.95 -> 0.68) on an Anthropic valuation wrong by ~15x — while its
    # criteria_read was TWO DAYS old, so no age-based rotation would ever have
    # surfaced it. Measuring the book that day: 3 of 8 positions had a fresh
    # check sitting on a source older than 60 days (Greenland 203d, MacBook
    # 116d, SpaceX 66d). A position can be diligently re-read and still rest on
    # facts nobody has rechecked, because re-reading the CRITERIA is a different
    # act from re-verifying the FACTS. Fire on either.
    SOURCE_STALE_DAYS = 60
    stale_src_key, stale_src_age = None, 0
    for k, v in priors_raw.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        if not any(k in s or s in k for s in live):
            continue
        for f in (v.get("key_facts") or []):
            try:
                age = (dt.date.today() - dt.date.fromisoformat(f.get("source_date", ""))).days
            except Exception:
                continue
            if age > SOURCE_STALE_DAYS and age > stale_src_age:
                stale_src_key, stale_src_age = k, age
    if stale_src_key and stale_src_key != oldest_key:
        # Silenceable ONLY with a dated, expiring ack — same shape as
        # divergence_ack, and for the same reason. Some positions rest on old
        # sources because no newer reporting EXISTS (Greenland's freshest is
        # ~200d old however hard I search), so an unclearable alert would become
        # wallpaper within a week and take the useful fires down with it. The
        # ack records "I looked and there is nothing newer" WITH a date, so the
        # claim expires and gets re-tested rather than calcifying.
        SOURCE_ACK_DAYS = 21
        ack = (priors_raw.get(stale_src_key, {}) or {}).get("source_ack")
        acked = False
        if ack:
            try:
                acked = (dt.date.today() - dt.date.fromisoformat(ack)).days <= SOURCE_ACK_DAYS
            except Exception:
                acked = False
        if not acked:
            issues.append(
                f"STALE SOURCE behind a fresh check: {stale_src_key[:52]} rests on a fact whose "
                f"source is {stale_src_age}d old{' (ack EXPIRED)' if ack else ''} — criteria were "
                f"re-read recently, but re-reading CRITERIA is not re-verifying FACTS. Search for "
                f"NEWER reporting; do not re-read the source you already have (it cannot reveal "
                f"the one you don't). If nothing newer exists, set source_ack to today.")
    if oldest_key:
        never = oldest_date == "1970-01-01"
        try:
            age_days = (dt.date.today() - dt.date.fromisoformat(oldest_date)).days
        except Exception:
            age_days = 9999
        if never or age_days > CRITERIA_STALE_DAYS:
            age = "NEVER" if never else f"{age_days}d ago"
            msg = [f"CRITERIA RE-READ due (read {age}): {oldest_key[:52]} — "
                   f"pull the market description, confirm the recorded thesis still matches "
                   f"the actual bar, then set criteria_read to today"]
            # SOURCE-DIFF (2026-08-11). Re-reading my own note is confirmation,
            # not verification: the MacBook prior survived TWO re-verifications
            # with an INVERTED anchor direction because each pass re-read the
            # note and reproduced the error. Both of that week's real catches
            # (this, and the HLE "frozen board" inference) came from fetching
            # the primary source and diffing it against what the note CLAIMED
            # the source said. So the rotation now names the claims to diff.
            # A claim is only diffable against a FETCHABLE artifact. Sources
            # like "coverage sweep" cannot be re-read, so a "verification"
            # against one is just my own memory agreeing with itself — the
            # failure this rotation exists to stop. Mark them so the weakest
            # claims are visibly the ones to fix first (2026-08-11: 3 of the
            # first 8 key_facts were written with unfetchable sources).
            for f in (priors_raw.get(oldest_key, {}).get("key_facts") or []):
                src = f.get("source", "?")
                tag = "URL" if src.startswith("http") else "NO FETCHABLE SOURCE — treat as UNVERIFIED"
                # SOURCE AGE, not just check age (2026-08-12). `checked` is when I
                # last LOOKED; `source_date` is when the source was PUBLISHED, and
                # the MacBook prior cost 18pp because those diverged invisibly:
                # checked 1 day ago, published 114 days earlier, in a story that had
                # moved three times since. Re-reading the article I have can never
                # reveal the article I do not. Emphasis (not a separate alert) once
                # the source passes SOURCE_OLD_DAYS — the prompt is to go hunting for
                # a NEWER source, which is a different action from re-reading.
                SOURCE_OLD_DAYS = 60
                sd = f.get("source_date", "unknown")
                age_txt = ""
                try:
                    sage = (dt.date.today() - dt.date.fromisoformat(sd)).days
                    age_txt = (f", source published {sage}d ago"
                               + ("  <<< STALE SOURCE — search for a NEWER one, do not re-read this"
                                  if sage > SOURCE_OLD_DAYS else ""))
                except Exception:
                    age_txt = ", source date UNKNOWN — record one"
                msg.append(f"    SOURCE-DIFF [{tag}] vs {src} (checked {f.get('checked','?')}{age_txt}):")
                msg.append(f"      \"{f.get('claim','')[:150]}\"")
            if len(msg) > 1:
                msg.append("    -> fetch the source and compare its ACTUAL words to the claim above; "
                           "a revision must record what the source said BEFORE and what it says NOW.")
            issues.append("\n".join(msg))

    # 3c. PRIOR-vs-MARK divergence (2026-08-10). The criteria rotation above
    # checks whether a thesis still matches the market's TEXT; nothing checked
    # whether the NUMBER still matches the market's PRICE. On 2026-08-10 the
    # Gemini-HLE prior read p_no 0.70 against a 0.10 mark — a 60pp claimed edge
    # I had carried for 8 days without buying a share. That state is incoherent
    # by construction: either the prior is fantasy, or it is the best trade in
    # the book and I am ignoring it. Both cannot be true, and neither resolves
    # itself by sitting there.
    #
    # A large gap is NOT automatically wrong — deliberate disagreement with a
    # market is the entire job. So the flag is silenceable, but only with a
    # DATE: set "divergence_ack" on the prior when the gap is intentional and
    # reviewed. Acks expire, which forces the disagreement back up for air
    # instead of letting it calcify into a number nobody re-derives.
    DIVERGENCE_PP = 0.25
    DIVERGENCE_ACK_DAYS = 14
    posmap = {p["slug"]: p for p in pos}
    for k, v in priors_raw.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        slug = next((s for s in live if k in s or s in k), None)
        if not slug:
            continue
        rec = posmap.get(slug) or {}
        held = (rec.get("outcome") or "").lower()
        mark = rec.get("curPrice")
        if mark is None or held not in ("yes", "no"):
            continue
        if f"p_{held}" in v:
            mine = float(v[f"p_{held}"])
        elif "p_no" in v:
            mine = 1.0 - float(v["p_no"])
        elif "p_yes" in v:
            mine = 1.0 - float(v["p_yes"])
        else:
            continue
        gap = mine - float(mark)
        if abs(gap) < DIVERGENCE_PP:
            continue
        ack = v.get("divergence_ack")
        if ack:
            try:
                if (dt.date.today() - dt.date.fromisoformat(ack)).days <= DIVERGENCE_ACK_DAYS:
                    continue
            except Exception:
                pass
        stale = f" (ack {ack} EXPIRED)" if ack else ""
        verb = ("market is CHEAPER than my number — size up or admit the prior is wrong"
                if gap > 0 else
                "market pays MORE than my number — trim or admit the prior is wrong")
        issues.append(
            f"PRIOR-vs-MARK {abs(gap)*100:.0f}pp on {slug[:44]}{stale}: "
            f"I hold {held.upper()} at mark {float(mark):.3f}, my prior says {mine:.2f} — {verb}. "
            f"Resolve by trading, re-deriving the prior, or setting divergence_ack to today.")

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
