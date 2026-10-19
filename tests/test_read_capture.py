from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from read_capture import Capture  # noqa: E402


META = {
    "read_only": True, "method": "eth_call", "endpoint": "polygon-rpc",
    "operation": "balanceOf", "chain_id": 137, "block_number": 12345,
    "call_window_label": "single-fixed-block-read",
}


def _unpack(response):
    return response[0], response[1], response[2]


def test_response_receipt_is_durable_before_parser_runs_and_parser_failure_keeps_it(tmp_path):
    cap = Capture(tmp_path / "private")
    body = b'{"result":"0x05"}'
    parser_saw_files = []

    def parse(status, raw, receipt):
        parser_saw_files.extend(p.name for p in (tmp_path / "private").iterdir())
        assert status == 200 and raw == body
        assert receipt["timing_basis"] == "call_window"
        raise ValueError("formatter schema mismatch")

    with pytest.raises(ValueError, match="formatter schema mismatch"):
        cap.capture_readonly_call(
            "balance", META,
            lambda: (200, body, {"Date": "Mon, 19 Oct 2026 01:00:00 GMT"}),
            _unpack, parse,
        )

    assert set(parser_saw_files) == {
        "balance.intent.json", "balance.body.json.gz", "balance.receipt.json"
    }
    receipt = json.loads((tmp_path / "private/balance.receipt.json").read_text())
    packed = (tmp_path / "private/balance.body.json.gz").read_bytes()
    assert gzip.decompress(packed) == body
    assert receipt["raw_sha256"] == hashlib.sha256(body).hexdigest()
    assert receipt["gzip_sha256"] == hashlib.sha256(packed).hexdigest()
    assert receipt["timing_basis"] == "call_window"
    assert "wire_started_utc" not in json.dumps(receipt)
    assert receipt["body_representation"] == "supplied_bytes"


def test_call_window_intent_precedes_call_and_private_permissions(tmp_path):
    cap = Capture(tmp_path / "private")
    called = []

    def invoke():
        intent = json.loads((tmp_path / "private/read.intent.json").read_text())
        called.append(intent)
        return (503, b"upstream unavailable", {})

    result = cap.capture_readonly_call("read", META, invoke, _unpack,
                                       lambda status, raw, receipt: (status, raw))
    assert result == (503, b"upstream unavailable")
    assert called and called[0]["timing_basis"] == "call_window"
    assert "wire_started_utc" not in called[0]
    assert os.stat(tmp_path / "private").st_mode & 0o777 == 0o700
    assert all(p.stat().st_mode & 0o777 == 0o600 for p in (tmp_path / "private").iterdir())
    receipt = json.loads((tmp_path / "private/read.receipt.json").read_text())
    assert receipt["response_status"] == 503
    assert receipt["error_type"] is None


def test_network_exception_is_recorded_without_exception_text(tmp_path):
    cap = Capture(tmp_path / "private")

    def invoke():
        raise RuntimeError("Authorization: bearer do-not-store")

    with pytest.raises(RuntimeError):
        cap.capture_readonly_call("failed", META, invoke, _unpack, lambda *args: args)
    receipt = json.loads((tmp_path / "private/failed.receipt.json").read_text())
    assert receipt["response_status"] is None
    assert receipt["error_type"] == "RuntimeError"
    assert "do-not-store" not in json.dumps(receipt)


def test_response_adapter_failure_is_recorded_and_not_mislabeled_http(tmp_path):
    cap = Capture(tmp_path / "private")
    with pytest.raises(ValueError, match="cannot extract"):
        cap.capture_readonly_call(
            "adapter-failure", META, lambda: object(),
            lambda response: (_ for _ in ()).throw(ValueError("cannot extract")),
            lambda *args: args,
        )
    receipt = json.loads((tmp_path / "private/adapter-failure.receipt.json").read_text())
    assert receipt["response_status"] is None
    assert receipt["error_type"] == "ValueError"
    assert receipt["raw_bytes"] == 0


def test_headers_and_request_metadata_are_allowlisted_and_query_secrets_removed(tmp_path):
    cap = Capture(tmp_path / "private")
    metadata = {**META, "url": "https://user:pw@example.test/read?token=secret&x=1#frag"}
    cap.write_intent("safe", metadata, "2026-10-19T00:00:00Z")
    receipt = cap.write_response(
        "safe", metadata, 200, b"ok", "2026-10-19T00:00:00Z", "2026-10-19T00:00:01Z",
        {"Date": "Mon, 19 Oct 2026 00:00:01 GMT", "Authorization": "Bearer secret",
         "Set-Cookie": "session=secret", "X-Owner-UUID": "secret"},
    )
    saved = json.loads((tmp_path / "private/safe.receipt.json").read_text())
    assert saved["request"]["url"] == "https://example.test/read"
    assert set(saved["headers"]) == {"date"}
    assert "secret" not in json.dumps(saved)
    assert receipt["response_status"] == 200
    with pytest.raises(ValueError, match="read_only=True"):
        cap.write_intent("unsafe", {"method": "GET"})
    with pytest.raises(ValueError, match="unsafe or unsupported"):
        cap.write_intent("bad", {**META, "authorization": "Bearer secret"})


def test_duplicate_capture_names_never_overwrite_existing_receipts(tmp_path):
    cap = Capture(tmp_path / "private")
    intent = cap.write_intent("same", META)
    path = tmp_path / "private/same.intent.json"
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        cap.write_intent("same", META)
    assert path.read_bytes() == before
    cap.write_response("same", META, 502, b"error", intent["started_utc"],
                       intent["started_utc"])
    with pytest.raises(FileExistsError):
        cap.write_response("same", META, 200, b"new", intent["started_utc"],
                           intent["started_utc"])
    assert gzip.decompress((tmp_path / "private/same.body.json.gz").read_bytes()) == b"error"


def test_body_representation_provenance_is_explicit_and_validated(tmp_path):
    cap = Capture(tmp_path / "private")
    result = cap.capture_readonly_call(
        "sdk", META, lambda: (200, b'{"balance":"0x05"}', {}), _unpack,
        lambda status, raw, receipt: receipt,
        body_representation="sdk_result_serialization",
    )
    assert result["body_representation"] == "sdk_result_serialization"
    assert result["hash_scope"] == "supplied_bytes_only_not_wire_authentication"
    intent = json.loads((tmp_path / "private/sdk.intent.json").read_text())
    with pytest.raises(ValueError, match="unsupported body_representation"):
        cap.write_response("sdk", META, 200, b"x", intent["started_utc"],
                           intent["started_utc"], body_representation="wire_verified")
