#!/usr/bin/env python3
"""Lossless storage for closed, untracked project artifacts; no evidence expiry.

Archive mappings preserve exact bytes and hashes. Receipts, tracked files,
hardlinks, current aliases, open files and private operator material are excluded.
"""
from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
INDEX = Path("logs/storage_archive/index.jsonl")
ROOTS = ("logs", "data/snapshots")
SUFFIXES = {".json", ".md", ".body", ".html", ".http", ".txt", ".tsv", ".stdout", ".stderr", ".bin", ".log"}
PRIVATE = {"operator", "telegram", "inbox", "private", "secrets", "storage_archive"}
METADATA = {"manifest.json", "summary.json", "response_metadata.json", "receipt_index.json"}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def relative(path: str | Path) -> str:
    path = Path(path)
    path = path if path.is_absolute() else ROOT / path
    # Keep a missing legacy filename; resolving an old alias still follows its target.
    return path.resolve(strict=False).relative_to(ROOT.resolve()).as_posix()


def mappings() -> dict[str, dict]:
    path = ROOT / INDEX
    if not path.exists():
        return {}
    found = {}
    for line in path.read_bytes().splitlines(keepends=True):
        # Newline is the record commit marker. A crashed append cannot hide
        # earlier verified mappings; malformed complete records still fail.
        if not line.endswith(b"\n"):
            break
        row = json.loads(line)
        if row["path"] in found and found[row["path"]] != row:
            raise ValueError("conflicting storage archive mappings")
        found[row["path"]] = row
    return found


def _recover_incomplete_tail(path: Path) -> int:
    """Under the maintenance lock, preserve/truncate only an uncommitted tail."""
    if not path.exists():
        return 0
    raw = path.read_bytes()
    if not raw or raw.endswith(b"\n"):
        return 0
    boundary = raw.rfind(b"\n") + 1
    tail = raw[boundary:]
    recovery = path.with_name(f"index-uncommitted-{time.time_ns()}.jsonpart.gz")
    _new_file(recovery, gzip.compress(tail, compresslevel=6, mtime=0))
    with path.open("r+b") as stream:
        stream.truncate(boundary)
        stream.flush()
        os.fsync(stream.fileno())
    return len(tail)


def _verified(row: dict) -> bytes:
    source = ROOT / row["path"]
    packed_path = ROOT / row["gzip_path"]
    if relative(source) != row["path"] or relative(packed_path) != row["gzip_path"]:
        raise ValueError("archive mapping escapes repository or changes identity")
    packed = packed_path.read_bytes()
    if digest(packed) != row["gzip_sha256"]:
        raise ValueError("archive compressed hash mismatch")
    raw = gzip.decompress(packed)
    if len(raw) != row["bytes"] or digest(raw) != row["sha256"]:
        raise ValueError("archive decompressed hash/size mismatch")
    return raw


def read_verified_bytes(path: str | Path) -> bytes:
    """Read plain/new gzip artifacts or a manifest-verified archived legacy path."""
    actual = Path(path)
    actual = actual if actual.is_absolute() else ROOT / actual
    if actual.is_file():
        raw = actual.read_bytes()
        return gzip.decompress(raw) if raw.startswith(b"\x1f\x8b") else raw
    key = relative(path)
    row = mappings().get(key)
    if row is not None:
        return _verified(row)
    # Existing frozen snapshot archives predate the general storage index.
    # Reuse their stricter hash/sidecar verification instead of trusting a .gz
    # filename or making older scans disappear from prior-snapshot selection.
    for module_name, manifest_name in (
        ("public_snapshot_archive", "ARCHIVED_PUBLIC_DISCOVERY_SNAPSHOTS.json"),
        ("public_snapshot_archive_data", "ARCHIVED_PUBLIC_DATA_THIN_TAIL_SNAPSHOTS.json"),
    ):
        if not (ROOT / "research/2026-10-17-deep-review" / manifest_name).is_file():
            continue
        module = __import__(module_name)
        loader = getattr(module, "load_manifest", None) or getattr(module, "_load_manifest")
        try:
            doc = loader()
        except FileNotFoundError:
            continue
        if any(entry.get("original_path") == key for entry in doc.get("entries", [])):
            return module.read_verified_path(key)
    raise FileNotFoundError(key)


read_verified_path = read_verified_bytes


def _signature(path: Path) -> tuple[int, int, int, int]:
    st = path.lstat()
    return st.st_ino, st.st_size, st.st_mtime_ns, st.st_nlink


def _excluded(parts: tuple[str, ...]) -> bool:
    words = "/".join(parts).lower()
    return bool(set(parts) & PRIVATE) or any(x in words for x in (
        "credential", "transcript", "session", "wallet", "secret", "private", "telegram", "inbox", "account/",
    ))


def candidates(*, older_hours: float = 24, min_bytes: int = 32768):
    """Inventory by metadata; never traverse private histories or follow symlinks."""
    tracked = set(subprocess.check_output(
        ["git", "ls-files", "-z"], cwd=ROOT
    ).decode().split("\0"))
    open_inodes = set()
    for fd_dir in Path("/proc").glob("[0-9]*/fd"):
        try:
            for fd in fd_dir.iterdir():
                try:
                    st = fd.stat()
                    open_inodes.add((st.st_dev, st.st_ino))
                except OSError:
                    pass
        except OSError:
            pass
    aliases = set()
    paths = []
    for folder in ROOTS:
        for parent, dirs, files in os.walk(ROOT / folder, followlinks=False):
            relparent = Path(parent).relative_to(ROOT)
            dirs[:] = [d for d in dirs if not _excluded((*relparent.parts, d)) and not (Path(parent) / d).is_symlink()]
            for name in files:
                path = Path(parent) / name
                if path.is_symlink():
                    aliases.add(path.resolve(strict=False))
                else:
                    paths.append(path)
    cutoff = time.time() - older_hours * 3600
    for path in sorted(paths):
        rel = path.relative_to(ROOT)
        if (rel.as_posix() in tracked or _excluded(rel.parts) or path in aliases
                or path.suffix not in SUFFIXES or path.name in METADATA
                or path.name.endswith((".meta.json", ".receipt.json", ".intent.json"))):
            continue
        # Root daemon logs remain open; only closed per-run .log files qualify.
        if path.suffix == ".log" and len(rel.parts) < 3:
            continue
        st = path.lstat()
        if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_size < min_bytes
                or st.st_mtime > cutoff or (st.st_dev, st.st_ino) in open_inodes):
            continue
        yield path


def _new_file(path: Path, data: bytes, mode: int = 0o600) -> None:
    fd, name = tempfile.mkstemp(prefix=".archive-", dir=path.parent)
    temporary = Path(name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)  # exclusive atomic publication
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def archive_one(path: Path, index_stream, known: dict | None = None) -> dict | None:
    before = _signature(path)
    st = path.stat()
    raw = path.read_bytes()
    if known is not None:
        # A restored exact original can be retired again without rewriting its
        # immutable mapping or its already verified archive.
        if (digest(raw) != known["sha256"] or len(raw) != known["bytes"]
                or stat.S_IMODE(st.st_mode) != known["mode"]
                or st.st_mtime_ns != known["mtime_ns"]):
            return None
        if _verified(known) != raw or _signature(path) != before:
            raise RuntimeError("restored source/archive differs; original retained")
        path.unlink()
        return {**known, "created_gzip": False}
    packed = gzip.compress(raw, compresslevel=6, mtime=0)
    if len(packed) >= len(raw) * .85:
        return None
    if _signature(path) != before:
        raise RuntimeError("artifact changed while reading")
    archive = Path(str(path) + ".gz")
    row = {"path": relative(path), "gzip_path": relative(archive),
           "bytes": len(raw), "sha256": digest(raw), "gzip_bytes": len(packed),
           "gzip_sha256": digest(packed), "mode": stat.S_IMODE(st.st_mode),
           "mtime_ns": st.st_mtime_ns}
    if archive.exists():
        existing = archive.read_bytes()
        try:
            if not existing.startswith(b"\x1f\x8b") or gzip.decompress(existing) != raw:
                return None
        except (OSError, EOFError):
            return None
        row.update(gzip_bytes=len(existing), gzip_sha256=digest(existing), created_gzip=False)
    else:
        _new_file(archive, packed, stat.S_IMODE(st.st_mode))
        row["created_gzip"] = True
    if _verified(row) != raw or _signature(path) != before:
        raise RuntimeError("archive roundtrip/source stability verification failed; original retained")
    # Durable recovery mapping precedes removal. A crash leaves both copies, never neither.
    index_stream.write(json.dumps(row, separators=(",", ":")) + "\n")
    index_stream.flush()
    os.fsync(index_stream.fileno())
    index_dir = os.open(Path(index_stream.name).parent, os.O_RDONLY)
    try:
        os.fsync(index_dir)
    finally:
        os.close(index_dir)
    if _signature(path) != before:
        raise RuntimeError("artifact changed before unlink; original retained")
    path.unlink()
    source_dir = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(source_dir)
    finally:
        os.close(source_dir)
    return row


def maintain(*, older_hours=24, min_bytes=32768, max_files=0, max_input_mib=0) -> dict:
    folder = (ROOT / INDEX).parent
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    result = {"archived": 0, "input_bytes": 0, "stored_bytes": 0, "errors": 0}
    with (folder / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result["recovered_tail_bytes"] = _recover_incomplete_tail(ROOT / INDEX)
        known = mappings()
        with (ROOT / INDEX).open("a", encoding="utf-8") as stream:
            os.chmod(ROOT / INDEX, 0o600)
            for path in candidates(older_hours=older_hours, min_bytes=min_bytes):
                if max_files and result["archived"] >= max_files:
                    break
                if max_input_mib and result["input_bytes"] >= max_input_mib * 1024**2:
                    break
                row = archive_one(path, stream, known.get(relative(path)))
                if row:
                    result["archived"] += 1
                    result["input_bytes"] += row["bytes"]
                    result["stored_bytes"] += row["gzip_bytes"] if row["created_gzip"] else 0
    result["saved_bytes"] = result["input_bytes"] - result["stored_bytes"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "maintain", "verify", "restore"))
    parser.add_argument("path", nargs="?")
    parser.add_argument("--older-hours", type=float, default=24)
    parser.add_argument("--min-bytes", type=int, default=32768)
    parser.add_argument("--max-files", type=int, default=0)
    parser.add_argument("--max-input-mib", type=int, default=0)
    args = parser.parse_args()
    if args.older_hours < 24 or args.min_bytes < 4096 or args.max_files < 0 or args.max_input_mib < 0:
        parser.error("require >=24 hours, >=4096 minimum bytes and nonnegative bounds")
    if args.command == "plan":
        paths = list(candidates(older_hours=args.older_hours, min_bytes=args.min_bytes))
        print(json.dumps({"files": len(paths), "bytes": sum(p.stat().st_size for p in paths),
                          "paths": [relative(p) for p in paths]}, separators=(",", ":")))
    elif args.command == "maintain":
        print(json.dumps(maintain(older_hours=args.older_hours, min_bytes=args.min_bytes,
                                 max_files=args.max_files, max_input_mib=args.max_input_mib), separators=(",", ":")))
    elif args.command == "verify":
        rows = mappings()
        for row in rows.values():
            _verified(row)
        data = (ROOT / INDEX).read_bytes() if (ROOT / INDEX).exists() else b""
        tail = len(data) - data.rfind(b"\n") - 1 if data and not data.endswith(b"\n") else 0
        print(json.dumps({"verified": len(rows), "uncommitted_tail_bytes": tail}))
    else:
        if not args.path:
            parser.error("restore requires original repository-relative path")
        key = relative(args.path)
        row = mappings()[key]
        raw = _verified(row)
        path = ROOT / key
        if path.exists():
            if path.read_bytes() != raw:
                raise ValueError("refusing to overwrite changed original")
        else:
            _new_file(path, raw, row["mode"])
            os.utime(path, ns=(row["mtime_ns"], row["mtime_ns"]))
        print(json.dumps({"restored": key, "sha256": digest(raw)}))


if __name__ == "__main__":
    main()
