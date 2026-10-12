#!/usr/bin/env python3
"""Build a bounded offline handoff packet from whitelisted public documents."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

HANDOFF = "notes/current_context.md"
PUBLIC_DOCS = {
    "MANDATE.md", "README.md", "docs/README.md", "scripts/README.md",
    "strategy/00_philosophy.md", "strategy/01_lessons.md",
    "strategy/02_operations.md", "strategy/03_opportunity_method.md",
    "strategy/archive/01_lessons_2026-10-12.md",
    "notes/backlog.md", "notes/longterm_watchlist.md",
    "notes/primary_sources.md", "notes/resting_orders.md", "notes/journal.md",
}
QUERY_DOCS = (
    "strategy/00_philosophy.md", "strategy/01_lessons.md",
    "strategy/02_operations.md", "strategy/03_opportunity_method.md",
    "strategy/archive/01_lessons_2026-10-12.md",
)
SCOPES = {
    "portfolio": [
        ("MANDATE.md", "Mandate and legal/horizon boundaries."),
        ("strategy/00_philosophy.md", "Current objective, risk framework, and portfolio context."),
        ("strategy/01_lessons.md", "Read first for hard-won execution and evidence lessons."),
        ("strategy/02_operations.md", "Operational procedures and execution controls."),
        ("README.md", "Dashboard is dated context; use live tools for current state."),
    ],
    "research": [
        ("MANDATE.md", "Mandate and research boundaries."),
        ("strategy/00_philosophy.md", "Current objective and portfolio context."),
        ("strategy/01_lessons.md", "Read first for evidence and calibration lessons."),
        ("strategy/03_opportunity_method.md", "Discovery, evaluation, and review method."),
        ("notes/primary_sources.md", "Source registry; verify current facts independently."),
        ("notes/longterm_watchlist.md", "Current on-chain candidate routing, not a buy list."),
    ],
    "engineering": [
        ("MANDATE.md", "Project scope and boundaries."),
        ("strategy/01_lessons.md", "Read first for failure classes and test expectations."),
        ("strategy/02_operations.md", "Secrets, wallets, operations, and side-effect controls."),
        ("strategy/03_opportunity_method.md", "Scanner/evaluation boundaries when relevant."),
        ("scripts/README.md", "Tool call paths and current execution constraints."),
    ],
    "operations": [
        ("MANDATE.md", "Mandate and legal boundaries."),
        ("strategy/01_lessons.md", "Read first for operational failure lessons."),
        ("strategy/02_operations.md", "Canonical operations procedures."),
        ("scripts/README.md", "Tool catalog and operational call paths."),
        ("README.md", "Dated public dashboard; not live state."),
        ("notes/backlog.md", "Current bounded follow-ups and dated triggers."),
    ],
}


class PacketError(ValueError):
    """The essential packet cannot be represented safely within its contract."""


def _require_tracked(root: Path, relative: str) -> None:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
                            capture_output=True, text=True, check=False)
    if result.returncode != 0 or result.stdout.strip() != relative:
        raise PacketError(f"document is not tracked by git: {relative}")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _utc(value: str, name: str) -> dt.datetime:
    if not isinstance(value, str):
        raise PacketError(f"{name} must be an ISO-8601 timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PacketError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise PacketError(f"{name} must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def _doc_path(root: Path, relative: str) -> Path:
    if relative not in PUBLIC_DOCS and relative != HANDOFF:
        raise PacketError(f"document is outside the public allowlist: {relative}")
    base = root.resolve()
    path = root / relative
    cursor = root
    for part in relative.split("/"):
        cursor = cursor / part
        if cursor.is_symlink():
            raise PacketError(f"document path contains a symlink: {relative}")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise PacketError(f"document escapes repository root: {relative}") from exc
    if path.is_symlink() or not resolved.is_file():
        raise PacketError(f"document is not a regular allowlisted file: {relative}")
    _require_tracked(root, relative)
    return resolved


def _file_metadata(root: Path, relative: str) -> dict[str, Any]:
    path = _doc_path(root, relative)
    raw = path.read_bytes()
    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).isoformat()
    return {"path": relative, "sha256": _sha(raw), "mtime_utc": mtime,
            "bytes": len(raw), "text": raw.decode("utf-8")}


def _front_matter(text: str) -> tuple[dict[str, str], dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise PacketError("current_context.md needs YAML-style front matter")
    try:
        stop = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise PacketError("unterminated handoff front matter") from exc
    fields: dict[str, str] = {}
    hashes: dict[str, str] = {}
    allowed_fields = {"reviewed_at", "valid_until", "source_hashes"}
    seen_fields: set[str] = set()
    in_hashes = False
    for line in lines[1:stop]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^\s{2}([^:]+):\s*['\"]?([0-9a-f]{64})['\"]?\s*$", line)
        if in_hashes and match:
            source = match.group(1).strip()
            if source in hashes:
                raise PacketError(f"duplicate source hash path: {source}")
            hashes[source] = match.group(2)
            continue
        match = re.match(r"^([a-z_]+):\s*(.*?)\s*$", line)
        if not match:
            raise PacketError(f"unsupported handoff front matter line: {line[:80]}")
        key, value = match.groups()
        if key not in allowed_fields:
            raise PacketError(f"unknown handoff front matter field: {key}")
        if key in seen_fields:
            raise PacketError(f"duplicate handoff front matter field: {key}")
        seen_fields.add(key)
        in_hashes = key == "source_hashes"
        if key == "source_hashes" and value:
            raise PacketError("source_hashes must be a nested mapping")
        if key != "source_hashes":
            fields[key] = value.strip().strip("\"'")
    if "reviewed_at" not in fields or "valid_until" not in fields:
        raise PacketError("handoff requires reviewed_at and valid_until")
    if "source_hashes" not in seen_fields or not hashes:
        raise PacketError("handoff source_hashes must contain at least one source")
    return fields, hashes, "\n".join(lines[stop + 1:]).strip()


def _handoff(root: Path, now: dt.datetime) -> dict[str, Any]:
    try:
        record = _file_metadata(root, HANDOFF)
    except (FileNotFoundError, PacketError) as exc:
        return {"path": HANDOFF, "status": "missing_or_invalid", "error": str(exc),
                "body": "", "source_hashes": {}}
    try:
        fields, hashes, body = _front_matter(record["text"])
        reviewed = _utc(fields.get("reviewed_at"), "reviewed_at")
        valid_until = _utc(fields.get("valid_until"), "valid_until")
        mismatches = []
        for relative, expected in hashes.items():
            if relative not in PUBLIC_DOCS:
                mismatches.append({"path": relative, "reason": "source_not_allowlisted"})
                continue
            try:
                actual = _file_metadata(root, relative)["sha256"]
            except (OSError, PacketError):
                mismatches.append({"path": relative, "reason": "source_missing_or_unreadable"})
                continue
            if actual != expected:
                mismatches.append({"path": relative, "reason": "source_hash_mismatch",
                                   "expected": expected, "actual": actual})
        if valid_until <= reviewed:
            freshness = "invalid_date_range"
        elif now < reviewed:
            freshness = "not_yet_reviewed"
        elif now >= valid_until:
            freshness = "stale"
        else:
            freshness = "within_declared_validity"
        status = "invalid" if mismatches or freshness == "invalid_date_range" else freshness
        return {"path": HANDOFF, "sha256": record["sha256"], "mtime_utc": record["mtime_utc"],
                "bytes": record["bytes"], "reviewed_at": reviewed.isoformat(),
                "valid_until": valid_until.isoformat(), "freshness_status": freshness,
                "status": status, "source_hashes": hashes, "source_mismatches": mismatches,
                "body": "" if status in {"invalid", "not_yet_reviewed"} else body}
    except PacketError as exc:
        return {"path": HANDOFF, "sha256": record["sha256"], "mtime_utc": record["mtime_utc"],
                "bytes": record["bytes"], "status": "invalid", "freshness_status": "invalid",
                "source_hashes": {}, "source_mismatches": [], "error": str(exc), "body": ""}


def _section_slug(title: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return value or "section"


def _matching_sections(root: Path, query: str | None) -> list[dict[str, Any]]:
    if not query:
        return []
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not terms:
        return []
    found: list[dict[str, Any]] = []
    for relative in QUERY_DOCS:
        metadata = _file_metadata(root, relative)
        text = metadata["text"]
        lines = text.splitlines()
        headings = [(i, len(m.group(1)), m.group(2).strip())
                    for i, line in enumerate(lines)
                    if (m := re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line))]
        for hidx, (start, level, title) in enumerate(headings):
            words = set(re.findall(r"[a-z0-9]+", title.lower()))
            if not terms.issubset(words):
                continue
            end = len(lines)
            for next_start, next_level, _ in headings[hidx + 1:]:
                if next_level <= level:
                    end = next_start
                    break
            section = "\n".join(lines[start:end]).strip()
            found.append({"id": f"{relative}#{_section_slug(title)}", "path": relative,
                          "title": title, "text": section,
                          "historical": relative.startswith("strategy/archive/"),
                          "source_fullfile_sha256": metadata["sha256"],
                          "section_sha256": _sha(section.encode("utf-8")),
                          "start_line": start + 1, "end_line": end})
    return found


def _render(packet: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
    out = [f"# Context packet: {packet['scope']}", "", f"Status: {packet['handoff']['status']}",
           f"Handoff reviewed {packet['handoff'].get('reviewed_at', 'unknown')}; valid until {packet['handoff'].get('valid_until', 'unknown')}",
           f"Handoff source SHA-256 `{packet['handoff'].get('sha256', 'unavailable')}`; mtime {packet['handoff'].get('mtime_utc', 'unknown')}",
           "", "Current account/quote snapshot: not loaded; handoff is not live state.",
           "Execution ready: false", "", "## Dated handoff", "",
           packet["handoff"].get("body", "(handoff unavailable)") or "(empty handoff)", "",
           "## Required references", ""]
    if packet["handoff"]["status"] != "within_declared_validity":
        out.extend(["**Handoff is stale, future, missing or invalid; do not treat it as current state.**", ""])
    if packet["handoff"].get("source_mismatches"):
        out.append("Handoff source mismatches:")
        out.extend([f"- `{x['path']}`: {x['reason']}" for x in packet["handoff"]["source_mismatches"]])
        out.append("")
    if packet["query_status"] == "no_exact_heading_matches":
        out.extend(["Query had no exact heading/title word matches.", ""])
    for ref in packet["references"]:
        out.extend([f"- `{ref['path']}` — {ref['required_read']} (SHA-256 `{ref['sha256']}`)"])
    out.extend(["", "## Optional matched sections", ""])
    for section in packet["sections"]:
        out.extend([f"### {section['id']}", ""])
        if section["historical"]:
            out.extend(["**Historical archive excerpt; not current policy.**",
                        f"Source SHA-256 `{section['source_fullfile_sha256']}`; section SHA-256 `{section['section_sha256']}`; lines {section['start_line']}–{section['end_line']}.", ""])
        out.extend([section["text"], ""])
    if packet["omitted_section_ids"]:
        out.extend(["Omitted complete sections: " + ", ".join(packet["omitted_section_ids"]), ""])
    out.extend(["## Primary-read requirement", "", packet["mandatory_primary_read_note"], ""])
    out.extend(["## Exclusions", "", ", ".join(packet["exclusions"]), "",
                packet["limitations"], "", "Full history was not loaded."])
    if packet["public_history_sections_included"]:
        out.append("Historical public excerpts included: " + ", ".join(packet["public_history_sections_included"]))
    else:
        out.append("History was not loaded.")
    out.append("")
    return "\n".join(out)


def build_packet(root: str | Path, scope: str, *, now: str | None = None,
                 max_bytes: int = 12000, query: str | None = None,
                 fmt: str = "json") -> str:
    if scope not in SCOPES:
        raise PacketError(f"unknown scope: {scope}")
    if fmt not in ("json", "markdown"):
        raise PacketError("format must be json or markdown")
    if max_bytes < 256:
        raise PacketError("max_bytes must be at least 256")
    root = Path(root).resolve(strict=True)
    instant = _utc(now, "now") if now else dt.datetime.now(dt.timezone.utc)
    handoff = _handoff(root, instant)
    references = []
    for relative, note in SCOPES[scope]:
        item = _file_metadata(root, relative)
        references.append({"path": relative, "title": relative.rsplit("/", 1)[-1],
                           "required_read": note, "sha256": item["sha256"],
                           "mtime_utc": item["mtime_utc"]})
    matched_all = _matching_sections(root, query)
    matched = matched_all[:3]
    packet: dict[str, Any] = {
        "schema_version": 1, "scope": scope, "created_at": instant.isoformat(),
        "packet_status": ("invalid" if handoff["status"] in {"invalid", "missing_or_invalid"} else
                          "stale_handoff" if handoff["status"] == "stale" else
                          handoff["status"]),
        "handoff": handoff, "references": references, "query": query,
        "sections": matched, "omitted_section_ids": [x["id"] for x in matched_all[3:]],
        "query_status": "not_requested" if query is None else ("matches_found" if matched_all else "no_exact_heading_matches"),
        "exclusions": ["untracked documents", "non-allowlisted paths", "private histories/inboxes",
                       "credentials/secrets", "runtime account state", "live quotes", "model calls"],
        "history_unloaded": not any(x["historical"] for x in matched),
        "full_history_not_in_packet": True,
        "public_history_sections_included": [x["id"] for x in matched if x["historical"]],
        "snapshot_not_live": True,
        "current_state_loaded": False,
        "mandatory_primary_reads": ["MANDATE.md", "README.md", "strategy/00_philosophy.md",
                                    "strategy/01_lessons.md", "strategy/02_operations.md"],
        "mandatory_primary_read_note": "For consequential work, the primary agent must read MANDATE.md, README.md, strategy/00_philosophy.md, strategy/01_lessons.md, and strategy/02_operations.md. This packet is task orientation, not authorization or a replacement for required reads, live checks, or execution gates.",
        "limitations": "Handoff freshness is its declared editorial validity only; no probability, quote, account-state, liquidity, or execution freshness is inferred.",
        "execution_ready": False,
    }
    packet["packet_bytes"] = 0
    def encoded_packet() -> bytes:
        for _ in range(5):
            current = _render(packet, fmt).encode("utf-8")
            if packet["packet_bytes"] == len(current):
                return current
            packet["packet_bytes"] = len(current)
        return _render(packet, fmt).encode("utf-8")
    encoded = encoded_packet()
    # Drop optional complete sections from the end; never cut section or handoff text.
    while len(encoded) > max_bytes and packet["sections"]:
        omitted = packet["sections"].pop()
        packet["omitted_section_ids"].append(omitted["id"])
        packet["history_unloaded"] = not any(x["historical"] for x in packet["sections"])
        packet["public_history_sections_included"] = [x["id"] for x in packet["sections"] if x["historical"]]
        encoded = encoded_packet()
    if len(encoded) > max_bytes:
        raise PacketError(f"essential packet requires {len(encoded)} UTF-8 bytes; budget is {max_bytes}")
    return encoded.decode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--scope", choices=sorted(SCOPES), required=True)
    parser.add_argument("--max-bytes", type=int, default=12000)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--query")
    parser.add_argument("--now", help="ISO-8601 timestamp for deterministic freshness checks")
    args = parser.parse_args(argv)
    try:
        output = build_packet(args.root, args.scope, now=args.now, max_bytes=args.max_bytes,
                              query=args.query, fmt=args.format)
        sys.stdout.write(output)
        return 0
    except (OSError, PacketError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
