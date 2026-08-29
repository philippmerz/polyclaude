"""Decision-ledger identity regressions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import decisions  # noqa: E402


def _args() -> argparse.Namespace:
    return argparse.Namespace(
        type="scaffolding",
        thesis="test",
        confidence="high",
        prediction="test passes",
        size=0.0,
        resolution_at="2026-08-30",
        tags=["test"],
        slug=None,
    )


def test_add_derives_id_from_ledger_when_next_id_is_stale(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "decisions.json"
    path.write_text(json.dumps({
        "next_id": 5,
        "decisions": [{"id": 5, "type": "scaffolding"}],
    }))
    monkeypatch.setattr(decisions, "DECISIONS_PATH", path)

    assert decisions.cmd_add(_args()) == 0

    saved = json.loads(path.read_text())
    assert [row["id"] for row in saved["decisions"]] == [5, 6]
    assert saved["next_id"] == 7


def test_add_refuses_a_store_with_duplicate_ids(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "decisions.json"
    original = {
        "next_id": 6,
        "decisions": [
            {"id": 5, "type": "scaffolding"},
            {"id": 5, "type": "skip"},
        ],
    }
    path.write_text(json.dumps(original))
    monkeypatch.setattr(decisions, "DECISIONS_PATH", path)

    assert decisions.cmd_add(_args()) == 2
    assert json.loads(path.read_text()) == original


def test_add_refuses_non_object_or_boolean_identity(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "decisions.json"
    monkeypatch.setattr(decisions, "DECISIONS_PATH", path)

    for original in (
        {"next_id": 2, "decisions": ["not-an-object"]},
        {"next_id": 2, "decisions": [{"id": True}]},
        {"next_id": True, "decisions": [{"id": 1}]},
    ):
        path.write_text(json.dumps(original))
        assert decisions.cmd_add(_args()) == 2
        assert json.loads(path.read_text()) == original
