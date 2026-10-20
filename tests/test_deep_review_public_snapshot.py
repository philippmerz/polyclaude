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


def test_compact_mapping_rejects_duplicate_malformed_and_extra_rows():
    base = {"c": "0xabc", "t": [{"o": "Yes", "t": "yes-token"},
                                    {"o": "No", "t": "no-token"}]}
    token_map = {"Yes": "yes-token", "No": "no-token"}
    snapshot.compact_market_identity(base, "0xabc", token_map)
    for rows in (
        [base["t"][0], base["t"][0]],
        [base["t"][0], {"o": "No", "t": "yes-token"}],
        [*base["t"], {"o": "Extra", "t": "extra-token"}],
        [base["t"][0], {"o": "No"}],
    ):
        with pytest.raises(ValueError):
            snapshot.compact_market_identity({**base, "t": rows}, "0xabc", token_map)


def test_full_market_fee_free_requires_exact_identity_map_and_numeric_zero():
    full = {"condition_id": "0xabc", "tokens": [
        {"outcome": "Yes", "token_id": "yes-token"},
        {"outcome": "No", "token_id": "no-token"}], "taker_base_fee": 0}
    snapshot.corroborate_fee_free_market(full, "0xabc", {"Yes": "yes-token", "No": "no-token"})
    for change in (
        {"condition_id": "0xwrong"},
        {"tokens": [full["tokens"][0], full["tokens"][0]]},
        {"tokens": [*full["tokens"], {"outcome": "Other", "token_id": "x"}]},
        {"taker_base_fee": True}, {"taker_base_fee": "0"},
        {"taker_base_fee": float("nan")}, {"taker_base_fee": 1},
        {"taker_base_fee": None},
    ):
        with pytest.raises(ValueError):
            snapshot.corroborate_fee_free_market({**full, **change}, "0xabc",
                                                   {"Yes": "yes-token", "No": "no-token"})


def _capture_fee_case(tmp_path, monkeypatch, *, gamma_changes=None, compact_changes=None, full_changes=None):
    frozen = _market()
    frozen["criteria_sha256"] = "a" * 64
    gamma = {**frozen, "feesEnabled": False, "feeSchedule": None, **(gamma_changes or {})}
    compact = {"c": "0xabc", "t": [{"o": "Yes", "t": "yes-token"},
                                       {"o": "No", "t": "no-token"}], **(compact_changes or {})}
    full = {"condition_id": "0xabc", "tokens": [
        {"outcome": "Yes", "token_id": "yes-token"},
        {"outcome": "No", "token_id": "no-token"}], "taker_base_fee": 0,
        **(full_changes or {})}
    monkeypatch.setattr(snapshot, "ROOT", tmp_path)
    monkeypatch.setattr(snapshot.ledger, "universe", lambda: {438: frozen})
    collector_cls = snapshot.Collector
    created = []

    class FakeClient:
        def request(self, method, url, json=None):
            if url == snapshot.GAMMA + "42":
                body = gamma
            elif url == snapshot.FEE + "0xabc":
                body = compact
            elif url == snapshot.FULL_MARKET + "0xabc":
                body = full
            elif url == snapshot.BOOKS:
                body = [{"asset_id": "yes-token"}, {"asset_id": "no-token"}]
            else:
                raise AssertionError(url)
            return SimpleNamespace(status_code=200, content=json_module.dumps(body).encode(), headers={})

    json_module = json
    old_init = collector_cls.__init__
    def init(self, log_dir):
        old_init(self, log_dir)
        self.client = FakeClient()
        created.append(self)
    monkeypatch.setattr(collector_cls, "__init__", init)
    result = snapshot.capture([438], tmp_path / "capture.json", tmp_path / "logs", include_geo=False)
    obj = json.loads((tmp_path / "capture.json").read_text())
    return result, obj, created[0]


def test_fee_free_capture_uses_full_receipt_without_fabricating_descriptor(tmp_path, monkeypatch):
    result, capture, collector = _capture_fee_case(tmp_path, monkeypatch)
    case = capture["cases"][0]
    fee = case["optionalfee_descriptor"]
    assert not result["errors"]
    assert result["fee_free_corroborated"] == 1 and result["fee_descriptors"] == 0
    assert fee["descriptor"] is None and fee["structured_gamma_parity"] is None
    assert fee["fee_free_corroborated"] is True
    assert fee["full_market_receipt_path"]
    assert any(row["url"] == snapshot.FULL_MARKET + "0xabc" for row in collector.receipts)


@pytest.mark.parametrize("kwargs", [
    {"full_changes": {"taker_base_fee": 1}},
    {"full_changes": {"condition_id": "0xwrong"}},
    {"full_changes": {"tokens": [{"outcome": "Yes", "token_id": "yes-token"}]}},
    {"gamma_changes": {"feeSchedule": {"rate": 0.01, "exponent": 1, "takerOnly": True}}},
    {"gamma_changes": {"feeSchedule": {"rate": 0, "exponent": 1}}},
    {"gamma_changes": {"feeSchedule": {"rate": 0, "exponent": 11, "takerOnly": True}}},
    {"gamma_changes": {"feesEnabled": True}},
    {"gamma_changes": {"description": "changed"}},
    {"compact_changes": {"t": [{"o": "Yes", "t": "yes-token"},
                                 {"o": "Yes", "t": "no-token"}]}},
])
def test_fee_free_capture_fails_closed_on_missing_or_contradictory_evidence(tmp_path, monkeypatch, kwargs):
    result, capture, collector = _capture_fee_case(tmp_path, monkeypatch, **kwargs)
    fee = capture["cases"][0]["optionalfee_descriptor"]
    assert result["errors"]
    assert fee.get("fee_free_corroborated") is not True
    if kwargs.get("gamma_changes"):
        assert not any(row["url"].startswith(snapshot.FULL_MARKET) for row in collector.receipts)


def test_fee_enabled_compact_path_retains_structured_parity_requirement(tmp_path, monkeypatch):
    descriptor = {"r": 0.04, "e": 1, "to": True}
    result, capture, collector = _capture_fee_case(
        tmp_path, monkeypatch,
        gamma_changes={"feesEnabled": True, "feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True}},
        compact_changes={"fd": descriptor})
    fee = capture["cases"][0]["optionalfee_descriptor"]
    assert not result["errors"]
    assert fee["descriptor"] == descriptor and fee["structured_gamma_parity"] is True
    assert not any(row["url"].startswith(snapshot.FULL_MARKET) for row in collector.receipts)


@pytest.mark.parametrize("fd", ["malformed", {"r": 0.01, "e": 1, "to": True}])
def test_malformed_or_nonzero_compact_descriptor_never_falls_back(tmp_path, monkeypatch, fd):
    result, capture, collector = _capture_fee_case(
        tmp_path, monkeypatch,
        compact_changes={"fd": fd})
    assert result["errors"]
    assert capture["cases"][0]["optionalfee_descriptor"].get("fee_free_corroborated") is not True
    assert not any(row["url"].startswith(snapshot.FULL_MARKET) for row in collector.receipts)


def test_disabled_flag_cannot_accept_matching_nonzero_gamma_and_compact_fees(tmp_path, monkeypatch):
    result, capture, collector = _capture_fee_case(
        tmp_path, monkeypatch,
        gamma_changes={"feeSchedule": {"rate": 0.04, "exponent": 1, "takerOnly": True}},
        compact_changes={"fd": {"r": 0.04, "e": 1, "to": True}})
    assert result["errors"]
    assert capture["cases"][0]["optionalfee_descriptor"].get("fee_free_corroborated") is not True
    assert not any(row["url"].startswith(snapshot.FULL_MARKET) for row in collector.receipts)


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
