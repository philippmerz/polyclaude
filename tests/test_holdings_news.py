import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import holdings_news as hn  # noqa: E402

ALIASES = hn.load_aliases()
MARKETS = [
    {"slug": "will-the-highest-score-achieved-by-a-moonshot-kimi-model-on-humanitys-last-exam-in-2026-be-55-or-higher-x",
     "title": "Will the highest score achieved by a Moonshot Kimi model on Humanity’s Last Exam in 2026 be 55% or higher?", "kind": "held"},
    {"slug": "will-delcy-rodrguez-be-the-leader-of-venezuela-end-of-2026", "title": "Will Delcy Rodríguez be the leader of Venezuela end of 2026?", "kind": "held"},
    {"slug": "will-lionel-messi-rank-in-googles-top-5-most-searched-athletes-of-2026", "title": "Will Lionel Messi rank?", "kind": "held"},
    {"slug": "will-over-50-senators-vote-for-the-clarity-act-1", "title": "Will over 50 Senators vote for the Clarity Act?", "kind": "held"},
    {"slug": "trump-out-as-president-before-2027", "title": "Trump out as President before 2027?", "kind": "order"},
]
SETS = hn.build_keyword_sets(MARKETS, ALIASES)


def slugs(text):
    return [s for s, _ in hn.match(text, SETS)]


def test_kimi_matches_and_excludes_antonelli():
    assert slugs("Moonshot releases Kimi K3")[0].startswith("will-the-highest-score")
    assert slugs("New SOTA on HUMANITY'S LAST EXAM")
    assert slugs("Kimi Antonelli wins Brazilian Grand Prix") == []
    assert slugs("Kimi wins") == []


def test_accent_and_case_insensitive():
    assert slugs("delcy rodriguez sworn in") == ["will-delcy-rodrguez-be-the-leader-of-venezuela-end-of-2026"]
    assert slugs("Delcy Rodríguez speaks")


def test_word_boundaries():
    assert slugs("Messianic movement grows") == []
    assert slugs("Messi scores twice")
    assert slugs("Senate passes CLARITY Act") == ["will-over-50-senators-vote-for-the-clarity-act-1"]
    assert slugs("Trump impeachment of Trump hearings") == ["trump-out-as-president-before-2027"]
    assert slugs("Trump deadline extended") == []


def test_title_derivation_for_unaliased_market():
    s = hn.build_keyword_sets([{"slug": "x", "title": "Will Taylor Swift win Album of the Year?"}], [])
    assert "Taylor Swift" in s["x"]["keywords"]


def test_refresh_and_fail_safe(tmp_path):
    clock = [1000.0]
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        if calls["n"] > 1:
            raise RuntimeError("data api down")
        return MARKETS[2:3]

    cache = tmp_path / "kw.json"
    hk = hn.HoldingsKeywords(fetch=fetch, cache_path=cache, refresh_s=1800, clock=lambda: clock[0])
    first = hk.get()
    assert list(first) == [MARKETS[2]["slug"]]
    clock[0] += 60
    hk.get()
    assert calls["n"] == 1  # not yet due
    clock[0] += 1800
    assert hk.get() == first  # failure keeps last set
    assert calls["n"] == 2
    # a fresh process with failing fetch uses the on-disk cache
    hk2 = hn.HoldingsKeywords(fetch=lambda: (_ for _ in ()).throw(RuntimeError("x")),
                              cache_path=cache, clock=lambda: clock[0])
    assert list(hk2.get()) == [MARKETS[2]["slug"]]
    assert json.loads(cache.read_text())["sets"]


def test_watcher_hook_sends_one_wake(monkeypatch):
    import news_watcher as nw
    sent = []
    monkeypatch.setattr(nw, "_HOLDINGS", type("H", (), {"get": lambda self: SETS})())
    monkeypatch.setattr(nw.holdings_news, "send_wake",
                        lambda slug, h, kw, link="": sent.append((slug, h)) or "wake x: pending")
    assert nw._holdings_wake_check("Lionel Messi tops searches", "Lionel Messi tops searches")
    assert sent == [("will-lionel-messi-rank-in-googles-top-5-most-searched-athletes-of-2026",
                     "Lionel Messi tops searches")]
    assert nw._holdings_wake_check("Weather today", "Weather today") == []
    assert len(sent) == 1


def test_send_wake_goes_through_outbox(tmp_path, monkeypatch):
    monkeypatch.delenv("POLYCLAUDE_WAKE_URL", raising=False)
    monkeypatch.delenv("POLYCLAUDE_WAKE_KEY", raising=False)
    out = hn.send_wake("messi-mkt", "Messi headline", "Messi", repo=tmp_path)
    out2 = hn.send_wake("messi-mkt", "Messi other headline", "Messi", repo=tmp_path)
    rows = [json.loads(l) for l in (tmp_path / "logs" / "wake_outbox.jsonl").read_text().splitlines()]
    assert rows[0]["market_slug"] == "messi-mkt" and rows[0]["source"] == "news_watcher"
    assert "Messi headline" in rows[0]["headline"]
    assert rows[-1]["status"] == "rate_limited_market", (out, out2)
