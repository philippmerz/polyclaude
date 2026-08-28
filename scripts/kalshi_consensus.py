#!/usr/bin/env python3
"""Strict, read-only Kalshi comparison for shortlisted Polymarket sports markets.

This module deliberately is *not* a Kalshi discovery crawler.  It accepts one
full Gamma market, uses its league, market type, participants, and scheduled
time to make one bounded public milestone lookup, and only then fetches the
single matching Kalshi event/book.  Unsupported or ambiguous cases fail
closed.  There are no authenticated endpoints or order methods here.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import datetime as dt
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
import re
import time
import unicodedata
from typing import Any, Callable
from zoneinfo import ZoneInfo

import httpx

import pm_fees


KALSHI_BASE = "https://external-api.kalshi.com/trade-api/v2"
PM_CLOB_BASE = "https://clob.polymarket.com"
KALSHI_MIN_ORDER_SIZE = Decimal("1")
MAX_COMPARE_SIZE = Decimal("1000")
MILESTONE_LIMIT = 200
TIME_TOLERANCE_SECONDS = 60
START_SAFETY_SECONDS = 300
PM_BOOK_MAX_AGE_SECONDS = 120
PM_BOOK_FUTURE_SKEW_SECONDS = 5


class PublicDataError(RuntimeError):
    """A bounded public-data request could not produce safe current data."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class LeagueRoute:
    key: str
    slug_prefixes: tuple[str, ...]
    category: str
    milestone_type: str
    competition: str | None
    event_prefixes: dict[str, tuple[str, ...]]


# Explicit allowlist.  It prevents a candidate from silently crossing leagues
# merely because two shortened team names happen to look similar.
LEAGUE_ROUTES: tuple[LeagueRoute, ...] = (
    LeagueRoute("mlb", ("mlb-",), "Sports", "baseball_game", None, {
        "moneyline": ("KXMLBGAME-",),
        "totals": ("KXMLBTOTAL-",),
    }),
    LeagueRoute("atp", ("atp-",), "Sports", "tennis_tournament_singles", "ATP", {
        "moneyline": ("KXATPMATCH-",),
        "totals": ("KXATPGTOTAL-",),
    }),
    LeagueRoute("wta", ("wta-",), "Sports", "tennis_tournament_singles", "WTA", {
        "moneyline": ("KXWTAMATCH-",),
        "totals": ("KXWTAGTOTAL-",),
    }),
    LeagueRoute("ufc", ("ufc-",), "Sports", "mma_match", "UFC", {
        "moneyline": ("KXUFCFIGHT-",),
    }),
    LeagueRoute("valorant", ("val-", "valorant-"), "Esports", "esports_match", "Valorant", {
        "moneyline": ("KXVALORANTGAME-",),
    }),
    LeagueRoute("lol", ("lol-",), "Esports", "esports_match", "League of Legends", {
        "moneyline": ("KXLOLGAME-",),
    }),
    LeagueRoute("dota2", ("dota2-", "dota-"), "Esports", "esports_match", "Dota 2", {
        "moneyline": ("KXDOTA2GAME-",),
    }),
    LeagueRoute("cs2", ("cs2-", "cs-"), "Esports", "esports_match", "CS2", {
        "moneyline": ("KXCS2GAME-",),
    }),
    LeagueRoute("epl", ("epl-",), "Sports", "soccer_tournament_multi_leg", "EPL", {
        "moneyline": ("KXEPLGAME-",),
    }),
    LeagueRoute("laliga", ("lal-",), "Sports", "soccer_tournament_multi_leg", "La Liga", {
        "moneyline": ("KXLALIGAGAME-",),
    }),
    LeagueRoute("eredivisie", ("ere-",), "Sports", "soccer_tournament_multi_leg", "Eredivisie", {
        "moneyline": ("KXEREDIVISIEGAME-",),
    }),
)


# Kalshi's milestone display intentionally shortens MLB team names.  These are
# explicit identities, not fuzzy aliases; anything outside this table remains
# unsupported rather than being guessed from a city substring.
MLB_TEAM_ALIASES = {
    "arizona diamondbacks": "arizona",
    "athletics": "a s",
    "atlanta braves": "atlanta",
    "baltimore orioles": "baltimore",
    "boston red sox": "boston",
    "chicago cubs": "chicago c",
    "chicago white sox": "chicago ws",
    "cincinnati reds": "cincinnati",
    "cleveland guardians": "cleveland",
    "colorado rockies": "colorado",
    "detroit tigers": "detroit",
    "houston astros": "houston",
    "kansas city royals": "kansas city",
    "los angeles angels": "los angeles a",
    "los angeles dodgers": "los angeles d",
    "miami marlins": "miami",
    "milwaukee brewers": "milwaukee",
    "minnesota twins": "minnesota",
    "new york mets": "new york m",
    "new york yankees": "new york y",
    "philadelphia phillies": "philadelphia",
    "pittsburgh pirates": "pittsburgh",
    "san diego padres": "san diego",
    "san francisco giants": "san francisco",
    "seattle mariners": "seattle",
    "st louis cardinals": "st louis",
    "tampa bay rays": "tampa bay",
    "texas rangers": "texas",
    "toronto blue jays": "toronto",
    "washington nationals": "washington",
}


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode().lower()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _decimal(value: object) -> Decimal | None:
    try:
        out = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return out if out.is_finite() else None


def _parse_time(value: object) -> dt.datetime | None:
    if not value:
        return None
    try:
        out = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if out.tzinfo is None:
        out = out.replace(tzinfo=dt.timezone.utc)
    return out.astimezone(dt.timezone.utc)


def _parse_json_list(value: object) -> list[Any] | None:
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, list) else None


def _split_participants(title: object) -> tuple[str, str] | None:
    text = str(title or "").strip()
    # Drop market-family decoration but retain the actual two competitors.
    text = re.sub(r"\s+-\s+(?:More Markets|Exact Score|Halftime Result).*$", "", text, flags=re.I)
    text = re.sub(r"\s+\((?:BO\d+|[^)]*(?:card|weight|prelims)[^)]*)\).*$", "", text, flags=re.I)
    # Kalshi event titles append a small, explicit contract-family suffix.
    # Strip only recognized suffixes; arbitrary trailing text remains a hard
    # participant mismatch rather than being fuzzily discarded.
    text = re.sub(
        r"\s*:\s*(?:total\s+(?:runs|points|games|goals|rounds)|"
        r"(?:game|match|fight)\s+winner|winner)\s*$",
        "",
        text,
        flags=re.I,
    )
    if ":" in text and re.search(r"\bvs\.?\b", text.rsplit(":", 1)[-1], re.I):
        text = text.rsplit(":", 1)[-1].strip()
    parts = re.split(r"\s+(?:vs\.?|at)\s+", text, maxsplit=1, flags=re.I)
    if len(parts) != 2 or not all(_norm(p) for p in parts):
        return None
    return parts[0].strip(), parts[1].strip()


def _event(market: dict) -> dict | None:
    events = market.get("events")
    return events[0] if isinstance(events, list) and len(events) == 1 and isinstance(events[0], dict) else None


def _participants(market: dict) -> tuple[str, str] | None:
    outcomes = _parse_json_list(market.get("outcomes"))
    generic = {"yes", "no", "over", "under"}
    if outcomes and len(outcomes) == 2 and all(_norm(x) not in generic for x in outcomes):
        if len({_norm(x) for x in outcomes}) == 2:
            return str(outcomes[0]), str(outcomes[1])
    event = _event(market)
    return _split_participants((event or {}).get("title"))


def _route_for(market: dict, market_type: str) -> LeagueRoute | None:
    slug = str(market.get("slug") or "").lower()
    matches = [route for route in LEAGUE_ROUTES
               if any(slug.startswith(prefix) for prefix in route.slug_prefixes)
               and market_type in route.event_prefixes]
    return matches[0] if len(matches) == 1 else None


_PERIOD_RE = re.compile(
    r"\b(?:first|second|third|fourth|1st|2nd|3rd|4th)\s+"
    r"(?:half|quarter|period|inning|set|map)\b|\b(?:set|map|inning)\s*\d+\b",
    re.I,
)


_SEGMENT_SCOPE_RE = re.compile(
    r"\b(?:first|opening|through|after)\s+(?:the\s+)?(?:end\s+of\s+(?:the\s+)?)?"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+"
    r"(?:innings?|sets?|maps?|rounds?|periods?|quarters?|halves?)\b|"
    r"\b(?:innings?|sets?|maps?|rounds?|periods?|quarters?)\s*(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b|"
    r"\bfirst\s+\d+\s+minutes?\b|\bregular(?:ation)?\s+(?:play|time)\b|"
    r"\b(?:extra\s+time|overtime|penalty\s+shootout)\b",
    re.I,
)


_ORDINARY_PREDICATE_QUALIFIER_RE = re.compile(
    r"\bextra[-\s]+innings?\b|\bthrough\s+regulation\b|"
    r"\bregulation[-\s]+innings?\b|\b(?:includes?|excludes?|including|excluding|except(?:\s+for)?|only|"
    r"regardless\s+of|unless|provided\s+that|subject\s+to|as\s+long\s+as|"
    r"if\s+and\s+only\s+if)\b|\b(?:do(?:es)?\s+not\s+count|counts?\s+only)\b|"
    r"\b(?:at\s+least|minimum\s+of|fewer\s+than|no\s+more\s+than)\s+"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+innings?\b|"
    r"\b(?:\d+|seven|eight|nine|ten|seventh|eighth|ninth|tenth)[-\s]+innings?\b",
    re.I,
)


def _displayed_total_lines(market: dict) -> set[Decimal]:
    values: set[Decimal] = set()
    display_re = re.compile(
        r"\b(?:o\s*/\s*u|over\s*/\s*under|over[- ]under|total(?:\s+(?:runs|points|games|goals))?)"
        r"\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)\b",
        re.I,
    )
    for field in (market.get("question"), market.get("groupItemTitle")):
        for raw in display_re.findall(str(field or "")):
            parsed = _decimal(raw)
            if parsed is not None:
                values.add(parsed)
    slug = str(market.get("slug") or "").lower()
    for whole, fraction in re.findall(
        r"(?:^|-)(?:total|o-u|ou|over-under)-([0-9]+)(?:pt([0-9]+))?(?:-|$)", slug
    ):
        parsed = _decimal(f"{whole}.{fraction}" if fraction else whole)
        if parsed is not None:
            values.add(parsed)
    return values


def _candidate_spec(market: dict, *, now: dt.datetime | None = None) -> tuple[dict | None, str | None]:
    if not isinstance(market, dict):
        return None, "missing_full_gamma_market"
    event = _event(market)
    if event is None:
        return None, "ambiguous_gamma_event"
    # This adapter prices immediate taker legs, so missing state is not the
    # same thing as affirmative tradeability. Gamma's current full-market
    # schema supplies all four fields.
    if (market.get("active") is not True
            or market.get("closed") is not False
            or market.get("acceptingOrders") is not True):
        return None, "pm_market_not_tradeable"
    if market.get("enableOrderBook") is not True:
        return None, "pm_orderbook_not_enabled"
    if market.get("isMve") or market.get("mve") or market.get("mve_collection_ticker"):
        return None, "pm_mve_unsupported"
    if market.get("live") or event.get("live") or event.get("ended"):
        return None, "live_or_ended_event"
    text = " ".join(str(x or "") for x in (
        market.get("question"), market.get("groupItemTitle"), market.get("description")
    ))
    if _ORDINARY_PREDICATE_QUALIFIER_RE.search(text):
        return None, "unparsed_ordinary_predicate_qualifier"
    if _PERIOD_RE.search(text) or _SEGMENT_SCOPE_RE.search(text):
        return None, "period_market_unsupported"

    market_type = str(market.get("sportsMarketType") or "").lower()
    # Spreads are deliberately deferred: PM's signed handicap changes which
    # participant/side maps to Kalshi's positive margin threshold.  Treating
    # abs(line) as equivalent can invert the hedge, so v1 fails closed.
    if market_type not in {"moneyline", "totals"}:
        return None, "unsupported_market_type"
    route = _route_for(market, market_type)
    if route is None:
        return None, "unsupported_or_ambiguous_league"
    # V1's canonical ordinary-predicate parser below is deliberately limited
    # to discrete MLB run totals. Tennis games and other units need their own
    # push/retirement grammar before they can safely emit a matched spread.
    if market_type == "totals" and route.key != "mlb":
        return None, "unsupported_totals_predicate_family"

    participants = _participants(market)
    if participants is None or len({_norm(x) for x in participants}) != 2:
        return None, "ambiguous_participants"
    start = _parse_time(market.get("gameStartTime") or event.get("startTime"))
    if start is None:
        return None, "missing_scheduled_time"
    current = now or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=dt.timezone.utc)
    current = current.astimezone(dt.timezone.utc)
    if start <= current + dt.timedelta(seconds=START_SAFETY_SECONDS):
        return None, "event_started_or_inside_start_safety_window"

    line: Decimal | None = None
    if market_type == "moneyline":
        if market.get("line") not in (None, ""):
            return None, "unexpected_moneyline_line"
    else:
        line = _decimal(market.get("line"))
        if line is None:
            return None, "missing_or_invalid_line"
        displayed_lines = _displayed_total_lines(market)
        if displayed_lines != {line}:
            return None, "pm_displayed_total_line_mismatch"
        if market_type == "totals" and line % Decimal("1") != Decimal("0.5"):
            return None, "integer_total_push_unsupported"

    return {
        "event": event,
        "market_type": market_type,
        "route": route,
        "participants": participants,
        "start": start,
        "line": line,
    }, None


_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "fourteen": 14,
}


def _duration_hours(text: str) -> str | None:
    low = text.lower()
    if re.search(r"remain open until (?:the (?:game|match|fight) (?:has been )?completed|completed)", low):
        return "until_completed"
    match = re.search(r"(?:within|more than|over|beyond)\s+([a-z]+|\d+)\s*(hours?|days?|weeks?)", low)
    if not match:
        return None
    raw, unit = match.groups()
    number = int(raw) if raw.isdigit() else _NUMBER_WORDS.get(raw)
    if number is None:
        return None
    multiplier = 1 if unit.startswith("hour") else 24 if unit.startswith("day") else 168
    return str(number * multiplier)


def _action(sentence: str) -> str | None:
    low = sentence.lower()
    if "fair price" in low or "fair market price" in low:
        return "fair"
    if re.search(r"50\s*[-/]\s*50|\$?0\.50|50/50", low):
        return "half"
    if re.search(r"resolv(?:e|es|ed|ing)\s+(?:to\s+)?(?:\"?no\"?|no)\b", low):
        return "no"
    if "void" in low or "refund" in low:
        return "void"
    if "official result" in low or "player who advances" in low or "winner who advances" in low:
        return "official_result"
    if "remain open" in low:
        return "remain_open"
    return None


_RULE_TRIGGERS = {
    "cancel": ("cancel", "does not occur", "not played at all"),
    "postpone": ("postpon", "reschedul", "delay"),
    "tie_draw": (" tie", "draw"),
    "no_contest": ("no contest", "not scored"),
    "walkover": ("walkover",),
    "forfeit": ("forfeit", "default"),
    "retirement": ("retirement", "retires"),
    "disqualification": ("disqualification", "disqualified"),
    "abandoned_suspended_shortened": ("abandon", "suspend", "shorten"),
}


def rules_fingerprint(text: object) -> dict | None:
    """Extract conservative exceptional-settlement semantics from rule text."""
    raw = str(text or "").strip()
    if not raw:
        return None
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", raw) if s.strip()]
    actions: dict[str, tuple[str, ...]] = {}
    for trigger, needles in _RULE_TRIGGERS.items():
        found: set[str] = set()
        mentioned = False
        for sentence in sentences:
            low = " " + sentence.lower()
            if any(needle in low for needle in needles):
                mentioned = True
                action = _action(sentence)
                if action:
                    found.add(action)
        if mentioned and not found:
            return None
        if found:
            actions[trigger] = tuple(sorted(found))
    # Cancellation must be explicit; otherwise series-level terms might change
    # the payout and this adapter has no basis to call the contracts equivalent.
    if "cancel" not in actions:
        return None
    if any(len(value) != 1 for value in actions.values()):
        return None
    postpone_window = _duration_hours(raw) if "postpone" in actions else None
    if "postpone" in actions and postpone_window is None:
        return None
    return {"actions": actions, "postpone_window_hours": postpone_window}


def _pm_resolution_text(pm_market: dict) -> tuple[str, str]:
    """Return the child contract's rules, with parent-event text as fallback.

    Gamma parent event descriptions commonly describe the moneyline while a
    child market is a total.  Concatenating the two imports sibling semantics,
    so a nonempty child description is authoritative for this comparison.
    """
    child = str(pm_market.get("description") or "").strip()
    if child:
        return child, "market.description"
    return str((_event(pm_market) or {}).get("description") or "").strip(), "event.description_fallback"


def compatible_rules(pm_market: dict, kalshi_market: dict) -> tuple[bool, dict]:
    pm_text, pm_source = _pm_resolution_text(pm_market)
    kalshi_text = "\n".join(str(x or "") for x in (
        kalshi_market.get("rules_primary"), kalshi_market.get("rules_secondary")
    ))
    pm_fp = rules_fingerprint(pm_text)
    kalshi_fp = rules_fingerprint(kalshi_text)
    evidence = {"pm": pm_fp, "pm_source": pm_source, "kalshi": kalshi_fp}
    if pm_fp is None or kalshi_fp is None:
        evidence["reason"] = "ambiguous_cancellation_or_postponement_rules"
        return False, evidence
    if pm_fp != kalshi_fp:
        evidence["reason"] = "cancellation_void_rules_mismatch"
        return False, evidence
    all_actions = {action for value in pm_fp["actions"].values() for action in value}
    if all_actions & {"fair", "void"}:
        evidence["reason"] = "non_binary_fixed_payout_rules"
        return False, evidence
    evidence["reason"] = "compatible"
    return True, evidence


_MONTH_NUMBER = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
_TZ_ZONE = {
    "ET": "America/New_York", "EST": "America/New_York", "EDT": "America/New_York",
    "CT": "America/Chicago", "CST": "America/Chicago", "CDT": "America/Chicago",
    "MT": "America/Denver", "MST": "America/Denver", "MDT": "America/Denver",
    "PT": "America/Los_Angeles", "PST": "America/Los_Angeles", "PDT": "America/Los_Angeles",
    "UTC": "UTC", "GMT": "UTC",
}
_RULE_TIME_RE = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+(\d{1,2})(?:,\s*(\d{4}))?\s+at\s+(\d{1,2}):(\d{2})\s*"
    r"(AM|PM)\s*(ET|EST|EDT|CT|CST|CDT|MT|MST|MDT|PT|PST|PDT|UTC|GMT)\b",
    re.I,
)


def _scheduled_times_in_rules(text: str, reference: dt.datetime) -> list[dt.datetime] | None:
    parsed: list[dt.datetime] = []
    for match in _RULE_TIME_RE.finditer(text):
        month_raw, day_raw, year_raw, hour_raw, minute_raw, ampm, zone_raw = match.groups()
        month = _MONTH_NUMBER.get(month_raw.lower())
        if month is None:
            return None
        hour = int(hour_raw) % 12 + (12 if ampm.upper() == "PM" else 0)
        try:
            local = dt.datetime(
                int(year_raw or reference.year), month, int(day_raw), hour, int(minute_raw),
                tzinfo=ZoneInfo(_TZ_ZONE[zone_raw.upper()]),
            )
        except (KeyError, ValueError):
            return None
        parsed.append(local.astimezone(dt.timezone.utc))
    return parsed


def _tokens_present(text: str, participant: str, route: LeagueRoute) -> bool:
    haystack = set(_norm(text).split())
    needle = set(_participant_key(participant, route).split())
    return bool(needle) and needle.issubset(haystack)


def _mlb_total_rule_line(text: str) -> Decimal | None:
    """Canonicalize only the two audited full-game MLB total grammars.

    Polymarket commonly states ``9 or more runs`` for an 8.5 line, while
    Kalshi states ``more 8.5 runs``. Anything outside these exact run-total
    forms is unsupported rather than inferred from a stray number.
    """
    normalized = " ".join(str(text or "").lower().split())
    canonical: set[Decimal] = set()
    for raw in re.findall(
        r"\b(?:combine\s+to\s+score|collectively\s+score)\s+"
        r"more(?:\s+than)?\s+(\d+(?:\.\d+)?)\s+runs?\b",
        normalized,
    ):
        value = _decimal(raw)
        if value is not None:
            canonical.add(value)
    for raw in re.findall(
        r"\b(?:combine\s+to\s+score|collectively\s+score)\s+"
        r"(\d+(?:\.\d+)?)\s+or\s+more\s+runs?\b",
        normalized,
    ):
        threshold = _decimal(raw)
        if threshold is None or threshold != threshold.to_integral_value():
            return None
        canonical.add(threshold - Decimal("0.5"))
    return next(iter(canonical)) if len(canonical) == 1 else None


def _winner_clause_matches(text: str, participant: str, route: LeagueRoute) -> bool:
    expected = set(_participant_key(participant, route).split())
    if not expected:
        return False
    for subject in re.findall(r"\bif\s+(.{1,120}?)\s+wins?\b", str(text or ""), re.I):
        if expected.issubset(set(_norm(subject).split())):
            return True
    return False


def _ordinary_contract_scope(pm_market: dict, kalshi_market: dict, spec: dict) -> tuple[bool, dict]:
    """Prove the ordinary (non-exception) predicate is the same full event."""
    pm_text, pm_source = _pm_resolution_text(pm_market)
    kalshi_text = "\n".join(str(x or "") for x in (
        kalshi_market.get("title"), kalshi_market.get("yes_sub_title"),
        kalshi_market.get("rules_primary"), kalshi_market.get("rules_secondary"),
    ))
    evidence: dict[str, object] = {
        "pm_rules_source": pm_source,
        "pm_scope": "full_event_from_structured_sports_type",
        "kalshi_scope": None,
    }
    if (_ORDINARY_PREDICATE_QUALIFIER_RE.search(pm_text)
            or _ORDINARY_PREDICATE_QUALIFIER_RE.search(kalshi_text)):
        evidence["reason"] = "unparsed_ordinary_predicate_qualifier"
        return False, evidence
    if (_PERIOD_RE.search(pm_text) or _SEGMENT_SCOPE_RE.search(pm_text)
            or _PERIOD_RE.search(kalshi_text) or _SEGMENT_SCOPE_RE.search(kalshi_text)):
        evidence["reason"] = "period_or_partial_event_scope"
        return False, evidence

    route: LeagueRoute = spec["route"]
    participants = spec["participants"]
    if spec["market_type"] == "totals":
        if not all(_tokens_present(pm_text, p, route) for p in participants):
            evidence["reason"] = "pm_rules_participant_mismatch"
            return False, evidence
        if not all(_tokens_present(kalshi_text, p, route) for p in participants):
            evidence["reason"] = "kalshi_rules_participant_mismatch"
            return False, evidence
        pm_rule_line = _mlb_total_rule_line(pm_text)
        kalshi_rule_line = _mlb_total_rule_line(str(kalshi_market.get("rules_primary") or ""))
        evidence["ordinary_predicate"] = {
            "metric": "full_game_runs",
            "pm_canonical_line": float(pm_rule_line) if pm_rule_line is not None else None,
            "kalshi_canonical_line": (
                float(kalshi_rule_line) if kalshi_rule_line is not None else None
            ),
            "structured_line": float(spec["line"]),
        }
        if pm_rule_line != spec["line"] or kalshi_rule_line != spec["line"]:
            evidence["reason"] = "ordinary_total_rule_predicate_mismatch"
            return False, evidence
    else:
        yes_participant = str(kalshi_market.get("yes_sub_title") or "").strip()
        kalshi_primary = str(kalshi_market.get("rules_primary") or "")
        evidence["ordinary_predicate"] = {
            "metric": "selected_participant_wins",
            "selected_yes_participant": yes_participant,
        }
        if (not yes_participant
                or not _winner_clause_matches(pm_text, yes_participant, route)):
            evidence["reason"] = "pm_moneyline_rules_participant_mismatch"
            return False, evidence
        if not _winner_clause_matches(kalshi_primary, yes_participant, route):
            evidence["reason"] = "kalshi_moneyline_rules_participant_mismatch"
            return False, evidence

    pm_times = _scheduled_times_in_rules(pm_text, spec["start"])
    kalshi_times = _scheduled_times_in_rules(kalshi_text, spec["start"])
    if pm_times is None or kalshi_times is None:
        evidence["reason"] = "unparseable_rules_scheduled_time"
        return False, evidence
    evidence["pm_explicit_scheduled_times"] = [x.isoformat() for x in pm_times]
    evidence["kalshi_explicit_scheduled_times"] = [x.isoformat() for x in kalshi_times]
    if pm_times and not all(abs((x - spec["start"]).total_seconds()) <= TIME_TOLERANCE_SECONDS
                            for x in pm_times):
        evidence["reason"] = "pm_rules_scheduled_time_mismatch"
        return False, evidence
    # The selected Kalshi child must affirmatively identify the scheduled full
    # event. Merely omitting words like "first five innings" is not proof.
    if not kalshi_times or not all(
        abs((x - spec["start"]).total_seconds()) <= TIME_TOLERANCE_SECONDS
        for x in kalshi_times
    ):
        evidence["reason"] = "kalshi_rules_scheduled_time_mismatch_or_missing"
        return False, evidence
    if not re.search(r"\b(?:game|match|fight|bout)\s+(?:originally\s+)?scheduled\b", kalshi_text, re.I):
        evidence["reason"] = "kalshi_full_event_scope_not_proven"
        return False, evidence
    evidence["kalshi_scope"] = "full_event_from_allowlisted_series_and_scheduled_rules"
    evidence["reason"] = "exact_full_event_scope"
    return True, evidence


class PublicJSONClient:
    """Bounded GET-only client with metadata memoization and 429 backoff.

    Live order books are always requested with ``cacheable=False``.  A failed
    refresh therefore cannot fall back to an older quote.
    """

    def __init__(self, client: Any | None = None, *, max_attempts: int = 3,
                 backoff_seconds: float = 0.25,
                 sleep_fn: Callable[[float], None] = time.sleep,
                 max_cache_entries: int = 128):
        self._owned = client is None
        self.client = client or httpx.Client(timeout=15.0, follow_redirects=False)
        self.max_attempts = max(1, min(int(max_attempts), 4))
        self.backoff_seconds = max(0.0, min(float(backoff_seconds), 2.0))
        self.sleep_fn = sleep_fn
        self.max_cache_entries = max(1, min(int(max_cache_entries), 256))
        self.cache: OrderedDict[tuple, dict] = OrderedDict()

    def close(self) -> None:
        if self._owned:
            self.client.close()

    def get(self, url: str, *, params: dict | None = None, cacheable: bool = False) -> dict:
        key = (url, tuple(sorted((params or {}).items())))
        if cacheable and key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        last_status = 0
        for attempt in range(self.max_attempts):
            try:
                response = self.client.get(url, params=params)
            except Exception as exc:
                if attempt + 1 >= self.max_attempts:
                    raise PublicDataError("network_error", str(exc)) from exc
                self.sleep_fn(self.backoff_seconds * (2 ** attempt))
                continue
            last_status = int(getattr(response, "status_code", 0))
            if last_status == 429:
                if attempt + 1 < self.max_attempts:
                    retry_after = _decimal((getattr(response, "headers", {}) or {}).get("Retry-After"))
                    delay = self.backoff_seconds * (2 ** attempt)
                    if retry_after is not None:
                        delay = max(delay, min(float(retry_after), 2.0))
                    self.sleep_fn(delay)
                    continue
                raise PublicDataError("http_429_exhausted", "public endpoint remained rate-limited")
            if last_status >= 500 and attempt + 1 < self.max_attempts:
                self.sleep_fn(self.backoff_seconds * (2 ** attempt))
                continue
            if last_status != 200:
                raise PublicDataError(f"http_{last_status}", f"GET failed with HTTP {last_status}")
            try:
                data = response.json()
            except Exception as exc:
                raise PublicDataError("invalid_json", str(exc)) from exc
            if not isinstance(data, dict):
                raise PublicDataError("invalid_payload", "expected a JSON object")
            if cacheable:
                self.cache[key] = data
                self.cache.move_to_end(key)
                while len(self.cache) > self.max_cache_entries:
                    self.cache.popitem(last=False)
            return data
        raise PublicDataError(f"http_{last_status}", "GET failed")


def _milestone_params(spec: dict) -> dict:
    minimum_start = spec["start"] - dt.timedelta(minutes=5)
    maximum_start = spec["start"] + dt.timedelta(minutes=5)
    route: LeagueRoute = spec["route"]
    params: dict[str, object] = {
        "limit": MILESTONE_LIMIT,
        "minimum_start_date": minimum_start.isoformat().replace("+00:00", "Z"),
        "maximum_start_date": maximum_start.isoformat().replace("+00:00", "Z"),
        "category": route.category,
        "type": route.milestone_type,
    }
    if route.competition:
        params["competition"] = route.competition
    return params


def _participant_key(name: str, route: LeagueRoute) -> str:
    normalized = _norm(name)
    if route.key == "mlb":
        return MLB_TEAM_ALIASES.get(normalized, normalized)
    if route.key in {"atp", "wta", "ufc"}:
        # Some official feeds reverse a person's family/given name.  Exact
        # token sets preserve identity without fuzzy spelling acceptance.
        return " ".join(sorted(normalized.split()))
    return normalized


def _same_participant_pair(left: tuple[str, str], right: tuple[str, str],
                           route: LeagueRoute) -> bool:
    return sorted(_participant_key(x, route) for x in left) == sorted(
        _participant_key(x, route) for x in right
    )


def _surname_shortlist_pair(left: tuple[str, str], right: tuple[str, str],
                            route: LeagueRoute) -> bool:
    """Allow unique surname-only discovery for individual matchups.

    This is only a discovery key.  Exact full outcome names are required from
    the fetched event before any book request.
    """
    if route.key not in {"atp", "wta"}:
        return False
    left_last = [_norm(x).split()[-1:] for x in left]
    right_last = [_norm(x).split()[-1:] for x in right]
    if not all(left_last) or not all(right_last):
        return False
    lvals = [x[0] for x in left_last]
    rvals = [x[0] for x in right_last]
    return len(set(lvals)) == 2 and sorted(lvals) == sorted(rvals)


def _matching_milestone(spec: dict, milestones: list[dict]) -> tuple[dict | None, str | None]:
    matches = []
    prefixes = spec["route"].event_prefixes[spec["market_type"]]
    for item in milestones:
        if not isinstance(item, dict) or item.get("category") != spec["route"].category:
            continue
        if item.get("type") != spec["route"].milestone_type:
            continue
        details = item.get("details")
        status = _norm(details.get("status")) if isinstance(details, dict) else ""
        # Status is nested under details in the live API. Missing status is not
        # equivalent to pre-event: MLB currently reports "scheduled" and ATP
        # reports "not_started" (normalized here to "not started").
        if status not in {"scheduled", "not started"}:
            continue
        scheduled = _parse_time(item.get("start_date"))
        if scheduled is None or abs((scheduled - spec["start"]).total_seconds()) > TIME_TOLERANCE_SECONDS:
            continue
        pair = _split_participants(item.get("title"))
        exact_identity = pair is not None and _same_participant_pair(
            spec["participants"], pair, spec["route"]
        )
        surname_discovery = (pair is not None and spec["market_type"] == "moneyline"
                             and _surname_shortlist_pair(spec["participants"], pair,
                                                        spec["route"]))
        if not exact_identity and not surname_discovery:
            continue
        tickers = [str(t) for t in (item.get("related_event_tickers") or [])
                   if any(str(t).startswith(prefix) for prefix in prefixes)]
        if len(tickers) != 1:
            continue
        candidate = dict(item)
        candidate["_matched_event_ticker"] = tickers[0]
        candidate["_participant_match_method"] = (
            "explicit_identity" if exact_identity else "surname_discovery_then_full_event_identity"
        )
        matches.append(candidate)
    if not matches:
        return None, "no_exact_participant_time_lineage_match"
    if len(matches) != 1:
        return None, "ambiguous_milestone_match"
    return matches[0], None


def _select_kalshi_markets(spec: dict, markets: list[dict], pm_market: dict) -> tuple[dict | None, str | None]:
    if any(isinstance(m, dict) and m.get("is_provisional") for m in markets):
        return None, "kalshi_provisional_market_unsupported"
    if any(isinstance(m, dict) and (m.get("mve_collection_ticker") or m.get("mve_selected_legs"))
           for m in markets):
        return None, "kalshi_mve_unsupported"
    if any(isinstance(m, dict) and (m.get("live") or m.get("is_live")) for m in markets):
        return None, "kalshi_live_market_unsupported"
    clean = [m for m in markets if isinstance(m, dict)
             and m.get("status") in {"active", "open"}
             and not m.get("mve_collection_ticker")
             and not m.get("mve_selected_legs")]
    if spec["market_type"] == "totals":
        outcomes = _parse_json_list(pm_market.get("outcomes")) or []
        if {_norm(x) for x in outcomes} != {"over", "under"} or len(outcomes) != 2:
            return None, "pm_totals_outcomes_mismatch"
        exact = [m for m in clean
                 if m.get("strike_type") == "greater"
                 and _decimal(m.get("floor_strike")) == spec["line"]
                 and m.get("cap_strike") in (None, "")
                 and m.get("functional_strike") in (None, "")]
        if len(exact) != 1:
            return None, "wrong_or_ambiguous_kalshi_line_or_predicate"
        market = exact[0]
        primary = str(market.get("rules_primary") or "")
        if not re.search(r"\b(?:more|over)\b", primary, re.I):
            return None, "kalshi_market_type_mismatch"
        return {"mode": "binary", "market": market, "yes_means": "Over"}, None

    outcomes = _parse_json_list(pm_market.get("outcomes")) or []
    generic_binary = [_norm(x) for x in outcomes] == ["yes", "no"]
    if generic_binary:
        target = _norm(pm_market.get("groupItemTitle"))
        if not target:
            # Questions like "Will X win ..." are accepted only when X can be
            # extracted without fuzzy matching.
            match = re.match(r"Will\s+(.+?)\s+win\b", str(pm_market.get("question") or ""), re.I)
            target = _norm(match.group(1)) if match else ""
        exact = [m for m in clean if _norm(m.get("yes_sub_title")) == target
                 and re.search(r"\bwins?\b", str(m.get("rules_primary") or ""), re.I)]
        if len(exact) != 1:
            return None, "wrong_or_ambiguous_kalshi_participant"
        return {"mode": "binary", "market": exact[0], "yes_means": "Yes"}, None

    if len(outcomes) != 2 or len({_norm(x) for x in outcomes}) != 2:
        return None, "ambiguous_pm_outcomes"
    mapped: dict[str, dict] = {}
    for outcome in outcomes:
        exact = [m for m in clean if _norm(m.get("yes_sub_title")) == _norm(outcome)
                 and re.search(r"\bwins?\b", str(m.get("rules_primary") or ""), re.I)]
        if len(exact) != 1:
            return None, "wrong_or_ambiguous_kalshi_participant"
        mapped[str(outcome)] = exact[0]
    if len({m.get("ticker") for m in mapped.values()}) != 2:
        return None, "non_unique_kalshi_outcomes"
    return {"mode": "categorical", "markets": mapped}, None


def _pm_fee_known(market: dict) -> bool:
    schedule = market.get("feeSchedule")
    if isinstance(schedule, dict):
        rate = _decimal(schedule.get("rate"))
        exponent = _decimal(schedule.get("exponent"))
        return rate is not None and rate >= 0 and exponent is not None and exponent >= 0
    return market.get("feesEnabled") is False


def _validated_pm_tokens(market: dict) -> tuple[list[str] | None, list[str] | None, str | None]:
    outcomes = _parse_json_list(market.get("outcomes"))
    tokens = _parse_json_list(market.get("clobTokenIds"))
    if not outcomes or not tokens or len(outcomes) != 2 or len(tokens) != 2:
        return None, None, "pm_outcome_token_cardinality"
    outcome_names = [str(x) for x in outcomes]
    token_names = [str(x) for x in tokens]
    if (len({_norm(x) for x in outcome_names}) != 2 or len(set(token_names)) != 2
            or not all(token_names) or not all(token.isdigit() for token in token_names)):
        return None, None, "pm_outcome_token_not_unique"
    return outcome_names, token_names, None


def _parse_pm_levels(raw_levels: object) -> list[tuple[Decimal, Decimal]] | None:
    if not isinstance(raw_levels, list):
        return None
    levels: list[tuple[Decimal, Decimal]] = []
    for raw in raw_levels:
        price = _decimal(raw.get("price") if isinstance(raw, dict) else None)
        qty = _decimal(raw.get("size") if isinstance(raw, dict) else None)
        if price is None or qty is None or not (Decimal("0") < price < Decimal("1")) or qty <= 0:
            return None
        levels.append((price, qty))
    return levels


def _validated_pm_book(payload: dict, *, token: str, condition_id: str,
                       now: dt.datetime) -> tuple[dict | None, str | None]:
    if not isinstance(payload, dict):
        return None, "invalid_pm_book_payload"
    if str(payload.get("asset_id") or "") != token:
        return None, "pm_book_asset_id_mismatch"
    if str(payload.get("market") or "").lower() != condition_id.lower():
        return None, "pm_book_condition_id_mismatch"
    timestamp_ms = _decimal(payload.get("timestamp"))
    if (timestamp_ms is None or timestamp_ms <= 0
            or timestamp_ms != timestamp_ms.to_integral_value()):
        return None, "invalid_pm_book_timestamp"
    try:
        timestamp = dt.datetime.fromtimestamp(float(timestamp_ms / Decimal("1000")), dt.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None, "invalid_pm_book_timestamp"
    age = (now - timestamp).total_seconds()
    if age > PM_BOOK_MAX_AGE_SECONDS or age < -PM_BOOK_FUTURE_SKEW_SECONDS:
        return None, "stale_or_future_pm_book"
    minimum = _decimal(payload.get("min_order_size"))
    if minimum is None or minimum <= 0:
        return None, "invalid_pm_book_min_order_size"
    asks = _parse_pm_levels(payload.get("asks"))
    bids = _parse_pm_levels(payload.get("bids"))
    if asks is None or bids is None:
        return None, "invalid_pm_book_level"
    if asks and bids and max(price for price, _ in bids) >= min(price for price, _ in asks):
        return None, "crossed_pm_book"
    return {
        "asks": asks,
        "bids": bids,
        "min_order_size": minimum,
        "timestamp": timestamp,
        "age_seconds": age,
    }, None


def _walk_pm_asks(levels: list[tuple[Decimal, Decimal]], size: Decimal,
                  market: dict) -> dict | None:
    levels.sort(key=lambda x: x[0])
    remaining = size
    cost = Decimal("0")
    fee = Decimal("0")
    fills = []
    for price, available in levels:
        take = min(remaining, available)
        if take <= 0:
            continue
        per_share_fee = _decimal(pm_fees.fee_per_share(market, float(price)))
        if per_share_fee is None or per_share_fee < 0:
            return None
        cost += take * price
        fee += take * per_share_fee
        fills.append({"price": float(price), "size": float(take),
                      "fee": float(take * per_share_fee)})
        remaining -= take
        if remaining <= 0:
            break
    if remaining > 0:
        return None
    return {"shares": float(size), "cost": float(cost), "fee": float(fee),
            "average_price": float(cost / size), "fills": fills}


def _walk_kalshi_ask(payload: dict, side: str, size: Decimal,
                     fee_multiplier: Decimal) -> dict | None:
    book = payload.get("orderbook_fp")
    if not isinstance(book, dict):
        return None
    # Kalshi publishes bids only. Buying YES consumes NO bids at 1-no_bid;
    # buying NO consumes YES bids at 1-yes_bid.
    opposing = "no_dollars" if side == "yes" else "yes_dollars"
    levels = []
    for raw in book.get(opposing) or []:
        if not isinstance(raw, (list, tuple)) or len(raw) != 2:
            return None
        bid, qty = _decimal(raw[0]), _decimal(raw[1])
        if bid is None or qty is None or not (Decimal("0") < bid < Decimal("1")) or qty <= 0:
            return None
        levels.append((Decimal("1") - bid, qty))
    levels.sort(key=lambda x: x[0])
    remaining = size
    cost = Decimal("0")
    fee = Decimal("0")
    fills = []
    for price, available in levels:
        take = min(remaining, available)
        if take <= 0:
            continue
        raw_fee = Decimal("0.07") * fee_multiplier * take * price * (Decimal("1") - price)
        rounded_fee = raw_fee.quantize(Decimal("0.01"), rounding=ROUND_CEILING)
        cost += take * price
        fee += rounded_fee
        fills.append({"price": float(price), "size": float(take), "fee": float(rounded_fee)})
        remaining -= take
        if remaining <= 0:
            break
    if remaining > 0:
        return None
    # Kalshi debits cent-aligned balances.  Per-level fee ceiling is already
    # conservative; ceil the aggregate debit once more so sub-cent fixed-point
    # prices can never make the reported spread look better than fundable cash.
    debit = (cost + fee).quantize(Decimal("0.01"), rounding=ROUND_CEILING)
    return {"contracts": float(size), "cost": float(cost), "fee": float(fee),
            "debit": float(debit),
            "average_price": float(cost / size), "fills": fills}


def _valid_kalshi_book(payload: dict) -> bool:
    book = payload.get("orderbook_fp") if isinstance(payload, dict) else None
    if not isinstance(book, dict):
        return False
    parsed: dict[str, list[tuple[Decimal, Decimal]]] = {}
    for side in ("yes_dollars", "no_dollars"):
        if side not in book:
            return False
        raw_levels = book[side]
        # Kalshi serializes a present-but-empty bid side as either [] or null.
        # Missing keys and all other shapes remain schema failures.
        if raw_levels is None:
            raw_levels = []
        elif not isinstance(raw_levels, list):
            return False
        levels = []
        for raw in raw_levels:
            if not isinstance(raw, (list, tuple)) or len(raw) != 2:
                return False
            price, qty = _decimal(raw[0]), _decimal(raw[1])
            if (price is None or qty is None or not (Decimal("0") < price < Decimal("1"))
                    or qty <= 0):
                return False
            levels.append((price, qty))
        parsed[side] = levels
    # A YES bid and NO bid whose sum reaches a dollar are mutually executable
    # complements and should have matched already. Treat such a snapshot as
    # crossed/stale rather than deriving a phantom ask from it.
    if parsed["yes_dollars"] and parsed["no_dollars"]:
        if (max(price for price, _ in parsed["yes_dollars"])
                + max(price for price, _ in parsed["no_dollars"]) >= Decimal("1")):
            return False
    return True


def _safe_fee_multiplier(series: dict) -> Decimal | None:
    if series.get("fee_type") not in {"quadratic", "quadratic_with_maker_fees"}:
        return None
    multiplier = _decimal(series.get("fee_multiplier"))
    return multiplier if multiplier is not None and multiplier >= 0 else None


class KalshiConsensusAdapter:
    """Compare one already-shortlisted full Gamma market with public books."""

    def __init__(self, client: Any | None = None, *,
                 now_fn: Callable[[], dt.datetime] | None = None,
                 **client_kwargs: Any):
        self.http = PublicJSONClient(client, **client_kwargs)
        self.now_fn = now_fn or (lambda: dt.datetime.now(dt.timezone.utc))

    def _now(self) -> dt.datetime:
        current = self.now_fn()
        if current.tzinfo is None:
            current = current.replace(tzinfo=dt.timezone.utc)
        return current.astimezone(dt.timezone.utc)

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> "KalshiConsensusAdapter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _rejected(reason: str, **evidence: object) -> dict:
        return {"status": "rejected", "reason": reason, "source": "public_unauthenticated_rest", **evidence}

    def compare(self, pm_market: dict) -> dict:
        spec, reason = _candidate_spec(pm_market, now=self._now())
        if spec is None:
            return self._rejected(reason or "invalid_candidate")
        if not _pm_fee_known(pm_market):
            return self._rejected("unknown_pm_fee_schedule")
        gamma_minimum = _decimal(pm_market.get("orderMinSize"))
        if gamma_minimum is None or gamma_minimum <= 0:
            return self._rejected("invalid_gamma_order_min_size")
        condition_id = str(pm_market.get("conditionId") or "").strip()
        if not condition_id:
            return self._rejected("missing_gamma_condition_id")

        route: LeagueRoute = spec["route"]
        evidence: dict[str, object] = {
            "source": "public_unauthenticated_rest",
            "pm_slug": pm_market.get("slug"),
            "league": route.key,
            "market_type": spec["market_type"],
            "line": float(spec["line"]) if spec["line"] is not None else None,
            "participants": list(spec["participants"]),
            "pm_scheduled_time": spec["start"].isoformat(),
            "gamma_order_min_size": float(gamma_minimum),
            "metadata_cache_policy": "bounded_process_lru; live books never cached",
        }
        try:
            payload = self.http.get(f"{KALSHI_BASE}/milestones",
                                    params=_milestone_params(spec), cacheable=True)
            milestones = payload.get("milestones")
            if not isinstance(milestones, list):
                return self._rejected("invalid_milestone_payload", **evidence)
            # This adapter never paginates a discovery universe.  Even a found
            # candidate is ambiguous if the bounded response says another page
            # exists, because a duplicate exact identity/time match could be
            # hidden there.
            if payload.get("cursor"):
                return self._rejected("bounded_milestone_page_incomplete", **evidence)
            milestone, reason = _matching_milestone(spec, milestones)
            if milestone is None:
                return self._rejected(reason or "no_milestone_match", **evidence)
            event_ticker = milestone["_matched_event_ticker"]
            evidence.update({
                "kalshi_milestone_id": milestone.get("id"),
                "kalshi_milestone_title": milestone.get("title"),
                "kalshi_milestone_status": (milestone.get("details") or {}).get("status"),
                "participant_match_method": milestone.get("_participant_match_method"),
                "kalshi_scheduled_time": milestone.get("start_date"),
                "scheduled_time_delta_seconds": abs((_parse_time(milestone.get("start_date")) - spec["start"]).total_seconds()),
                "kalshi_event_ticker": event_ticker,
            })
            event_payload = self.http.get(
                f"{KALSHI_BASE}/events/{event_ticker}",
                params={"with_nested_markets": "true"}, cacheable=True,
            )
            event_obj = event_payload.get("event")
            if not isinstance(event_obj, dict):
                return self._rejected("invalid_kalshi_event_payload", **evidence)
            if str(event_obj.get("event_ticker") or "") != event_ticker:
                return self._rejected("kalshi_event_ticker_mismatch", **evidence)
            if event_obj.get("live") or event_obj.get("is_live"):
                return self._rejected("kalshi_live_event_unsupported", **evidence)
            event_pair = _split_participants(event_obj.get("title"))
            if event_pair is None or not _same_participant_pair(
                spec["participants"], event_pair, route
            ):
                return self._rejected("kalshi_event_identity_mismatch", **evidence)
            allowed_series = {prefix.rstrip("-")
                              for prefix in route.event_prefixes[spec["market_type"]]}
            reported_series = str(event_obj.get("series_ticker") or "")
            if reported_series not in allowed_series:
                return self._rejected("kalshi_league_or_market_type_mismatch", **evidence)
            markets = event_payload.get("markets")
            if not isinstance(markets, list) or not markets:
                markets = event_obj.get("markets")
            if not isinstance(markets, list):
                return self._rejected("invalid_kalshi_event_payload", **evidence)
            selected, reason = _select_kalshi_markets(spec, markets, pm_market)
            if selected is None:
                return self._rejected(reason or "no_kalshi_market", **evidence)

            selected_markets = ([selected["market"]] if selected["mode"] == "binary"
                                else list(selected["markets"].values()))
            for market in selected_markets:
                ticker = str(market.get("ticker") or "")
                if (str(market.get("event_ticker") or "") != event_ticker
                        or not ticker.startswith(event_ticker + "-")):
                    return self._rejected("kalshi_child_market_lineage_mismatch", **evidence)
            rule_evidence = []
            for market in selected_markets:
                compatible, rules = compatible_rules(pm_market, market)
                rule_evidence.append({"ticker": market.get("ticker"), **rules})
                if not compatible:
                    return self._rejected(rules["reason"], rules=rule_evidence, **evidence)
                scoped, scope = _ordinary_contract_scope(pm_market, market, spec)
                rule_evidence[-1]["ordinary_scope"] = scope
                if not scoped:
                    return self._rejected(scope["reason"], rules=rule_evidence, **evidence)
            evidence["rules"] = rule_evidence

            series_ticker = reported_series
            series_payload = self.http.get(f"{KALSHI_BASE}/series/{series_ticker}", cacheable=True)
            series_obj = series_payload.get("series")
            if (not isinstance(series_obj, dict)
                    or str(series_obj.get("ticker") or "") != series_ticker):
                return self._rejected("kalshi_series_response_ticker_mismatch", **evidence)
            fee_multiplier = _safe_fee_multiplier(series_obj)
            if fee_multiplier is None:
                return self._rejected("unknown_kalshi_fee_schedule", **evidence)
            evidence["kalshi_series_ticker"] = series_ticker
            evidence["kalshi_fee_multiplier"] = float(fee_multiplier)

            outcomes, tokens, reason = _validated_pm_tokens(pm_market)
            if outcomes is None or tokens is None:
                return self._rejected(reason or "invalid_pm_tokens", **evidence)

            snapshot_started = self._now()
            pm_books: dict[str, dict] = {}
            pm_minimums: list[Decimal] = []
            pm_timestamp_evidence = []
            for outcome, token in zip(outcomes, tokens):
                raw_book = self.http.get(
                    f"{PM_CLOB_BASE}/book", params={"token_id": token}, cacheable=False
                )
                acquired = self._now()
                book, book_reason = _validated_pm_book(
                    raw_book, token=token, condition_id=condition_id, now=acquired
                )
                if book is None:
                    return self._rejected(book_reason or "invalid_pm_book", **evidence)
                pm_books[outcome] = book
                pm_minimums.append(book["min_order_size"])
                pm_timestamp_evidence.append({
                    "outcome": outcome,
                    "token_id": token,
                    "book_timestamp": book["timestamp"].isoformat(),
                    "age_at_fetch_seconds": book["age_seconds"],
                    "fetched_at": acquired.isoformat(),
                })

            comparison_size = max([gamma_minimum, KALSHI_MIN_ORDER_SIZE, *pm_minimums])
            comparison_size = comparison_size.to_integral_value(rounding=ROUND_CEILING)
            if comparison_size <= 0 or comparison_size > MAX_COMPARE_SIZE:
                return self._rejected("unsupported_comparison_order_size", **evidence)
            evidence.update({
                "comparison_size": float(comparison_size),
                "pm_book_min_order_sizes": [float(value) for value in pm_minimums],
                "kalshi_min_order_size": float(KALSHI_MIN_ORDER_SIZE),
                "comparison_size_policy": "ceil(max(gamma_orderMinSize, live_pm_book_minimums, kalshi_1_contract))",
                "pm_book_timestamps": pm_timestamp_evidence,
            })

            pm_walks = {}
            for outcome, token in zip(outcomes, tokens):
                walk = _walk_pm_asks(pm_books[outcome]["asks"], comparison_size, pm_market)
                pm_walks[outcome] = ({"token_id": token, **walk} if walk is not None else None)

            book_cache: dict[str, dict] = {}
            for market in selected_markets:
                ticker = str(market.get("ticker") or "")
                if not ticker:
                    return self._rejected("missing_kalshi_market_ticker", **evidence)
                # Quotes are intentionally never memoized.
                live_book = self.http.get(
                    f"{KALSHI_BASE}/markets/{ticker}/orderbook",
                    params={"depth": 100}, cacheable=False,
                )
                if not _valid_kalshi_book(live_book):
                    return self._rejected("invalid_or_crossed_kalshi_book", **evidence)
                book_cache[ticker] = live_book
            snapshot_finished = self._now()
            evidence.update({
                "snapshot_atomic": False,
                "snapshot_started_at": snapshot_started.isoformat(),
                "snapshot_finished_at": snapshot_finished.isoformat(),
                "snapshot_fetch_span_ms": max(
                    0.0, (snapshot_finished - snapshot_started).total_seconds() * 1000.0
                ),
                "snapshot_caveat": (
                    "Sequential public REST snapshots; fee-only spread is not a simultaneous "
                    "or guaranteed executable quote."
                ),
                "kalshi_fee_rounding_policy": (
                    "ceil each walked fill fee and aggregate cash debit to whole cents"
                ),
            })

            directions = []
            direction_priceability = []
            for outcome in outcomes:
                if selected["mode"] == "categorical":
                    kalshi_market = selected["markets"][outcome]
                    same_outcome_side = "yes"
                else:
                    kalshi_market = selected["market"]
                    yes_means = _norm(selected["yes_means"])
                    outcome_norm = _norm(outcome)
                    expected = {yes_means, "under" if yes_means == "over" else "no"}
                    if {_norm(x) for x in outcomes} != expected:
                        return self._rejected("pm_binary_outcome_semantics_mismatch", **evidence)
                    # This intentionally keys on the named outcome, not
                    # token/Gamma array position.
                    same_outcome_side = "yes" if outcome_norm == yes_means else "no"
                kalshi_side = "no" if same_outcome_side == "yes" else "yes"
                ticker = str(kalshi_market.get("ticker"))
                kalshi_walk = _walk_kalshi_ask(book_cache[ticker], kalshi_side,
                                               comparison_size, fee_multiplier)
                same_outcome_walk = _walk_kalshi_ask(
                    book_cache[ticker], same_outcome_side, comparison_size, fee_multiplier
                )
                pm_walk = pm_walks[outcome]
                priceability = {
                    "pm_outcome": outcome,
                    "kalshi_market_ticker": ticker,
                    "pm_ask_depth": "priceable" if pm_walk is not None else "insufficient",
                    "kalshi_hedge_side": kalshi_side.upper(),
                    "kalshi_hedge_depth": (
                        "priceable" if kalshi_walk is not None else "insufficient"
                    ),
                    "kalshi_same_outcome_side": same_outcome_side.upper(),
                    "kalshi_same_outcome_depth": (
                        "priceable" if same_outcome_walk is not None else "insufficient"
                    ),
                    "emitted": pm_walk is not None and kalshi_walk is not None,
                }
                direction_priceability.append(priceability)
                # The same-outcome side is comparison evidence, not a hedge
                # leg. Missing depth there cannot suppress a fully priceable
                # PM + opposite-Kalshi complement. Likewise, one unpriceable
                # PM outcome cannot suppress the other outcome's direction.
                if pm_walk is None or kalshi_walk is None:
                    continue
                total_cost = Decimal(str(pm_walk["cost"])) + Decimal(str(pm_walk["fee"]))
                total_cost += Decimal(str(kalshi_walk["debit"]))
                net_profit = comparison_size - total_cost
                pm_all_in = (
                    Decimal(str(pm_walk["cost"])) + Decimal(str(pm_walk["fee"]))
                ) / comparison_size
                kalshi_same_all_in = (
                    Decimal(str(same_outcome_walk["debit"])) / comparison_size
                    if same_outcome_walk is not None else None
                )
                directions.append({
                    "pm_outcome": outcome,
                    "kalshi_market_ticker": ticker,
                    "kalshi_same_outcome_side": same_outcome_side.upper(),
                    "kalshi_side": kalshi_side.upper(),
                    "pm_live_book": pm_walk,
                    "kalshi_same_outcome_live_book": same_outcome_walk,
                    "kalshi_same_outcome_priceability": (
                        "priceable" if same_outcome_walk is not None else "insufficient"
                    ),
                    "kalshi_live_book": kalshi_walk,
                    "pm_vs_kalshi_ask_pp": ((
                        pm_walk["average_price"] - same_outcome_walk["average_price"]
                    ) * 100.0 if same_outcome_walk is not None else None),
                    "pm_vs_kalshi_all_in_pp": (
                        float((pm_all_in - kalshi_same_all_in) * Decimal("100"))
                        if kalshi_same_all_in is not None else None
                    ),
                    "combined_cost": float(total_cost),
                    "net_profit_dollars": float(net_profit),
                    "fee_only_snapshot_spread_pp": float(
                        net_profit / comparison_size * Decimal("100")
                    ),
                })

            if not directions:
                return self._rejected(
                    "no_fully_priceable_pm_kalshi_hedge_direction",
                    direction_priceability=direction_priceability,
                    **evidence,
                )
            best = max(directions, key=lambda row: row["fee_only_snapshot_spread_pp"])
            return {
                "status": "matched",
                "reason": "strict_rules_identity_scope_and_live_book_match",
                **evidence,
                "price_source": "live_pm_clob_and_live_kalshi_orderbook",
                "gamma_outcome_prices_ignored": pm_market.get("outcomePrices"),
                "direction_priceability": direction_priceability,
                "directions": directions,
                "best_fee_only_snapshot_spread_pp": best["fee_only_snapshot_spread_pp"],
                "best_direction": {
                    "pm_outcome": best["pm_outcome"],
                    "kalshi_market_ticker": best["kalshi_market_ticker"],
                    "kalshi_side": best["kalshi_side"],
                },
                "execution": "disabled_read_only",
            }
        except PublicDataError as exc:
            return {"status": "error", "reason": exc.code, "detail": exc.detail, **evidence}
