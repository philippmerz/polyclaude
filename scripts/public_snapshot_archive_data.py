#!/usr/bin/env python3
"""Reversible archive for one frozen set of old public Gamma thin-tail snapshots.

Only the exact 48 pre-2026-10-13 paths below are accepted. The shared
``data/snapshots/shortlist_latest.json`` symlink remains mutable and untouched;
every operation fails if it points at a selected archive target. Historical
direct reads of an archived path require ``restore``; the deep-review ledger
adapter can verify/read it without restoring.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "scripts/public_snapshot_archive.py"
MANIFEST = ROOT / "research/2026-10-17-deep-review/ARCHIVED_PUBLIC_DATA_THIN_TAIL_SNAPSHOTS.json"
LATEST_REL = "data/snapshots/shortlist_latest.json"
SCHEMA = "public_gamma_data_thin_tail_snapshot_archive.v1"
SOURCE_URL = "https://gamma-api.polymarket.com"
PRODUCER = "scripts/discover_markets.py"
SIDECAR_SCHEMA_VERSIONS = (1, 2)

# Exact inventory from the read-only 2026-10-20 audit. Never broaden by glob.
ALLOWED_PATHS = (
    "data/snapshots/shortlist_20260923T105728852070Z_thin_tail.json",
    "data/snapshots/shortlist_20260923T110117034313Z_thin_tail.json",
    "data/snapshots/shortlist_20260923T110136567953Z_thin_tail.json",
    "data/snapshots/shortlist_20260923T140135532011Z_thin_tail.json",
    "data/snapshots/shortlist_20260924T020129400393Z_thin_tail.json",
    "data/snapshots/shortlist_20260924T140116243446Z_thin_tail.json",
    "data/snapshots/shortlist_20260925T020102651964Z_thin_tail.json",
    "data/snapshots/shortlist_20260925T140120976390Z_thin_tail.json",
    "data/snapshots/shortlist_20260926T020203116994Z_thin_tail.json",
    "data/snapshots/shortlist_20260926T140135948456Z_thin_tail.json",
    "data/snapshots/shortlist_20260927T020305481918Z_thin_tail.json",
    "data/snapshots/shortlist_20260927T140209816196Z_thin_tail.json",
    "data/snapshots/shortlist_20260927T221739226728Z_thin_tail.json",
    "data/snapshots/shortlist_20260928T020320265983Z_thin_tail.json",
    "data/snapshots/shortlist_20260928T140302797826Z_thin_tail.json",
    "data/snapshots/shortlist_20260929T020135005043Z_thin_tail.json",
    "data/snapshots/shortlist_20260929T140337559002Z_thin_tail.json",
    "data/snapshots/shortlist_20260930T020326441759Z_thin_tail.json",
    "data/snapshots/shortlist_20260930T020334020691Z_thin_tail.json",
    "data/snapshots/shortlist_20260930T140522210136Z_thin_tail.json",
    "data/snapshots/shortlist_20260930T140957646529Z_thin_tail.json",
    "data/snapshots/shortlist_20260930T211047522536Z_thin_tail.json",
    "data/snapshots/shortlist_20261001T020700758275Z_thin_tail.json",
    "data/snapshots/shortlist_20261001T140254592725Z_thin_tail.json",
    "data/snapshots/shortlist_20261002T020257361091Z_thin_tail.json",
    "data/snapshots/shortlist_20261002T140252393699Z_thin_tail.json",
    "data/snapshots/shortlist_20261003T020313895324Z_thin_tail.json",
    "data/snapshots/shortlist_20261003T140309355259Z_thin_tail.json",
    "data/snapshots/shortlist_20261004T020314193942Z_thin_tail.json",
    "data/snapshots/shortlist_20261004T140213739800Z_thin_tail.json",
    "data/snapshots/shortlist_20261005T020423531903Z_thin_tail.json",
    "data/snapshots/shortlist_20261005T140240754636Z_thin_tail.json",
    "data/snapshots/shortlist_20261006T020227154676Z_thin_tail.json",
    "data/snapshots/shortlist_20261006T140217774948Z_thin_tail.json",
    "data/snapshots/shortlist_20261007T020222793669Z_thin_tail.json",
    "data/snapshots/shortlist_20261007T140300544934Z_thin_tail.json",
    "data/snapshots/shortlist_20261008T020306204930Z_thin_tail.json",
    "data/snapshots/shortlist_20261008T020450557017Z_thin_tail.json",
    "data/snapshots/shortlist_20261008T140412847120Z_thin_tail.json",
    "data/snapshots/shortlist_20261009T020417851322Z_thin_tail.json",
    "data/snapshots/shortlist_20261009T140432824231Z_thin_tail.json",
    "data/snapshots/shortlist_20261010T020317736681Z_thin_tail.json",
    "data/snapshots/shortlist_20261010T140406916840Z_thin_tail.json",
    "data/snapshots/shortlist_20261011T020301694410Z_thin_tail.json",
    "data/snapshots/shortlist_20261011T140341700270Z_thin_tail.json",
    "data/snapshots/shortlist_20261012T020233722262Z_thin_tail.json",
    "data/snapshots/shortlist_20261012T140330074895Z_thin_tail.json",
    "data/snapshots/shortlist_20261012T141402452441Z_thin_tail.json",
)

_RUN_RE = re.compile(r"^shortlist_(202609\d\d|202610(?:0[1-9]|1[0-2]))T\d{12}Z_thin_tail\.json$")
_ENGINE_CACHE: ModuleType | None = None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _assert_inventory(paths: tuple[str, ...] = ALLOWED_PATHS) -> None:
    if len(paths) != 48 or len(set(paths)) != 48:
        raise ValueError("frozen data snapshot inventory must contain 48 unique paths")
    for value in paths:
        p = Path(value)
        if (p.is_absolute() or p.as_posix() != value or p.parts[:2] != ("data", "snapshots")
                or not _RUN_RE.fullmatch(p.name) or "latest" in p.name):
            raise ValueError(f"path is outside frozen pre-Oct13 thin-tail inventory: {value}")


def _load_engine(*, root: Path = ROOT, allowed_paths: tuple[str, ...] = ALLOWED_PATHS,
                 manifest: Path | None = None, testing: bool = False) -> ModuleType:
    """Load the established engine in an isolated namespace with this exact profile."""
    if testing:
        if not allowed_paths or len(set(allowed_paths)) != len(allowed_paths):
            raise ValueError("test profile requires a nonempty unique allowlist")
    else:
        _assert_inventory(allowed_paths)
    spec = importlib.util.spec_from_file_location("_public_snapshot_archive_data_engine", ENGINE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load public snapshot archive engine")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    engine.ROOT = root.resolve()
    engine.ALLOWED_PATHS = tuple(allowed_paths)
    engine.MANIFEST = manifest or (root / MANIFEST.relative_to(ROOT))
    engine.SCHEMA = SCHEMA
    engine.SOURCE_URL = SOURCE_URL
    engine.PRODUCER = PRODUCER

    def assert_allowlisted(value: str) -> None:
        if value not in engine.ALLOWED_PATHS:
            raise ValueError(f"path is outside frozen data snapshot inventory: {value}")

    def check_latest_alias() -> dict[str, Any]:
        alias_rel = Path(LATEST_REL)
        engine._checked_path(alias_rel.parent.as_posix(), must_exist=True)
        alias_path = engine.ROOT.joinpath(*alias_rel.parts)
        if not os.path.lexists(alias_path):
            return {"path": LATEST_REL, "mutable": True, "present_at_check": False}
        st = alias_path.lstat()
        if not stat.S_ISLNK(st.st_mode):
            raise ValueError(f"mutable latest path is no longer a symlink: {LATEST_REL}")
        target = os.readlink(alias_path)
        target_path = Path(target)
        if target_path.is_absolute() or target_path.name != target or target in {Path(x).name for x in engine.ALLOWED_PATHS}:
            raise ValueError(f"shortlist_latest points at an unsafe or archived path: {target!r}")
        current = alias_path.parent / target
        if not current.is_file() or current.is_symlink():
            raise ValueError("shortlist_latest target is missing, nonregular, or a symlink")
        return {"path": LATEST_REL, "mutable": True, "present_at_check": True}

    def alias_snapshot(_original_rel: str) -> dict[str, Any]:
        return check_latest_alias()

    def verify_alias(expected: dict[str, Any]) -> None:
        if expected.get("path") != LATEST_REL or expected.get("mutable") is not True:
            raise ValueError("archive entry lacks mutable latest-alias guard")
        # Existence and target are deliberately not frozen: the discovery writer
        # may atomically replace this alias. Its target must never be archived.
        check_latest_alias()

    base_sidecar = engine._sidecar

    def verified_sidecar(original: Path, raw: bytes, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        receipt = base_sidecar(original, raw, rows)
        if receipt is None:
            raise ValueError(f"required metadata sidecar missing: {original.name}")
        metadata = json.loads((original.with_name(original.stem + ".meta.json")).read_text(encoding="utf-8"))
        version = metadata.get("schema_version")
        if version not in SIDECAR_SCHEMA_VERSIONS:
            raise ValueError(f"unsupported snapshot sidecar schema {version!r}: {original.name}")
        if metadata.get("scan_kind") != "thin_tail" or metadata.get("criteria_fingerprint") != "sha256:canonical-json-exact-v1":
            raise ValueError(f"snapshot sidecar semantics mismatch: {original.name}")
        if not isinstance(metadata.get("params"), dict):
            raise ValueError(f"snapshot sidecar params are not an object: {original.name}")
        policy = metadata.get("selection_policy")
        coverage = metadata.get("coverage")
        if version == 1 and (policy is not None or coverage is not None):
            raise ValueError(f"unexpected v2 optional fields in v1 sidecar: {original.name}")
        if version == 2 and policy not in (None, "filter-before-top-v1"):
            raise ValueError(f"unsupported selection_policy in sidecar: {original.name}")
        if version == 2 and coverage is not None and not isinstance(coverage, dict):
            raise ValueError(f"unsupported coverage field in sidecar: {original.name}")
        sidecar_path = original.with_name(original.stem + ".meta.json")
        sidecar_bytes, sidecar_sig = engine._read_stable(sidecar_path)
        if (len(sidecar_bytes) != receipt["size_bytes"] or _sha256(sidecar_bytes) != receipt["sha256"]
                or sidecar_sig["mtime_ns"] != receipt["mtime_ns"]
                or oct(sidecar_sig["mode"]) != receipt["mode_octal"]):
            raise RuntimeError(f"metadata sidecar changed while validating: {original.name}")
        return receipt

    engine._assert_allowlisted = assert_allowlisted
    engine._alias_snapshot = alias_snapshot
    engine._verify_alias = verify_alias
    engine._sidecar = verified_sidecar
    base_manifest_doc = engine._manifest_doc

    def manifest_doc(entries: list[dict[str, Any]], producer_source: dict[str, Any]) -> dict[str, Any]:
        doc = base_manifest_doc(entries, producer_source)
        doc["scope"] = "Exact frozen 48 pre-2026-10-13 data/snapshots thin_tail JSON paths in scripts/public_snapshot_archive_data.py."
        doc["reader"] = "scripts/public_snapshot_archive_data.py read_verified_path verifies original or gzip by hash and sidecar; restore recreates original bytes/mode/mtime."
        doc["alias_handling"] = "Mutable data/snapshots/shortlist_latest.json is never changed or frozen; every operation checks it is not a selected archive target. Historical direct reads require restore; ledger Markdown links use the verified reader."
        doc["source_sidecar_policy"] = "Exact sidecar bytes/hash/size/mode/mtime retained. Accept observed schema_version 1/2 only; version-specific optional fields are not synthesized."
        doc["frozen_allowlist_sha256"] = _sha256(("\n".join(engine.ALLOWED_PATHS) + "\n").encode())
        return doc

    engine._manifest_doc = manifest_doc
    # Check the mutable pointer during profile construction, before any plan or write.
    check_latest_alias()
    return engine


def _engine() -> ModuleType:
    global _ENGINE_CACHE
    if _ENGINE_CACHE is None:
        _ENGINE_CACHE = _load_engine()
    return _ENGINE_CACHE


def load_manifest() -> dict[str, Any]:
    """Load the immutable manifest and check the mutable latest-pointer guard."""
    return _engine()._load_manifest()


def verify_all() -> dict[str, int]:
    return _engine().verify_all()


def read_verified_path(original_path: str) -> bytes:
    """Read one exact allowlisted historical path from disk or verified gzip."""
    return _engine().read_verified_path(original_path)


def restore_one(original_path: str) -> dict[str, Any]:
    return _engine().restore_one(original_path)


def plan() -> dict[str, Any]:
    engine = _engine()
    entries = engine.collect_plan()
    raw = sum(e["original_size_bytes"] for e in entries)
    packed = sum(e["gzip_size_bytes"] for e in entries)
    versions: dict[int, int] = {}
    for entry in entries:
        meta = json.loads((engine.ROOT / entry["existing_meta_sidecar"]["path"]).read_text())
        version = meta["schema_version"]
        versions[version] = versions.get(version, 0) + 1
    statvfs = os.statvfs(engine.ROOT)
    available = statvfs.f_bavail * statvfs.f_frsize
    return {
        "observed_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "profile": SCHEMA,
        "entries": len(entries),
        "sidecar_schema_counts": versions,
        "original_bytes": raw,
        "gzip_bytes": packed,
        "estimated_reclaim_bytes": raw - packed,
        "peak_added_bytes_before_unlink": packed,
        "filesystem_available_bytes": available,
        "peak_fits_available": packed < available,
        "latest_alias": check_latest_alias_for_plan(engine),
        "manifest": engine.MANIFEST.relative_to(engine.ROOT).as_posix(),
        "paths": [{"path": e["original_path"], "original_bytes": e["original_size_bytes"],
                   "gzip_bytes": e["gzip_size_bytes"], "sha256": e["original_sha256"]}
                  for e in entries],
    }


def check_latest_alias_for_plan(engine: ModuleType) -> dict[str, Any]:
    # Use the configured guard without exposing or persisting the mutable target.
    return engine._alias_snapshot(ALLOWED_PATHS[0])


def archive_all() -> dict[str, Any]:
    return _engine().archive_all()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="read-only exact inventory/schema/hash/gzip check")
    archive = sub.add_parser("archive", help="archive exact frozen set; originals unlinked only after verification")
    archive.add_argument("--confirm-unlink", action="store_true", help="required explicit acknowledgement")
    sub.add_parser("verify", help="verify manifest, archives/originals, sidecars and latest-pointer exclusion")
    restore = sub.add_parser("restore", help="restore one exact original without overwriting changed files")
    restore.add_argument("original_path")
    args = parser.parse_args()
    if args.command == "plan":
        print(json.dumps(plan(), sort_keys=True))
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
