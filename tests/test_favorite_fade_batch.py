from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import favorite_fade_scan as scanner  # noqa: E402


def test_validated_book_rejects_missing_or_crossed():
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    assert scanner._validated_book(None, "a", "condition") is None
    assert scanner._validated_book({"asset_id": "a", "market": "condition", "timestamp": now,
                                    "asks": [{"price": ".4", "size": "1"}],
                                    "bids": [{"price": ".5", "size": "1"}]},
                                   "a", "condition") is None


def test_validated_book_returns_sorted_quote_data():
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    book = scanner._validated_book({"asset_id": "a", "market": "condition", "timestamp": now,
                                    "asks": [{"price": ".5", "size": "2"},
                                              {"price": ".4", "size": "1"}],
                                    "bids": [{"price": ".3", "size": "2"}]},
                                   "a", "condition")
    assert book["asks"] == [(0.5, 2.0), (0.4, 1.0)]


def test_validated_book_rejects_wrong_condition_and_nonfinite_size():
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    base = {"asset_id": "a", "market": "other", "timestamp": now,
            "asks": [{"price": ".4", "size": "1"}], "bids": []}
    assert scanner._validated_book(base, "a", "condition") is None
    base["market"] = "condition"
    base["asks"][0]["size"] = "NaN"
    assert scanner._validated_book(base, "a", "condition") is None


def test_main_batches_candidate_books_once(monkeypatch, capsys):
    end = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    market = {
        "outcomes": '["Yes", "No"]', "outcomePrices": '[0.95, 0.05]',
        "endDate": end, "liquidity": 50_000, "volume24hr": 10_000,
        "clobTokenIds": '["yes-token", "no-token"]',
        "conditionId": "condition", "question": "Will the president remain?",
        "umaResolutionStatus": "",
    }
    requested = []

    monkeypatch.setattr(scanner, "fetch_active", lambda *_args, **_kwargs: [market])
    monkeypatch.setattr(
        scanner, "fetch_books",
        lambda tokens, **_kwargs: requested.append(list(tokens)) or {
            "yes-token": {
                "asset_id": "yes-token", "market": "condition",
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                "asks": [{"price": ".95", "size": "100"}],
                "bids": [{"price": ".94", "size": "100"}],
            }
        },
    )
    monkeypatch.setattr(sys, "argv", ["favorite_fade_scan.py"])

    assert scanner.main() == 0
    assert requested == [["yes-token"]]
    assert "Will the president remain?" in capsys.readouterr().out
