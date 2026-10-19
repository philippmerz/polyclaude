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


def _standard_economics(p_yes: float, reserve_pp: float = 15.0) -> dict:
    return {
        "both_sides_considered": True,
        "actual_entry_reserve_pp": reserve_pp,
        "sides": {
            "Yes": {
                "probability": p_yes,
                "selected_stress_probability": max(0.0, p_yes - reserve_pp / 100),
            },
            "No": {
                "probability": 1 - p_yes,
                "selected_stress_probability": max(0.0, 1 - p_yes - reserve_pp / 100),
            },
        },
    }


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


def test_record_rejects_stale_economic_probability_before_writing(review_run: Path, tmp_path: Path):
    payload = _record_input(1, "valued", "Stale probability fixture.")
    payload["economics"] = _standard_economics(0.8)
    source = _write_input(tmp_path / "stale-base.json", payload)

    with pytest.raises(AssertionError, match="economic Yes probability does not match forecast"):
        ledger.record(source)

    assert not (review_run / "evaluations" / "0001.json").exists()
    assert not (review_run / "evaluations" / "0001.md").exists()
    assert not (review_run / "evaluations.jsonl").exists()


@pytest.mark.parametrize(("tamper", "message"), [
    ("complement", "economic No probability does not complement forecast"),
    ("stress", "economic No stress probability does not match forecast reserve"),
])
def test_revision_probability_economics_mismatch_fails_without_mutation(
    review_run: Path, tmp_path: Path, tamper: str, message: str,
):
    base_path, base_record = _save_base(review_run, tmp_path)
    base_bytes = base_path.read_bytes()
    evaluation_ledger = review_run / "evaluations.jsonl"
    ledger_bytes = evaluation_ledger.read_bytes()
    source = _revision_input(tmp_path, report="Inconsistent source update.")
    payload = json.loads(source.read_text())
    payload["economics"] = _standard_economics(0.74592)
    payload["forecast"]["p_yes"] = 0.74592
    payload["forecast"]["low"] = 0.7
    payload["forecast"]["high"] = 0.8
    if tamper == "complement":
        payload["economics"]["sides"]["No"]["probability"] = 0.2
    else:
        payload["economics"]["sides"]["No"]["selected_stress_probability"] = 0.2
    _write_input(source, payload)

    with pytest.raises(AssertionError, match=message):
        ledger.revise(source, base_record["report_sha256"], "Reject inconsistent economics.")

    assert base_path.read_bytes() == base_bytes
    assert evaluation_ledger.read_bytes() == ledger_bytes
    assert not (review_run / "revisions.jsonl").exists()
    assert _revision_files(review_run) == []


def test_source_update_with_current_probabilities_and_reserve_is_accepted(review_run: Path, tmp_path: Path):
    base_path, base_record = _save_base(review_run, tmp_path)
    base_bytes = base_path.read_bytes()
    source = _revision_input(tmp_path, report="Current probability and economics.")
    payload = json.loads(source.read_text())
    p_yes = 0.74592
    payload["forecast"]["p_yes"] = p_yes
    payload["forecast"]["low"] = 0.6
    payload["forecast"]["high"] = 0.9
    payload["economics"] = _standard_economics(p_yes)
    _write_input(source, payload)

    result = ledger.revise(source, base_record["report_sha256"], "Record current probability consistently.")

    assert result["completed_valuations"] == 1
    assert base_path.read_bytes() == base_bytes
    row = json.loads((review_run / "revisions.jsonl").read_text().splitlines()[0])
    revised = json.loads((review_run / row["revision_path"]).read_text())
    assert revised["forecast"]["p_yes"] == pytest.approx(p_yes)
    assert revised["economics"]["sides"]["Yes"]["probability"] == pytest.approx(p_yes)
    assert revised["economics"]["sides"]["No"]["probability"] == pytest.approx(1 - p_yes)


def _named_record_fixture():
    frozen = {**_frozen(1), "outcomes": '["Mbappé", "Yamal"]'}
    payload = _record_input(1, "valued", "Exact named outcomes.")
    payload["forecast"]["probability_reference_outcome"] = "Mbappé"
    economics = _standard_economics(0.6)
    economics["probability_reference_outcome"] = "Mbappé"
    economics["sides"] = {"Yamal": economics["sides"]["No"], "Mbappé": economics["sides"]["Yes"]}
    payload["economics"] = economics
    return payload, frozen


def test_named_outcomes_bind_reference_and_complement_by_exact_label():
    payload, frozen = _named_record_fixture()
    ledger.validate_record(payload, frozen, validate_economics_forecast=True)


@pytest.mark.parametrize("tamper", ["reference", "forecast_reference", "side_label", "probability", "stress"])
def test_named_outcome_mismatch_stops_before_record(review_run: Path, tmp_path: Path, monkeypatch, tamper):
    payload, frozen = _named_record_fixture()
    monkeypatch.setattr(ledger, "universe", lambda: {1: frozen})
    if tamper == "reference":
        del payload["economics"]["probability_reference_outcome"]
    elif tamper == "forecast_reference":
        payload["forecast"]["probability_reference_outcome"] = "Yamal"
    elif tamper == "side_label":
        payload["economics"]["sides"]["Mbappe"] = payload["economics"]["sides"].pop("Mbappé")
    elif tamper == "probability":
        payload["economics"]["sides"]["Yamal"]["probability"] = 0.3
    else:
        payload["economics"]["sides"]["Yamal"]["selected_stress_probability"] = 0.3
    source = _write_input(tmp_path / "named-invalid.json", payload)
    with pytest.raises(AssertionError):
        ledger.record(source)
    assert not (review_run / "evaluations.jsonl").exists()
    assert not (review_run / "evaluations" / "0001.json").exists()
    assert not (review_run / "evaluations" / "0001.md").exists()


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


def test_record_checks_links_from_evaluations_directory_before_writing(review_run: Path, tmp_path: Path):
    source_dir = review_run.parent.parent / "data"
    source_dir.mkdir()
    source = source_dir / "source artifact.md"
    source.write_text("Source facts.\n", encoding="utf-8")
    report = (
        "Valid local [source](<../../../data/source%20artifact.md#facts>), "
        "[web](https://example.test/a), [anchor](#section), and "
        "[mail](mailto:research@example.test)."
    )
    path = _write_input(tmp_path / "valid-base.json", _record_input(1, "blocked_after_review", report))
    ledger.record(path)
    saved = (review_run / "evaluations" / "0001.md").read_text(encoding="utf-8")
    assert "../../../data/source%20artifact.md#facts" in saved

    broken = _write_input(
        tmp_path / "broken-base.json",
        _record_input(2, "blocked_after_review", "Broken [source](../../data/missing.md)."),
    )
    with pytest.raises(ValueError, match="local Markdown link target is missing"):
        ledger.record(broken)
    assert not (review_run / "evaluations" / "0002.json").exists()
    assert not (review_run / "evaluations" / "0002.md").exists()
    assert len((review_run / "evaluations.jsonl").read_text().splitlines()) == 1


def test_revision_checks_links_from_revisions_directory_before_writing(review_run: Path, tmp_path: Path):
    source_dir = review_run.parent.parent / "data"
    source_dir.mkdir()
    (source_dir / "source artifact.md").write_text("Source facts.\n", encoding="utf-8")
    _, base_record = _save_base(review_run, tmp_path)

    valid = _revision_input(
        tmp_path,
        report=(
            "[source](<../../../data/source%20artifact.md#facts>) "
            "[external](https://example.test) [anchor](#notes) [email](mailto:a@b.test)."
        ),
    )
    ledger.revise(valid, base_record["report_sha256"], "Test valid revision links.")
    rows_before = (review_run / "revisions.jsonl").read_bytes()
    files_before = [p.relative_to(review_run).as_posix() for p in _revision_files(review_run)]

    invalid = _revision_input(tmp_path, report="Bad [source](../../../data/missing.md).")
    current = json.loads((review_run / "revisions.jsonl").read_text().splitlines()[-1])
    with pytest.raises(ValueError, match="local Markdown link target is missing"):
        ledger.revise(invalid, current["report_sha256"], "Must fail before write.")
    assert (review_run / "revisions.jsonl").read_bytes() == rows_before
    assert [p.relative_to(review_run).as_posix() for p in _revision_files(review_run)] == files_before


def test_local_link_repository_escape_fails_before_record_artifacts(review_run: Path, tmp_path: Path):
    path = _write_input(
        tmp_path / "escaping-base.json",
        _record_input(1, "blocked_after_review", "Escape [source](../../../../outside.md)."),
    )
    with pytest.raises(ValueError, match="local Markdown link escapes repository"):
        ledger.record(path)
    assert not (review_run / "evaluations" / "0001.json").exists()
    assert not (review_run / "evaluations.jsonl").exists()


@pytest.mark.parametrize("profile", ["prior36", "more-html"])
def test_local_link_accepts_existing_extra_archived_public_source_without_restore(profile: str):
    # Exercise a real receipt-linked archive entry and its profile-specific
    # verified reader. Validation must not restore the adjacent .body file.
    import public_source_archive_extra

    manifest_path = public_source_archive_extra.PROFILES[profile]["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = next(
        item for item in manifest["entries"]
        if item.get("original_path") and not (ledger.ROOT / item["original_path"]).exists()
    )
    original = ledger.ROOT / entry["original_path"]
    archive = ledger.ROOT / entry["archive_path"]
    assert archive.is_file()
    report_path = ledger.ROOT / "research/2026-10-17-deep-review/evaluations/archive-link-fixture.md"
    relative = Path(__import__("os").path.relpath(original, report_path.parent))
    assert not original.exists()

    ledger.validate_local_markdown_links(f"[archived source]({relative.as_posix()})", report_path)

    assert not original.exists()
