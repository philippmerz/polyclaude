from __future__ import annotations

import gzip
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deep_review_public_snapshot as snapshot  # noqa: E402


def _market() -> dict:
    return {
        "id": "42", "conditionId": "0xabc", "question": "Q?", "description": "literal",
        "slug": "q", "resolutionSource": "https://source.example", "endDate": "2026-10-31T00:00:00Z",
        "outcomes": '["Yes", "No"]', "clobTokenIds": '["yes-token", "no-token"]',
    }


def test_identity_checks_bind_literal_description_and_ordered_tokens():
    frozen = _market()
    current = {**frozen, "outcomes": ["Yes", "No"], "clobTokenIds": ["yes-token", "no-token"]}
    assert all(snapshot.identity_checks(frozen, current).values())
    current["description"] = "changed condition"
    assert snapshot.identity_checks(frozen, current)["description"] is False


def test_compact_fee_reads_fd_and_ignores_top_level_rebate_object():
    payload = {
        "c": "0xabc", "t": [{"o": "Yes", "t": "yes-token"}, {"o": "No", "t": "no-token"}],
        "r": {"mi": 20, "ma": 6.5, "e": True, "moas": 30},
        "fd": {"r": 0.04, "e": 1, "to": True},
    }
    assert snapshot.compact_fee_fields(payload, "0xabc", {"Yes": "yes-token", "No": "no-token"}) == {
        "r": 0.04, "e": 1.0, "to": True,
    }
    with pytest.raises(ValueError, match="fee descriptor"):
        snapshot.compact_fee_fields({**payload, "fd": None}, "0xabc", {"Yes": "yes-token", "No": "no-token"})


def test_fee_parity_unavailable_is_not_treated_as_verified():
    descriptor = {"r": 0.04, "e": 1.0, "to": True}
    assert snapshot.fee_parity({}, descriptor) is None
    assert snapshot.fee_parity_error(None) == "compact_fee_vs_gamma_schedule_parity_unavailable"
    assert snapshot.fee_parity_error(True) is None


@pytest.mark.parametrize(
    ("status", "valid", "available", "expected"),
    [
        (503, False, False, "unavailable_http_503"),
        (200, True, False, "omitted_from_http_200"),
        (200, False, False, "invalid_http_200_books_payload"),
        (200, True, True, "returned_in_http_200"),
    ],
)
def test_book_availability_distinguishes_transport_failure_from_omission(
    status, valid, available, expected
):
    assert snapshot.book_availability_status(status, valid, available) == expected


def test_request_receipt_records_status_times_hash_and_only_safe_headers(tmp_path, monkeypatch):
    monkeypatch.setattr(snapshot, "ROOT", tmp_path)
    collector = snapshot.Collector(tmp_path / "logs/run")

    class FakeClient:
        def request(self, method, url, json=None):
            return SimpleNamespace(status_code=503, content=b'{"temporary":"failure"}',
                                   headers={"date": "Sun, 18 Oct 2026 00:00:00 GMT", "Set-Cookie": "secret"})

    collector.client = FakeClient()
    status, body, receipt = collector.request(name="one", method="GET", url="https://example.test/x")
    assert status == 503 and body == b'{"temporary":"failure"}'
    row = collector.receipts[0]
    saved = json.loads((tmp_path / row["receipt_path"]).read_text())
    assert saved["status_code"] == 503
    assert saved["raw_sha256"] == hashlib.sha256(body).hexdigest()
    compressed = (tmp_path / saved["gzip_path"]).read_bytes()
    assert saved["gzip_sha256"] == hashlib.sha256(compressed).hexdigest()
    assert gzip.decompress(compressed) == body
    assert "Set-Cookie" not in json.dumps(saved)
    assert datetime.fromisoformat(saved["started_utc"]) <= datetime.fromisoformat(saved["received_utc"])
