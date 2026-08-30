#!/usr/bin/env python3
"""Continuous opportunity watcher — 24/7 scanning between cron ticks.

Operator authorization 2026-07-15 ("you have the VM 24/7... run some script
constantly. Just cap the memory use"). Rationale: arbs and price-triggers are
EPHEMERAL — a real consistency/monotonicity arb lives minutes-to-hours, and
armed price triggers (ARB retrace-add, regime-fall re-entry) were only checked
at 2x-daily ticks. This daemon closes that latency gap.

Design (memory-safe by construction):
  - The parent is a tiny scheduler loop (~30MB RSS). Heavy scans run as
    SUBPROCESSES of the existing, tested scanner scripts — children die after
    each run, so scan memory never accumulates in the daemon.
  - Inline work is limited to single cheap HTTP calls (price triggers).
  - RSS self-cap: parent reads /proc/self/status each loop and EXITS at
    RSS_CAP_MB (crontab keepalive restarts it; a death also surfaces via
    heartbeat_watch PID check).

Schedules:
  - every 300s: armed price triggers (notes/opportunity_triggers.json)
  - every 300s: exact-label rollout signals (short-dated Google Maps catalysts)
  - every 900s: polymarket_consistency_scan (parse REAL-arb count)
  - every 900s (staggered +450s): event_monotonicity_scan (parse violations)
  - every 900s: new-listing watch (catalyst families: Gamescom, NYCC, ...)
  - every 900s: pair-arb bounds (two-leg, gated on the EXECUTABLE number)

Alerting: hits append notes/opportunity_alerts.jsonl. ACTIONABLE hits (real
arb >2% net, or an armed capital trigger crossing) telegram the operator AND
fire daily_checkin.sh (90-min cooldown, same pattern as news_watcher Tier-1).
Info hits just queue for the next tick.

CLI: opportunity_watch.py start | once
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx

from google_maps_label_check import LabelCheckError, check_google_maps_label

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
PY = str(REPO / ".venv" / "bin" / "python3")
ALERTS_PATH = REPO / "notes" / "opportunity_alerts.jsonl"
TRIGGERS_PATH = REPO / "notes" / "opportunity_triggers.json"
STATE_PATH = REPO / "logs" / ".opportunity_watch_state.json"
PID_PATH = REPO / "logs" / "opportunity_watch.pid"

RSS_CAP_MB = 150
LOOP_SECONDS = 60
PRICE_EVERY = 300
SCAN_EVERY = 900
LISTING_EVERY = 900        # new-market listing watch (catalyst families)
CRON_FIRE_COOLDOWN = 5400   # 90 min, matches news_watcher
ALERT_COOLDOWN = 3600       # per-key telegram cooldown


def _now() -> int:
    return int(time.time())


def _log(msg: str) -> None:
    print(f"[oppwatch {dt.datetime.utcnow().isoformat(timespec='seconds')}Z] {msg}", flush=True)


def _rss_mb() -> float:
    try:
        for line in open("/proc/self/status"):
            if line.startswith("VmRSS"):
                return int(line.split()[1]) / 1024.0
    except Exception:
        pass
    return 0.0


def _load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return {"last": {}, "alerts": {}, "last_cron": 0}


def _save_state(s: dict) -> None:
    try:
        STATE_PATH.write_text(json.dumps(s))
    except Exception:
        pass


def _append_alert(rec: dict) -> None:
    rec["ts"] = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    try:
        with ALERTS_PATH.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        _log(f"alert append failed: {e}")


def _telegram(text: str) -> None:
    try:
        subprocess.run([PY, str(SCRIPTS / "telegram.py"), "msg", text],
                       capture_output=True, timeout=30, cwd=str(REPO))
    except Exception as e:
        _log(f"telegram failed: {e}")


def _fire_tick(state: dict, why: str) -> bool:
    if _now() - state.get("last_cron", 0) < CRON_FIRE_COOLDOWN:
        _log(f"cron-fire suppressed (cooldown): {why}")
        return False
    _log(f"FIRING tick: {why}")
    try:
        # Pass the REASON through (2026-07-28): daemon-fired ticks used to
        # arrive as the generic scheduled-tick prompt, indistinguishable from
        # cron — so an off-schedule fire read as noise instead of "an armed
        # trigger crossed, act on it". daily_checkin.sh appends $1 to the prompt.
        subprocess.Popen(["bash", str(SCRIPTS / "daily_checkin.sh"),
                          f"REVALIDATION REQUEST FROM OPPORTUNITY WATCH: {why} — inspect "
                          f"notes/opportunity_alerts.jsonl (tail) FIRST. A trigger is an "
                          f"observation, not evidence of current executability or authorization "
                          f"to act; independently revalidate current inputs and constraints "
                          f"before recommending or taking action."],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        _log(f"tick fire failed: {e}")
        return False
    state["last_cron"] = _now()
    return True


def _alert(state: dict, key: str, text: str, actionable: bool) -> bool:
    _append_alert({"key": key, "text": text, "review_required": actionable})
    last = state.get("alerts", {}).get(key, 0)
    # Unchanged-payload dedupe (2026-07-16 audit): a persistently-true
    # condition (trigger stays crossed, arb stays open-but-unactable) used to
    # re-telegram every hour indefinitely. Same key AND same text → 6h
    # between sends; a CHANGED payload (new price/count) keeps the 1h cadence.
    prev_text = state.get("alert_texts", {}).get(key)
    cooldown = ALERT_COOLDOWN * 6 if prev_text == text else ALERT_COOLDOWN
    if _now() - last < cooldown:
        _log(f"telegram suppressed (cooldown): {key}")
    else:
        state.setdefault("alerts", {})[key] = _now()
        state.setdefault("alert_texts", {})[key] = text
        _telegram(f"[OPPWATCH] {text}")
    if actionable:
        return _fire_tick(state, key)
    return False


# ---------- checks ----------

def check_price_triggers(state: dict) -> None:
    """Armed triggers from notes/opportunity_triggers.json.

    Format: [{"key": "arb-retrace-add", "kind": "coingecko"|"clob_no_ask",
              "id": <coingecko id>|<token_id>, "op": "<="|">=",
              "level": 0.08, "note": "...", "actionable": true}]
    """
    try:
        trigs = json.loads(TRIGGERS_PATH.read_text())
    except Exception as e:
        _log(f"triggers file unreadable: {e}")
        return
    for t in trigs:
        try:
            if t["kind"] == "coingecko":
                r = httpx.get("https://api.coingecko.com/api/v3/simple/price",
                              params={"ids": t["id"], "vs_currencies": "usd"}, timeout=15).json()
                px = float(r[t["id"]]["usd"])
            elif t["kind"] == "clob_no_ask":
                b = httpx.get("https://clob.polymarket.com/book",
                              params={"token_id": t["id"]}, timeout=15).json()
                asks = sorted(b.get("asks", []), key=lambda x: float(x["price"]))
                if not asks:
                    continue
                px = float(asks[0]["price"])
            elif t["kind"] == "clob_bid":
                b = httpx.get("https://clob.polymarket.com/book",
                              params={"token_id": t["id"]}, timeout=15).json()
                bids = sorted(b.get("bids", []), key=lambda x: -float(x["price"]))
                if not bids:
                    continue
                px = float(bids[0]["price"])
            else:
                continue
            state.setdefault("trig_fails", {}).pop(t["key"], None)
        except Exception as e:
            # Visible failure accounting (2026-07-16 audit: bare continue made
            # a blind armed trigger indistinguishable from a quiet one). After
            # ~1h of consecutive failures (12 rounds @ 5min), alert once/6h.
            fails = state.setdefault("trig_fails", {})
            fails[t["key"]] = fails.get(t["key"], 0) + 1
            if fails[t["key"]] % 6 == 0:
                _log(f"trigger {t['key']} fetch failing x{fails[t['key']]}: {e}")
            if fails[t["key"]] == 12:
                _alert(state, f"trig-blind-{t['key']}",
                       f"armed trigger '{t['key']}' has been BLIND for ~1h "
                       f"(fetch failures) — not watching that price.",
                       actionable=False)
            continue
        hit = (px <= t["level"]) if t["op"] == "<=" else (px >= t["level"])
        if hit:
            _alert(state, t["key"],
                   f"armed trigger CROSSED: {t['key']} at {px} ({t['op']} {t['level']}). {t.get('note','')}",
                   bool(t.get("actionable")))


def _expiry_epoch(value: str) -> int:
    """Parse an explicit UTC trigger cutoff; invalid config fails closed."""
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("expires_at must include a timezone")
    return int(parsed.timestamp())


def _daemon_process_pattern() -> str:
    """Match only this daemon's canonical absolute start command.

    A broad ``pgrep -f 'opportunity_watch.py start'`` also matches an invoking
    shell whose command text happens to contain that phrase. During a restart
    that caused ``stop`` to signal its own parent shell. The keepalive already
    requires this exact absolute command, so status/stop should use it too.
    """
    command = f"{PY} {Path(__file__).resolve()} start"
    return f"^{re.escape(command)}$"


def check_google_maps_labels(state: dict) -> None:
    """Watch an exact Maps label as a one-response rollout signal.

    This inspects server HTML, not the client-rendered canvas, and intentionally
    does not infer majority-US rollout or market resolution. It fires one review
    tick, once, so that a human/agent can recheck rendered clients and credible
    reporting against the literal market criteria.
    """
    try:
        trigs = json.loads(TRIGGERS_PATH.read_text())
    except Exception as e:
        _log(f"triggers file unreadable (Google Maps labels): {e}")
        return

    observed = state.setdefault("google_maps_label_hits", {})
    expired = state.setdefault("google_maps_label_expired", {})
    for t in trigs:
        if t.get("kind") != "google_maps_label":
            continue
        key = t["key"]
        prior_hit = observed.get(key)
        if prior_hit is not None:
            # Alert/Telegram dedupe must not also discard the promised review
            # tick. The global 90-minute cooldown can suppress the first
            # dispatch when another trigger fired recently, so retain a small
            # persistent pending flag and retry only the tick on later polls.
            if prior_hit.get("review_tick_pending") and _fire_tick(state, key):
                prior_hit["review_tick_pending"] = False
                prior_hit["review_tick_dispatched"] = _now()
            continue
        try:
            expires_at = t["expires_at"]
            if _now() >= _expiry_epoch(expires_at):
                if expired.get(key) != expires_at:
                    expired[key] = expires_at
                    _log(f"Google Maps label watch '{key}' expired {expires_at}")
                continue
            result = check_google_maps_label(
                query=t["query"],
                target_label=t["target_label"],
                control_label=t["control_label"],
                region=t.get("region", "us"),
                language=t.get("language", "en"),
            )
            state.setdefault("trig_fails", {}).pop(key, None)
        except (KeyError, ValueError, LabelCheckError) as e:
            # Fail closed: an HTTP, consent, schema, or config error can never
            # become a positive rollout observation. Reuse the daemon's
            # persistent failure/alert state so prolonged blindness is visible.
            fails = state.setdefault("trig_fails", {})
            fails[key] = fails.get(key, 0) + 1
            if fails[key] % 6 == 0:
                _log(f"Google Maps label watch {key} failing x{fails[key]}: {e}")
            if fails[key] == 12:
                _alert(
                    state,
                    f"trig-blind-{key}",
                    f"Google Maps label watch '{key}' has been BLIND for ~1h "
                    f"(request/consent/schema failures) — no rollout inference made.",
                    actionable=False,
                )
            continue

        if not result.rollout_signal:
            continue
        text = (
            f"Google Maps US-region rollout SIGNAL: exact label "
            f"'{result.target_label}' appeared {result.target_count} time(s) in one "
            f"server HTML response for '{result.query}'. This is NOT proof that the "
            f"label rendered on the map, of majority-US rollout, or of resolution; "
            f"recheck independent rendered US clients/reporting and the criteria "
            f"before acting. {t.get('note', '')}"
        )
        actionable = bool(t.get("actionable", True))
        tick_dispatched = _alert(state, key, text, actionable)
        observed[key] = {
            "first_seen": _now(),
            "target_count": result.target_count,
            "control_count": result.control_count,
            "review_tick_pending": actionable and not tick_dispatched,
        }
        if tick_dispatched:
            observed[key]["review_tick_dispatched"] = _now()


def check_new_listings(state: dict) -> None:
    """Fire when a NEW event matching a watched query appears on Polymarket.

    Motivation (2026-08-10): the announce-template edge (SDCC 4-for-4, Prime
    +59%, Marvel +43.9%) is biggest in the hours AFTER a catalyst family lists,
    because the cheap legs get bid up fast. Until now that watch was manual —
    I searched "gamescom" once per tick and D23 burned 7 days of tick attention
    before expiring unlisted. This converts it to a 15-min daemon check.

    Config entries in the same triggers file:
      {"key": "...", "kind": "new_listing", "query": "gamescom",
       "match": "gamescom", "expires": "2026-08-26", "note": "...",
       "actionable": true}

    First sight of a key SEEDS the baseline silently — otherwise arming a
    watcher would immediately alert on every pre-existing market.
    """
    try:
        trigs = json.loads(TRIGGERS_PATH.read_text())
    except Exception as e:
        _log(f"triggers file unreadable (listings): {e}")
        return
    today = dt.datetime.utcnow().date().isoformat()
    seen_all = state.setdefault("seen_listings", {})
    for t in trigs:
        if t.get("kind") != "new_listing":
            continue
        key = t["key"]
        exp = t.get("expires")
        if exp and exp < today:
            if state.setdefault("listing_expired", {}).get(key) != exp:
                state["listing_expired"][key] = exp
                _log(f"listing watch '{key}' expired {exp} — no longer checked")
            continue
        try:
            # limit_per_type 20 -> 50 (2026-08-14). public-search is FUZZY: the
            # query "gamescom" returns 20 events that are all GameStop, and the
            # needle filter below correctly discards every one — but they consume
            # the entire result window first. So a genuine Gamescom listing that
            # ranked below the fuzzy noise would never enter the candidate set,
            # and the watch would look perfectly healthy while missing the exact
            # event it exists to catch (it ticks, it is seeded, it logs no error).
            # Same shape as a gate that silently does not run. The API caps at 48
            # regardless of larger values, so 50 buys the full window.
            r = httpx.get("https://gamma-api.polymarket.com/public-search",
                          params={"q": t["query"], "limit_per_type": 50}, timeout=20)
            events = r.json().get("events", []) or []
        except Exception as e:
            fails = state.setdefault("trig_fails", {})
            fails[key] = fails.get(key, 0) + 1
            if fails[key] % 6 == 0:
                _log(f"listing watch {key} fetch failing x{fails[key]}: {e}")
            if fails[key] == 12:
                _alert(state, f"trig-blind-{key}",
                       f"listing watch '{key}' has been BLIND for ~3h (fetch failures).",
                       actionable=False)
            continue
        state.setdefault("trig_fails", {}).pop(key, None)
        needle = (t.get("match") or t["query"]).lower()
        live = []
        for e in events:
            if e.get("closed") or not e.get("active"):
                continue
            slug = (e.get("slug") or "")
            if needle in slug.lower() or needle in (e.get("title") or "").lower():
                live.append(slug)
        prior = seen_all.get(key)
        if prior is None:
            seen_all[key] = sorted(live)
            _log(f"listing watch '{key}' seeded with {len(live)} existing event(s)")
            continue
        fresh = [s for s in live if s not in prior]
        if not fresh:
            continue
        seen_all[key] = sorted(set(prior) | set(live))
        _alert(state, f"listing-{key}",
               f"NEW MARKET LISTED for watch '{key}': {', '.join(fresh[:5])}"
               f"{' (+%d more)' % (len(fresh) - 5) if len(fresh) > 5 else ''}. {t.get('note','')}",
               bool(t.get("actionable", True)))


def run_pair_arb(state: dict) -> None:
    """Two-leg bound checks, gated on the EXECUTABLE number.

    Why this replaced a price trigger (2026-08-11): I armed `hle-cross-event-arb`
    as a single-leg clob_no_ask trigger at 0.47, a level derived from the OTHER
    leg's ask (0.44) at arming time. That leg then moved to 0.56, so the real
    breakeven fell to ~0.35 — and when the umbrella ask touched 0.45 the trigger
    fired a tick dispatch on a structure that cost 1.01 before ~8pp of fees.
    A one-leg trigger cannot price a two-leg structure: the level goes stale the
    moment the unwatched leg moves, and it goes stale SILENTLY. My own note on
    that trigger said "re-walk both books first" — anticipating the failure in a
    comment is not handling it. This walks both books every cycle and alerts only
    when the taker structure is actually positive after fees.

    Config: {"key": ..., "kind": "pair_arb", "mode": "umbrella"|"implies",
             "a": <slug>, "b": <slug>, "note": ...}
      umbrella: a = umbrella EVENT slug, b = subset EVENT slug
      implies:  a implies b, both MARKET slugs (so P(a) <= P(b))
    """
    try:
        trigs = json.loads(TRIGGERS_PATH.read_text())
    except Exception as e:
        _log(f"triggers file unreadable (pair_arb): {e}")
        return
    for t in trigs:
        if t.get("kind") != "pair_arb":
            continue
        args = (["--umbrella", t["a"], "--subset", t["b"]] if t.get("mode") == "umbrella"
                else ["--implies", t["a"], t["b"]])
        try:
            r = subprocess.run([PY, str(SCRIPTS / "cross_event_bound_scan.py")] + args,
                               capture_output=True, text=True, timeout=300, cwd=str(REPO))
            out = (r.stdout or "") + (r.stderr or "")
        except Exception as e:
            _log(f"pair_arb {t['key']} run failed: {e}")
            continue
        n_exec = None
        for line in out.splitlines():
            if "executable after live-CLOB walk" in line:
                parts = line.replace("#", " ").split(";")
                if len(parts) > 1:
                    tok = parts[1].strip().split()[0]
                    n_exec = int(tok) if tok.isdigit() else None
        if n_exec is None:
            _log(f"pair_arb {t['key']}: no summary line parsed")
            continue
        if n_exec > 0:
            _alert(state, t["key"],
                   f"pair-arb EXECUTABLE after live books + fees: {t['key']}. {t.get('note','')}",
                   actionable=True)
        else:
            _log(f"pair_arb {t['key']}: 0 executable (bound may be violated on mids; books say no)")


def run_consistency(state: dict) -> None:
    try:
        r = subprocess.run([PY, str(SCRIPTS / "polymarket_consistency_scan.py")],
                           capture_output=True, text=True, timeout=300, cwd=str(REPO))
        out = (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        _log(f"consistency run failed: {e}")
        return
    if r.returncode != 0:
        _log(f"consistency: scanner exited {r.returncode}; no alert")
        return
    pattern = re.compile(
        r"^(?P<count>\d+) PROVISIONAL consistency candidates exceed "
        r"(?P<threshold>\d+(?:\.\d+)?)% modeled net; REVALIDATION REQUIRED$"
    )
    for line in out.splitlines():
        match = pattern.fullmatch(line.strip())
        if match:
            count = int(match.group("count"))
            if count > 0:
                _alert(
                    state,
                    "consistency-arb",
                    f"CONSISTENCY REVALIDATION REQUEST: {count} candidate(s) crossed "
                    f"the {match.group('threshold')}% modeled-net screen in sequential, "
                    f"non-atomic CLOB snapshots. Refresh basket membership and resolution "
                    f"criteria; re-walk every leg at one common size; recompute fees/net "
                    f"edge and assess legging risk. Do not execute from this alert. "
                    f"See logs/polymarket_consistency_latest.json",
                    actionable=True,
                )
            return
    _log("consistency: no provisional-revalidation line parsed")


def run_monotonicity(state: dict) -> None:
    try:
        r = subprocess.run([PY, str(SCRIPTS / "event_monotonicity_scan.py")],
                           capture_output=True, text=True, timeout=300, cwd=str(REPO))
        out = (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        _log(f"monotonicity run failed: {e}")
        return
    # 2026-07-23: only fire on REAL (live-CLOB-validated) arbs, never on
    # midpoint mirages. The scanner now prints "... ; M REAL after live-CLOB
    # walk"; parse M. A 3-hour false-positive storm (Elon-tweet mid-flag,
    # -10.95pp executable) is exactly what this prevents.
    import re as _re
    m = _re.search(r";\s*(\d+)\s+REAL after live-CLOB walk", out)
    if m is None:
        _log("monotonicity: no REAL-count line parsed (scanner output format?)")
        return
    n_real = int(m.group(1))
    if n_real <= 0:
        return  # midpoint flags only — not actionable
    # ECONOMIC FLOOR (2026-08-11). This fired a tick on a genuinely executable
    # WTI >=81/>=80 pair worth +0.37pp — a TRUE positive that was still not worth
    # waking for. The floor is NOT about bankroll size (0.37% is 0.37% at any
    # scale, and capacity is explicitly not a filter here); it is about MODEL
    # ERROR: a sub-2pp edge sits inside the uncertainty of my own fee and
    # slippage estimate, and a two-leg structure converts to a directional
    # position the moment one leg fills alone. The consistency scanner already
    # uses a 2% net bar; this brings the two into line. Sub-threshold arbs are
    # still LOGGED, so the information is kept without paying a tick dispatch
    # and the 90-minute global cron cooldown it consumes.
    MIN_ARB_EDGE_PP = 2.0
    best = None
    for line in out.splitlines():
        if "REAL ARB" not in line:
            continue
        edges = _re.findall(r"([+-]?\d+\.\d+)pp", line)
        edge = float(edges[-1]) if edges else 0.0
        if best is None or edge > best[0]:
            best = (edge, line.strip())
    if best is None:
        return
    edge, line = best
    if edge < MIN_ARB_EDGE_PP:
        _log(f"monotonicity: {n_real} real arb(s) but best edge {edge:+.2f}pp < "
             f"{MIN_ARB_EDGE_PP}pp floor — logged, not firing: {line[:120]}")
        return
    _alert(state, "monotonicity-arb",
           f"monotonicity: {n_real} EXECUTABLE arb(s) after live-CLOB walk, best {edge:+.2f}pp — {line[:140]}",
           actionable=True)


# ---------- main ----------

def poll_loop() -> int:
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(os.getpid()))
    state = _load_state()
    _log(f"up pid={os.getpid()} rss={_rss_mb():.0f}MB cap={RSS_CAP_MB}MB")
    offset = 0
    while True:
        now = _now()
        last = state.setdefault("last", {})
        try:
            if now - last.get("price", 0) >= PRICE_EVERY:
                last["price"] = now
                check_price_triggers(state)
                check_google_maps_labels(state)
            if now - last.get("listings", 0) >= LISTING_EVERY:
                last["listings"] = now
                check_new_listings(state)
            if now - last.get("pair_arb", 0) >= SCAN_EVERY:
                last["pair_arb"] = now
                run_pair_arb(state)
            if now - last.get("consistency", 0) >= SCAN_EVERY:
                last["consistency"] = now
                run_consistency(state)
            if now - last.get("monotonicity", 0) >= SCAN_EVERY + 450 - (450 if last.get("monotonicity") else 0):
                last["monotonicity"] = now
                run_monotonicity(state)
        except KeyboardInterrupt:
            return 0
        except Exception as e:
            _log(f"loop error: {e}")
        _save_state(state)
        rss = _rss_mb()
        if rss > RSS_CAP_MB:
            _telegram(f"[OPPWATCH] RSS {rss:.0f}MB > cap {RSS_CAP_MB}MB — exiting for restart (keepalive).")
            _log(f"RSS cap exceeded ({rss:.0f}MB) — exiting")
            return 1
        time.sleep(LOOP_SECONDS)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "start"
    # 2026-08-14: there was no "stop" mode, and ANY unrecognised argument fell
    # through to poll_loop() — so `opportunity_watch.py stop` did not stop the
    # daemon, it STARTED A SECOND ONE. Discovered by running exactly that during
    # a restart: two extra instances were spawned against a live one, on a 1.9GB
    # box whose standing rule is one background process at a time. An unknown
    # argument must never mean "silently launch a daemon".
    if mode in ("stop", "status"):
        import signal
        pidfile = REPO / "logs" / "opportunity_watch.pid"
        pids = []
        try:
            out = subprocess.run(["pgrep", "-f", _daemon_process_pattern()],
                                 capture_output=True, text=True, timeout=10).stdout
            pids = [int(x) for x in out.split() if x.strip().isdigit() and int(x) != os.getpid()]
        except Exception:
            pass
        if mode == "status":
            print(f"opportunity_watch: {len(pids)} running {pids or ''}")
            return 0 if pids else 1
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"sent SIGTERM to {pid}")
            except Exception as e:
                print(f"could not signal {pid}: {e}")
        try:
            pidfile.unlink(missing_ok=True)      # it went stale on every crash
        except Exception:
            pass
        return 0
    if mode not in ("start", "once"):
        print(f"unknown mode {mode!r}; use start|stop|status|once", file=sys.stderr)
        return 2
    if mode == "once":
        state = _load_state()
        check_price_triggers(state)
        check_google_maps_labels(state)
        check_new_listings(state)
        run_pair_arb(state)
        run_consistency(state)
        run_monotonicity(state)
        _save_state(state)
        _log(f"once done rss={_rss_mb():.0f}MB")
        return 0
    return poll_loop()


if __name__ == "__main__":
    sys.exit(main())
