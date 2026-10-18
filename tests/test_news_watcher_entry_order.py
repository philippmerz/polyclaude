from __future__ import annotations

import sys
from pathlib import Path
from time import struct_time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import news_watcher  # noqa: E402


def _entry(name: str, published=None, updated=None) -> dict:
    row = {"title": name, "id": name}
    if published is not None:
        row["published_parsed"] = published
    if updated is not None:
        row["updated_parsed"] = updated
    return row


def _date(day: int) -> struct_time:
    return struct_time((2026, 10, day, 12, 0, 0, 0, 0, 0))


def test_newest_dated_entries_are_selected_before_cap():
    entries = [_entry(f"old-{i}", _date(1 + i)) for i in range(4)]
    entries.extend(_entry(f"tail-{i}", _date(10 + i)) for i in range(3))

    assert [e["id"] for e in news_watcher._newest_entries_first(entries, 3)] == [
        "tail-2", "tail-1", "tail-0"
    ]


def test_published_precedes_updated_and_equal_times_keep_source_order():
    entries = [
        _entry("first", _date(17), _date(18)),
        _entry("same-time-later-in-feed", _date(18)),
        _entry("same-time-first", _date(18)),
        _entry("updated-fallback", updated=_date(19)),
    ]

    assert [e["id"] for e in news_watcher._newest_entries_first(entries)] == [
        "updated-fallback", "same-time-later-in-feed", "same-time-first", "first"
    ]


def test_malformed_dates_fall_back_then_undated_keep_source_order():
    entries = [
        _entry("undated-a"),
        _entry("bad-published-good-update", (2026, 99), _date(20)),
        _entry("bad-both", (2026, 99), ("not", "a", "date")),
        _entry("undated-b"),
    ]

    assert [e["id"] for e in news_watcher._newest_entries_first(entries)] == [
        "bad-published-good-update", "undated-a", "bad-both", "undated-b"
    ]
