from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import cross_event_bound_scan as scanner  # noqa: E402


def _book(token="a", ask=".4", bid=".3", condition="condition"):
    return {"asset_id": token, "market": condition,
            "timestamp": int(time.time() * 1000),
            "asks": [{"price": ask, "size": "2"}],
            "bids": [{"price": bid, "size": "2"}]}


def test_book_validation_fails_closed_for_missing_stale_and_crossed():
    assert scanner._validated_book(None, "a", "condition") is None
    stale = _book(); stale["timestamp"] = 1
    assert scanner._validated_book(stale, "a", "condition") is None
    crossed = _book(bid=".5")
    assert scanner._validated_book(crossed, "a", "condition") is None


def test_ask_and_bid_use_asset_id_mapping():
    row = {"tokens": ["yes", "no"], "outcomes": ["Yes", "No"],
           "condition_id": "condition"}
    books = {"yes": _book("yes", ".42", ".4"), "no": _book("no", ".58", ".56")}
    assert scanner._ask(row, "Yes", books) == (0.42, 2.0)
    assert scanner._bid(row, "No", books) == 0.56
    assert scanner._ask(row, "Yes", {}) == (None, 0.0)


def test_book_validation_rejects_wrong_condition_and_nonfinite_size():
    wrong = _book(condition="other")
    assert scanner._validated_book(wrong, "a", "condition") is None
    malformed = _book(); malformed["asks"][0]["size"] = "NaN"
    assert scanner._validated_book(malformed, "a", "condition") is None


def test_umbrella_main_batches_relevant_books_once(monkeypatch, capsys):
    umbrella = {
        50.0: {"yes_mid": .60, "vol24": 1000,
               "tokens": ["u-yes", "u-no"], "outcomes": ["Yes", "No"],
               "condition_id": "u-condition", "slug": "u"},
    }
    subset = {
        50.0: {"yes_mid": .80, "vol24": 1000,
               "tokens": ["s-yes", "s-no"], "outcomes": ["Yes", "No"],
               "condition_id": "s-condition", "slug": "s"},
    }
    monkeypatch.setattr(scanner, "_rungs", lambda slug: umbrella if slug == "u" else subset)
    requested = []

    def fetch(tokens, **_kwargs):
        requested.append(list(tokens))
        return {
            "u-yes": _book("u-yes", ".61", ".60", "u-condition"),
            "u-no": _book("u-no", ".40", ".39", "u-condition"),
            "s-yes": _book("s-yes", ".81", ".80", "s-condition"),
            "s-no": _book("s-no", ".11", ".10", "s-condition"),
        }

    monkeypatch.setattr(scanner, "fetch_books", fetch)
    monkeypatch.setattr(
        sys, "argv", ["cross_event_bound_scan.py", "--umbrella", "u", "--subset", "s"],
    )

    assert scanner.main() == 0
    assert len(requested) == 1
    assert set(requested[0]) == {"u-yes", "u-no", "s-yes", "s-no"}
    assert "PROVISIONAL ARB" in capsys.readouterr().out
