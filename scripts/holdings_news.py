"""Held/ordered-market keyword matching for news_watcher immediate wakes.

Builds one keyword set per Polymarket market we hold (Data API v2) or have a
resting BUY on, from a curated alias map (holdings_aliases.json) plus distinctive
phrases derived from the market title.  Refreshed every REFRESH_SECONDS; if
inventory cannot be read the last good set is kept (fail safe).  Matches are
case-insensitive with word boundaries and support exclusion terms.

On a match the watcher calls ``send_wake`` which hands the event to
scripts/wake_webhook.py (its outbox applies the 1/market/30min and 12/day caps).
Read-only: never places, changes or cancels orders.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
REPO = _SCRIPT_DIR.parent
ALIASES_PATH = _SCRIPT_DIR / "holdings_aliases.json"
CACHE_PATH = REPO / "logs" / "holdings_keywords.json"
REFRESH_SECONDS = 30 * 60
RETRY_SECONDS = 5 * 60

_STOP = {"will", "the", "be", "of", "a", "an", "in", "on", "by", "to", "for", "or", "and",
         "end", "before", "after", "higher", "lower", "over", "under", "less", "more", "than",
         "yes", "no", "who", "what", "which", "how", "many", "much", "top", "most", "google",
         "googles", "google’s", "january", "february", "march", "april", "may", "june", "july",
         "august", "september", "october", "november", "december", "president", "leader",
         "score", "highest", "vote", "senators", "model", "searched", "athletes", "rank"}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").replace("’", "'")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _rx(phrase: str) -> re.Pattern:
    toks = _fold(phrase).split()
    return re.compile(r"(?<!\w)" + r"\s+".join(re.escape(t) for t in toks) + r"(?!\w)")


def load_aliases(path: Path = ALIASES_PATH) -> list[dict]:
    try:
        return list(json.loads(path.read_text()).get("aliases") or [])
    except (OSError, ValueError):
        return []


def derive_title_keywords(title: str) -> list[str]:
    """Capitalised multi-word names from a market title (e.g. 'Lionel Messi')."""
    out = []
    for m in re.finditer(r"(?:[A-Z][\w’'.-]+(?:\s+|$)){2,}", title or ""):
        words = [w for w in m.group(0).split() if _fold(w).strip("?'’") not in _STOP]
        if len(words) >= 2:
            out.append(" ".join(words).rstrip("?"))
    return out


def build_keyword_sets(markets: list[dict], aliases: list[dict]) -> dict[str, dict]:
    """markets: [{slug, event_slug, title, kind}] -> {slug: {title, kind, keywords, exclude}}."""
    result: dict[str, dict] = {}
    for mk in markets:
        slug = str(mk.get("slug") or "").lower()
        if not slug:
            continue
        hay = slug + " " + str(mk.get("event_slug") or "").lower()
        kws: list[str] = []
        exc: list[str] = []
        for a in aliases:
            if any(str(p).lower() in hay for p in a.get("match", [])):
                kws += a.get("keywords", [])
                exc += a.get("exclude", [])
        kws += derive_title_keywords(str(mk.get("title") or ""))
        entry = result.setdefault(slug, {"title": mk.get("title") or "", "kinds": [],
                                         "keywords": [], "exclude": []})
        if mk.get("kind") and mk["kind"] not in entry["kinds"]:
            entry["kinds"].append(mk["kind"])
        for k in kws:
            if k and k not in entry["keywords"]:
                entry["keywords"].append(k)
        for e in exc:
            if e and e not in entry["exclude"]:
                entry["exclude"].append(e)
    return result


def match(text: str, sets: dict[str, dict]) -> list[tuple[str, str]]:
    """Return [(market_slug, keyword)] for every market whose keywords hit and no exclusion does."""
    t = _fold(text)
    hits = []
    for slug, s in sets.items():
        if any(_rx(e).search(t) for e in s.get("exclude", [])):
            continue
        for kw in s.get("keywords", []):
            if _rx(kw).search(t):
                hits.append((slug, kw))
                break
    return hits


def fetch_markets() -> list[dict]:
    """Held (non-redeemable) positions + resting BUY orders. Raises on any read failure."""
    import _data_api
    import _paths
    addr = json.loads(_paths.path("POLYCLAUDE_WALLET").read_text())["address"]
    rows = _data_api.get_positions(params={"user": addr.lower(), "sizeThreshold": "0"},
                                   timeout=15).json()
    out = [{"slug": p.get("slug"), "event_slug": p.get("eventSlug"), "title": p.get("title"),
            "kind": "held"} for p in rows if not p.get("redeemable") and (p.get("size") or 0) > 0]
    from polyclaude_enter import _fetch_open_buy_commitments
    for r in _fetch_open_buy_commitments():
        if str(r.get("side") or "BUY").upper() == "SELL":
            continue
        if not r.get("slug"):
            raise RuntimeError("open order lacks slug")
        out.append({"slug": r.get("slug"), "event_slug": r.get("eventSlug") or "",
                    "title": r.get("question"), "kind": "order"})
    return out


class HoldingsKeywords:
    def __init__(self, fetch=fetch_markets, cache_path: Path = CACHE_PATH,
                 aliases_path: Path = ALIASES_PATH, refresh_s: int = REFRESH_SECONDS,
                 clock=time.time):
        self.fetch, self.cache_path, self.aliases_path = fetch, cache_path, aliases_path
        self.refresh_s, self.clock = refresh_s, clock
        self.sets: dict[str, dict] = {}
        self.next_refresh = 0.0
        self.last_ok = 0.0
        try:
            cached = json.loads(cache_path.read_text())
            self.sets, self.last_ok = cached.get("sets") or {}, float(cached.get("ts") or 0)
        except (OSError, ValueError):
            pass

    def get(self) -> dict[str, dict]:
        now = self.clock()
        if now >= self.next_refresh:
            try:
                self.sets = build_keyword_sets(self.fetch(), load_aliases(self.aliases_path))
                self.last_ok = now
                self.next_refresh = now + self.refresh_s
                try:
                    self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                    tmp = self.cache_path.with_suffix(".tmp")
                    tmp.write_text(json.dumps({"ts": now, "sets": self.sets}, indent=1))
                    os.replace(tmp, self.cache_path)
                except OSError:
                    pass
            except Exception as e:  # fail safe: keep last cached set
                print(f"[holdings] refresh failed, keeping {len(self.sets)} cached markets: "
                      f"{str(e)[:120]}", flush=True)
                self.next_refresh = now + min(RETRY_SECONDS, self.refresh_s)
        return self.sets


def send_wake(market_slug: str, headline: str, keyword: str, link: str = "",
              repo: Path = REPO) -> str:
    """Queue an immediate wake via wake_webhook.py queue; returns its status line."""
    prompt = (f"NEWS on held/ordered market {market_slug} (matched {keyword!r}): {headline}"
              + (f"\n{link}" if link else ""))
    env = dict(os.environ, POLYCLAUDE_WAKE_SOURCE="news_watcher",
               POLYCLAUDE_WAKE_MARKET=market_slug, POLYCLAUDE_WAKE_SEVERITY="high")
    env.pop("POLYCLAUDE_PROMPT_SOURCE", None)
    try:
        r = subprocess.run([sys.executable, str(_SCRIPT_DIR / "wake_webhook.py"), "queue",
                            "--workdir", str(repo)], input=prompt, text=True,
                           capture_output=True, timeout=60, env=env)
        return (r.stdout or r.stderr).strip()
    except Exception as e:
        return f"wake error: {e}"


if __name__ == "__main__":
    print(json.dumps(HoldingsKeywords().get(), indent=1, ensure_ascii=False))
