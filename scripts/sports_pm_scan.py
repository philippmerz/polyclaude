#!/usr/bin/env python3
"""Sports-market scanner for Polymarket — surfaces short-tail trade candidates.

discover_markets.py covers the bond-like-fade lens (high APY tail). This script
adds a SPORTS-specific filter:
- Resolves within next 36-72h (matches <1y horizon)
- Liquid book (vol24h > $50k, liq > $10k)
- Categorizes by lens:
  - BOND_LIKE_FADE: dominant side > 0.93, decent APY
  - MID_50_50: 0.40 <= yes <= 0.60 (requires fair-value model to enter)
  - PROP_TAIL: extreme tails on prop bets (over/under, spread)
- Future v2: integrate bookie consensus odds via the-odds-api or similar to
  find Polymarket vs bookie-consensus deltas.

Operator directive 2026-05-09 ~17:10 UTC: aggressive engineering campaign
to recoup R-U drawdown via untapped sports + cross-venue alpha.

Usage:
    python scripts/sports_pm_scan.py
    python scripts/sports_pm_scan.py --hours 72
    python scripts/sports_pm_scan.py --json
    python scripts/sports_pm_scan.py --with-kalshi --json
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import sys

import re
import subprocess

import httpx

from agent_runtime import run_agent
import pm_fees  # scalar APY estimate; full market dicts honor feeSchedule


KALSHI_TOP_N_HARD_CAP = 5


def validate_consensus_freshness(
    consensus: dict,
    lim_hours: float,
    *,
    now: datetime.datetime | None = None,
    expected_outcomes: list[str] | None = None,
    market_context: dict | None = None,
) -> dict:
    """Validate timestamped bookmaker odds, then derive a margin-free YES probability."""
    if not isinstance(consensus, dict):
        return {"error": "consensus payload is not an object"}
    if "error" in consensus:
        return consensus
    if any(key in consensus for key in ("yes_prob", "ai_probability", "model_probability")):
        return {"error": "scalar/model probability payload is unverified; decimal odds required"}
    if consensus.get("source_type") != "bookmaker_decimal_odds":
        return {"error": "consensus source is not identified as bookmaker decimal odds"}
    bookmaker = consensus.get("bookmaker")
    if not isinstance(bookmaker, str) or not bookmaker.strip():
        return {"error": "consensus omitted the named bookmaker"}
    source_url = consensus.get("source_url")
    if not isinstance(source_url, str) or not source_url.startswith(("http://", "https://")):
        return {"error": "consensus source omitted an auditable source_url"}
    raw = consensus.get("source_at")
    if not isinstance(raw, str) or not raw.strip():
        return {"error": "consensus source omitted a verifiable source_at timestamp"}
    try:
        source_at = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if source_at.tzinfo is None:
            source_at = source_at.replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return {"error": "consensus source_at timestamp is malformed"}
    # Many news/insight URLs encode their publication date. Catch a worker that
    # relabels an old article with the current check time (the Sep-1 Alvarez
    # false lead cited a /20260825- Oddschecker article as Sep-1 consensus).
    url_dates = re.findall(r"(?<!\d)(20\d{6})(?!\d)", source_url)
    for encoded in url_dates:
        try:
            url_date = datetime.datetime.strptime(encoded, "%Y%m%d").date()
        except ValueError:
            continue
        if abs((source_at.date() - url_date).days) > 1:
            return {"error": "consensus source_at conflicts with date encoded in source_url"}
    now_dt = now or datetime.datetime.now(datetime.timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=datetime.timezone.utc)
    age_hours = (now_dt - source_at).total_seconds() / 3600
    max_age_hours = min(24.0, max(3.0, float(lim_hours) / 2.0))
    if age_hours < -0.25:
        return {"error": "consensus source timestamp is in the future"}
    if age_hours > max_age_hours:
        return {"error": (f"consensus stale ({age_hours:.1f}h old; "
                          f"max {max_age_hours:.1f}h for this contract clock)")}
    context = market_context if isinstance(market_context, dict) else {}
    context_question = context.get("question")
    context_description = context.get("description") or ""
    context_type = str(context.get("sportsMarketType") or "").casefold()
    expected_names = [str(x) for x in (expected_outcomes or [])]
    binary_yes_no = len(expected_names) == 2 and {x.casefold() for x in expected_names} == {"yes", "no"}
    expected_type = None
    if len(expected_names) == 3:
        expected_type = "1x2"
    elif len(expected_names) == 2 and not binary_yes_no:
        expected_type = "two_way"
    elif binary_yes_no:
        # Gamma's binary outcomes alone do not reveal whether a football NO
        # includes a draw. Infer only from trusted Gamma market type and rules.
        context_rules = f"{context_question or ''} {context_description}".casefold()
        has_draw_rule = bool(re.search(r"\b(draw|tie)\b", context_rules))
        is_moneyline = context_type in {"moneyline", "money_line", "money line"}
        is_football_period = bool(re.search(r"\b(90 minutes?|first 90|full time)\b", context_rules))
        if is_moneyline and has_draw_rule and is_football_period:
            expected_type = "1x2"
        else:
            return {"error": "Gamma context does not establish the bookmaker market type for binary YES/NO"}
    if expected_type is None:
        return {"error": "Gamma outcomes do not establish a supported bookmaker market type"}
    market_type = consensus.get("market_type")
    if market_type not in ("two_way", "1x2"):
        return {"error": "consensus market type is missing or unsupported"}
    if expected_type and market_type != expected_type:
        return {"error": f"consensus market type {market_type!r} does not match expected {expected_type!r}"}
    raw_odds = consensus.get("decimal_odds")
    required_count = 3 if market_type == "1x2" else 2
    if not isinstance(raw_odds, list) or len(raw_odds) != required_count:
        return {"error": f"{market_type} consensus requires a complete outcome odds list"}
    odds: dict[str, float] = {}
    for row in raw_odds:
        if not isinstance(row, dict):
            return {"error": "decimal odds rows must include outcome and odds"}
        name, value = row.get("outcome"), row.get("odds")
        if not isinstance(name, str) or not name.strip() or name in odds:
            return {"error": "decimal odds contain a missing or duplicate outcome"}
        if row.get("bookmaker") != bookmaker:
            return {"error": "decimal odds rows do not all identify the same named bookmaker"}
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 1):
            return {"error": f"decimal odds for {name!r} are invalid"}
        odds[name] = float(value)
    yes_outcomes = consensus.get("yes_outcomes")
    if (not isinstance(yes_outcomes, list) or not yes_outcomes
            or any(not isinstance(name, str) or name not in odds for name in yes_outcomes)
            or len(set(yes_outcomes)) != len(yes_outcomes)
            or len(yes_outcomes) == len(odds)):
        return {"error": "YES outcome mapping must select a proper subset of the complete book market"}
    mapping_note = consensus.get("mapping_note")
    if not isinstance(mapping_note, str) or not mapping_note.strip():
        return {"error": "consensus omitted the mapping from bookmaker outcomes to market YES"}
    no_outcomes = [name for name in odds if name not in yes_outcomes]
    context_question = (market_context or {}).get("question")
    if market_context and not isinstance(context_question, str):
        return {"error": "market context question is malformed"}
    normalize = lambda value: "".join(ch.casefold() for ch in value if ch.isalnum())
    if expected_type == "1x2" and binary_yes_no:
        # A binary YES contract on a football winner has three bookmaker
        # outcomes: its NO complement must include both draw and opponent.
        if len(yes_outcomes) != 1 or len(no_outcomes) != 2:
            return {"error": "binary YES on a 1x2 market must select one winner and retain two NO outcomes"}
        draw_rows = [name for name in no_outcomes if re.search(r"\b(draw|tie)\b", name, re.I)]
        yes_name = yes_outcomes[0]
        question = context_question if isinstance(context_question, str) else ""
        description = context_description if isinstance(context_description, str) else ""
        trusted_text = f"{question} {description}"
        if (not draw_rows or not re.search(r"\b(win|wins|beat|beats|defeat|defeats|winner)\b", question, re.I)):
            return {"error": "1x2 YES/NO mapping is not established by Gamma question/rules"}
        question_teams = [name for name in odds if name not in draw_rows
                          and re.search(rf"(?<!\w){re.escape(name)}(?!\w)", question, re.I)]
        if len(question_teams) != 1 or normalize(yes_name) != normalize(question_teams[0]):
            return {"error": "1x2 YES side does not match the team named as winning in the Gamma question"}
        opponent_names = [name for name in no_outcomes if name not in draw_rows]
        if (len(opponent_names) != 1 or not re.search(
                rf"(?<!\w){re.escape(opponent_names[0])}(?!\w)", trusted_text, re.I)):
            return {"error": "1x2 opponent is not present in the Gamma question/rules"}
    elif expected_type == "1x2":
        if {normalize(name) for name in odds} != {normalize(name) for name in expected_names}:
            return {"error": "bookmaker outcomes do not match the ordered Gamma 1x2 outcomes"}
        if (len(yes_outcomes) != 1
                or normalize(yes_outcomes[0]) != normalize(expected_names[0])):
            return {"error": "bookmaker YES mapping does not match the first Gamma 1x2 outcome"}
    elif expected_type == "two_way":
        if {normalize(name) for name in odds} != {normalize(name) for name in expected_names}:
            return {"error": "bookmaker outcomes do not match the ordered Gamma market outcomes"}
        if (len(yes_outcomes) != 1
                or normalize(yes_outcomes[0]) != normalize(expected_names[0])):
            return {"error": "bookmaker YES mapping does not match the first Gamma market outcome"}
    implied = {name: 1.0 / price for name, price in odds.items()}
    total = sum(implied.values())
    return {
        "yes_prob": sum(implied[name] for name in yes_outcomes) / total,
        "bookmaker": bookmaker.strip(),
        "source": bookmaker.strip(),
        "source_url": source_url,
        "source_at": source_at.isoformat(),
        "market_type": market_type,
        "decimal_odds": [{"outcome": name, "odds": odds[name], "bookmaker": bookmaker} for name in odds],
        "yes_outcomes": list(yes_outcomes),
        "no_outcomes": no_outcomes,
        "mapping_note": mapping_note,
        "implied_probabilities": {name: implied[name] / total for name in odds},
        "derivation": "reciprocal decimal odds normalized across this bookmaker's complete market",
        "confidence": consensus.get("confidence", "unrated"),
        "note": consensus.get("note", ""),
    }


def fetch_bookie_consensus(question: str, lim_hours: float, outcomes: list[str] | None = None,
                            timeout: int = 120, market_context: dict | None = None) -> dict:
    """Fetch one book's complete odds and derive a margin-free YES probability."""

    # Derivative-market guard (2026-07-30): a "Spread: Raków (-1.5)" question
    # answered with MONEYLINE odds produced a phantom -27.1pp delta (bookie
    # 0.636 was the match-winner prob, ~= PM's own moneyline 0.625; the spread
    # market at 0.365 was internally consistent). Comparing across market
    # types is the false-positive class; force haiku to error out rather than
    # substitute the winner line.
    derivative = re.search(r"spread|handicap|\(\s*[+-]\d|o/u|over/under|total",
                           question, re.I)
    deriv_clause = ""
    if derivative:
        deriv_clause = ("\n\nIMPORTANT: this is a DERIVATIVE market (point spread / "
                        "handicap / total), NOT a match-winner market. The probability "
                        "MUST be for the exact stated line. Match-winner/moneyline odds "
                        "are NOT acceptable as a substitute — if you can only find "
                        "match-winner odds, output the error case instead.")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    max_age_hours = min(24.0, max(3.0, float(lim_hours) / 2.0))
    prompt = f"""Find current named-bookmaker DECIMAL ODDS for the exact sports event/market below.

Market question: {question}
Polymarket outcomes in order: {json.dumps(outcomes or [])}
Gamma market metadata/rules: {json.dumps(market_context or {}, ensure_ascii=False)}
Resolves within: {lim_hours:.1f} hours
Current UTC time: {now_utc.isoformat(timespec='seconds')}
Maximum acceptable odds age: {max_age_hours:.1f} hours{deriv_clause}

Search for the exact market from one named sportsbook. Odds comparison sites are acceptable only when they show actual odds attributed to that book. Do not use an AI/model probability, predicted probability, consensus percentage, or a field labeled "AI Probability". Do not combine books or select cross-book best odds.

DO NOT use Polymarket as a source — that's the venue we're comparing AGAINST and would create circular reasoning. If you can only find Polymarket odds, output the error case.

FRESHNESS IS MANDATORY. A dated article or odds snapshot older than the maximum age is not current. The page must show actual odds and a verifiable update/capture timestamp. For an explicitly live sportsbook page use current check time only if that page visibly shows these prices; otherwise provide its actual updated timestamp. If freshness cannot be established, output the error case.

Return complete decimal odds from ONE named bookmaker for every mutually exclusive outcome: use market_type "1x2" for a draw-permitting football home/draw/away market (all three required), or "two_way" for an exact two-outcome market (both required). State which literal bookmaker outcome(s) correspond to Polymarket YES and explain the mapping in mapping_note. NO is the complement. Each decimal_odds row must repeat the same bookmaker name. Decimal odds must be numeric and greater than 1. Never return a probability scalar.

Output ONE line of JSON only, no preamble:
{{"source_type":"bookmaker_decimal_odds","bookmaker":"<named book>","source_url":"<exact URL showing these odds>","source_at":"<ISO-8601 timestamp>","market_type":"1x2|two_way","decimal_odds":[{{"outcome":"<literal outcome>","odds":<decimal>,"bookmaker":"<same named book>"}}],"yes_outcomes":["<literal outcome(s) mapping to PM YES>"],"mapping_note":"<why these outcomes map to the exact PM question/YES>","confidence":"high|med|low","note":"<visible price and timestamp context>"}}

If no non-Polymarket consensus is fetchable (event too obscure, props market with no public odds, etc.), output:
{{"error": "<one-sentence reason>"}}

Be concise. ONE line only."""
    try:
        r = run_agent(prompt, profile="fast", effort="low", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": f"agent timeout after {timeout}s"}
    if r.returncode != 0:
        return {"error": f"agent exited {r.returncode}: {r.stderr[:100]}"}

    out = r.stdout.strip()
    # Extract one balanced JSON object if the worker adds commentary; the
    # evidence schema nests one object per bookmaker outcome.
    start = out.find("{")
    if start < 0:
        return {"error": "no JSON in agent output"}
    depth = 0
    end = None
    in_string = escaped = False
    for index in range(start, len(out)):
        char = out[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        return {"error": "no complete JSON object in agent output"}
    try:
        import json as _json
        parsed = _json.loads(out[start:end])
        return validate_consensus_freshness(parsed, lim_hours, now=now_utc,
                                            expected_outcomes=outcomes,
                                            market_context=market_context)
    except Exception as e:
        return {"error": f"json parse: {e}"}


def fetch_active_sports_markets(min_vol24: float = 30000, min_liq: float = 5000) -> list[dict]:
    out: list[dict] = []
    seen_ids: set[str] = set()
    with httpx.Client(timeout=20) as c:
        for page in range(6):
            try:
                r = c.get("https://gamma-api.polymarket.com/markets", params={
                    # gamma caps pages at 100; offset stride must match (else skips 80%).
                    "closed": "false", "active": "true", "limit": 100,
                    "offset": page * 100,
                    "order": "volume24hr", "ascending": "false",
                })
                r.raise_for_status()
            except Exception as e:
                print(f"page {page} fetch err: {e}", file=sys.stderr)
                continue
            data = r.json() or []
            if not data:
                break
            for m in data:
                mid = m.get("id")
                if not mid or mid in seen_ids:
                    continue
                seen_ids.add(mid)
                if m.get("umaResolutionStatus") in ("proposed", "disputed"):
                    continue
                if not _is_sports(m):
                    continue
                vol = float(m.get("volume24hr", 0) or 0)
                liq = float(m.get("liquidityNum", 0) or 0)
                if vol < min_vol24 or liq < min_liq:
                    continue
                out.append(m)
    return out


def _is_sports(m: dict) -> bool:
    if m.get("sportsMarketType"):
        return True
    text = ((m.get("question") or "") + " " + (m.get("description") or "") + " " + (m.get("slug") or "")).lower()
    return any(k in text for k in [
        " vs. ", " vs ", "premier league", "serie a", "nba", "nfl", "nhl",
        "mlb", "uefa", "fifa", "ufc", "f1 ", "tennis", "match", "mls",
        "champions league", "atletico", "real madrid", "manchester",
        "lakers", "warriors", "celtics", "thunder", "pistons", "cavaliers",
    ])


def categorize(m: dict) -> tuple[str, float, float, float]:
    """Return (lens, yes_price, no_price, days_to_resolve)."""
    try:
        prices = json.loads(m.get("outcomePrices", "[]")) if isinstance(m.get("outcomePrices"), str) else m.get("outcomePrices", [])
        yes = float(prices[0])
        no = float(prices[1])
    except Exception:
        return "UNKNOWN", 0.0, 0.0, 0.0

    # Prefer endDate (datetime) over endDateIso (date-only); date-only collapses
    # same-day events to 00:00 UTC which is in the past for any afternoon scan.
    end = m.get("endDate") or m.get("endDateIso") or ""
    try:
        end_dt = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        days = (end_dt - now_dt).total_seconds() / 86400
    except Exception:
        days = 0.0

    if yes >= 0.93:
        lens = "BOND_LIKE_FADE_YES"
    elif no >= 0.93:
        lens = "BOND_LIKE_FADE_NO"
    elif 0.40 <= yes <= 0.60:
        lens = "MID_50_50"
    elif yes >= 0.85 or no >= 0.85:
        lens = "STRONG_FAVORITE"
    else:
        lens = "OTHER"
    return lens, yes, no, days


def is_in_play(m: dict, now: datetime.datetime | None = None) -> bool:
    """Return True only when Gamma gives a parseable start at/before now.

    Bookie workers frequently find cached pregame prices.  Comparing those with
    a Polymarket price after play has begun manufactures huge phantom deltas.
    Markets without a usable ``gameStartTime`` remain eligible because absence
    of metadata is not proof that the event is live; the manual criteria gate
    still applies to every surfaced comparison.
    """
    raw = m.get("gameStartTime")
    if not raw:
        return False
    try:
        start = datetime.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=datetime.timezone.utc)
        now_dt = now or datetime.datetime.now(datetime.timezone.utc)
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=datetime.timezone.utc)
        return start <= now_dt
    except (TypeError, ValueError):
        return False


def annualized_apy(p: float, days: float, fee_rate: float | None = None) -> float:
    """Fee-aware APY at price ``p``. Capped at 10000x for display.

    ``fee_rate`` is scalar, so this helper deliberately uses the legacy
    exponent-1 estimate ``effective_rate × p × (1−p)`` and ``pm_fees.py``'s
    0.07 compatibility cap. It cannot propagate a structured feeSchedule
    exponent; authoritative full-market calculations should use
    ``pm_fees.fee_per_share(market, p)``.
    """
    if p >= 0.999 or days < 0.5:
        return 0.0
    raw_rate = pm_fees.FEE_RATE_FALLBACK if fee_rate is None else fee_rate
    fee_per_share = pm_fees.fee_per_share_at(raw_rate, p)
    cost = p + fee_per_share
    if cost >= 1.0:
        return 0.0
    gross = (1.0 - cost) / cost
    # Cap APY at 10000x (1,000,000%) to avoid overflow on sub-day windows.
    # For sub-day windows the APY math becomes meaningless anyway; absolute
    # return-per-dollar is the meaningful metric there.
    try:
        apy = (1.0 + gross) ** (365.0 / max(days, 0.5)) - 1.0
    except OverflowError:
        apy = 1e4
    return min(apy, 1e4)


def main() -> int:
    p = argparse.ArgumentParser(description="Sports-market scanner for Polymarket trade candidates.")
    p.add_argument("--hours", type=float, default=48,
                   help="Resolution-window cutoff hours (default 48).")
    p.add_argument("--min-vol24", type=float, default=30000)
    p.add_argument("--min-liq", type=float, default=5000)
    p.add_argument("--hurdle-apy", type=float, default=None,
                   help="Hurdle APY for bond-like-fade surfacing. Default: the LIVE "
                        "Aave-Polygon USDC supply rate (24h-cached via check_marginal_apy). "
                        "Was hard-coded 0.034 until 2026-08-25 — a third instance of the "
                        "stale-constant class (the hand-maintained hurdle has been wrong at "
                        "3.4%%, then 5.0%%, against a live rate near 2.9%%). Direction of the "
                        "old error was safe here (too high = under-surfaces candidates), which "
                        "is exactly why nothing ever surfaced it.")
    p.add_argument("--json", action="store_true")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--with-consensus", action="store_true",
                   help="Fetch bookie-consensus odds per top-5 candidate via "
                        "a scoped web-research worker. Slower (~30s per market) "
                        "but surfaces Polymarket-vs-bookie pricing deltas.")
    p.add_argument("--consensus-top-n", type=int, default=5,
                   help="Number of top candidates to fetch consensus for "
                        "(default 5, to bound model cost).")
    p.add_argument("--with-kalshi", action="store_true",
                   help="Compare top shortlisted candidates with strictly matched "
                        "Kalshi public REST books. Read-only; no account/auth/trading. "
                        "Default behavior is unchanged when omitted.")
    p.add_argument("--kalshi-top-n", type=int, default=5,
                   help="Number of already-shortlisted candidates to compare with "
                        "Kalshi (default 5, hard maximum 5; each lookup is bounded "
                        "and fail-closed).")
    args = p.parse_args()
    if args.hurdle_apy is None:
        from discover_markets import live_hurdle_apy
        args.hurdle_apy = live_hurdle_apy()

    print(f"# sports_pm_scan window=<={args.hours}h vol24h>=${args.min_vol24:.0f} liq>=${args.min_liq:.0f}", file=sys.stderr)

    markets = fetch_active_sports_markets(args.min_vol24, args.min_liq)
    print(f"# fetched {len(markets)} sports markets passing thresholds", file=sys.stderr)

    rows = []
    # Keep the full Gamma object out-of-band for optional enrichers.  Identity,
    # line, scheduled time, rules, fee schedule, and token validation cannot be
    # reconstructed safely from the compact display row.
    markets_by_id = {str(m.get("id")): m for m in markets if m.get("id") is not None}
    for m in markets:
        lens, yes, no, days = categorize(m)
        if days <= 0 or days * 24 > args.hours:
            continue
        market_fee_rate = pm_fees.fee_rate(m)
        # APY for the dominant side
        if yes >= no:
            apy = annualized_apy(yes, days, market_fee_rate)
            buy_side = "YES"
            mark = yes
        else:
            apy = annualized_apy(no, days, market_fee_rate)
            buy_side = "NO"
            mark = no
        try:
            outcomes_list = json.loads(m.get("outcomes", "[]")) if isinstance(m.get("outcomes"), str) else m.get("outcomes", [])
        except Exception:
            outcomes_list = []
        rows.append({
            "question": m.get("question", "?"),
            "slug": m.get("slug", ""),
            "outcomes": outcomes_list,
            "lens": lens,
            "yes": yes,
            "no": no,
            "buy_side": buy_side,
            "mark": mark,
            "apy_pct": apy * 100 if apy != float("inf") else float("inf"),
            "clears_hurdle": apy >= args.hurdle_apy if apy != float("inf") else True,
            "days_to_resolve": round(days, 2),
            "vol24h": float(m.get("volume24hr", 0) or 0),
            "liq": float(m.get("liquidityNum", 0) or 0),
            "id": m.get("id"),
            "tokens": m.get("clobTokenIds"),
            "game_start_time": m.get("gameStartTime"),
            "in_play": is_in_play(m),
        })

    rows.sort(key=lambda r: r["apy_pct"] if r["apy_pct"] != float("inf") else 9e9, reverse=True)
    rows = rows[: args.limit]

    # Fetch bookie consensus for top-N if requested
    if args.with_consensus:
        eligible_rows = [r for r in rows if not r["in_play"]]
        skipped_rows = [r for r in rows if r["in_play"]]
        for r in skipped_rows:
            r["consensus_summary"] = "SKIP_IN_PLAY: pregame odds are not comparable"
        selected_rows = eligible_rows[: args.consensus_top_n]
        print(f"# fetching bookie consensus for top {len(selected_rows)} pregame candidates "
              f"(~30s each via scoped worker); skipped {len(skipped_rows)} in-play", file=sys.stderr)
        for i, r in enumerate(selected_rows):
            source_market = markets_by_id.get(str(r.get("id")), {})
            market_context = {
                "question": source_market.get("question"),
                "description": source_market.get("description"),
                "sportsMarketType": source_market.get("sportsMarketType"),
                "outcomes": source_market.get("outcomes"),
                "gameStartTime": source_market.get("gameStartTime"),
            }
            cons = fetch_bookie_consensus(r["question"], r["days_to_resolve"] * 24,
                                          outcomes=r.get("outcomes"),
                                          market_context=market_context)
            r["consensus"] = cons
            if "yes_prob" in cons:
                bookie_yes = float(cons["yes_prob"])
                pm_yes = r["yes"]
                # Delta: PM YES - bookie YES (positive = PM overprices YES)
                r["pm_vs_bookie_pp"] = round((pm_yes - bookie_yes) * 100, 2)
                r["consensus_summary"] = f"bookie={bookie_yes:.3f} delta={r['pm_vs_bookie_pp']:+.1f}pp ({cons.get('confidence','?')}/{cons.get('source','?')[:25]})"
            else:
                r["pm_vs_bookie_pp"] = None
                r["consensus_summary"] = f"NO_CONSENSUS: {cons.get('error', '?')[:60]}"
            print(f"  [{i+1}/{len(selected_rows)}] {r['question'][:50]}: {r.get('consensus_summary','?')}", file=sys.stderr)

    # Optional public Kalshi comparison.  This receives only the final PM
    # shortlist, uses no credentials, and never exposes an execution method.
    if args.with_kalshi:
        from kalshi_consensus import KalshiConsensusAdapter

        top_n = max(0, min(args.kalshi_top_n, KALSHI_TOP_N_HARD_CAP, len(rows)))
        print(f"# comparing live Kalshi books for top {top_n} shortlisted candidates "
              f"(public REST, read-only)...", file=sys.stderr)
        with KalshiConsensusAdapter() as adapter:
            for i, row in enumerate(rows[:top_n]):
                full_market = markets_by_id.get(str(row.get("id")))
                result = adapter.compare(full_market or {})
                row["pm_vs_kalshi"] = result
                detail = result.get("best_fee_only_snapshot_spread_pp")
                suffix = f" best={detail:+.2f}pp" if isinstance(detail, (int, float)) else ""
                print(f"  [{i+1}/{top_n}] {row['question'][:50]}: "
                      f"{result.get('status','?')}/{result.get('reason','?')}{suffix}",
                      file=sys.stderr)

    if args.json:
        print(json.dumps({"results": rows}, indent=2, default=str))
        return 0

    print(f"\n# top {len(rows)} candidates (resolves <={args.hours}h):\n")
    for r in rows:
        # Profit per $1 if dominant side wins
        profit_per_dollar = (1.0 - r['mark']) / r['mark'] if r['mark'] > 0 else 0
        # APY display
        apy_pct = r['apy_pct']
        if apy_pct >= 1e6:
            apy_str = "  >1e6%"
        else:
            apy_str = f"{apy_pct:>9.1f}%"
        hurdle = "✓" if r['clears_hurdle'] else " "
        cons_str = ""
        if "consensus_summary" in r:
            cons_str = f"  {r['consensus_summary']}"
        if "pm_vs_kalshi" in r:
            kalshi = r["pm_vs_kalshi"]
            if kalshi.get("status") == "matched":
                cons_str += (
                    f"  kalshi_fee_only_snapshot="
                    f"{kalshi['best_fee_only_snapshot_spread_pp']:+.2f}pp"
                )
            else:
                cons_str += f"  kalshi={kalshi.get('status','?')}:{kalshi.get('reason','?')}"
        print(f"  {r['lens']:20s} {r['buy_side']}@${r['mark']:.4f}  +{profit_per_dollar*100:5.2f}%  d={r['days_to_resolve']:.1f}  v24=${r['vol24h']:>7.0f}  {r['question'][:55]}{cons_str}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
