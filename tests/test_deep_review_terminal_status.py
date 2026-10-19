import sys
import gzip
import hashlib
import json
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deep_review_terminal_status as terminal


RULE = {
    "id": "123", "conditionId": "0xabc", "question": "Will it happen?",
    "slug": "will-it-happen", "description": "Full frozen criteria.",
    "resolutionSource": "https://source.example/rule", "endDate": "2026-12-31T12:00:00Z",
    "outcomes": ["Yes", "No"], "clobTokenIds": ["111", "222"],
}


def resolved_market():
    return {
        "id": "123", "conditionId": "0xabc", "question": "Will it happen?",
        "slug": "will-it-happen", "description": "Full frozen criteria.",
        "resolutionSource": "https://source.example/rule", "endDate": "2026-12-31T12:00:00Z",
        "outcomes": '["Yes", "No"]', "clobTokenIds": '["111", "222"]',
        "closed": True, "acceptingOrders": False, "umaResolutionStatus": "resolved",
        "outcomePrices": '["1", "0"]',
    }


def test_exact_terminal_gamma_is_candidate():
    result = terminal.classify(RULE, resolved_market())
    assert result["classification"] == "terminal_candidate"
    assert result["terminal_candidate"] is True
    assert result["identity_exact"] is True


def test_changed_criteria_is_unknown_even_if_gamma_says_resolved():
    market = resolved_market()
    market["description"] = "A changed or truncated rule"
    result = terminal.classify(RULE, market)
    assert result["classification"] == "unknown_primary_review"
    assert result["terminal_candidate"] is False
    assert result["identity_checks"]["description"] is False


@pytest.mark.parametrize("field,value", [
    ("closed", None), ("acceptingOrders", None),
    ("closed", "true"), ("acceptingOrders", 0),
])
def test_terminal_flags_must_be_explicit_booleans(field, value):
    market = resolved_market()
    market[field] = value
    result = terminal.classify(RULE, market)
    assert result["terminal_candidate"] is False


@pytest.mark.parametrize("status,prices", [
    ("proposed", '["1", "0"]'),
    ("resolved", '["0.5", "0.5"]'),
    ("resolved", '[true, 0]'),
    ("resolved", '["1", "1"]'),
    ("resolved", "not-json"),
])
def test_proposed_or_nonbinary_or_malformed_prices_never_terminal(status, prices):
    market = resolved_market()
    market["umaResolutionStatus"] = status
    market["outcomePrices"] = prices
    result = terminal.classify(RULE, market)
    assert result["terminal_candidate"] is False
    assert result["classification"] == "nonterminal_primary_review"


@pytest.mark.parametrize("field,value", [
    ("outcomes", "not-json"), ("outcomes", ["Yes", True]),
    ("clobTokenIds", "not-json"), ("clobTokenIds", ["111"]),
])
def test_malformed_or_changed_identity_arrays_fail_closed(field, value):
    market = resolved_market()
    market[field] = value
    result = terminal.classify(RULE, market)
    assert result["terminal_candidate"] is False
    assert result["classification"] == "unknown_primary_review"


def test_capture_binds_raw_receipt_and_sanitizes_open_prices(monkeypatch, tmp_path):
    # 306 deliberately uses the exact same frozen identity and a response body
    # that claims terminal status; its non-200 status must still force unknown.
    rules = {305: RULE, 306: RULE, 307: {**RULE, "id": "125"}}
    terminal_body = resolved_market()
    error_body = resolved_market()
    open_body = resolved_market()
    open_body.update({"id": "125", "closed": False, "acceptingOrders": True,
                      "umaResolutionStatus": "proposed", "outcomePrices": [0.24, 0.76]})
    responses = [
        (200, terminal_body),
        (503, error_body),
        (200, open_body),
    ]
    calls = []

    class FakeResponse:
        def __init__(self, status, body):
            self.status_code = status
            self.content = json.dumps(body, separators=(",", ":")).encode()
            self.headers = {"content-type": "application/json", "date": "Mon, 19 Oct 2026 01:00:00 GMT"}

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs == {"timeout": 20, "follow_redirects": False}

        def get(self, url):
            calls.append(url)
            status, body = responses[len(calls) - 1]
            return FakeResponse(status, body)

        def close(self):
            pass

    monkeypatch.setattr(terminal, "ROOT", tmp_path)
    monkeypatch.setattr(terminal.ledger, "universe", lambda: rules)
    monkeypatch.setattr(terminal.httpx, "Client", FakeClient)
    output_dir = tmp_path / "units"
    log_dir = tmp_path / "raw"

    batch = terminal.capture([305, 306, 307], output_dir, log_dir)
    assert len(calls) == 3
    assert batch["cases"][0]["terminal_candidate"] is True
    assert batch["cases"][1]["terminal_candidate"] is False
    assert batch["cases"][1]["classification"] == "unknown_primary_review"
    assert batch["cases"][2]["classification"] == "nonterminal_primary_review"

    for idx, expected_status, expected_body in (
        (305, 200, terminal_body), (306, 503, error_body), (307, 200, open_body)
    ):
        receipt = json.loads((log_dir / f"{idx:04d}_gamma.receipt.json").read_text())
        compressed = (log_dir / f"{idx:04d}_gamma.body.json.gz").read_bytes()
        raw = gzip.decompress(compressed)
        assert receipt["status_code"] == expected_status
        assert receipt["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert receipt["gzip_sha256"] == hashlib.sha256(compressed).hexdigest()
        assert json.loads(raw) == expected_body
        unit = json.loads((output_dir / f"case_{idx:04d}.json").read_text())
        assert unit["raw_sha256"] == receipt["raw_sha256"]
        assert unit["gzip_sha256"] == receipt["gzip_sha256"]
        assert unit["started_utc"] == receipt["started_utc"]
        assert unit["received_utc"] == receipt["received_utc"]
    open_unit_text = (output_dir / "case_0307.json").read_text()
    assert "outcomePrices" not in open_unit_text
    assert "0.24" not in open_unit_text and "0.76" not in open_unit_text
