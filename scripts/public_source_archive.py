#!/usr/bin/env python3
"""Verified, reversible archive for a narrow set of public HTML source captures.

This utility is intentionally limited to four named source families in completed
Oct 1–16 checkin/periodic folders. It never edits source receipt JSON.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import html.parser
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from datetime import datetime, timezone
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/2026-10-17-deep-review/ARCHIVED_PUBLIC_SOURCE_BODIES.json"
ALLOWED_BODIES = {
    "aa_argon_comparison.body": "aa_argon_comparison",
    "google_september_recap.body": "google_september_recap",
    "google_argon.body": "google_argon",
    "agi_homepage.body": "agi_homepage",
}
RUN_RE = re.compile(r"^(?:checkin|periodic)_202610(?:0[1-9]|1[0-6])T\d{4}(?:[A-Za-z0-9_-]*)$")
SCHEMA = "public_source_body_archive.v1"


class UnlinkedCapture(Exception):
    """A body has no successful receipt proving that it is the public response."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def safe_repo_path(value: str) -> Path:
    path = (ROOT / value).resolve(strict=False)
    path.relative_to(ROOT)
    return path


def approved_source_rel(value: str) -> bool:
    parts = Path(value).parts
    return (
        len(parts) == 4
        and parts[0] == "logs"
        and bool(RUN_RE.match(parts[1]))
        and parts[2] == "sources"
        and parts[3] in ALLOWED_BODIES
    )


class _TitleParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


def page_title(data: bytes) -> str | None:
    parser = _TitleParser()
    parser.feed(data.decode("utf-8", errors="replace"))
    value = " ".join(" ".join(parser.title_parts).split())
    return value or None


def file_signature(path: Path) -> dict[str, int]:
    st = path.stat()
    return {
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "mode": stat.S_IMODE(st.st_mode),
        "inode": st.st_ino,
        "device": st.st_dev,
    }


def receipt_for(path: Path, data: bytes, family: str) -> dict[str, Any]:
    actual_sha = sha256(data)
    wanted_path = rel(path)
    options: list[tuple[Path, str, str, dict[str, Any], bytes, dict[str, int]]] = []
    for filename, schema in (("response_metadata.json", "response_metadata"), ("summary.json", "summary.source_metadata")):
        receipt_path = path.parent / filename
        if not receipt_path.is_file():
            continue
        before = file_signature(receipt_path)
        receipt_bytes = receipt_path.read_bytes()
        after = file_signature(receipt_path)
        if before != after or len(receipt_bytes) != before["size"]:
            raise RuntimeError(f"response metadata changed while reading: {rel(receipt_path)}")
        receipt = json.loads(receipt_bytes)
        records = receipt.get("source_metadata") or {} if schema == "summary.source_metadata" else receipt
        if not isinstance(records, dict):
            continue
        for key, record in records.items():
            if not isinstance(key, str) or not (key == family or key.startswith(family + "_retry")) or not isinstance(record, dict):
                continue
            body_path = record.get("body_path") or record.get("final_body_capture") or record.get("capture")
            request = record.get("request") or {}
            final_url = record.get("final_url") or record.get("response_url") or request.get("url")
            headers = record.get("selected_response_headers") or record.get("response_headers_selected") or record.get("response_headers") or record.get("headers") or {}
            recorded_bytes = record.get("bytes") if record.get("bytes") is not None else record.get("response_bytes")
            status = record.get("status") or record.get("final_status")
            if body_path != wanted_path:
                continue
            if status != 200:
                continue
            if recorded_bytes != len(data) or record.get("sha256") != actual_sha:
                raise RuntimeError(f"HTTP 200 receipt hash/size mismatch; refusing changed capture: {wanted_path}")
            content_type = headers.get("content-type")
            if not isinstance(final_url, str) or not final_url.startswith("https://"):
                raise RuntimeError(f"invalid public source URL in receipt: {wanted_path}")
            if not isinstance(content_type, str) or not content_type.lower().startswith("text/html"):
                raise RuntimeError(f"unexpected receipt MIME type {content_type!r}: {wanted_path}")
            options.append((receipt_path, schema, key, record, receipt_bytes, after))
    if not options:
        raise UnlinkedCapture(f"no successful HTTP 200 HTML receipt binds source body: {wanted_path}")
    receipt_path, schema, key, record, receipt_bytes, after = options[-1]
    request = record.get("request") or {}
    final_url = record.get("final_url") or record.get("response_url") or request.get("url")
    headers = record.get("selected_response_headers") or record.get("response_headers_selected") or record.get("response_headers") or record.get("headers") or {}
    content_type = headers["content-type"]
    body_path = record.get("body_path") or record.get("final_body_capture") or record.get("capture")
    recorded_bytes = record.get("bytes") if record.get("bytes") is not None else record.get("response_bytes")
    status = record.get("status") or record.get("final_status")
    return {
        "metadata_path": rel(receipt_path),
        "metadata_sha256": sha256(receipt_bytes),
        "metadata_bytes": len(receipt_bytes),
        "metadata_key": key,
        "metadata_schema": schema,
        "receipt_body_path": body_path,
        "receipt_status": status,
        "receipt_bytes": recorded_bytes,
        "receipt_sha256": record["sha256"],
        "source_url": request.get("url"),
        "final_url": final_url,
        "content_type": content_type,
        "captured_started_utc": record.get("started_utc"),
        "captured_ended_utc": record.get("ended_utc"),
        "source_title": page_title(data),
        "metadata_signature": after,
    }


def candidate_paths() -> list[Path]:
    found: list[Path] = []
    for run in sorted((ROOT / "logs").iterdir()):
        if not run.is_dir() or not RUN_RE.match(run.name):
            continue
        sources = run / "sources"
        if not sources.is_dir() or sources.is_symlink():
            continue
        for basename in ALLOWED_BODIES:
            path = sources / basename
            if path.exists():
                if path.is_symlink() or not approved_source_rel(rel(path)):
                    raise RuntimeError(f"unexpected symlink/path in approved source family: {path}")
                found.append(path)
    return found


def collect_plan() -> tuple[list[dict[str, Any]], list[tuple[Path, bytes, dict[str, int]]], list[dict[str, str]]]:
    if MANIFEST.exists():
        raise FileExistsError(f"archive manifest already exists: {rel(MANIFEST)}")
    entries: list[dict[str, Any]] = []
    staged: list[tuple[Path, bytes, dict[str, int]]] = []
    skipped: list[dict[str, str]] = []
    for path in candidate_paths():
        if path.parent.parent.name == "operator" or any(x in path.parts for x in ("operator", "telegram", "inbox", "private")):
            raise RuntimeError(f"unexpected excluded path in candidate set: {rel(path)}")
        before = file_signature(path)
        raw = path.read_bytes()
        after = file_signature(path)
        if before != after or len(raw) != before["size"]:
            raise RuntimeError(f"source changed while reading: {rel(path)}")
        family = ALLOWED_BODIES[path.name]
        try:
            linkage = receipt_for(path, raw, family)
        except UnlinkedCapture:
            skipped.append({"original_path": rel(path), "reason": "no successful HTTP 200 HTML receipt binds body; left untouched"})
            continue
        archive = path.with_name(path.name + ".gz")
        if archive.exists():
            raise FileExistsError(f"archive collision: {rel(archive)}")
        compressed = gzip.compress(raw, compresslevel=6, mtime=0)
        entry = {
            "original_path": rel(path),
            "archive_path": rel(archive),
            "original_size_bytes": len(raw),
            "original_sha256": sha256(raw),
            "archive_size_bytes": len(compressed),
            "archive_sha256": sha256(compressed),
            "original_mode_octal": oct(before["mode"]),
            "original_mtime_ns": before["mtime_ns"],
            "capture_run": path.parent.parent.name,
            "capture_key": family,
            **{k: v for k, v in linkage.items() if k != "metadata_signature"},
        }
        entries.append(entry)
        staged.append((path, raw, before))
    if not entries:
        raise RuntimeError("no approved source bodies found")
    return entries, staged, skipped


def write_atomic(
    path: Path,
    data: bytes,
    mode: int = 0o644,
    mtime_ns: int | None = None,
    replace: bool = True,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        if mtime_ns is not None:
            os.utime(temp, ns=(mtime_ns, mtime_ns))
        if replace:
            os.replace(temp, path)
        else:
            os.link(temp, path)
            temp.unlink()
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        try:
            temp.unlink(missing_ok=True)
        finally:
            raise


def load_manifest() -> dict[str, Any]:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA or not isinstance(doc.get("entries"), list):
        raise ValueError(f"unsupported or malformed manifest: {rel(MANIFEST)}")
    seen: set[str] = set()
    for entry in doc["entries"]:
        original = entry.get("original_path")
        archive = entry.get("archive_path")
        if not isinstance(original, str) or not isinstance(archive, str) or original in seen:
            raise ValueError("invalid or duplicate source-body manifest entry")
        seen.add(original)
        if archive != original + ".gz":
            raise ValueError(f"unexpected archive mapping: {original}")
        safe_repo_path(original)
        safe_repo_path(archive)
        if not approved_source_rel(original):
            raise ValueError(f"unapproved source path in manifest: {original}")
    for skipped in doc.get("skipped_candidates", []):
        if not isinstance(skipped, dict) or not approved_source_rel(skipped.get("original_path", "")):
            raise ValueError("unapproved skipped source path in manifest")
    if doc.get("entry_count") != len(doc["entries"]):
        raise ValueError("manifest entry_count mismatch")
    if doc.get("skipped_count") != len(doc.get("skipped_candidates", [])):
        raise ValueError("manifest skipped_count mismatch")
    return doc


def verified_bytes(entry: dict[str, Any]) -> bytes:
    original = safe_repo_path(entry["original_path"])
    archive = safe_repo_path(entry["archive_path"])
    if original.is_file():
        raw = original.read_bytes()
        if len(raw) != entry["original_size_bytes"] or sha256(raw) != entry["original_sha256"]:
            raise ValueError(f"restored source differs from manifest: {entry['original_path']}")
        st = original.stat()
        if st.st_mtime_ns != entry["original_mtime_ns"] or stat.S_IMODE(st.st_mode) != int(entry["original_mode_octal"], 8):
            raise ValueError(f"restored source metadata differs from manifest: {entry['original_path']}")
        return raw
    if not archive.is_file():
        raise FileNotFoundError(f"both source and archive missing: {entry['original_path']}")
    packed = archive.read_bytes()
    if len(packed) != entry["archive_size_bytes"] or sha256(packed) != entry["archive_sha256"]:
        raise ValueError(f"gzip hash/size mismatch: {entry['archive_path']}")
    raw = gzip.decompress(packed)
    if len(raw) != entry["original_size_bytes"] or sha256(raw) != entry["original_sha256"]:
        raise ValueError(f"decompressed source hash/size mismatch: {entry['original_path']}")
    return raw


def read_verified_path(original_rel: str) -> bytes:
    """Read a legacy source path from disk or its verified adjacent gzip archive."""
    doc = load_manifest()
    entry = next((x for x in doc["entries"] if x["original_path"] == original_rel), None)
    if entry is None:
        raise KeyError(f"path is not in archive manifest: {original_rel}")
    return verified_bytes(entry)


def verify_all() -> dict[str, Any]:
    doc = load_manifest()
    raw_total = archive_total = 0
    for entry in doc["entries"]:
        raw = verified_bytes(entry)
        raw_total += len(raw)
        archive = safe_repo_path(entry["archive_path"])
        if archive.exists():
            packed = archive.read_bytes()
            if len(packed) != entry["archive_size_bytes"] or sha256(packed) != entry["archive_sha256"]:
                raise ValueError(f"gzip hash/size mismatch: {entry['archive_path']}")
            archive_stat = archive.stat()
            if archive_stat.st_mtime_ns != entry["original_mtime_ns"]:
                raise ValueError(f"archive mtime differs from original capture: {entry['archive_path']}")
            if stat.S_IMODE(archive_stat.st_mode) != int(entry["original_mode_octal"], 8):
                raise ValueError(f"archive mode differs from original capture: {entry['archive_path']}")
            archive_total += len(packed)
        # Verify the untouched capture receipt still binds the original body and source.
        metadata = safe_repo_path(entry["metadata_path"])
        mbytes = metadata.read_bytes()
        if len(mbytes) != entry["metadata_bytes"] or sha256(mbytes) != entry["metadata_sha256"]:
            raise ValueError(f"source metadata changed: {entry['metadata_path']}")
        receipt = json.loads(mbytes)
        if entry["metadata_schema"] == "summary.source_metadata":
            record = (receipt.get("source_metadata") or {}).get(entry["metadata_key"])
        else:
            record = receipt.get(entry["metadata_key"])
        linked_path = None if not isinstance(record, dict) else (
            record.get("body_path") or record.get("final_body_capture") or record.get("capture")
        )
        if not isinstance(record, dict) or linked_path != entry["receipt_body_path"]:
            raise ValueError(f"receipt linkage changed: {entry['original_path']}")
        recorded_bytes = record.get("bytes") if record.get("bytes") is not None else record.get("response_bytes")
        if record.get("sha256") != entry["original_sha256"] or recorded_bytes != entry["original_size_bytes"]:
            raise ValueError(f"receipt body hash/size no longer match: {entry['original_path']}")
        request_url = (record.get("request") or {}).get("url")
        final_url = record.get("final_url") or record.get("response_url") or request_url
        status = record.get("status") or record.get("final_status")
        if final_url != entry["final_url"] or status != 200:
            raise ValueError(f"receipt source identity/status mismatch: {entry['original_path']}")
        content_type = (record.get("selected_response_headers") or record.get("response_headers_selected") or record.get("response_headers") or record.get("headers") or {}).get("content-type")
        if content_type != entry["content_type"]:
            raise ValueError(f"receipt MIME type mismatch: {entry['original_path']}")
    for skipped in doc.get("skipped_candidates", []):
        path = safe_repo_path(skipped["original_path"])
        if not path.is_file():
            raise FileNotFoundError(f"unlinked/failure body should remain untouched: {skipped['original_path']}")
    return {"entries_verified": len(doc["entries"]), "original_bytes": raw_total, "archive_bytes": archive_total}


def restore_one(original_rel: str) -> dict[str, Any]:
    doc = load_manifest()
    entry = next((x for x in doc["entries"] if x["original_path"] == original_rel), None)
    if entry is None:
        raise KeyError(f"path is not in archive manifest: {original_rel}")
    original = safe_repo_path(original_rel)
    raw = verified_bytes(entry)
    if original.exists():
        return {"restored": False, "already_present": True, "path": original_rel}
    mode = int(entry["original_mode_octal"], 8)
    original.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{original.name}.", suffix=".restore", dir=original.parent)
    temp = Path(temp_name)
    try:
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
            existing = original.read_bytes()
            if sha256(existing) != entry["original_sha256"]:
                raise RuntimeError(f"refusing to overwrite differing existing source: {original_rel}")
        os.unlink(temp)
        dir_fd = os.open(original.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    restored = original.read_bytes()
    st = original.stat()
    if len(restored) != entry["original_size_bytes"] or sha256(restored) != entry["original_sha256"]:
        raise RuntimeError(f"restored bytes failed validation: {original_rel}")
    if stat.S_IMODE(st.st_mode) != mode or st.st_mtime_ns != entry["original_mtime_ns"]:
        raise RuntimeError(f"restored metadata failed validation: {original_rel}")
    return {"restored": True, "path": original_rel, "bytes": len(restored), "sha256": sha256(restored)}


def archive_all() -> dict[str, Any]:
    entries, staged, skipped = collect_plan()
    # Create all gzip files first, leaving every original intact until all mappings pass.
    created: list[Path] = []
    try:
        for entry, (original, raw, original_sig) in zip(entries, staged, strict=True):
            archive = safe_repo_path(entry["archive_path"])
            if archive.exists():
                raise FileExistsError(f"archive collision: {entry['archive_path']}")
            packed = gzip.compress(raw, compresslevel=6, mtime=0)
            write_atomic(archive, packed, int(entry["original_mode_octal"], 8), original_sig["mtime_ns"])
            created.append(archive)
        # Verify every gzip, every source, every receipt, and stable original metadata.
        for entry, (original, raw, original_sig) in zip(entries, staged, strict=True):
            packed = safe_repo_path(entry["archive_path"]).read_bytes()
            current_raw = original.read_bytes()
            current_sig = file_signature(original)
            if current_sig != original_sig or current_raw != raw:
                raise RuntimeError(f"source changed during archive creation: {entry['original_path']}")
            if len(packed) != entry["archive_size_bytes"] or sha256(packed) != entry["archive_sha256"]:
                raise RuntimeError(f"gzip bytes mismatch: {entry['archive_path']}")
            inflated = gzip.decompress(packed)
            if len(inflated) != entry["original_size_bytes"] or sha256(inflated) != entry["original_sha256"]:
                raise RuntimeError(f"gzip round-trip mismatch: {entry['original_path']}")
            receipt_for(original, current_raw, entry["capture_key"])
        now = datetime.now(timezone.utc).isoformat()
        manifest = {
            "schema": SCHEMA,
            "created_utc": now,
            "scope": "Only four named public HTML source-body families in completed Oct 1–16 checkin/periodic runs; all captures retained individually.",
            "compression": {"format": "gzip", "level": 6, "mtime": 0, "method": "gzip.compress"},
            "path_resolution": "Original path maps to adjacent .gz. scripts/public_source_archive.py verifies bytes and source receipt links; restore refuses a differing existing file.",
            "hash_algorithm": "SHA-256 over exact source bytes and exact gzip bytes",
            "entry_count": len(entries),
            "skipped_count": len(skipped),
            "skipped_candidates": skipped,
            "original_total_bytes": sum(e["original_size_bytes"] for e in entries),
            "archive_total_bytes": sum(e["archive_size_bytes"] for e in entries),
            "entries": entries,
        }
        payload = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        write_atomic(MANIFEST, payload, 0o644, replace=False)
        verified = verify_all()
        if verified["entries_verified"] != len(entries):
            raise RuntimeError("manifest verification count mismatch")
        # Only now remove originals, after a fresh per-path stat/hash/receipt check.
        removed_raw = 0
        removed_entries: list[str] = []
        for entry, (original, raw, original_sig) in zip(entries, staged, strict=True):
            if file_signature(original) != original_sig or sha256(original.read_bytes()) != entry["original_sha256"]:
                raise RuntimeError(f"source changed before removal: {entry['original_path']}")
            receipt_for(original, raw, entry["capture_key"])
            original.unlink()
            removed_raw += len(raw)
            removed_entries.append(entry["original_path"])
        final = verify_all()
        return {
            "entries_archived": len(entries),
            "original_bytes_removed": removed_raw,
            "archive_bytes": final["archive_bytes"],
            "bytes_reclaimed": removed_raw - final["archive_bytes"],
            "removed_original_paths": removed_entries,
        }
    except Exception:
        # Leave verified archives in place for recovery if manifest was already committed;
        # otherwise delete only gzip files created by this invocation, never source bodies.
        if not MANIFEST.exists():
            for archive in created:
                archive.unlink(missing_ok=True)
        raise


def roundtrip_one(original_rel: str) -> dict[str, Any]:
    result = restore_one(original_rel)
    doc = load_manifest()
    entry = next(x for x in doc["entries"] if x["original_path"] == original_rel)
    original = safe_repo_path(original_rel)
    raw = original.read_bytes()
    packed = gzip.compress(raw, compresslevel=6, mtime=0)
    if len(packed) != entry["archive_size_bytes"] or sha256(packed) != entry["archive_sha256"]:
        raise RuntimeError(f"deterministic rearchive comparison failed: {original_rel}")
    # Remove only the exact restored verification copy, preserving the validated gzip.
    if sha256(original.read_bytes()) != entry["original_sha256"]:
        raise RuntimeError(f"refusing to remove changed restore exercise file: {original_rel}")
    original.unlink()
    return {"path": original_rel, "restore": result, "deterministic_rearchive_matches": True, "restored_copy_removed": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="read-only candidate/receipt validation and gzip size estimates")
    sub.add_parser("archive", help="archive only the four approved public source-body families")
    sub.add_parser("verify", help="verify every manifest mapping, archive and untouched receipt")
    restore = sub.add_parser("restore", help="restore one exact original path without overwriting different bytes")
    restore.add_argument("original_path")
    roundtrip = sub.add_parser("roundtrip", help="controlled restore/recompress/cleanup test for one path")
    roundtrip.add_argument("original_path")
    args = parser.parse_args()
    if args.command == "plan":
        entries, _staged, skipped = collect_plan()
        raw = sum(x["original_size_bytes"] for x in entries)
        packed = sum(x["archive_size_bytes"] for x in entries)
        print(json.dumps({"entries": len(entries), "original_bytes": raw, "gzip_bytes": packed, "estimated_reclaim": raw-packed, "skipped": skipped}, sort_keys=True))
    elif args.command == "archive":
        print(json.dumps(archive_all(), sort_keys=True))
    elif args.command == "verify":
        print(json.dumps(verify_all(), sort_keys=True))
    elif args.command == "restore":
        print(json.dumps(restore_one(args.original_path), sort_keys=True))
    elif args.command == "roundtrip":
        print(json.dumps(roundtrip_one(args.original_path), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
