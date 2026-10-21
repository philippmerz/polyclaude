import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location("log_storage_test", Path(__file__).parents[1] / "scripts/log_storage.py")
storage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(storage)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ROOT", tmp_path)
    monkeypatch.setattr(storage.subprocess, "check_output", lambda *a, **kw: b"logs/run/tracked.body\0")
    (tmp_path / "logs/run").mkdir(parents=True)
    return tmp_path


def old_file(repo, name="logs/run/page.body", content=None):
    p = repo / name
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = content if content is not None else b"exact original source with repeated evidence\n" * 3000
    p.write_bytes(raw)
    os.chmod(p, 0o600)
    age = time.time() - 48 * 3600
    os.utime(p, (age, age))
    return p, raw


def test_lossless_archive_verify_and_restore_bytes_mode_time(repo):
    p, raw = old_file(repo)
    mtime = p.stat().st_mtime_ns
    result = storage.maintain()
    assert result["archived"] == 1 and result["saved_bytes"] > 0
    assert not p.exists()
    assert storage.read_verified_bytes(p) == raw
    row = storage.mappings()["logs/run/page.body"]
    assert row["sha256"] == hashlib.sha256(raw).hexdigest()
    assert storage._verified(row) == raw
    storage._new_file(p, storage._verified(row), row["mode"])
    os.utime(p, ns=(row["mtime_ns"], row["mtime_ns"]))
    assert p.read_bytes() == raw and p.stat().st_mtime_ns == mtime
    assert p.stat().st_mode & 0o777 == 0o600
    index_before = (repo / storage.INDEX).read_bytes()
    assert storage.maintain()["archived"] == 1
    assert not p.exists() and storage.read_verified_bytes(p) == raw
    assert (repo / storage.INDEX).read_bytes() == index_before


def test_tampered_archive_fails_closed(repo):
    p, _ = old_file(repo)
    storage.maintain()
    Path(str(p) + ".gz").write_bytes(gzip.compress(b"altered"))
    with pytest.raises(ValueError, match="hash mismatch"):
        storage.read_verified_bytes(p)


def test_excludes_tracked_recent_open_alias_hardlink_private_and_receipts(repo):
    tracked, _ = old_file(repo, "logs/run/tracked.body")
    recent, _ = old_file(repo, "logs/run/recent.body")
    os.utime(recent, None)
    held, _ = old_file(repo, "logs/run/held.body")
    alias_target, _ = old_file(repo, "logs/run/latest_target.json")
    (repo / "logs/run/latest.json").symlink_to(alias_target.name)
    hard, _ = old_file(repo, "logs/run/hard.body")
    os.link(hard, repo / "logs/run/hard2.body")
    private, _ = old_file(repo, "logs/operator/opaque.body")
    receipt, _ = old_file(repo, "logs/run/source.receipt.json")
    with held.open("rb"):
        assert list(storage.candidates()) == []
    for p in (tracked, recent, held, alias_target, hard, private, receipt):
        assert p.exists()


def test_changed_source_does_not_unlink(repo, monkeypatch):
    p, raw = old_file(repo)
    before = storage._signature(p)
    original = storage._signature
    calls = 0
    def changing(path):
        nonlocal calls
        calls += 1
        return before if calls == 1 else (before[0], before[1] + 1, before[2], before[3])
    monkeypatch.setattr(storage, "_signature", changing)
    index = repo / storage.INDEX
    index.parent.mkdir(parents=True)
    with index.open("a") as stream, pytest.raises(RuntimeError, match="changed while reading"):
        storage.archive_one(p, stream)
    assert p.read_bytes() == raw
    assert index.read_bytes() == b""


def test_gzip_alias_and_unregistered_missing_path(repo):
    packed = repo / "logs/run/new.json.gz"
    raw = b'{"criteria":"exact text","id":"123"}'
    packed.write_bytes(gzip.compress(raw))
    alias = repo / "logs/run/latest.json"
    alias.symlink_to(packed.name)
    assert storage.read_verified_bytes(alias) == raw
    with pytest.raises(FileNotFoundError):
        storage.read_verified_bytes(repo / "logs/run/unknown.json")


def test_existing_adjacent_gzip_reused_without_changing_it(repo):
    p, raw = old_file(repo)
    archive = Path(str(p) + ".gz")
    packed = gzip.compress(raw, mtime=123)
    archive.write_bytes(packed)
    before = archive.stat().st_mtime_ns
    result = storage.maintain()
    assert result["saved_bytes"] == len(raw)
    assert archive.read_bytes() == packed and archive.stat().st_mtime_ns == before
    assert storage.read_verified_bytes(p) == raw


def test_wrong_or_mislabeled_adjacent_gzip_retains_original(repo):
    p, raw = old_file(repo)
    Path(str(p) + ".gz").write_bytes(raw)
    assert storage.maintain()["archived"] == 0
    assert p.read_bytes() == raw


def test_legacy_snapshot_archive_uses_existing_verified_reader(repo, monkeypatch):
    manifest = repo / "research/2026-10-17-deep-review/ARCHIVED_PUBLIC_DISCOVERY_SNAPSHOTS.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}")
    key = "logs/run/historical.json"
    calls = []
    module = SimpleNamespace(
        load_manifest=lambda: {"entries": [{"original_path": key}]},
        read_verified_path=lambda requested: calls.append(requested) or b"exact verified legacy bytes",
    )
    monkeypatch.setitem(sys.modules, "public_snapshot_archive", module)
    assert storage.read_verified_bytes(repo / key) == b"exact verified legacy bytes"
    assert calls == [key]


def test_interrupted_index_tail_keeps_previous_evidence_readable(repo):
    p, raw = old_file(repo)
    storage.maintain()
    with (repo / storage.INDEX).open("ab") as stream:
        stream.write(b'{"path":"unfinished')
    assert storage.read_verified_bytes(p) == raw
    assert len(storage.mappings()) == 1


def test_maintenance_preserves_and_recovers_incomplete_tail(repo):
    p, raw = old_file(repo)
    storage.maintain()
    tail = b'{"path":"unfinished'
    with (repo / storage.INDEX).open("ab") as stream:
        stream.write(tail)
    new, other = old_file(repo, "logs/run/other.body", b"different content\n" * 5000)
    result = storage.maintain()
    assert result["recovered_tail_bytes"] == len(tail)
    assert len(storage.mappings()) == 2
    assert storage.read_verified_bytes(p) == raw
    assert storage.read_verified_bytes(new) == other
    recovery = list((repo / storage.INDEX).parent.glob("index-uncommitted-*.gz"))
    assert len(recovery) == 1 and gzip.decompress(recovery[0].read_bytes()) == tail


def test_complete_corrupt_index_row_is_rejected(repo):
    p, _ = old_file(repo)
    storage.maintain()
    with (repo / storage.INDEX).open("ab") as stream:
        stream.write(b'not valid JSON\n')
    with pytest.raises(ValueError):
        storage.mappings()
