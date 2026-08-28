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

CLI: position_state_audit.py [--fix]   (exit 1 for state issues, 2 if live data is unavailable)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import time
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
NOTES = REPO / "notes"
ADDR = "0x9032ad983ee5a22bfd078ecc4fd3d4d69e57267b"
MIN_LIVE_SHARES = 0.5
SET_SIZE_TOLERANCE = 0.01
POSITIONS_URL = "https://data-api.polymarket.com/positions"
POSITION_FETCH_ATTEMPTS = 3
POSITION_RETRY_BASE_SECONDS = 0.5
POSITION_RETRY_MAX_SECONDS = 2.0
SHORT_DATED_WINDOW_DAYS = 30


class LivePositionsUnavailable(RuntimeError):
    """Raised when the live book cannot be read and the audit must stop."""


def _position_retry_delay(response: httpx.Response | None, attempt: int) -> float:
    """Return a short bounded backoff, respecting numeric Retry-After hints."""
    retry_after = None
    if response is not None:
        retry_after = response.headers.get("Retry-After")
    if retry_after is not None:
        try:
            return min(POSITION_RETRY_MAX_SECONDS, max(0.0, float(retry_after)))
        except ValueError:
            pass
    return min(
        POSITION_RETRY_MAX_SECONDS,
        POSITION_RETRY_BASE_SECONDS * (2 ** (attempt - 1)),
    )


def _live_positions() -> list[dict]:
    """Fetch and validate the live position list, retrying transient failures.

    This is a safety input: an unavailable or malformed response must never be
    interpreted as an empty book.  In particular, data-api rate-limit payloads
    have appeared as JSON strings, which previously reached ``p.get`` and
    crashed with an opaque ``AttributeError``.
    """
    last_error = "unknown error"
    attempts_used = 0

    for attempt in range(1, POSITION_FETCH_ATTEMPTS + 1):
        attempts_used = attempt
        response: httpx.Response | None = None
        retryable = True
        try:
            response = httpx.get(
                POSITIONS_URL,
                params={"user": ADDR, "limit": "100"},
                timeout=25,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError(
                    f"unexpected JSON shape ({type(payload).__name__}, expected list)"
                )

            live: list[dict] = []
            for index, position in enumerate(payload):
                if not isinstance(position, dict):
                    raise ValueError(
                        f"position row {index} has type {type(position).__name__}, "
                        "expected object"
                    )
                try:
                    size = float(position.get("size", 0))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"position row {index} has invalid size") from exc
                if not math.isfinite(size) or size < 0:
                    raise ValueError(f"position row {index} has invalid size")
                if size > MIN_LIVE_SHARES:
                    slug = position.get("slug")
                    if not isinstance(slug, str) or not slug.strip():
                        raise ValueError(
                            f"live position row {index} has missing/invalid slug"
                        )
                    outcome = position.get("outcome")
                    if not isinstance(outcome, str) or not outcome.strip():
                        raise ValueError(
                            f"live position row {index} has missing/invalid outcome"
                        )
                    mark = position.get("curPrice")
                    if mark is not None:
                        try:
                            mark_value = float(mark)
                        except (TypeError, ValueError) as exc:
                            raise ValueError(
                                f"live position row {index} has invalid curPrice"
                            ) from exc
                        if not math.isfinite(mark_value) or not 0 <= mark_value <= 1:
                            raise ValueError(
                                f"live position row {index} has invalid curPrice"
                            )
                    live.append(position)
            return live
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            last_error = f"HTTP {status}"
            retryable = status == 429 or 500 <= status < 600
        except httpx.RequestError as exc:
            last_error = type(exc).__name__
        except (TypeError, ValueError) as exc:
            # A gateway/CDN can return a successful HTTP status with an error
            # payload. Retry briefly, but never treat that payload as no book.
            last_error = str(exc)

        if not retryable or attempt == POSITION_FETCH_ATTEMPTS:
            break
        time.sleep(_position_retry_delay(response, attempt))

    noun = "attempt" if attempts_used == 1 else "attempts"
    raise LivePositionsUnavailable(
        f"data-api positions unavailable after {attempts_used} {noun} ({last_error})"
    )


def _load(name: str, default):
    try:
        return json.loads((NOTES / name).read_text())
    except Exception:
        return default


def set_only_issues(
    priors: dict,
    positions: list[dict],
    *,
    size_tolerance: float = SET_SIZE_TOLERANCE,
) -> list[str]:
    """Return hard alerts for incomplete or imbalanced ``set_only`` groups.

    A set-only position has economic meaning only at the group level.  The
    shared, non-empty ``set_only`` value is its identity and every prior carrying
    that value is an expected leg.  Exact slugs are deliberate here: fuzzy slug
    matching is acceptable for advisory prior lookup, but it can silently map
    the wrong contract in a safety invariant.

    ``arb_paired`` is intentionally not folded into this check.  Legacy
    monotonicity structures can contain overlapping pairs and directional
    crumbs, so their total live sizes need not be equal.  They require an
    explicit topology/quantity model rather than pretending they are sets.
    """
    issues: list[str] = []
    groups: dict[str, list[str]] = {}

    if not isinstance(priors, dict):
        return ["SET_BROKEN configuration unreadable: portfolio priors are not an object"]

    for slug, prior in priors.items():
        if str(slug).startswith("_") or not isinstance(prior, dict):
            continue
        if "set_only" not in prior:
            continue
        label = prior.get("set_only")
        if not isinstance(label, str) or not label.strip():
            issues.append(
                f"SET_BROKEN malformed set_only label on {str(slug)[:60]}"
            )
            continue
        groups.setdefault(label.strip(), []).append(str(slug))

    # Retain rows rather than collapsing to a dict.  Duplicate live rows for an
    # expected slug are ambiguous (for example both outcomes held) and must not
    # be made to look healthy by last-write-wins behaviour.
    live_by_slug: dict[str, list[float]] = {}
    for position in positions:
        if not isinstance(position, dict) or not position.get("slug"):
            continue
        try:
            size = float(position.get("size", 0))
        except (TypeError, ValueError):
            continue
        if size > MIN_LIVE_SHARES:
            live_by_slug.setdefault(str(position["slug"]), []).append(size)

    for label, expected_slugs in groups.items():
        label_display = label if len(label) <= 80 else label[:77] + "..."
        if len(expected_slugs) < 2:
            issues.append(
                f"SET_BROKEN {label_display}: only one configured leg; "
                "a set requires at least two"
            )
            continue

        missing = [slug for slug in expected_slugs if slug not in live_by_slug]
        ambiguous = [
            slug for slug in expected_slugs if len(live_by_slug.get(slug, [])) > 1
        ]
        if missing or ambiguous:
            details = []
            if missing:
                details.append("missing " + ", ".join(missing))
            if ambiguous:
                details.append("ambiguous duplicate live rows " + ", ".join(ambiguous))
            issues.append(f"SET_BROKEN {label_display}: {'; '.join(details)}")
            continue

        sizes = {slug: live_by_slug[slug][0] for slug in expected_slugs}
        # One nanoshare of comparison slack prevents binary representation of
        # the decimal API values from making the exact tolerance boundary fail.
        if max(sizes.values()) - min(sizes.values()) > size_tolerance + 1e-9:
            size_text = ", ".join(
                f"{slug}={size:g}" for slug, size in sizes.items()
            )
            issues.append(
                f"SET_BROKEN {label_display}: unequal live shares "
                f"(tolerance {size_tolerance:g}): {size_text}"
            )

    return issues


def _iso_date(value: object) -> dt.date | None:
    """Parse a date or ISO datetime without guessing malformed values."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        if "T" in text:
            return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        return dt.date.fromisoformat(text)
    except ValueError:
        return None


def _matching_prior(priors: dict, slug: str) -> tuple[str, dict] | None:
    exact = priors.get(slug)
    if isinstance(exact, dict):
        return slug, exact
    for key, prior in priors.items():
        if str(key).startswith("_") or not isinstance(prior, dict):
            continue
        if str(key) in slug or slug in str(key):
            return str(key), prior
    return None


def short_dated_prior_issues(
    priors: dict,
    positions: list[dict],
    *,
    today: dt.date | None = None,
) -> list[str]:
    """Require a same-day prior re-derivation inside the final 30 days.

    The backlog's build gate is specifically about by-date priors becoming
    stale through passage of time.  ``verified`` has day precision, so the
    lowest-noise enforceable version of "every tick" is once per UTC date:
    later ticks on a freshly reviewed date remain silent.  Equal-share
    ``set_only`` legs are collapsed into one economic-position diagnostic.
    """
    if not isinstance(priors, dict):
        return [
            "SHORT-DATED PRIOR CHECK DEGRADED — portfolio priors are unreadable; "
            "cannot verify final-30-day re-derivations"
        ]

    today = today or dt.datetime.now(dt.timezone.utc).date()
    invalid_dates: list[str] = []
    due_groups: dict[tuple[str, str], dict] = {}

    for position in positions:
        if not isinstance(position, dict):
            continue
        slug = str(position.get("slug") or "")
        if not slug:
            continue

        raw_end = position.get("endDate") or position.get("endDateIso")
        end_date = _iso_date(raw_end)
        if end_date is None:
            invalid_dates.append(f"{slug[:52]}={raw_end!r}")
            continue
        remaining = (end_date - today).days
        if remaining > SHORT_DATED_WINDOW_DAYS:
            continue

        match = _matching_prior(priors, slug)
        prior_key, prior = match if match is not None else (slug, {})
        verified_raw = prior.get("verified")
        verified = _iso_date(verified_raw)
        if verified == today:
            continue

        set_label = prior.get("set_only")
        if isinstance(set_label, str) and set_label.strip():
            group_key = ("set", set_label.strip())
            cluster = str(prior.get("cluster") or "set-only structure")
            label = f"set-only {cluster}"
        else:
            group_key = ("position", prior_key)
            label = slug

        if verified is None:
            verified_text = f"verified={verified_raw!r} (missing/malformed)"
        elif verified > today:
            verified_text = f"verified={verified.isoformat()} (future date)"
        else:
            age = (today - verified).days
            verified_text = f"verified {age}d ago ({verified.isoformat()})"

        clock = (
            f"{-remaining}d past endDate"
            if remaining < 0
            else f"{remaining}d remaining"
        )
        group = due_groups.setdefault(
            group_key,
            {
                "label": label,
                "slugs": [],
                "end_dates": set(),
                "clocks": set(),
                "verified": set(),
            },
        )
        group["slugs"].append(slug)
        group["end_dates"].add(end_date.isoformat())
        group["clocks"].add(clock)
        group["verified"].add(verified_text)

    issues: list[str] = []
    if invalid_dates:
        issues.append(
            "SHORT-DATED PRIOR CHECK DEGRADED — malformed/missing live endDate: "
            + "; ".join(invalid_dates)
            + ". Verify resolution dates manually; the audit cannot prove the "
              "final-30-day rotation is current."
        )

    if due_groups:
        rows_due = sum(len(group["slugs"]) for group in due_groups.values())
        msg = [
            f"SHORT-DATED PRIOR RE-DERIVATION due ({rows_due} live row(s), "
            f"{len(due_groups)} economic position(s)):"
        ]
        for group in due_groups.values():
            slugs = group["slugs"]
            leg_text = f" [{len(slugs)} set-only legs]" if len(slugs) > 1 else ""
            msg.append(
                f"    {group['label']}{leg_text} — end "
                f"{','.join(sorted(group['end_dates']))}; "
                f"{','.join(sorted(group['clocks']))}; "
                f"{','.join(sorted(group['verified']))}"
            )
        msg.append(
            "    -> re-check current evidence and recompute P(win), then set "
            "`verified` to today; do not merely roll the old probability forward."
        )
        issues.append("\n".join(msg))

    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true",
                    help="refresh conditionId snapshot + drop expired acked-holds")
    args = ap.parse_args()

    try:
        pos = _live_positions()
    except LivePositionsUnavailable as exc:
        print(
            f"AUDIT DEGRADED — {exc}; no state files were changed",
            file=sys.stderr,
        )
        return 2
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

    priors_loaded = _load("portfolio_kelly_priors.json", None)
    priors_raw = priors_loaded if isinstance(priors_loaded, dict) else {}

    # 3. SET-ONLY integrity.  Missing or unequal legs turn one economic position
    # into unintended directional exposure, so this is a hard non-clean result,
    # not an advisory judgment item and never auto-fixed.
    issues.extend(set_only_issues(priors_loaded, pos))

    # 3a. orphan priors (position gone — keep only if a deliberate re-entry candidate)
    for k, v in priors_raw.items():
        if k.startswith("_"):
            continue
        if not any(k in s or s in k for s in live):
            note = (v.get("note", "") if isinstance(v, dict) else "")
            if "closed" not in note.lower() and "re-entry" not in note.lower():
                issues.append(f"PRIOR orphan (no live position, no closure note): {k[:52]}")

    # 3b. SHORT-DATED PRIOR rotation. The 2026-08-12 backlog gate fired when
    # Lake America, the Iran-Oman agreement, and the Duma set simultaneously
    # entered their final 30 days. A by-date probability can go stale merely
    # because another day passed; enforce a fresh derivation once per UTC date.
    issues.extend(short_dated_prior_issues(priors_raw, pos))

    # 3c. CRITERIA RE-READ rotation (2026-08-05). Staleness guards watch the
    # `verified` DATE, not whether the recorded thesis is still CORRECT — and
    # an audit that day found 2 of 8 positions running on wrong/stale facts
    # (SpaceX's prior carried a "$2.1T day-one bar" when the IPO had already
    # happened at ~$1.75T; GPT-6's thesis assumed a naming crux the criteria
    # do not require). Neither was flagged by anything automated. So: surface
    # the LIVE position whose criteria were read longest ago, one per tick —
    # round-robin means every position gets re-read within ~a week.
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

    # 3d. PRIOR-vs-MARK divergence (2026-08-10). The criteria rotation above
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
