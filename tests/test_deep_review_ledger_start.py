"""Single-active-case guards for the finite deep-review ledger."""

from __future__ import annotations

import gzip
import hashlib
import json
import csv
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deep_review_ledger as ledger  # noqa: E402


def _frozen(index: int) -> dict:
    return {
        "review_index": index,
        "id": f"market-{index}",
        "conditionId": f"0x{index:064x}",
        "criteria_sha256": hashlib.sha256(f"criteria-{index}".encode()).hexdigest(),
        "question": f"Will event {index} happen?",
    }


@pytest.fixture
def review_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    run = tmp_path / "research" / "fixture-review"
    run.mkdir(parents=True)
    rules = tmp_path / "frozen.jsonl.gz"
    with gzip.open(rules, "wt", encoding="utf-8") as stream:
        for index in (1, 2, 3):
            stream.write(json.dumps(_frozen(index)) + "\n")
    monkeypatch.setattr(ledger, "ROOT", tmp_path)
    monkeypatch.setattr(ledger, "RUN", run)
    monkeypatch.setattr(ledger, "RULES", rules)
    monkeypatch.setattr(ledger, "POINTER", tmp_path / "notes" / "checkpoint.json")
    (run / "evaluations").mkdir()
    return run


def _record_input(tmp_path: Path, index: int = 1, *, report_markdown: bool = True) -> Path:
    frozen = _frozen(index)
    record = {
        "review_index": index,
        "condition_id": frozen["conditionId"],
        "criteria_sha256": frozen["criteria_sha256"],
        "status": "blocked_after_review",
        "literal_analysis": "The exact fixture condition was read.",
        "evidence": [{
            "url": "https://example.test/source",
            "observed_utc": "2026-10-20T00:00:00Z",
            "finding": "Fixture evidence.",
        }],
        "forecast": {"reasoning": "Not valued while the blocker remains."},
        "economics": {"both_sides_considered": True},
        "verdict": "Blocked pending the required source.",
        "reopen_condition": "Reopen after that source is captured.",
    }
    if report_markdown:
        record["report_markdown"] = "Fixture blocked report."
    path = tmp_path / f"record-{index}.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def _ledger_snapshot(run: Path) -> dict[str, bytes | None]:
    paths = [
        run / "progress.json",
        run / "index.csv",
        run / "INDEX.md",
        ledger.POINTER,
        run / "evaluations.jsonl",
    ]
    return {str(path): path.read_bytes() if path.exists() else None for path in paths}


def test_failed_record_keeps_other_case_from_starting_without_any_ledger_change(
    review_run: Path, tmp_path: Path,
):
    ledger.start(1)
    before = _ledger_snapshot(review_run)

    with pytest.raises(AssertionError, match="report_markdown required"):
        ledger.record(_record_input(tmp_path, report_markdown=False))
    after_failed_record = _ledger_snapshot(review_run)
    assert after_failed_record == before

    with pytest.raises(ValueError, match=r"unfinished active case\(s\): 1"):
        ledger.start(2)

    assert _ledger_snapshot(review_run) == after_failed_record
    assert not (review_run / "evaluations" / "0001.json").exists()
    assert not (review_run / "evaluations" / "0002.json").exists()


def test_same_active_case_can_be_resumed_idempotently(review_run: Path):
    first = ledger.start(1)
    progress_before = json.loads((review_run / "progress.json").read_text())
    assert first["active_indices"] == [1]

    resumed = ledger.start(1)

    assert resumed["active_indices"] == [1]
    assert json.loads((review_run / "progress.json").read_text())["active_indices"] == [1]
    assert progress_before["active_indices"] == [1]
    assert not (review_run / "evaluations.jsonl").exists()


def test_record_then_start_next_case_preserves_completed_record(review_run: Path, tmp_path: Path):
    ledger.start(1)
    ledger.record(_record_input(tmp_path))
    base_json = (review_run / "evaluations" / "0001.json").read_bytes()
    base_md = (review_run / "evaluations" / "0001.md").read_bytes()
    ledger_bytes = (review_run / "evaluations.jsonl").read_bytes()
    assert json.loads((review_run / "progress.json").read_text())["active_indices"] == []

    result = ledger.start(2)

    assert result["active_indices"] == [2]
    with (review_run / "index.csv").open(newline="", encoding="utf-8") as stream:
        rows = {row["index"]: row for row in csv.DictReader(stream)}
    assert rows["1"]["status"] == "blocked_after_review"
    assert rows["2"]["status"] == "in_progress"
    assert (review_run / "evaluations" / "0001.json").read_bytes() == base_json
    assert (review_run / "evaluations" / "0001.md").read_bytes() == base_md
    assert (review_run / "evaluations.jsonl").read_bytes() == ledger_bytes


def test_start_rejects_unknown_and_completed_indices(review_run: Path, tmp_path: Path):
    with pytest.raises(ValueError, match="unknown review index"):
        ledger.start(99)

    ledger.record(_record_input(tmp_path))
    snapshot = _ledger_snapshot(review_run)
    with pytest.raises(ValueError, match="already has a completed record"):
        ledger.start(1)
    assert _ledger_snapshot(review_run) == snapshot
