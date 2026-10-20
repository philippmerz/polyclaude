#!/usr/bin/env python3
"""Persist primary evaluations and dated append-only revisions. No network/trading."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "research/2026-10-17-deep-review"
RULES = ROOT / "research/2026-10-17-primary-market-review-rules.jsonl.gz"
POINTER = ROOT / "notes/deep_review_checkpoint.json"
STATES = {"valued", "blocked_after_review", "excluded_factual"}
REVISION_SCHEMA = "deep_review_revision.v1"
_MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\((.*?)\)", re.DOTALL)


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def dump(path, value):
    atomic(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def universe():
    with gzip.open(RULES, "rt", encoding="utf-8") as f:
        return {int(x["review_index"]): x for x in map(json.loads, f)}


def _validate_economics_forecast_consistency(x, frozen):
    """Check standard side probabilities only for new record/revision writes."""
    economics = x.get("economics")
    sides = economics.get("sides") if isinstance(economics, dict) else None
    if not isinstance(sides, dict):
        return
    if not any(isinstance(side, dict) and "probability" in side for side in sides.values()):
        return  # Preserve older compact economics records.
    labels = frozen.get("outcomes", ["Yes", "No"])
    labels = json.loads(labels) if isinstance(labels, str) else labels
    assert (isinstance(labels, list) and len(labels) == 2
            and len(set(labels)) == 2 and set(sides) == set(labels)), "economic outcomes must match both frozen labels"
    reference = economics.get("probability_reference_outcome")
    if reference is None:
        assert set(labels) == {"Yes", "No"}, "named economic outcomes require an explicit probability reference"
        reference = "Yes"
    assert isinstance(reference, str) and reference in labels, "economic probability reference must match a frozen label"
    forecast_reference = x["forecast"].get("probability_reference_outcome")
    if forecast_reference is not None or reference != "Yes" or set(labels) != {"Yes", "No"}:
        assert forecast_reference == reference, "economic probability reference does not match forecast"
    other = next(label for label in labels if label != reference)
    yes = sides.get(reference)
    no = sides.get(other)
    yes = yes if isinstance(yes, dict) else {}
    no = no if isinstance(no, dict) else {}
    assert "probability" in yes and "probability" in no, "both economic side probabilities required"
    forecast = x["forecast"]
    p_yes = forecast["p_yes"]

    def checked_probability(value, label):
        assert (isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(value) and 0 <= value <= 1), f"invalid {label} probability"
        return float(value)

    yes_probability = checked_probability(yes["probability"], "economic Yes")
    no_probability = checked_probability(no["probability"], "economic No")
    assert abs(yes_probability - p_yes) <= 1e-10, "economic Yes probability does not match forecast"
    assert abs(no_probability - (1 - p_yes)) <= 1e-10, "economic No probability does not complement forecast"

    has_stress = ("selected_stress_probability" in yes
                  or "selected_stress_probability" in no)
    reserve = economics.get("actual_entry_reserve_pp")
    if reserve is None:
        reserve = forecast.get("actual_entry_reserve_pp")
    if has_stress and reserve is not None:
        assert (isinstance(reserve, (int, float)) and not isinstance(reserve, bool)
                and math.isfinite(reserve) and 0 <= reserve <= 100), "invalid actual entry reserve in percentage points"
        assert ("selected_stress_probability" in yes
                and "selected_stress_probability" in no), "both economic side stress probabilities required"
        reserve_fraction = float(reserve) / 100.0
        expected_yes = max(0.0, p_yes - reserve_fraction)
        expected_no = max(0.0, (1 - p_yes) - reserve_fraction)
        actual_yes = checked_probability(yes["selected_stress_probability"], "economic Yes stress")
        actual_no = checked_probability(no["selected_stress_probability"], "economic No stress")
        assert abs(actual_yes - expected_yes) <= 1e-10, "economic Yes stress probability does not match forecast reserve"
        assert abs(actual_no - expected_no) <= 1e-10, "economic No stress probability does not match forecast reserve"


def validate_record(x, frozen, *, revision=False, validate_economics_forecast=False):
    i = int(x["review_index"])
    assert i == int(frozen["review_index"]), "review index mismatch"
    assert x["status"] in STATES, "invalid status"
    if revision:
        assert str(x.get("market_id", "")) == str(frozen["id"]), "market id mismatch"
    elif x.get("market_id") is not None:
        assert str(x["market_id"]) == str(frozen["id"]), "market id mismatch"
    assert x["condition_id"].lower() == frozen["conditionId"].lower(), "condition id mismatch"
    assert (x["criteria_sha256"] == frozen["criteria_sha256"] or
            (not revision and x.get("criteria_change_explained"))), "criteria fingerprint mismatch"
    for field in ["literal_analysis", "evidence", "forecast", "economics", "verdict", "reopen_condition"]:
        assert x.get(field), field
    assert isinstance(x["evidence"], list) and all(
        e.get("url") and e.get("observed_utc") and e.get("finding") for e in x["evidence"]
    ), "evidence rows require URL, observed_utc and finding"
    if x["status"] == "valued":
        f = x["forecast"]
        assert 0 <= f["p_yes"] <= 1 and 0 <= f["low"] <= f["p_yes"] <= f["high"] <= 1, "invalid probability/range"
        assert f.get("reasoning") and f.get("method"), "forecast reasoning/method required"
        assert x["economics"].get("both_sides_considered") is True, "both outcomes required"
        if validate_economics_forecast:
            _validate_economics_forecast_consistency(x, frozen)
    return i


def validate_local_markdown_links(markdown, report_path):
    """Reject broken or escaping relative file links in a report before writes."""
    report_dir = Path(report_path).parent.resolve()
    root = ROOT.resolve()
    try:
        report_dir.relative_to(root)
    except ValueError as exc:
        raise ValueError("report directory escapes repository") from exc

    def archived_source_exists(root_relative):
        # These existing read-only adapters preserve legacy links after approved
        # public captures are gzip-archived. Their readers verify manifest hashes.
        for module_name in ("public_source_archive", "public_snapshot_archive"):
            try:
                module = __import__(module_name)
                manifest_loader = getattr(module, "load_manifest", None)
                if manifest_loader is None:
                    manifest_loader = getattr(module, "_load_manifest")
                manifest = manifest_loader()
            except FileNotFoundError:
                continue
            if any(entry.get("original_path") == root_relative
                   for entry in manifest.get("entries", []) if isinstance(entry, dict)):
                module.read_verified_path(root_relative)
                return True

        # The extra HTML captures have two independent manifests and reader
        # profiles. Consult only their declared manifest paths and exact
        # original_path entries; the selected reader verifies the archive and
        # source receipt without restoring the original body.
        try:
            extra = __import__("public_source_archive_extra")
        except ModuleNotFoundError:
            extra = None
        if extra is not None:
            for profile in ("prior36", "more-html"):
                config = extra.PROFILES[profile]
                manifest_path = Path(config["manifest"])
                if not manifest_path.is_file():
                    continue
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if any(entry.get("original_path") == root_relative
                       for entry in manifest.get("entries", []) if isinstance(entry, dict)):
                    extra.read_verified_path(root_relative, profile=profile)
                    return True
        return False

    checked = set()
    for match in _MARKDOWN_LINK.finditer(markdown):
        destination = match.group(1).strip()
        if not destination:
            continue
        if destination.startswith("<"):
            end = destination.find(">")
            if end < 0:
                continue
            destination = destination[1:end]
        else:
            # Optional Markdown link titles follow the destination separated
            # by whitespace; they are not part of the local path.
            destination = destination.split(None, 1)[0]
        parsed = urlsplit(destination)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue  # HTTP(S), mailto, fragments, and other intentional URLs.
        decoded_path = unquote(parsed.path)
        target = (report_dir / decoded_path).resolve(strict=False)
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"local Markdown link escapes repository: {destination!r}") from exc
        key = target.as_posix()
        if key in checked:
            continue
        checked.add(key)
        if target.is_file():
            continue
        root_relative = target.relative_to(root).as_posix()
        if archived_source_exists(root_relative):
            continue
        raise ValueError(f"local Markdown link target is missing: {destination!r}")


def _base_records():
    records = {}
    frozen_by_index = universe()
    for p in sorted((RUN / "evaluations").glob("*.json")):
        x = json.loads(p.read_text())
        i = int(x["review_index"])
        assert i not in records, f"duplicate base record {i}"
        frozen = frozen_by_index[i]
        assert str(x.get("market_id", frozen["id"])) == str(frozen["id"]), f"base market id mismatch {i}"
        assert x["condition_id"].lower() == frozen["conditionId"].lower(), f"base condition id mismatch {i}"
        assert (x["criteria_sha256"] == frozen["criteria_sha256"] or x.get("criteria_change_explained")), f"base criteria mismatch {i}"
        md = p.with_suffix(".md")
        assert md.exists(), f"missing base report {md}"
        assert hashlib.sha256(md.read_bytes()).hexdigest() == x["report_sha256"], f"base report hash mismatch {i}"
        x["report_path"] = f"evaluations/{i:04d}.md"
        records[i] = x
    return records


def _revision_path(rel):
    p = Path(rel)
    assert not p.is_absolute() and ".." not in p.parts, "unsafe revision path"
    candidate = RUN
    for part in p.parts:
        candidate = candidate / part
        assert not candidate.is_symlink(), "symlink in revision path"
    full = (RUN / p).resolve()
    full.relative_to(RUN.resolve())
    return full


def _apply_revisions(records, frozen_by_index):
    ledger = RUN / "revisions.jsonl"
    rows = [] if not ledger.exists() else [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    effective = dict(records)
    for number, row in enumerate(rows, 1):
        assert row.get("schema") == REVISION_SCHEMA, f"bad revision schema at row {number}"
        i = int(row["review_index"])
        previous = effective.get(i)
        assert previous is not None, f"revision has no base record: {i}"
        assert row.get("prior_report_sha256") == previous["report_sha256"], f"revision predecessor mismatch: {i}"
        path = _revision_path(row["revision_path"])
        raw_json = path.read_bytes()
        assert hashlib.sha256(raw_json).hexdigest() == row.get("revision_json_sha256"), f"revision JSON hash mismatch: {i}"
        x = json.loads(raw_json)
        frozen = frozen_by_index[i]
        assert int(x["review_index"]) == i, f"revision index mismatch: {i}"
        validate_record(x, frozen, revision=True)
        assert x.get("revision_reason") == row["reason"] and bool(row["reason"].strip()), "revision reason mismatch/empty"
        assert x.get("prior_report_sha256") == previous["report_sha256"], "revision JSON predecessor mismatch"
        md_path = _revision_path(x["report_path"])
        md = md_path.read_bytes()
        assert hashlib.sha256(md).hexdigest() == x["report_sha256"] == row["report_sha256"], f"revision report hash mismatch: {i}"
        effective[i] = x
    return effective, rows


def rebuild(active=None):
    u = universe()
    base = _base_records()
    effective, revisions = _apply_revisions(base, u)
    counts = {s: sum(x["status"] == s for x in effective.values()) for s in STATES}
    base_counts = {s: sum(x["status"] == s for x in base.values()) for s in STATES}
    pending = [i for i in u if i not in effective]
    old = json.loads((RUN / "progress.json").read_text()) if (RUN / "progress.json").exists() else {}
    active = old.get("active_indices", []) if active is None else active
    active = [i for i in active if i not in effective]
    progress = {
        "schema": "polyclaude.deep_review.v1", "updated_utc": now(),
        "scope": "All3000 frozen conditions; original screens do not reject. First100 completed valuations is operator inspection milestone; blocked reviews and factual exclusions are separate and do not count.",
        "universe": len(u), "completed_in_depth_reviews": counts["valued"] + counts["blocked_after_review"],
        "completed_valuations": counts["valued"], "blocked_after_in_depth_review": counts["blocked_after_review"],
        "factual_exclusions": counts["excluded_factual"], "pending": len(pending),
        "active_indices": active, "next_pending_indices": pending[:30],
        "base_records": len(base), "base_record_counts": base_counts,
        "revisions_written": len(revisions), "milestone": 100,
        "milestone_notified": old.get("milestone_notified", False),
        "execution_authority": "Research records are observations, never later execution authorization.",
    }
    rows = []
    for i, r in u.items():
        v = effective.get(i, {})
        rows.append({
            "index": i, "condition_id": r["conditionId"], "market_id": r["id"], "question": r["question"],
            "status": v.get("status", "in_progress" if i in active else "pending"),
            "evaluated_utc": v.get("evaluated_utc", ""), "p_yes": v.get("forecast", {}).get("p_yes", ""),
            "verdict": v.get("verdict", ""), "report": v.get("report_path", ""),
        })
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    atomic(RUN / "index.csv", buf.getvalue())

    lines = ["# In-depth market review — live index", "", f"Updated: {progress['updated_utc']}", "",
             f"**{counts['valued']} valuations saved; first milestone100:** {counts['valued']} valued; "
             f"{counts['blocked_after_review']} blocked after in-depth review. "
             f"{counts['excluded_factual']} factual exclusions separately; {len(pending)} pending.", "",
             "Full queue: [index.csv](index.csv). Machine resume: [progress.json](progress.json). Protocol: [PROTOCOL.md](PROTOCOL.md). Prior screens carry no rejection authority.", "",
             "Read the [first100 inspection report](MILESTONE_100.md), [dated corrections](CURRENT_REVISIONS.md) and [candidate follow-up](candidate_followup.md) with the original observations. A [spacing-normalized reader snapshot](reader/INDEX.md) is available for older reports; the complete canonical queue is below.", "",
             "Each report below is written before moving to the next evaluation. Related contracts may share evidence, but each probability, literal binding and economic evaluation is explicit. Observations are dated; orders need fresh execution checks.", "",
             "| Index | Market | Status | Verdict |", "|---:|---|---|---|"]
    for i, v in sorted(effective.items()):
        title = u[i]["question"].replace("|", "/")
        verdict = v["verdict"].replace("|", "/")
        lines.append(f"|{i}|[{title}]({v['report_path']})|{v['status']}|{verdict}|")
    if active:
        lines += ["", "Active indices: " + ", ".join(map(str, active))]
    atomic(RUN / "INDEX.md", "\n".join(lines) + "\n")
    dump(RUN / "progress.json", progress)

    base_ledger = RUN / "evaluations.jsonl"
    revision_ledger = RUN / "revisions.jsonl"
    pointer = {
        **progress, "run_directory": str(RUN.relative_to(ROOT)),
        "index": "research/2026-10-17-deep-review/INDEX.md",
        "progress": "research/2026-10-17-deep-review/progress.json",
        "queue": "research/2026-10-17-deep-review/index.csv",
        "protocol": "research/2026-10-17-deep-review/PROTOCOL.md",
        "original_frozen_rules": str(RULES.relative_to(ROOT)),
        "original_rules_sha256": hashlib.sha256(RULES.read_bytes()).hexdigest(),
        # Preserve established meaning: this counts immutable base evaluations only.
        "evaluations_written": len(base),
        "ledger_sha256": hashlib.sha256(base_ledger.read_bytes()).hexdigest() if base_ledger.exists() else None,
        "revisions_sha256": hashlib.sha256(revision_ledger.read_bytes()).hexdigest() if revision_ledger.exists() else None,
        "revisions_written": len(revisions),
        "resume": "Read PROTOCOL and progress; validate index/record identities. Resume active work first, then next pending. Preserve all prior case records; append explicit revisions for changed evidence. Never turn blocked/unpriced into rejected.",
    }
    dump(POINTER, pointer)
    return progress


def record(path):
    x = json.loads(Path(path).read_text())
    u = universe()
    i = int(x["review_index"])
    assert x.get("report_markdown"), "report_markdown required"
    validate_record(x, u[i], validate_economics_forecast=True)
    x["evaluated_utc"] = x.get("evaluated_utc", now())
    x["question"] = u[i]["question"]
    x["market_id"] = u[i]["id"]
    x["valuation_author"] = "primary_operator"
    x["original_index"] = i
    dest = RUN / "evaluations" / f"{i:04d}.json"
    assert not dest.exists(), f"already recorded {i}; use revise"
    report = x.pop("report_markdown").rstrip() + "\n"
    validate_local_markdown_links(report, dest.with_suffix(".md"))
    x["report_sha256"] = hashlib.sha256(report.encode()).hexdigest()
    atomic(dest.with_suffix(".md"), report)
    dump(dest, x)
    with (RUN / "evaluations.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return rebuild()


def revise(path, prior_report_sha256, reason):
    reason = reason.strip()
    assert reason, "revision reason is required"
    u = universe()
    base = _base_records()
    effective, rows = _apply_revisions(base, u)
    x = json.loads(Path(path).read_text())
    i = int(x["review_index"])
    assert i in effective, "cannot revise a condition without a base evaluation"
    previous = effective[i]
    assert re.fullmatch(r"[0-9a-f]{64}", prior_report_sha256 or ""), "prior report SHA-256 required"
    assert prior_report_sha256 == previous["report_sha256"], "provided predecessor hash is stale or mismatched"
    assert x.get("report_markdown"), "report_markdown required"
    validate_record(x, u[i], revision=True, validate_economics_forecast=True)
    report = x.pop("report_markdown").rstrip() + "\n"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    relbase = f"revisions/{i:04d}_{stamp}"
    md_rel = relbase + ".md"
    json_rel = relbase + ".json"
    md_path = _revision_path(md_rel)
    json_path = _revision_path(json_rel)
    assert not md_path.exists() and not json_path.exists(), "duplicate revision path"
    validate_local_markdown_links(report, md_path)
    report_sha = hashlib.sha256(report.encode()).hexdigest()
    assert report_sha != previous["report_sha256"], "duplicate revision report"
    x["evaluated_utc"] = now()
    x["question"] = u[i]["question"]
    x["market_id"] = u[i]["id"]
    x["valuation_author"] = "primary_operator"
    x["original_index"] = i
    x["revision_reason"] = reason
    x["prior_report_sha256"] = prior_report_sha256
    x["report_sha256"] = report_sha
    x["report_path"] = md_rel
    x["revision_path"] = json_rel
    json_payload = json.dumps(x, ensure_ascii=False, indent=2) + "\n"
    row = {"schema": REVISION_SCHEMA, "review_index": i, "revision_path": json_rel,
           "report_sha256": report_sha, "prior_report_sha256": prior_report_sha256,
           "revision_json_sha256": hashlib.sha256(json_payload.encode("utf-8")).hexdigest(),
           "reason": reason, "revision_utc": x["evaluated_utc"]}
    # Create immutable artifacts first; the append-only ledger is the commit point.
    atomic(md_path, report)
    atomic(json_path, json_payload)
    ledger = RUN / "revisions.jsonl"
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return rebuild()


def start(index):
    """Start or resume exactly one unfinished case in this review run."""
    frozen = universe()
    if not isinstance(index, int) or isinstance(index, bool) or index not in frozen:
        raise ValueError(f"unknown review index: {index!r}")

    base = _base_records()
    effective, _ = _apply_revisions(base, frozen)
    if index in effective:
        raise ValueError(f"review index {index} already has a completed record; use revise")

    progress_path = RUN / "progress.json"
    old = json.loads(progress_path.read_text()) if progress_path.exists() else {}
    active = old.get("active_indices", [])
    if not isinstance(active, list):
        raise ValueError("progress active_indices must be a list")
    if any(not isinstance(i, int) or isinstance(i, bool) or i not in frozen for i in active):
        raise ValueError("progress contains an invalid active review index")
    if len(set(active)) != len(active):
        raise ValueError("progress contains duplicate active review indices")

    unfinished = [i for i in active if i not in effective]
    if index in unfinished:
        # Resume the same case without duplicating or reordering active work.
        return rebuild(active)
    if unfinished:
        raise ValueError(
            f"cannot start review index {index}; unfinished active case(s): "
            + ", ".join(map(str, unfinished))
        )

    # Keep any stale completed entries for rebuild() to filter, preserving
    # the order of live active cases and adding the new case last.
    return rebuild(active + [index])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["init", "start", "record", "revise", "rebuild"])
    p.add_argument("--index", type=int)
    p.add_argument("--input")
    p.add_argument("--prior-report-sha256")
    p.add_argument("--reason")
    a = p.parse_args()
    (RUN / "evaluations").mkdir(parents=True, exist_ok=True)
    if a.command == "record":
        out = record(a.input)
    elif a.command == "revise":
        out = revise(a.input, a.prior_report_sha256, a.reason)
    elif a.command == "start":
        out = start(a.index)
    else:
        out = rebuild()
    print(json.dumps(out))


if __name__ == "__main__":
    main()
