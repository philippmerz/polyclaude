"""Durable regression tests for immutable primary-evaluation revisions."""

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
def review_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path
    run = root / "research" / "fixture-review"
    rules = root / "frozen.jsonl.gz"
    pointer = root / "notes" / "checkpoint.json"
    run.mkdir(parents=True)
    with gzip.open(rules, "wt", encoding="utf-8") as stream:
        for index in (1, 2, 3):
            stream.write(json.dumps(_frozen(index)) + "\n")
    monkeypatch.setattr(ledger, "ROOT", root)
    monkeypatch.setattr(ledger, "RUN", run)
    monkeypatch.setattr(ledger, "RULES", rules)
    monkeypatch.setattr(ledger, "POINTER", pointer)
    return run


def _record_input(index: int, status: str, report: str, *, revision: bool = False) -> dict:
    frozen = _frozen(index)
    record = {
        "review_index": index,
        "condition_id": frozen["conditionId"],
        "criteria_sha256": frozen["criteria_sha256"],
        "status": status,
        "literal_analysis": "Exact event and settlement condition reviewed.",
        "evidence": [{"url": "https://example.test/source", "observed_utc": "2026-10-18T00:00:00Z", "finding": "Test fact."}],
        "forecast": {},
        "economics": {"both_sides_considered": True},
        "verdict": "Blocked pending a source fact." if status == "blocked_after_review" else "Valued from the reviewed evidence.",
        "reopen_condition": "Reopen if the cited source changes.",
        "report_markdown": report,
    }
    if status == "valued":
        record["forecast"] = {"p_yes": 0.6, "low": 0.4, "high": 0.8, "reasoning": "Fixture judgment.", "method": "Fixture method."}
    else:
        record["forecast"] = {"reasoning": "Not valued before the blocker is resolved."}
    if revision:
        record["market_id"] = frozen["id"]
    return record


def _write_input(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _save_base(run: Path, tmp_path: Path) -> tuple[Path, dict]:
    # Mirrors case_tools.save(): the base input intentionally omits market_id.
    source = _write_input(tmp_path / "base.json", _record_input(1, "blocked_after_review", "Original blocked report."))
    ledger.record(source)
    base = run / "evaluations" / "0001.json"
    return base, json.loads(base.read_text())


def _revision_input(tmp_path: Path, *, status: str = "valued", report: str = "Updated report.") -> Path:
    return _write_input(tmp_path / "revision-input.json", _record_input(1, status, report, revision=True))


def _revision_files(run: Path) -> list[Path]:
    return sorted((run / "revisions").glob("*")) if (run / "revisions").exists() else []


def test_blocked_to_valued_revision_updates_effective_index_once_and_preserves_base(review_run: Path, tmp_path: Path):
    base_path, base_record = _save_base(review_run, tmp_path)
    original_base = base_path.read_bytes()
    result = ledger.revise(_revision_input(tmp_path), base_record["report_sha256"], "New evidence resolves the blocker.")

    assert result["completed_valuations"] == 1
    assert result["blocked_after_in_depth_review"] == 0
    assert result["base_records"] == 1
    assert result["revisions_written"] == 1
    assert base_path.read_bytes() == original_base
    with (review_run / "index.csv").open(newline="", encoding="utf-8") as stream:
        rows = [row for row in csv.DictReader(stream) if row["index"] == "1"]
    assert len(rows) == 1
    row = rows[0]
    revision = json.loads((review_run / "revisions.jsonl").read_text().splitlines()[0])
    assert row["status"] == "valued"
    assert row["report"] == revision["revision_path"].replace(".json", ".md")
    assert revision["revision_path"].replace(".json", ".md") in (review_run / "INDEX.md").read_text()


def test_successive_revisions_chain_and_stale_predecessor_fails_before_write(review_run: Path, tmp_path: Path):
    base_path, base_record = _save_base(review_run, tmp_path)
    original_base = base_path.read_bytes()
    first_result = ledger.revise(_revision_input(tmp_path, report="First revision."), base_record["report_sha256"], "First correction.")
    first = json.loads((review_run / "revisions.jsonl").read_text().splitlines()[0])
    second_input = _revision_input(tmp_path, report="Second revision.")
    ledger.revise(second_input, first["report_sha256"], "Follow-up correction.")
    rows = [json.loads(line) for line in (review_run / "revisions.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["prior_report_sha256"] == base_record["report_sha256"]
    assert rows[1]["prior_report_sha256"] == rows[0]["report_sha256"]
    assert base_path.read_bytes() == original_base
    before = (review_run / "revisions.jsonl").read_bytes()
    files_before = [p.relative_to(review_run).as_posix() for p in _revision_files(review_run)]
    with pytest.raises(AssertionError, match="stale or mismatched"):
        ledger.revise(_revision_input(tmp_path, report="Must not be written."), base_record["report_sha256"], "Stale predecessor.")
    assert (review_run / "revisions.jsonl").read_bytes() == before
    assert [p.relative_to(review_run).as_posix() for p in _revision_files(review_run)] == files_before
    assert first_result["revisions_written"] == 1


@pytest.mark.parametrize("field,value", [
    ("market_id", "wrong-market"),
    ("criteria_sha256", "0" * 64),
])
def test_revision_identity_or_criteria_mismatch_fails_before_mutation(
    review_run: Path, tmp_path: Path, field: str, value: str,
):
    base_path, base_record = _save_base(review_run, tmp_path)
    base_bytes = base_path.read_bytes()
    source = _revision_input(tmp_path)
    payload = json.loads(source.read_text())
    payload[field] = value
    _write_input(source, payload)
    with pytest.raises(AssertionError, match="market id mismatch|criteria fingerprint mismatch"):
        ledger.revise(source, base_record["report_sha256"], "Invalid identity.")
    assert base_path.read_bytes() == base_bytes
    assert not (review_run / "revisions.jsonl").exists()
    assert _revision_files(review_run) == []


@pytest.mark.parametrize("tamper", ["json", "markdown"])
def test_rebuild_detects_tampered_revision_artifact(review_run: Path, tmp_path: Path, tamper: str):
    _, base_record = _save_base(review_run, tmp_path)
    ledger.revise(_revision_input(tmp_path), base_record["report_sha256"], "Resolve blocker.")
    revision = json.loads((review_run / "revisions.jsonl").read_text().splitlines()[0])
    artifact = review_run / revision["revision_path"]
    if tamper == "json":
        artifact.write_bytes(artifact.read_bytes() + b" ")
    else:
        markdown = json.loads(artifact.read_text())["report_path"]
        (review_run / markdown).write_text("Tampered report.\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="revision JSON hash mismatch|revision report hash mismatch"):
        ledger.rebuild()
