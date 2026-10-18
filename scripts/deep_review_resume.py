#!/usr/bin/env python3
"""Emit a tiny, read-only resume packet for one frozen deep-review case."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "research/2026-10-17-deep-review"
DATA = ROOT / "data/deep_review_20261017"
RULES = ROOT / "research/2026-10-17-primary-market-review-rules.jsonl.gz"
PROGRESS = RUN / "progress.json"
CHECKPOINT = ROOT / "notes/deep_review_checkpoint.json"
REVISION_RE = re.compile(r"^revisions/[0-9]{4}_[0-9TZ]+\.(?:json|md)$")


class ResumeError(ValueError):
    """Input metadata cannot be safely or completely represented."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_file(base: Path, relative: str) -> Path:
    """Resolve an existing file under an allowlisted root without symlinks."""
    p = Path(relative)
    if p.is_absolute() or not p.parts or any(part in ("", ".", "..") for part in p.parts):
        raise ResumeError(f"unsafe scoped reference: {relative!r}")
    cur = base
    for part in p.parts:
        cur = cur / part
        if cur.is_symlink():
            raise ResumeError(f"symlink in scoped reference: {relative!r}")
    resolved = cur.resolve(strict=True)
    try:
        resolved.relative_to(base.resolve(strict=True))
    except ValueError as exc:
        raise ResumeError(f"reference escapes its scope: {relative!r}") from exc
    if not resolved.is_file():
        raise ResumeError(f"scoped reference is not a file: {relative!r}")
    return resolved


def _frozen_universe() -> dict[int, dict]:
    rows = {}
    with gzip.open(RULES, "rt", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            i = int(row["review_index"])
            if i in rows:
                raise ResumeError(f"duplicate frozen review index {i}")
            rows[i] = row
    return rows


def _load_case_progress(i: int, frozen: dict, active: set[int], base_records: list[dict], revision_rows: list[dict]) -> dict:
    candidates = [r for r in base_records if int(r.get("review_index", -1)) == i]
    if len(candidates) > 1:
        raise ResumeError(f"duplicate base evaluation record for case {i}")
    effective = candidates[0] if candidates else None
    pointer = None
    verified = []
    if effective:
        if str(effective.get("market_id", frozen["id"])) != str(frozen["id"]):
            raise ResumeError(f"base market identity mismatch for case {i}")
        if str(effective.get("condition_id", "")).lower() != str(frozen["conditionId"]).lower():
            raise ResumeError(f"base condition identity mismatch for case {i}")
        if effective.get("criteria_sha256") != frozen.get("criteria_sha256") and not effective.get("criteria_change_explained"):
            raise ResumeError(f"base criteria fingerprint mismatch for case {i}")
        report_rel = effective.get("report_path") or f"evaluations/{i:04d}.md"
        report = _safe_file(RUN, report_rel)
        report_sha = _sha256(report)
        if report_sha != effective.get("report_sha256"):
            raise ResumeError(f"base report hash mismatch for case {i}")
        pointer = {"path": f"research/2026-10-17-deep-review/{report_rel}", "sha256": report_sha}
        verified.append({"kind": "base", "sha256": report_sha})

    for row in revision_rows:
        if int(row.get("review_index", -1)) != i:
            continue
        if row.get("schema") != "deep_review_revision.v1":
            raise ResumeError(f"invalid revision schema for case {i}")
        if effective is None:
            raise ResumeError(f"revision exists without base case {i}")
        rel = row.get("revision_path", "")
        if not REVISION_RE.fullmatch(rel):
            raise ResumeError(f"unsafe revision pointer for case {i}")
        revision_path = _safe_file(RUN, rel)
        revision_sha = _sha256(revision_path)
        if revision_sha != row.get("revision_json_sha256"):
            raise ResumeError(f"revision JSON hash mismatch for case {i}")
        revision = json.loads(revision_path.read_text(encoding="utf-8"))
        if int(revision.get("review_index", -1)) != i:
            raise ResumeError(f"revision index mismatch for case {i}")
        if str(revision.get("market_id", "")) != str(frozen["id"]):
            raise ResumeError(f"revision market identity mismatch for case {i}")
        if str(revision.get("condition_id", "")).lower() != str(frozen["conditionId"]).lower():
            raise ResumeError(f"revision condition identity mismatch for case {i}")
        if revision.get("criteria_sha256") != frozen.get("criteria_sha256"):
            raise ResumeError(f"revision criteria fingerprint mismatch for case {i}")
        if row.get("prior_report_sha256") != effective.get("report_sha256"):
            raise ResumeError(f"revision predecessor mismatch for case {i}")
        if revision.get("prior_report_sha256") != effective.get("report_sha256"):
            raise ResumeError(f"revision JSON predecessor mismatch for case {i}")
        report_rel = revision.get("report_path", "")
        report = _safe_file(RUN, report_rel)
        report_sha = _sha256(report)
        if report_sha != revision.get("report_sha256") or report_sha != row.get("report_sha256"):
            raise ResumeError(f"revision report hash mismatch for case {i}")
        if revision.get("revision_reason") != row.get("reason"):
            raise ResumeError(f"revision reason mismatch for case {i}")
        effective = revision
        pointer = {"path": f"research/2026-10-17-deep-review/{report_rel}", "sha256": report_sha}
        verified.append({"kind": "revision", "json_path": f"research/2026-10-17-deep-review/{rel}",
                         "json_sha256": revision_sha, "report_sha256": report_sha,
                         "revision_utc": revision.get("evaluated_utc"),
                         "reason": revision.get("revision_reason")})

    if effective:
        status = effective["status"]
        evaluated = effective.get("evaluated_utc")
        latest_revision = verified[-1] if verified and verified[-1]["kind"] == "revision" else None
    else:
        status = "in_progress" if i in active else "pending"
        evaluated = None
        latest_revision = None
    return {"status": status, "evaluated_utc": evaluated,
            "report_pointer": pointer, "latest_revision": latest_revision,
            "verified_artifacts": verified}


def _public_pointers(i: int) -> dict | None:
    rel = f"work/{i:04d}_resume.json"
    path = DATA / rel
    if not path.exists() and not path.is_symlink():
        return None
    source = _safe_file(DATA, rel)
    raw = json.loads(source.read_text(encoding="utf-8"))
    if int(raw.get("review_index", -1)) != i:
        raise ResumeError(f"work resume case identity mismatch in {rel}")
    pointers = []
    for key in ("source_pointers", "source_paths", "draft_paths", "public_draft_paths"):
        values = raw.get(key, [])
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            raise ResumeError(f"malformed {key} in {rel}")
        for value in values:
            if not isinstance(value, str):
                raise ResumeError(f"non-string pointer in {rel}")
            if value.startswith(("https://", "http://")):
                parsed = urlparse(value)
                if not parsed.netloc or parsed.username or parsed.password:
                    raise ResumeError(f"unsafe public URL in {rel}")
                pointers.append({"url": value})
            else:
                scoped = None
                for base, prefix in ((RUN, "research/2026-10-17-deep-review"),
                                     (DATA, "data/deep_review_20261017")):
                    try:
                        target = _safe_file(base, value)
                        scoped = f"{prefix}/{target.relative_to(base.resolve())}"
                        break
                    except (FileNotFoundError, ResumeError):
                        continue
                if scoped is None:
                    raise ResumeError(f"source pointer outside scoped research/data: {value!r}")
                pointers.append({"path": scoped})
    return {"path": f"data/deep_review_20261017/{rel}",
            "sha256": _sha256(source), "pointers_total": len(pointers),
            "pointers_omitted": max(0, len(pointers) - 30),
            "public_pointers": pointers[:30]}


def build_packet(index: int | None = None, max_bytes: int = 8000) -> dict:
    if max_bytes < 1:
        raise ResumeError("--max-bytes must be a positive integer")
    progress = json.loads(PROGRESS.read_text(encoding="utf-8"))
    checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    compare_fields = (
        "updated_utc", "universe", "completed_in_depth_reviews", "completed_valuations",
        "blocked_after_in_depth_review", "factual_exclusions", "pending", "base_records",
        "revisions_written", "active_indices", "next_pending_indices",
    )
    mismatched_fields = [k for k in compare_fields if progress.get(k) != checkpoint.get(k)]
    if mismatched_fields:
        raise ResumeError("checkpoint/progress disagreement: " + ", ".join(mismatched_fields))
    frozen_rows = _frozen_universe()
    active = [int(x) for x in progress.get("active_indices", [])]
    pending = [int(x) for x in progress.get("next_pending_indices", [])]
    if index is None:
        index = next(iter(active), None)
        if index is None:
            index = next(iter(pending), None)
    if index is None or index not in frozen_rows:
        raise ResumeError(f"selected review index is not in frozen universe: {index}")
    frozen = frozen_rows[index]
    base_rows = [json.loads(line) for line in (RUN / "evaluations.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    revision_rows = [json.loads(line) for line in (RUN / "revisions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    effective = _load_case_progress(index, frozen, set(active), base_rows, revision_rows)
    hashes = {}
    files = {
        "checkpoint": CHECKPOINT,
        "progress": PROGRESS,
        "frozen_rules_gzip": RULES,
        "base_ledger": RUN / "evaluations.jsonl",
        "revision_ledger": RUN / "revisions.jsonl",
        "queue_index": RUN / "index.csv",
    }
    for name, path in files.items():
        hashes[name] = {"sha256": _sha256(path), "path": str(path.relative_to(ROOT))}
    declared = {
        "frozen_rules_gzip": checkpoint.get("original_rules_sha256"),
        "base_ledger": checkpoint.get("ledger_sha256"),
        "revision_ledger": checkpoint.get("revisions_sha256"),
    }
    for name, value in declared.items():
        if not isinstance(value, str):
            raise ResumeError(f"checkpoint is missing declared SHA-256 for {name}")
        hashes[name]["checkpoint_declared_sha256"] = value
        hashes[name]["matches_checkpoint"] = value == hashes[name]["sha256"]
        if not hashes[name]["matches_checkpoint"]:
            raise ResumeError(f"checkpoint declared SHA-256 mismatch for {name}")
    packet = {
        "schema": "polyclaude.deep_review_resume.v1",
        "checkpoint": {k: progress.get(k) for k in (
            "updated_utc", "universe", "completed_in_depth_reviews", "completed_valuations",
            "blocked_after_in_depth_review", "factual_exclusions", "pending", "base_records",
            "revisions_written", "active_indices", "next_pending_indices")},
        "checkpoint_hashes": hashes,
        "selected_review_index": index,
        "case": {k: frozen.get(k) for k in (
            "review_index", "id", "conditionId", "question", "slug", "description",
            "resolutionSource", "outcomes", "clobTokenIds", "endDate", "criteria_sha256")},
        "effective_case": effective,
        "optional_work_pointers": _public_pointers(index),
    }
    packet["case"]["outcomes"] = json.loads(frozen["outcomes"])
    packet["case"]["clobTokenIds"] = json.loads(frozen["clobTokenIds"])
    packet["packet_bytes"] = 0
    rendered = ""
    for _ in range(4):
        rendered = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
        size = len(rendered.encode("utf-8"))
        if packet["packet_bytes"] == size:
            break
        packet["packet_bytes"] = size
    if size > max_bytes:
        raise ResumeError(f"resume packet is {size} UTF-8 bytes, exceeding --max-bytes={max_bytes}; no fields were truncated")
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=int, help="exact frozen review index; defaults to active then next pending")
    parser.add_argument("--max-bytes", type=int, default=8000, help="hard UTF-8 packet limit (default: 8000)")
    args = parser.parse_args(argv)
    try:
        packet = build_packet(args.index, args.max_bytes)
    except (ResumeError, OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"deep_review_resume: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(packet, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
