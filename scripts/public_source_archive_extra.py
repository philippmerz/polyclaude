#!/usr/bin/env python3
"""Verified reversible archives for bounded public HTML source families.

The default ``prior36`` profile preserves the earlier 36-body archive. The
``more-html`` profile uses a separate immutable manifest for an exact set of
Oct 1–16 receipt-verified HTML captures. Each profile gets an isolated copy of
the existing archive engine; loading this module never changes the original
engine's globals.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
from types import ModuleType
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PRIOR36_MANIFEST = ROOT / "research/2026-10-17-deep-review/ARCHIVED_PUBLIC_SOURCE_BODIES_EXTRA.json"
MORE_HTML_MANIFEST = ROOT / "research/2026-10-17-deep-review/ARCHIVED_PUBLIC_SOURCE_BODIES_MORE_HTML.json"
# Backwards-compatible module constant: callers that used MANIFEST still see the prior36 manifest.
MANIFEST = PRIOR36_MANIFEST

PROFILES: dict[str, dict[str, Any]] = {
    "prior36": {
        "manifest": PRIOR36_MANIFEST,
        "scope": (
            "Only receipt-linked HTTP 200 text/html captures of argon.body, homepage.body, "
            "google_september_recap_retry1.body, and agi_homepage_retry1.body in completed "
            "checkin/periodic run folders dated Oct 1–16, 2026. Unlinked captures are "
            "excluded and left untouched; all archived captures remain individually restorable."
        ),
        "allowed_bodies": {
            "argon.body": "argon",
            "homepage.body": "homepage",
            "google_september_recap_retry1.body": "google_september_recap",
            "agi_homepage_retry1.body": "agi_homepage",
        },
    },
    "more-html": {
        "manifest": MORE_HTML_MANIFEST,
        "scope": (
            "Only receipt-linked HTTP 200 text/html captures of the approved more-html basename "
            "families in completed Oct 1–16, 2026 checkin/periodic logs. Allowed folders are "
            "sources/ and its exact new_release/ or release_check/ children. The final response "
            "host must be blog.google or agi.safe.ai. All captures remain individually restorable."
        ),
        "allowed_bodies": {
            "argon_announcement.body": "argon_announcement",
            "google_rss_new_1.body": "google_rss_new_1",
            "google_rss_new_2.body": "google_rss_new_2",
            "google_rss_new_3.body": "google_rss_new_3",
            "argon_app_availability.body": "argon_app_availability",
            "argon_developer_availability.body": "argon_developer_availability",
            "google_diamond.body": "google_diamond",
            "diamond.body": "diamond",
        },
        "allowed_final_hosts": {"blog.google", "agi.safe.ai"},
    },
}

_ENGINE_CACHE: dict[str, ModuleType] = {}


def _normalize_profile(profile: str) -> str:
    # ``extra`` was used by early callers for the existing prior36 archive.
    if profile == "extra":
        return "prior36"
    if profile not in PROFILES:
        raise ValueError(f"unknown archive profile: {profile}")
    return profile


def _more_html_approved_source_rel(value: str, allowed_bodies: dict[str, str], run_re: re.Pattern[str]) -> bool:
    """Strict lexical allowlist for only the requested source paths; reject symlinks."""
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    rel = Path(value)
    if rel.is_absolute() or rel.as_posix() != value or any(part in {"", ".", ".."} for part in rel.parts):
        return False
    parts = rel.parts
    if len(parts) == 4:
        if parts[0] != "logs" or not run_re.fullmatch(parts[1]) or parts[2] != "sources":
            return False
        basename = parts[3]
    elif len(parts) == 5:
        if parts[0] != "logs" or not run_re.fullmatch(parts[1]) or parts[2] != "sources":
            return False
        if parts[3] not in {"new_release", "release_check"}:
            return False
        basename = parts[4]
    else:
        return False
    if basename not in allowed_bodies:
        return False

    # Reject symlinks in every present component while allowing an absent source body
    # when validating a manifest entry whose content is in its adjacent gzip archive.
    current = ROOT
    for part in parts:
        current = current / part
        if current.is_symlink():
            return False
    return True


def _load_isolated_engine(profile: str) -> ModuleType:
    """Load the verified engine into a private namespace and configure that copy only."""
    profile = _normalize_profile(profile)
    config = PROFILES[profile]
    engine_path = ROOT / "scripts/public_source_archive.py"
    module_name = f"_public_source_archive_extra_engine_{profile.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, engine_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load verified archive engine: {engine_path}")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)

    engine.MANIFEST = config["manifest"]
    engine.ALLOWED_BODIES = dict(config["allowed_bodies"])
    engine.SCOPE_DESCRIPTION = config["scope"]
    engine.READER_HELPER = "scripts/public_source_archive_extra.py"

    if profile == "more-html":
        allowed = dict(config["allowed_bodies"])
        run_re = engine.RUN_RE

        def approved_source_rel(value: str) -> bool:
            return _more_html_approved_source_rel(value, allowed, run_re)

        def candidate_paths() -> list[Path]:
            logs = ROOT / "logs"
            if logs.is_symlink() or not logs.is_dir():
                return []
            found: list[Path] = []
            for run in sorted(logs.iterdir()):
                if run.is_symlink() or not run.is_dir() or not run_re.fullmatch(run.name):
                    continue
                sources = run / "sources"
                if sources.is_symlink() or not sources.is_dir():
                    continue
                folders = [sources]
                for child in ("new_release", "release_check"):
                    folder = sources / child
                    if not folder.is_symlink() and folder.is_dir():
                        folders.append(folder)
                for folder in folders:
                    for basename in allowed:
                        path = folder / basename
                        if path.is_symlink() or not path.is_file():
                            continue
                        rel = engine.rel(path)
                        if approved_source_rel(rel):
                            found.append(path)
            return sorted(found, key=lambda path: engine.rel(path))

        base_receipt_for = engine.receipt_for
        allowed_hosts = set(config["allowed_final_hosts"])

        def receipt_for(path: Path, data: bytes, family: str) -> dict[str, Any]:
            receipt = base_receipt_for(path, data, family)
            final_url = receipt.get("final_url")
            host = urlsplit(final_url).hostname if isinstance(final_url, str) else None
            if host not in allowed_hosts:
                raise engine.UnlinkedCapture(f"final response host is outside more-html allowlist: {host!r}")
            return receipt

        # These overrides exist only on this isolated module object.
        engine.approved_source_rel = approved_source_rel
        engine.candidate_paths = candidate_paths
        engine.receipt_for = receipt_for

    return engine


def _engine_for(profile: str = "prior36") -> ModuleType:
    normalized = _normalize_profile(profile)
    if normalized not in _ENGINE_CACHE:
        _ENGINE_CACHE[normalized] = _load_isolated_engine(normalized)
    return _ENGINE_CACHE[normalized]


def read_verified_path(original_rel: str, profile: str = "prior36") -> bytes:
    """Read an original capture via the selected verified archive profile."""
    return _engine_for(profile).read_verified_path(original_rel)


def verify_all(profile: str = "prior36") -> dict[str, Any]:
    """Validate every archive entry and its untouched public response receipt."""
    return _engine_for(profile).verify_all()


def restore_one(original_rel: str, profile: str = "prior36") -> dict[str, Any]:
    return _engine_for(profile).restore_one(original_rel)


def archive_all(profile: str = "prior36") -> dict[str, Any]:
    return _engine_for(profile).archive_all()


def collect_plan(profile: str = "prior36"):
    return _engine_for(profile).collect_plan()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=tuple(PROFILES), default=None, help="archive profile (default: prior36)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("plan", "read-only candidate and receipt validation"),
        ("archive", "archive approved files; originals removed only after full verification"),
        ("verify", "verify this profile's archive manifest, gzip, and source receipts"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--profile", choices=tuple(PROFILES), dest="profile_after", default=None)
    restore = sub.add_parser("restore", help="restore one exact source path without overwriting different bytes")
    restore.add_argument("original_path")
    restore.add_argument("--profile", choices=tuple(PROFILES), dest="profile_after", default=None)
    roundtrip = sub.add_parser("roundtrip", help="controlled restore/recompress/cleanup test for one path")
    roundtrip.add_argument("original_path")
    roundtrip.add_argument("--profile", choices=tuple(PROFILES), dest="profile_after", default=None)
    args = parser.parse_args()
    profile = args.profile_after or args.profile or "prior36"
    engine = _engine_for(profile)

    if args.command == "plan":
        entries, _staged, skipped = engine.collect_plan()
        raw = sum(row["original_size_bytes"] for row in entries)
        packed = sum(row["archive_size_bytes"] for row in entries)
        families: dict[str, int] = {}
        for entry in entries:
            families[entry["capture_key"]] = families.get(entry["capture_key"], 0) + 1
        print(json.dumps({
            "profile": profile,
            "manifest": str(engine.MANIFEST.relative_to(ROOT)),
            "entries": len(entries),
            "original_bytes": raw,
            "gzip_bytes": packed,
            "estimated_reclaim_bytes": raw - packed,
            "family_counts": families,
            "skipped": skipped,
        }, sort_keys=True))
    elif args.command == "archive":
        print(json.dumps(engine.archive_all(), sort_keys=True))
    elif args.command == "verify":
        print(json.dumps(engine.verify_all(), sort_keys=True))
    elif args.command == "restore":
        print(json.dumps(engine.restore_one(args.original_path), sort_keys=True))
    elif args.command == "roundtrip":
        print(json.dumps(engine.roundtrip_one(args.original_path), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
