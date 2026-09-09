from pathlib import Path
import re

import pytest

from scripts import kb


def write_doc(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def kb_root(tmp_path, monkeypatch):
    monkeypatch.setattr(kb, "ROOT", tmp_path)
    write_doc(tmp_path, "docs/START.md", "# Agent\ncurrent needle\n")
    write_doc(tmp_path, "README.md", "# Readme\ncurrent readme\n")
    write_doc(tmp_path, "strategy/00_philosophy.md", "# Philosophy\ncurrent doctrine\n")
    write_doc(tmp_path, "notes/backlog.md", "# Backlog\ncurrent gate\n")
    return tmp_path


def test_search_defaults_to_current_and_history_is_explicit(kb_root, capsys):
    write_doc(kb_root, "notes/journal.md", "# 2026-01-01\nneedle historical\n")
    write_doc(kb_root, "research/old.md", "# Old\nneedle research\n")
    assert kb.main(["search", "needle"]) == 0
    current = capsys.readouterr().out
    assert "docs/START.md:2" in current
    assert "journal.md" not in current
    assert kb.main(["search", "needle", "--history"]) == 0
    history = capsys.readouterr().out
    assert "notes/journal.md:2" in history
    assert "research/old.md:2" in history


def test_toc_ignores_fenced_headings_and_keeps_levels(kb_root, capsys):
    path = write_doc(kb_root, "notes/toc.md", "# One\n```md\n## hidden\n```\n### Three\n~~~~\n# hidden too\n~~~~\n#### Four\n")
    assert kb.main(["toc", str(path)]) == 0
    output = capsys.readouterr().out
    assert "toc.md:1: # One" in output
    assert "toc.md:5: ### Three" in output
    assert "toc.md:9: #### Four" in output
    assert "hidden" not in output


def test_toc_last_is_bounded(kb_root, capsys):
    path = write_doc(kb_root, "notes/toc.md", "# One\n## Two\n### Three\n")
    assert kb.main(["toc", str(path), "--last", "2"]) == 0
    output = capsys.readouterr().out
    assert "One" not in output
    assert "Two" in output and "Three" in output
    assert "[INCOMPLETE:" in output
    assert "omit --last" in output


def test_recent_inherits_date_for_time_subentries_and_weekly_heading(kb_root, capsys):
    path = write_doc(
        kb_root,
        "notes/log.md",
        "# Week 2026-09-01 → 2026-09-07\n\n10:00 UTC first\nbody\n- 11:30 UTC second\n### 12:00 UTC heading child\nchild\n## 2026-09-08 — next\nfinal\n",
    )
    assert kb.main(["recent", str(path), "--entries", "3"]) == 0
    output = capsys.readouterr().out
    assert "2026-09-08" in output
    assert "2026-09-01 11:30 (date inherited)" in output
    assert "2026-09-01 12:00 (date inherited)" in output
    assert "10:00 UTC first" not in output
    assert "FILE: notes/log.md" in output


def test_recent_warns_when_no_dated_entries(kb_root, capsys):
    write_doc(kb_root, "notes/plain.md", "# Heading\nno date here\n")
    assert kb.main(["recent", "notes/plain.md"]) == 0
    assert "WARNING: no dated entries" in capsys.readouterr().out


def test_read_is_line_numbered_and_reports_end(kb_root, capsys):
    write_doc(kb_root, "notes/slice.md", "a\nb\nc\nd\n")
    assert kb.main(["read", "notes/slice.md", "--start", "2", "--lines", "1"]) == 0
    output = capsys.readouterr().out
    assert "FILE: notes/slice.md" in output
    assert "2: b" in output
    assert "continues after line 2" in output
    assert "next line 3" in output


def test_truncation_has_incomplete_and_continuation(kb_root, capsys):
    write_doc(kb_root, "notes/long.md", "# Heading\n" + ("needle " * 100) + "\n")
    assert kb.main(["search", "needle", "--history", "--max-chars", "256"]) == 0
    output = capsys.readouterr().out
    assert "[INCOMPLETE:" in output
    assert "CONTINUE:" in output


def test_read_budget_continues_at_first_unprinted_line_and_long_line_is_not_sliced(kb_root, capsys):
    write_doc(kb_root, "notes/lines.md", "\n".join(f"value {i}" for i in range(1, 80)))
    assert kb.main(["read", "notes/lines.md", "--start", "1", "--lines", "60", "--max-chars", "256"]) == 0
    output = capsys.readouterr().out
    match = re.search(r"output truncated before source line (\d+)", output)
    assert match
    next_line = int(match.group(1))
    assert f"CONTINUE: read notes/lines.md --start {next_line} --lines 60" in output
    assert f"\n{next_line}:" not in output
    assert len(output) <= 256

    write_doc(kb_root, "notes/huge.md", "x" * 10000)
    assert kb.main(["read", "notes/huge.md", "--lines", "1", "--max-chars", "256"]) == 0
    output = capsys.readouterr().out
    assert "output truncated before source line 1" in output
    assert "CONTINUE: read notes/huge.md --start 1" in output


def test_recent_budget_continuation_identifies_file_and_line(kb_root, capsys):
    path = write_doc(kb_root, "notes/recent.md", "\n".join([f"## 2026-09-{i:02d} entry" for i in range(1, 15)]))
    assert kb.main(["recent", str(path), "--entries", "2", "--max-chars", "256"]) == 0
    output = capsys.readouterr().out
    assert "FILE: notes/recent.md" in output
    assert "[INCOMPLETE:" in output
    assert "CONTINUE: read notes/recent.md --start" in output or "CONTINUE: recent notes/recent.md" in output


def test_tiny_budget_is_rejected(kb_root, capsys):
    with pytest.raises(SystemExit):
        kb.main(["read", "README.md", "--max-chars", "255"])
    assert "256..20000" in capsys.readouterr().err


def test_search_limits_hits_to_twelve_with_marker(kb_root, capsys):
    write_doc(kb_root, "notes/many.md", "\n".join(f"manyneedle {i}" for i in range(20)))
    assert kb.main(["search", "manyneedle", "--history"]) == 0
    output = capsys.readouterr().out
    assert output.count("many.md:") == 12
    assert "bounded to 12 hits" in output
    assert "read notes/many.md --start 13" in output


def test_search_path_is_bounded_and_history_tree_skips_unapproved_dirs(kb_root, capsys):
    write_doc(kb_root, "notes/many.md", "manyneedle\n")
    write_doc(kb_root, "node_modules/noise.md", "manyneedle\n")
    write_doc(kb_root, "data/secret.md", "manyneedle\n")
    seen = []
    original_walk = kb.os.walk

    def spy(*args, **kwargs):
        seen.append(Path(args[0]))
        yield from original_walk(*args, **kwargs)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(kb.os, "walk", spy)
    try:
        assert kb.main(["search", "manyneedle", "--history"]) == 0
        output = capsys.readouterr().out
        assert "notes/many.md:1" in output
        assert "node_modules" not in output and "data/secret" not in output
        assert all("node_modules" not in str(path) and "data" not in str(path) for path in seen)
        assert any(path == kb_root / "notes" for path in seen)
        assert kb.main(["search", "manyneedle", "--history", "--path", "notes/many.md"]) == 0
        assert "notes/many.md:1" in capsys.readouterr().out
    finally:
        monkeypatch.undo()


def test_rejects_outside_traversal_symlink_and_nonprose(kb_root, tmp_path, capsys):
    outside = tmp_path.parent / "outside.md"
    outside.write_text("secret needle", encoding="utf-8")
    assert kb.main(["read", str(outside)]) == 2
    assert "inside the repository" in capsys.readouterr().err
    write_doc(kb_root, "misc/notes.md", "not in an approved directory")
    assert kb.main(["read", "misc/notes.md"]) == 2
    assert "approved prose" in capsys.readouterr().err
    assert kb.main(["read", "notes/../README.md"]) == 2
    assert "traversal" in capsys.readouterr().err
    write_doc(kb_root, "notes/private/secret.md", "secret")
    assert kb.main(["read", "notes/private/secret.md"]) == 2
    assert "private" in capsys.readouterr().err
    (kb_root / "notes/link.md").symlink_to(kb_root / "README.md")
    assert kb.main(["read", "notes/link.md"]) == 2
    assert "symlink" in capsys.readouterr().err
    write_doc(kb_root, "notes/state.json", "{}")
    assert kb.main(["read", "notes/state.json"]) == 2
    assert "Markdown/text" in capsys.readouterr().err
    write_doc(kb_root, "AGENTS.md", "host private")
    assert kb.main(["read", "AGENTS.md"]) == 2
    assert "host-private" in capsys.readouterr().err


def test_retrieval_does_not_write(kb_root, monkeypatch, capsys):
    write_doc(kb_root, "notes/read.md", "# 2026-09-01\nneedle\n")
    before = {p: p.stat().st_mtime_ns for p in kb_root.rglob("*") if p.is_file()}
    assert kb.main(["recent", "notes/read.md"]) == 0
    capsys.readouterr()
    after = {p: p.stat().st_mtime_ns for p in kb_root.rglob("*") if p.is_file()}
    assert before == after
