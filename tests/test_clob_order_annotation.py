from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import clob_v2  # noqa: E402


def _snapshot(tmp_path: Path) -> Path:
    path = tmp_path / "position_condition_ids.json"
    path.write_text(json.dumps({"positions": [{
        "slug": "trump-out-as-president-before-2027",
        "outcome": "No", "conditionId": "0xAbC", "asset": "token-no",
    }]}))
    return path


def test_orders_are_annotated_only_by_exact_condition_and_asset(tmp_path):
    result = {"status_code": 200, "body": {"data": [
        {"id": "live", "market": "0xabc", "asset_id": "token-no"},
        {"id": "unknown", "market": "0xabc", "asset_id": "other"},
    ]}}
    annotated = clob_v2.annotate_open_orders(result, snapshot_path=_snapshot(tmp_path))
    rows = annotated["body"]["data"]
    assert rows[0]["canonical_slug"] == "trump-out-as-president-before-2027"
    assert rows[0]["position_outcome"] == "No"
    assert rows[0]["identity_status"] == "matched_position_snapshot"
    assert "canonical_slug" not in rows[1]
    assert rows[1]["identity_status"] == "unmapped_position_snapshot"
    assert result["body"]["data"][0].get("identity_status") is None


def test_duplicate_snapshot_identity_is_explicitly_ambiguous(tmp_path):
    path = tmp_path / "position_condition_ids.json"
    path.write_text(json.dumps({"positions": [
        {"slug": "one", "outcome": "No", "conditionId": "0xabc", "asset": "t"},
        {"slug": "two", "outcome": "No", "conditionId": "0xabc", "asset": "t"},
    ]}))
    result = {"status_code": 200, "body": {"data": [
        {"market": "0xABC", "asset_id": "t"}
    ]}}
    row = clob_v2.annotate_open_orders(result, snapshot_path=path)["body"]["data"][0]
    assert row["identity_status"] == "ambiguous_position_snapshot"
    assert "canonical_slug" not in row


def test_snapshot_failure_is_fail_safe(tmp_path):
    with pytest.raises(RuntimeError, match="snapshot unavailable"):
        clob_v2.annotate_open_orders(
            {"status_code": 200, "body": {"data": []}},
            snapshot_path=tmp_path / "missing.json",
        )
