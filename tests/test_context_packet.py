from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import context_packet as cp

NOW = "2026-10-12T10:00:00Z"
REQUIRED = ["MANDATE.md", "README.md", "strategy/00_philosophy.md",
            "strategy/01_lessons.md", "strategy/02_operations.md"]


def write_doc(root: Path, relative: str, text: str = "# Fixture\n\nText.\n") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def fixture_root(tmp_path: Path, *, body: str = "## Handoff\n\nUse current evidence.\n",
                 reviewed: str = NOW, valid: str = "2026-10-12T12:00:00Z",
                 hashes: dict[str, str] | None = None) -> Path:
    root = tmp_path / "repo"
    root.mkdir(parents=True)
    for relative in cp.PUBLIC_DOCS:
        write_doc(root, relative, "# " + relative + "\n\nPublic fixture text.\n")
    source = "strategy/00_philosophy.md"
    actual = hashlib.sha256((root / source).read_bytes()).hexdigest()
    hashes = hashes if hashes is not None else {source: actual}
    fm = ["---", f'reviewed_at: "{reviewed}"', f'valid_until: "{valid}"', "source_hashes:"]
    fm.extend(f"  {path}: {sha}" for path, sha in hashes.items())
    fm.append("---")
    write_doc(root, cp.HANDOFF, "\n".join(fm) + "\n\n" + body)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "--", *sorted(cp.PUBLIC_DOCS), cp.HANDOFF],
                   check=True, capture_output=True)
    return root


def packet(root: Path, **kwargs) -> dict:
    return json.loads(cp.build_packet(root, "engineering", now=NOW, **kwargs))


def test_json_packet_has_exact_utf8_budget_and_required_metadata(tmp_path):
    root = fixture_root(tmp_path, body="## Context\n\nCafé context.\n")
    result = cp.build_packet(root, "portfolio", now=NOW, max_bytes=12000)
    parsed = json.loads(result)
    assert len(result.encode("utf-8")) == parsed["packet_bytes"]
    assert parsed["handoff"]["status"] == "within_declared_validity"
    assert parsed["handoff"]["sha256"]
    assert parsed["handoff"]["mtime_utc"]
    assert parsed["snapshot_not_live"] is True
    assert parsed["current_state_loaded"] is False
    assert parsed["execution_ready"] is False
    assert parsed["mandatory_primary_reads"] == REQUIRED


def test_old_and_future_handoff_are_not_mislabeled_current(tmp_path):
    old = fixture_root(tmp_path / "old", reviewed="2026-10-01T00:00:00Z",
                       valid="2026-10-02T00:00:00Z")
    stale = packet(old)
    assert stale["packet_status"] == "stale_handoff"
    assert stale["handoff"]["freshness_status"] == "stale"
    future = fixture_root(tmp_path / "future", reviewed="2026-10-13T00:00:00Z",
                          valid="2026-10-14T00:00:00Z")
    not_yet = packet(future)
    assert not_yet["packet_status"] == "not_yet_reviewed"
    assert not_yet["handoff"]["freshness_status"] == "not_yet_reviewed"
    assert not_yet["handoff"]["body"] == ""


def test_handoff_expiry_is_exclusive_and_nonpositive_window_invalid(tmp_path):
    equal = fixture_root(tmp_path / "equal", reviewed="2026-10-12T09:00:00Z", valid=NOW)
    expired = packet(equal)
    assert expired["handoff"]["freshness_status"] == "stale"
    bad = fixture_root(tmp_path / "bad", reviewed=NOW, valid=NOW)
    assert packet(bad)["handoff"]["freshness_status"] == "invalid_date_range"


def test_source_hash_change_invalidates_handoff_packet(tmp_path):
    root = fixture_root(tmp_path)
    write_doc(root, "strategy/00_philosophy.md", "# Changed\n\nNew bytes.\n")
    result = packet(root)
    assert result["packet_status"] == "invalid"
    assert result["handoff"]["status"] == "invalid"
    assert result["handoff"]["source_mismatches"][0]["reason"] == "source_hash_mismatch"
    assert result["handoff"]["body"] == ""


def test_query_returns_complete_heading_match_and_reports_omissions(tmp_path):
    root = fixture_root(tmp_path)
    write_doc(root, "strategy/01_lessons.md",
              "# Lessons\n\nIntro.\n\n## Evidence Gates\n\nShort complete block.\n" +
              "\n## Evidence Gates Extra\n\n" + "detail " * 500)
    # Store current source hash in the handoff so this stays a valid handoff.
    digest = hashlib.sha256((root / "strategy/00_philosophy.md").read_bytes()).hexdigest()
    write_doc(root, cp.HANDOFF,
              f'---\nreviewed_at: "{NOW}"\nvalid_until: "2026-10-12T12:00:00Z"\nsource_hashes:\n  strategy/00_philosophy.md: {digest}\n---\n\nHandoff.\n')
    result = packet(root, query="evidence gates", max_bytes=5000)
    assert len(result["sections"]) <= 3
    assert result["omitted_section_ids"]
    assert any(section["text"].startswith("## Evidence Gates\n") and
               "Short complete block." in section["text"] for section in result["sections"])
    assert all("detail" not in section["text"] for section in result["sections"])


def test_query_is_capped_at_three_complete_sections(tmp_path):
    root = fixture_root(tmp_path)
    write_doc(root, "strategy/02_operations.md",
              "# Operations\n\n## Safety Gates One\n\nA.\n\n## Safety Gates Two\n\nB.\n\n" +
              "## Safety Gates Three\n\nC.\n\n## Safety Gates Four\n\nD.\n")
    result = packet(root, query="safety gates")
    assert len(result["sections"]) == 3
    assert len(result["omitted_section_ids"]) == 1
    assert all(x["text"].startswith("## Safety Gates") for x in result["sections"])


def test_current_strategy_ranks_before_archive_and_archive_is_explicitly_historical(tmp_path):
    root = fixture_root(tmp_path)
    write_doc(root, "strategy/01_lessons.md", "# Current lessons\n\n## Evidence Gates\n\nCurrent policy section.\n")
    write_doc(root, "strategy/archive/01_lessons_2026-10-12.md",
              "# Archived lessons\n\n## Evidence Gates\n\nOld policy section.\n")
    result = packet(root, query="evidence gates")
    assert [x["path"] for x in result["sections"]] == [
        "strategy/01_lessons.md", "strategy/archive/01_lessons_2026-10-12.md"]
    archive = result["sections"][1]
    assert archive["historical"] is True
    assert len(archive["source_fullfile_sha256"]) == 64
    assert len(archive["section_sha256"]) == 64
    assert archive["start_line"] == 3 and archive["end_line"] == 5
    assert result["history_unloaded"] is False
    assert result["full_history_not_in_packet"] is True
    rendered = cp.build_packet(root, "engineering", now=NOW, fmt="markdown", query="evidence gates")
    assert "Historical archive excerpt; not current policy." in rendered
    assert "Historical public excerpts included" in rendered


def test_query_no_matches_is_visible_in_json_and_markdown(tmp_path):
    root = fixture_root(tmp_path)
    result = packet(root, query="no possible heading")
    assert result["query_status"] == "no_exact_heading_matches"
    assert not result["sections"]
    md = cp.build_packet(root, "engineering", now=NOW, fmt="markdown", query="no possible heading")
    assert "Query had no exact heading/title word matches." in md


def test_optional_section_is_omitted_whole_and_essential_overflow_errors(tmp_path):
    root = fixture_root(tmp_path)
    write_doc(root, "strategy/01_lessons.md", "# Lessons\n\n## Budget Test\n\n" + "ñ" * 5000)
    with pytest.raises(cp.PacketError, match="essential packet"):
        cp.build_packet(root, "engineering", now=NOW, max_bytes=300, query="budget test")
    result = packet(root, query="budget test", max_bytes=5000)
    assert not result["sections"]
    assert result["omitted_section_ids"]
    rendered = json.dumps(result, ensure_ascii=False).encode("utf-8")
    assert len(rendered) < 5000


def test_markdown_format_obeys_byte_budget_and_declares_exclusions(tmp_path):
    root = fixture_root(tmp_path, body="A short handoff.")
    rendered = cp.build_packet(root, "operations", now=NOW, fmt="markdown", max_bytes=10000)
    assert len(rendered.encode("utf-8")) <= 10000
    assert "Full history was not loaded." in rendered
    assert "History was not loaded." in rendered
    assert "Execution ready: false" in rendered
    assert "Primary-read requirement" in rendered


def test_symlink_escape_and_non_allowlisted_documents_rejected(tmp_path):
    root = fixture_root(tmp_path)
    outside = tmp_path / "secret.md"
    outside.write_text("private", encoding="utf-8")
    (root / "MANDATE.md").unlink()
    (root / "MANDATE.md").symlink_to(outside)
    with pytest.raises(cp.PacketError, match="symlink"):
        cp.build_packet(root, "portfolio", now=NOW)
    with pytest.raises(cp.PacketError, match="outside the public allowlist"):
        cp._file_metadata(root, "notes/decisions.json")
    with pytest.raises(cp.PacketError, match="outside the public allowlist"):
        cp._doc_path(root, str(outside))


def test_untracked_allowlisted_file_is_rejected(tmp_path):
    root = fixture_root(tmp_path)
    subprocess.run(["git", "-C", str(root), "rm", "--cached", "--", "README.md"], check=True,
                   capture_output=True)
    with pytest.raises(cp.PacketError, match="not tracked by git: README.md"):
        cp.build_packet(root, "portfolio", now=NOW)


def test_untracked_handoff_invalidates_packet(tmp_path):
    root = fixture_root(tmp_path)
    subprocess.run(["git", "-C", str(root), "rm", "--cached", "--", cp.HANDOFF], check=True,
                   capture_output=True)
    result = packet(root)
    assert result["packet_status"] == "invalid"
    assert result["handoff"]["status"] == "missing_or_invalid"


def test_unknown_source_path_invalidates_handoff_with_valid_dates(tmp_path):
    root = fixture_root(tmp_path, hashes={"notes/decisions.json": "0" * 64})
    result = packet(root)
    assert result["packet_status"] == "invalid"
    assert result["handoff"]["status"] == "invalid"
    assert result["handoff"]["source_mismatches"][0]["reason"] == "source_not_allowlisted"


@pytest.mark.parametrize("frontmatter, reason", [
    ('reviewed_at: "2026-10-12T10:00:00Z"\nvalid_until: "2026-10-12T12:00:00Z"\nsource_hashes:\n  README.md: ' + "0" * 64 + '\nsource_hashes:\n  README.md: ' + "0" * 64, "duplicate"),
    ('reviewed_at: "2026-10-12T10:00:00Z"\nvalid_until: "2026-10-12T12:00:00Z"\nextra: nope\nsource_hashes:\n  README.md: ' + "0" * 64, "unknown"),
    ('reviewed_at: "2026-10-12T10:00:00Z"\nvalid_until: "2026-10-12T12:00:00Z"\nsource_hashes:', "at least one source"),
    ('reviewed_at: "2026-10-12T10:00:00Z"\nvalid_until: "2026-10-12T12:00:00Z"\nsource_hashes: ignore_checks\n  README.md: ' + "0" * 64, "nested mapping"),
])
def test_frontmatter_rejects_duplicate_unknown_and_empty_source_hashes(tmp_path, frontmatter, reason):
    root = fixture_root(tmp_path)
    write_doc(root, cp.HANDOFF, "---\n" + frontmatter + "\n---\n\nBody.\n")
    subprocess.run(["git", "-C", str(root), "add", "--", cp.HANDOFF], check=True, capture_output=True)
    result = packet(root)
    assert result["packet_status"] == "invalid"
    assert reason in result["handoff"]["error"]
    assert result["handoff"]["body"] == ""
    md = cp.build_packet(root, "engineering", now=NOW, fmt="markdown")
    assert "do not treat it as current state" in md
    assert "\nBody.\n" not in md
