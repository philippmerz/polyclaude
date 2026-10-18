#!/usr/bin/env python3
"""Reversible, allowlisted archive for nine public Gamma discovery snapshots.

The default ``plan`` command is read-only. ``archive --confirm-unlink`` writes
deterministic adjacent gzip copies, commits an immutable manifest, verifies all
bytes and metadata, and only then unlinks the original snapshots. No HTTP receipt
is asserted; the existing discovery metadata sidecar is recorded by hash only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/2026-10-17-deep-review/ARCHIVED_PUBLIC_DISCOVERY_SNAPSHOTS.json"
SCHEMA = "public_gamma_discovery_snapshot_archive.v1"
SOURCE_URL = "https://gamma-api.polymarket.com"
PRODUCER = "scripts/discover_markets.py"

# Exact inventory allowlist only. Never expand this with globbing.
ALLOWED_PATHS = (
    "logs/checkin_20261014T0200/discovery/snapshots/shortlist_20261014T020425380830Z_thin_tail.json",
    "logs/checkin_20261013T0200/discovery/snapshots/shortlist_20261013T020442113512Z_thin_tail.json",
    "logs/checkin_20261015T1400/discovery/snapshots/shortlist_20261015T140224824104Z_thin_tail.json",
    "logs/checkin_20261016T0200/discovery/snapshots/shortlist_20261016T020207340252Z_thin_tail.json",
    "logs/checkin_20261013T1400/discovery/snapshots/shortlist_20261013T140234104643Z_thin_tail.json",
    "logs/checkin_20261016T0014/discovery/snapshots/shortlist_20261016T001703271816Z_thin_tail.json",
    "logs/checkin_20261014T1400/discovery/snapshots/shortlist_20261014T140226311832Z_thin_tail.json",
    "logs/checkin_20261015T0200/discovery/snapshots/shortlist_20261015T020152718331Z_thin_tail.json",
    "logs/checkin_20261016T1400/discovery/snapshots/shortlist_20261016T140204941589Z_thin_tail.json",
)
ALIASES = {
    ALLOWED_PATHS[0]: "logs/checkin_20261014T0200/discovery/snapshots/shortlist_latest.json",
    ALLOWED_PATHS[1]: "logs/checkin_20261013T0200/discovery/snapshots/shortlist_latest.json",
    ALLOWED_PATHS[2]: "logs/checkin_20261015T1400/discovery/snapshots/shortlist_latest.json",
    ALLOWED_PATHS[3]: "logs/checkin_20261016T0200/discovery/snapshots/shortlist_latest.json",
    ALLOWED_PATHS[4]: "logs/checkin_20261013T1400/discovery/snapshots/shortlist_latest.json",
    ALLOWED_PATHS[5]: "logs/checkin_20261016T0014/discovery/snapshots/shortlist_latest.json",
    ALLOWED_PATHS[6]: "logs/checkin_20261014T1400/discovery/snapshots/shortlist_latest.json",
    ALLOWED_PATHS[7]: "logs/checkin_20261015T0200/discovery/snapshots/shortlist_latest.json",
    ALLOWED_PATHS[8]: "logs/checkin_20261016T1400/discovery/snapshots/shortlist_latest.json",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(p in {"", ".", ".."} for p in path.parts):
        raise ValueError(f"unsafe repository-relative path: {value!r}")
    return path


def _checked_path(value: str, *, must_exist: bool = False) -> Path:
    rel = _relative(value)
    path = ROOT.joinpath(*rel.parts)
    current = ROOT
    for component in rel.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError(f"symlink component refused: {value}")
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {value}") from exc
    if must_exist and not path.exists():
        raise FileNotFoundError(value)
    return path


def _signature(path: Path) -> dict[str, int]:
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode):
        raise ValueError(f"not a regular file: {path.relative_to(ROOT)}")
    return {
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "mode": stat.S_IMODE(st.st_mode),
        "inode": st.st_ino,
        "device": st.st_dev,
    }


def _read_stable(path: Path) -> tuple[bytes, dict[str, int]]:
    before = _signature(path)
    data = path.read_bytes()
    after = _signature(path)
    if before != after or len(data) != before["size"]:
        raise RuntimeError(f"file changed while reading: {path.relative_to(ROOT)}")
    return data, before


def _sidecar(original: Path, raw: bytes, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    sidecar = original.with_name(original.stem + ".meta.json")
    rel = sidecar.relative_to(ROOT).as_posix()
    path = _checked_path(rel)
    if not path.exists():
        raise FileNotFoundError(f"required discovery metadata sidecar missing: {rel}")
    data, sig = _read_stable(path)
    metadata = json.loads(data)
    if metadata.get("snapshot_sha256") != sha256(raw):
        raise ValueError(f"discovery sidecar snapshot_sha256 mismatch: {rel}")
    if metadata.get("market_count") != len(rows):
        raise ValueError(f"discovery sidecar market_count mismatch: {rel}")
    if metadata.get("snapshot") != original.name:
        raise ValueError(f"discovery sidecar names a different snapshot: {rel}")
    return {"path": rel, "size_bytes": len(data), "sha256": sha256(data),
            "mode_octal": oct(sig["mode"]), "mtime_ns": sig["mtime_ns"]}


def _alias_snapshot(original_rel: str) -> dict[str, Any]:
    """Record an adjacent shortlist_latest.json symlink without following it."""
    alias_rel = ALIASES[original_rel]
    alias = _relative(alias_rel)
    parent_rel = alias.parent.as_posix()
    _checked_path(parent_rel, must_exist=True)
    path = ROOT.joinpath(*alias.parts)
    if not os.path.lexists(path):
        return {"path": alias_rel, "present": False}
    st = path.lstat()
    if not stat.S_ISLNK(st.st_mode):
        raise ValueError(f"expected shortlist_latest.json symlink: {alias_rel}")
    target = os.readlink(path)
    expected_target = Path(original_rel).name
    if target != expected_target:
        raise ValueError(f"shortlist alias target mismatch for {alias_rel}: {target!r}")
    return {
        "path": alias_rel,
        "present": True,
        "target": target,
        "mode_octal": oct(stat.S_IMODE(st.st_mode)),
        "mtime_ns": st.st_mtime_ns,
    }


def _verify_alias(expected: dict[str, Any]) -> None:
    alias = _relative(expected["path"])
    _checked_path(alias.parent.as_posix(), must_exist=True)
    path = ROOT.joinpath(*alias.parts)
    if not expected.get("present"):
        if os.path.lexists(path):
            raise ValueError(f"unexpected shortlist alias appeared: {expected['path']}")
        return
    if not os.path.lexists(path):
        raise FileNotFoundError(f"shortlist alias missing: {expected['path']}")
    st = path.lstat()
    if not stat.S_ISLNK(st.st_mode):
        raise ValueError(f"shortlist alias changed from symlink: {expected['path']}")
    target = os.readlink(path)
    if (target != expected["target"] or oct(stat.S_IMODE(st.st_mode)) != expected["mode_octal"]
            or st.st_mtime_ns != expected["mtime_ns"]):
        raise ValueError(f"shortlist alias metadata/target changed: {expected['path']}")


def _assert_allowlisted(original_rel: str) -> None:
    if original_rel not in ALLOWED_PATHS:
        raise ValueError(f"path is outside the exact nine-file allowlist: {original_rel}")


def _make_entry(original_rel: str, *, compress: bool) -> tuple[dict[str, Any], bytes | None]:
    _assert_allowlisted(original_rel)
    original = _checked_path(original_rel, must_exist=True)
    raw, sig = _read_stable(original)
    rows = json.loads(raw)
    if not isinstance(rows, list):
        raise ValueError(f"discovery snapshot must be a JSON list: {original_rel}")
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"snapshot row {index} is not an object: {original_rel}")
        if not row.get("id") or not row.get("condition_id") or not isinstance(row.get("criteria"), dict):
            raise ValueError(f"snapshot row {index} lacks id, condition_id, or criteria object: {original_rel}")
    packed = gzip.compress(raw, compresslevel=6, mtime=0) if compress else None
    archive_rel = original_rel + ".gz"
    archive = _checked_path(archive_rel)
    if archive.exists():
        raise FileExistsError(f"adjacent archive already exists: {archive_rel}")
    sidecar = _sidecar(original, raw, rows)
    entry = {
        "original_path": original_rel,
        "archive_path": archive_rel,
        "original_size_bytes": len(raw),
        "original_sha256": sha256(raw),
        "gzip_size_bytes": len(packed) if packed is not None else None,
        "gzip_sha256": sha256(packed) if packed is not None else None,
        "original_mode_octal": oct(sig["mode"]),
        "original_mtime_ns": sig["mtime_ns"],
        "existing_meta_sidecar": sidecar,
        "symlink_alias": _alias_snapshot(original_rel),
        "http_receipt": None,
    }
    return entry, packed


def collect_plan() -> list[dict[str, Any]]:
    if MANIFEST.exists():
        raise FileExistsError(f"immutable archive manifest already exists: {MANIFEST.relative_to(ROOT)}")
    entries: list[dict[str, Any]] = []
    for rel in ALLOWED_PATHS:
        entry, _ = _make_entry(rel, compress=True)
        entries.append(entry)
    return entries


def _manifest_doc(entries: list[dict[str, Any]], producer_source: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "Exact nine completed Oct 13–16 check-in thin-tail snapshots listed in scripts/public_snapshot_archive.py; no data/snapshots, Oct 17+, or other files.",
        "provenance": {
            "producer_script": PRODUCER,
            "producer_script_sha256": producer_source["sha256"],
            "producer_script_size_bytes": producer_source["size_bytes"],
            "public_endpoint": SOURCE_URL,
            "description": "Gamma-derived local discovery snapshots; archive metadata does not assert an HTTP receipt or exact request response binding.",
            "http_receipts_asserted": False,
        },
        "compression": {"format": "gzip", "level": 6, "mtime": 0, "deterministic_within_runtime": True},
        "hash_algorithm": "SHA-256 over exact original bytes and exact gzip bytes",
        "reader": "scripts/public_snapshot_archive.py read_verified_path(original_path) verifies the original or adjacent gzip. Restore recreates the exact original and refuses changed existing files.",
        "alias_handling": "Existing shortlist_latest.json symlinks are preserved unchanged and verified by path/target/mode/mtime. They are not rewritten to gzip; while the original is archived, each existing alias is dangling, so direct filesystem/JSON reads through it require restore first.",
        "entry_count": len(entries),
        "original_total_bytes": sum(x["original_size_bytes"] for x in entries),
        "gzip_total_bytes": sum(x["gzip_size_bytes"] for x in entries),
        "entries": entries,
    }


def _load_manifest() -> dict[str, Any]:
    manifest_rel = MANIFEST.relative_to(ROOT).as_posix()
    path = _checked_path(manifest_rel, must_exist=True)
    raw, _ = _read_stable(path)
    doc = json.loads(raw)
    if doc.get("schema") != SCHEMA or doc.get("entry_count") != len(ALLOWED_PATHS):
        raise ValueError("archive manifest schema/count mismatch")
    entries = doc.get("entries")
    if not isinstance(entries, list) or {x.get("original_path") for x in entries if isinstance(x, dict)} != set(ALLOWED_PATHS):
        raise ValueError("manifest does not contain the exact allowlist")
    for e in entries:
        original = e["original_path"]
        _assert_allowlisted(original)
        if e.get("archive_path") != original + ".gz" or e.get("http_receipt") is not None:
            raise ValueError(f"unexpected manifest mapping/receipt: {original}")
        _checked_path(original)
        _checked_path(e["archive_path"])
        if not isinstance(e.get("symlink_alias"), dict):
            raise ValueError(f"missing recorded alias state: {original}")
        _verify_alias(e["symlink_alias"])
    return doc


def _verify_entry(entry: dict[str, Any]) -> bytes:
    original = _checked_path(entry["original_path"])
    archive = _checked_path(entry["archive_path"])
    raw: bytes | None = None
    if original.exists():
        raw, sig = _read_stable(original)
        if (len(raw) != entry["original_size_bytes"] or sha256(raw) != entry["original_sha256"]
                or sig["mtime_ns"] != entry["original_mtime_ns"]
                or oct(sig["mode"]) != entry["original_mode_octal"]):
            raise ValueError(f"original bytes/metadata differ from manifest: {entry['original_path']}")
    if archive.exists():
        packed, sig = _read_stable(archive)
        if (len(packed) != entry["gzip_size_bytes"] or sha256(packed) != entry["gzip_sha256"]
                or sig["mtime_ns"] != entry["original_mtime_ns"]
                or oct(sig["mode"]) != entry["original_mode_octal"]):
            raise ValueError(f"gzip bytes/metadata differ from manifest: {entry['archive_path']}")
        unpacked = gzip.decompress(packed)
        if len(unpacked) != entry["original_size_bytes"] or sha256(unpacked) != entry["original_sha256"]:
            raise ValueError(f"gzip round trip mismatch: {entry['original_path']}")
        if raw is not None and raw != unpacked:
            raise ValueError(f"original/gzip bytes differ: {entry['original_path']}")
        raw = unpacked
    if raw is None:
        raise FileNotFoundError(f"original and archive both missing: {entry['original_path']}")
    side = entry.get("existing_meta_sidecar")
    if side is None:
        sidecar = original.with_name(original.stem + ".meta.json")
        if sidecar.exists():
            raise ValueError(f"unexpected metadata sidecar appeared: {sidecar.relative_to(ROOT)}")
    else:
        sidecar = _checked_path(side["path"], must_exist=True)
        data, sig = _read_stable(sidecar)
        if (len(data) != side["size_bytes"] or sha256(data) != side["sha256"]
                or sig["mtime_ns"] != side["mtime_ns"] or oct(sig["mode"]) != side["mode_octal"]):
            raise ValueError(f"metadata sidecar changed: {side['path']}")
    alias = entry.get("symlink_alias")
    if not isinstance(alias, dict):
        raise ValueError(f"missing recorded symlink alias: {entry['original_path']}")
    _verify_alias(alias)
    return raw


def read_verified_path(original_path: str) -> bytes:
    """Read an allowlisted original path from disk or its verified adjacent gzip."""
    _assert_allowlisted(original_path)
    doc = _load_manifest()
    entry = next(e for e in doc["entries"] if e["original_path"] == original_path)
    return _verify_entry(entry)


def verify_all() -> dict[str, int]:
    doc = _load_manifest()
    raw_total = gzip_total = 0
    for entry in doc["entries"]:
        _verify_entry(entry)
        raw_total += entry["original_size_bytes"]
        archive = _checked_path(entry["archive_path"])
        if archive.exists():
            gzip_total += entry["gzip_size_bytes"]
    return {"entries_verified": len(doc["entries"]), "symlink_aliases_verified": len(doc["entries"]),
            "original_bytes": raw_total, "gzip_bytes": gzip_total}


def _producer_source() -> dict[str, Any]:
    path = _checked_path(PRODUCER, must_exist=True)
    raw, sig = _read_stable(path)
    return {"sha256": sha256(raw), "size_bytes": len(raw), "mtime_ns": sig["mtime_ns"]}


def _write_new(path: Path, data: bytes, *, mode: int, mtime_ns: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        if mtime_ns is not None:
            os.utime(temp, ns=(mtime_ns, mtime_ns))
        os.link(temp, path)
        temp.unlink()
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def archive_all() -> dict[str, Any]:
    if MANIFEST.exists():
        raise FileExistsError(f"immutable archive manifest already exists: {MANIFEST.relative_to(ROOT)}")
    entries: list[dict[str, Any]] = []
    created_archives: list[Path] = []
    manifest_written = False
    try:
        for rel in ALLOWED_PATHS:
            entry, packed = _make_entry(rel, compress=True)
            assert packed is not None
            original = _checked_path(rel, must_exist=True)
            _write_new(_checked_path(entry["archive_path"]), packed,
                       mode=int(entry["original_mode_octal"], 8), mtime_ns=entry["original_mtime_ns"])
            created_archives.append(_checked_path(entry["archive_path"]))
            entries.append(entry)
        doc = _manifest_doc(entries, _producer_source())
        # Verify source, gzip, metadata sidecars and all round trips before manifest commit.
        for entry in entries:
            _verify_entry(entry)
        payload = (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        _write_new(MANIFEST, payload, mode=0o644)
        manifest_written = True
        verify_all()
        # Recheck every source and sidecar before the first unlink.
        for entry in entries:
            _verify_entry(entry)
        for entry in entries:
            source = _checked_path(entry["original_path"], must_exist=True)
            # Hash/signature check immediately before each destructive unlink.
            _verify_entry(entry)
            source.unlink()
        final = verify_all()
        return {"entries_archived": len(entries), "original_bytes_removed": doc["original_total_bytes"],
                "gzip_bytes": final["gzip_bytes"], "bytes_reclaimed": doc["original_total_bytes"] - final["gzip_bytes"]}
    except Exception:
        if not manifest_written and not MANIFEST.exists():
            for archive in created_archives:
                archive.unlink(missing_ok=True)
        raise


def restore_one(original_path: str) -> dict[str, Any]:
    _assert_allowlisted(original_path)
    doc = _load_manifest()
    entry = next(e for e in doc["entries"] if e["original_path"] == original_path)
    original = _checked_path(original_path)
    raw = _verify_entry(entry)
    if original.exists():
        return {"restored": False, "already_present": True, "path": original_path}
    fd, name = tempfile.mkstemp(prefix=f".{original.name}.", suffix=".restore", dir=original.parent)
    temp = Path(name)
    try:
        mode = int(entry["original_mode_octal"], 8)
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        ns = entry["original_mtime_ns"]
        os.utime(temp, ns=(ns, ns))
        try:
            os.link(temp, original)
        except FileExistsError:
            existing, sig = _read_stable(original)
            if (sha256(existing) != entry["original_sha256"] or len(existing) != entry["original_size_bytes"]
                    or sig["mtime_ns"] != ns or oct(sig["mode"]) != entry["original_mode_octal"]):
                raise RuntimeError(f"refusing to overwrite a changed existing file: {original_path}")
        temp.unlink()
        _verify_entry(entry)
        return {"restored": True, "path": original_path, "bytes": len(raw), "sha256": sha256(raw)}
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="read-only exact allowlist and deterministic gzip estimate")
    archive = sub.add_parser("archive", help="archive, verify, commit manifest, then unlink originals")
    archive.add_argument("--confirm-unlink", action="store_true", help="required explicit destructive-operation acknowledgement")
    sub.add_parser("verify", help="verify manifest, originals/archives, and sidecar identities")
    restore = sub.add_parser("restore", help="restore one allowlisted original without overwriting changed bytes")
    restore.add_argument("original_path")
    args = parser.parse_args()
    if args.command == "plan":
        entries = collect_plan()
        raw = sum(e["original_size_bytes"] for e in entries)
        packed = sum(e["gzip_size_bytes"] for e in entries)
        producer_source = _producer_source()
        print(json.dumps({"entries": len(entries), "original_bytes": raw, "gzip_bytes": packed,
                          "estimated_reclaim_bytes": raw - packed, "manifest": MANIFEST.relative_to(ROOT).as_posix(),
                          "sidecars_present": sum(e["existing_meta_sidecar"] is not None for e in entries),
                          "symlink_aliases_present": sum(e["symlink_alias"]["present"] for e in entries),
                          "producer_script_sha256": producer_source["sha256"],
                          "http_receipts_asserted": False,
                          "paths": [{"path": e["original_path"], "raw_bytes": e["original_size_bytes"],
                                     "gzip_bytes": e["gzip_size_bytes"],
                                     "symlink_alias": e["symlink_alias"]} for e in entries]}, sort_keys=True))
    elif args.command == "archive":
        if not args.confirm_unlink:
            parser.error("archive requires --confirm-unlink; no files changed")
        print(json.dumps(archive_all(), sort_keys=True))
    elif args.command == "verify":
        print(json.dumps(verify_all(), sort_keys=True))
    elif args.command == "restore":
        print(json.dumps(restore_one(args.original_path), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
