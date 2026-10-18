from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deep_review_resume as resume  # noqa: E402


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def layout(tmp_path, monkeypatch):
    root = tmp_path
    run = root / "research/2026-10-17-deep-review"
    data = root / "data/deep_review_20261017"
    rules = root / "research/2026-10-17-primary-market-review-rules.jsonl.gz"
    checkpoint = root / "notes/deep_review_checkpoint.json"
    rows = [
        {"review_index": 1, "id": "101", "conditionId": "0x" + "1" * 64,
         "question": "Will exact case one happen?", "slug": "exact-one",
         "description": "Full literal rule one.\nSecond paragraph.",
         "resolutionSource": "https://public.example/rule", "outcomes": '["Yes", "No"]',
         "clobTokenIds": '["yes-token-1", "no-token-1"]', "endDate": "2026-12-31",
         "criteria_sha256": "a" * 64},
        {"review_index": 2, "id": "202", "conditionId": "0x" + "2" * 64,
         "question": "Will exact case two happen?", "slug": "exact-two",
         "description": "Full literal rule two.", "resolutionSource": "source",
         "outcomes": '["Yes", "No"]', "clobTokenIds": '["yes-token-2", "no-token-2"]',
         "endDate": "2026-12-31", "criteria_sha256": "b" * 64},
    ]
    rules.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(rules, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    run.mkdir(parents=True)
    (run / "evaluations.jsonl").write_text("", encoding="utf-8")
    (run / "revisions.jsonl").write_text("", encoding="utf-8")
    (run / "index.csv").write_text("index\n", encoding="utf-8")
    _write_json(run / "progress.json", {
        "updated_utc": "2026-10-18T12:00:00Z", "universe": 2,
        "completed_in_depth_reviews": 0, "completed_valuations": 0,
        "blocked_after_in_depth_review": 0, "factual_exclusions": 0,
        "pending": 1, "base_records": 0, "revisions_written": 0,
        "active_indices": [2], "next_pending_indices": [1],
    })
    progress = json.loads((run / "progress.json").read_text())
    checkpoint_data = dict(progress)
    checkpoint_data.update({
        "original_rules_sha256": hashlib.sha256(rules.read_bytes()).hexdigest(),
        "ledger_sha256": hashlib.sha256((run / "evaluations.jsonl").read_bytes()).hexdigest(),
        "revisions_sha256": hashlib.sha256((run / "revisions.jsonl").read_bytes()).hexdigest(),
    })
    _write_json(checkpoint, checkpoint_data)
    monkeypatch.setattr(resume, "ROOT", root)
    monkeypatch.setattr(resume, "RUN", run)
    monkeypatch.setattr(resume, "DATA", data)
    monkeypatch.setattr(resume, "RULES", rules)
    monkeypatch.setattr(resume, "PROGRESS", run / "progress.json")
    monkeypatch.setattr(resume, "CHECKPOINT", checkpoint)
    return {"root": root, "run": run, "data": data, "rules": rules, "rows": rows}


def test_default_selects_active_and_returns_exact_full_identity_without_mutation(layout):
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (
        layout["rules"], layout["run"] / "progress.json", layout["run"] / "evaluations.jsonl",
        layout["run"] / "revisions.jsonl", layout["run"] / "index.csv")}
    packet = resume.build_packet()
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before}
    assert before == after
    assert packet["selected_review_index"] == 2
    assert packet["effective_case"]["status"] == "in_progress"
    assert packet["case"]["conditionId"] == layout["rows"][1]["conditionId"]
    assert packet["case"]["description"] == layout["rows"][1]["description"]
    assert packet["case"]["outcomes"] == ["Yes", "No"]
    assert packet["case"]["clobTokenIds"] == ["yes-token-2", "no-token-2"]
    assert packet["packet_bytes"] <= 8000


def test_explicit_case_uses_newest_verified_revision_pointer(layout):
    i = 1
    base_report = "base report\n"
    base_sha = hashlib.sha256(base_report.encode()).hexdigest()
    (layout["run"] / "evaluations").mkdir()
    (layout["run"] / "evaluations/0001.md").write_text(base_report)
    base = {"review_index": i, "market_id": "101", "condition_id": layout["rows"][0]["conditionId"],
            "criteria_sha256": "a" * 64, "status": "valued", "evaluated_utc": "2026-10-17T10:00:00Z",
            "report_sha256": base_sha}
    (layout["run"] / "evaluations.jsonl").write_text(json.dumps(base) + "\n")
    revised_report = "revised report\n"
    revised_sha = hashlib.sha256(revised_report.encode()).hexdigest()
    rev_rel = "revisions/0001_20261018T120000000000Z.json"
    md_rel = "revisions/0001_20261018T120000000000Z.md"
    (layout["run"] / "revisions").mkdir()
    (layout["run"] / md_rel).write_text(revised_report)
    revision = {**base, "status": "blocked_after_review", "evaluated_utc": "2026-10-18T12:00:00Z",
                "prior_report_sha256": base_sha, "report_sha256": revised_sha,
                "report_path": md_rel, "revision_reason": "fresh evidence", "revision_path": rev_rel}
    raw_revision = json.dumps(revision, ensure_ascii=False, indent=2) + "\n"
    (layout["run"] / rev_rel).write_text(raw_revision)
    row = {"schema": "deep_review_revision.v1", "review_index": i,
           "revision_path": rev_rel, "report_sha256": revised_sha,
           "prior_report_sha256": base_sha,
           "revision_json_sha256": hashlib.sha256(raw_revision.encode()).hexdigest(),
           "reason": "fresh evidence"}
    (layout["run"] / "revisions.jsonl").write_text(json.dumps(row) + "\n")
    progress_path = layout["run"] / "progress.json"
    progress = json.loads(progress_path.read_text())
    progress.update({"updated_utc": "2026-10-18T12:30:00Z", "completed_in_depth_reviews": 1,
                     "completed_valuations": 0, "blocked_after_in_depth_review": 1,
                     "pending": 1, "base_records": 1, "revisions_written": 1})
    _write_json(progress_path, progress)
    checkpoint = dict(progress)
    checkpoint.update({
        "original_rules_sha256": hashlib.sha256(layout["rules"].read_bytes()).hexdigest(),
        "ledger_sha256": hashlib.sha256((layout["run"] / "evaluations.jsonl").read_bytes()).hexdigest(),
        "revisions_sha256": hashlib.sha256((layout["run"] / "revisions.jsonl").read_bytes()).hexdigest(),
    })
    _write_json(layout["root"] / "notes/deep_review_checkpoint.json", checkpoint)

    packet = resume.build_packet(i)
    assert packet["effective_case"]["status"] == "blocked_after_review"
    assert packet["effective_case"]["report_pointer"]["path"].endswith(md_rel)
    assert packet["effective_case"]["report_pointer"]["sha256"] == revised_sha
    assert packet["effective_case"]["latest_revision"]["json_sha256"] == row["revision_json_sha256"]
    assert "report" not in packet["effective_case"]


def test_oversized_full_criteria_fails_without_truncation(layout):
    rows = layout["rows"]
    rows[1]["description"] = "literal criterion " * 1000
    with gzip.open(layout["rules"], "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    checkpoint_path = layout["root"] / "notes/deep_review_checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text())
    checkpoint["original_rules_sha256"] = hashlib.sha256(layout["rules"].read_bytes()).hexdigest()
    _write_json(checkpoint_path, checkpoint)
    with pytest.raises(resume.ResumeError, match="no fields were truncated"):
        resume.build_packet(2, max_bytes=8000)


def test_unsafe_optional_source_pointer_is_rejected(layout):
    work = layout["data"] / "work"
    work.mkdir(parents=True)
    _write_json(work / "0002_resume.json", {
        "review_index": 2, "source_paths": ["../../outside.md"],
    })
    with pytest.raises(resume.ResumeError, match="outside scoped research/data"):
        resume.build_packet(2)


def test_symlink_optional_resume_file_is_rejected(layout, tmp_path):
    work = layout["data"] / "work"
    work.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    _write_json(outside, {"review_index": 2})
    (work / "0002_resume.json").symlink_to(outside)
    with pytest.raises(resume.ResumeError, match="symlink"):
        resume.build_packet(2)


def test_declared_hash_mismatch_fails_clearly(layout):
    checkpoint_path = layout["root"] / "notes/deep_review_checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text())
    checkpoint["original_rules_sha256"] = "0" * 64
    _write_json(checkpoint_path, checkpoint)
    with pytest.raises(resume.ResumeError, match="declared SHA-256 mismatch"):
        resume.build_packet(2)


def test_checkpoint_progress_count_disagreement_fails_clearly(layout):
    checkpoint_path = layout["root"] / "notes/deep_review_checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_text())
    checkpoint["pending"] = 99
    _write_json(checkpoint_path, checkpoint)
    with pytest.raises(resume.ResumeError, match="checkpoint/progress disagreement: pending"):
        resume.build_packet(2)


def test_optional_pointer_omissions_are_counted(layout):
    work = layout["data"] / "work"
    work.mkdir(parents=True)
    _write_json(work / "0002_resume.json", {
        "review_index": 2,
        "source_pointers": [f"https://public.example/source/{i}" for i in range(35)],
    })
    pointers = resume.build_packet(2)["optional_work_pointers"]
    assert pointers["pointers_total"] == 35
    assert pointers["pointers_omitted"] == 5
    assert len(pointers["public_pointers"]) == 30
