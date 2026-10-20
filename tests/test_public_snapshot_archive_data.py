import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_snapshot_archive_data_testmod", ROOT / "scripts/public_snapshot_archive_data.py")
ARCHIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ARCHIVER)


def _fixture(tmp_path, *, version=2, alias_target="shortlist_20261020T104703590448Z_thin_tail.json"):
    rel = "data/snapshots/shortlist_20261012T140330074895Z_thin_tail.json"
    original = tmp_path / rel
    original.parent.mkdir(parents=True)
    rows = [{"id": "m1", "condition_id": "0x01", "criteria": {"x": 1}}]
    raw = json.dumps(rows, separators=(",", ":")).encode()
    original.write_bytes(raw)
    os.chmod(original, 0o640)
    os.utime(original, ns=(1_700_000_000_123_456_789,) * 2)
    metadata = {
        "schema_version": version,
        "snapshot": original.name,
        "scan_kind": "thin_tail",
        "criteria_fingerprint": "sha256:canonical-json-exact-v1",
        "params": {},
        "market_count": 1,
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
    }
    if version == 2 and alias_target == "with_optional":
        metadata["selection_policy"] = "filter-before-top-v1"
        metadata["coverage"] = {"complete": True}
        alias_target = "shortlist_20261020T104703590448Z_thin_tail.json"
    original.with_name(original.stem + ".meta.json").write_text(json.dumps(metadata))
    current = original.parent / "shortlist_20261020T104703590448Z_thin_tail.json"
    current.write_text("[]")
    (original.parent / "shortlist_latest.json").symlink_to(alias_target)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/discover_markets.py").write_text("# test producer\n")
    manifest = tmp_path / "research/archive.json"
    return rel, original, manifest


def _engine(tmp_path, rel, manifest, **kw):
    return ARCHIVER._load_engine(root=tmp_path, allowed_paths=(rel,), manifest=manifest, testing=True, **kw)


def test_frozen_inventory_is_exact_and_excludes_mutable_alias():
    assert len(ARCHIVER.ALLOWED_PATHS) == 48
    assert len(set(ARCHIVER.ALLOWED_PATHS)) == 48
    assert all("20261013" not in p and "latest" not in p for p in ARCHIVER.ALLOWED_PATHS)
    assert "data/snapshots/shortlist_latest.json" not in ARCHIVER.ALLOWED_PATHS


@pytest.mark.parametrize("version,optional", [(1, False), (2, False), (2, True)])
def test_legacy_sidecar_variants_preserved_by_hash(tmp_path, version, optional):
    rel, original, manifest = _fixture(tmp_path, version=version, alias_target="with_optional" if optional else "shortlist_20261020T104703590448Z_thin_tail.json")
    engine = _engine(tmp_path, rel, manifest)
    entry, _ = engine._make_entry(rel, compress=True)
    sidecar = original.with_name(original.stem + ".meta.json").read_bytes()
    assert entry["existing_meta_sidecar"]["sha256"] == hashlib.sha256(sidecar).hexdigest()
    assert entry["existing_meta_sidecar"]["size_bytes"] == len(sidecar)


def test_current_latest_target_must_not_be_archived(tmp_path):
    rel, _, manifest = _fixture(tmp_path, alias_target="shortlist_20261012T140330074895Z_thin_tail.json")
    with pytest.raises(ValueError, match="unsafe or archived"):
        _engine(tmp_path, rel, manifest)


def test_unselected_latest_target_can_change_without_freezing_alias(tmp_path):
    rel, original, manifest = _fixture(tmp_path)
    engine = _engine(tmp_path, rel, manifest)
    alias = original.parent / "shortlist_latest.json"
    alias.unlink()
    alias.symlink_to("shortlist_20261019T104703590448Z_thin_tail.json")
    (original.parent / "shortlist_20261019T104703590448Z_thin_tail.json").write_text("[]")
    assert len(engine.collect_plan()) == 1


@pytest.mark.parametrize("damage", ["symlink", "body", "sidecar", "collision"])
def test_refuses_unsafe_or_changed_inputs(tmp_path, damage):
    rel, original, manifest = _fixture(tmp_path)
    if damage == "symlink":
        outside = tmp_path / "outside.json"
        outside.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(outside)
    elif damage == "body":
        original.write_bytes(b"[]")
    elif damage == "sidecar":
        side = original.with_name(original.stem + ".meta.json")
        side.write_text("{}")
    else:
        original.with_name(original.name + ".gz").write_bytes(b"collision")
    engine = _engine(tmp_path, rel, manifest)
    with pytest.raises((ValueError, FileExistsError, RuntimeError)):
        engine.collect_plan()


def test_roundtrip_restore_and_changed_existing_restore_refusal(tmp_path):
    rel, original, manifest = _fixture(tmp_path)
    raw = original.read_bytes()
    before = original.stat()
    engine = _engine(tmp_path, rel, manifest)
    result = engine.archive_all()
    assert result["entries_archived"] == 1
    assert engine.read_verified_path(rel) == raw
    restored = engine.restore_one(rel)
    assert restored["restored"] is True
    after = original.stat()
    assert original.read_bytes() == raw
    assert stat.S_IMODE(after.st_mode) == stat.S_IMODE(before.st_mode)
    assert after.st_mtime_ns == before.st_mtime_ns

    original.unlink()
    original.write_bytes(b"changed")
    with pytest.raises((ValueError, RuntimeError)):
        engine.restore_one(rel)
    assert original.read_bytes() == b"changed"


def test_ledger_link_checker_uses_data_archive_reader(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts"))
    import deep_review_ledger

    report_dir = tmp_path / "research"
    report_dir.mkdir()
    rel = "data/snapshots/shortlist_20261012T140330074895Z_thin_tail.json"
    calls = []

    class Reader:
        @staticmethod
        def load_manifest():
            return {"entries": [{"original_path": rel}]}

        @staticmethod
        def read_verified_path(path):
            calls.append(path)
            return b"[]"

    monkeypatch.setattr(deep_review_ledger, "ROOT", tmp_path)
    monkeypatch.setitem(sys.modules, "public_snapshot_archive_data", Reader)
    deep_review_ledger.validate_local_markdown_links("[old](../data/snapshots/shortlist_20261012T140330074895Z_thin_tail.json)", report_dir / "report.md")
    assert calls == [rel]


def test_ledger_still_rejects_unrelated_missing_link_without_data_manifest(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "scripts"))
    import deep_review_ledger

    report_dir = tmp_path / "research"
    report_dir.mkdir()

    class EmptyReader:
        @staticmethod
        def load_manifest():
            return {"entries": []}

        @staticmethod
        def read_verified_path(_path):
            raise AssertionError("reader must not be called for an unrelated missing path")

    monkeypatch.setattr(deep_review_ledger, "ROOT", tmp_path)
    monkeypatch.setitem(sys.modules, "public_snapshot_archive_data", EmptyReader)
    with pytest.raises(ValueError, match="local Markdown link target is missing"):
        deep_review_ledger.validate_local_markdown_links("[missing](../docs/no-such-file.md)", report_dir / "report.md")
